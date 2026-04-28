"""
公共爬虫基类
提供统一的爬虫基础设施，支持多策略切换
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .managers.user_agent_manager import UserAgentManager
from .managers.proxy_manager import ProxyManager
from .managers.cookie_manager import CookieManager
from .strategies.base_strategy import CrawlStrategy, RequestStrategy, SeleniumStrategy, CrawlResult, create_strategy

logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    """
    爬虫配置类
    """
    headless: bool = True
    timeout: int = 30
    page_load_timeout: int = 60
    implicit_wait: int = 10
    request_delay_min: float = 1.0
    request_delay_max: float = 3.0
    max_retries: int = 3
    proxy_enabled: bool = False
    proxy_list: List[str] = field(default_factory=list)
    user_agent_rotation: bool = True
    cookies_enabled: bool = True
    javascript_enabled: bool = True
    strategy: str = 'auto'


@dataclass
class SelectorConfig:
    """
    选择器配置类
    """
    list_container: str = ''
    item_container: str = ''
    title: str = ''
    link: str = ''
    date: str = ''
    region: str = ''
    project_code: str = ''
    budget: str = ''
    description: str = ''
    detail_content: str = ''
    pagination_next: str = ''
    pagination_info: str = ''


class CommonCrawler(ABC):
    """
    通用爬虫基类
    支持多种采集策略（Requests/Selenium），自动降级

    使用示例：
        class MyCrawler(CommonCrawler):
            def parse_items(self, html: str) -> List[Dict]:
                # 解析逻辑
                pass

        crawler = MyCrawler(config=CrawlerConfig(proxy_enabled=True, proxy_list=['http://proxy:8080']))
        results = crawler.crawl('https://example.com')
    """

    def __init__(self, config: CrawlerConfig = None):
        """
        初始化爬虫

        Args:
            config: 爬虫配置
        """
        self.config = config or CrawlerConfig()
        self.user_agent_manager = UserAgentManager()
        self.proxy_manager = ProxyManager(self.config.proxy_list) if self.config.proxy_enabled else None
        self.cookie_manager = CookieManager()
        self._strategy: Optional[CrawlStrategy] = None
        self._request_count = 0

    @property
    def strategy(self) -> CrawlStrategy:
        """
        获取当前策略（懒加载）
        """
        if self._strategy is None:
            self._strategy = self._create_strategy()
        return self._strategy

    def _create_strategy(self) -> CrawlStrategy:
        """
        创建采集策略

        Returns:
            CrawlStrategy: 策略实例
        """
        common_kwargs = {
            'user_agent_manager': self.user_agent_manager,
            'proxy_manager': self.proxy_manager,
            'delay_min': self.config.request_delay_min,
            'delay_max': self.config.request_delay_max,
        }

        if self.config.strategy == 'requests':
            return RequestStrategy(
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                **common_kwargs
            )
        elif self.config.strategy == 'selenium':
            return SeleniumStrategy(
                headless=self.config.headless,
                timeout=self.config.timeout,
                page_load_timeout=self.config.page_load_timeout,
                implicit_wait=self.config.implicit_wait,
                **common_kwargs
            )
        elif self.config.strategy == 'auto':
            return RequestStrategy(
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                **common_kwargs
            )
        else:
            return RequestStrategy(**common_kwargs)

    def fetch(self, url: str, **kwargs) -> CrawlResult:
        """
        抓取页面

        Args:
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            CrawlResult: 抓取结果
        """
        self._request_count += 1
        result = self.strategy.fetch(url, **kwargs)

        if not result.success and isinstance(self.strategy, RequestStrategy):
            logger.warning(f"Request策略失败，尝试降级到Selenium: {url}")
            selenium_strategy = SeleniumStrategy(
                user_agent_manager=self.user_agent_manager,
                proxy_manager=self.proxy_manager,
                delay_min=self.config.request_delay_min,
                delay_max=self.config.request_delay_max,
                headless=self.config.headless,
                timeout=self.config.timeout,
                page_load_timeout=self.config.page_load_timeout,
                implicit_wait=self.config.implicit_wait,
            )
            result = selenium_strategy.fetch(url, **kwargs)
            selenium_strategy.close()

        return result

    def get_page(self, url: str, **kwargs) -> Optional[str]:
        """
        获取页面内容（便捷方法）

        Args:
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            Optional[str]: 页面HTML内容
        """
        result = self.fetch(url, **kwargs)
        return result.content if result.success else None

    def parse_html(self, html: str, parser: str = 'html.parser'):
        """
        解析HTML

        Args:
            html: HTML字符串
            parser: 解析器类型

        Returns:
            BeautifulSoup: 解析后的对象
        """
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, parser)

    def get_request_count(self) -> int:
        """获取请求计数"""
        return self._request_count

    @abstractmethod
    def parse_items(self, html: str) -> List[Dict[str, Any]]:
        """
        解析数据项（子类必须实现）

        Args:
            html: 页面HTML内容

        Returns:
            List[Dict]: 解析结果列表
        """
        pass

    def crawl(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """
        执行爬取（便捷方法）

        Args:
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            List[Dict]: 爬取结果
        """
        result = self.fetch(url, **kwargs)
        if result.success and result.content:
            return self.parse_items(result.content)
        return []

    def crawl_with_retry(self, url: str, max_retries: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        带重试的爬取

        Args:
            url: 目标URL
            max_retries: 最大重试次数
            **kwargs: 其他参数

        Returns:
            List[Dict]: 爬取结果
        """
        max_retries = max_retries or self.config.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                results = self.crawl(url, **kwargs)
                if results:
                    return results
            except Exception as e:
                last_error = e
                logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")

        logger.error(f"所有重试均失败: {last_error}")
        return []

    def close(self):
        """关闭爬虫，释放资源"""
        if self._strategy and hasattr(self._strategy, 'close'):
            self._strategy.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        logger.info(f"爬虫结束，总请求数: {self._request_count}")


