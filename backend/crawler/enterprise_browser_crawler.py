"""
企业信息浏览器采集器
专门用于从天眼查、企查查、爱企查等平台采集企业信息
支持反检测、验证码识别、人类行为模拟
"""
import asyncio
import logging
import random
import re
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import quote, urlparse
from datetime import datetime

from crawler.stealth_crawler import (
    StealthCrawler, 
    CrawlResult, 
    BrowserFingerprint,
    ProxyConfig,
    HumanBehaviorSimulator
)

logger = logging.getLogger(__name__)


class TianyanchaCrawler(StealthCrawler):
    """
    天眼查企业信息采集器
    """
    
    BASE_URL = "https://www.tianyancha.com"
    SEARCH_URL = "https://www.tianyancha.com/search"
    
    FIELD_MAPPING = {
        'name': 'name',
        'credit_code': 'creditCode',
        'registration_number': 'regNo',
        'legal_person': 'legalPersonName',
        'registered_capital': 'regCapital',
        'establishment_date': 'estiblishTime',
        'province': 'province',
        'city': 'city',
        'district': 'district',
        'address': 'regLocation',
        'business_scope': 'businessScope',
        'industry': 'industry',
        'company_type': 'companyType',
        'company_status': 'regStatus',
        'social_staff_num': 'socialStaffNum',
        'phone': 'phoneNumber',
        'email': 'email',
        'website': 'websiteList',
        'taxpayer_id': 'taxpayerId',
        'registration_authority': 'regInstitute',
        'approved_date': 'approvedTime',
        'organization_code': 'orgCode',
        'business_term': 'businessTerm',
        'insured_count': 'insuredCount',
        'former_names': 'originalName',
        'english_name': 'aliasName',
    }
    
    def __init__(self, proxy_config: ProxyConfig = None, ocr_service=None):
        super().__init__(
            proxy_config=proxy_config,
            max_retries=3,
            timeout=60,
            ocr_service=ocr_service
        )
    
    async def crawl(self, company_name: str, **kwargs) -> CrawlResult:
        """
        采集企业信息
        
        Args:
            company_name: 企业名称
        """
        url = f"{self.SEARCH_URL}?key={quote(company_name)}"
        return await self.crawl_with_fallback(url, company_name=company_name, **kwargs)
    
    async def parse_response(self, html: str, **kwargs) -> List[Dict[str, Any]]:
        """
        解析天眼查页面
        """
        company_name = kwargs.get('company_name', '')
        result = {'name': company_name, 'source': 'tianyancha'}
        
        try:
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    company_list = data.get('searchResult', {}).get('resultList', [])
                    if company_list:
                        company = company_list[0].get('data', {})
                        result = self._extract_company_data(company, company_name)
                        result['source'] = 'tianyancha'
                        return [result]
                except json.JSONDecodeError:
                    pass
            
            result = await self._parse_html_fallback(html, company_name)
            result['source'] = 'tianyancha'
            
        except Exception as e:
            logger.error(f"解析天眼查页面失败: {str(e)}")
        
        return [result] if len(result) > 2 else []
    
    def _extract_company_data(self, company: Dict, company_name: str) -> Dict:
        """
        从JSON数据中提取企业信息
        """
        result = {'name': company.get('name', company_name)}
        
        for target_field, source_field in self.FIELD_MAPPING.items():
            value = company.get(source_field)
            if value is not None:
                result[target_field] = value
        
        if company.get('estiblishTime'):
            result['establishment_date'] = self._parse_timestamp(company.get('estiblishTime'))
        
        if company.get('regCapital'):
            result['registered_capital'] = self._parse_capital(company.get('regCapital'))
        
        if company.get('tags'):
            result['tags'] = company.get('tags', [])
        
        return result
    
    async def _parse_html_fallback(self, html: str, company_name: str) -> Dict:
        """
        HTML正则解析作为备用方案
        """
        result = {'name': company_name}
        
        patterns = {
            'credit_code': r'统一社会信用代码[：:]\s*([A-Z0-9]{18})',
            'legal_person': r'法定代表人[：:]\s*<[^>]*>([^<]+)</',
            'registered_capital': r'注册资本[：:]\s*([0-9.]+[万亿]?元?)',
            'establishment_date': r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})',
            'address': r'注册地址[：:]\s*([^<\n]+)',
            'business_scope': r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)',
            'company_status': r'经营状态[：:]\s*([^<\n]+)',
            'phone': r'电话[：:]\s*([0-9\-]+)',
            'email': r'邮箱[：:]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                result[field] = match.group(1).strip()
        
        return result
    
    def _parse_timestamp(self, timestamp: Any) -> str:
        """
        解析时间戳
        """
        if not timestamp:
            return None
        
        if isinstance(timestamp, (int, float)):
            try:
                dt = datetime.fromtimestamp(timestamp / 1000)
                return dt.strftime('%Y-%m-%d')
            except (ValueError, OSError, OverflowError):
                return None
        
        return str(timestamp)[:10] if len(str(timestamp)) >= 10 else None
    
    def _parse_capital(self, capital_str: Any) -> float:
        """
        解析注册资本
        """
        if not capital_str:
            return None
        
        if isinstance(capital_str, (int, float)):
            return float(capital_str)
        
        capital_str = str(capital_str).strip()
        
        match = re.search(r'([\d,.]+)\s*(万|亿元)?', capital_str)
        if match:
            value = float(match.group(1).replace(',', ''))
            unit = match.group(2)
            if unit == '亿':
                value *= 100000000
            elif unit == '万':
                value *= 10000
            return value
        
        return None


