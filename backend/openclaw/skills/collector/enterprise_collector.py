"""
企业信息采集技能 - 增强版
支持浏览器自动化采集，具备反检测能力
"""
import asyncio
import logging
import ssl
import re
import json
import aiohttp
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
from openclaw.skill_registry import Skill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


class RetryConfig:
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2
    RETRY_DELAY_MAX = 10
    SOURCE_RETRY_DELAY = 1


class EnterpriseInfoCollectorSkill(Skill):
    """
    企业信息采集技能
    支持两种采集模式：
    1. 浏览器模式（推荐）：使用反检测浏览器采集，可绑过JS渲染和部分反爬
    2. HTTP模式：快速采集，适用于无反爬限制的场景
    """
    
    metadata = SkillMetadata(
        name='enterprise_info_collector',
        description='从公开网站采集企业信息（天眼查、企查查、爱企查、公示系统），支持浏览器反检测模式',
        version='4.0.0',
        author='OpenClaw',
        category='collector',
        tags=['enterprise', 'tianyancha', 'qichacha', 'aiqicha', 'gsxt', 'crawler', 'stealth'],
        input_schema={
            'type': 'object',
            'properties': {
                'company_name': {
                    'type': 'string',
                    'description': '企业全称'
                },
                'source': {
                    'type': 'string',
                    'enum': ['tianyancha', 'qichacha', 'aiqicha', 'gsxt', 'auto'],
                    'default': 'auto',
                    'description': '数据源'
                },
                'mode': {
                    'type': 'string',
                    'enum': ['browser', 'http', 'auto'],
                    'default': 'auto',
                    'description': '采集模式：browser=浏览器模式，http=HTTP模式，auto=自动选择'
                },
                'fields': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '需要采集的字段列表'
                },
                'max_retries': {
                    'type': 'integer',
                    'default': 3,
                    'description': '最大重试次数'
                },
                'use_proxy': {
                    'type': 'boolean',
                    'default': False,
                    'description': '是否使用代理'
                }
            },
            'required': ['company_name']
        },
        output_schema={
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {'type': 'object'},
                'error': {'type': 'string'}
            }
        }
    )
    
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
        'tags': 'tags',
    }
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行企业信息采集
        """
        company_name = kwargs.get('company_name')
        source = kwargs.get('source', 'auto')
        mode = kwargs.get('mode', 'auto')
        fields = kwargs.get('fields')
        max_retries = kwargs.get('max_retries', RetryConfig.MAX_RETRIES)
        use_proxy = kwargs.get('use_proxy', False)
        
        if not company_name:
            return SkillResult(
                success=False,
                error='企业名称不能为空'
            )
        
        try:
            if mode == 'browser' or (mode == 'auto' and self._should_use_browser(source)):
                result = await self._collect_with_browser(
                    company_name, source, max_retries, use_proxy
                )
            else:
                result = await self._collect_with_http(
                    company_name, source, max_retries
                )
            
            if result.get('success'):
                normalized_data = self._normalize_data(
                    result.get('data', {}),
                    result.get('source', source)
                )
                
                return SkillResult(
                    success=True,
                    data=normalized_data,
                    metadata={
                        'source': result.get('source'),
                        'sources_tried': result.get('sources_tried', []),
                        'company_name': company_name,
                        'mode': result.get('mode', mode),
                        'fields_count': len(normalized_data),
                        'timestamp': datetime.now().isoformat()
                    }
                )
            else:
                return SkillResult(
                    success=False,
                    error=result.get('error', '采集失败'),
                    metadata={
                        'sources_tried': result.get('sources_tried', []),
                        'mode': result.get('mode', mode)
                    }
                )
            
        except Exception as e:
            logger.error(f"企业信息采集失败: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e),
                metadata={'sources_tried': self._get_source_order(source)}
            )
    
    def _should_use_browser(self, source: str) -> bool:
        """
        判断是否应该使用浏览器模式
        """
        browser_required_sources = ['tianyancha', 'qichacha', 'aiqicha']
        if source in browser_required_sources:
            return True
        return True
    
    async def _collect_with_browser(
        self,
        company_name: str,
        source: str,
        max_retries: int,
        use_proxy: bool
    ) -> Dict[str, Any]:
        """
        使用浏览器模式采集（优先使用 Scrapling）
        """
        try:
            from crawler.scrapling_enterprise_collector import ScraplingEnterpriseCollector
            
            collector = ScraplingEnterpriseCollector(use_ai=True, use_stealth=True)
            result = await collector.collect(company_name, source, max_retries)
            
            if result.get('success'):
                return {
                    'success': True,
                    'data': result.get('data', {}),
                    'source': result.get('source'),
                    'sources_tried': result.get('sources_tried', []),
                    'mode': 'scrapling'
                }
            
        except ImportError:
            logger.warning("Scrapling 未安装，尝试 Pyppeteer 浏览器采集")
            
            try:
                from crawler.enterprise_browser_crawler import EnterpriseBrowserCollector
                from crawler.stealth_crawler import ProxyConfig
                
                proxy_config = None
                if use_proxy:
                    proxy_config = ProxyConfig(enabled=True)
                
                ocr_service = self._get_ocr_service()
                
                collector = EnterpriseBrowserCollector(
                    proxy_config=proxy_config,
                    ocr_service=ocr_service
                )
                
                result = await collector.collect(company_name, source, max_retries)
                
                return {
                    'success': result.get('success', False),
                    'data': result.get('data', {}),
                    'source': result.get('source'),
                    'sources_tried': result.get('sources_tried', []),
                    'mode': 'browser',
                    'error': result.get('error')
                }
                
            except ImportError as e:
                logger.warning(f"浏览器采集模块导入失败，降级到HTTP模式: {str(e)}")
                return await self._collect_with_http(company_name, source, max_retries)
                
        except Exception as e:
            logger.error(f"浏览器模式采集失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'browser'
            }
    
    def _get_ocr_service(self):
        """
        获取OCR服务实例
        """
        try:
            from services.aliyun_ocr_service import AliyunOCRService
            return AliyunOCRService()
        except Exception as e:
            logger.warning(f"OCR服务初始化失败: {str(e)}")
            return None
    
    async def _collect_with_http(
        self,
        company_name: str,
        source: str,
        max_retries: int
    ) -> Dict[str, Any]:
        """
        使用HTTP模式采集（原有逻辑）
        """
        headers = self._get_random_headers()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        source_order = self._get_source_order(source)
        sources_tried = []
        errors = []
        
        async with aiohttp.ClientSession(connector=connector) as session:
            for src in source_order:
                sources_tried.append(src)
                for attempt in range(max_retries):
                    try:
                        result = await self._collect_from_source(
                            company_name, src, session, headers
                        )
                        if result and len(result) > 1:
                            logger.info(f"从 {src} 成功采集企业信息: {company_name}")
                            return {
                                'success': True,
                                'data': result,
                                'source': src,
                                'sources_tried': sources_tried,
                                'mode': 'http'
                            }
                        
                        if attempt < max_retries - 1:
                            delay = self._calculate_retry_delay(attempt)
                            await asyncio.sleep(delay)
                            
                    except Exception as e:
                        error_msg = f"{src} 采集失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                        
                        if attempt < max_retries - 1:
                            delay = self._calculate_retry_delay(attempt)
                            await asyncio.sleep(delay)
                
                if src != source_order[-1]:
                    await asyncio.sleep(RetryConfig.SOURCE_RETRY_DELAY)
        
        error_detail = '; '.join(errors[-6:])
        return {
            'success': False,
            'error': f"无法从公开渠道获取企业信息: {company_name}。错误: {error_detail}",
            'sources_tried': source_order,
            'mode': 'http'
        }
    
    async def _collect_from_source(
        self,
        company_name: str,
        source: str,
        session: aiohttp.ClientSession,
        headers: Dict
    ) -> Dict:
        """
        从指定数据源采集企业信息
        """
        collectors = {
            'tianyancha': self._collect_from_tianyancha,
            'qichacha': self._collect_from_qichacha,
            'aiqicha': self._collect_from_aiqicha,
            'gsxt': self._collect_from_gsxt,
        }
        
        collector = collectors.get(source)
        if not collector:
            raise Exception(f"不支持的数据源: {source}")
        
        return await collector(company_name, session, headers)
    
    async def _collect_from_tianyancha(
        self, 
        company_name: str, 
        session: aiohttp.ClientSession, 
        headers: dict
    ) -> Dict:
        """
        从天眼查采集企业信息
        """
        search_url = f"https://www.tianyancha.com/search?key={quote(company_name)}"
        
        async with session.get(
            search_url, 
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True
        ) as resp:
            if resp.status != 200:
                raise Exception(f"天眼查请求失败: {resp.status}")
            
            html = await resp.text()
            return self._parse_tianyancha_html(html, company_name)
    
    def _parse_tianyancha_html(self, html: str, company_name: str) -> Dict:
        """
        解析天眼查HTML页面
        """
        result = {'name': company_name}
        
        try:
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    company_list = data.get('searchResult', {}).get('resultList', [])
                    if company_list:
                        company = company_list[0].get('data', {})
                        result.update({
                            'name': company.get('name', company_name),
                            'creditCode': company.get('creditCode'),
                            'legalPersonName': company.get('legalPersonName'),
                            'regCapital': company.get('regCapital'),
                            'estiblishTime': company.get('estiblishTime'),
                            'regStatus': company.get('regStatus'),
                            'regLocation': company.get('regLocation'),
                            'businessScope': company.get('businessScope'),
                            'industry': company.get('industry'),
                            'province': company.get('province'),
                            'city': company.get('city'),
                            'phone': company.get('phone'),
                            'email': company.get('email'),
                        })
                        if len(result) > 1:
                            return result
                except json.JSONDecodeError:
                    pass
            
            credit_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', html)
            if credit_match:
                result['creditCode'] = credit_match.group(1)
            
            legal_match = re.search(r'法定代表人[：:]\s*<[^>]*>([^<]+)</', html)
            if legal_match:
                result['legalPersonName'] = legal_match.group(1).strip()
            
            capital_match = re.search(r'注册资本[：:]\s*([0-9.]+[万亿]?元?)', html)
            if capital_match:
                result['regCapital'] = capital_match.group(1)
            
            date_match = re.search(r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})', html)
            if date_match:
                result['estiblishTime'] = date_match.group(1)
            
            address_match = re.search(r'注册地址[：:]\s*([^<\n]+)', html)
            if address_match:
                result['regLocation'] = address_match.group(1).strip()
            
            scope_match = re.search(r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)', html)
            if scope_match:
                result['businessScope'] = scope_match.group(1).strip()
            
            status_match = re.search(r'经营状态[：:]\s*([^<\n]+)', html)
            if status_match:
                result['regStatus'] = status_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"解析天眼查HTML失败: {str(e)}")
        
        if len(result) <= 1:
            raise Exception(f"未能从天眼查获取到企业信息: {company_name}")
        
        return result
    
    async def _collect_from_qichacha(
        self, 
        company_name: str, 
        session: aiohttp.ClientSession, 
        headers: dict
    ) -> Dict:
        """
        从企查查采集企业信息
        """
        search_url = f"https://www.qcc.com/web/search?key={quote(company_name)}"
        
        async with session.get(
            search_url, 
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True
        ) as resp:
            if resp.status != 200:
                raise Exception(f"企查查请求失败: {resp.status}")
            
            html = await resp.text()
            return self._parse_qichacha_html(html, company_name)
    
    def _parse_qichacha_html(self, html: str, company_name: str) -> Dict:
        """
        解析企查查HTML页面
        """
        result = {'name': company_name}
        
        try:
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    company_list = data.get('Result', [])
                    if company_list:
                        company = company_list[0]
                        result.update({
                            'name': company.get('Name', company_name),
                            'creditCode': company.get('CreditCode'),
                            'legalPersonName': company.get('OperName'),
                            'regCapital': company.get('RegistCapi'),
                            'estiblishTime': company.get('StartDate'),
                            'regStatus': company.get('Status'),
                            'regLocation': company.get('Address'),
                            'businessScope': company.get('Scope'),
                            'industry': company.get('Industry'),
                            'province': company.get('Province'),
                            'city': company.get('City'),
                            'phone': company.get('Phone'),
                            'email': company.get('Email'),
                        })
                        if len(result) > 1:
                            return result
                except json.JSONDecodeError:
                    pass
            
            credit_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', html)
            if credit_match:
                result['creditCode'] = credit_match.group(1)
            
            legal_match = re.search(r'法定代表人[：:]\s*<[^>]*>([^<]+)</', html)
            if legal_match:
                result['legalPersonName'] = legal_match.group(1).strip()
            
            capital_match = re.search(r'注册资本[：:]\s*([0-9.]+[万亿]?元?)', html)
            if capital_match:
                result['regCapital'] = capital_match.group(1)
            
            date_match = re.search(r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})', html)
            if date_match:
                result['estiblishTime'] = date_match.group(1)
            
            address_match = re.search(r'注册地址[：:]\s*([^<\n]+)', html)
            if address_match:
                result['regLocation'] = address_match.group(1).strip()
            
            scope_match = re.search(r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)', html)
            if scope_match:
                result['businessScope'] = scope_match.group(1).strip()
            
            status_match = re.search(r'经营状态[：:]\s*([^<\n]+)', html)
            if status_match:
                result['regStatus'] = status_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"解析企查查HTML失败: {str(e)}")
        
        if len(result) <= 1:
            raise Exception(f"未能从企查查获取到企业信息: {company_name}")
        
        return result
    
    async def _collect_from_aiqicha(self, company_name: str, session, headers: dict) -> Dict:
        """
        从爱企查采集企业信息
        """
        search_url = f"https://aiqicha.baidu.com/s?q={quote(company_name)}"
        
        async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise Exception(f"爱企查请求失败: {resp.status}")
            
            html = await resp.text()
            return self._parse_aiqicha_html(html, company_name)
    
    def _parse_aiqicha_html(self, html: str, company_name: str) -> Dict:
        """
        解析爱企查HTML页面
        """
        result = {'name': company_name}
        
        try:
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    company_list = data.get('result', {}).get('resultList', [])
                    if company_list:
                        company = company_list[0]
                        result.update({
                            'name': company.get('entName', company_name),
                            'creditCode': company.get('creditCode'),
                            'legalPersonName': company.get('legalPerson'),
                            'regCapital': company.get('regCap'),
                            'estiblishTime': company.get('openTime'),
                            'regStatus': company.get('entStatus'),
                            'regLocation': company.get('opLoc'),
                            'businessScope': company.get('opScope'),
                            'industry': company.get('industry'),
                            'province': company.get('province'),
                            'city': company.get('city'),
                        })
                        if len(result) > 1:
                            return result
                except json.JSONDecodeError:
                    pass
            
            credit_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', html)
            if credit_match:
                result['creditCode'] = credit_match.group(1)
            
            legal_match = re.search(r'法定代表人[：:]\s*<[^>]*>([^<]+)</', html)
            if legal_match:
                result['legalPersonName'] = legal_match.group(1).strip()
            
            capital_match = re.search(r'注册资本[：:]\s*([0-9.]+[万亿]?元?)', html)
            if capital_match:
                result['regCapital'] = capital_match.group(1)
            
            date_match = re.search(r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})', html)
            if date_match:
                result['estiblishTime'] = date_match.group(1)
            
            address_match = re.search(r'注册地址[：:]\s*([^<\n]+)', html)
            if address_match:
                result['regLocation'] = address_match.group(1).strip()
            
            scope_match = re.search(r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)', html)
            if scope_match:
                result['businessScope'] = scope_match.group(1).strip()
            
            status_match = re.search(r'经营状态[：:]\s*([^<\n]+)', html)
            if status_match:
                result['regStatus'] = status_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"解析爱企查HTML失败: {str(e)}")
        
        if len(result) <= 1:
            raise Exception(f"未能从爱企查获取到企业信息: {company_name}")
        
        return result
    
    async def _collect_from_gsxt(self, company_name: str, session, headers: dict) -> Dict:
        """
        从国家企业信用信息公示系统采集
        """
        search_url = "https://www.gsxt.gov.cn/corp-query-search-1.html"
        params = {'searchword': company_name}
        
        async with session.get(search_url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise Exception(f"公示系统请求失败: {resp.status}")
            
            html = await resp.text()
            return self._parse_gsxt_html(html, company_name)
    
    def _parse_gsxt_html(self, html: str, company_name: str) -> Dict:
        """
        解析国家企业信用信息公示系统HTML
        """
        result = {'name': company_name}
        
        credit_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', html)
        if credit_match:
            result['creditCode'] = credit_match.group(1)
        
        legal_match = re.search(r'法定代表人[：:]\s*([^\s<]+)', html)
        if legal_match:
            result['legalPersonName'] = legal_match.group(1).strip()
        
        capital_match = re.search(r'注册资本[：:]\s*([0-9.]+[万亿]?元?)', html)
        if capital_match:
            result['regCapital'] = capital_match.group(1)
        
        date_match = re.search(r'成立日期[：:]\s*(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})', html)
        if date_match:
            result['estiblishTime'] = date_match.group(1)
        
        address_match = re.search(r'住所[：:]\s*([^<\n]+)', html)
        if address_match:
            result['regLocation'] = address_match.group(1).strip()
        
        scope_match = re.search(r'经营范围[：:]\s*([^<\n]+(?:\n[^<\n]+)*)', html)
        if scope_match:
            result['businessScope'] = scope_match.group(1).strip()
        
        if len(result) <= 1:
            raise Exception(f"未能从公示系统获取到企业信息: {company_name}")
        
        return result
    
    def _get_source_order(self, source: str) -> List[str]:
        """
        获取数据源尝试顺序
        """
        all_sources = ['tianyancha', 'qichacha', 'aiqicha', 'gsxt']
        
        if source != 'auto':
            other_sources = [s for s in all_sources if s != source]
            return [source] + other_sources
        
        return all_sources
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间
        """
        base_delay = RetryConfig.RETRY_DELAY_BASE ** attempt
        jitter = random.uniform(0, 1)
        delay = min(base_delay + jitter, RetryConfig.RETRY_DELAY_MAX)
        return delay
    
    def _get_random_headers(self) -> Dict:
        """
        获取随机请求头
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
    
    def _normalize_data(self, data: Dict, source: str) -> Dict:
        """
        标准化数据字段名
        """
        normalized = {'source': source}
        
        for target_field, source_field in self.FIELD_MAPPING.items():
            value = data.get(source_field)
            if value is not None:
                normalized[target_field] = value
        
        if 'estiblishTime' in data:
            normalized['establishment_date'] = self._parse_date(data['estiblishTime'])
        
        if 'regCapital' in data:
            normalized['registered_capital'] = self._parse_capital(data['regCapital'])
        
        return normalized
    
    def _parse_date(self, date_str: Any) -> str:
        """
        解析日期字符串
        """
        if not date_str:
            return None
        
        if isinstance(date_str, (int, float)):
            try:
                dt = datetime.fromtimestamp(date_str / 1000)
                return dt.strftime('%Y-%m-%d')
            except (ValueError, OSError, OverflowError):
                return None
        
        date_str = str(date_str).strip()
        
        match = re.search(r'(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})', date_str)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        
        match = re.search(r'(\d{4})[-年/](\d{1,2})', date_str)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-01"
        
        return date_str[:10] if len(date_str) >= 10 else None
    
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
