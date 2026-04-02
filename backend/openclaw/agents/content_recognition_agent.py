"""
内容识别Agent
负责对爬取获取的各类数据进行精准识别与结构化处理
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from asgiref.sync import sync_to_async

from openclaw.base_agent import BaseAgent, AgentType, AgentCapability, TaskResult
from core.constants import (
    SOURCE_TYPE_CHOICES,
    FILE_TYPE_CHOICES,
    PROJECT_TYPE_CHOICES,
)


logger = logging.getLogger(__name__)


class ContentRecognitionAgent(BaseAgent):
    """
    内容识别Agent
    对爬取内容进行多维度分析，提取关键业务数据
    按照预设的数据模型进行标准化整理与存储
    """

    agent_type = AgentType.PARSER
    capabilities = [
        AgentCapability.PARSING,
        AgentCapability.ANALYZING,
    ]
    default_tools = ['llm_chat', 'execute_code']

    SYSTEM_PROMPT = """你是一个专业的内容识别专家。你的任务是：
1. 对爬取的网页内容进行精准识别和解析
2. 提取关键业务数据（企业信息、产品信息、财务指标、资质要求等）
3. 按照预设的数据模型进行标准化整理
4. 进行数据质量校验，确保数据准确性

支持识别的数据类型：
- 招标公告：标题、编号、采购人、代理机构、预算金额、截止日期等
- 企业信息：企业名称、信用代码、法人代表、注册资本等
- 资质要求：资质等级、专业类别、有效期限等
- 财务指标：预算金额、报价、保证金等

请确保提取的数据准确、完整，并标记数据质量等级。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extraction_rules = {}
        self._load_extraction_rules()

    def _load_extraction_rules(self):
        """
        加载数据提取规则
        """
        try:
            from apps.crawler.models import WebsiteTemplate
            templates = WebsiteTemplate.objects.filter(is_active=True)
            for template in templates:
                selectors = template.selectors or {}
                self._extraction_rules[template.code] = {
                    'selectors': selectors,
                    'pagination': template.pagination_config or {},
                    'request': template.request_config or {},
                }
            logger.info(f"加载了 {len(self._extraction_rules)} 个网站模板的提取规则")
        except Exception as e:
            logger.warning(f"加载提取规则失败: {str(e)}")

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行内容识别任务

        Args:
            task: {
                'content': '原始网页内容或HTML',
                'url': '来源URL',
                'source_type': 'government/enterprise/other',
                'content_type': 'tender/enterprise/document/other',
                'website_code': '网站代码',
                'raw_data': {},  # 原始爬取数据
                'save_to_db': True/False,
                'validate_quality': True/False
            }
        """
        content = task.get('content', '')
        url = task.get('url', '')
        source_type = task.get('source_type', 'other')
        content_type = task.get('content_type', 'other')
        website_code = task.get('website_code', '')
        raw_data = task.get('raw_data', {})
        save_to_db = task.get('save_to_db', True)
        validate_quality = task.get('validate_quality', True)

        if not content and not raw_data:
            return TaskResult(
                success=False,
                error='内容不能为空'
            )

        try:
            self.update_context('url', url)
            self.update_context('source_type', source_type)
            self.update_context('content_type', content_type)

            if content_type == 'tender' or source_type == 'government':
                extracted_data = await self._extract_tender_info(content, url, raw_data)
            elif content_type == 'enterprise':
                extracted_data = await self._extract_enterprise_info(content, url, raw_data)
            else:
                extracted_data = await self._extract_general_info(content, url, raw_data)

            quality_result = None
            if validate_quality:
                quality_result = self._validate_data_quality(extracted_data, content_type)
                extracted_data['_quality'] = quality_result

            structured_data = self._structure_data(extracted_data, content_type)

            record_id = None
            if save_to_db:
                record_id = await self._save_recognized_content(
                    url=url,
                    source_type=source_type,
                    content_type=content_type,
                    extracted_data=structured_data,
                    raw_data=raw_data,
                    quality_result=quality_result
                )

            self.add_memory('last_recognition', {
                'url': url,
                'content_type': content_type,
                'record_id': record_id,
                'timestamp': datetime.now().isoformat(),
                'quality': quality_result.get('grade') if quality_result else None
            })

            return TaskResult(
                success=True,
                data={
                    'url': url,
                    'content_type': content_type,
                    'extracted_data': structured_data,
                    'record_id': record_id,
                    'quality_result': quality_result
                },
                metadata={
                    'agent_id': self.agent_id,
                    'source_type': source_type,
                    'content_type': content_type
                }
            )

        except Exception as e:
            logger.error(f"内容识别失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e),
                metadata={'url': url, 'content_type': content_type}
            )

    async def _extract_tender_info(
        self,
        content: str,
        url: str,
        raw_data: Dict
    ) -> Dict[str, Any]:
        """
        提取招标公告信息
        """
        extracted = {}

        if raw_data:
            extracted = {
                'title': raw_data.get('title', ''),
                'project_code': raw_data.get('project_code', ''),
                'region': raw_data.get('region', ''),
                'industry': raw_data.get('industry', ''),
                'category': raw_data.get('category', ''),
                'purchaser_name': raw_data.get('purchaser_name', ''),
                'purchaser_contact': raw_data.get('purchaser_contact', ''),
                'purchaser_phone': raw_data.get('purchaser_phone', ''),
                'agency_name': raw_data.get('agency_name', ''),
                'agency_contact': raw_data.get('agency_contact', ''),
                'agency_phone': raw_data.get('agency_phone', ''),
                'budget': raw_data.get('budget'),
                'publish_date': raw_data.get('publish_date'),
                'deadline_date': raw_data.get('deadline_date'),
                'description': raw_data.get('description', ''),
                'requirements': raw_data.get('requirements', ''),
            }
        else:
            extracted = await self._llm_extract_tender(content, url)

        extracted['source_url'] = url
        extracted['detail_url'] = url

        return extracted

    async def _llm_extract_tender(self, content: str, url: str) -> Dict[str, Any]:
        """
        使用LLM提取招标信息
        """
        system_prompt = """你是一个专业的招标公告信息提取专家。请从网页内容中提取以下信息：

