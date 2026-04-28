"""
爬虫策略基类
定义策略接口，实现多种采集策略
"""
import time
import random
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from ..managers.user_agent_manager import UserAgentManager
from ..managers.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """
    爬取结果
    """
    success: bool
    content: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CrawlStrategy(ABC):
    """
    爬虫策略基类
    定义统一的采集接口，支持策略模式切换采集方式
    """

    def __init__(
        self,
        user_agent_manager: UserAgentManager = None,
        proxy_manager: ProxyManager = None,
        delay_min: float = 1.0,
        delay_max: float = 3.0
    ):
        """
        初始化策略

        Args:
            user_agent_manager: UA管理器
            proxy_manager: 代理管理器
            delay_min: 最小延迟（秒）
            delay_max: 最大延迟（秒）
        """
        self.user_agent_manager = user_agent_manager or UserAgentManager()
        self.proxy_manager = proxy_manager
        self.delay_min = delay_min
        self.delay_max = delay_max
        self._request_count = 0

    def delay(self):
        """执行延迟"""
        delay_time = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay_time)

    @abstractmethod
    def fetch(self, url: str, **kwargs) -> CrawlResult:
        """
        抓取页面

        Args:
            url: 目标URL
            **kwargs: 其他参数

        Returns:
            CrawlResult: 抓取结果
        """
        pass

    def get_request_count(self) -> int:
        """获取请求计数"""
        return self._request_count

    def reset_count(self):
        """重置请求计数"""
        self._request_count = 0