class MultiStrategyCrawler(CommonCrawler):
    """
    多策略爬虫
    自动尝试多种策略直到成功
    """

    def __init__(self, config: CrawlerConfig = None):
        super().__init__(config)
        self._strategies: List[CrawlStrategy] = []

    def _create_strategy(self) -> CrawlStrategy:
        """创建多策略"""
        common_kwargs = {
            'user_agent_manager': self.user_agent_manager,
            'proxy_manager': self.proxy_manager,
            'delay_min': self.config.request_delay_min,
            'delay_max': self.config.request_delay_max,
        }

        self._strategies = [
            RequestStrategy(
                timeout=self.config.timeout,
                max_retries=1,
                **common_kwargs
            ),
            SeleniumStrategy(
                headless=self.config.headless,
                timeout=self.config.timeout,
                page_load_timeout=self.config.page_load_timeout,
                implicit_wait=self.config.implicit_wait,
                **common_kwargs
            ),
        ]
        return self._strategies[0]

    def fetch(self, url: str, **kwargs) -> CrawlResult:
        """
        尝试多种策略抓取

        Args:
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            CrawlResult: 抓取结果
        """
        last_result = None

        for strategy in self._strategies:
            result = strategy.fetch(url, **kwargs)
            if result.success:
                return result
            last_result = result
            logger.warning(f"策略 {type(strategy).__name__} 失败，尝试下一个策略")

        return last_result or CrawlResult(success=False, error="所有策略均失败")

    def close(self):
        """关闭所有策略"""
        for strategy in self._strategies:
            if hasattr(strategy, 'close'):
                strategy.close()


def create_crawler(crawler_type: str = 'common', **kwargs) -> CommonCrawler:
    """
    工厂函数：创建爬虫

    Args:
        crawler_type: 爬虫类型 ('common', 'multi_strategy')
        **kwargs: 爬虫参数

    Returns:
        CommonCrawler: 爬虫实例
    """
    if crawler_type == 'common':
        return CommonCrawler(**kwargs)
    elif crawler_type == 'multi_strategy':
        return MultiStrategyCrawler(**kwargs)
    else:
        raise ValueError(f"不支持的爬虫类型: {crawler_type}")