class QichachaCrawler(StealthCrawler):
    """
    企查查企业信息采集器
    """
    
    BASE_URL = "https://www.qcc.com"
    SEARCH_URL = "https://www.qcc.com/web/search"
    
    FIELD_MAPPING = {
        'name': 'Name',
        'credit_code': 'CreditCode',
        'legal_person': 'OperName',
        'registered_capital': 'RegistCapi',
        'establishment_date': 'StartDate',
        'address': 'Address',
        'business_scope': 'Scope',
        'industry': 'Industry',
        'province': 'Province',
        'city': 'City',
        'phone': 'Phone',
        'email': 'Email',
        'company_status': 'Status',
    }
    
    def __init__(self, proxy_config: ProxyConfig = None, ocr_service=None):
        super().__init__(
            proxy_config=proxy_config,
            max_retries=3,
            timeout=60,
            ocr_service=ocr_service
        )
    
    async def crawl(self, company_name: str, **kwargs) -> CrawlResult:
        """
        采集企业信息
        """
        url = f"{self.SEARCH_URL}?key={quote(company_name)}"
        return await self.crawl_with_fallback(url, company_name=company_name, **kwargs)
    
    async def parse_response(self, html: str, **kwargs) -> List[Dict[str, Any]]:
        """
        解析企查查页面
        """
        company_name = kwargs.get('company_name', '')
        result = {'name': company_name, 'source': 'qichacha'}
        
        try:
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    company_list = data.get('Result', [])
                    if company_list:
                        company = company_list[0]
                        result = self._extract_company_data(company, company_name)
                        result['source'] = 'qichacha'
                        return [result]
                except json.JSONDecodeError:
                    pass
            
            result = self._parse_html_fallback(html, company_name)
            result['source'] = 'qichacha'
            
        except Exception as e:
            logger.error(f"解析企查查页面失败: {str(e)}")
        
        return [result] if len(result) > 2 else []
    
    def _extract_company_data(self, company: Dict, company_name: str) -> Dict:
        """
        从JSON数据中提取企业信息
        """
        result = {'name': company.get('Name', company_name)}
        
        for target_field, source_field in self.FIELD_MAPPING.items():
            value = company.get(source_field)
            if value is not None:
                result[target_field] = value
        
        return result
    
    def _parse_html_fallback(self, html: str, company_name: str) -> Dict:
        """
        HTML正则解析
        """
        result = {'name': company_name}
        
        patterns = {
            'credit_code': r'统一社会信用代码[：:]\s*([A-Z0-9]{18})',
            'legal_person': r'法定代表人[：:]\s*<[^>]*>([^<]+)</',
            'registered_capital': r'注册资本[：:]\s*([0-9.]+[万亿]?元?)',
            'establishment_date': r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})',
            'address': r'注册地址[：:]\s*([^<\n]+)',
            'business_scope': r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)',
            'company_status': r'经营状态[：:]\s*([^<\n]+)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                result[field] = match.group(1).strip()
        
        return result