1. title - 招标项目标题
2. project_code - 项目编号/招标编号
3. purchaser_name - 采购人/招标人名称
4. agency_name - 代理机构名称
5. budget - 预算金额（数字）
6. publish_date - 发布日期（YYYY-MM-DD格式）
7. deadline_date - 截止日期（YYYY-MM-DD格式）
8. region - 地区
9. description - 项目描述

请以JSON格式返回，字段为空或不明确时使用null。"""

        result = await self.llm_chat(
            message=f"请提取以下网页内容中的招标信息：\n\n{content[:8000]}",
            system_prompt=system_prompt
        )

        try:
            import json
            response_text = result.get('response', '')
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"LLM提取解析失败: {str(e)}")

        return {}

    async def _extract_enterprise_info(
        self,
        content: str,
        url: str,
        raw_data: Dict
    ) -> Dict[str, Any]:
        """
        提取企业信息
        """
        extracted = {}

        if raw_data:
            extracted = {
                'name': raw_data.get('name', ''),
                'short_name': raw_data.get('short_name', ''),
                'credit_code': raw_data.get('credit_code', ''),
                'legal_person': raw_data.get('legal_person', ''),
                'registered_capital': raw_data.get('registered_capital', ''),
                'establishment_date': raw_data.get('establishment_date', ''),
                'province': raw_data.get('province', ''),
                'city': raw_data.get('city', ''),
                'address': raw_data.get('address', ''),
                'business_scope': raw_data.get('business_scope', ''),
                'industry': raw_data.get('industry', ''),
                'contact_phone': raw_data.get('phone', ''),
                'website': raw_data.get('website', ''),
            }
        else:
            extracted = await self._llm_extract_enterprise(content, url)

        extracted['source_url'] = url
        return extracted

    async def _llm_extract_enterprise(self, content: str, url: str) -> Dict[str, Any]:
        """
        使用LLM提取企业信息
        """
        system_prompt = """你是一个专业的企业信息提取专家。请从网页内容中提取以下信息：

