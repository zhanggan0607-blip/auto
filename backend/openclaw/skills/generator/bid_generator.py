"""
投标文件生成技能
使用本地大模型生成投标文件内容
"""
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from openclaw.skill_registry import Skill, SkillMetadata, SkillResult


logger = logging.getLogger(__name__)


class BidDocumentGeneratorSkill(Skill):
    """
    投标文件生成技能
    根据招标要求和模板生成投标文件
    """
    
    metadata = SkillMetadata(
        name='bid_document_generator',
        description='根据招标文件要求生成投标文件',
        version='1.0.0',
        author='OpenClaw',
        category='generator',
        tags=['bid', 'document', 'generator', 'llm'],
        input_schema={
            'type': 'object',
            'properties': {
                'tender_info': {
                    'type': 'object',
                    'description': '招标项目信息'
                },
                'template_id': {
                    'type': 'integer',
                    'description': '模板ID'
                },
                'enterprise_info': {
                    'type': 'object',
                    'description': '企业信息'
                },
                'sections': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '需要生成的章节'
                }
            },
            'required': ['tender_info']
        }
    )
    
    def __init__(self):
        super().__init__()
        self._llm_client = None
    
    def _get_llm_client(self):
        """
        获取LLM客户端（使用统一LLM服务）
        """
        if self._llm_client is None:
            from services.unified_llm_service import unified_llm_service
            self._llm_client = unified_llm_service
        return self._llm_client
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行投标文件生成
        """
        tender_info = kwargs.get('tender_info', {})
        template_id = kwargs.get('template_id')
        enterprise_info = kwargs.get('enterprise_info', {})
        sections = kwargs.get('sections', [
            'technical_proposal',
            'business_proposal',
            'qualification',
            'service_plan'
        ])
        
        try:
            generated_sections = {}
            
            for section in sections:
                section_content = await self._generate_section(
                    section, tender_info, enterprise_info
                )
                generated_sections[section] = section_content
            
            if template_id:
                document_path = await self._apply_template(
                    template_id, generated_sections, tender_info
                )
            else:
                document_path = None
            
            return SkillResult(
                success=True,
                data={
                    'sections': generated_sections,
                    'document_path': document_path
                },
                metadata={
                    'sections_generated': list(generated_sections.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Bid document generation failed: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _generate_section(
        self,
        section: str,
        tender_info: Dict,
        enterprise_info: Dict
    ) -> str:
        """
        生成单个章节
        """
        llm = self._get_llm_client()
        
        section_prompts = {
            'technical_proposal': self._get_technical_proposal_prompt,
            'business_proposal': self._get_business_proposal_prompt,
            'qualification': self._get_qualification_prompt,
            'service_plan': self._get_service_plan_prompt
        }
        
        prompt_func = section_prompts.get(section)
        if not prompt_func:
            return ''
        
        prompt = prompt_func(tender_info, enterprise_info)
        result = await llm.chat(message=prompt)
        
        return result.get('content', '')
    
    def _get_technical_proposal_prompt(
        self,
        tender_info: Dict,
        enterprise_info: Dict
    ) -> str:
        """
        技术方案提示词
        """
        return f"""请根据以下招标要求和企业信息，撰写技术方案章节。

招标项目信息：
{json.dumps(tender_info, ensure_ascii=False, indent=2)}

企业信息：
{json.dumps(enterprise_info, ensure_ascii=False, indent=2)}

要求：
1. 技术方案应针对招标项目的具体需求
2. 突出企业的技术优势和解决方案
3. 包含技术实现方案、技术路线、关键技术等内容
4. 语言专业、条理清晰

请直接输出技术方案内容，不要添加标题。"""
    
    def _get_business_proposal_prompt(
        self,
        tender_info: Dict,
        enterprise_info: Dict
    ) -> str:
        """
        商务方案提示词
        """
        return f"""请根据以下招标要求和企业信息，撰写商务方案章节。

招标项目信息：
{json.dumps(tender_info, ensure_ascii=False, indent=2)}

企业信息：
{json.dumps(enterprise_info, ensure_ascii=False, indent=2)}

要求：
1. 商务方案应包含报价依据、成本分析等
2. 说明价格构成的合理性
3. 提供优惠条件和增值服务
4. 语言专业、条理清晰

请直接输出商务方案内容，不要添加标题。"""
    
    def _get_qualification_prompt(
        self,
        tender_info: Dict,
        enterprise_info: Dict
    ) -> str:
        """
        资质证明提示词
        """
        return f"""请根据以下招标要求和企业信息，整理资质证明章节内容。

招标项目信息：
{json.dumps(tender_info, ensure_ascii=False, indent=2)}

企业信息：
{json.dumps(enterprise_info, ensure_ascii=False, indent=2)}

要求：
1. 列出企业相关资质证书
2. 说明资质与项目要求的对应关系
3. 突出核心资质和荣誉
4. 语言专业、条理清晰

