"""
上海市政府采购网专用爬虫 (zfcg.sh.gov.cn)
支持多级降级策略和故障自愈
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .pyppeteer_crawler import (
    PyppeteerCrawler,
    CrawlResult,
    CrawlStrategy,
    ProxyConfig,
    BrowserFingerprint
)
from .self_healing import SelfHealingCrawler, ProxyPool

logger = logging.getLogger(__name__)


class ShanghaiGovCrawler(PyppeteerCrawler):
    """
    上海市政府采购网爬虫
    支持采集：招标公告、中标公告、更正公告等
    """
    
    BASE_URL = 'https://www.zfcg.sh.gov.cn'
    
    NOTICE_TYPE_MAP = {
        'gkzb': {'name': '公开招标公告', 'code': 'GKZB', 'category': 'tender'},
        'jzxcs': {'name': '竞争性磋商公告', 'code': 'JZXCS', 'category': 'tender'},
        'jzxtp': {'name': '竞争性谈判公告', 'code': 'JZXTP', 'category': 'tender'},
        'xjcg': {'name': '询价采购公告', 'code': 'XJCG', 'category': 'tender'},
        'dyly': {'name': '单一来源公告', 'code': 'DYLY', 'category': 'tender'},
        'zbjg': {'name': '中标公告', 'code': 'ZBJG', 'category': 'result'},
        'gzgg': {'name': '更正公告', 'code': 'GZGG', 'category': 'notice'},
        'zbgg': {'name': '终止公告', 'code': 'ZBGG', 'category': 'notice'},
        'htgg': {'name': '合同公告', 'code': 'HTGG', 'category': 'contract'},
        'cgjg': {'name': '采购结果公告', 'code': 'CGJG', 'category': 'result'},
    }
    
    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        super().__init__(proxy_config, max_retries, timeout)
        self.base_url = self.BASE_URL
    
    async def crawl(
        self,
        notice_types: List[str] = None,
        keywords: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        start_date: str = None,
        end_date: str = None
    ) -> CrawlResult:
        """
        执行采集
        
        Args:
            notice_types: 公告类型列表
            keywords: 关键词列表
            page: 页码
            page_size: 每页数量
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CrawlResult: 采集结果
        """
        if notice_types is None:
            notice_types = ['gkzb', 'jzxcs', 'zbjg']
        
        all_results = []
        errors = []
        
        for notice_type in notice_types:
            if notice_type not in self.NOTICE_TYPE_MAP:
                logger.warning(f"未知的公告类型: {notice_type}")
                continue
            
            type_info = self.NOTICE_TYPE_MAP[notice_type]
            logger.info(f"开始采集 {type_info['name']}")
            
            try:
                url = self._build_list_url(notice_type, page)
                result = await self.crawl_with_fallback(
                    url,
                    wait_selector='.el-table, .list-container, table',
                    notice_type=notice_type,
                    keywords=keywords,
                    page_size=page_size
                )
                
                if result.success:
                    all_results.extend(result.data)
                    logger.info(f"{type_info['name']} 采集完成，获取 {len(result.data)} 条数据")
                else:
                    errors.append(f"{type_info['name']}: {result.error_message}")
                    
            except Exception as e:
                errors.append(f"{type_info['name']}: {str(e)}")
                logger.error(f"采集 {type_info['name']} 失败: {str(e)}")
        
        return CrawlResult(
            success=len(all_results) > 0,
            data=all_results,
            error_message='; '.join(errors) if errors else '',
            metadata={'total_count': len(all_results)}
        )
    
    def _build_list_url(self, notice_type: str, page: int = 1) -> str:
        """
        构建列表页URL
        """
        type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
        code = type_info.get('code', 'GKZB')
        
        return f"{self.base_url}/site/main/tradeinfo/index.html"
    
    async def parse_response(
        self,
        html: str,
        notice_type: str = None,
        keywords: List[str] = None,
        page_size: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        解析响应

        Args:
            html: HTML内容
            notice_type: 公告类型
            keywords: 关键词列表
            page_size: 每页数量

        Returns:
            list: 解析后的数据列表
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        items = self._extract_items(soup)

        for item in items[:page_size]:
            try:
                data = self._parse_item(item, notice_type)
                if not data:
                    continue

                source_url = data.get('source_url')
                if not source_url:
                    logger.debug(f"跳过无URL的公告: {data.get('title', '')[:30]}...")
                    continue

                if not await self._validate_url_async(source_url):
                    logger.info(f"跳过无效链接: {source_url}")
                    continue

                if keywords:
                    if self._match_keywords(data, keywords):
                        results.append(data)
                else:
                    results.append(data)
            except Exception as e:
                logger.error(f"解析项目失败: {str(e)}")
                continue

        return results
    
    def _extract_items(self, soup: BeautifulSoup) -> List:
        """
        从页面提取公告列表
        """
        selectors = [
            '.el-table__body tr',
            '.el-table__row',
            '.list-item',
            '.project-item',
            '.notice-item',
            'table tbody tr',
            '.content-list li',
            '.news-list li',
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items and len(items) > 2:
                logger.info(f"使用选择器 '{selector}' 找到 {len(items)} 个元素")
                return items
        
        all_links = soup.find_all('a', href=True)
        valid_links = []
        for a in all_links:
            href = a.get('href', '')
            text = a.get_text(strip=True)
            if ('detail' in href or 'articleId' in href or 'tradeinfo' in href) and text and len(text) > 5:
                valid_links.append(a)
        
        if valid_links:
            logger.info(f"通过链接找到 {len(valid_links)} 个公告")
            return valid_links
        
        logger.warning("未找到公告列表元素")
        return []
    
    def _parse_item(self, item, notice_type: str = None) -> Optional[Dict[str, Any]]:
        """
        解析单个公告项
        """
        type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
        
        try:
            if isinstance(item, dict):
                title = item.get('title', '')
                link = item.get('source_url', '')
            elif hasattr(item, 'get_text'):
                title = item.get_text(strip=True)
                link = item.get('href', '')
                
                if not title or len(title) < 5:
                    title_elem = item.select_one('a, .title, .project-title, .name')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title_elem.name == 'a':
                            link = title_elem.get('href', '')
            else:
                return None
            
            if not title or len(title) < 5:
                return None
            
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            publish_date = None
            region = ''
            project_code = ''
            budget = None
            
            if hasattr(item, 'select_one'):
                date_elem = item.select_one('.date, .time, .publish-date, .publishTime, td:nth-child(2), td:nth-child(3)')
                if date_elem:
                    publish_date = self._parse_date(date_elem.get_text(strip=True))
                
                region_elem = item.select_one('.region, .area, .district, td:nth-child(4)')
                if region_elem:
                    region = region_elem.get_text(strip=True)
                
                code_elem = item.select_one('.code, .project-code, .notice-code, td:nth-child(1)')
                if code_elem:
                    project_code = code_elem.get_text(strip=True)
            
            return {
                'title': title,
                'source_url': link,
                'publish_date': publish_date,
                'region': region,
                'project_code': project_code,
                'budget': budget,
                'source_type': 'shanghai_gov',
                'notice_type': notice_type,
                'notice_type_name': type_info.get('name', ''),
                'category': type_info.get('category', 'tender'),
            }
        except Exception as e:
            logger.error(f"解析公告详情失败: {str(e)}")
            return None
    
    def _match_keywords(self, data: Dict, keywords: List[str]) -> bool:
        """
        匹配关键词
        """
        title = data.get('title', '').lower()
        text = title

        return any(kw.lower() in text for kw in keywords)

    async def _validate_url_async(self, url: str) -> bool:
        """
        验证URL是否有效（异步HTTP HEAD请求检查状态码）

        Args:
            url: 待验证的URL

        Returns:
            bool: URL有效返回True，无效返回False
        """
        if not url:
            return False
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(url, allow_redirects=True) as response:
                    is_valid = response.status == 200
                    if not is_valid:
                        logger.warning(f"URL无效 [{response.status}]: {url}")
                    return is_valid
        except Exception as e:
            logger.warning(f"URL验证失败 [{type(e).__name__}]: {url}")
            return False

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
            (r'(\d{8})', '%Y%m%d'),
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, str(date_str))
            if match:
                try:
                    dt = datetime.strptime(match.group(1), date_format)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    async def get_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取公告详情
        
        Args:
            url: 详情页URL
            
        Returns:
            dict: 详情数据
        """
        result = await self.crawl_with_fallback(url)
        
        if not result.success:
            return None
        
        soup = BeautifulSoup(result.data.get('html', ''), 'html.parser')
        
        content_elem = soup.select_one('.content, .detail-content, .article-content, .main-content')
        content = content_elem.get_text(strip=True) if content_elem else ''
        
        return {
            'url': url,
            'content': content,
            'html': result.data.get('html', '')
        }


