"""
自动优化引擎

功能：
- 根据历史失败记录优化执行策略
- 动态调整重试次数和超时时间
- 智能选择备用方案
- 系统健康监控和预警

使用示例：
    optimizer = AutoOptimizer()

    # 获取优化后的参数
    params = optimizer.get_optimized_params('collect', error_history)

    # 获取健康检查结果
    health = optimizer.check_system_health()

    # 获取优化建议
    suggestions = optimizer.get_optimization_suggestions()
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """系统健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class OptimizationStrategy(Enum):
    """优化策略"""
    AGGRESSIVE = "aggressive"      # 激进策略：多重试、快超时
    BALANCED = "balanced"         # 平衡策略
    CONSERVATIVE = "conservative"  # 保守策略：少重试、长超时


@dataclass
class OptimizationConfig:
    """优化配置"""
    max_retries: int = 3
    timeout_seconds: int = 30
    retry_delay_base: float = 1.0
    retry_delay_max: float = 30.0
    use_backup_first: bool = False
    confidence_threshold: float = 0.8
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    services: Dict[str, bool]
    issues: List[str]
    recommendations: List[str]
    checked_at: str


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    priority: str
    category: str
    issue: str
    current_value: Any
    suggested_value: Any
    reason: str
    expected_improvement: str


