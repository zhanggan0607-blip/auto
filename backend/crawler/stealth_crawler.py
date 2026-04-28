"""
智能采集模块 - 增强版反检测爬虫
基于Pyppeteer的高级反检测爬虫，支持：
- 完整的浏览器指纹伪装
- 人类行为模拟
- 验证码自动识别
- 代理轮换
- Cookie管理

注意：CrawlResult, ProxyConfig, BrowserFingerprint 已移至 common_types.py
"""
import asyncio
import logging
import random
import time
import json
import base64
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse

from django.conf import settings
from core.constants import CrawlStrategy, CrawlStatus

from .common_types import CrawlResult, ProxyConfig, BrowserFingerprint
from .pyppeteer_crawler import PyppeteerCrawler


logger = logging.getLogger(__name__)


# 保留 HumanBehaviorSimulator 和 CaptchaHandler 在此文件中（它们是功能性类，不是数据类）


class HumanBehaviorSimulator:
    """
    人类行为模拟器
    模拟真实用户的鼠标移动、点击、滚动等行为
    """
    
    @staticmethod
    async def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    @staticmethod
    async def human_like_mouse_move(page, target_x: int, target_y: int, steps: int = 20):
        current_x, current_y = 0, 0
        for i in range(steps):
            progress = (i + 1) / steps
            ease_progress = progress * progress * (3 - 2 * progress)
            
            noise_x = random.randint(-5, 5)
            noise_y = random.randint(-5, 5)
            
            x = int(current_x + (target_x - current_x) * ease_progress + noise_x)
            y = int(current_y + (target_y - current_y) * ease_progress + noise_y)
            
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.05))
        
        await page.mouse.move(target_x, target_y)
    
    @staticmethod
    async def human_like_click(page, selector: str = None, x: int = None, y: int = None):
        if selector:
            element = await page.querySelector(selector)
            if element:
                box = await element.boundingBox()
                if box:
                    x = int(box['x'] + box['width'] / 2 + random.randint(-5, 5))
                    y = int(box['y'] + box['height'] / 2 + random.randint(-5, 5))
        
        if x is not None and y is not None:
            await HumanBehaviorSimulator.human_like_mouse_move(page, x, y)
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.mouse.down()
            await asyncio.sleep(random.uniform(0.05, 0.1))
            await page.mouse.up()
    
    @staticmethod
    async def human_like_input(page, selector: str, text: str):
        element = await page.querySelector(selector)
        if not element:
            return False
        
        await element.click()
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        for char in text:
            await page.keyboard.press(char)
            await asyncio.sleep(random.uniform(0.03, 0.12))
        
        return True
    
    @staticmethod
    async def random_scroll(page, times: int = 3):
        for _ in range(times):
            scroll_amount = random.randint(100, 400)
            direction = random.choice([1, -1])
            
            await page.evaluate(f'window.scrollBy(0, {scroll_amount * direction})')
            await asyncio.sleep(random.uniform(0.3, 0.8))
    
    @staticmethod
    async def random_mouse_movement(page, movements: int = 5):
        viewport = await page.evaluate('({width: window.innerWidth, height: window.innerHeight})')
        
        for _ in range(movements):
            x = random.randint(100, viewport['width'] - 100)
            y = random.randint(100, viewport['height'] - 100)
            await HumanBehaviorSimulator.human_like_mouse_move(page, x, y, steps=random.randint(10, 25))
            await asyncio.sleep(random.uniform(0.1, 0.3))


