"""
爬虫模块 - 基础爬虫类（优化版）
"""
import os
import time
import random
import glob
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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


class UserAgentManager:
    """
    User-Agent管理器
    """
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ]
    
    @classmethod
    def get_random(cls) -> str:
        """
        获取随机User-Agent
        """
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_chrome_user_agent(cls) -> str:
        """
        获取Chrome User-Agent
        """
        chrome_agents = [ua for ua in cls.USER_AGENTS if 'Chrome' in ua and 'Edg' not in ua]
        return random.choice(chrome_agents) if chrome_agents else cls.USER_AGENTS[0]


class ProxyManager:
    """
    代理管理器
    """
    
    def __init__(self, proxy_list: List[str] = None):
        """
        初始化代理管理器
        
        Args:
            proxy_list: 代理列表，格式如 ['http://ip:port', 'socks5://ip:port']
        """
        self.proxy_list = proxy_list or []
        self.current_index = 0
        self.failed_proxies = set()
    
    def get_proxy(self) -> Optional[str]:
        """
        获取可用代理
        """
        available = [p for p in self.proxy_list if p not in self.failed_proxies]
        if not available:
            self.failed_proxies.clear()
            available = self.proxy_list
        
        if available:
            proxy = random.choice(available)
            return proxy
        return None
    
    def mark_failed(self, proxy: str):
        """
        标记代理失败
        """
        self.failed_proxies.add(proxy)
    
    def add_proxy(self, proxy: str):
        """
        添加代理
        """
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)


class AntiDetection:
    """
    反检测工具类
    """
    
    @staticmethod
    def get_stealth_js() -> str:
        """
        获取反检测JS脚本
        """
        return """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
        window.chrome = {runtime: {}};
        Object.defineProperty(navigator, 'permissions', {
            query: () => Promise.resolve({state: 'granted'})
        });
        """
    
    @staticmethod
    def get_chrome_options(options: Options = None) -> Options:
        """
        获取反检测Chrome选项
        """
        if options is None:
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
        
        return options


