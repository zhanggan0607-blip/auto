"""
爬虫模块 - 多级降级策略与监控系统
实现采集任务的自动降级、监控和动态调优
"""
import time
import random
import logging
import hashlib
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class CrawlStrategy(Enum):
    """采集策略枚举"""
    API_DIRECT = "api_direct"
    HTTP_REQUESTS = "http_requests"
    SELENIUM_STEALTH = "selenium_stealth"
    PYPPEETEER_STEALTH = "pyppeteer_stealth"
    MANUAL_REVIEW = "manual_review"


class ResponseStatus(Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    CAPTCHA = "captcha"
    ERROR = "error"


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    priority: int
    description: str
    enabled: bool = True
    max_retries: int = 3
    timeout: int = 60
    weight: float = 1.0


@dataclass
class CrawlMetrics:
    """采集指标"""
    total_requests: int = 0
    successes: int = 0
    failures: int = 0
    blocks: int = 0
    timeouts: int = 0
    captchas: int = 0
    strategy_usage: Dict[str, int] = field(default_factory=dict)
    last_request_time: float = 0
    last_block_time: float = 0
    consecutive_blocks: int = 0


class AdaptiveRateLimiter:
    """
    自适应频率限制器
    根据采集状态动态调整请求频率
    """

    def __init__(
        self,
        base_rate: float = 1.0,
        min_rate: float = 0.1,
        max_rate: float = 5.0,
        burst_size: int = 3,
        cooldown_period: float = 60.0
    ):
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.burst_size = burst_size
        self.cooldown_period = cooldown_period

        self._request_times: List[float] = []
        self._burst_count = 0
        self._cooldown_until = 0
        self._consecutive_failures = 0

    def wait(self, context: dict = None) -> float:
        """
        等待直到可以发送下一个请求

        Args:
            context: 上下文信息，包含url, status_code等

        Returns:
            float: 实际等待的秒数
        """
        current_time = time.time()

        if current_time < self._cooldown_until:
            wait_time = self._cooldown_until - current_time
            logger.info(f"冷却期中，等待 {wait_time:.2f} 秒")
            time.sleep(wait_time)
            current_time = time.time()

        if self._burst_count >= self.burst_size:
            cooldown = self.cooldown_period * (1 + self._consecutive_failures * 0.5)
            self._cooldown_until = current_time + cooldown
            self._burst_count = 0
            logger.warning(f"触发冷却期，持续 {cooldown:.1f} 秒")

        interval = (1.0 / self.current_rate) + random.uniform(0.1, 0.5)
        time.sleep(interval)

        self._request_times.append(time.time())
        self._burst_count += 1

        if len(self._request_times) > 100:
            self._request_times = self._request_times[-50:]

        return interval

    def report_success(self, response_time: float = None):
        """
        报告成功响应

        Args:
            response_time: 响应时间（秒）
        """
        self._consecutive_failures = 0
        self.current_rate = min(self.max_rate, self.current_rate * 1.05)
        logger.debug(f"成功率提升，当前速率: {self.current_rate:.2f} req/s")

    def report_failure(self, is_block: bool = False):
        """
        报告失败响应

        Args:
            is_block: 是否为封锁/拦截
        """
        self._consecutive_failures += 1

        if is_block:
            self.current_rate = max(self.min_rate, self.current_rate * 0.2)
            self._cooldown_until = time.time() + self.cooldown_period * 2
            logger.warning(f"检测到封锁，速率降至: {self.current_rate:.2f} req/s")
        else:
            self.current_rate = max(self.min_rate, self.current_rate * 0.8)
            logger.warning(f"请求失败，速率降至: {self.current_rate:.2f} req/s")

    def should_switch_strategy(self) -> bool:
        """
        判断是否需要切换策略

        Returns:
            bool: 是否应该切换策略
        """
        if self._consecutive_failures >= 3:
            return True
        if self.current_rate <= self.min_rate * 1.5:
            return True
        return False

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'current_rate': self.current_rate,
            'consecutive_failures': self._consecutive_failures,
            'in_cooldown': time.time() < self._cooldown_until,
            'burst_count': self._burst_count
        }