class CaptchaHandler:
    """
    验证码处理器
    支持图片验证码、滑块验证码等
    """
    
    def __init__(self, ocr_service=None):
        self.ocr_service = ocr_service
    
    async def detect_captcha(self, page) -> Dict[str, Any]:
        captcha_selectors = [
            {'type': 'image', 'selector': 'img[src*="captcha"], img[src*="verify"], .captcha-img, #captcha_img'},
            {'type': 'slider', 'selector': '.slide-verify, .slider-wrap, #nc_1_wrapper'},
            {'type': 'click', 'selector': '.geetest-wrap, .geetest_slider'},
        ]
        
        for captcha in captcha_selectors:
            element = await page.querySelector(captcha['selector'])
            if element:
                return {'detected': True, 'type': captcha['type'], 'selector': captcha['selector']}
        
        return {'detected': False}
    
    async def handle_image_captcha(self, page, selector: str) -> Optional[str]:
        if not self.ocr_service:
            logger.warning("OCR服务未配置，无法识别验证码")
            return None
        
        try:
            element = await page.querySelector(selector)
            if not element:
                return None
            
            screenshot = await element.screenshot({'encoding': 'base64'})
            image_bytes = base64.b64decode(screenshot)
            
            result = self.ocr_service.recognize_captcha(image_content=image_bytes)
            
            if result.get('success'):
                captcha_text = result.get('captcha', '').strip()
                logger.info(f"验证码识别结果: {captcha_text}")
                return captcha_text
            
        except Exception as e:
            logger.error(f"验证码识别失败: {str(e)}")
        
        return None
    
    async def handle_slider_captcha(self, page, slider_selector: str) -> bool:
        try:
            slider = await page.querySelector(slider_selector)
            if not slider:
                return False
            
            box = await slider.boundingBox()
            if not box:
                return False
            
            start_x = box['x'] + box['width'] / 2
            start_y = box['y'] + box['height'] / 2
            
            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            
            distance = random.randint(250, 320)
            steps = random.randint(20, 35)
            
            for i in range(steps):
                progress = (i + 1) / steps
                ease_progress = progress * progress * (3 - 2 * progress)
                
                x = start_x + distance * ease_progress + random.randint(-2, 2)
                y = start_y + random.randint(-3, 3)
                
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            await asyncio.sleep(random.uniform(0.05, 0.1))
            await page.mouse.up()
            
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"滑块验证码处理失败: {str(e)}")
            return False