1. name - 企业全称
2. short_name - 企业简称
3. credit_code - 统一社会信用代码
4. legal_person - 法人代表
5. registered_capital - 注册资本
6. establishment_date - 成立日期
7. province - 省份
8. city - 城市
9. address - 详细地址
10. business_scope - 经营范围
11. industry - 所属行业
12. contact_phone - 联系电话

请以JSON格式返回，字段为空或不明确时使用null。"""

        result = await self.llm_chat(
            message=f"请提取以下网页内容中的企业信息：\n\n{content[:8000]}",
            system_prompt=system_prompt
        )

        try:
            import json
            response_text = result.get('response', '')
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"LLM提取解析失败: {str(e)}")

        return {}

    async def _extract_general_info(
        self,
        content: str,
        url: str,
        raw_data: Dict
    ) -> Dict[str, Any]:
        """
        提取通用信息
        """
        extracted = raw_data.copy() if raw_data else {}
        extracted['source_url'] = url

        if content and not raw_data:
            extracted = await self._llm_extract_general(content, url)

        return extracted

    async def _llm_extract_general(self, content: str, url: str) -> Dict[str, Any]:
        """
        使用LLM提取通用信息
        """
        system_prompt = """你是一个专业的内容提取专家。请分析以下网页内容，提取所有有价值的信息。

请以JSON格式返回，字段名使用英文，值可以是字符串、数字或null。

