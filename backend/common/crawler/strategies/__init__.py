"""
公共爬虫策略模块
提供多种采集策略：API直连、Selenium、Pyppeteer等
"""

from .base_strategy import CrawlStrategy, RequestStrategy, SeleniumStrategy

__all__ = [
    'CrawlStrategy',
    'RequestStrategy',
    'SeleniumStrategy',
]