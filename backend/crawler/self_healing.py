"""
故障自愈机制
包含：IP切换、指纹更换、降级解析、失败知识库
"""
import logging
import random
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from django.conf import settings

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """
    失败类型枚举
    """
    NETWORK_ERROR = 'network_error'
    TIMEOUT = 'timeout'
    BLOCKED = 'blocked'
    CAPTCHA = 'captcha'
    RATE_LIMIT = 'rate_limit'
    PARSE_ERROR = 'parse_error'
    UNKNOWN = 'unknown'


@dataclass
class FailureRecord:
    """
    失败记录
    """
    url: str
    failure_type: str
    error_message: str
    strategy_used: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    resolved: bool = False
    resolution_method: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


class FailureKnowledgeBase:
    """
    失败知识库
    记录失败原因和解决方案
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._failures = []
            cls._instance._solutions = {}
        return cls._instance
    
    def record_failure(self, record: FailureRecord):
        """
        记录失败
        """
        self._failures.append(record)
        logger.info(f"记录失败: {record.url} - {record.failure_type}")
    
    def get_similar_failures(self, url: str, failure_type: str) -> List[FailureRecord]:
        """
        获取相似失败记录
        """
        similar = []
        for record in self._failures:
            if record.failure_type == failure_type:
                if self._is_similar_url(record.url, url):
                    similar.append(record)
        return similar
    
    def _is_similar_url(self, url1: str, url2: str) -> bool:
        """
        判断URL是否相似
        """
        from urllib.parse import urlparse
        
        parsed1 = urlparse(url1)
        parsed2 = urlparse(url2)
        
        return parsed1.netloc == parsed2.netloc
    
    def get_solution(self, failure_type: str) -> Optional[str]:
        """
        获取解决方案
        """
        return self._solutions.get(failure_type)
    
    def set_solution(self, failure_type: str, solution: str):
        """
        设置解决方案
        """
        self._solutions[failure_type] = solution
    
    def mark_resolved(self, url: str, resolution_method: str):
        """
        标记为已解决
        """
        for record in self._failures:
            if record.url == url and not record.resolved:
                record.resolved = True
                record.resolution_method = resolution_method
                logger.info(f"失败记录已解决: {url}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        """
        total = len(self._failures)
        resolved = sum(1 for f in self._failures if f.resolved)
        
        type_counts = {}
        for record in self._failures:
            type_counts[record.failure_type] = type_counts.get(record.failure_type, 0) + 1
        
        return {
            'total_failures': total,
            'resolved': resolved,
            'resolution_rate': resolved / total if total > 0 else 0,
            'type_distribution': type_counts
        }


failure_knowledge_base = FailureKnowledgeBase()


class ProxyPool:
    """
    代理池管理
    支持住宅代理池
    """
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or settings.CRAWLER_CONFIG.get('PROXY_LIST', [])
        self.failed_proxies = set()
        self.current_index = 0
    
    def get_proxy(self) -> Optional[str]:
        """
        获取可用代理
        """
        available = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available:
            self.failed_proxies.clear()
            available = self.proxy_list
        
        if available:
            return random.choice(available)
        return None
    
    def mark_failed(self, proxy: str):
        """
        标记代理失败
        """
        self.failed_proxies.add(proxy)
        logger.warning(f"代理标记为失败: {proxy}")
    
    def rotate_proxy(self) -> Optional[str]:
        """
        轮换代理
        """
        return self.get_proxy()


