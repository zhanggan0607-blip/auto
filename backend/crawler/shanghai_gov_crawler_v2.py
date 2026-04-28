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
        'gkzb': {'name': '公开招标公告', 'code': 'GKZB', 'category': 'tender', 'parentId': '137028', 'childrenCode': 'ZcyAnnouncement2'},
        'jzxcs': {'name': '竞争性磋商公告', 'code': 'JZXCS', 'category': 'tender', 'parentId': '137028', 'childrenCode': 'ZcyAnnouncement3'},
        'jzxtp': {'name': '竞争性谈判公告', 'code': 'JZXTP', 'category': 'tender', 'parentId': '137028', 'childrenCode': 'ZcyAnnouncement4'},
        'xjcg': {'name': '询价采购公告', 'code': 'XJCG', 'category': 'tender', 'parentId': '137028', 'childrenCode': 'ZcyAnnouncement5'},
        'dyly': {'name': '单一来源公告', 'code': 'DYLY', 'category': 'tender', 'parentId': '137117', 'childrenCode': 'ZcyAnnouncement1'},
        'zbjg': {'name': '中标公告', 'code': 'ZBJG', 'category': 'result', 'parentId': '137029', 'childrenCode': 'ZcyAnnouncement6'},
        'gzgg': {'name': '更正公告', 'code': 'GZGG', 'category': 'notice', 'parentId': '137030', 'childrenCode': 'ZcyAnnouncement7'},
        'zbgg': {'name': '终止公告', 'code': 'ZBGG', 'category': 'notice', 'parentId': '137031', 'childrenCode': 'ZcyAnnouncement8'},
        'htgg': {'name': '合同公告', 'code': 'HTGG', 'category': 'contract', 'parentId': '137032', 'childrenCode': 'ZcyAnnouncement9'},
        'cgjg': {'name': '采购结果公告', 'code': 'CGJG', 'category': 'result', 'parentId': '137029', 'childrenCode': 'ZcyAnnouncement6'},
        'cgyx': {'name': '采购意向公开', 'code': 'CGYX', 'category': 'tender', 'parentId': '137119', 'childrenCode': 'ZcyAnnouncement10016'},
    }
    
    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        super().__init__(proxy_config, max_retries, timeout)
        self.base_url = self.BASE_URL

    async def _crawl_by_api(self, url: str, **kwargs) -> 'CrawlResult':
        """
        API直连采集 - 上海政府采购网站是Vue SPA，列表API需要JS会话上下文，
        静态HTTP请求无法获取列表数据，直接返回失败让headless策略处理
        """
        return CrawlResult(success=False, error_message='Vue SPA页面列表API需要JS会话，需要使用headless浏览器采集')

    async def _crawl_by_headless(self, url: str, **kwargs) -> 'CrawlResult':
        """
        无头浏览器采集 - 使用系统Chrome/Edge
        优先HTML解析，视觉模型作为降级方案
        """
        try:
            executablePath = self.find_browser_executable()
            browser_ok = await self.init_browser(headless=True, executablePath=executablePath)
            if not browser_ok or not self.page:
                return CrawlResult(success=False, error_message='浏览器初始化失败')

            await self.page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 60000})
            await asyncio.sleep(3)
            await self.scroll_page(2)
            await asyncio.sleep(2)

            notice_type = kwargs.get('notice_type', 'gkzb')
            page_size = kwargs.get('page_size', 20)

            html = await self.page.content()
            data = await self.parse_response(html, notice_type=notice_type, page_size=page_size)

            if not data:
                logger.info("HTML解析未获取到数据，尝试视觉模型...")
                data = await self._parse_with_vision(self.page, notice_type, page_size)

            if data:
                for item in data:
                    article_id = self._extract_article_id(item.get('source_url', ''))
                    if article_id:
                        detail = await self._fetch_detail_via_api(article_id)
                        if detail:
                            item['project_code'] = detail.get('projectCode') or item.get('project_code', '')
                            item['budget'] = detail.get('budget') or item.get('budget')
                            if detail.get('publishDate'):
                                ts = detail['publishDate']
                                if isinstance(ts, (int, float)) and ts > 0:
                                    from datetime import datetime as dt_module
                                    item['publish_date'] = dt_module.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')

            return CrawlResult(success=True, data=data)
        except Exception as e:
            import traceback
            logger.error(f"Headless采集失败: {str(e)}")
            logger.error(f"堆栈: {traceback.format_exc()}")
            return CrawlResult(success=False, error_message=str(e))
        finally:
            await self.close_browser()
    
    async def crawl(
        self,
        notice_types: List[str] = None,
        keywords: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        max_pages: int = None,
        start_date: str = None,
        end_date: str = None
    ) -> CrawlResult:
        """
        执行采集
        
        Args:
            notice_types: 公告类型列表
            keywords: 关键词列表
            page: 起始页码
            page_size: 每页数量
            max_pages: 最大采集页数（None表示只采集page指定的一页）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            CrawlResult: 采集结果
        """
        if notice_types is None:
            notice_types = ['gkzb', 'jzxcs', 'zbjg']
        
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
                    url = self._build_list_url(notice_type, current_page)
                    result = await self.crawl_with_fallback(
                        url,
                        wait_selector='ul.list, .el-table, .list-container, table',
                        notice_type=notice_type,
                        keywords=keywords,
                        page_size=page_size
                    )
                    
                    if result.success and result.data:
                        all_results.extend(result.data)
                        logger.info(f"{type_info['name']} 第 {current_page} 页采集 {len(result.data)} 条数据")
                    else:
                        logger.info(f"{type_info['name']} 第 {current_page} 页无数据，停止翻页")
                        break
                        
                except Exception as e:
                    errors.append(f"{type_info['name']} 第{current_page}页: {str(e)}")
                    logger.error(f"采集 {type_info['name']} 第 {current_page} 页失败: {str(e)}")
                    break
        
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
        parent_id = type_info.get('parentId', '137027')
        children_code = type_info.get('childrenCode', 'ZcyAnnouncement')

        return f"{self.base_url}/site/category?parentId={parent_id}&childrenCode={children_code}&page={page}"
    
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

        if not results and html and len(html) > 500:
            logger.info("传统方法未提取到数据，尝试使用LLM解析...")
            results = await self._parse_with_llm(html, notice_type, page_size)

        return results

    async def _parse_with_llm(
        self,
        html: str,
        notice_type: str = None,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        使用LLM解析页面提取招标公告

        Args:
            html: HTML内容
            notice_type: 公告类型
            page_size: 每页数量

        Returns:
            list: 解析后的数据列表
        """
        try:
            from services.unified_llm_service import unified_llm_service

            type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
            notice_type_name = type_info.get('name', '招标公告')

            prompt = f"""你是一个专业的招标信息收集专家。请从以下HTML网页内容中提取招标公告信息。

网站来源: 上海市政府采购网 (zfcg.sh.gov.cn)
公告类型: {notice_type_name}

请仔细分析HTML内容，提取所有招标公告项目。每个公告通常包含：
- 标题（项目名称）
- 链接URL
- 发布日期
- 地区/区域
- 项目编号

HTML内容:
{html[:15000]}

请以JSON数组格式返回提取到的公告列表，格式如下：
[
  {{
    "title": "项目标题",
    "source_url": "完整URL链接",
    "publish_date": "2026-04-06",
    "region": "上海市",
    "project_code": "项目编号"
  }}
]

如果某个字段无法提取，请使用空字符串或null。只返回JSON数组，不要包含其他文字。"""

            response = await unified_llm_service.chat(
                message=prompt,
                agent_type='collector'
            )

            content = response.get('content', '')

            import json
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                results = []
                for item in data[:page_size]:
                    if isinstance(item, dict) and item.get('title'):
                        results.append({
                            'title': item.get('title', ''),
                            'source_url': item.get('source_url', ''),
                            'publish_date': item.get('publish_date', ''),
                            'region': item.get('region', '上海市'),
                            'project_code': item.get('project_code', ''),
                            'budget': None,
                            'source_type': 'shanghai_gov',
                            'notice_type': notice_type,
                            'notice_type_name': notice_type_name,
                            'category': type_info.get('category', 'tender'),
                        })
                logger.info(f"LLM解析成功，提取到 {len(results)} 条数据")
                return results

            logger.warning(f"LLM返回格式异常: {content[:200]}")
            return []

        except Exception as e:
            import traceback
            logger.error(f"LLM解析失败: {str(e)}")
            logger.error(f"堆栈: {traceback.format_exc()}")
            return []

    async def _parse_with_vision(
        self,
        page,
        notice_type: str = None,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        使用视觉模型通过截图分析页面提取招标公告

        Args:
            page: Pyppeteer页面对象
            notice_type: 公告类型
            page_size: 每页数量

        Returns:
            list: 解析后的数据列表
        """
        import base64
        import json
        import re
        from services.unified_llm_service import unified_llm_service

        try:
            type_info = self.NOTICE_TYPE_MAP.get(notice_type, {})
            notice_type_name = type_info.get('name', '招标公告')

            logger.info("正在截取页面...")
            await page.setViewport({'width': 1280, 'height': 960})
            screenshot_bytes = await page.screenshot({
                'type': 'jpeg',
                'quality': 50,
                'fullPage': False
            })
            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.info(f"截图完成，大小: {len(image_base64)} 字符")

            prompt = f"""Extract tender notices from this image. Return as JSON array like:
[{{"title": "...", "date": "...", "region": "...", "source_url": "..."}}]
Only return JSON array, no other text. If you can see a URL for an item, include it in source_url field."""

            logger.info("正在使用视觉模型分析截图...")
            response = await unified_llm_service.analyze_image(
                image_base64=image_base64,
                prompt=prompt,
                model_id='qwen3-vl:8b',
                agent_type='vision',
                max_tokens=8192
            )

            if not response.get('success'):
                logger.error(f"视觉分析失败: {response.get('error', 'Unknown error')}")
                return []

            content = response.get('content', '')
            logger.info(f"视觉模型返回内容长度: {len(content)} 字符")

            # 尝试提取JSON数组
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group().replace('\n', ' ').replace('\r', '')
                try:
                    data = json.loads(json_str)
                    results = []
                    for item in data[:page_size]:
                        if isinstance(item, dict):
                            title = item.get('title') or item.get('Title', '')
                            date = item.get('date') or item.get('Date', '') or item.get('publish_date', '')
                            region = item.get('region') or item.get('Region', '上海市')
                            if title:
                                results.append({
                                    'title': title,
                                    'source_url': item.get('source_url') or '',
                                    'publish_date': date,
                                    'region': region,
                                    'project_code': item.get('project_code', ''),
                                    'budget': None,
                                    'source_type': 'shanghai_gov',
                                    'notice_type': notice_type,
                                    'notice_type_name': notice_type_name,
                                    'category': type_info.get('category', 'tender'),
                                })
                    logger.info(f"视觉解析成功，提取到 {len(results)} 条数据")
                    return results
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")

            logger.warning(f"视觉模型返回格式异常: {content[:200]}")
            return []

        except Exception as e:
            import traceback
            logger.error(f"视觉解析失败: {str(e)}")
            logger.error(f"堆栈: {traceback.format_exc()}")
            return []

    def _extract_items(self, soup: BeautifulSoup) -> List:
        """
        从页面提取公告列表
        """
        list_ul = soup.select_one('ul.list')
        if list_ul:
            items = list_ul.find_all('li', recursive=False)
            if items and len(items) > 2:
                logger.info(f"使用选择器 'ul.list > li' 找到 {len(items)} 个元素")
                return items

        selectors = [
            '.el-table__body tr',
            '.el-table__row',
            '.list-item',
            '.project-item',
            '.notice-item',
            'table tbody tr',
            '.content-list li',
            '.news-list li',
            '.list li',
            '.search-list li',
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
                link = item.get('href', '')
                title_elem = item.select_one('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                else:
                    title = item.get_text(strip=True)

                if not title or len(title) < 5:
                    title_elem = item.select_one('.title, .project-title, .name')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
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
                date_elem = item.select_one('.date, .time, .publish-date, .publishTime, .publish-time, td:nth-child(2), td:nth-child(3)')
                if date_elem:
                    publish_date = self._parse_date(date_elem.get_text(strip=True))

                region_elem = item.select_one('.region, .area, .district, .title-head, td:nth-child(4)')
                if region_elem:
                    region = region_elem.get_text(strip=True).replace('[', '').replace(']', '')
                
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
                'raw_data': {
                    'title': title,
                    'source_url': link,
                    'publish_date': str(publish_date) if publish_date else None,
                    'region': region,
                    'project_code': project_code,
                    'notice_type': notice_type,
                    'notice_type_name': type_info.get('name', ''),
                },
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
        验证URL是否有效
        对于政府网站SPA路由，HEAD请求常常失败（405/403/503），
        因此采用宽松策略：只有明确的404才判定无效，其他情况默认通过
        """
        if not url:
            return False
        if 'articleId' in url or '/site/detail' in url:
            return True
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.head(url, allow_redirects=True) as response:
                        if response.status == 404:
                            logger.warning(f"URL返回404: {url}")
                            return False
                        return True
                except aiohttp.ClientError:
                    try:
                        async with session.get(url, allow_redirects=True) as response:
                            if response.status == 404:
                                logger.warning(f"URL返回404: {url}")
                                return False
                            return True
                    except Exception:
                        return True
        except Exception:
            return True

    def _extract_article_id(self, url: str) -> str:
        """
        从URL中提取articleId参数
        """
        if not url:
            return ''
        match = re.search(r'articleId=([^&]+)', url)
        if match:
            return match.group(1)
        return ''

    async def _fetch_detail_via_api(self, article_id: str) -> Optional[Dict]:
        """
        通过/portal/detail API获取公告详情
        该API不需要JS会话，可直接HTTP请求获取结构化JSON数据
        """
        if not article_id:
            return None
        try:
            import aiohttp
            url = f"{self.base_url}/portal/detail?articleId={article_id}"
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and data.get('result', {}).get('data'):
                            return data['result']['data']
            return None
        except Exception as e:
            logger.debug(f"Detail API获取失败 [{article_id}]: {str(e)}")
            return None

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
