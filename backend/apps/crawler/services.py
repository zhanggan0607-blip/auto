"""
SAAS采集模块 - 通用爬虫引擎
"""
import re
import time
import random
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from crawler.base_crawler import BaseCrawler, CrawlerConfig
from crawler.multi_strategy_crawler import MultiStrategyCrawler, AdaptiveRateLimiter, CrawlMonitor, CrawlStrategy

logger = logging.getLogger(__name__)


class UniversalCrawlerEngine(BaseCrawler):
    """
    通用爬虫引擎 - 支持任意网站的自动识别和采集
    支持多级降级策略和自适应频率控制
    """

    _cached_chromedriver_path = None

    def __init__(self, config: CrawlerConfig = None, website_template=None,
                 enable_multi_strategy: bool = True, proxy_list: List[str] = None):
        """
        初始化通用爬虫引擎

        Args:
            config: 爬虫配置
            website_template: 网站模板对象
            enable_multi_strategy: 启用多级降级策略
            proxy_list: 代理列表
        """
        super().__init__(config)
        self.website_template = website_template
        self.detected_patterns = {}

        self.enable_multi_strategy = enable_multi_strategy
        if enable_multi_strategy:
            self.multi_strategy_crawler = MultiStrategyCrawler(
                proxy_enabled=bool(proxy_list),
                proxy_list=proxy_list or []
            )
            self.crawl_monitor = self.multi_strategy_crawler.monitor
            self.rate_limiter = self.multi_strategy_crawler.rate_limiter
        else:
            self.multi_strategy_crawler = None
            self.crawl_monitor = None
            self.rate_limiter = None
        
    def crawl(self, target_url: str, keywords: List[str] = None,
              max_pages: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        通用爬取方法

        Args:
            target_url: 目标URL
            keywords: 搜索关键词列表
            max_pages: 最大爬取页数
            **kwargs: 其他参数

        Returns:
            list: 爬取结果列表
        """
        results = []

        try:
            if self.enable_multi_strategy and self.multi_strategy_crawler:
                results = self._crawl_with_multi_strategy(target_url, keywords, max_pages, **kwargs)
            else:
                self.init_driver()
                if self.website_template:
                    results = self._crawl_with_template(target_url, keywords, max_pages, **kwargs)
                else:
                    results = self._crawl_auto_detect(target_url, keywords, max_pages, **kwargs)

            logger.info(f"爬取完成，共获取 {len(results)} 条数据")

        except Exception as e:
            logger.error(f"爬取失败: {str(e)}")
            raise
        finally:
            if not self.enable_multi_strategy:
                self.close_driver()

        return results

    def _crawl_with_multi_strategy(self, target_url: str, keywords: List[str],
                                    max_pages: int, **kwargs) -> List[Dict[str, Any]]:
        """
        使用多级降级策略爬取
        当检测到空内容时自动降级到Selenium模式

        Args:
            target_url: 目标URL
            keywords: 搜索关键词列表
            max_pages: 最大爬取页数
            **kwargs: 其他参数

        Returns:
            list: 爬取结果列表
        """
        results = []
        selectors = None

        if self.website_template and self.website_template.selectors:
            selectors = self.website_template.selectors

        pagination_config = self.website_template.pagination_config if self.website_template else {}
        template_max_pages = pagination_config.get('max_pages')
        effective_max_pages = min(max_pages, template_max_pages) if template_max_pages else max_pages

        for page in range(1, effective_max_pages + 1):
            try:
                page_url = self._build_page_url(target_url, page, keywords, **kwargs)

                logger.info(f"正在采集第 {page} 页: {page_url}")

                if self.enable_multi_strategy and self.multi_strategy_crawler:
                    result = self.multi_strategy_crawler.crawl(page_url)
                else:
                    html = self.get_page(page_url)
                    result = {'success': bool(html), 'content': html}

                if not result.get('success'):
                    logger.warning(f"第 {page} 页采集失败: {result.get('error_message', '未知错误')}")

                    adjustments = self.crawl_monitor.get_recommended_adjustments()
                    if adjustments['action'] != 'none':
                        logger.info(f"自动调整策略: {adjustments['message']}")

                    break

                html = result.get('content', '')
                if not html:
                    logger.warning(f"第 {page} 页内容为空，尝试降级到Selenium模式")
                    html = self._crawl_with_selenium(page_url)
                    if not html:
                        break

                soup = self.parse_html(html)

                if selectors:
                    items = self._extract_items_with_selectors(soup, selectors)
                else:
                    items = self._extract_items_auto(soup)

                if not items:
                    logger.info(f"第 {page} 页没有数据，尝试降级到Selenium模式")
                    html = self._crawl_with_selenium(page_url)
                    if html:
                        soup = self.parse_html(html)
                        if selectors:
                            items = self._extract_items_with_selectors(soup, selectors)
                        else:
                            items = self._extract_items_auto(soup)

                if not items:
                    logger.info(f"Selenium模式也没有数据，停止翻页")
                    break

                for item in items:
                    try:
                        if selectors:
                            item_data = self._parse_item_with_selectors(item, selectors, page_url)
                        else:
                            item_data = self._parse_item_auto(item, page_url)

                        if item_data:
                            if keywords:
                                if self._match_keywords(item_data, keywords):
                                    results.append(item_data)
                            else:
                                results.append(item_data)
                    except Exception as e:
                        logger.error(f"解析项目失败: {str(e)}")
                        continue

                if selectors:
                    pagination_config = self.website_template.pagination_config or {}
                    if not self._has_next_page(soup, pagination_config, page):
                        logger.info("没有下一页，停止翻页")
                        break

                time.sleep(random.uniform(1, 3))

            except Exception as e:
                logger.error(f"爬取第 {page} 页失败: {str(e)}")
                continue

        if self.crawl_monitor:
            stats = self.crawl_monitor.get_stats()
            logger.info(f"采集统计: 成功率={stats['success_rate']}, 封锁率={stats['block_rate']}")

        return results
    
    def _crawl_with_template(self, target_url: str, keywords: List[str], 
                              max_pages: int, **kwargs) -> List[Dict[str, Any]]:
        """
        使用网站模板爬取
        """
        results = []
        selectors = self.website_template.selectors or {}
        pagination_config = self.website_template.pagination_config or {}
        
        template_max_pages = pagination_config.get('max_pages')
        effective_max_pages = min(max_pages, template_max_pages) if template_max_pages else max_pages
        
        for page in range(1, effective_max_pages + 1):
            try:
                page_url = self._build_page_url(target_url, page, keywords, **kwargs)
                
                wait_selector = selectors.get('list_container', 'body')
                html = self.get_page(page_url, wait_selector=wait_selector)
                
                if not html:
                    logger.warning(f"获取页面失败: {page_url}")
                    break
                
                soup = self.parse_html(html)
                items = self._extract_items_with_selectors(soup, selectors)
                
                if not items:
                    logger.info(f"第 {page} 页没有数据，停止翻页")
                    break
                
                for item in items:
                    try:
                        item_data = self._parse_item_with_selectors(item, selectors, page_url)
                        if item_data:
                            if keywords:
                                if self._match_keywords(item_data, keywords):
                                    results.append(item_data)
                            else:
                                results.append(item_data)
                    except Exception as e:
                        logger.error(f"解析项目失败: {str(e)}")
                        continue
                
                if not self._has_next_page(soup, pagination_config, page):
                    logger.info(f"没有下一页，停止翻页")
                    break
                    
            except Exception as e:
                logger.error(f"爬取第 {page} 页失败: {str(e)}")
                break
        
        return results
    
    def _crawl_auto_detect(self, target_url: str, keywords: List[str],
                            max_pages: int, **kwargs) -> List[Dict[str, Any]]:
        """
        自动检测并爬取（无模板时使用）
        """
        results = []
        
        try:
            html = self.get_page(target_url, wait_selector='body')
            if not html:
                return results
            
            soup = self.parse_html(html)
            
            self.detected_patterns = self._detect_page_patterns(soup)
            
            items = self._extract_items_auto(soup)
            
            for item in items:
                try:
                    item_data = self._parse_item_auto(item, target_url)
                    if item_data:
                        if keywords:
                            if self._match_keywords(item_data, keywords):
                                results.append(item_data)
                        else:
                            results.append(item_data)
                except Exception as e:
                    logger.error(f"解析项目失败: {str(e)}")
                    continue
            
            next_page_url = self._detect_next_page(soup, target_url)
            if next_page_url and max_pages > 1:
                more_results = self._crawl_auto_detect(
                    next_page_url, keywords, max_pages - 1, **kwargs
                )
                results.extend(more_results)
                
        except Exception as e:
            logger.error(f"自动检测爬取失败: {str(e)}")

        return results

    def _crawl_with_selenium(self, url: str, wait_time: int = 10) -> Optional[str]:
        """
        使用Selenium爬取动态渲染页面

        Args:
            url: 目标URL
            wait_time: 等待时间（秒）

        Returns:
            str: 页面HTML内容，如果失败则返回None
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-notifications')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe",
            ]
            for chrome_path in chrome_paths:
                import os
                if os.path.exists(chrome_path):
                    options.binary_location = chrome_path
                    break

            chromedriver_path = self._find_chromedriver()
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)

            try:
                driver.set_page_load_timeout(30)
                driver.get(url)
                time.sleep(wait_time)
                html = driver.page_source
                logger.info(f"Selenium模式获取页面成功，内容长度: {len(html)}")
                return html
            finally:
                driver.quit()

        except Exception as e:
            logger.error(f"Selenium爬取失败: {str(e)}")
            return None

    def _find_chromedriver(self) -> Optional[str]:
        """查找可用的ChromeDriver（带缓存）"""
        if self._cached_chromedriver_path is not None:
            return self._cached_chromedriver_path

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
                UniversalCrawlerEngine._cached_chromedriver_path = versions[0]
                return versions[0]

        for path in possible_paths:
            if os.path.exists(path):
                UniversalCrawlerEngine._cached_chromedriver_path = path
                return path

        chromedriver_in_path = None
        for path in os.environ.get('PATH', '').split(os.pathsep):
            full_path = os.path.join(path, 'chromedriver.exe')
            if os.path.exists(full_path):
                chromedriver_in_path = full_path
                break

        UniversalCrawlerEngine._cached_chromedriver_path = chromedriver_in_path
        return chromedriver_in_path

    def _build_page_url(self, base_url: str, page: int, 
                         keywords: List[str], **kwargs) -> str:
        """
        构建分页URL
        """
        if not self.website_template:
            return base_url
        
        pattern = self.website_template.list_url_pattern or base_url
        
        url_params = {
            'page': page,
            'keyword': ' '.join(keywords) if keywords else '',
            'category': kwargs.get('category', ''),
        }
        
        if kwargs.get('start_date'):
            url_params['start_date'] = kwargs['start_date']
        if kwargs.get('end_date'):
            url_params['end_date'] = kwargs['end_date']
        
        for key, value in kwargs.items():
            if key not in ['start_date', 'end_date']:
                url_params[key] = value
        
        try:
            result_url = pattern.format(**url_params)
            if not result_url.startswith('http'):
                result_url = urljoin(base_url, result_url)
            return result_url
        except KeyError:
            return base_url
    
    def _extract_items_with_selectors(self, soup: BeautifulSoup, 
                                       selectors: Dict) -> List:
        """
        使用选择器提取项目列表
        """
        item_selector = selectors.get('item_container', '')
        
        if item_selector:
            return soup.select(item_selector)
        
        common_selectors = [
            '.list-item', '.project-item', '.item', '.news-item',
            'tr[data-id]', 'li[data-id]', '.result-item',
            '.tender-item', '.bid-item', '.content-item',
            'table tbody tr', '.list li', '.items > div'
        ]
        
        for selector in common_selectors:
            items = soup.select(selector)
            if items and len(items) > 0:
                logger.info(f"自动检测到项目选择器: {selector}")
                return items
        
        return []
    
    def _parse_item_with_selectors(self, item, selectors: Dict, 
                                    base_url: str) -> Optional[Dict[str, Any]]:
        """
        使用选择器解析单个项目
        """
        try:
            title = self._extract_field(item, selectors, 'title', 'a, .title, .name')
            if not title:
                return None
            
            link = self._extract_field(item, selectors, 'link', 'a')
            if link and not link.startswith('http'):
                link = urljoin(base_url, link)
            
            publish_date = self._extract_field(item, selectors, 'date', '.date, .time, .publish-date')
            publish_date = self._parse_date(publish_date) if publish_date else None
            
            result = {
                'title': title,
                'source_url': link or base_url,
                'detail_url': link,
                'publish_date': publish_date,
                'region': self._extract_field(item, selectors, 'region', '.region, .area'),
                'category': self._extract_field(item, selectors, 'category', '.category, .type'),
                'project_code': self._extract_field(item, selectors, 'project_code', '.code, .project-code'),
                'budget': self._parse_budget(
                    self._extract_field(item, selectors, 'budget', '.budget, .amount, .price')
                ),
                'purchaser_name': self._extract_field(item, selectors, 'purchaser', '.purchaser, .buyer, .purchaser-name'),
                'purchaser_contact': self._extract_field(item, selectors, 'purchaser_contact', '.contact, .purchaser-contact'),
                'purchaser_phone': self._extract_field(item, selectors, 'purchaser_phone', '.phone, .tel, .purchaser-phone'),
                'agency_name': self._extract_field(item, selectors, 'agency', '.agency, .agent, .agency-name'),
                'description': self._extract_field(item, selectors, 'description', '.desc, .description, .content'),
            }
            
            result = {k: v for k, v in result.items() if v is not None}
            
            return result
            
        except Exception as e:
            logger.error(f"解析项目失败: {str(e)}")
            return None
    
    def _extract_field(self, item, selectors: Dict, field_name: str, 
                        default_selectors: str) -> Optional[str]:
        """
        提取字段值
        """
        selector = selectors.get(field_name, default_selectors)
        
        if not selector:
            return None
        
        selectors_list = [s.strip() for s in selector.split(',')]
        
        for sel in selectors_list:
            try:
                elem = item.select_one(sel)
                if elem:
                    if elem.name == 'a':
                        href = elem.get('href', '')
                        if href and field_name in ['link', 'detail_url']:
                            return href
                    return elem.get_text(strip=True)
            except Exception:
                continue
        
        return None
    
    def _detect_page_patterns(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        检测页面模式
        """
        patterns = {
            'has_table': bool(soup.find('table')),
            'has_list': bool(soup.find('ul') or soup.find('ol')),
            'has_div_items': bool(soup.select('[class*="item"]')),
            'title_tags': [],
            'date_patterns': [],
        }
        
        title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.name', 'a[title]']
        for selector in title_selectors:
            elements = soup.select(selector)
            if elements:
                patterns['title_tags'].append(selector)
        
        date_pattern = re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?')
        text_content = soup.get_text()
        dates = date_pattern.findall(text_content)
        if dates:
            patterns['date_patterns'] = dates[:5]
        
        return patterns
    
    def _extract_items_auto(self, soup: BeautifulSoup) -> List:
        """
        自动提取项目列表
        """
        items = []
        
        table = soup.find('table')
        if table:
            tbody = table.find('tbody') or table
            items = tbody.find_all('tr')
            if items and len(items) > 1:
                items = items[1:]
                logger.info("检测到表格布局")
                return items
        
        list_containers = soup.find_all(['ul', 'ol'])
        for container in list_containers:
            list_items = container.find_all('li', recursive=False)
            if len(list_items) >= 3:
                items = list_items
                logger.info("检测到列表布局")
                return items
        
        div_items = soup.select('[class*="item"], [class*="list"] > div')
        if div_items and len(div_items) >= 3:
            items = div_items
            logger.info("检测到DIV布局")
            return items
        
        links = soup.find_all('a', href=True)
        if links:
            items = links
            logger.info("使用链接作为项目")
        
        return items
    
    def _parse_item_auto(self, item, base_url: str) -> Optional[Dict[str, Any]]:
        """
        自动解析项目
        """
        try:
            if item.name == 'a':
                title = item.get_text(strip=True)
                link = item.get('href', '')
            elif item.name == 'tr':
                tds = item.find_all('td')
                if not tds:
                    return None
                title = tds[0].get_text(strip=True) if tds else ''
                link_elem = tds[0].find('a')
                link = link_elem.get('href', '') if link_elem else ''
            else:
                title_elem = item.find(['a', 'h1', 'h2', 'h3', 'h4', '.title', '.name'])
                title = title_elem.get_text(strip=True) if title_elem else ''
                link_elem = item.find('a', href=True)
                link = link_elem.get('href', '') if link_elem else ''
            
            if not title or len(title) < 5:
                return None
            
            if link and not link.startswith('http'):
                link = urljoin(base_url, link)
            
            date_str = self._extract_date_from_text(item.get_text())
            publish_date = self._parse_date(date_str) if date_str else None
            
            return {
                'title': title,
                'source_url': link or base_url,
                'detail_url': link,
                'publish_date': publish_date,
                'raw_data': {'html': str(item)[:1000]}
            }
            
        except Exception as e:
            logger.error(f"自动解析项目失败: {str(e)}")
            return None
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取日期
        """
        patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _detect_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        检测下一页URL
        """
        next_selectors = [
            'a:contains("下一页")', 'a:contains("Next")',
            '.next a', '.pagination .next a',
            'a[rel="next"]', '.page-next a',
            'a.next', 'li.next a'
        ]
        
        for selector in next_selectors:
            try:
                next_elem = soup.select_one(selector)
                if next_elem:
                    href = next_elem.get('href', '')
                    if href:
                        return urljoin(current_url, href)
            except Exception:
                continue
        
        current_page = self._get_current_page(soup, current_url)
        if current_page:
            next_page = current_page + 1
            return self._increment_page_param(current_url, next_page)
        
        return None
    
    def _get_current_page(self, soup: BeautifulSoup, url: str) -> Optional[int]:
        """
        获取当前页码
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if 'page' in params:
            return int(params['page'][0])
        if 'p' in params:
            return int(params['p'][0])
        
        current_elem = soup.select_one('.pagination .current, .page-current, .active')
        if current_elem:
            try:
                return int(current_elem.get_text(strip=True))
            except ValueError:
                pass
        
        return None
    
    def _increment_page_param(self, url: str, page: int) -> str:
        """
        增加页码参数
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if 'page' in params:
            params['page'] = [str(page)]
        elif 'p' in params:
            params['p'] = [str(page)]
        else:
            params['page'] = [str(page)]
        
        new_query = urlencode(params, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
    
    def _has_next_page(self, soup: BeautifulSoup, pagination_config: Dict, 
                        current_page: int) -> bool:
        """
        判断是否有下一页
        注意：翻页上限由外层循环的 effective_max_pages 控制，此处不再检查 pagination_config['max_pages']
        """
        next_selectors = pagination_config.get('next_selectors', [
            '.next a', '.pagination .next a', 'a[rel="next"]'
        ])
        
        next_button = pagination_config.get('next_button')
        if next_button:
            next_selectors = [next_button] + next_selectors
        
        for selector in next_selectors:
            if soup.select_one(selector):
                return True
        
        return False
    
    def _match_keywords(self, item_data: Dict, keywords: List[str]) -> bool:
        """
        匹配关键词
        """
        title = item_data.get('title', '').lower()
        description = item_data.get('description', '').lower()
        text = f"{title} {description}"
        
        return any(kw.lower() in text for kw in keywords)
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        解析日期字符串
        """
        if not date_str:
            return None
        
        patterns = [
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
            (r'(\d{4}/\d{2}/\d{2})', '%Y/%m/%d'),
            (r'(\d{4}年\d{1,2}月\d{1,2}日)', '%Y年%m月%d日'),
            (r'(\d{2}-\d{2}-\d{4})', '%m-%d-%Y'),
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    dt = datetime.strptime(match.group(1), date_format)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _parse_budget(self, budget_str: str) -> Optional[float]:
        """
        解析预算金额
        """
        if not budget_str:
            return None
        
        budget_str = budget_str.replace(',', '').replace('，', '')
        
        patterns = [
            (r'(\d+\.?\d*)\s*万', 10000),
            (r'(\d+\.?\d*)\s*亿', 100000000),
            (r'(\d+\.?\d*)\s*元', 1),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, budget_str)
            if match:
                try:
                    return float(match.group(1)) * multiplier
                except ValueError:
                    continue
        
        numbers = re.findall(r'\d+\.?\d*', budget_str)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    def get_detail(self, url: str, selectors: Dict = None) -> Dict[str, Any]:
        """
        获取详情页面内容
        """
        try:
            html = self.get_page(url, wait_selector='body')
            if not html:
                return {}
            
            soup = self.parse_html(html)
            
            content_selector = selectors.get('detail_content', '.content, .detail, article') if selectors else '.content, .detail, article'
            
            content = ''
            if content_selector:
                content_elem = soup.select_one(content_selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
            
            info = {}
            info_items = soup.select('.info-item, .detail-item, tr, .field')
            for item in info_items:
                label_elem = item.select_one('th, .label, .name, .field-label')
                value_elem = item.select_one('td, .value, .field-value')
                if label_elem and value_elem:
                    label = label_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    info[label] = value
            
            return {
                'description': content,
                'raw_data': info
            }
        except Exception as e:
            logger.error(f"获取详情失败: {url}, 错误: {str(e)}")
            return {}