class BaseCrawler(ABC):
    """
    爬虫基类（优化版）
    """
    
    def __init__(self, config: CrawlerConfig = None):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置
        """
        self.config = config or CrawlerConfig()
        self.driver = None
        self.session = self._create_session()
        self.proxy_manager = ProxyManager(self.config.proxy_list) if self.config.proxy_enabled else None
        self._request_count = 0
    
    def _create_session(self) -> requests.Session:
        """
        创建带重试机制的Session
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头
        """
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if self.config.user_agent_rotation:
            headers['User-Agent'] = UserAgentManager.get_random()
        else:
            headers['User-Agent'] = UserAgentManager.get_chrome_user_agent()
        
        return headers
    
    def _delay(self):
        """
        请求延迟
        """
        delay = random.uniform(self.config.request_delay_min, self.config.request_delay_max)
        time.sleep(delay)
    
    def init_driver(self):
        """
        初始化Selenium驱动
        """
        if self.driver is None:
            options = AntiDetection.get_chrome_options()

            if self.config.headless:
                options.add_argument('--headless=new')

            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument(f'--user-agent={UserAgentManager.get_chrome_user_agent()}')

            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe",
            ]
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    options.binary_location = chrome_path
                    break

            if self.config.proxy_enabled and self.proxy_manager:
                proxy = self.proxy_manager.get_proxy()
                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')

            try:
                chromedriver_path = self._find_chromedriver()
                if chromedriver_path:
                    from selenium.webdriver.chrome.service import Service
                    service = Service(executable_path=chromedriver_path)
                    self.driver = webdriver.Chrome(service=service, options=options)
                else:
                    self.driver = webdriver.Chrome(options=options)

                self.driver.set_page_load_timeout(self.config.page_load_timeout)
                self.driver.implicitly_wait(self.config.implicit_wait)

                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': AntiDetection.get_stealth_js()
                })

                logger.info("Selenium驱动初始化成功")
            except WebDriverException as e:
                logger.error(f"Selenium驱动初始化失败: {str(e)}")
                raise

    def _find_chromedriver(self) -> Optional[str]:
        """查找可用的ChromeDriver"""
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
    
    def close_driver(self):
        """
        关闭Selenium驱动
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"关闭驱动时出错: {str(e)}")
            finally:
                self.driver = None
    
    def get_page(self, url: str, wait_selector: str = None, wait_type: str = 'css') -> Optional[str]:
        """
        获取页面内容（使用Selenium）
        """
        self._request_count += 1
        self._delay()
        
        try:
            self.init_driver()
            logger.info(f"正在访问: {url}")
            self.driver.get(url)
            
            if wait_selector:
                wait_by = By.CSS_SELECTOR if wait_type == 'css' else By.XPATH
                WebDriverWait(self.driver, self.config.timeout).until(
                    EC.presence_of_element_located((wait_by, wait_selector))
                )
            
            return self.driver.page_source
        except TimeoutException:
            logger.error(f"页面加载超时: {url}")
            return None
        except Exception as e:
            logger.error(f"获取页面失败: {url}, 错误: {str(e)}")
            return None
    
    def get_page_requests(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[str]:
        """
        使用requests获取页面内容
        """
        self._request_count += 1
        self._delay()
        
        try:
            request_headers = self._get_headers()
            if headers:
                request_headers.update(headers)
            
            proxies = None
            if self.config.proxy_enabled and self.proxy_manager:
                proxy = self.proxy_manager.get_proxy()
                if proxy:
                    proxies = {'http': proxy, 'https': proxy}
            
            response = self.session.get(
                url, 
                params=params, 
                headers=request_headers,
                timeout=self.config.timeout,
                proxies=proxies
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            logger.info(f"请求成功: {url}, 状态码: {response.status_code}")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"requests获取页面失败: {url}, 错误: {str(e)}")
            if self.config.proxy_enabled and self.proxy_manager and proxies:
                self.proxy_manager.mark_failed(proxies.get('http'))
            return None
    
    def parse_html(self, html: str, parser: str = 'html.parser') -> BeautifulSoup:
        """
        解析HTML
        """
        return BeautifulSoup(html, parser)
    
    def find_element(self, by: By, value: str, timeout: int = None) -> Optional[Any]:
        """
        查找元素
        """
        timeout = timeout or self.config.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def find_elements(self, by: By, value: str) -> List[Any]:
        """
        查找多个元素
        """
        try:
            return self.driver.find_elements(by, value)
        except NoSuchElementException:
            return []
    
    def click_element(self, by: By, value: str, timeout: int = None) -> bool:
        """
        点击元素
        """
        timeout = timeout or self.config.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except Exception:
            return False
    
    def input_text(self, by: By, value: str, text: str, clear: bool = True) -> bool:
        """
        输入文本
        """
        try:
            element = self.find_element(by, value)
            if element:
                if clear:
                    element.clear()
                element.send_keys(text)
                return True
            return False
        except Exception:
            return False
    
    def scroll_to_bottom(self, pause_time: float = 1.0):
        """
        滚动到页面底部
        """
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def scroll_into_view(self, element):
        """
        滚动到元素可见
        """
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
    
    def wait_for_ajax(self, timeout: int = None):
        """
        等待AJAX加载完成
        """
        timeout = timeout or self.config.timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return typeof jQuery != 'undefined' ? jQuery.active == 0 : true")
            )
        except Exception:
            pass
    
    def get_cookies(self) -> List[Dict]:
        """
        获取Cookies
        """
        if self.driver:
            return self.driver.get_cookies()
        return []
    
    def set_cookies(self, cookies: List[Dict]):
        """
        设置Cookies
        """
        if self.driver and cookies:
            for cookie in cookies:
                self.driver.add_cookie(cookie)
    
    def save_cookies(self, filepath: str):
        """
        保存Cookies到文件
        """
        cookies = self.get_cookies()
        with open(filepath, 'w') as f:
            json.dump(cookies, f)
    
    def load_cookies(self, filepath: str):
        """
        从文件加载Cookies
        """
        try:
            with open(filepath, 'r') as f:
                cookies = json.load(f)
            self.set_cookies(cookies)
        except FileNotFoundError:
            logger.warning(f"Cookies文件不存在: {filepath}")
    
    def take_screenshot(self, filepath: str):
        """
        截图
        """
        if self.driver:
            self.driver.save_screenshot(filepath)
            logger.info(f"截图已保存: {filepath}")
    
    def get_request_count(self) -> int:
        """
        获取请求计数
        """
        return self._request_count
    
    @abstractmethod
    def crawl(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        爬取数据（抽象方法，子类必须实现）
        """
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()
        logger.info(f"爬虫结束，总请求数: {self._request_count}")
