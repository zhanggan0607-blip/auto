"""
投标Agent基类
为所有投标相关Agent提供基础功能
"""
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

from openclaw.base_agent import BaseAgent, AgentType, AgentStatus, TaskResult, AgentContext
from services.unified_llm_service import unified_llm_service


logger = logging.getLogger(__name__)


@dataclass
class BidAgentContext(AgentContext):
    """
    投标Agent上下文
    """
    tender_id: int = None
    tender_title: str = None
    tender_data: Dict[str, Any] = field(default_factory=dict)
    enterprise_data: Dict[str, Any] = field(default_factory=dict)
    match_result: Dict[str, Any] = field(default_factory=dict)
    bid_documents: List[Dict[str, Any]] = field(default_factory=list)
    review_results: List[Dict[str, Any]] = field(default_factory=list)
    workflow_id: int = None


class BaseBidAgent(BaseAgent, ABC):
    """
    投标Agent基类
    """

    def __init__(self, agent_id: str = None, session_id: str = None):
        super().__init__(agent_id, session_id)
        self.llm_service = unified_llm_service
        self._agent_type_config = None

    def _setup(self):
        """
        初始化设置
        """
        self._load_agent_config()

    def _load_agent_config(self):
        """
        加载Agent配置
        """
        from apps.openclaw.models import AgentModelConfig

        agent_type_value = self.agent_type.value if self.agent_type else None

        if agent_type_value:
            try:
                self._agent_type_config = AgentModelConfig.objects.filter(
                    agent_type=agent_type_value,
                    is_active=True
                ).first()
            except Exception as e:
                logger.warning(f"加载Agent配置失败: {str(e)}")

    async def llm_chat(
        self,
        message: str,
        system_prompt: str = None,
        history: List[Dict] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        调用LLM进行对话
        """
        agent_type = self.agent_type.value if self.agent_type else None

        result = await self.llm_service.chat(
            message=message,
            agent_type=agent_type,
            system_prompt=system_prompt,
            history=history,
            temperature=temperature or (self._agent_type_config.temperature if self._agent_type_config else 0.7),
            max_tokens=max_tokens or (self._agent_type_config.max_tokens if self._agent_type_config else 4096),
            session_id=self.session_id
        )

        self.context.add_message('assistant', message, {'model': result.get('model')})

        return result

    async def llm_reasoning(
        self,
        question: str,
        context: str = None
    ) -> Dict[str, Any]:
        """
        调用LLM进行推理
        """
        agent_type = self.agent_type.value if self.agent_type else None

        return await self.llm_service.reasoning(
            question=question,
            context=context,
            agent_type=agent_type,
            session_id=self.session_id
        )

    def save_to_workflow_context(self, key: str, value: Any):
        """
        保存到工作流上下文
        """
        if 'workflow_data' not in self.context.memory:
            self.context.memory['workflow_data'] = {}
        self.context.memory['workflow_data'][key] = value

    def get_from_workflow_context(self, key: str, default: Any = None) -> Any:
        """
        从工作流上下文获取
        """
        workflow_data = self.context.memory.get('workflow_data', {})
        return workflow_data.get(key, default)

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行任务（抽象方法）
        """
        pass


class BidCollectorAgent(BaseBidAgent):
    """
    信息收集Agent
    负责收集招标项目详细信息
    """
    agent_type = AgentType.COLLECTOR

    SYSTEM_PROMPT = """你是一个专业的招标信息收集专家。你的任务是：
1. 收集招标项目的详细信息（项目背景、技术要求、资质要求等）
2. 分析招标文件的各项条款
3. 识别关键信息和潜在风险
4. 整理结构化的项目信息

请以JSON格式输出收集到的信息，包含以下字段：
- project_background: 项目背景
- technical_requirements: 技术要求
- qualification_requirements: 资质要求
- budget_info: 预算信息
- timeline: 时间安排
- risk_factors: 风险因素
- key_points: 关键要点"""

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行信息收集任务
        """
        tender_id = task.get('tender_id')
        tender_title = task.get('tender_title')
        source_url = task.get('source_url')

        try:
            self.update_context('tender_id', tender_id)
            self.update_context('tender_title', tender_title)

            tender_data = await self._collect_tender_info(tender_id, source_url)

            self.update_context('tender_data', tender_data)

            self.context.add_message('system', self.SYSTEM_PROMPT)

            result = await self._analyze_with_llm(tender_data)

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_id,
                    'tender_title': tender_title,
                    'collected_info': tender_data,
                    'analysis': result
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"信息收集失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _collect_tender_info(self, tender_id: int, source_url: str) -> Dict[str, Any]:
        """
        收集招标信息
        """
        tender_data = {}

        if tender_id:
            from apps.tenders.models import TenderProject, TenderFile

            try:
                tender = TenderProject.objects.get(id=tender_id)
                tender_data = {
                    'title': tender.title,
                    'project_code': tender.project_code,
                    'region': tender.region,
                    'industry': tender.industry,
                    'category': tender.category,
                    'budget': str(tender.budget) if tender.budget else None,
                    'description': tender.description,
                    'requirements': tender.requirements,
                    'publish_date': str(tender.publish_date) if tender.publish_date else None,
                    'deadline_date': str(tender.deadline_date) if tender.deadline_date else None,
                    'open_date': str(tender.open_date) if tender.open_date else None,
                    'purchaser_name': tender.purchaser_name,
                    'purchaser_contact': tender.purchaser_contact,
                    'purchaser_phone': tender.purchaser_phone,
                    'agency_name': tender.agency_name,
                    'agency_contact': tender.agency_contact,
                    'agency_phone': tender.agency_phone,
                }

                files = TenderFile.objects.filter(tender=tender)
                tender_data['files'] = [
                    {'file_name': f.file_name, 'file_type': f.file_type}
                    for f in files
                ]
            except TenderProject.DoesNotExist:
                logger.warning(f"招标项目不存在: {tender_id}")

        if source_url and not tender_data:
            tender_data['source_url'] = source_url

        return tender_data

    async def _analyze_with_llm(self, tender_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM分析招标信息
        """
        message = f"""请分析以下招标项目信息，提取关键内容：

项目名称：{tender_data.get('title')}
项目编号：{tender_data.get('project_code')}
预算金额：{tender_data.get('budget')}
项目描述：{tender_data.get('description')}
技术要求：{tender_data.get('requirements')}
地区：{tender_data.get('region')}
行业：{tender_data.get('industry')}"""

        result = await self.llm_chat(
            message=message,
            system_prompt=self.SYSTEM_PROMPT
        )

        try:
            import json
            content = result.get('content', '')

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            analysis = json.loads(content.strip())
            return analysis
        except:
            return {'raw_analysis': result.get('content', '')}


class BidMatcherAgent(BaseBidAgent):
    """
    企业比对Agent
    负责将招标项目与企业资料库进行匹配
    """
    agent_type = AgentType.PARSER

    SYSTEM_PROMPT = """你是一个专业的企业资质匹配专家。你的任务是：
1. 分析招标项目的资质要求
2. 将企业资料与招标要求进行比对
3. 评估匹配度并给出理由
4. 识别匹配和不匹配的点

请以JSON格式输出匹配结果，包含以下字段：
- match_score: 匹配得分(0-1)
- match_level: 匹配等级(high/medium/low)
- matched_points: 匹配的要点列表
- unmatched_points: 不匹配的要点列表
- recommendations: 建议"""

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行企业比对任务
        """
        tender_data = task.get('tender_data', {})
        enterprise_id = task.get('enterprise_id')

        try:
            enterprise_data = await self._get_enterprise_data(enterprise_id)

            match_result = await self._perform_matching(tender_data, enterprise_data)

            self.update_context('enterprise_data', enterprise_data)
            self.update_context('match_result', match_result)

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_data.get('id'),
                    'enterprise_id': enterprise_id,
                    'enterprise_data': enterprise_data,
                    'match_result': match_result
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"企业匹配失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _get_enterprise_data(self, enterprise_id: int = None) -> Dict[str, Any]:
        """
        获取企业数据
        """
        from apps.enterprise.models import Enterprise, EnterpriseQualification, EnterprisePerformance

        enterprise_data = {}

        if enterprise_id:
            try:
                enterprise = Enterprise.objects.get(id=enterprise_id)
                enterprise_data = {
                    'id': enterprise.id,
                    'name': enterprise.name,
                    'short_name': enterprise.short_name,
                    'credit_code': enterprise.credit_code,
                    'province': enterprise.province,
                    'city': enterprise.city,
                    'industry': enterprise.industry,
                    'business_scope': enterprise.business_scope,
                }

                qualifications = EnterpriseQualification.objects.filter(
                    enterprise=enterprise,
                    is_valid=True
                )
                enterprise_data['qualifications'] = [
                    {
                        'name': q.qualification_name,
                        'category': q.qualification_category,
                        'grade': q.grade,
                        'scope': q.scope,
                        'expiry_date': str(q.expiry_date) if q.expiry_date else None
                    }
                    for q in qualifications
                ]

                performances = EnterprisePerformance.objects.filter(
                    enterprise=enterprise
                )[:10]
                enterprise_data['performances'] = [
                    {
                        'name': p.project_name,
                        'type': p.performance_type,
                        'amount': str(p.contract_amount) if p.contract_amount else None,
                        'date': str(p.end_date) if p.end_date else None
                    }
                    for p in performances
                ]

            except Enterprise.DoesNotExist:
                logger.warning(f"企业不存在: {enterprise_id}")

        return enterprise_data

    async def _perform_matching(
        self,
        tender_data: Dict[str, Any],
        enterprise_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行匹配
        """
        from services.enterprise_matching_engine import enterprise_matching_engine

        match_result = {
            'tender': tender_data,
            'enterprise': enterprise_data,
            'manual_review': True
        }

        try:
            tender_for_matching = {
                'title': tender_data.get('title'),
                'description': tender_data.get('description'),
                'requirements': tender_data.get('requirements'),
                'budget': tender_data.get('budget'),
                'region': tender_data.get('region'),
                'industry': tender_data.get('industry')
            }

            results = enterprise_matching_engine.match_tender(
                tender_data=tender_for_matching,
                top_k=1
            )

            if results:
                match_result['match_score'] = results[0].match_score
                match_result['match_level'] = results[0].match_level
                match_result['matched_reasons'] = results[0].matched_reasons
            else:
                match_result['match_score'] = 0
                match_result['match_level'] = 'low'
                match_result['matched_reasons'] = []

        except Exception as e:
            logger.warning(f"向量匹配失败，使用LLM分析: {str(e)}")

        llm_analysis = await self._llm_matching_analysis(tender_data, enterprise_data)
        match_result.update(llm_analysis)

        return match_result

    async def _llm_matching_analysis(
        self,
        tender_data: Dict[str, Any],
        enterprise_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用LLM进行匹配分析
        """
        message = f"""请分析以下企业是否符合招标项目要求：

招标项目信息：
- 项目名称：{tender_data.get('title')}
- 项目预算：{tender_data.get('budget')}
- 技术要求：{tender_data.get('requirements')}
- 地区：{tender_data.get('region')}
- 行业：{tender_data.get('industry')}

企业信息：
- 企业名称：{enterprise_data.get('name')}
- 经营范围：{enterprise_data.get('business_scope')}
- 行业：{enterprise_data.get('industry')}
- 资质列表：{enterprise_data.get('qualifications', [])}
- 业绩列表：{enterprise_data.get('performances', [])}

请给出匹配得分(0-100)和详细的匹配分析。"""

        result = await self.llm_chat(
            message=message,
            system_prompt=self.SYSTEM_PROMPT
        )

        content = result.get('content', '')

        return {
            'llm_analysis': content,
            'match_reasoning': True
        }


class BidAnalystAgent(BaseBidAgent):
    """
    投标论证Agent
    负责分析是否应该参与投标
    """
    agent_type = AgentType.GENERATOR

    SYSTEM_PROMPT = """你是一个专业的招投标分析专家。你的任务是：
1. 分析招标项目的可行性和风险
2. 评估企业参与投标的优势和劣势
3. 给出是否参与投标的建议
4. 制定投标策略

请以JSON格式输出分析结果，包含以下字段：
- recommendation: 建议(participate/skip/pending)
- recommendation_score: 推荐分数(0-100)
- strengths: 优势分析
- weaknesses: 劣势分析
- risks: 风险因素
- opportunities: 机会因素
- strategy: 投标策略建议
- reasoning: 推理过程"""

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行投标论证任务
        """
        tender_data = task.get('tender_data', {})
        enterprise_data = task.get('enterprise_data', {})
        match_result = task.get('match_result', {})

        try:
            analysis = await self._analyze_bid_opportunity(
                tender_data,
                enterprise_data,
                match_result
            )

            recommendation = analysis.get('recommendation', 'pending')
            score = analysis.get('recommendation_score', 0)

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_data.get('id'),
                    'analysis': analysis,
                    'recommendation': recommendation,
                    'recommendation_score': score,
                    'decision': 'proceed' if recommendation == 'participate' and score >= 60 else 'review'
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"投标论证失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _analyze_bid_opportunity(
        self,
        tender_data: Dict[str, Any],
        enterprise_data: Dict[str, Any],
        match_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析投标机会
        """
        match_score = match_result.get('match_score', 0)

        context = f"""
招标项目：{tender_data.get('title')}
预算金额：{tender_data.get('budget')}
匹配得分：{match_score}

企业资质：{enterprise_data.get('qualifications', [])}
企业业绩：{enterprise_data.get('performances', [])}
"""

        question = """请分析企业是否应该参与此项目的投标，给出：
1. 详细的推理过程
2. 推荐分数(0-100)
3. 最终建议(参与/放弃/待定)
4. 投标策略"""

        result = await self.llm_reasoning(question, context)

        try:
            import json
            content = result.get('content', '')

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            analysis = json.loads(content.strip())
            return analysis
        except:
            return {
                'recommendation': 'pending',
                'recommendation_score': 50,
                'raw_analysis': result.get('content', ''),
                'reasoning': '基于LLM分析结果'
            }