格式示例：
{
    "title": "页面标题",
    "main_content": "主要内容摘要",
    "key_value_pairs": {"关键信息": "对应值"},
    "dates": ["提到的日期列表"],
    "amounts": ["提到的金额列表"],
    "organizations": ["提到的主体名称列表"]
}"""

        result = await self.llm_chat(
            message=f"请提取以下网页内容中的信息：\n\n{content[:8000]}",
            system_prompt=system_prompt
        )

        try:
            import json
            response_text = result.get('response', '')
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"LLM提取解析失败: {str(e)}")

        return {'title': content[:200], 'main_content': content[:2000]}

    def _validate_data_quality(
        self,
        data: Dict[str, Any],
        content_type: str
    ) -> Dict[str, Any]:
        """
        校验数据质量
        """
        quality_score = 0
        issues = []
        warnings = []

        required_fields = {
            'tender': ['title', 'purchaser_name', 'budget', 'deadline_date'],
            'enterprise': ['name', 'credit_code'],
            'general': ['title', 'source_url']
        }

        required = required_fields.get(content_type, required_fields['general'])

        for field in required:
            if not data.get(field):
                issues.append(f'缺少必填字段: {field}')
                quality_score -= 20
            else:
                quality_score += 10

        quality_score = max(0, min(100, quality_score))

        if data.get('budget'):
            try:
                budget = float(data.get('budget', 0))
                if budget <= 0:
                    warnings.append('预算金额异常（<=0）')
                    quality_score -= 10
                elif budget > 1000000000:
                    warnings.append('预算金额异常（过大）')
                    quality_score -= 5
            except (ValueError, TypeError):
                issues.append('预算金额格式错误')
                quality_score -= 15

        if data.get('deadline_date'):
            try:
                deadline = data.get('deadline_date')
                if isinstance(deadline, str):
                    deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
                    if deadline_date < datetime.now():
                        warnings.append('截止日期已过')
                        quality_score -= 10
            except ValueError:
                issues.append('日期格式错误')
                quality_score -= 10

        if data.get('credit_code'):
            credit_code = data.get('credit_code', '')
            if not self._validate_credit_code(credit_code):
                warnings.append('统一社会信用代码格式可能不正确')
                quality_score -= 5

        if quality_score >= 80:
            grade = 'A'
        elif quality_score >= 60:
            grade = 'B'
        elif quality_score >= 40:
            grade = 'C'
        else:
            grade = 'D'

        return {
            'score': quality_score,
            'grade': grade,
            'issues': issues,
            'warnings': warnings,
            'is_valid': len(issues) == 0
        }

    def _validate_credit_code(self, code: str) -> bool:
        """
        验证统一社会信用代码格式
        """
        if not code or len(code) != 18:
            return False

        pattern = r'^[0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10}$'
        return bool(re.match(pattern, code))

    def _structure_data(
        self,
        extracted_data: Dict[str, Any],
        content_type: str
    ) -> Dict[str, Any]:
        """
        标准化整理数据
        """
        structured = extracted_data.copy()

        if content_type == 'tender':
            if structured.get('budget'):
                try:
                    budget_str = str(structured['budget'])
                    numbers = re.findall(r'[\d,]+\.?\d*', budget_str)
                    if numbers:
                        structured['budget'] = float(numbers[0].replace(',', ''))
                except (ValueError, TypeError):
                    structured['budget'] = None

            if structured.get('publish_date'):
                structured['publish_date'] = self._normalize_date(
                    structured['publish_date']
                )

            if structured.get('deadline_date'):
                structured['deadline_date'] = self._normalize_date(
                    structured['deadline_date']
                )

        structured['_content_type'] = content_type
        structured['_recognized_at'] = datetime.now().isoformat()
        structured['_agent_id'] = self.agent_id

        return structured

    def _normalize_date(self, date_value: Any) -> Optional[str]:
        """
        标准化日期格式
        """
        if not date_value:
            return None

        if isinstance(date_value, str):
            patterns = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
                '%Y-%m-%d %H:%M:%S',
            ]
            for pattern in patterns:
                try:
                    dt = datetime.strptime(date_value[:19], pattern)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', date_value)
            if date_match:
                year, month, day = date_match.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"

        return str(date_value)

    @sync_to_async
    def _save_recognized_content(
        self,
        url: str,
        source_type: str,
        content_type: str,
        extracted_data: Dict[str, Any],
        raw_data: Dict,
        quality_result: Dict[str, Any] = None
    ) -> int:
        """
        保存识别结果到数据库
        """
        from apps.crawler.models import CrawlResult
        from apps.tenders.models import TenderProject, TenderSource
        from django.utils import timezone

        try:
            if content_type == 'tender':
                source_code = self._extract_source_code(url)

                source, _ = TenderSource.objects.get_or_create(
                    code=source_code,
                    defaults={
                        'name': source_code,
                        'source_type': source_type,
                        'base_url': self._extract_base_url(url),
                        'is_active': True,
                    }
                )

                tender, created = TenderProject.objects.update_or_create(
                    source_url=url,
                    defaults={
                        'title': extracted_data.get('title', ''),
                        'project_code': extracted_data.get('project_code', ''),
                        'source': source,
                        'publish_date': extracted_data.get('publish_date'),
                        'deadline_date': extracted_data.get('deadline_date'),
                        'region': extracted_data.get('region', ''),
                        'industry': extracted_data.get('industry', ''),
                        'category': extracted_data.get('category', ''),
                        'purchaser_name': extracted_data.get('purchaser_name', ''),
                        'purchaser_contact': extracted_data.get('purchaser_contact', ''),
                        'purchaser_phone': extracted_data.get('purchaser_phone', ''),
                        'agency_name': extracted_data.get('agency_name', ''),
                        'agency_contact': extracted_data.get('agency_contact', ''),
                        'agency_phone': extracted_data.get('agency_phone', ''),
                        'budget': extracted_data.get('budget'),
                        'description': extracted_data.get('description', ''),
                        'requirements': extracted_data.get('requirements', ''),
                        'status': 'pending',
                        'raw_data': {
                            'recognized_data': extracted_data,
                            'raw_data': raw_data,
                            'quality': quality_result,
                        },
                    }
                )

                return tender.id

            return None

        except Exception as e:
            logger.error(f"保存识别结果失败: {str(e)}")
            return None

    def _extract_source_code(self, url: str) -> str:
        """
        从URL提取数据源代码
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.netloc.lower()

            source_mapping = {
                'ccgp.gov.cn': 'china_gov',
                'zfcg.sh.gov.cn': 'shanghai_gov',
                'zbtb.cn': 'zbtb',
                'ctex.cn': 'ctex',
            }

            for domain, code in source_mapping.items():
                if domain in host:
                    return code

            return host.replace('.', '_')
        except Exception:
            return 'unknown'

    def _extract_base_url(self, url: str) -> str:
        """
        从URL提取基础URL
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return url


class BatchContentRecognitionAgent(BaseAgent):
    """
    批量内容识别Agent
    批量处理多个内容识别任务
    """

    agent_type = AgentType.PARSER
    capabilities = [
        AgentCapability.PARSING,
        AgentCapability.ORCHESTRATING,
    ]

    SYSTEM_PROMPT = """你是一个批量内容识别专家。你的任务是：
