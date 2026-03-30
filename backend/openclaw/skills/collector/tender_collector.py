"""
政府采购网站采集技能
支持中国政府采购网、上海市政府采购网等
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from openclaw.skill_registry import Skill, SkillMetadata, SkillResult


logger = logging.getLogger(__name__)


class GovernmentTenderCollectorSkill(Skill):
    """
    政府采购网站采集技能
    """
    
    metadata = SkillMetadata(
        name='government_tender_collector',
        description='从政府采购网站采集招标公告信息',
        version='1.0.0',
        author='OpenClaw',
        category='collector',
        tags=['tender', 'government', 'crawler', 'procurement'],
        input_schema={
            'type': 'object',
            'properties': {
                'source': {
                    'type': 'string',
                    'description': '数据源：china_gov, shanghai_gov'
                },
                'keywords': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '搜索关键词列表'
                },
                'notice_types': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '公告类型'
                },
                'page': {
                    'type': 'integer',
                    'description': '页码',
                    'default': 1
                },
                'page_size': {
                    'type': 'integer',
                    'description': '每页数量',
                    'default': 20
                },
                'start_date': {
                    'type': 'string',
                    'format': 'date',
                    'description': '开始日期 YYYY-MM-DD'
                },
                'end_date': {
                    'type': 'string',
                    'format': 'date',
                    'description': '结束日期 YYYY-MM-DD'
                }
            },
            'required': ['source']
        },
        output_schema={
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'title': {'type': 'string'},
                            'project_code': {'type': 'string'},
                            'publish_date': {'type': 'string'},
                            'source_url': {'type': 'string'}
                        }
                    }
                },
                'error': {'type': 'string'}
            }
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行采集
        
        Args:
            source: 数据源代码
            keywords: 关键词列表
            notice_types: 公告类型列表
            page: 页码
            page_size: 每页数量
            start_date: 开始日期
            end_date: 结束日期
        """
        source = kwargs.get('source')
        keywords = kwargs.get('keywords', [])
        notice_types = kwargs.get('notice_types')
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 20)
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        try:
            if source == 'china_gov':
                results = await self._crawl_china_gov(
                    keywords=keywords,
                    notice_types=notice_types,
                    page=page,
                    page_size=page_size,
                    start_date=start_date,
                    end_date=end_date
                )
            elif source == 'shanghai_gov':
                results = await self._crawl_shanghai_gov(
                    keywords=keywords,
                    notice_types=notice_types,
                    page=page,
                    page_size=page_size
                )
            else:
                return SkillResult(
                    success=False,
                    error=f"Unknown source: {source}"
                )
            
            return SkillResult(
                success=True,
                data=results,
                metadata={
                    'source': source,
                    'count': len(results),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Government tender collection failed: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _crawl_china_gov(
        self,
        keywords: List[str],
        notice_types: List[str],
        page: int,
        page_size: int,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        采集中国政府采购网
        """
        from crawler.china_gov_crawler import ChinaGovCrawler
        
        crawler = ChinaGovCrawler()
        
        def sync_crawl():
            return crawler.crawl(
                notice_types=notice_types,
                keywords=keywords,
                page=page,
                page_size=page_size,
                start_date=start_date,
                end_date=end_date
            )
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, sync_crawl)
        
        return results
    
    async def _crawl_shanghai_gov(
        self,
        keywords: List[str],
        notice_types: List[str],
        page: int,
        page_size: int
    ) -> List[Dict]:
        """
        采集上海市政府采购网
        """
        from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler

        crawler = ShanghaiGovCrawler()

        result = await crawler.crawl(
            notice_types=notice_types,
            keywords=keywords,
            page=page,
            page_size=page_size
        )

        if hasattr(result, 'data'):
            return result.data or []
        elif isinstance(result, list):
            return result
        else:
            return []


class WebPageCollectorSkill(Skill):
    """
    通用网页采集技能
    """
    
    metadata = SkillMetadata(
        name='webpage_collector',
        description='采集指定URL的网页内容',
        version='1.0.0',
        author='OpenClaw',
        category='collector',
        tags=['web', 'crawler', 'scraper'],
        input_schema={
            'type': 'object',
            'properties': {
                'url': {'type': 'string', 'description': '目标URL'},
                'method': {'type': 'string', 'enum': ['get', 'post'], 'default': 'get'},
                'headers': {'type': 'object', 'description': '请求头'},
                'params': {'type': 'object', 'description': '查询参数'},
                'data': {'type': 'object', 'description': 'POST数据'},
                'use_selenium': {'type': 'boolean', 'default': False}
            },
            'required': ['url']
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行网页采集
        """
        url = kwargs.get('url')
        method = kwargs.get('method', 'get')
        headers = kwargs.get('headers')
        params = kwargs.get('params')
        data = kwargs.get('data')
        use_selenium = kwargs.get('use_selenium', False)
        
        try:
            if use_selenium:
                content = await self._fetch_with_selenium(url)
            else:
                content = await self._fetch_with_requests(
                    url, method, headers, params, data
                )
            
            return SkillResult(
                success=True,
                data={'content': content, 'url': url},
                metadata={'timestamp': datetime.now().isoformat()}
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _fetch_with_requests(
        self,
        url: str,
        method: str,
        headers: Dict,
        params: Dict,
        data: Dict
    ) -> str:
        """
        使用requests获取网页
        """
        import requests
        
        request_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        if headers:
            request_headers.update(headers)
        
        if method.lower() == 'post':
            response = requests.post(url, headers=request_headers, data=data, timeout=30)
        else:
            response = requests.get(url, headers=request_headers, params=params, timeout=30)
        
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        return response.text
    
    async def _fetch_with_selenium(self, url: str) -> str:
        """
        使用Selenium获取网页
        """
        from crawler.base_crawler import BaseCrawler, CrawlerConfig
        
        config = CrawlerConfig(headless=True)
        crawler = BaseCrawler(config)
        
        def sync_fetch():
            return crawler.get_page(url)
        
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, sync_fetch)
        
        crawler.close_driver()
        
        return content or ''