def create_shanghai_crawler(
    proxy_enabled: bool = False,
    proxy_list: List[str] = None
) -> ShanghaiGovCrawler:
    """
    创建上海市政府采购网爬虫实例
    
    Args:
        proxy_enabled: 是否启用代理
        proxy_list: 代理列表
        
    Returns:
        ShanghaiGovCrawler: 爬虫实例
    """
    proxy_config = ProxyConfig(enabled=proxy_enabled)
    
    if proxy_enabled and proxy_list:
        proxy_config.server = proxy_list[0] if proxy_list else ''
    
    return ShanghaiGovCrawler(proxy_config=proxy_config)


async def crawl_shanghai_gov(
    notice_types: List[str] = None,
    keywords: List[str] = None,
    proxy_enabled: bool = False,
    proxy_list: List[str] = None
) -> CrawlResult:
    """
    采集上海市政府采购网的便捷函数
    
    Args:
        notice_types: 公告类型列表
        keywords: 关键词列表
        proxy_enabled: 是否启用代理
        proxy_list: 代理列表
        
    Returns:
        CrawlResult: 采集结果
    """
    crawler = create_shanghai_crawler(proxy_enabled, proxy_list)
    
    if proxy_enabled:
        proxy_pool = ProxyPool(proxy_list)
        healing_crawler = SelfHealingCrawler(crawler, proxy_pool)
        return await healing_crawler.crawl_with_healing(
            crawler.base_url,
            notice_types=notice_types,
            keywords=keywords
        )
    
    return await crawler.crawl(
        notice_types=notice_types,
        keywords=keywords
    )
