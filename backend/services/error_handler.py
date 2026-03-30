"""
自动诊断优化包装器

整合错误诊断器和知识库，为工作流提供统一的错误处理接口

使用示例：
    from services.error_handler import AutoErrorHandler

    handler = AutoErrorHandler()

    try:
        result = await some_operation()
    except Exception as e:
        # 自动诊断并记录
        handled = await handler.handle_error(
            error=e,
            stage="collect",
            workflow_id="xxx",
            operation=lambda: retry_operation()
        )

        if handled.success:
            logger.info("错误已自动修复")
        else:
            logger.warning(f"需要人工处理: {handled.solution}")
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Awaitable, TypeVar

from services.error_diagnoser import (
    ErrorDiagnoser,
    ErrorType,
    FallbackAction,
    DiagnosisResult,
    error_diagnoser
)
from services.failure_knowledge_base import (
    FailureKnowledgeBase,
    failure_knowledge_base
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class HandledError:
    """已处理的错误"""
    success: bool
    error_type: ErrorType
    root_cause: str
    solution: str
    fallback_action: FallbackAction
    retry_count: int
    final_result: Any = None
    requires_manual_intervention: bool = False
    knowledge_base_id: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0


class AutoErrorHandler:
    """
    自动错误处理器

    功能：
    1. 自动诊断错误类型和根因
    2. 查询知识库获取已知解决方案
    3. 执行降级策略
    4. 记录失败到知识库
    5. 智能重试机制
    """

    def __init__(
        self,
        diagnoser: ErrorDiagnoser = None,
        knowledge_base: FailureKnowledgeBase = None,
        retry_config: RetryConfig = None
    ):
        """
        初始化错误处理器

        Args:
            diagnoser: 错误诊断器实例
            knowledge_base: 知识库实例
            retry_config: 重试配置
        """
        self.diagnoser = diagnoser or error_diagnoser
        self.kb = knowledge_base or failure_knowledge_base
        self.retry_config = retry_config or RetryConfig()

        self._retry_count: Dict[str, int] = {}

        logger.info("AutoErrorHandler initialized")

    async def handle_error(
        self,
        error: Exception,
        stage: str,
        workflow_id: str,
        operation: Callable[[], Awaitable[T]] = None,
        context: Dict[str, Any] = None,
        skip_kb_record: bool = False
    ) -> HandledError:
        """
        处理错误的统一入口

        Args:
            error: 捕获的异常
            stage: 当前工作流阶段
            workflow_id: 工作流ID
            operation: 可选的降级操作（用于重试）
            context: 额外的上下文信息
            skip_kb_record: 是否跳过知识库记录（用于测试）

        Returns:
            HandledError: 处理结果
        """
        context = context or {}

        diagnosis = self.diagnoser.diagnose(error, stage, context)

        retry_key = f"{workflow_id}:{stage}"
        current_retry = self._retry_count.get(retry_key, 0)

        known_solution = self.kb.get_solution_for_error(
            diagnosis.error_type_name,
            diagnosis.root_cause
        )

        if known_solution and diagnosis.solution != known_solution:
            diagnosis.solution = known_solution
            logger.info(f"Using known solution from knowledge base: {known_solution[:50]}...")

        if operation and self._should_retry(diagnosis, current_retry):
            retry_result = await self._execute_with_retry(
                operation,
                diagnosis,
                retry_key,
                context
            )

            if retry_result is not None:
                self.kb.record_success_by_context(
                    diagnosis.error_type_name,
                    diagnosis.root_cause,
                    diagnosis.solution
                )
                self._retry_count.pop(retry_key, None)

                return HandledError(
                    success=True,
                    error_type=diagnosis.error_type,
                    root_cause=diagnosis.root_cause,
                    solution=diagnosis.solution,
                    fallback_action=diagnosis.fallback_action,
                    retry_count=current_retry + 1,
                    final_result=retry_result
                )

        kb_id = None
        if not skip_kb_record:
            kb_id = self.kb.record_failure(
                error_type=diagnosis.error_type_name,
                error_message=str(error)[:500],
                stage=stage,
                root_cause=diagnosis.root_cause,
                solution=diagnosis.solution,
                workflow_id=workflow_id,
                retry_count=current_retry,
                metadata=context
            )

        requires_manual = diagnosis.fallback_action in [
            FallbackAction.WAIT_FOR_MANUAL,
            FallbackAction.ABORT_WORKFLOW
        ]

        return HandledError(
            success=False,
            error_type=diagnosis.error_type,
            root_cause=diagnosis.root_cause,
            solution=diagnosis.solution,
            fallback_action=diagnosis.fallback_action,
            retry_count=current_retry,
            requires_manual_intervention=requires_manual,
            knowledge_base_id=kb_id
        )

    def _should_retry(self, diagnosis: DiagnosisResult, current_retry: int) -> bool:
        """判断是否应该重试"""
        if diagnosis.fallback_action in [
            FallbackAction.RETRY,
            FallbackAction.RETRY_WITH_BACKUP
        ]:
            return current_retry < self.retry_config.max_retries

        return False

    async def _execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        diagnosis: DiagnosisResult,
        retry_key: str,
        context: Dict[str, Any]
    ) -> Optional[T]:
        """
        执行带重试的操作

        Args:
            operation: 要执行的操作
            diagnosis: 诊断结果
            retry_key: 重试键
            context: 上下文

        Returns:
            操作结果或None
        """
        for attempt in range(self.retry_config.max_retries):
            try:
                delay = min(
                    self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay
                )

                if attempt > 0:
                    logger.info(f"Retrying after {delay:.1f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)

                self._retry_count[retry_key] = attempt

                result = await operation()

                logger.info(f"Operation succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {str(e)[:100]}")

                if attempt == self.retry_config.max_retries - 1:
                    return None

                new_diagnosis = self.diagnoser.diagnose(e, context.get('stage', 'unknown'), context)

                if new_diagnosis.error_type != diagnosis.error_type:
                    logger.warning(f"Error type changed during retry: {diagnosis.error_type} -> {new_diagnosis.error_type}")
                    return None

        return None

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误处理摘要"""
        return {
            'recent_failures': self.kb.get_recent_failures(limit=10),
            'frequent_errors': self.kb.get_frequent_errors(top_n=5),
            'error_trend': self.kb.get_error_trend(days=7),
            'diagnoser_stats': self.diagnoser.get_error_statistics(),
            'suggestions': self.kb.suggest_improvements()
        }

    def clear_context(self, workflow_id: str = None):
        """清除重试计数"""
        if workflow_id:
            keys_to_remove = [k for k in self._retry_count if k.startswith(f"{workflow_id}:")]
            for key in keys_to_remove:
                self._retry_count.pop(key, None)
        else:
            self._retry_count.clear()


auto_error_handler = AutoErrorHandler()
