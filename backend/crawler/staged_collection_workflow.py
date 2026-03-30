"""
双阶段采集审核工作流
Stage 1: 验证阶段 - 执行数据源验证
Stage 2: 采集阶段 - 执行正式数据采集（仅在验证通过后）
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """工作流阶段"""
    PENDING = "pending"
    VALIDATION = "validation"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    COLLECTION = "collection"
    COLLECTION_PASSED = "collection_passed"
    COLLECTION_FAILED = "collection_failed"
    COMPLETED = "completed"


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageResult:
    """阶段结果"""
    stage: WorkflowStage
    status: WorkflowStatus
    message: str
    data: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            return (end - start).total_seconds()
        return 0


@dataclass
class CollectionWorkflow:
    """采集工作流"""
    workflow_id: str
    source_name: str
    source_url: str
    source_type: str = "unknown"

    current_stage: WorkflowStage = WorkflowStage.PENDING
    overall_status: WorkflowStatus = WorkflowStatus.PENDING

    validation_result: Optional[StageResult] = None
    collection_result: Optional[StageResult] = None

    can_proceed: bool = False
    requires_manual_review: bool = False

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_status(self, stage: WorkflowStage, status: WorkflowStatus, message: str = ""):
        self.current_stage = stage
        self.overall_status = status
        self.updated_at = datetime.now().isoformat()

        if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            self.completed_at = datetime.now().isoformat()

    def mark_validation_passed(self, validation_result: StageResult):
        self.validation_result = validation_result
        self.can_proceed = True
        self.requires_manual_review = len(validation_result.warnings) > 0
        self.update_status(
            WorkflowStage.VALIDATION_PASSED,
            WorkflowStatus.RUNNING if not self.requires_manual_review else WorkflowStatus.PAUSED,
            "验证通过"
        )

    def mark_validation_failed(self, validation_result: StageResult):
        self.validation_result = validation_result
        self.can_proceed = False
        self.update_status(
            WorkflowStage.VALIDATION_FAILED,
            WorkflowStatus.FAILED,
            f"验证失败: {validation_result.message}"
        )

    def mark_collection_started(self):
        self.update_status(WorkflowStage.COLLECTION, WorkflowStatus.RUNNING, "采集中")

    def mark_collection_passed(self, collection_result: StageResult):
        self.collection_result = collection_result
        self.update_status(WorkflowStage.COLLECTION_PASSED, WorkflowStatus.COMPLETED, "采集完成")

    def mark_collection_failed(self, collection_result: StageResult):
        self.collection_result = collection_result
        self.update_status(WorkflowStage.COLLECTION_FAILED, WorkflowStatus.FAILED, "采集失败")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'workflow_id': self.workflow_id,
            'source_name': self.source_name,
            'source_url': self.source_url,
            'source_type': self.source_type,
            'current_stage': self.current_stage.value,
            'overall_status': self.overall_status.value,
            'can_proceed': self.can_proceed,
            'requires_manual_review': self.requires_manual_review,
            'validation_result': {
                'stage': self.validation_result.stage.value if self.validation_result else None,
                'status': self.validation_result.status.value if self.validation_result else None,
                'message': self.validation_result.message if self.validation_result else None,
                'errors': self.validation_result.errors if self.validation_result else [],
                'warnings': self.validation_result.warnings if self.validation_result else [],
                'duration_seconds': self.validation_result.duration_seconds() if self.validation_result else 0,
            } if self.validation_result else None,
            'collection_result': {
                'stage': self.collection_result.stage.value if self.collection_result else None,
                'status': self.collection_result.status.value if self.collection_result else None,
                'message': self.collection_result.message if self.collection_result else None,
                'data': self.collection_result.data if self.collection_result else None,
                'errors': self.collection_result.errors if self.collection_result else [],
                'duration_seconds': self.collection_result.duration_seconds() if self.collection_result else 0,
            } if self.collection_result else None,
            'can_proceed': self.can_proceed,
            'requires_manual_review': self.requires_manual_review,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'metadata': self.metadata,
        }


class DualStageCollectionWorkflow:
    """
    双阶段采集工作流管理器

    Stage 1: 验证阶段
    - 合规性验证（robots.txt、授权、隐私政策）
    - 技术可行性验证（URL可访问性、反爬机制、页面结构）
    - 数据质量预验证（字段完整性、内容质量、格式标准）

    Stage 2: 采集阶段
    - 执行正式数据采集
    - URL有效性验证（采集前验证每个URL）
    - 数据完整性校验
    """

    def __init__(self):
        self.workflows: Dict[str, CollectionWorkflow] = {}
        self._validator = None

    def _get_validator(self):
        if self._validator is None:
            from .data_source_validator import DataSourceValidator
            self._validator = DataSourceValidator()
        return self._validator

    async def execute_workflow(
        self,
        workflow_id: str,
        source_name: str,
        source_url: str,
        source_type: str = "unknown",
        collection_func: Optional[Callable] = None,
        collection_params: Optional[Dict[str, Any]] = None,
        skip_validation: bool = False,
        **kwargs
    ) -> CollectionWorkflow:
        """
        执行双阶段工作流

        Args:
            workflow_id: 工作流ID
            source_name: 数据源名称
            source_url: 数据源URL
            source_type: 数据源类型
            collection_func: 采集函数（异步）
            collection_params: 采集参数
            skip_validation: 是否跳过验证（仅用于测试）

        Returns:
            CollectionWorkflow: 工作流结果
        """
        workflow = CollectionWorkflow(
            workflow_id=workflow_id,
            source_name=source_name,
            source_url=source_url,
            source_type=source_type,
            metadata=kwargs
        )
        self.workflows[workflow_id] = workflow

        workflow.update_status(WorkflowStage.VALIDATION, WorkflowStatus.RUNNING, "开始验证")

        if skip_validation:
            workflow.can_proceed = True
            workflow.mark_validation_passed(StageResult(
                stage=WorkflowStage.VALIDATION,
                status=WorkflowStatus.COMPLETED,
                message="跳过验证（测试模式）"
            ))
        else:
            await self._execute_validation(workflow)

        if not workflow.can_proceed:
            logger.warning(f"工作流 {workflow_id} 验证未通过，终止")
            return workflow

        if workflow.requires_manual_review:
            logger.info(f"工作流 {workflow_id} 需要人工审核")
            return workflow

        if collection_func is None:
            logger.info(f"工作流 {workflow_id} 验证通过，但未提供采集函数")
            workflow.update_status(WorkflowStage.COMPLETED, WorkflowStatus.COMPLETED, "验证通过，待采集")
            return workflow

        workflow.mark_collection_started()

        try:
            params = collection_params or {}
            result_data = await collection_func(**params)

            workflow.mark_collection_passed(StageResult(
                stage=WorkflowStage.COLLECTION,
                status=WorkflowStatus.COMPLETED,
                message=f"采集完成，获取 {len(result_data) if result_data else 0} 条数据",
                data=result_data
            ))

        except Exception as e:
            logger.error(f"工作流 {workflow_id} 采集失败: {str(e)}")
            workflow.mark_collection_failed(StageResult(
                stage=WorkflowStage.COLLECTION,
                status=WorkflowStatus.FAILED,
                message=f"采集失败: {str(e)}",
                errors=[str(e)]
            ))

        return workflow

    async def _execute_validation(self, workflow: CollectionWorkflow):
        """执行验证阶段"""
        start_time = datetime.now().isoformat()

        try:
            validator = self._get_validator()
            report = await validator.validate_async(
                source_name=workflow.source_name,
                source_url=workflow.source_url
            )

            errors = []
            for result in report.compliance_results + report.technical_results + report.quality_results:
                if not result.passed:
                    errors.append(f"{result.item}: {result.message}")

            warnings = report.warnings.copy()

            stage_result = StageResult(
                stage=WorkflowStage.VALIDATION,
                status=WorkflowStatus.COMPLETED if report.overall_passed else WorkflowStatus.FAILED,
                message="验证通过" if report.overall_passed else "验证未通过",
                data=report.get_summary(),
                warnings=warnings,
                errors=errors,
                start_time=start_time,
                end_time=datetime.now().isoformat()
            )

            if report.overall_passed:
                workflow.mark_validation_passed(stage_result)
            else:
                workflow.mark_validation_failed(stage_result)

        except Exception as e:
            logger.error(f"验证执行失败: {str(e)}")
            workflow.mark_validation_failed(StageResult(
                stage=WorkflowStage.VALIDATION,
                status=WorkflowStatus.FAILED,
                message=f"验证执行失败: {str(e)}",
                errors=[str(e)],
                start_time=start_time,
                end_time=datetime.now().isoformat()
            ))

    def get_workflow(self, workflow_id: str) -> Optional[CollectionWorkflow]:
        return self.workflows.get(workflow_id)

    def list_workflows(self, status: Optional[WorkflowStatus] = None) -> List[CollectionWorkflow]:
        if status is None:
            return list(self.workflows.values())
        return [w for w in self.workflows.values() if w.overall_status == status]


workflow_manager = DualStageCollectionWorkflow()
