"""
全自动化配置服务
提供统一的配置获取接口，供工作流和定时任务调用
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from apps.openclaw.models import (
    AutomationConfig, AIDecisionConfig, AutoMatchConfig,
    DocumentReviewConfig, RiskControlConfig, CrawlConfig, NotificationConfig
)

logger = logging.getLogger(__name__)


@dataclass
class AIDecisionParams:
    """AI决策参数"""
    QUALIFICATION_WEIGHT: float = 0.4
    COMPETITOR_WEIGHT: float = 0.2
    PERFORMANCE_WEIGHT: float = 0.2
    RISK_WEIGHT: float = 0.2
    AUTO_BID_THRESHOLD: int = 60
    OBSERVATION_THRESHOLD: int = 40
    SKIP_THRESHOLD: int = 40
    USE_AI_DECISION: bool = True


@dataclass
class AutoMatchParams:
    """自动匹配参数"""
    AUTO_MATCH_ENABLED: bool = True
    AUTO_IMPORT_THRESHOLD: float = 0.8
    AUTO_BID_MATCH_THRESHOLD: float = 0.6
    EXCLUDE_THRESHOLD: float = 0.6
    ADAPTIVE_THRESHOLD: bool = True
    LEARNING_FROM_HISTORY: bool = True
    KEYWORD_BOOST_ENABLED: bool = True
    REGION_BOOST_ENABLED: bool = True


@dataclass
class DocumentReviewParams:
    """文档审核参数"""
    AUTO_UPLOAD_THRESHOLD: int = 90
    OBSERVATION_THRESHOLD: int = 60
    MANUAL_REVIEW_THRESHOLD: int = 60
    MAX_OPTIMIZATION_ROUNDS: int = 3
    ENABLE_ANTI_REJECTION_CHECK: bool = True
    ENABLE_PRICE_ANALYSIS: bool = True
    USE_SIMULATED_SCORING: bool = True


@dataclass
class RiskControlParams:
    """风险控制参数"""
    MAX_DAILY_BIDS: int = 50
    AMOUNT_THRESHOLD: float = 1000000
    CONSECUTIVE_FAILURES: int = 3
    ENABLE_AMOUNT_CHECK: bool = True
    ENABLE_COUNT_CHECK: bool = True
    ENABLE_FAILURE_CHECK: bool = True
    AUTO_PAUSE_ON_RISK: bool = True
    NOTIFY_ON_RISK: bool = True


@dataclass
class CrawlParams:
    """采集参数"""
    AUTO_LEARN_KEYWORDS: bool = True
    ADAPTIVE_CRAWL_MODE: bool = True
    MULTI_SOURCE_ENABLED: bool = True
    DEFAULT_CRAWL_INTERVAL: int = 60
    MAX_PAGES_PER_CRAWL: int = 50
    ENABLE_DEDUP: bool = True


@dataclass
class NotificationParams:
    """通知参数"""
    NOTIFICATION_ENABLED: bool = True
    DINGTALK_ENABLED: bool = True
    KEY_EVENTS_ONLY: bool = False
    DAILY_REPORT_ENABLED: bool = True
    WEEKLY_REPORT_ENABLED: bool = False
    NOTIFY_ON_START: bool = False
    NOTIFY_ON_SUCCESS: bool = True
    NOTIFY_ON_FAILURE: bool = True
    NOTIFY_ON_WIN: bool = True
    NOTIFY_ON_LOSS: bool = True


class AutomationConfigService:
    """
    全自动化配置服务
    提供配置获取、更新、验证等方法
    """
    _instance = None
    _cache = {}
    _cache_timeout = 300

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_default_config(self) -> Optional[AutomationConfig]:
        """
        获取默认配置
        """
        try:
            config = AutomationConfig.objects.filter(
                is_default=True,
                is_active=True
            ).first()

            if not config:
                config = AutomationConfig.objects.filter(is_active=True).first()

            return config
        except Exception as e:
            logger.error(f"获取默认配置失败: {e}")
            return None

    def get_all_params(self, config_id: int = None) -> Dict[str, Any]:
        """
        获取所有配置参数
        """
        config = None

        if config_id:
            try:
                config = AutomationConfig.objects.get(id=config_id)
            except AutomationConfig.DoesNotExist:
                pass

        if not config:
            config = self.get_default_config()

        if not config:
            return self._get_default_params()

        return {
            'decision': self.get_decision_params(config),
            'match': self.get_match_params(config),
            'review': self.get_review_params(config),
            'risk': self.get_risk_params(config),
            'crawl': self.get_crawl_params(config),
            'notification': self.get_notification_params(config)
        }

    def get_decision_params(self, config: AutomationConfig = None) -> AIDecisionParams:
        """
        获取AI决策参数
        """
        if not config:
            config = self.get_default_config()

        if not config:
            return AIDecisionParams()

        try:
            decision_config = config.decision_configs.first()
            if decision_config:
                return AIDecisionParams(
                    QUALIFICATION_WEIGHT=decision_config.QUALIFICATION_WEIGHT,
                    COMPETITOR_WEIGHT=decision_config.COMPETITOR_WEIGHT,
                    PERFORMANCE_WEIGHT=decision_config.PERFORMANCE_WEIGHT,
                    RISK_WEIGHT=decision_config.RISK_WEIGHT,
                    AUTO_BID_THRESHOLD=decision_config.AUTO_BID_THRESHOLD,
                    OBSERVATION_THRESHOLD=decision_config.OBSERVATION_THRESHOLD,
                    SKIP_THRESHOLD=decision_config.SKIP_THRESHOLD,
                    USE_AI_DECISION=decision_config.USE_AI_DECISION
                )
        except Exception as e:
            logger.error(f"获取AI决策参数失败: {e}")

        return AIDecisionParams()

    def get_match_params(self, config: AutomationConfig = None) -> AutoMatchParams:
        """
        获取自动匹配参数
        """
        if not config:
            config = self.get_default_config()

        if not config:
            return AutoMatchParams()

        try:
            match_config = config.match_configs.first()
            if match_config:
                return AutoMatchParams(
                    AUTO_MATCH_ENABLED=match_config.AUTO_MATCH_ENABLED,
                    AUTO_IMPORT_THRESHOLD=match_config.AUTO_IMPORT_THRESHOLD,
                    AUTO_BID_MATCH_THRESHOLD=match_config.AUTO_BID_MATCH_THRESHOLD,
                    EXCLUDE_THRESHOLD=match_config.EXCLUDE_THRESHOLD,
                    ADAPTIVE_THRESHOLD=match_config.ADAPTIVE_THRESHOLD,
                    LEARNING_FROM_HISTORY=match_config.LEARNING_FROM_HISTORY,
                    KEYWORD_BOOST_ENABLED=match_config.KEYWORD_BOOST_ENABLED,
                    REGION_BOOST_ENABLED=match_config.REGION_BOOST_ENABLED
                )
        except Exception as e:
            logger.error(f"获取自动匹配参数失败: {e}")

        return AutoMatchParams()

    def get_review_params(self, config: AutomationConfig = None) -> DocumentReviewParams:
        """
        获取文档审核参数
        """
        if not config:
            config = self.get_default_config()

        if not config:
            return DocumentReviewParams()

        try:
            review_config = config.review_configs.first()
            if review_config:
                return DocumentReviewParams(
                    AUTO_UPLOAD_THRESHOLD=review_config.AUTO_UPLOAD_THRESHOLD,
                    OBSERVATION_THRESHOLD=review_config.OBSERVATION_THRESHOLD,
                    MANUAL_REVIEW_THRESHOLD=review_config.MANUAL_REVIEW_THRESHOLD,
                    MAX_OPTIMIZATION_ROUNDS=review_config.MAX_OPTIMIZATION_ROUNDS,
                    ENABLE_ANTI_REJECTION_CHECK=review_config.ENABLE_ANTI_REJECTION_CHECK,
                    ENABLE_PRICE_ANALYSIS=review_config.ENABLE_PRICE_ANALYSIS,
                    USE_SIMULATED_SCORING=review_config.USE_SIMULATED_SCORING
                )
        except Exception as e:
            logger.error(f"获取文档审核参数失败: {e}")

        return DocumentReviewParams()

    def get_risk_params(self, config: AutomationConfig = None) -> RiskControlParams:
        """
        获取风险控制参数
        """
        if not config:
            config = self.get_default_config()

        if not config:
            return RiskControlParams()

        try:
            risk_config = config.risk_configs.first()
            if risk_config:
                return RiskControlParams(
                    MAX_DAILY_BIDS=risk_config.MAX_DAILY_BIDS,
                    AMOUNT_THRESHOLD=float(risk_config.AMOUNT_THRESHOLD),
                    CONSECUTIVE_FAILURES=risk_config.CONSECUTIVE_FAILURES,
                    ENABLE_AMOUNT_CHECK=risk_config.ENABLE_AMOUNT_CHECK,
                    ENABLE_COUNT_CHECK=risk_config.ENABLE_COUNT_CHECK,
                    ENABLE_FAILURE_CHECK=risk_config.ENABLE_FAILURE_CHECK,
                    AUTO_PAUSE_ON_RISK=risk_config.AUTO_PAUSE_ON_RISK,
                    NOTIFY_ON_RISK=risk_config.NOTIFY_ON_RISK
                )
        except Exception as e:
            logger.error(f"获取风险控制参数失败: {e}")

        return RiskControlParams()

    def get_crawl_params(self, config: AutomationConfig = None) -> CrawlParams:
        """
        获取采集参数
        """
        if not config:
            config = self.get_default_config()

        if not config:
            return CrawlParams()

        try:
            crawl_config = config.crawl_configs.first()
            if crawl_config:
                return CrawlParams(
                    AUTO_LEARN_KEYWORDS=crawl_config.AUTO_LEARN_KEYWORDS,
                    ADAPTIVE_CRAWL_MODE=crawl_config.ADAPTIVE_CRAWL_MODE,
                    MULTI_SOURCE_ENABLED=crawl_config.MULTI_SOURCE_ENABLED,
                    DEFAULT_CRAWL_INTERVAL=crawl_config.DEFAULT_CRAWL_INTERVAL,
                    MAX_PAGES_PER_CRAWL=crawl_config.MAX_PAGES_PER_CRAWL,
                    ENABLE_DEDUP=crawl_config.ENABLE_DEDUP
                )
        except Exception as e:
            logger.error(f"获取采集参数失败: {e}")

        return CrawlParams()

    def get_notification_params(self, config: AutomationConfig = None) -> NotificationParams:
        """
        获取通知参数
        """
        if not config:
            config = self.get_default_config()

        if not config:
            return NotificationParams()

        try:
            notification_config = config.notification_configs.first()
            if notification_config:
                return NotificationParams(
                    NOTIFICATION_ENABLED=notification_config.NOTIFICATION_ENABLED,
                    DINGTALK_ENABLED=notification_config.DINGTALK_ENABLED,
                    KEY_EVENTS_ONLY=notification_config.KEY_EVENTS_ONLY,
                    DAILY_REPORT_ENABLED=notification_config.DAILY_REPORT_ENABLED,
                    WEEKLY_REPORT_ENABLED=notification_config.WEEKLY_REPORT_ENABLED,
                    NOTIFY_ON_START=notification_config.NOTIFY_ON_START,
                    NOTIFY_ON_SUCCESS=notification_config.NOTIFY_ON_SUCCESS,
                    NOTIFY_ON_FAILURE=notification_config.NOTIFY_ON_FAILURE,
                    NOTIFY_ON_WIN=notification_config.NOTIFY_ON_WIN,
                    NOTIFY_ON_LOSS=notification_config.NOTIFY_ON_LOSS
                )
        except Exception as e:
            logger.error(f"获取通知参数失败: {e}")

        return NotificationParams()

    def _get_default_params(self) -> Dict[str, Any]:
        """
        获取默认参数（当没有配置时使用）
        """
        return {
            'decision': AIDecisionParams().__dict__,
            'match': AutoMatchParams().__dict__,
            'review': DocumentReviewParams().__dict__,
            'risk': RiskControlParams().__dict__,
            'crawl': CrawlParams().__dict__,
            'notification': NotificationParams().__dict__
        }


automation_config_service = AutomationConfigService()
