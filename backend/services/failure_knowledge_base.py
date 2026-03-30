"""
失败知识库模块

功能：
- 记录所有失败案例
- 统计高频错误
- 提供已知解决方案查询
- 建议系统优化

使用示例：
    kb = FailureKnowledgeBase()

    # 记录失败
    kb.record_failure(
        error_type="llm_error",
        error_message="connection refused to ollama",
        stage="generate",
        root_cause="Ollama服务不可用",
        solution="启动Ollama服务: ollama serve",
        workflow_id="xxx-xxx"
    )

    # 查询已知解决方案
    solution = kb.get_solution_for_error("llm_error", "Ollama服务不可用")

    # 获取高频错误
    frequent = kb.get_frequent_errors(top_n=5)
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FailureRecord:
    """失败记录"""
    id: str
    error_type: str
    error_message: str
    stage: str
    root_cause: str
    solution_applied: str
    success: bool
    workflow_id: str
    retry_count: int = 0
    created_at: str = ""
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FailureRecord':
        """从字典创建"""
        return cls(**data)


@dataclass
class ErrorStatistics:
    """错误统计"""
    error_type: str
    root_cause: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    last_occurrence: str = ""
    common_solution: str = ""

    def update(self, success: bool):
        """更新统计"""
        self.total_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.success_rate = self.success_count / self.total_count if self.total_count > 0 else 0.0
        self.last_occurrence = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class FailureKnowledgeBase:
    """
    失败知识库

    核心功能：
    1. 失败记录存储 - 持久化存储所有失败案例
    2. 解决方案查询 - 根据错误类型和根因查找已知解决方案
    3. 统计分析 - 统计高频错误、成功率等
    4. 优化建议 - 基于历史数据提供系统优化建议
    """

    def __init__(self, storage_path: str = None):
        """
        初始化知识库

        Args:
            storage_path: 存储文件路径，默认使用 logs/failure_knowledge_base.json
        """
        if storage_path is None:
            base_dir = Path(__file__).parent.parent
            storage_path = base_dir / "logs" / "failure_knowledge_base.json"

        self.storage_path = Path(storage_path)
        self.failures: List[FailureRecord] = []
        self._statistics: Dict[str, ErrorStatistics] = {}
        self._max_records = 10000
        self._min_success_rate = 0.6

        self._ensure_storage_dir()
        self._load()

        logger.info(f"FailureKnowledgeBase initialized with {len(self.failures)} records")

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        """从磁盘加载知识库"""
        if not self.storage_path.exists():
            logger.info("No existing knowledge base found, starting fresh")
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.failures = [FailureRecord.from_dict(r) for r in data.get('failures', [])]
            self._rebuild_statistics()

            logger.info(f"Loaded {len(self.failures)} records from knowledge base")
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            self.failures = []

    def _save(self):
        """保存知识库到磁盘"""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'failures': [r.to_dict() for r in self.failures]
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(self.failures)} records to knowledge base")
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")

    def _rebuild_statistics(self):
        """重建统计信息"""
        self._statistics.clear()

        for record in self.failures:
            key = self._make_key(record.error_type, record.root_cause)

            if key not in self._statistics:
                self._statistics[key] = ErrorStatistics(
                    error_type=record.error_type,
                    root_cause=record.root_cause
                )

            self._statistics[key].update(record.success)

            if record.success and not self._statistics[key].common_solution:
                self._statistics[key].common_solution = record.solution_applied

    def _make_key(self, error_type: str, root_cause: str) -> str:
        """生成统计键"""
        return f"{error_type}:{root_cause}"

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"FR{datetime.now().strftime('%Y%m%d%H%M%S')}{datetime.now().microsecond % 1000:03d}"

    def record_failure(
        self,
        error_type: str,
        error_message: str,
        stage: str,
        root_cause: str,
        solution: str,
        workflow_id: str,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录一个新的失败案例

        Args:
            error_type: 错误类型
            error_message: 错误原始消息
            stage: 工作流阶段
            root_cause: 根本原因
            solution: 应用的解决方案
            workflow_id: 工作流ID
            retry_count: 重试次数
            metadata: 额外元数据

        Returns:
            str: 记录ID
        """
        record = FailureRecord(
            id=self._generate_id(),
            error_type=error_type,
            error_message=error_message[:500] if error_message else "",
            stage=stage,
            root_cause=root_cause,
            solution_applied=solution,
            success=False,
            workflow_id=workflow_id,
            retry_count=retry_count,
            metadata=metadata or {}
        )

        self.failures.append(record)

        key = self._make_key(error_type, root_cause)
        if key not in self._statistics:
            self._statistics[key] = ErrorStatistics(
                error_type=error_type,
                root_cause=root_cause
            )
        self._statistics[key].update(False)

        self._trim_old_records()
        self._save()

        logger.info(f"Recorded failure: {record.id} - {error_type}: {root_cause}")
        return record.id

    def record_success(
        self,
        failure_id: str,
        final_solution: Optional[str] = None
    ) -> bool:
        """
        标记一个失败案例已解决

        Args:
            failure_id: 失败记录ID
            final_solution: 最终使用的解决方案

        Returns:
            bool: 是否成功更新
        """
        for record in self.failures:
            if record.id == failure_id:
                record.success = True
                record.resolved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if final_solution:
                    record.solution_applied = final_solution

                key = self._make_key(record.error_type, record.root_cause)
                if key in self._statistics:
                    self._statistics[key].update(True)
                    if final_solution:
                        self._statistics[key].common_solution = final_solution

                self._save()
                logger.info(f"Recorded success for failure: {failure_id}")
                return True

        return False

    def record_success_by_context(
        self,
        error_type: str,
        root_cause: str,
        final_solution: str
    ) -> int:
        """
        根据错误上下文标记最新记录为成功

        Args:
            error_type: 错误类型
            root_cause: 根本原因
            final_solution: 最终解决方案

        Returns:
            int: 更新的记录数
        """
        updated = 0

        for record in reversed(self.failures):
            if (record.error_type == error_type and
                record.root_cause == root_cause and
                not record.success):

                record.success = True
                record.resolved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                record.solution_applied = final_solution
                updated += 1

                key = self._make_key(error_type, root_cause)
                if key in self._statistics:
                    self._statistics[key].update(True)
                    self._statistics[key].common_solution = final_solution

        if updated > 0:
            self._save()
            logger.info(f"Recorded success for {updated} failures: {error_type}: {root_cause}")

        return updated

    def _trim_old_records(self):
        """裁剪旧记录，保持知识库大小"""
        if len(self.failures) > self._max_records:
            kept_count = self._max_records // 2
            self.failures = self.failures[-kept_count:]
            logger.info(f"Trimmed knowledge base to {kept_count} records")

    def get_solution_for_error(
        self,
        error_type: str,
        root_cause: str
    ) -> Optional[str]:
        """
        根据错误类型和根因获取已知解决方案

        Args:
            error_type: 错误类型
            root_cause: 根本原因

        Returns:
            str: 已知的成功解决方案，如果没有则返回None
        """
        key = self._make_key(error_type, root_cause)

        if key in self._statistics:
            stats = self._statistics[key]
            if stats.success_rate >= self._min_success_rate and stats.common_solution:
                logger.debug(f"Found known solution for {key}: {stats.common_solution}")
                return stats.common_solution

        for record in reversed(self.failures):
            if (record.error_type == error_type and
                record.root_cause == root_cause and
                record.success):

                logger.debug(f"Found solution from record {record.id}")
                return record.solution_applied

        return None

    def get_frequent_errors(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        获取高频错误统计

        Args:
            top_n: 返回前N个

        Returns:
            List[Dict]: 高频错误列表
        """
        sorted_stats = sorted(
            self._statistics.values(),
            key=lambda x: x.total_count,
            reverse=True
        )

        return [
            {
                'error_type': s.error_type,
                'root_cause': s.root_cause,
                'total_count': s.total_count,
                'success_count': s.success_count,
                'failure_count': s.failure_count,
                'success_rate': round(s.success_rate * 100, 1),
                'last_occurrence': s.last_occurrence,
                'common_solution': s.common_solution
            }
            for s in sorted_stats[:top_n]
        ]

    def get_recent_failures(
        self,
        limit: int = 20,
        only_unsolved: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取最近的失败记录

        Args:
            limit: 返回数量限制
            only_unsolved: 只返回未解决的

        Returns:
            List[Dict]: 失败记录列表
        """
        failures = self.failures

        if only_unsolved:
            failures = [f for f in failures if not f.success]

        recent = sorted(failures, key=lambda x: x.created_at, reverse=True)[:limit]

        return [r.to_dict() for r in recent]

    def get_error_trend(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取错误趋势统计

        Args:
            days: 统计天数

        Returns:
            Dict: 趋势统计
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        recent_failures = [
            f for f in self.failures
            if datetime.strptime(f.created_at, '%Y-%m-%d %H:%M:%S').timestamp() > cutoff
        ]

        total = len(recent_failures)
        solved = sum(1 for f in recent_failures if f.success)
        unsolved = total - solved

        by_type: Dict[str, int] = {}
        by_stage: Dict[str, int] = {}

        for f in recent_failures:
            by_type[f.error_type] = by_type.get(f.error_type, 0) + 1
            by_stage[f.stage] = by_stage.get(f.stage, 0) + 1

        return {
            'period_days': days,
            'total_failures': total,
            'solved': solved,
            'unsolved': unsolved,
            'solve_rate': round(solved / total * 100, 1) if total > 0 else 0,
            'by_error_type': by_type,
            'by_stage': by_stage
        }

    def suggest_improvements(self) -> List[Dict[str, Any]]:
        """
        基于历史数据建议系统优化

        Returns:
            List[Dict]: 优化建议列表
        """
        suggestions = []

        for key, stats in self._statistics.items():
            if stats.total_count >= 3 and stats.success_rate < 0.5:
                suggestions.append({
                    'priority': 'high' if stats.total_count >= 5 else 'medium',
                    'error_type': stats.error_type,
                    'root_cause': stats.root_cause,
                    'occurrence_count': stats.total_count,
                    'current_success_rate': round(stats.success_rate * 100, 1),
                    'suggestion': self._generate_suggestion(stats)
                })

        suggestions.sort(key=lambda x: (x['priority'] == 'medium', -x['occurrence_count']))

        return suggestions[:10]

    def _generate_suggestion(self, stats: ErrorStatistics) -> str:
        """生成针对特定错误的建议"""
        if stats.success_rate < 0.3:
            return f"该错误已发生{stats.total_count}次但解决率仅{stats.success_rate*100:.0f}%，建议添加自动修复逻辑或更新解决方案库"
        elif stats.success_rate < 0.5:
            return f"该错误解决率偏低({stats.success_rate*100:.0f}%)，建议优化当前的解决方案"
        else:
            return "建议监控该错误的最新趋势"

    def clear_old_records(self, days: int = 90) -> int:
        """
        清理旧记录

        Args:
            days: 保留最近N天的记录

        Returns:
            int: 删除的记录数
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        original_count = len(self.failures)

        self.failures = [
            f for f in self.failures
            if datetime.strptime(f.created_at, '%Y-%m-%d %H:%M:%S').timestamp() > cutoff
        ]

        deleted = original_count - len(self.failures)

        if deleted > 0:
            self._rebuild_statistics()
            self._save()
            logger.info(f"Cleared {deleted} old records")

        return deleted

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """
        获取知识库摘要

        Returns:
            Dict: 摘要信息
        """
        total = len(self.failures)
        solved = sum(1 for f in self.failures if f.success)
        unsolved = total - solved

        return {
            'total_records': total,
            'solved_records': solved,
            'unsolved_records': unsolved,
            'solve_rate': round(solved / total * 100, 1) if total > 0 else 0,
            'unique_error_types': len(set(f.error_type for f in self.failures)),
            'unique_root_causes': len(self._statistics),
            'storage_path': str(self.storage_path),
            'last_updated': self.failures[-1].created_at if self.failures else None
        }


failure_knowledge_base = FailureKnowledgeBase()