class StealthCrawler(ABC):
    """
    增强版反检测爬虫基类
    """
    
    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        max_retries: int = 3,
        timeout: int = 60,
        ocr_service=None
    ):
        self.proxy_config = proxy_config or ProxyConfig()
        self.max_retries = max_retries
        self.timeout = timeout
        self.ocr_service = ocr_service
        self.browser = None
        self.page = None
        self.context = None
        self._current_strategy = None
        self._fallback_strategy = ['stealth', 'headless']
        self._captcha_handler = CaptchaHandler(ocr_service)
        self._cookies_cache: Dict[str, List[Dict]] = {}
    
    async def init_browser(
        self,
        headless: bool = True,
        fingerprint: BrowserFingerprint = None,
        executablePath: str = None
    ) -> bool:
        from pyppeteer import launch
        
        try:
            fingerprint = fingerprint or BrowserFingerprint.random_fingerprint()
            
            args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                f'--window-size={fingerprint.viewport["width"]},{fingerprint.viewport["height"]}',
                f'--lang={fingerprint.locale}',
            ]
            
            if headless:
                args.append('--headless=new')
            
            launch_options = {
                'headless': headless,
                'args': args,
                'defaultViewport': fingerprint.viewport,
                'ignoreHTTPSErrors': True,
                'dumpio': False,
                'handleSIGINT': False,
                'handleSIGTERM': False,
                'handleSIGHUP': False,
            }
            
            if executablePath:
                launch_options['executablePath'] = executablePath
            
            if self.proxy_config.enabled:
                proxy = self.proxy_config.get_next_proxy()
                if proxy:
                    launch_options['args'].append(f'--proxy-server={proxy}')
            
            self.browser = await launch(launch_options)
            self.page = await self.browser.newPage()
            
            await self._setup_page(fingerprint)
            
            logger.info(f"浏览器初始化成功，无头模式: {headless}")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            return False
    
    async def _setup_page(self, fingerprint: BrowserFingerprint):
        await self.page.setUserAgent(fingerprint.user_agent)
        await self.page.setViewport(fingerprint.viewport)
        
        await self._inject_advanced_stealth_scripts(fingerprint)
        
        await self.page.setExtraHTTPHeaders({
            'Accept-Language': f'{fingerprint.locale},zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-CH-UA': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
        })
    
    async def _inject_advanced_stealth_scripts(self, fingerprint: BrowserFingerprint):
        stealth_js = f"""
        () => {{
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [
                    {{name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''}},
                    {{name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}}
                ]
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['zh-CN', 'zh', 'en']
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint.platform}'
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint.hardware_concurrency}
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint.device_memory}
            }});
            
            Object.defineProperty(navigator, 'language', {{
                get: () => 'zh-CN'
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            }});
            
            window.chrome = {{
                runtime: {{}},
                loadTimes: function() {{}},
                csi: function() {{}},
                app: {{}}
            }};
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fingerprint.webgl_vendor}';
                if (parameter === 37446) return '{fingerprint.webgl_renderer}';
                return getParameter.apply(this, arguments);
            }};
            
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fingerprint.webgl_vendor}';
                if (parameter === 37446) return '{fingerprint.webgl_renderer}';
                return getParameter2.apply(this, arguments);
            }};
            
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {{
                if (type === 'image/png' && this.width === 220 && this.height === 30) {{
                    const shift = {{r: '{fingerprint.canvas_noise[:2]}', g: '{fingerprint.canvas_noise[2:4]}', b: '{fingerprint.canvas_noise[4:6]}'}};
                }}
                return originalToDataURL.apply(this, arguments);
            }};
            
            Object.defineProperty(screen, 'width', {{get: () => {fingerprint.screen['width']}}});
            Object.defineProperty(screen, 'height', {{get: () => {fingerprint.screen['height']}}});
            Object.defineProperty(screen, 'availWidth', {{get: () => {fingerprint.screen['width']}}});
            Object.defineProperty(screen, 'availHeight', {{get: () => {fingerprint.screen['height'] - 40}}});
            Object.defineProperty(screen, 'colorDepth', {{get: () => {fingerprint.screen['colorDepth']}}});
            Object.defineProperty(screen, 'pixelDepth', {{get: () => {fingerprint.screen['colorDepth']}}});
            
            Object.defineProperty(Date.prototype, 'getTimezoneOffset', {{
                get: () => function() {{ return {fingerprint.timezone_offset}; }}
            }});
            
            const originalAudioContext = window.AudioContext || window.webkitAudioContext;
            if (originalAudioContext) {{
                const originalCreateAnalyser = originalAudioContext.prototype.createAnalyser;
                originalAudioContext.prototype.createAnalyser = function() {{
                    const analyser = originalCreateAnalyser.call(this);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData.bind(analyser);
                    analyser.getFloatFrequencyData = function(array) {{
                        originalGetFloatFrequencyData(array);
                        for (let i = 0; i < array.length; i++) {{
                            array[i] += (Math.random() - 0.5) * 0.0001;
                        }}
                    }};
                    return analyser;
                }};
            }}
            
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                }})
            }});
            
            window.outerWidth = window.innerWidth;
            window.outerHeight = window.innerHeight + 100;
        }}
        """
        
        await self.page.evaluateOnNewDocument(stealth_js)
    
    async def navigate_with_behavior(
        self,
        url: str,
        wait_selector: str = None,
        wait_timeout: int = None,
        simulate_human: bool = True
    ) -> Optional[str]:
        if not self.page:
            return None
        
        wait_timeout = wait_timeout or self.timeout
        
        try:
            if simulate_human:
                await HumanBehaviorSimulator.random_delay(0.5, 1.5)
            
            await self.page.goto(url, {
                'waitUntil': 'domcontentloaded',
                'timeout': wait_timeout * 1000
            })
            
            if simulate_human:
                await HumanBehaviorSimulator.random_delay(0.3, 0.8)
            
            captcha_info = await self._captcha_handler.detect_captcha(self.page)
            if captcha_info['detected']:
                handled = await self._handle_captcha(captcha_info)
                if not handled:
                    logger.warning("验证码处理失败")
            
            if wait_selector:
                await self.page.waitForSelector(wait_selector, {
                    'timeout': wait_timeout * 1000
                })
            
            if simulate_human:
                await HumanBehaviorSimulator.random_scroll(self.page, times=random.randint(1, 3))
                await HumanBehaviorSimulator.random_mouse_movement(self.page, movements=random.randint(2, 4))
            
            await self.page.waitFor(500)
            
            content = await self.page.content()
            return content
            
        except Exception as e:
            logger.error(f"页面导航失败: {url}, 错误: {str(e)}")
            return None
    
    async def _handle_captcha(self, captcha_info: Dict) -> bool:
        captcha_type = captcha_info['type']
        selector = captcha_info['selector']
        
        if captcha_type == 'image':
            captcha_text = await self._captcha_handler.handle_image_captcha(self.page, selector)
            if captcha_text:
                input_selectors = [
                    'input[name="captcha"]',
                    'input.captcha-input',
                    '#captcha_input',
                    'input[placeholder*="验证码"]'
                ]
                for input_sel in input_selectors:
                    input_el = await self.page.querySelector(input_sel)
                    if input_el:
                        await input_el.type(captcha_text)
                        return True
        
        elif captcha_type == 'slider':
            return await self._captcha_handler.handle_slider_captcha(self.page, selector)
        
        return False
    
    async def close_browser(self):
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {str(e)}")
            finally:
                self.browser = None
                self.page = None
    
    async def get_cookies(self, domain: str = None) -> List[Dict]:
        if not self.page:
            return []
        
        try:
            cookies = await self.page.cookies()
            if domain:
                cookies = [c for c in cookies if domain in c.get('domain', '')]
            return cookies
        except Exception as e:
            logger.error(f"获取Cookies失败: {str(e)}")
            return []
    
    async def set_cookies(self, cookies: List[Dict]):
        if not self.page or not cookies:
            return
        
        try:
            for cookie in cookies:
                await self.page.setCookie(cookie)
        except Exception as e:
            logger.error(f"设置Cookies失败: {str(e)}")
    
    def save_cookies_to_cache(self, domain: str, cookies: List[Dict], expire_hours: int = 24):
        self._cookies_cache[domain] = {
            'cookies': cookies,
            'expire_at': datetime.now() + timedelta(hours=expire_hours)
        }
    
    def get_cookies_from_cache(self, domain: str) -> Optional[List[Dict]]:
        cache_entry = self._cookies_cache.get(domain)
        if cache_entry and cache_entry['expire_at'] > datetime.now():
            return cache_entry['cookies']
        return None
    
    async def screenshot_base64(self) -> Optional[str]:
        if not self.page:
            return None
        
        try:
            screenshot = await self.page.screenshot({'encoding': 'base64'})
            return screenshot
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            return None
    
    async def execute_js(self, script: str) -> Any:
        if not self.page:
            return None
        
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            logger.error(f"执行JS失败: {str(e)}")
            return None
    
    async def wait_for_selector(self, selector: str, timeout: int = None) -> bool:
        if not self.page:
            return False
        
        try:
            await self.page.waitForSelector(selector, {'timeout': (timeout or self.timeout) * 1000})
            return True
        except Exception:
            return False
    
    async def wait_for_navigation(self, timeout: int = None):
        if not self.page:
            return
        
        try:
            await self.page.waitForNavigation({
                'timeout': (timeout or self.timeout) * 1000
            })
        except Exception as e:
            logger.warning(f"等待导航超时: {str(e)}")
    
    async def crawl_with_fallback(self, url: str, **kwargs) -> CrawlResult:
        start_time = time.time()
        
        for strategy in self._fallback_strategy:
            self._current_strategy = strategy
            
            try:
                if strategy == CrawlStrategy.STEALTH.value:
                    result = await self._crawl_by_stealth(url, **kwargs)
                elif strategy == CrawlStrategy.HEADLESS.value:
                    result = await self._crawl_by_headless(url, **kwargs)
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
    
    async def _crawl_by_stealth(self, url: str, **kwargs) -> CrawlResult:
        try:
            fingerprint = BrowserFingerprint.random_fingerprint()
            executable_path = PyppeteerCrawler.find_browser_executable()
            browser_ok = await self.init_browser(headless=True, fingerprint=fingerprint, executablePath=executable_path)
            if not browser_ok or not self.page:
                return CrawlResult(success=False, error_message='浏览器初始化失败')
            
            domain = urlparse(url).netloc
            cached_cookies = self.get_cookies_from_cache(domain)
            if cached_cookies:
                await self.set_cookies(cached_cookies)
            
            html = await self.navigate_with_behavior(
                url,
                wait_selector=kwargs.get('wait_selector'),
                simulate_human=True
            )
            
            if html:
                cookies = await self.get_cookies(domain)
                if cookies:
                    self.save_cookies_to_cache(domain, cookies)
                
                data = await self.parse_response(html, **kwargs)
                return CrawlResult(success=True, data=data)
            else:
                return CrawlResult(success=False, error_message='页面加载失败')
        except Exception as e:
            return CrawlResult(success=False, error_message=str(e))
        finally:
            await self.close_browser()
    
    async def _crawl_by_headless(self, url: str, **kwargs) -> CrawlResult:
        try:
            executable_path = PyppeteerCrawler.find_browser_executable()
            browser_ok = await self.init_browser(headless=True, executablePath=executable_path)
            if not browser_ok or not self.page:
                return CrawlResult(success=False, error_message='浏览器初始化失败')
            html = await self.navigate_with_behavior(
                url,
                wait_selector=kwargs.get('wait_selector'),
                simulate_human=False
            )
            
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
        pass
    
    @abstractmethod
    async def crawl(self, **kwargs) -> CrawlResult:
        pass