class CrawlMonitor:
    """
    采集监控系统
    监控采集状态，检测异常并提供调优建议
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics = CrawlMetrics()
        self._request_history: List[dict] = []
        self._block_patterns: Dict[str, int] = defaultdict(int)

    def record_request(
        self,
        url: str,
        strategy: str,
        status: ResponseStatus,
        response_time: float = None,
        error_message: str = None
    ):
        """
        记录请求结果

        Args:
            url: 请求URL
            strategy: 使用的策略
            status: 响应状态
            response_time: 响应时间
            error_message: 错误信息
        """
        self.metrics.total_requests += 1
        self.metrics.last_request_time = time.time()

        self.metrics.strategy_usage[strategy] = self.metrics.strategy_usage.get(strategy, 0) + 1

        record = {
            'url': url,
            'strategy': strategy,
            'status': status.value,
            'response_time': response_time,
            'error_message': error_message,
            'timestamp': time.time()
        }
        self._request_history.append(record)

        if len(self._request_history) > self.window_size:
            self._request_history = self._request_history[-self.window_size:]

        if status == ResponseStatus.SUCCESS:
            self.metrics.successes += 1
        elif status == ResponseStatus.BLOCKED:
            self.metrics.blocks += 1
            self.metrics.last_block_time = time.time()
            self.metrics.consecutive_blocks += 1
            self._analyze_block_pattern(url)
        elif status == ResponseStatus.TIMEOUT:
            self.metrics.timeouts += 1
            self.metrics.consecutive_blocks = 0
        elif status == ResponseStatus.CAPTCHA:
            self.metrics.captchas += 1
            self.metrics.consecutive_blocks += 1
        else:
            self.metrics.failures += 1
            self.metrics.consecutive_blocks = 0

    def _analyze_block_pattern(self, url: str):
        """
        分析封锁模式

        Args:
            url: 被封锁的URL
        """
        parsed = urlparse(url)
        key = f"{parsed.netloc}"
        self._block_patterns[key] += 1
        logger.warning(f"检测到封锁模式: {key} (累计 {self._block_patterns[key]} 次)")

    def should_adjust_strategy(self) -> bool:
        """
        判断是否需要调整策略

        Returns:
            bool: 是否应该调整策略
        """
        if self.metrics.total_requests < 5:
            return False

        recent = self._request_history[-10:]
        recent_blocks = sum(1 for r in recent if r['status'] == ResponseStatus.BLOCKED.value)
        recent_success = sum(1 for r in recent if r['status'] == ResponseStatus.SUCCESS.value)

        if recent_blocks >= 3:
            return True

        if len(recent_success) > 0 and recent_blocks / len(recent) > 0.3:
            return True

        return False

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.metrics.total_requests == 0:
            return 1.0
        return self.metrics.successes / self.metrics.total_requests

    def get_block_rate(self) -> float:
        """获取封锁率"""
        if self.metrics.total_requests == 0:
            return 0.0
        return self.metrics.blocks / self.metrics.total_requests

    def get_recommended_adjustments(self) -> dict:
        """
        获取推荐的调整参数

        Returns:
            dict: 调整建议
        """
        success_rate = self.get_success_rate()
        block_rate = self.get_block_rate()

        adjustments = {
            'action': 'none',
            'reduce_rate_by': 0.0,
            'enable_proxy': False,
            'increase_delay': False,
            'switch_user_agent': False,
            'switch_strategy': None,
            'message': ''
        }

        if block_rate > 0.2:
            adjustments['action'] = 'aggressive'
            adjustments['reduce_rate_by'] = 0.7
            adjustments['enable_proxy'] = True
            adjustments['increase_delay'] = True
            adjustments['message'] = f'封锁率过高 ({block_rate:.1%})，大幅降低频率'
        elif block_rate > 0.1:
            adjustments['action'] = 'moderate'
            adjustments['reduce_rate_by'] = 0.5
            adjustments['increase_delay'] = True
            adjustments['message'] = f'检测到封锁 ({block_rate:.1%})，降低频率'
        elif success_rate < 0.5:
            adjustments['action'] = 'moderate'
            adjustments['switch_strategy'] = True
            adjustments['message'] = f'成功率较低 ({success_rate:.1%})，建议切换策略'
        else:
            adjustments['message'] = '采集状态正常'

        return adjustments

    def get_stats(self) -> dict:
        """获取完整统计信息"""
        return {
            'total_requests': self.metrics.total_requests,
            'successes': self.metrics.successes,
            'failures': self.metrics.failures,
            'blocks': self.metrics.blocks,
            'timeouts': self.metrics.timeouts,
            'captchas': self.metrics.captchas,
            'success_rate': f"{self.get_success_rate():.1%}",
            'block_rate': f"{self.get_block_rate():.1%}",
            'consecutive_blocks': self.metrics.consecutive_blocks,
            'strategy_usage': self.metrics.strategy_usage,
            'block_patterns': dict(self._block_patterns)
        }

    def reset(self):
        """重置监控数据"""
        self.metrics = CrawlMetrics()
        self._request_history.clear()
        self._block_patterns.clear()


class MultiStrategyCrawler:
    """
    多级降级采集器
    核心类，实现采集任务的自动降级和策略切换
    """

    DEFAULT_STRATEGIES = [
        StrategyConfig(
            name=CrawlStrategy.HTTP_REQUESTS.value,
            priority=1,
            description='HTTP请求直连，速度最快',
            max_retries=2,
            timeout=30,
            weight=0.4
        ),
        StrategyConfig(
            name=CrawlStrategy.SELENIUM_STEALTH.value,
            priority=2,
            description='Selenium反检测浏览器',
            max_retries=2,
            timeout=60,
            weight=0.3
        ),
        StrategyConfig(
            name=CrawlStrategy.PYPPEETEER_STEALTH.value,
            priority=3,
            description='Pyppeteer增强反检测',
            max_retries=2,
            timeout=90,
            weight=0.2
        ),
        StrategyConfig(
            name=CrawlStrategy.MANUAL_REVIEW.value,
            priority=4,
            description='人工审核处理',
            max_retries=1,
            timeout=0,
            weight=0.1
        ),
    ]

    def __init__(
        self,
        strategies: List[StrategyConfig] = None,
        rate_limiter: AdaptiveRateLimiter = None,
        monitor: CrawlMonitor = None,
        proxy_enabled: bool = False,
        proxy_list: List[str] = None
    ):
        """
        初始化多级降级采集器

        Args:
            strategies: 策略列表
            rate_limiter: 频率限制器
            monitor: 监控系统
            proxy_enabled: 是否启用代理
            proxy_list: 代理列表
        """
        self.strategies = strategies or self.DEFAULT_STRATEGIES
        self.strategies.sort(key=lambda x: x.priority)

        self.rate_limiter = rate_limiter or AdaptiveRateLimiter()
        self.monitor = monitor or CrawlMonitor()

        self.proxy_enabled = proxy_enabled
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0

        self._current_strategy_index = 0
        self._retry_count = 0

    def crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        执行多级降级采集

        Args:
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            dict: 采集结果
        """
        start_time = time.time()
        last_error = None

        for strategy in self.strategies:
            if not strategy.enabled:
                continue

            self._current_strategy_index = self.strategies.index(strategy)
            self._retry_count = 0

            for attempt in range(strategy.max_retries):
                try:
                    self.rate_limiter.wait()

                    logger.info(f"尝试策略: {strategy.name} (第 {attempt + 1} 次)")

                    result = self._execute_strategy(strategy.name, url, **kwargs)

                    if result.get('success'):
                        result['strategy_used'] = strategy.name
                        result['attempts'] = attempt + 1
                        result['duration'] = time.time() - start_time

                        self.monitor.record_request(
                            url=url,
                            strategy=strategy.name,
                            status=ResponseStatus.SUCCESS,
                            response_time=result.get('response_time')
                        )
                        self.rate_limiter.report_success()

                        return result

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"策略 {strategy.name} 第 {attempt + 1} 次失败: {e}")

                    self._analyze_failure(url, strategy.name, e)

                    if attempt == strategy.max_retries - 1:
                        break

        logger.error(f"所有策略均失败: {last_error}")

        return {
            'success': False,
            'error_message': f'所有采集策略均失败: {last_error}',
            'strategies_tried': [s.name for s in self.strategies if s.enabled],
            'duration': time.time() - start_time
        }

    def _execute_strategy(self, strategy_name: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        执行具体策略

        Args:
            strategy_name: 策略名称
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            dict: 策略执行结果
        """
        proxy = self._get_next_proxy() if self.proxy_enabled else None

        if strategy_name == CrawlStrategy.HTTP_REQUESTS.value:
            return self._crawl_by_http_requests(url, proxy, **kwargs)
        elif strategy_name == CrawlStrategy.SELENIUM_STEALTH.value:
            return self._crawl_by_selenium_stealth(url, proxy, **kwargs)
        elif strategy_name == CrawlStrategy.PYPPEETEER_STEALTH.value:
            return self._crawl_by_pyppeteer_stealth(url, proxy, **kwargs)
        elif strategy_name == CrawlStrategy.MANUAL_REVIEW.value:
            return self._create_manual_review_task(url, **kwargs)
        else:
            raise Exception(f"未知策略: {strategy_name}")

    def _crawl_by_http_requests(self, url: str, proxy: str = None, **kwargs) -> Dict[str, Any]:
        """HTTP请求策略"""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        start_time = time.time()

        session = requests.Session()

        adapter = HTTPAdapter(
            max_retries=Retry(total=2, backoff_factor=0.5),
            pool_connections=10,
            pool_maxsize=20
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        response = session.get(
            url,
            headers=headers,
            proxies={'http': proxy, 'https': proxy} if proxy else None,
            timeout=30
        )

        response_time = time.time() - start_time

        if response.status_code == 200:
            return {
                'success': True,
                'content': response.text,
                'status_code': response.status_code,
                'response_time': response_time,
                'strategy': 'http_requests'
            }
        elif response.status_code in [403, 429]:
            self.monitor.record_request(url, CrawlStrategy.HTTP_REQUESTS.value, ResponseStatus.BLOCKED)
            self.rate_limiter.report_failure(is_block=True)
            raise Exception(f"被封锁: HTTP {response.status_code}")
        else:
            raise Exception(f"HTTP错误: {response.status_code}")

    def _crawl_by_selenium_stealth(self, url: str, proxy: str = None, **kwargs) -> Dict[str, Any]:
        """Selenium反检测策略"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from crawler.anti_detection import AntiDetection

        start_time = time.time()

        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        options = AntiDetection.get_chrome_options(options)

        options.add_argument(f'--user-agent={self._get_random_user_agent()}')

        if proxy:
            options.add_argument(f'--proxy-server={proxy}')

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            time.sleep(random.uniform(2, 4))

            content = driver.page_source
            response_time = time.time() - start_time

            self.monitor.record_request(
                url, CrawlStrategy.SELENIUM_STEALTH.value, ResponseStatus.SUCCESS, response_time
            )

            return {
                'success': True,
                'content': content,
                'response_time': response_time,
                'strategy': 'selenium_stealth'
            }

        finally:
            driver.quit()

    def _crawl_by_pyppeteer_stealth(self, url: str, proxy: str = None, **kwargs) -> Dict[str, Any]:
        """Pyppeteer反检测策略"""
        import asyncio
        from crawler.stealth_crawler import StealthCrawler

        start_time = time.time()

        async def _crawl():
            crawler = StealthCrawler()
            result = await crawler.crawl_with_fallback(url, **kwargs)
            return result

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(_crawl())
        response_time = time.time() - start_time

        if result.success:
            self.monitor.record_request(
                url, CrawlStrategy.PYPPEETEER_STEALTH.value, ResponseStatus.SUCCESS, response_time
            )
            return {
                'success': True,
                'content': result.data,
                'response_time': response_time,
                'strategy': 'pyppeteer_stealth'
            }
        else:
            raise Exception(result.error_message)

    def _create_manual_review_task(self, url: str, **kwargs) -> Dict[str, Any]:
        """人工审核策略"""
        logger.info(f"创建人工审核任务: {url}")

        return {
            'success': True,
            'requires_manual_review': True,
            'url': url,
            'reason': '自动采集失败，需人工处理',
            'strategy': 'manual_review'
        }

    def _analyze_failure(self, url: str, strategy: str, error: Exception):
        """分析失败原因"""
        error_msg = str(error).lower()

        if '403' in error_msg or 'blocked' in error_msg or 'forbidden' in error_msg:
            self.monitor.record_request(url, strategy, ResponseStatus.BLOCKED)
            self.rate_limiter.report_failure(is_block=True)
        elif 'timeout' in error_msg or 'timed out' in error_msg:
            self.monitor.record_request(url, strategy, ResponseStatus.TIMEOUT)
            self.rate_limiter.report_failure(is_block=False)
        elif 'captcha' in error_msg or 'verify' in error_msg:
            self.monitor.record_request(url, strategy, ResponseStatus.CAPTCHA)
            self.rate_limiter.report_failure(is_block=True)
        else:
            self.monitor.record_request(url, strategy, ResponseStatus.ERROR, error_message=error_msg)
            self.rate_limiter.report_failure(is_block=False)

    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        return random.choice(agents)

    def _get_next_proxy(self) -> Optional[str]:
        """获取下一个代理"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def get_stats(self) -> dict:
        """获取采集器和监控统计"""
        return {
            'strategies': [
                {
                    'name': s.name,
                    'priority': s.priority,
                    'enabled': s.enabled,
                    'max_retries': s.max_retries
                }
                for s in self.strategies
            ],
            'rate_limiter': self.rate_limiter.get_stats(),
            'monitor': self.monitor.get_stats()
        }


from urllib.parse import urlparse