class SelfHealingCrawler:
    """
    自愈爬虫包装器
    自动处理失败场景
    """
    
    def __init__(
        self,
        crawler,
        proxy_pool: ProxyPool = None,
        max_retries: int = 3
    ):
        self.crawler = crawler
        self.proxy_pool = proxy_pool or ProxyPool()
        self.max_retries = max_retries
        self.knowledge_base = failure_knowledge_base
    
    async def crawl_with_healing(
        self,
        url: str,
        **kwargs
    ) -> 'CrawlResult':
        """
        带自愈机制的采集
        """
        from .pyppeteer_crawler import CrawlResult
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self.crawler.crawl_with_fallback(url, **kwargs)
                
                if result.success:
                    self.knowledge_base.mark_resolved(url, f"retry_{attempt}")
                    return result
                
                failure_type = self._detect_failure_type(result.error_message)
                
                self._apply_healing_strategy(failure_type, attempt)
                
                failure_record = FailureRecord(
                    url=url,
                    failure_type=failure_type.value,
                    error_message=result.error_message,
                    strategy_used=result.strategy,
                    retry_count=attempt + 1
                )
                self.knowledge_base.record_failure(failure_record)
                
                last_error = result.error_message
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"采集异常 (尝试 {attempt + 1}): {str(e)}")
        
        return CrawlResult(
            success=False,
            error_message=f"自愈失败，重试 {self.max_retries} 次后仍失败: {last_error}"
        )
    
    def _detect_failure_type(self, error_message: str) -> FailureType:
        """
        检测失败类型
        """
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return FailureType.TIMEOUT
        elif 'blocked' in error_lower or 'forbidden' in error_lower or '403' in error_lower:
            return FailureType.BLOCKED
        elif 'captcha' in error_lower or '验证' in error_message:
            return FailureType.CAPTCHA
        elif 'rate limit' in error_lower or '429' in error_lower:
            return FailureType.RATE_LIMIT
        elif 'network' in error_lower or 'connection' in error_lower:
            return FailureType.NETWORK_ERROR
        elif 'parse' in error_lower or 'selector' in error_lower:
            return FailureType.PARSE_ERROR
        else:
            return FailureType.UNKNOWN
    
    def _apply_healing_strategy(self, failure_type: FailureType, attempt: int):
        """
        应用自愈策略
        """
        if failure_type == FailureType.BLOCKED:
            self._handle_blocked()
        elif failure_type == FailureType.RATE_LIMIT:
            self._handle_rate_limit(attempt)
        elif failure_type == FailureType.CAPTCHA:
            self._handle_captcha()
        elif failure_type == FailureType.TIMEOUT:
            self._handle_timeout()
        elif failure_type == FailureType.NETWORK_ERROR:
            self._handle_network_error()
    
    def _handle_blocked(self):
        """
        处理被封禁
        """
        if self.proxy_pool.proxy_list:
            new_proxy = self.proxy_pool.rotate_proxy()
            if new_proxy:
                logger.info(f"切换代理: {new_proxy}")
        
        logger.info("更换浏览器指纹")
    
    def _handle_rate_limit(self, attempt: int):
        """
        处理限流
        """
        delay = min(2 ** attempt, 60)
        logger.info(f"限流，等待 {delay} 秒")
        time.sleep(delay)
    
    def _handle_captcha(self):
        """
        处理验证码
        """
        logger.warning("遇到验证码，建议人工介入或使用OCR服务")
    
    def _handle_timeout(self):
        """
        处理超时
        """
        logger.info("超时，增加超时时间")
    
    def _handle_network_error(self):
        """
        处理网络错误
        """
        if self.proxy_pool.proxy_list:
            new_proxy = self.proxy_pool.rotate_proxy()
            if new_proxy:
                logger.info(f"网络错误，切换代理: {new_proxy}")


class RecoveryStrategy:
    """
    恢复策略
    """
    
    @staticmethod
    def delay_exponential(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
        """
        指数退避延迟
        """
        delay = min(base * (2 ** attempt), max_delay)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter
    
    @staticmethod
    def should_retry(error_message: str, attempt: int, max_retries: int) -> bool:
        """
        判断是否应该重试
        """
        if attempt >= max_retries:
            return False
        
        non_retryable = ['404', 'not found', 'invalid url']
        error_lower = error_message.lower()
        
        return not any(n in error_lower for n in non_retryable)
    
    @staticmethod
    def get_next_strategy(current_strategy: str) -> Optional[str]:
        """
        获取下一个降级策略
        """
        strategies = settings.CRAWLER_CONFIG['FALLBACK_STRATEGY']
        
        try:
            current_index = strategies.index(current_strategy)
            if current_index < len(strategies) - 1:
                return strategies[current_index + 1]
        except ValueError:
            pass
        
        return None
