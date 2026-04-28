"""
上海建筑建材业网站爬虫 (ciac.zjw.sh.gov.cn)
上海市建设工程交易服务中心

使用公开API /JGBAppZtbInterWeb/interWeb/jygg/list 直接采集数据
该API不需要SSO认证，返回JSON格式数据
"""
import asyncio
import logging
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin

import aiohttp

from .pyppeteer_crawler import (
    PyppeteerCrawler,
    CrawlResult,
    CrawlStrategy,
    ProxyConfig,
    BrowserFingerprint
)
from .self_healing import SelfHealingCrawler, ProxyPool

logger = logging.getLogger(__name__)


class ShanghaiConstructionCrawler(PyppeteerCrawler):
    """
    上海建筑建材业网站爬虫
    使用公开API采集：招标公告、中标结果、更正公告等
    
    API端点: /JGBAppZtbInterWeb/interWeb/jygg/list
    请求方式: POST
    参数: gglx(公告类型), pageNo(页码), pageSize(每页数量)
    """
    
    BASE_URL = 'https://ciac.zjw.sh.gov.cn'
    API_URL = 'https://ciac.zjw.sh.gov.cn/JGBAppZtbInterWeb/interWeb/jygg/list'
    DETAIL_URL = 'https://ciac.zjw.sh.gov.cn/JGBAppZtbInterWeb/pc/#/jyggInfo'
    
    NOTICE_TYPE_MAP = {
        'zbgg': {'name': '招标公告', 'code': 'zbgg', 'category': 'tender'},
        'zbjg': {'name': '中标结果', 'code': 'zbjg', 'category': 'result'},
        'gzgg': {'name': '更正公告', 'code': 'gzgg', 'category': 'notice'},
        'fbgg': {'name': '废标公告', 'code': 'fbgg', 'category': 'notice'},
        'htgg': {'name': '合同公告', 'code': 'htgg', 'category': 'contract'},
    }
    
    PROJECT_TYPE_MAP = {
        'all': '全部',
        'jg': '施工',
        'jgsg': '施工监理',
        'sj': '设计',
        'sjzj': '设计咨询',
        'kc': '勘察',
        'kczj': '勘察咨询',
        'zj': '咨询',
        'dz': '代建',
        'jz': '检测',
        'cl': '材料',
        'sb': '设备',
        'fw': '服务',
    }
    
    API_FIELD_MAP = {
        'ggmc': 'title',
        'ggbh': 'project_code',
        'fbsj': 'publish_date',
        'jsdd': 'region',
        'xmlx': 'project_type',
        'gglx': 'notice_type',
        'id': 'id',
        'xmbh': 'project_code',
    }
    
    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        super().__init__(proxy_config, max_retries, timeout)
        self.base_url = self.BASE_URL
    
    async def _crawl_by_api(self, url: str, **kwargs) -> CrawlResult:
        return CrawlResult(success=False, error_message='使用内部API采集，不走基类API策略')
    
    async def parse_response(self, html: str, **kwargs) -> list:
        return []
    
    async def crawl(
        self,
        notice_types: List[str] = None,
        project_types: List[str] = None,
        keywords: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        max_pages: int = None,
        start_date: str = None,
        end_date: str = None
    ) -> CrawlResult:
        if notice_types is None:
            notice_types = ['zbgg']
        
        all_results = []
        errors = []
        
        effective_max_pages = max_pages if max_pages else 1
        
        for notice_type in notice_types:
            if notice_type not in self.NOTICE_TYPE_MAP:
                logger.warning(f"未知的公告类型: {notice_type}")
                continue
            
            type_info = self.NOTICE_TYPE_MAP[notice_type]
            logger.info(f"开始采集 {type_info['name']}，最大 {effective_max_pages} 页")
            
            for current_page in range(page, page + effective_max_pages):
                try:
                    items = await self._fetch_page(notice_type, current_page, page_size)
                    
                    if not items:
                        logger.info(f"{type_info['name']} 第 {current_page} 页无数据，停止翻页")
                        break
                    
                    parsed_items = []
                    for item in items:
                        data = self._parse_api_item(item, notice_type)
                        if not data or not data.get('title'):
                            continue
                        
                        if start_date or end_date:
                            if not self._match_date_range(data.get('publish_date'), start_date, end_date):
                                continue
                        
                        if keywords:
                            if self._match_keywords(data, keywords):
                                parsed_items.append(data)
                        else:
                            parsed_items.append(data)
                    
                    all_results.extend(parsed_items)
                    logger.info(f"{type_info['name']} 第 {current_page} 页采集 {len(parsed_items)} 条数据")
                    
                    if len(items) < page_size:
                        break
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    errors.append(f"{type_info['name']} 第{current_page}页: {str(e)}")
                    logger.error(f"采集 {type_info['name']} 第 {current_page} 页失败: {str(e)}")
                    break
        
        if not all_results and not errors:
            logger.info("sh_construction 采集无数据")
        
        return CrawlResult(
            success=len(all_results) > 0,
            data=all_results,
            error_message='; '.join(errors) if errors else '',
            metadata={'total_count': len(all_results)}
        )
    
    async def _fetch_page(
        self,
        notice_type: str,
        page_no: int,
        page_size: int = 20
    ) -> List[Dict]:
        params = {
            'gglx': notice_type,
            'pageNo': page_no,
            'pageSize': page_size,
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://ciac.zjw.sh.gov.cn',
            'Referer': 'https://ciac.zjw.sh.gov.cn/JGBAppZtbInterWeb/pc/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.post(self.API_URL, json=params) as response:
                    if response.status != 200:
                        logger.error(f"API请求失败: HTTP {response.status}")
                        return []
                    
                    data = await response.json()
                    code = data.get('code', -1)
                    
                    if code != 200:
                        msg = data.get('msg', '未知错误')
                        logger.error(f"API返回错误: code={code}, msg={msg}")
                        return []
                    
                    total = data.get('total', 0)
                    rows = data.get('rows', [])
                    
                    logger.info(f"API返回 total={total}, rows={len(rows)}")
                    return rows
                    
        except asyncio.TimeoutError:
            logger.error("API请求超时")
            return []
        except Exception as e:
            logger.error(f"API请求异常: {type(e).__name__}: {str(e)}")
            return []
    
    def _parse_api_item(self, item: Dict, notice_type: str) -> Optional[Dict[str, Any]]:
        type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
        
        try:
            item_id = item.get('id', '')
            title = item.get('ggmc', '') or item.get('xmmc', '') or item.get('title', '')
            
            if not title:
                return None
            
            source_url = f"{self.DETAIL_URL}?id={item_id}" if item_id else ''
            
            publish_date = item.get('fbsj', '')
            if publish_date:
                publish_date = self._parse_date(str(publish_date))
            
            region = item.get('jsdd', '') or item.get('xzqh', '')
            project_code = item.get('ggbh', '') or item.get('xmbh', '')
            project_type = item.get('xmlxmc', '') or item.get('xmlx', '')
            
            budget = None
            budget_str = item.get('ysje', '') or item.get('xmje', '') or item.get('gczj', '')
            if budget_str:
                budget_match = re.search(r'[\d,.]+', str(budget_str))
                if budget_match:
                    try:
                        budget = float(budget_match.group().replace(',', ''))
                    except ValueError:
                        pass
            
            return {
                'title': title,
                'source_url': source_url,
                'publish_date': publish_date,
                'region': region,
                'project_code': project_code,
                'project_type': project_type,
                'budget': budget,
                'source_type': 'shanghai_construction',
                'notice_type': notice_type,
                'notice_type_name': type_info.get('name', ''),
                'category': type_info.get('category', 'tender'),
                'raw_data': item,
            }
        except Exception as e:
            logger.error(f"解析API公告详情失败: {str(e)}")
            return None
    
    def _match_keywords(self, data: Dict, keywords: List[str]) -> bool:
        title = data.get('title', '').lower()
        region = data.get('region', '').lower()
        project_type = data.get('project_type', '').lower()
        text = f"{title} {region} {project_type}"
        return any(kw.lower() in text for kw in keywords)
    
    def _match_date_range(
        self,
        date_str: str,
        start_date: str = None,
        end_date: str = None
    ) -> bool:
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
        return {'url': url, 'content': '', 'html': ''}


def create_shanghai_construction_crawler(
    proxy_enabled: bool = False,
    proxy_list: List[str] = None
) -> ShanghaiConstructionCrawler:
    proxy_config = ProxyConfig(enabled=proxy_enabled)
    
    if proxy_enabled and proxy_list:
        proxy_config.server = proxy_list[0] if proxy_list else ''
    
    return ShanghaiConstructionCrawler(proxy_config=proxy_config)


async def crawl_shanghai_construction(
    notice_types: List[str] = None,
    project_types: List[str] = None,
    keywords: List[str] = None,
    proxy_enabled: bool = False,
    proxy_list: List[str] = None
) -> CrawlResult:
    crawler = create_shanghai_construction_crawler(proxy_enabled, proxy_list)
    
    if proxy_enabled:
        proxy_pool = ProxyPool(proxy_list)
        healing_crawler = SelfHealingCrawler(crawler, proxy_pool)
        return await healing_crawler.crawl_with_healing(
            crawler.base_url,
            notice_types=notice_types,
            project_types=project_types,
            keywords=keywords
        )
    
    return await crawler.crawl(
        notice_types=notice_types,
        project_types=project_types,
        keywords=keywords
    )