class RequestStrategy(CrawlStrategy):
    """
    基于 requests 库的采集策略
    适用于普通网页和 API 请求
    """

    def __init__(
        self,
        user_agent_manager: UserAgentManager = None,
        proxy_manager: ProxyManager = None,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs
    ):
        """
        初始化 Request 策略

        Args:
            user_agent_manager: UA管理器
            proxy_manager: 代理管理器
            delay_min: 最小延迟
            delay_max: 最大延迟
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
        """
        super().__init__(user_agent_manager, proxy_manager, delay_min, delay_max)
        self.timeout = timeout
        self.max_retries = max_retries

        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent_manager.get_random(),
        }

    def fetch(self, url: str, **kwargs) -> CrawlResult:
        """
        使用 requests 抓取页面

        Args:
            url: 目标URL
            **kwargs: 其他参数（如 params, data, headers, cookies 等）

        Returns:
            CrawlResult: 抓取结果
        """
        self._request_count += 1
        self.delay()

        try:
            headers = self._get_headers()
            if 'headers' in kwargs:
                headers.update(kwargs.pop('headers'))

            proxies = None
            if self.proxy_manager:
                proxy = self.proxy_manager.get_proxy()
                if proxy:
                    proxies = self.proxy_manager.get_proxy_dict(proxy)

            response = self.session.get(
                url,
                timeout=self.timeout,
                proxies=proxies,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            return CrawlResult(
                success=True,
                content=response.text,
                status_code=response.status_code,
                metadata={
                    'url': response.url,
                    'encoding': response.encoding,
                    'proxy': proxies.get('http') if proxies else None
                }
            )

        except Exception as e:
            logger.error(f"Request策略抓取失败: {url}, 错误: {str(e)}")
            return CrawlResult(
                success=False,
                error=str(e),
                metadata={'url': url}
            )


class SeleniumStrategy(CrawlStrategy):
    """
    基于 Selenium 的采集策略
    适用于需要 JavaScript 渲染的页面
    """

    def __init__(
        self,
        user_agent_manager: UserAgentManager = None,
        proxy_manager: ProxyManager = None,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        headless: bool = True,
        timeout: int = 30,
        page_load_timeout: int = 60,
        implicit_wait: int = 10,
        **kwargs
    ):
        """
        初始化 Selenium 策略

        Args:
            user_agent_manager: UA管理器
            proxy_manager: 代理管理器
            delay_min: 最小延迟
            delay_max: 最大延迟
            headless: 是否无头模式
            timeout: 元素等待超时
            page_load_timeout: 页面加载超时
            implicit_wait: 隐式等待
        """
        super().__init__(user_agent_manager, proxy_manager, delay_min, delay_max)
        self.headless = headless
        self.timeout = timeout
        self.page_load_timeout = page_load_timeout
        self.implicit_wait = implicit_wait
        self._driver = None
        self._options = None

    def _get_chrome_options(self):
        """获取 Chrome 选项"""
        from selenium.webdriver.chrome.options import Options

        if self._options is not None:
            return self._options

        options = Options()

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-web-security')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={self.user_agent_manager.get_chrome()}')

        if self.headless:
            options.add_argument('--headless=new')

        if self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            if proxy:
                proxy_dict = self.proxy_manager.get_proxy_dict(proxy)
                if proxy_dict:
                    proxy_url = proxy_dict.get('http', proxy_dict.get('https', proxy))
                    if not proxy_url.startswith('socks'):
                        options.add_argument(f'--proxy-server={proxy_url}')

        self._options = options
        return options

    def _inject_stealth_js(self, driver):
        """注入反检测脚本"""
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
        window.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'permissions', {
            query: () => Promise.resolve({state: 'granted'})
        });
        """
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
        except Exception as e:
            logger.warning(f"注入反检测脚本失败: {str(e)}")

    def _init_driver(self):
        """初始化 WebDriver"""
        if self._driver is not None:
            return

        import os
        import glob
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.common.exceptions import WebDriverException

        options = self._get_chrome_options()

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe",
        ]
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                break

        try:
            chromedriver_path = self._find_chromedriver()
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
                self._driver = webdriver.Chrome(service=service, options=options)
            else:
                self._driver = webdriver.Chrome(options=options)

            self._driver.set_page_load_timeout(self.page_load_timeout)
            self._driver.implicitly_wait(self.implicit_wait)

            self._inject_stealth_js(self._driver)
            logger.info("Selenium WebDriver 初始化成功")

        except WebDriverException as e:
            logger.error(f"WebDriver 初始化失败: {str(e)}")
            raise

    def _find_chromedriver(self) -> Optional[str]:
        """查找可用的 ChromeDriver"""
        import os
        import glob

        possible_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chromedriver.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chromedriver.exe'),
        ]

        cache_dir = os.path.join(os.environ.get('USERPROFILE', ''), '.cache', 'selenium', 'chromedriver', 'win64')
        if os.path.exists(cache_dir):
            versions = sorted(glob.glob(os.path.join(cache_dir, '*', 'chromedriver.exe')), reverse=True)
            if versions:
                return versions[0]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        chromedriver_in_path = None
        for path in os.environ.get('PATH', '').split(os.pathsep):
            full_path = os.path.join(path, 'chromedriver.exe')
            if os.path.exists(full_path):
                chromedriver_in_path = full_path
                break

        return chromedriver_in_path

    def fetch(self, url: str, **kwargs) -> CrawlResult:
        """
        使用 Selenium 抓取页面

        Args:
            url: 目标URL
            **kwargs: 其他参数（如 wait_selector, wait_type 等）

        Returns:
            CrawlResult: 抓取结果
        """
        from selenium.common.exceptions import TimeoutException, WebDriverException

        self._request_count += 1
        self.delay()

        wait_selector = kwargs.get('wait_selector')
        wait_type = kwargs.get('wait_type', 'css')

        try:
            self._init_driver()

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            logger.info(f"正在访问: {url}")
            self._driver.get(url)

            if wait_selector:
                wait_by = By.CSS_SELECTOR if wait_type == 'css' else By.XPATH
                WebDriverWait(self._driver, self.timeout).until(
                    EC.presence_of_element_located((wait_by, wait_selector))
                )

            return CrawlResult(
                success=True,
                content=self._driver.page_source,
                status_code=200,
                metadata={
                    'url': url,
                    'title': self._driver.title if hasattr(self._driver, 'title') else None
                }
            )

        except TimeoutException:
            logger.error(f"页面加载超时: {url}")
            return CrawlResult(success=False, error="页面加载超时", metadata={'url': url})

        except WebDriverException as e:
            logger.error(f"Selenium抓取失败: {url}, 错误: {str(e)}")
            return CrawlResult(success=False, error=str(e), metadata={'url': url})

        except Exception as e:
            logger.error(f"Selenium抓取异常: {url}, 错误: {str(e)}")
            return CrawlResult(success=False, error=str(e), metadata={'url': url})

    def close(self):
        """关闭 WebDriver"""
        if self._driver:
            try:
                self._driver.quit()
            except Exception as e:
                logger.warning(f"关闭驱动时出错: {str(e)}")
            finally:
                self._driver = None

    def __del__(self):
        """析构时关闭驱动"""
        self.close()


def create_strategy(strategy_type: str = 'requests', **kwargs) -> CrawlStrategy:
    """
    工厂函数：创建爬虫策略

    Args:
        strategy_type: 策略类型 ('requests', 'selenium')
        **kwargs: 策略参数

    Returns:
        CrawlStrategy: 爬虫策略实例
    """
    if strategy_type == 'requests' or strategy_type == 'request':
        return RequestStrategy(**kwargs)
    elif strategy_type == 'selenium' or strategy_type == 'selenium':
        return SeleniumStrategy(**kwargs)
    else:
        raise ValueError(f"不支持的策略类型: {strategy_type}")