"""
上海政府采购网爬虫 (zfcg.sh.gov.cn)
支持采集：招标公告、中标结果、更正公告等
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlencode

import requests
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


class ShanghaiGovProcurementCrawler(PyppeteerCrawler):
    """
    上海政府采购网爬虫
    支持采集：招标公告、中标结果、更正公告等
    """

    BASE_URL = 'https://www.zfcg.sh.gov.cn'

    NOTICE_TYPE_MAP = {
        'cggg': {'name': '采购公告', 'url': '/cgxx/cggg/index.html', 'category': 'tender'},
        'zbgg': {'name': '招标公告', 'url': '/cgxx/cggg/index.html', 'category': 'tender'},
        'zbjg': {'name': '中标结果', 'url': '/cgxx/zbjg/index.html', 'category': 'result'},
        'gzgg': {'name': '更正公告', 'url': '/cgxx/gzgg/index.html', 'category': 'notice'},
        'htgg': {'name': '合同公告', 'url': '/cgxx/htgg/index.html', 'category': 'contract'},
    }

    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        super().__init__(proxy_config, max_retries, timeout)
        self.base_url = self.BASE_URL
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.BASE_URL,
        })
        return session

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
            notice_types = ['cggg']

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
                    wait_selector='.list-box, .news-list, ul, table',
                    notice_type=notice_type,
                    keywords=keywords,
                    page_size=page_size,
                    start_date=start_date,
                    end_date=end_date
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

    def _build_list_url(
        self,
        notice_type: str,
        page: int = 1
    ) -> str:
        """构建列表页URL"""
        type_info = self.NOTICE_TYPE_MAP.get(notice_type, self.NOTICE_TYPE_MAP['cggg'])
        url_path = type_info['url']

        if page > 1:
            url_path = url_path.replace('index.html', f'index_{page}.html')

        return f"{self.base_url}{url_path}"

    async def parse_response(
        self,
        html: str,
        notice_type: str = None,
        keywords: List[str] = None,
        page_size: int = 20,
        start_date: str = None,
        end_date: str = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """解析响应"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        items = self._extract_items(soup)

        for item in items[:page_size]:
            try:
                data = self._parse_item(item, notice_type)
                if data:
                    if start_date or end_date:
                        if not self._match_date_range(data.get('publish_date'), start_date, end_date):
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
        """从页面提取公告列表"""
        selectors = [
            '.list-box li',
            '.news-list li',
            '.procurement-list li',
            '.article-list li',
            '.data-list li',
            'ul.list li',
            'table tbody tr',
            '.content-list li',
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
            if ('detail' in href or 'article' in href or '/cgxx/' in href) and text and len(text) > 5:
                if not href.startswith('http'):
                    href = urljoin(self.base_url, href)
                valid_links.append({'href': href, 'text': text, 'element': a})

        if valid_links:
            logger.info(f"通过链接找到 {len(valid_links)} 个公告")
            return valid_links

        logger.warning("未找到公告列表元素")
        return []

    def _parse_item(self, item, notice_type: str = None) -> Optional[Dict[str, Any]]:
        """解析单个公告项"""
        type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})

        try:
            if isinstance(item, dict):
                title = item.get('text', '')
                link = item.get('href', '')
                element = item.get('element')
            elif hasattr(item, 'get_text'):
                title = item.get_text(strip=True)
                link = item.get('href', '')
                element = item
            else:
                return None

            if not title or len(title) < 5:
                title_elem = item.select_one('a, .title, .item-title') if hasattr(item, 'select_one') else None
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title_elem.name == 'a':
                        link = title_elem.get('href', '')

            if not title or len(title) < 5:
                return None

            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)

            publish_date = None
            region = ''
            project_code = ''
            budget = None

            if hasattr(element, 'select_one') or hasattr(element, 'find'):
                date_elem = element.select_one('.date, .time, .publish-date, .fbsj, span:nth-child(2)') if hasattr(element, 'select_one') else None
                if date_elem:
                    publish_date = self._parse_date(date_elem.get_text(strip=True))
                else:
                    text = element.get_text() if hasattr(element, 'get_text') else str(element)
                    date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)', text)
                    if date_match:
                        publish_date = self._parse_date(date_match.group(1))

            return {
                'title': title,
                'source_url': link,
                'publish_date': publish_date,
                'region': region,
                'project_code': project_code,
                'budget': budget,
                'source_type': 'shanghai_gov_procurement',
                'notice_type': notice_type,
                'notice_type_name': type_info.get('name', '采购公告'),
                'category': type_info.get('category', 'tender'),
            }
        except Exception as e:
            logger.error(f"解析公告详情失败: {str(e)}")
            return None

    def _match_keywords(self, data: Dict, keywords: List[str]) -> bool:
        """匹配关键词"""
        title = data.get('title', '').lower()
        text = title
        return any(kw.lower() in text for kw in keywords)

    def _match_date_range(
        self,
        date_str: str,
        start_date: str = None,
        end_date: str = None
    ) -> bool:
        """匹配日期范围"""
        if not date_str:
            return True

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')

            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                if date < start:
                    return False

            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if date > end:
                    return False

            return True
        except ValueError:
            return True

    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None

        date_str = date_str.strip()

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
        """获取公告详情"""
        result = await self.crawl_with_fallback(url)

        if not result.success:
            return None

        soup = BeautifulSoup(result.data.get('html', ''), 'html.parser')

        content_elem = soup.select_one('.content, .detail-content, .article-content, .main-content')
        content = content_elem.get_text(strip=True) if content_elem else ''

        detail_data = {
            'url': url,
            'content': content,
            'html': result.data.get('html', '')
        }

        info_items = soup.select('.info-item, .detail-item, tr, .field')
        for info_item in info_items:
            label_elem = info_item.select_one('th, .label, .name, .field-label')
            value_elem = info_item.select_one('td, .value, .field-value')
            if label_elem and value_elem:
                label = label_elem.get_text(strip=True)
                value = value_elem.get_text(strip=True)
                if '采购人' in label:
                    detail_data['purchaser_name'] = value
                elif '联系人' in label:
                    detail_data['purchaser_contact'] = value
                elif '电话' in label or '联系方式' in label:
                    detail_data['purchaser_phone'] = value
                elif '代理机构' in label:
                    detail_data['agency_name'] = value
                elif '预算' in label or '金额' in label:
                    budget_match = re.search(r'[\d,.]+', value)
                    if budget_match:
                        try:
                            detail_data['budget'] = float(budget_match.group().replace(',', ''))
                        except ValueError:
                            pass

        return detail_data


def create_shanghai_gov_procurement_crawler(
    proxy_enabled: bool = False,
    proxy_list: List[str] = None
) -> ShanghaiGovProcurementCrawler:
    """
    创建上海政府采购网爬虫实例

    Args:
        proxy_enabled: 是否启用代理
        proxy_list: 代理列表

    Returns:
        ShanghaiGovProcurementCrawler: 爬虫实例
    """
    proxy_config = ProxyConfig(enabled=proxy_enabled)

    if proxy_enabled and proxy_list:
        proxy_config.server = proxy_list[0] if proxy_list else ''

    return ShanghaiGovProcurementCrawler(proxy_config=proxy_config)


async def crawl_shanghai_gov_procurement(
    notice_types: List[str] = None,
    keywords: List[str] = None,
    proxy_enabled: bool = False,
    proxy_list: List[str] = None
) -> CrawlResult:
    """
    采集上海政府采购网的便捷函数

    Args:
        notice_types: 公告类型列表
        keywords: 关键词列表
        proxy_enabled: 是否启用代理
        proxy_list: 代理列表

    Returns:
        CrawlResult: 采集结果
    """
    crawler = create_shanghai_gov_procurement_crawler(proxy_enabled, proxy_list)

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