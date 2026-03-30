"""
爬虫模块 - 反爬虫策略
"""
import time
import random
import logging
import hashlib
from typing import Dict, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """
    请求频率限制配置
    """
    requests_per_second: float = 1.0
    burst_size: int = 5
    cooldown_period: float = 60.0


class RateLimiter:
    """
    请求频率限制器
    """
    
    def __init__(self, config: RateLimitConfig = None):
        """
        初始化频率限制器
        """
        self.config = config or RateLimitConfig()
        self._last_request_time = 0
        self._request_count = 0
        self._burst_count = 0
        self._cooldown_start = 0
    
    def wait(self):
        """
        等待直到可以发送请求
        """
        current_time = time.time()
        
        if self._burst_count >= self.config.burst_size:
            if current_time - self._cooldown_start < self.config.cooldown_period:
                wait_time = self.config.cooldown_period - (current_time - self._cooldown_start)
                logger.info(f"触发冷却期，等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
            self._burst_count = 0
        
        min_interval = 1.0 / self.config.requests_per_second
        elapsed = current_time - self._last_request_time
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed + random.uniform(0, 0.5)
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
        self._request_count += 1
        self._burst_count += 1
        
        if self._burst_count == 1:
            self._cooldown_start = time.time()
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        """
        return {
            'total_requests': self._request_count,
            'current_burst': self._burst_count,
            'last_request': self._last_request_time
        }


class FingerprintGenerator:
    """
    浏览器指纹生成器
    """
    
    @staticmethod
    def generate_canvas_fingerprint() -> str:
        """
        生成Canvas指纹
        """
        random_data = ''.join([str(random.randint(0, 9)) for _ in range(100)])
        return hashlib.md5(random_data.encode()).hexdigest()
    
    @staticmethod
    def generate_webgl_fingerprint() -> Dict:
        """
        生成WebGL指纹
        """
        vendors = ['Google Inc.', 'Intel Inc.', 'NVIDIA Corporation', 'AMD']
        renderers = [
            'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.6)',
            'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060, OpenGL 4.6)',
            'ANGLE (AMD, AMD Radeon RX 580, OpenGL 4.6)'
        ]
        
        return {
            'vendor': random.choice(vendors),
            'renderer': random.choice(renderers)
        }
    
    @staticmethod
    def generate_audio_fingerprint() -> str:
        """
        生成音频指纹
        """
        return f"{random.uniform(124.0434, 124.0435):.4f}"
    
    @staticmethod
    def generate_screen_fingerprint() -> Dict:
        """
        生成屏幕指纹
        """
        resolutions = [
            (1920, 1080), (2560, 1440), (1366, 768), (1536, 864)
        ]
        width, height = random.choice(resolutions)
        
        return {
            'width': width,
            'height': height,
            'colorDepth': 24,
            'pixelDepth': 24
        }
    
    @classmethod
    def generate_full_fingerprint(cls) -> Dict:
        """
        生成完整指纹
        """
        return {
            'canvas': cls.generate_canvas_fingerprint(),
            'webgl': cls.generate_webgl_fingerprint(),
            'audio': cls.generate_audio_fingerprint(),
            'screen': cls.generate_screen_fingerprint(),
            'timezone': -480,
            'language': 'zh-CN',
            'platform': 'Win32',
            'hardwareConcurrency': random.choice([4, 8, 12, 16]),
            'deviceMemory': random.choice([4, 8, 16])
        }


class BehaviorSimulator:
    """
    用户行为模拟器
    """
    
    @staticmethod
    def random_mouse_movement(driver, element=None):
        """
        随机鼠标移动
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            
            if element:
                actions.move_to_element(element)
            
            for _ in range(random.randint(1, 3)):
                x_offset = random.randint(-50, 50)
                y_offset = random.randint(-50, 50)
                actions.move_by_offset(x_offset, y_offset)
                actions.pause(random.uniform(0.1, 0.3))
            
            actions.perform()
        except Exception as e:
            logger.warning(f"鼠标移动模拟失败: {str(e)}")
    
    @staticmethod
    def human_like_input(element, text: str, driver):
        """
        模拟人类输入
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            element.clear()
            
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
        except Exception as e:
            logger.warning(f"输入模拟失败: {str(e)}")
    
    @staticmethod
    def random_scroll(driver, times: int = 3):
        """
        随机滚动
        """
        try:
            for _ in range(times):
                scroll_amount = random.randint(100, 500)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.3, 0.8))
        except Exception as e:
            logger.warning(f"滚动模拟失败: {str(e)}")
    
    @staticmethod
    def random_click(driver, element):
        """
        随机点击
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            
            BehaviorSimulator.random_mouse_movement(driver, element)
            
            actions.pause(random.uniform(0.1, 0.3))
            actions.click(element)
            actions.perform()
            
        except Exception as e:
            logger.warning(f"点击模拟失败: {str(e)}")


class CaptchaHandler:
    """
    验证码处理器
    """
    
    def __init__(self, ocr_service=None):
        """
        初始化验证码处理器
        
        Args:
            ocr_service: OCR服务实例
        """
        self.ocr_service = ocr_service
    
    def handle_image_captcha(self, image_url: str) -> Optional[str]:
        """
        处理图片验证码
        """
        if not self.ocr_service:
            logger.warning("OCR服务未配置")
            return None
        
        try:
            result = self.ocr_service.recognize_general(image_url)
            if result:
                captcha_text = result.get('text', '').strip()
                logger.info(f"验证码识别结果: {captcha_text}")
                return captcha_text
        except Exception as e:
            logger.error(f"验证码识别失败: {str(e)}")
        
        return None
    
    def handle_slider_captcha(self, driver, slider_element, distance: int):
        """
        处理滑块验证码
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            actions.click_and_hold(slider_element)
            
            current = 0
            while current < distance:
                move = random.randint(5, 15)
                actions.move_by_offset(move, random.randint(-2, 2))
                current += move
                time.sleep(random.uniform(0.01, 0.03))
            
            actions.release()
            actions.perform()
            
            return True
        except Exception as e:
            logger.error(f"滑块验证码处理失败: {str(e)}")
            return False


class AntiDetectionStrategy:
    """
    反检测策略
    """
    
    def __init__(self, driver=None):
        """
        初始化反检测策略
        """
        self.driver = driver
    
    def apply(self):
        """
        应用反检测策略
        """
        if not self.driver:
            return
        
        self._inject_stealth_scripts()
        self._modify_navigator()
    
    def _inject_stealth_scripts(self):
        """
        注入反检测脚本
        """
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ];
            }
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
        
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        Object.defineProperty(navigator, 'permissions', {
            query: () => Promise.resolve({ state: 'granted' })
        });
        """
        
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
        except Exception as e:
            logger.warning(f"注入反检测脚本失败: {str(e)}")
    
    def _modify_navigator(self):
        """
        修改导航器属性
        """
        pass


def with_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟
        backoff: 延迟增长因子
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}, {current_delay:.1f}秒后重试")
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"所有重试均失败: {str(last_exception)}")
            raise last_exception
        
        return wrapper
    return decorator


def with_rate_limit(requests_per_second: float = 1.0):
    """
    频率限制装饰器
    """
    limiter = RateLimiter(RateLimitConfig(requests_per_second=requests_per_second))
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