请直接输出资质证明内容，不要添加标题。"""
    
    def _get_service_plan_prompt(
        self,
        tender_info: Dict,
        enterprise_info: Dict
    ) -> str:
        """
        服务方案提示词
        """
        return f"""请根据以下招标要求和企业信息，撰写服务方案章节。

招标项目信息：
{json.dumps(tender_info, ensure_ascii=False, indent=2)}

企业信息：
{json.dumps(enterprise_info, ensure_ascii=False, indent=2)}

要求：
1. 服务方案应包含服务承诺、服务流程、服务保障等
2. 针对项目特点提供定制化服务方案
3. 包含应急预案和售后保障
4. 语言专业、条理清晰

请直接输出服务方案内容，不要添加标题。"""
    
    async def _apply_template(
        self,
        template_id: int,
        sections: Dict[str, str],
        tender_info: Dict
    ) -> str:
        """
        应用模板生成文档
        """
        from services.document_generator import DocumentGenerator
        from apps.documents.models import DocumentTemplate
        from apps.tenders.models import TenderProject
        
        try:
            template = DocumentTemplate.objects.get(pk=template_id)
            tender = TenderProject.objects.get(pk=tender_info.get('id'))
            
            generator = DocumentGenerator()
            result = generator.generate(
                template=template,
                tender=tender,
                variables=sections
            )
            
            return result.get('docx_path')
            
        except Exception as e:
            logger.error(f"Template application failed: {str(e)}")
            return None


class TechnicalProposalSkill(Skill):
    """
    技术方案生成技能
    """
    
    metadata = SkillMetadata(
        name='technical_proposal_generator',
        description='生成技术方案',
        version='1.0.0',
        author='OpenClaw',
        category='generator',
        tags=['technical', 'proposal', 'generator'],
        input_schema={
            'type': 'object',
            'properties': {
                'requirements': {
                    'type': 'string',
                    'description': '技术需求描述'
                },
                'enterprise_capabilities': {
                    'type': 'object',
                    'description': '企业技术能力'
                }
            },
            'required': ['requirements']
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行技术方案生成
        """
        requirements = kwargs.get('requirements')
        enterprise_capabilities = kwargs.get('enterprise_capabilities', {})
        
        try:
            from services.unified_llm_service import unified_llm_service
            
            prompt = f"""请根据以下技术需求，撰写一份专业的技术方案。

技术需求：
{requirements}

企业技术能力：
{json.dumps(enterprise_capabilities, ensure_ascii=False, indent=2)}

要求：
1. 方案应具有针对性和可行性
2. 包含技术架构、实现方案、关键技术等
3. 突出技术优势和创新点
4. 语言专业、结构清晰

请输出完整的技术方案。"""

            result = await unified_llm_service.chat(message=prompt)
            
            return SkillResult(
                success=True,
                data={'content': result.get('content', '')},
                metadata={'timestamp': datetime.now().isoformat()}
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )


class BidPriceCalculatorSkill(Skill):
    """
    投标报价计算技能
    """
    
    metadata = SkillMetadata(
        name='bid_price_calculator',
        description='计算投标报价',
        version='1.0.0',
        author='OpenClaw',
        category='generator',
        tags=['price', 'calculator', 'bid'],
        input_schema={
            'type': 'object',
            'properties': {
                'budget': {
                    'type': 'number',
                    'description': '项目预算'
                },
                'cost_items': {
                    'type': 'array',
                    'description': '成本项列表'
                },
                'profit_margin': {
                    'type': 'number',
                    'description': '预期利润率'
                },
                'strategy': {
                    'type': 'string',
                    'enum': ['competitive', 'balanced', 'premium'],
                    'description': '报价策略'
                }
            }
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行报价计算
        """
        budget = kwargs.get('budget', 0)
        cost_items = kwargs.get('cost_items', [])
        profit_margin = kwargs.get('profit_margin', 0.1)
        strategy = kwargs.get('strategy', 'balanced')
        
        try:
            total_cost = sum(item.get('amount', 0) for item in cost_items)
            
            strategy_multipliers = {
                'competitive': 0.85,
                'balanced': 1.0,
                'premium': 1.15
            }
            
            multiplier = strategy_multipliers.get(strategy, 1.0)
            
            base_price = total_cost * (1 + profit_margin)
            final_price = base_price * multiplier
            
            if budget > 0 and final_price > budget:
                final_price = budget * 0.95
            
            breakdown = {
                'total_cost': total_cost,
                'profit_margin': profit_margin,
                'base_price': base_price,
                'strategy': strategy,
                'strategy_multiplier': multiplier,
                'final_price': final_price,
                'cost_breakdown': cost_items
            }
            
            return SkillResult(
                success=True,
                data=breakdown,
                metadata={'timestamp': datetime.now().isoformat()}
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