class AutoOptimizer:
    """
    自动优化引擎

    核心功能：
    1. 参数优化 - 根据历史数据动态调整超时、重试等参数
    2. 健康监控 - 检查各服务组件状态
    3. 智能建议 - 基于统计分析给出优化建议
    4. 策略调整 - 根据错误趋势调整优化策略
    """

    DEFAULT_CONFIGS: Dict[str, OptimizationConfig] = {
        "collect": OptimizationConfig(
            max_retries=3,
            timeout_seconds=30,
            strategy=OptimizationStrategy.BALANCED
        ),
        "match": OptimizationConfig(
            max_retries=2,
            timeout_seconds=20,
            strategy=OptimizationStrategy.CONSERVATIVE
        ),
        "generate": OptimizationConfig(
            max_retries=3,
            timeout_seconds=60,
            strategy=OptimizationStrategy.AGGRESSIVE
        ),
        "review": OptimizationConfig(
            max_retries=2,
            timeout_seconds=45,
            strategy=OptimizationStrategy.BALANCED
        ),
        "upload": OptimizationConfig(
            max_retries=5,
            timeout_seconds=120,
            strategy=OptimizationStrategy.CONSERVATIVE
        ),
        "track": OptimizationConfig(
            max_retries=2,
            timeout_seconds=15,
            strategy=OptimizationStrategy.BALANCED
        ),
    }

    def __init__(self):
        """初始化优化器"""
        self._configs: Dict[str, OptimizationConfig] = {}
        self._error_history: List[Dict] = []
        self._max_history = 1000
        self._last_optimization: Optional[str] = None
        self._strategy_adjustment_threshold = 5

        for stage, config in self.DEFAULT_CONFIGS.items():
            self._configs[stage] = config

        logger.info("AutoOptimizer initialized")

    def get_optimized_params(
        self,
        stage: str,
        error_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        根据历史错误优化参数

        Args:
            stage: 工作流阶段
            error_history: 最近的错误历史

        Returns:
            Dict: 优化后的参数
        """
        config = self._configs.get(stage, OptimizationConfig())

        params = {
            "max_retries": config.max_retries,
            "timeout": config.timeout_seconds,
            "retry_delay_base": config.retry_delay_base,
            "retry_delay_max": config.retry_delay_max,
            "use_backup_first": config.use_backup_first,
            "strategy": config.strategy.value
        }

        if error_history:
            params.update(self._analyze_and_adjust(stage, config, error_history))

        return params

    def _analyze_and_adjust(
        self,
        stage: str,
        config: OptimizationConfig,
        error_history: List[Dict]
    ) -> Dict[str, Any]:
        """分析错误历史并调整参数"""
        adjustments = {}

        if not error_history:
            return adjustments

        recent_errors = error_history[-10:]

        timeout_errors = sum(
            1 for e in recent_errors
            if "timeout" in str(e.get("error_message", "")).lower()
        )

        if timeout_errors >= 3:
            new_timeout = min(config.timeout_seconds * 1.5, 300)
            adjustments["timeout_seconds"] = int(new_timeout)
            logger.info(f"[{stage}] Timeout increased to {new_timeout}s due to {timeout_errors} timeout errors")

        network_errors = sum(
            1 for e in recent_errors
            if "network" in str(e.get("error_type", "")).lower() or "conn" in str(e.get("error_message", "")).lower()
        )

        if network_errors >= 3:
            adjustments["use_backup_first"] = True
            logger.info(f"[{stage}] Enabled backup source due to {network_errors} network errors")

        retry_errors = sum(
            1 for e in recent_errors
            if "retry" in str(e.get("solution", "")).lower()
        )

        if retry_errors >= 5 and config.max_retries < 5:
            adjustments["max_retries"] = config.max_retries + 1
            logger.info(f"[{stage}] Increased retries to {config.max_retries + 1}")

        return adjustments

    def check_system_health(self) -> HealthCheckResult:
        """
        检查系统健康状态

        Returns:
            HealthCheckResult: 健康检查结果
        """
        services = {}
        issues = []
        recommendations = []

        services["database"] = self._check_database()
        if not services["database"]:
            issues.append("数据库连接失败")
            recommendations.append("检查PostgreSQL服务状态")

        services["cache"] = self._check_cache()
        if not services["cache"]:
            issues.append("缓存服务不可用")
            recommendations.append("检查Redis服务状态")

        services["vector_db"] = self._check_vector_db()
        if not services["vector_db"]:
            issues.append("向量数据库不可用")
            recommendations.append("检查Chroma/Milvus服务状态")

        services["llm_service"] = self._check_llm_service()
        if not services["llm_service"]:
            issues.append("LLM服务不可用")
            recommendations.append("检查Ollama服务状态")

        services["crawler"] = self._check_crawler()
        if not services["crawler"]:
            issues.append("爬虫服务异常")
            recommendations.append("检查代理池和浏览器配置")

        healthy_count = sum(1 for v in services.values() if v)
        total_count = len(services)

        if healthy_count == total_count:
            status = HealthStatus.HEALTHY
        elif healthy_count >= total_count * 0.6:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        return HealthCheckResult(
            status=status,
            services=services,
            issues=issues,
            recommendations=recommendations,
            checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def _check_database(self) -> bool:
        """检查数据库连接"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    def _check_cache(self) -> bool:
        """检查缓存服务"""
        try:
            from django.core.cache import cache
            cache.set("health_check", "ok", 10)
            return cache.get("health_check") == "ok"
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            return False

    def _check_vector_db(self) -> bool:
        """检查向量数据库"""
        try:
            from chroma_api import chroma_client
            chroma_client.heartbeat()
            return True
        except Exception:
            return False

    def _check_llm_service(self) -> bool:
        """检查LLM服务"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _check_crawler(self) -> bool:
        """检查爬虫服务"""
        try:
            from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
            return True
        except Exception as e:
            logger.warning(f"Crawler health check failed: {e}")
            return False

    def get_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        """
        获取系统优化建议

        Returns:
            List[OptimizationSuggestion]: 优化建议列表
        """
        suggestions = []

        try:
            from services.failure_knowledge_base import failure_knowledge_base

            frequent_errors = failure_knowledge_base.get_frequent_errors(top_n=5)

            for error in frequent_errors:
                if error.get("total_count", 0) >= 3:
                    error_type = error.get("error_type", "")

                    if "timeout" in error_type.lower():
                        suggestions.append(OptimizationSuggestion(
                            priority="high" if error.get("total_count", 0) >= 5 else "medium",
                            category="performance",
                            issue=f"超时错误频繁发生 ({error.get('total_count')}次)",
                            current_value="当前超时设置可能不足",
                            suggested_value="增加超时时间或启用备用数据源",
                            reason=error.get("root_cause", ""),
                            expected_improvement="减少超时导致的失败"
                        ))

                    elif "network" in error_type.lower():
                        suggestions.append(OptimizationSuggestion(
                            priority="high",
                            category="reliability",
                            issue=f"网络错误频繁发生 ({error.get('total_count')}次)",
                            current_value="单一网络配置",
                            suggested_value="启用多代理池和自动切换",
                            reason=error.get("root_cause", ""),
                            expected_improvement="提高网络请求成功率"
                        ))

                    elif "llm" in error_type.lower():
                        suggestions.append(OptimizationSuggestion(
                            priority="medium",
                            category="ai",
                            issue=f"LLM调用错误频繁发生 ({error.get('total_count')}次)",
                            current_value="单一LLM模型",
                            suggested_value="配置多模型降级方案",
                            reason=error.get("root_cause", ""),
                            expected_improvement="提高AI任务成功率"
                        ))

            health = self.check_system_health()
            if health.status != HealthStatus.HEALTHY:
                for recommendation in health.recommendations:
                    suggestions.append(OptimizationSuggestion(
                        priority="high",
                        category="infrastructure",
                        issue=f"系统{health.status.value}: {recommendation}",
                        current_value="服务异常",
                        suggested_value="检查并修复服务",
                        reason="健康检查失败",
                        expected_improvement="恢复正常服务"
                    ))

        except Exception as e:
            logger.error(f"Failed to generate optimization suggestions: {e}")

        suggestions.sort(key=lambda x: (x.priority == "medium", x.priority == "high"))

        return suggestions[:10]

    def adjust_strategy(self, stage: str, success_rate: float) -> OptimizationStrategy:
        """
        根据成功率调整优化策略

        Args:
            stage: 工作流阶段
            success_rate: 最近的成功率 (0-1)

        Returns:
            OptimizationStrategy: 调整后的策略
        """
        config = self._configs.get(stage)
        if not config:
            return OptimizationStrategy.BALANCED

        if success_rate >= 0.9:
            new_strategy = OptimizationStrategy.CONSERVATIVE
            logger.info(f"[{stage}] Success rate high ({success_rate:.1%}), switching to conservative strategy")
        elif success_rate >= 0.7:
            new_strategy = OptimizationStrategy.BALANCED
            logger.info(f"[{stage}] Success rate moderate ({success_rate:.1%}), keeping balanced strategy")
        else:
            new_strategy = OptimizationStrategy.AGGRESSIVE
            logger.info(f"[{stage}] Success rate low ({success_rate:.1%}), switching to aggressive strategy")

        config.strategy = new_strategy
        return new_strategy

    def record_error(self, error_info: Dict[str, Any]):
        """
        记录错误用于后续分析

        Args:
            error_info: 错误信息字典
        """
        error_info["recorded_at"] = datetime.now().isoformat()
        self._error_history.append(error_info)

        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]

    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        获取错误趋势统计

        Args:
            days: 统计天数

        Returns:
            Dict: 趋势统计
        """
        cutoff = datetime.now() - timedelta(days=days)

        recent_errors = [
            e for e in self._error_history
            if datetime.fromisoformat(e.get("recorded_at", datetime.now().isoformat())) > cutoff
        ]

        total = len(recent_errors)
        if total == 0:
            return {
                "period_days": days,
                "total_errors": 0,
                "by_type": {},
                "trend": "no_data"
            }

        by_type: Dict[str, int] = {}
        for error in recent_errors:
            error_type = error.get("error_type", "unknown")
            by_type[error_type] = by_type.get(error_type, 0) + 1

        sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
        most_common = sorted_types[0] if sorted_types else ("none", 0)

        trend = "increasing" if len(recent_errors) > 10 else "stable" if len(recent_errors) > 5 else "decreasing"

        return {
            "period_days": days,
            "total_errors": total,
            "by_type": by_type,
            "most_common_error": {"type": most_common[0], "count": most_common[1]},
            "trend": trend
        }

    def get_stage_config(self, stage: str) -> OptimizationConfig:
        """获取指定阶段的优化配置"""
        return self._configs.get(stage, OptimizationConfig())

    def update_stage_config(self, stage: str, config: OptimizationConfig):
        """更新指定阶段的优化配置"""
        self._configs[stage] = config
        logger.info(f"Updated config for stage '{stage}': max_retries={config.max_retries}, timeout={config.timeout_seconds}s")

    def reset_to_defaults(self, stage: Optional[str] = None):
        """重置配置到默认值"""
        if stage:
            self._configs[stage] = self.DEFAULT_CONFIGS.get(stage, OptimizationConfig())
            logger.info(f"Reset config for stage '{stage}'")
        else:
            for stage_name, config in self.DEFAULT_CONFIGS.items():
                self._configs[stage_name] = config
            logger.info("Reset all stage configs to defaults")


auto_optimizer = AutoOptimizer()
