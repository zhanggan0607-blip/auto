"""
企业信息采集器 - 基于 Scrapling + AI 语义提取
支持自适应爬取、反检测、AI辅助提取
"""
import asyncio
import logging
import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from datetime import datetime

logger = logging.getLogger(__name__)


class ScraplingEnterpriseCollector:
    """
    基于 Scrapling 的企业信息采集器
    支持：
    - 自适应元素定位（网站结构变化时自动适应）
    - 内置反检测能力
    - AI 语义提取
    - 自动绕过 Cloudflare 等反爬
    """
    
    FIELD_MAPPING = {
        'name': ['name', 'companyName', 'entName', '企业名称'],
        'credit_code': ['creditCode', 'credit_code', 'CreditCode', '统一社会信用代码'],
        'legal_person': ['legalPersonName', 'legalPerson', 'OperName', '法定代表人'],
        'registered_capital': ['regCapital', 'regCap', 'RegistCapi', '注册资本'],
        'establishment_date': ['estiblishTime', 'openTime', 'StartDate', '成立日期'],
        'address': ['regLocation', 'opLoc', 'Address', '注册地址'],
        'business_scope': ['businessScope', 'opScope', 'Scope', '经营范围'],
        'industry': ['industry', 'Industry', '所属行业'],
        'province': ['province', 'Province'],
        'city': ['city', 'City'],
        'company_status': ['regStatus', 'entStatus', 'Status', '经营状态'],
        'phone': ['phoneNumber', 'Phone', '联系电话'],
        'email': ['email', 'Email', '邮箱'],
    }
    
    SOURCE_URLS = {
        'tianyancha': 'https://www.tianyancha.com/search?key={}',
        'qichacha': 'https://www.qcc.com/web/search?key={}',
        'aiqicha': 'https://aiqicha.baidu.com/s?q={}',
    }
    
    def __init__(self, use_ai: bool = True, use_stealth: bool = True):
        """
        初始化采集器
        
        Args:
            use_ai: 是否启用 AI 语义提取
            use_stealth: 是否使用隐身模式
        """
        self.use_ai = use_ai
        self.use_stealth = use_stealth
        self._fetcher = None
        self._stealthy_fetcher = None
    
    def _get_fetcher(self):
        """获取普通 Fetcher"""
        if self._fetcher is None:
            try:
                from scrapling.fetchers import Fetcher
                self._fetcher = Fetcher
            except ImportError:
                raise ImportError(
                    "Scrapling 未安装，请运行: pip install scrapling[fetchers] && scrapling install"
                )
        return self._fetcher
    
    def _get_stealthy_fetcher(self):
        """获取隐身 Fetcher"""
        if self._stealthy_fetcher is None:
            try:
                from scrapling.fetchers import StealthyFetcher
                self._stealthy_fetcher = StealthyFetcher
            except ImportError:
                raise ImportError(
                    "Scrapling fetchers 未安装，请运行: pip install scrapling[fetchers] && scrapling install"
                )
        return self._stealthy_fetcher
    
    async def collect(
        self,
        company_name: str,
        source: str = 'auto',
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        采集企业信息
        
        Args:
            company_name: 企业名称
            source: 数据源 (tianyancha/qichacha/aiqicha/auto)
            max_retries: 每个数据源最大重试次数
            
        Returns:
            Dict: 采集结果
        """
        sources_tried = []
        errors = []
        
        source_order = self._get_source_order(source)
        
        for src in source_order:
            sources_tried.append(src)
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"尝试从 {src} 采集企业信息: {company_name} (尝试 {attempt + 1}/{max_retries})")
                    
                    result = await self._collect_from_source(company_name, src)
                    
                    if result and len(result) > 3:
                        result['source'] = src
                        result['sources_tried'] = sources_tried
                        logger.info(f"从 {src} 成功采集企业信息: {company_name}")
                        
                        return {
                            'success': True,
                            'data': result,
                            'source': src,
                            'sources_tried': sources_tried
                        }
                        
                except Exception as e:
                    error_msg = f"{src} 采集失败: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
            
            if src != source_order[-1]:
                await asyncio.sleep(1)
        
        return {
            'success': False,
            'error': f"无法从任何数据源获取企业信息: {company_name}",
            'sources_tried': sources_tried,
            'errors': errors
        }
    
    async def _collect_from_source(self, company_name: str, source: str) -> Dict[str, Any]:
        """
        从指定数据源采集
        """
        url = self.SOURCE_URLS.get(source, '').format(quote(company_name))
        
        if not url:
            raise ValueError(f"不支持的数据源: {source}")
        
        page = await self._fetch_page(url)
        
        if page is None:
            raise Exception("页面获取失败")
        
        result = self._extract_data(page, company_name)
        
        if self.use_ai and len(result) < 5:
            ai_result = await self._extract_with_ai(page, company_name)
            if ai_result:
                result.update(ai_result)
        
        return result
    
    async def _fetch_page(self, url: str):
        """
        获取页面
        """
        try:
            if self.use_stealth:
                StealthyFetcher = self._get_stealthy_fetcher()
                page = StealthyFetcher.fetch(
                    url,
                    headless=True,
                    network_idle=True,
                    solve_cloudflare=True
                )
            else:
                Fetcher = self._get_fetcher()
                page = Fetcher.get(url, impersonate='chrome')
            
            return page
            
        except Exception as e:
            logger.error(f"获取页面失败: {str(e)}")
            return None
    
    def _extract_data(self, page, company_name: str) -> Dict[str, Any]:
        """
        从页面提取数据
        """
        result = {'name': company_name}
        
        result.update(self._extract_from_json_data(page, company_name))
        
        result.update(self._extract_from_text_patterns(page))
        
        result.update(self._extract_from_selectors(page))
        
        return result
    
    def _extract_from_json_data(self, page, company_name: str) -> Dict[str, Any]:
        """
        从页面 JSON 数据中提取
        """
        result = {}
        
        try:
            html = page.html if hasattr(page, 'html') else str(page)
            
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__NEXT_DATA__\s*=\s*({.*?});',
                r'"data"\s*:\s*({.*?})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        extracted = self._parse_json_data(data, company_name)
                        if extracted:
                            result.update(extracted)
                            break
                    except json.JSONDecodeError:
                        continue
                    
        except Exception as e:
            logger.warning(f"JSON 数据提取失败: {str(e)}")
        
        return result
    
    def _parse_json_data(self, data: Dict, company_name: str) -> Dict[str, Any]:
        """
        解析 JSON 数据结构
        """
        result = {}
        
        def find_company_data(obj, depth=0):
            if depth > 10:
                return None
            
            if isinstance(obj, dict):
                if obj.get('name') == company_name or obj.get('entName') == company_name:
                    return obj
                
                if 'searchResult' in obj or 'resultList' in obj or 'Result' in obj:
                    for key in ['searchResult', 'resultList', 'Result', 'result']:
                        if key in obj:
                            items = obj[key]
                            if isinstance(items, list) and items:
                                first = items[0]
                                if isinstance(first, dict):
                                    if 'data' in first:
                                        return first['data']
                                    return first
                
                for value in obj.values():
                    found = find_company_data(value, depth + 1)
                    if found:
                        return found
                        
            elif isinstance(obj, list):
                for item in obj:
                    found = find_company_data(item, depth + 1)
                    if found:
                        return found
            
            return None
        
        company_data = find_company_data(data)
        
        if company_data:
            for target_field, source_fields in self.FIELD_MAPPING.items():
                for source_field in source_fields:
                    if source_field in company_data:
                        result[target_field] = company_data[source_field]
                        break
        
        return result
    
    def _extract_from_text_patterns(self, page) -> Dict[str, Any]:
        """
        从文本模式中提取
        """
        result = {}
        
        try:
            text = page.text if hasattr(page, 'text') else str(page)
            
            patterns = {
                'credit_code': r'统一社会信用代码[：:]\s*([A-Z0-9]{18})',
                'legal_person': r'法定代表人[：:]\s*([^\s<]+)',
                'registered_capital': r'注册资本[：:]\s*([0-9.]+[万亿]?元?)',
                'establishment_date': r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})',
                'address': r'注册地址[：:]\s*([^<\n]{5,100})',
                'phone': r'(?:电话|联系方式)[：:]\s*([0-9\-]{7,15})',
                'email': r'邮箱[：:]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            }
            
            for field, pattern in patterns.items():
                if field not in result or not result.get(field):
                    match = re.search(pattern, text)
                    if match:
                        result[field] = match.group(1).strip()
                        
        except Exception as e:
            logger.warning(f"文本模式提取失败: {str(e)}")
        
        return result
    
    def _extract_from_selectors(self, page) -> Dict[str, Any]:
        """
        从 CSS 选择器中提取（使用 Scrapling 的自适应能力）
        """
        result = {}
        
        try:
            selector_configs = [
                {'field': 'name', 'selectors': ['.company-name', '.ent-name', 'h1.name', '.title']},
                {'field': 'credit_code', 'selectors': ['.credit-code', '.creditCode', '[data-key="creditCode"]']},
                {'field': 'legal_person', 'selectors': ['.legal-person', '.legalPerson', '.oper-name']},
                {'field': 'registered_capital', 'selectors': ['.reg-capital', '.regCapital', '.capital']},
                {'field': 'address', 'selectors': ['.address', '.reg-location', '.regLocation']},
            ]
            
            for config in selector_configs:
                field = config['field']
                if field not in result or not result.get(field):
                    for selector in config['selectors']:
                        try:
                            element = page.css(selector)
                            if element:
                                text = element[0].text.strip() if hasattr(element[0], 'text') else str(element[0])
                                if text:
                                    result[field] = text
                                    break
                        except Exception:
                            continue
                            
        except Exception as e:
            logger.warning(f"选择器提取失败: {str(e)}")
        
        return result
    
    async def _extract_with_ai(self, page, company_name: str) -> Dict[str, Any]:
        """
        使用 AI 语义提取
        """
        try:
            from openclaw.ai_extractors.enterprise_extractor import AIEnterpriseExtractor
            
            extractor = AIEnterpriseExtractor()
            html = page.html if hasattr(page, 'html') else str(page)
            
            return await extractor.extract(html, company_name)
            
        except ImportError:
            logger.warning("AI 提取器未安装，跳过 AI 提取")
            return {}
        except Exception as e:
            logger.warning(f"AI 提取失败: {str(e)}")
            return {}
    
    def _get_source_order(self, source: str) -> List[str]:
        """
        获取数据源尝试顺序
        """
        all_sources = ['tianyancha', 'qichacha', 'aiqicha']
        
        if source != 'auto' and source in all_sources:
            other_sources = [s for s in all_sources if s != source]
            return [source] + other_sources
        
        return all_sources
    
    async def collect_batch(
        self,
        company_names: List[str],
        source: str = 'auto',
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        批量采集企业信息
        
        Args:
            company_names: 企业名称列表
            source: 数据源
            max_concurrent: 最大并发数
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def collect_with_limit(name: str) -> Dict:
            async with semaphore:
                result = await self.collect(name, source)
                result['company_name'] = name
                return result
        
        tasks = [collect_with_limit(name) for name in company_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if not isinstance(r, Exception) else {
                'success': False,
                'company_name': company_names[i],
                'error': str(r)
            }
            for i, r in enumerate(results)
        ]
