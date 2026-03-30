"""
支持Cookie登录的企业信息采集器
使用登录态Cookie绑过登录验证
"""
import asyncio
import logging
import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from datetime import datetime

from crawler.cookie_manager import cookie_manager

logger = logging.getLogger(__name__)


class CookieBasedCollector:
    """
    基于Cookie的企业信息采集器
    使用已登录的Cookie进行采集
    """
    
    FIELD_MAPPING = {
        'name': ['name', 'companyName', 'entName'],
        'credit_code': ['creditCode', 'credit_code', 'CreditCode'],
        'legal_person': ['legalPersonName', 'legalPerson', 'OperName'],
        'registered_capital': ['regCapital', 'regCap', 'RegistCapi'],
        'establishment_date': ['estiblishTime', 'openTime', 'StartDate'],
        'address': ['regLocation', 'opLoc', 'Address'],
        'business_scope': ['businessScope', 'opScope', 'Scope'],
        'industry': ['industry', 'Industry'],
        'industry_code': ['industryCode', 'industry_code', 'IndustryCode'],
        'province': ['province', 'Province'],
        'city': ['city', 'City'],
        'company_status': ['regStatus', 'entStatus', 'Status'],
        'phone': ['phoneNumber', 'Phone'],
        'email': ['email', 'Email'],
        'website': ['websiteList', 'website', 'WebSite'],
        'enterprise_scale': ['enterpriseScale', 'scale', 'EntScale'],
        'staff_count': ['staffNum', 'staffCount', 'socialStaffNum'],
        'insured_count': ['socialStaffNum', 'insuredCount', 'InsuredCount'],
    }
    
    SOURCE_URLS = {
        'tianyancha': 'https://www.tianyancha.com/search?key={}',
        'qichacha': 'https://www.qcc.com/web/search?key={}',
        'aiqicha': 'https://aiqicha.baidu.com/s?q={}',
        'qixin': 'https://www.qixin.com/search?key={}',
    }
    
    def __init__(self):
        self._session = None
    
    async def collect(
        self,
        company_name: str,
        source: str = 'auto'
    ) -> Dict[str, Any]:
        """
        采集企业信息
        
        Args:
            company_name: 企业名称
            source: 数据源
            
        Returns:
            Dict: 采集结果
        """
        source_order = self._get_source_order(source)
        sources_tried = []
        errors = []
        
        for src in source_order:
            if not cookie_manager.has_valid_cookies(src):
                logger.warning(f"平台 {src} 没有有效的登录Cookie，跳过")
                continue
            
            sources_tried.append(src)
            
            try:
                logger.info(f"使用Cookie从 {src} 采集: {company_name}")
                
                result = await self._collect_with_cookies(company_name, src)
                
                if result and len(result) > 3:
                    result['source'] = src
                    logger.info(f"从 {src} 成功采集: {company_name}")
                    return {
                        'success': True,
                        'data': result,
                        'source': src,
                        'sources_tried': sources_tried,
                        'mode': 'cookie'
                    }
                    
            except Exception as e:
                error_msg = f"{src} 采集失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            'success': False,
            'error': f"无法从任何已登录平台获取企业信息: {company_name}",
            'sources_tried': sources_tried,
            'errors': errors
        }
    
    async def _collect_with_cookies(self, company_name: str, source: str) -> Dict[str, Any]:
        """使用Cookie采集"""
        try:
            from scrapling.fetchers import StealthyFetcher
        except ImportError:
            raise ImportError("请安装 scrapling: pip install scrapling[fetchers]")
        
        url = self.SOURCE_URLS.get(source, '').format(quote(company_name))
        
        cookies = cookie_manager.get_cookies_for_scrapling(source)
        if not cookies:
            raise Exception(f"无法获取 {source} 的Cookie")
        
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            cookies=cookies
        )
        
        if not page:
            raise Exception("页面获取失败")
        
        html = page.html if hasattr(page, 'html') else str(page)
        
        if self._is_login_page(html, source):
            cookie_manager.clear_cookies(source)
            raise Exception("Cookie已失效，请重新登录")
        
        return self._extract_data(html, company_name, source)
    
    def _is_login_page(self, html: str, source: str) -> bool:
        """检查是否是登录页面"""
        login_indicators = {
            'tianyancha': ['login', '登录', '请先登录'],
            'qichacha': ['weblogin', '会员登录', '请登录'],
            'aiqicha': ['passport.baidu.com', '请登录'],
            'qixin': ['login', '登录', '请先登录'],
        }
        
        indicators = login_indicators.get(source, ['login', '登录'])
        html_lower = html.lower()
        
        return any(ind.lower() in html_lower for ind in indicators)
    
    def _extract_data(self, html: str, company_name: str, source: str) -> Dict[str, Any]:
        """提取数据"""
        result = {'name': company_name}
        
        result.update(self._extract_from_json(html, company_name))
        
        result.update(self._extract_from_patterns(html))
        
        return result
    
    def _extract_from_json(self, html: str, company_name: str) -> Dict[str, Any]:
        """从JSON数据提取"""
        result = {}
        
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__NEXT_DATA__\s*=\s*({.*?});',
            r'"resultList"\s*:\s*(\[.*?\])',
            r'"Result"\s*:\s*(\[.*?\])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    extracted = self._parse_json_structure(data, company_name)
                    if extracted:
                        result.update(extracted)
                        break
                except json.JSONDecodeError:
                    continue
        
        return result
    
    def _parse_json_structure(self, data: Any, company_name: str) -> Dict[str, Any]:
        """解析JSON结构"""
        result = {}
        
        def find_company(obj, depth=0):
            if depth > 10:
                return None
            
            if isinstance(obj, dict):
                if obj.get('name') == company_name or obj.get('entName') == company_name:
                    return obj
                
                for key in ['resultList', 'Result', 'result', 'data', 'items']:
                    if key in obj:
                        items = obj[key]
                        if isinstance(items, list) and items:
                            first = items[0]
                            if isinstance(first, dict):
                                if 'data' in first:
                                    return first['data']
                                return first
                
                for value in obj.values():
                    found = find_company(value, depth + 1)
                    if found:
                        return found
                        
            elif isinstance(obj, list):
                for item in obj:
                    found = find_company(item, depth + 1)
                    if found:
                        return found
            
            return None
        
        company_data = find_company(data)
        
        if company_data:
            for target_field, source_fields in self.FIELD_MAPPING.items():
                for source_field in source_fields:
                    if source_field in company_data:
                        result[target_field] = company_data[source_field]
                        break
        
        return result
    
    def _extract_from_patterns(self, html: str) -> Dict[str, Any]:
        """从文本模式提取"""
        result = {}
        
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
                match = re.search(pattern, html)
                if match:
                    result[field] = match.group(1).strip()
        
        return result
    
    def _get_source_order(self, source: str) -> List[str]:
        """获取数据源顺序"""
        all_sources = ['tianyancha', 'qichacha', 'aiqicha', 'qixin']
        
        if source != 'auto' and source in all_sources:
            other_sources = [s for s in all_sources if s != source]
            return [source] + other_sources
        
        return all_sources


async def collect_with_cookies(company_name: str, source: str = 'auto') -> Dict[str, Any]:
    """
    使用Cookie采集企业信息的便捷函数
    
    Args:
        company_name: 企业名称
        source: 数据源
        
    Returns:
        Dict: 采集结果
    """
    collector = CookieBasedCollector()
    return await collector.collect(company_name, source)
