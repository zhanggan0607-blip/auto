"""
Common Crawler 公共爬虫模块
提供统一的爬虫基础设施，支持多种采集策略
"""
from .managers.user_agent_manager import UserAgentManager
from .managers.proxy_manager import ProxyManager
from .managers.cookie_manager import CookieManager, cookie_manager
from .strategies.base_strategy import CrawlStrategy, RequestStrategy, SeleniumStrategy
from .common_crawler import CommonCrawler, CrawlerConfig, SelectorConfig

__all__ = [
    'UserAgentManager',
    'ProxyManager',
    'CookieManager',
    'cookie_manager',
    'CrawlStrategy',
    'RequestStrategy',
    'SeleniumStrategy',
    'CommonCrawler',
    'CrawlerConfig',
    'SelectorConfig',
]