1. 接收多个内容的识别任务
2. 并发调用ContentRecognitionAgent进行识别
3. 汇总识别结果
4. 处理识别失败的条目
5. 生成批量识别报告"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._child_agents: Dict[str, ContentRecognitionAgent] = {}

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行批量识别任务

        Args:
            task: {
                'items': [
                    {
                        'content': '内容',
                        'url': 'URL',
                        'source_type': '类型',
                        'content_type': '内容类型',
                        ...
                    },
                    ...
                ],
                'max_concurrent': 5,
                'save_to_db': True,
                'validate_quality': True
            }
        """
        items = task.get('items', [])
        max_concurrent = task.get('max_concurrent', 5)
        save_to_db = task.get('save_to_db', True)
        validate_quality = task.get('validate_quality', True)

        if not items:
            return TaskResult(
                success=False,
                error='识别项目列表不能为空'
            )

        try:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def recognize_with_limit(item: Dict, index: int) -> Dict:
                async with semaphore:
                    agent = ContentRecognitionAgent(session_id=self.session_id)
                    result = await agent.run({
                        **item,
                        'save_to_db': save_to_db,
                        'validate_quality': validate_quality
                    })
                    return {
                        'index': index,
                        'url': item.get('url', ''),
                        'success': result.success,
                        'data': result.data if result.success else None,
                        'error': result.error if not result.success else None
                    }

            tasks = [recognize_with_limit(item, i) for i, item in enumerate(items)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = 0
            failed_count = 0
            recognized_items = []
            errors = []

            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    errors.append(str(result))
                elif result.get('success'):
                    success_count += 1
                    recognized_items.append(result)
                else:
                    failed_count += 1
                    errors.append(result.get('error'))

            quality_stats = self._calc_quality_stats(recognized_items)

            return TaskResult(
                success=True,
                data={
                    'total': len(items),
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'recognized_items': recognized_items,
                    'quality_stats': quality_stats,
                    'errors': errors[:10]
                },
                metadata={
                    'agent_id': self.agent_id,
                    'total_items': len(items)
                }
            )

        except Exception as e:
            logger.error(f"批量识别失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e)
            )

    def _calc_quality_stats(self, recognized_items: List[Dict]) -> Dict:
        """
        计算质量统计
        """
        if not recognized_items:
            return {'avg_score': 0, 'grade_distribution': {}}

        scores = []
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

        for item in recognized_items:
            data = item.get('data', {})
            quality = data.get('quality_result')
            if quality:
                scores.append(quality.get('score', 0))
                grade = quality.get('grade', 'D')
                grade_counts[grade] = grade_counts.get(grade, 0) + 1

        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            'avg_score': round(avg_score, 2),
            'grade_distribution': grade_counts,
            'total_with_quality': len(scores)
        }
