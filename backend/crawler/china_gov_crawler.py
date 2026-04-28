"""
中国政府采购网爬虫
支持采集多种类型的采购公告信息
"""
import re
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base_crawler import BaseCrawler, CrawlerConfig

logger = logging.getLogger(__name__)


class ChinaGovCrawler(BaseCrawler):
    """
    中国政府采购网爬虫
    支持采集：招标公告、中标公告、更正公告等
    """
    
    BASE_URL = 'http://www.ccgp.gov.cn'
    
    NOTICE_TYPE_MAP = {
        'gkzb': {'name': '公开招标公告', 'url': '/cggg/dfgg/gkzb/'},
        'jzxcs': {'name': '竞争性磋商公告', 'url': '/cggg/dfgg/jzxcs/'},
        'jzxtp': {'name': '竞争性谈判公告', 'url': '/cggg/dfgg/jzxtp/'},
        'xjcg': {'name': '询价公告', 'url': '/cggg/dfgg/xjgg/'},
        'zbjg': {'name': '中标公告', 'url': '/cggg/dfgg/zbgg/'},
        'gzgg': {'name': '更正公告', 'url': '/cggg/dfgg/gzgg/'},
        'htgg': {'name': '合同公告', 'url': '/cggg/dfgg/htgg/'},
    }
    
    def __init__(self, config: CrawlerConfig = None):
        """
        初始化爬虫
        
        Args:
            config: 爬虫配置
        """
        if config is None:
            config = CrawlerConfig(
                headless=True,
                timeout=30,
                request_delay_min=2.0,
                request_delay_max=4.0,
                max_retries=3
            )
        super().__init__(config)
        self.session = self._create_session()
        self._setup_session()
    
    def _setup_session(self):
        """
        配置Session
        """
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def crawl(self, notice_types: List[str] = None, keywords: List[str] = None,
              page: int = 1, page_size: int = 20, max_pages: int = None,
              start_date: str = None, end_date: str = None, region: str = None) -> List[Dict[str, Any]]:
        """
        爬取采购公告信息
        
        Args:
            notice_types: 公告类型列表
            keywords: 关键词列表
            page: 起始页码
            page_size: 每页数量
            max_pages: 最大采集页数（None时默认3页）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            region: 地区过滤
            
        Returns:
            list: 公告数据列表
        """
        results = []
        
        if notice_types is None:
            notice_types = ['gkzb', 'jzxcs', 'zbjg']
        
        effective_max_pages = max_pages if max_pages else 3
        
        for notice_type in notice_types:
            if notice_type not in self.NOTICE_TYPE_MAP:
                logger.warning(f"未知的公告类型: {notice_type}")
                continue
            
            type_info = self.NOTICE_TYPE_MAP[notice_type]
            logger.info(f"开始采集 {type_info['name']}")
            
            try:
                type_results = self._crawl_by_type(
                    notice_type=notice_type,
                    keywords=keywords,
                    page=page,
                    page_size=page_size,
                    max_pages=effective_max_pages,
                    region=region,
                    start_date=start_date,
                    end_date=end_date
                )
                results.extend(type_results)
                logger.info(f"{type_info['name']} 采集完成，获取 {len(type_results)} 条数据")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"采集 {type_info['name']} 失败: {str(e)}")
                continue
        
        logger.info(f"爬取完成，共获取 {len(results)} 条数据")
        return results
    
    def _crawl_by_type(self, notice_type: str, keywords: List[str] = None,
                       page: int = 1, page_size: int = 20, max_pages: int = 3,
                       region: str = None, start_date: str = None,
                       end_date: str = None) -> List[Dict[str, Any]]:
        """
        按类型爬取公告
        """
        results = []
        
        type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
        base_url = f"{self.BASE_URL}{type_info.get('url', '')}"
        
        for current_page in range(1, max_pages + 1):
            if current_page == 1:
                url = base_url
            else:
                url = f"{base_url}index_{current_page}.htm"
            
            try:
                html = self._fetch_page(url)
                if not html:
                    break
                
                soup = self.parse_html(html)
                items = self._extract_items(soup)
                
                logger.info(f"第{current_page}页提取到 {len(items)} 个公告项")
                
                if not items:
                    break
                
                for item in items:
                    try:
                        tender_data = self._parse_item(item, notice_type)
                        if not tender_data:
                            continue

                        if region and region not in tender_data.get('region', ''):
                            continue

                        if keywords:
                            if not self._match_keywords(tender_data, keywords):
                                continue

                        if start_date or end_date:
                            publish_date = tender_data.get('publish_date', '')
                            if publish_date:
                                if start_date and publish_date < start_date:
                                    continue
                                if end_date and publish_date > end_date:
                                    continue
                            else:
                                continue

                        results.append(tender_data)

                        if len(results) >= page_size:
                            break

                    except Exception as e:
                        logger.error(f"解析公告项目失败: {str(e)}")
                        continue
                
                if len(results) >= page_size:
                    break
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"爬取公告失败: {notice_type} 第{current_page}页, 错误: {str(e)}")
                break
        
        return results
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        获取页面内容
        """
        try:
            logger.info(f"正在获取页面: {url}")
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            if not response.encoding or response.encoding.lower() == 'iso-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'
            logger.info(f"页面获取成功，内容长度: {len(response.text)}")
            return response.text
        except Exception as e:
            logger.error(f"获取页面失败: {url}, 错误: {str(e)}")
            return None
    
    def _extract_items(self, soup: BeautifulSoup) -> List:
        """
        从页面提取公告列表
        """
        items = []
        
        ul_lists = soup.find_all('ul')
        for ul in ul_lists:
            li_items = ul.find_all('li')
            for li in li_items:
                text = li.get_text(strip=True)
                if '发布时间' in text and '地域' in text:
                    items.append(li)
        
        if not items:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                if '/20' in href and ('t20' in href or 'shtml' in href):
                    items.append(link)

        logger.info(f"找到 {len(items)} 个公告项")
        
        return items
    
    def _parse_item(self, item, notice_type: str) -> Optional[Dict[str, Any]]:
        """
        解析单个公告项
        """
        try:
            type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})

            text = item.get_text(strip=True)

            if item.name == 'a':
                link_elem = item
            else:
                link_elem = item.find('a')

            if not link_elem:
                logger.debug(f"解析失败: 未找到链接元素, item.name={item.name}")
                return None

            title = link_elem.get_text(strip=True)
            link = link_elem.get('href', '')

            if not title or len(title) < 5:
                title = item.get_text(strip=True) if hasattr(item, 'get_text') else ''
            if not title or len(title) < 5:
                logger.debug(f"解析失败: 标题太短或为空, title={title[:50] if title else 'None'}")
                return None

            link = self._fix_ccgp_url(link, notice_type)

            publish_date = None
            date_match = re.search(r'发布时间[：:]?\s*(\d{4}-\d{2}-\d{2})', text)
            if date_match:
                publish_date = date_match.group(1)
            else:
                url_date_match = re.search(r'/(\d{4})(\d{2})(\d{2})/', link)
                if url_date_match:
                    publish_date = f"{url_date_match.group(1)}-{url_date_match.group(2)}-{url_date_match.group(3)}"

            region = ''
            region_match = re.search(r'地域[：:]?\s*(\S+?)(?:采购人|$)', text)
            if region_match:
                region = region_match.group(1)

            purchaser = ''
            purchaser_match = re.search(r'采购人[：:]?\s*(.+?)$', text)
            if purchaser_match:
                purchaser = purchaser_match.group(1)

            result = {
                'title': title,
                'source_url': link,
                'publish_date': publish_date,
                'region': region,
                'project_code': '',
                'purchaser_name': purchaser,
                'source_type': 'government',
                'notice_type': notice_type,
                'notice_type_name': type_info.get('name', ''),
            }

            logger.debug(f"解析成功: {title[:30]}...")
            return result
        except Exception as e:
            logger.error(f"解析公告详情失败: {str(e)}")
            return None
    
    def _match_keywords(self, tender_data: Dict, keywords: List[str]) -> bool:
        """
        匹配关键词
        """
        title = tender_data.get('title', '').lower()
        return any(kw.lower() in title for kw in keywords)

    def _fix_ccgp_url(self, link: str, notice_type: str) -> str:
        """
        修复中国政府采购网URL格式
        有些页面的链接是相对路径如 /202603/t20260329_26331188.htm
        需要拼接正确的完整路径

        Args:
            link: 原始链接
            notice_type: 公告类型

        Returns:
            str: 修复后的完整URL
        """
        if not link:
            return link

        if link.startswith('http'):
            return link

        if link.startswith('./'):
            link = link[2:]
        elif link.startswith('../'):
            link = link[3:]

        ccgp_url_pattern = re.compile(r'^/?(\d{4})(\d{2})/t(\d{8}_\d+)\.htm$')
        match = ccgp_url_pattern.match(link)
        if match:
            year = match.group(1)
            month = match.group(2)
            date_part = match.group(3)
            type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
            notice_path = type_info.get('url', '/cggg/dfgg/gkzb/').rstrip('/')
            return f'http://www.ccgp.gov.cn{notice_path}/{year}{month}/t{date_part}.htm'

        if not link.startswith('http'):
            link = urljoin(self.BASE_URL, link)

        return link

    def _validate_url(self, url: str) -> bool:
        """
        验证URL是否有效
        对于政府网站，HEAD请求常常失败（405/403/503），
        因此采用宽松策略：只有明确的404才判定无效，其他情况默认通过
        """
        if not url:
            return False
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 404:
                logger.warning(f"URL返回404: {url}")
                return False
            return True
        except requests.exceptions.RequestException:
            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)
                if response.status_code == 404:
                    logger.warning(f"URL返回404: {url}")
                    return False
                return True
            except requests.exceptions.RequestException:
                return True
    
    def get_notice_types(self) -> Dict[str, Dict[str, str]]:
        """
        获取支持的公告类型
        """
        return self.NOTICE_TYPE_MAP