class AiqichaCrawler(StealthCrawler):
    """
    爱企查企业信息采集器
    """
    
    BASE_URL = "https://aiqicha.baidu.com"
    SEARCH_URL = "https://aiqicha.baidu.com/s"
    
    FIELD_MAPPING = {
        'name': 'entName',
        'credit_code': 'creditCode',
        'legal_person': 'legalPerson',
        'registered_capital': 'regCap',
        'establishment_date': 'openTime',
        'address': 'opLoc',
        'business_scope': 'opScope',
        'industry': 'industry',
        'province': 'province',
        'city': 'city',
        'company_status': 'entStatus',
    }
    
    def __init__(self, proxy_config: ProxyConfig = None, ocr_service=None):
        super().__init__(
            proxy_config=proxy_config,
            max_retries=3,
            timeout=60,
            ocr_service=ocr_service
        )
    
    async def crawl(self, company_name: str, **kwargs) -> CrawlResult:
        """
        采集企业信息
        """
        url = f"{self.SEARCH_URL}?q={quote(company_name)}"
        return await self.crawl_with_fallback(url, company_name=company_name, **kwargs)
    
    async def parse_response(self, html: str, **kwargs) -> List[Dict[str, Any]]:
        """
        解析爱企查页面
        """
        company_name = kwargs.get('company_name', '')
        result = {'name': company_name, 'source': 'aiqicha'}
        
        try:
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    company_list = data.get('result', {}).get('resultList', [])
                    if company_list:
                        company = company_list[0]
                        result = self._extract_company_data(company, company_name)
                        result['source'] = 'aiqicha'
                        return [result]
                except json.JSONDecodeError:
                    pass
            
            result = self._parse_html_fallback(html, company_name)
            result['source'] = 'aiqicha'
            
        except Exception as e:
            logger.error(f"解析爱企查页面失败: {str(e)}")
        
        return [result] if len(result) > 2 else []
    
    def _extract_company_data(self, company: Dict, company_name: str) -> Dict:
        """
        从JSON数据中提取企业信息
        """
        result = {'name': company.get('entName', company_name)}
        
        for target_field, source_field in self.FIELD_MAPPING.items():
            value = company.get(source_field)
            if value is not None:
                result[target_field] = value
        
        return result
    
    def _parse_html_fallback(self, html: str, company_name: str) -> Dict:
        """
        HTML正则解析
        """
        result = {'name': company_name}
        
        patterns = {
            'credit_code': r'统一社会信用代码[：:]\s*([A-Z0-9]{18})',
            'legal_person': r'法定代表人[：:]\s*<[^>]*>([^<]+)</',
            'registered_capital': r'注册资本[：:]\s*([0-9.]+[万亿]?元?)',
            'establishment_date': r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})',
            'address': r'注册地址[：:]\s*([^<\n]+)',
            'business_scope': r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)',
            'company_status': r'经营状态[：:]\s*([^<\n]+)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                result[field] = match.group(1).strip()
        
        return result


class EnterpriseBrowserCollector:
    """
    企业信息浏览器采集器
    支持多平台采集，自动降级
    """
    
    SOURCE_ORDER = ['tianyancha', 'qichacha', 'aiqicha']
    
    def __init__(
        self,
        proxy_config: ProxyConfig = None,
        ocr_service=None
    ):
        self.proxy_config = proxy_config
        self.ocr_service = ocr_service
        
        self._crawlers = {
            'tianyancha': TianyanchaCrawler(proxy_config, ocr_service),
            'qichacha': QichachaCrawler(proxy_config, ocr_service),
            'aiqicha': AiqichaCrawler(proxy_config, ocr_service),
        }
    
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
        sources_to_try = self._get_source_order(source)
        sources_tried = []
        errors = []
        
        for src in sources_to_try:
            sources_tried.append(src)
            crawler = self._crawlers.get(src)
            
            if not crawler:
                continue
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"尝试从 {src} 采集企业信息: {company_name} (尝试 {attempt + 1}/{max_retries})")
                    
                    result = await crawler.crawl(company_name)
                    
                    if result.success and result.data:
                        data = result.data[0] if result.data else {}
                        
                        if len(data) > 3:
                            logger.info(f"从 {src} 成功采集企业信息: {company_name}")
                            return {
                                'success': True,
                                'data': data,
                                'source': src,
                                'sources_tried': sources_tried,
                                'duration': result.duration
                            }
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(random.uniform(2, 5))
                        
                except Exception as e:
                    error_msg = f"{src} 采集失败: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(random.uniform(2, 5))
            
            if src != sources_to_try[-1]:
                await asyncio.sleep(random.uniform(1, 3))
        
        return {
            'success': False,
            'error': f'无法从任何数据源获取企业信息: {company_name}',
            'sources_tried': sources_tried,
            'errors': errors
        }
    
    def _get_source_order(self, source: str) -> List[str]:
        """
        获取数据源尝试顺序
        """
        if source != 'auto' and source in self._crawlers:
            other_sources = [s for s in self.SOURCE_ORDER if s != source]
            return [source] + other_sources
        
        return self.SOURCE_ORDER
    
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
