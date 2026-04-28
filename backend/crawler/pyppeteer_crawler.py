"""
智能采集模块 - Pyppeteer 动态爬虫基类
支持多级降级策略：API直连 → 无头浏览器 → 反检测模式

注意：CrawlResult, ProxyConfig, BrowserFingerprint 已移至 common_types.py
"""
import asyncio
import logging
import os
import random
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from django.conf import settings
from core.constants import CrawlStrategy, CrawlStatus

from .common_types import CrawlResult, ProxyConfig, BrowserFingerprint


logger = logging.getLogger(__name__)


class PyppeteerCrawler(ABC):
    """
    Pyppeteer 动态爬虫基类
    支持多级降级策略
    """

    BROWSER_CANDIDATES = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]

    @staticmethod
    def find_browser_executable() -> Optional[str]:
        for path in PyppeteerCrawler.BROWSER_CANDIDATES:
            if os.path.exists(path):
                logger.info(f"找到浏览器: {path}")
                return path
        logger.warning("未找到系统浏览器 (Chrome/Edge/Brave)")
        return None

    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        self.proxy_config = proxy_config or ProxyConfig()
        self.max_retries = max_retries
        self.timeout = timeout
        self.browser = None
        self.page = None
        self._current_strategy = None
        self._fallback_strategy = settings.CRAWLER_CONFIG['FALLBACK_STRATEGY']
    
    async def init_browser(
        self,
        headless: bool = True,
        fingerprint: BrowserFingerprint = None,
        executablePath: str = None
    ) -> bool:
        """
        初始化浏览器
        
        Args:
            headless: 是否无头模式
            fingerprint: 浏览器指纹
            executablePath: 浏览器可执行文件路径，如果为None则使用pyppeteer下载的Chromium
            
        Returns:
            bool: 是否成功
        """
        from pyppeteer import launch
        
        try:
            fingerprint = fingerprint or BrowserFingerprint.random_fingerprint()
            
            args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size={},{}'.format(
                    fingerprint.viewport['width'],
                    fingerprint.viewport['height']
                ),
            ]
            
            if headless:
                args.append('--headless=new')
            
            launch_options = {
                'headless': headless,
                'args': args,
                'defaultViewport': fingerprint.viewport,
                'ignoreHTTPSErrors': True,
                'handleSIGINT': False,
                'handleSIGTERM': False,
                'handleSIGHUP': False,
            }
            
            if executablePath:
                launch_options['executablePath'] = executablePath
            
            if self.proxy_config.enabled and self.proxy_config.server:
                launch_options['args'].append(f'--proxy-server={self.proxy_config.server}')
            
            self.browser = await launch(launch_options)
            self.page = await self.browser.newPage()
            
            await self.page.setUserAgent(fingerprint.user_agent)
            await self.page.setViewport(fingerprint.viewport)
            
            await self._inject_stealth_scripts(fingerprint)
            
            logger.info(f"浏览器初始化成功，无头模式: {headless}")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            return False
    
    async def _inject_stealth_scripts(self, fingerprint: BrowserFingerprint):
        """
        注入反检测脚本
        """
        stealth_js = """
        () => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => '%s'});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            window.chrome = {runtime: {}};
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return '%s';
                if (parameter === 37446) return '%s';
                return getParameter.apply(this, arguments);
            };
        }
        """ % (fingerprint.platform, fingerprint.webgl_vendor, fingerprint.webgl_renderer)
        
        await self.page.evaluateOnNewDocument(stealth_js)
    
    async def close_browser(self):
        """
        关闭浏览器
        """
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {str(e)}")
            finally:
                self.browser = None
                self.page = None
    
    async def navigate(
        self,
        url: str,
        wait_selector: str = None,
        wait_timeout: int = None
    ) -> Optional[str]:
        """
        导航到页面
        
        Args:
            url: 目标URL
            wait_selector: 等待的选择器
            wait_timeout: 等待超时
            
        Returns:
            str: 页面内容
        """
        if not self.page:
            return None
        
        wait_timeout = wait_timeout or self.timeout
        
        try:
            await self.page.goto(url, {
                'waitUntil': 'networkidle2',
                'timeout': wait_timeout * 1000
            })
            
            if wait_selector:
                await self.page.waitForSelector(wait_selector, {
                    'timeout': wait_timeout * 1000
                })
            
            content = await self.page.content()
            return content
            
        except Exception as e:
            logger.error(f"页面导航失败: {url}, 错误: {str(e)}")
            return None
    
    async def scroll_page(self, pause_time: float = 1.0):
        """
        滚动页面
        """
        if not self.page:
            return
        
        try:
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(pause_time)
        except Exception as e:
            logger.warning(f"滚动页面失败: {str(e)}")
    
    async def get_cookies(self) -> List[Dict]:
        """
        获取 Cookies
        """
        if not self.page:
            return []
        
        try:
            cookies = await self.page.cookies()
            return cookies
        except Exception as e:
            logger.error(f"获取 Cookies 失败: {str(e)}")
            return []
    
    async def set_cookies(self, cookies: List[Dict]):
        """
        设置 Cookies
        """
        if not self.page or not cookies:
            return
        
        try:
            await self.page.setCookie(*cookies)
        except Exception as e:
            logger.error(f"设置 Cookies 失败: {str(e)}")
    
    async def screenshot(self, filepath: str) -> bool:
        """
        截图
        """
        if not self.page:
            return False
        
        try:
            await self.page.screenshot({'path': filepath})
            return True
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return False
    
    async def crawl_with_fallback(
        self,
        url: str,
        **kwargs
    ) -> CrawlResult:
        """
        使用多级降级策略采集
        
        Args:
            url: 目标URL
            **kwargs: 其他参数
            
        Returns:
            CrawlResult: 采集结果
        """
        start_time = time.time()
        
        for strategy in self._fallback_strategy:
            self._current_strategy = strategy
            
            try:
                if strategy == CrawlStrategy.API.value:
                    result = await self._crawl_by_api(url, **kwargs)
                elif strategy == CrawlStrategy.HEADLESS.value:
                    result = await self._crawl_by_headless(url, **kwargs)
                elif strategy == CrawlStrategy.STEALTH.value:
                    result = await self._crawl_by_stealth(url, **kwargs)
                else:
                    continue
                
                if result.success:
                    result.strategy = strategy
                    result.duration = time.time() - start_time
                    return result
                    
            except Exception as e:
                logger.warning(f"策略 {strategy} 执行失败: {str(e)}")
                continue
        
        return CrawlResult(
            success=False,
            error_message='所有采集策略均失败',
            duration=time.time() - start_time
        )
    
    async def _crawl_by_api(self, url: str, **kwargs) -> CrawlResult:
        """
        API 直连采集（子类可重写）
        """
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        data = await self.parse_response(html, **kwargs)
                        return CrawlResult(success=True, data=data)
                    else:
                        return CrawlResult(success=False, error_message=f'HTTP {response.status}')
        except Exception as e:
            return CrawlResult(success=False, error_message=str(e))
    
    async def _crawl_by_headless(self, url: str, **kwargs) -> CrawlResult:
        """
        无头浏览器采集
        """
        try:
            browser_ok = await self.init_browser(headless=True)
            if not browser_ok or not self.page:
                return CrawlResult(success=False, error_message='浏览器初始化失败')
            html = await self.navigate(url, kwargs.get('wait_selector'))
            
            if html:
                data = await self.parse_response(html, **kwargs)
                return CrawlResult(success=True, data=data)
            else:
                return CrawlResult(success=False, error_message='页面加载失败')
        except Exception as e:
            return CrawlResult(success=False, error_message=str(e))
        finally:
            await self.close_browser()
    
    async def _crawl_by_stealth(self, url: str, **kwargs) -> CrawlResult:
        """
        反检测模式采集
        """
        try:
            fingerprint = BrowserFingerprint.random_fingerprint()
            browser_ok = await self.init_browser(headless=True, fingerprint=fingerprint)
            if not browser_ok or not self.page:
                return CrawlResult(success=False, error_message='浏览器初始化失败')
            
            if self.proxy_config.enabled:
                if self.proxy_config.username:
                    await self.page.authenticate({
                        'username': self.proxy_config.username,
                        'password': self.proxy_config.password
                    })
            
            await asyncio.sleep(random.uniform(1, 3))
            
            html = await self.navigate(url, kwargs.get('wait_selector'))
            
            if html:
                data = await self.parse_response(html, **kwargs)
                return CrawlResult(success=True, data=data)
            else:
                return CrawlResult(success=False, error_message='页面加载失败')
        except Exception as e:
            return CrawlResult(success=False, error_message=str(e))
        finally:
            await self.close_browser()
    
    @abstractmethod
    async def parse_response(self, html: str, **kwargs) -> List[Dict[str, Any]]:
        """
        解析响应（子类必须实现）
        """
        pass
    
    @abstractmethod
    async def crawl(self, **kwargs) -> CrawlResult:
        """
        执行采集（子类必须实现）
        """
        pass
