"""
标书制作Agent
负责生成投标文件
"""
import asyncio
import logging
from typing import Any, Dict, List
from openclaw.base_agent import AgentType, TaskResult
from openclaw.agents.bid_collector_agent import BaseBidAgent


logger = logging.getLogger(__name__)


class BidDocumentGeneratorAgent(BaseBidAgent):
    """
    标书制作Agent
    负责生成投标文件
    """
    agent_type = AgentType.GENERATOR

    SYSTEM_PROMPT = """你是一个专业的投标文件撰写专家。你的任务是：
1. 根据招标文件要求撰写投标文件
2. 确保投标文件符合招标要求
3. 突出企业优势和竞争力
4. 提供完整的技术方案和商务方案

投标文件应包含以下部分：
- 投标函
- 法定代表人授权书
- 投标报价表
- 技术方案
- 项目实施方案
- 质量保证措施
- 售后服务承诺
- 企业资质证明
- 类似业绩证明"""

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行标书制作任务
        """
        tender_data = task.get('tender_data', {})
        enterprise_data = task.get('enterprise_data', {})
        match_result = task.get('match_result', {})
        template_id = task.get('template_id')

        try:
            document_structure = await self._plan_document_structure(tender_data)

            sections = await self._generate_sections(
                tender_data,
                enterprise_data,
                match_result,
                document_structure
            )

            document = await self._assemble_document(sections, tender_data)

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_data.get('id'),
                    'document': document,
                    'sections': sections,
                    'total_sections': len(sections)
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"标书制作失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _plan_document_structure(self, tender_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划文档结构
        """
        message = f"""请根据以下招标项目要求，规划投标文件的结构：

项目名称：{tender_data.get('title')}
项目预算：{tender_data.get('budget')}
技术要求：{tender_data.get('requirements')}

请列出投标文件应该包含的所有章节和子章节，以JSON格式输出：
{{
    "sections": [
        {{"title": "章节标题", "subsections": ["子章节1", "子章节2"]}}
    ]
}}"""

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

            structure = json.loads(content.strip())
            return structure
        except:
            return {
                'sections': [
                    {'title': '投标函', 'subsections': []},
                    {'title': '法定代表人授权书', 'subsections': []},
                    {'title': '投标报价表', 'subsections': []},
                    {'title': '技术方案', 'subsections': ['技术路线', '实施方案', '质量保证']},
                    {'title': '企业资质', 'subsections': []},
                    {'title': '类似业绩', 'subsections': []}
                ]
            }

    async def _generate_sections(
        self,
        tender_data: Dict[str, Any],
        enterprise_data: Dict[str, Any],
        match_result: Dict[str, Any],
        document_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成各章节内容
        """
        sections = []

        for section_info in document_structure.get('sections', []):
            section_title = section_info.get('title')
            subsections = section_info.get('subsections', [])

            content = await self._generate_section_content(
                section_title,
                subsections,
                tender_data,
                enterprise_data
            )

            sections.append({
                'title': section_title,
                'subsections': subsections,
                'content': content
            })

        return sections

    async def _generate_section_content(
        self,
        section_title: str,
        subsections: List[str],
        tender_data: Dict[str, Any],
        enterprise_data: Dict[str, Any]
    ) -> str:
        """
        生成章节内容
        """
        enterprise_name = enterprise_data.get('name', '本公司')
        tender_title = tender_data.get('title', '本项目')
        budget = tender_data.get('budget', '待定')

        if section_title == '投标函':
            return self._generate_bid_letter(tender_title, enterprise_name, budget)

        elif section_title == '法定代表人授权书':
            return self._generate_authorization(enterprise_name)

        elif section_title == '投标报价表':
            return await self._generate_price_table(tender_data, enterprise_data)

        elif section_title == '技术方案':
            return await self._generate_technical_proposal(tender_data, enterprise_data, subsections)

        elif section_title == '企业资质':
            return self._generate_qualification_section(enterprise_data)

        elif section_title == '类似业绩':
            return self._generate_performance_section(enterprise_data)

        else:
            return await self._generate_generic_section(section_title, tender_data, enterprise_data)

    def _generate_bid_letter(self, tender_title: str, enterprise_name: str, budget: str) -> str:
        """
        生成投标函
        """
        return f"""
投标函

致：采购人/招标代理机构

1. 我方已仔细研究了{tender_title}项目的招标文件，对招标文件的全部条款及格式已充分理解，无任何异议。我方愿意参加本项目的投标，并按招标文件要求提交投标文件。

2. 我方承诺：投标文件中所有内容真实、准确、完整，如有虚假，我方愿承担相应法律责任。

3. 我方承诺：如中标，将严格按照招标文件要求及投标文件承诺履行合同，保证工程质量、工期和安全。

4. 我方投标报价为：人民币{budget}元（大写：待填写）。

5. 我方承诺投标有效期为：{90}日历天。

投标单位：{enterprise_name}（盖章）
法定代表人：（签字或盖章）
日期：____年____月____日
"""

    def _generate_authorization(self, enterprise_name: str) -> str:
        """
        生成授权书
        """
        return f"""
法定代表人授权书

致：采购人/招标代理机构

我______（法定代表人姓名）系{enterprise_name}的法定代表人，现授权我单位______（姓名）为我方代理人，以我方名义参加{enterprise_name}项目的投标活动。

代理人在投标过程中所签署的一切文件和处理与之有关的一切事务，我均予以承认。

代理人无转委托权。

特此授权。

投标单位：{enterprise_name}（盖章）
法定代表人：（签字或盖章）
授权代理人：（签字）
日期：____年____月____日
"""

    async def _generate_price_table(self, tender_data: Dict, enterprise_data: Dict) -> str:
        """
        生成报价表
        """
        message = f"""请根据以下信息生成投标报价表：

项目名称：{tender_data.get('title')}
预算金额：{tender_data.get('budget')}
技术要求：{tender_data.get('requirements')}

请生成一份详细的投标报价表，包含：
1. 项目总价
2. 分项报价
3. 备注说明"""

        result = await self.llm_chat(message=message, system_prompt=self.SYSTEM_PROMPT)
        return result.get('content', '报价表待填写')

    async def _generate_technical_proposal(
        self,
        tender_data: Dict,
        enterprise_data: Dict,
        subsections: List[str]
    ) -> str:
        """
        生成技术方案
        """
        default_sections = '- 技术路线' + chr(10) + '- 实施方案' + chr(10) + '- 质量保证'
        sections_text = chr(10).join(f'- {s}' for s in subsections) if subsections else default_sections
        
        message = f"""请根据以下信息撰写技术方案：

项目名称：{tender_data.get('title')}
项目描述：{tender_data.get('description')}
技术要求：{tender_data.get('requirements')}
企业资质：{enterprise_data.get('qualifications', [])}

请撰写完整的技术方案，包含以下章节：
{sections_text}

要求：
1. 方案要针对招标要求
2. 突出企业技术优势
3. 方案要具体可行
4. 包含必要的图表说明"""

        result = await self.llm_chat(
            message=message,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=8000
        )
        return result.get('content', '技术方案待编写')

    def _generate_qualification_section(self, enterprise_data: Dict) -> str:
        """
        生成资质章节
        """
        qualifications = enterprise_data.get('qualifications', [])

        content = "企业资质证明\n\n"

        if qualifications:
            for i, q in enumerate(qualifications, 1):
                content += f"{i}. {q.get('name', '')}\n"
                content += f"   资质等级：{q.get('grade', '')}\n"
                content += f"   资质范围：{q.get('scope', '')}\n"
                content += f"   有效期至：{q.get('expiry_date', '')}\n\n"
        else:
            content += "（请附上企业相关资质证书复印件）\n"

        return content

    def _generate_performance_section(self, enterprise_data: Dict) -> str:
        """
        生成业绩章节
        """
        performances = enterprise_data.get('performances', [])

        content = "类似业绩证明\n\n"

        if performances:
            for i, p in enumerate(performances, 1):
                content += f"{i}. {p.get('name', '')}\n"
                content += f"   项目类型：{p.get('type', '')}\n"
                content += f"   合同金额：{p.get('amount', '')}\n"
                content += f"   完成时间：{p.get('date', '')}\n\n"
        else:
            content += "（请附上企业类似业绩证明材料）\n"

        return content

    async def _generate_generic_section(
        self,
        section_title: str,
        tender_data: Dict,
        enterprise_data: Dict
    ) -> str:
        """
        生成通用章节
        """
        message = f"""请根据以下信息撰写"{section_title}"章节：

项目名称：{tender_data.get('title')}
项目要求：{tender_data.get('requirements')}
企业名称：{enterprise_data.get('name')}"""

        result = await self.llm_chat(message=message, system_prompt=self.SYSTEM_PROMPT)
        return result.get('content', f'{section_title}内容待编写')

    async def _assemble_document(
        self,
        sections: List[Dict[str, Any]],
        tender_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        组装文档
        """
        full_content = f"# 投标文件\n\n"
        full_content += f"## 项目名称：{tender_data.get('title')}\n\n"

        for section in sections:
            full_content += f"### {section['title']}\n\n"
            full_content += section['content']
            full_content += "\n\n"

        return {
            'title': f"{tender_data.get('title')} - 投标文件",
            'content': full_content,
            'sections': sections,
            'format': 'markdown'
        }


class BidDocumentReviewerAgent(BaseBidAgent):
    """
    标书审核Agent
    负责审核投标文件质量，90分以下需要优化
    """
    agent_type = AgentType.ORCHESTRATOR

    SYSTEM_PROMPT = """你是一个专业的投标文件审核专家。你的任务是：
1. 审核投标文件是否完整
2. 检查投标文件是否符合招标要求
3. 评估投标文件的竞争力
4. 给出改进建议

审核标准：
- 合规性（35%）：是否符合招标文件要求
- 完整性（25%）：是否包含所有必要内容
- 质量（25%）：内容质量是否专业
- 竞争力（15%）：是否突出企业优势

请以JSON格式输出审核结果：
{
    "overall_score": 总分(0-100),
    "compliance_score": 合规性得分(0-100),
    "completeness_score": 完整性得分(0-100),
    "quality_score": 质量得分(0-100),
    "competitiveness_score": 竞争力得分(0-100),
    "strengths": ["优势点1", "优势点2"],
    "weaknesses": ["待改进点1", "待改进点2"],
    "suggestions": ["建议1", "建议2"],
    "risk_points": ["风险点1", "风险点2"],
    "is_passed": 是否通过(true/false),
    "needs_optimization": 是否需要优化(true/false)
}"""

    PASS_THRESHOLD = 90

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行标书审核任务
        """
        tender_data = task.get('tender_data', {})
        document = task.get('document', {})
        sections = task.get('sections', [])

        try:
            review_result = await self._review_document(tender_data, document, sections)

            overall_score = review_result.get('overall_score', 0)
            is_passed = overall_score >= self.PASS_THRESHOLD

            review_result['pass_threshold'] = self.PASS_THRESHOLD
            review_result['is_passed'] = is_passed
            review_result['needs_optimization'] = not is_passed

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_data.get('id'),
                    'review_result': review_result,
                    'overall_score': overall_score,
                    'is_passed': is_passed,
                    'needs_optimization': not is_passed
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"标书审核失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _review_document(
        self,
        tender_data: Dict[str, Any],
        document: Dict[str, Any],
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        审核文档
        """
        document_content = document.get('content', '')

        compliance_review = await self._review_compliance(tender_data, document)

        completeness_review = await self._review_completeness(tender_data, sections)

        quality_review = await self._review_quality(document_content)

        competitiveness_review = await self._review_competitiveness(tender_data, document)

        overall_score = int(
            compliance_review['score'] * 0.35 +
            completeness_review['score'] * 0.25 +
            quality_review['score'] * 0.25 +
            competitiveness_review['score'] * 0.15
        )

        return {
            'overall_score': overall_score,
            'compliance_score': compliance_review['score'],
            'completeness_score': completeness_review['score'],
            'quality_score': quality_review['score'],
            'competitiveness_score': competitiveness_review['score'],
            'strengths': (
                compliance_review.get('strengths', []) +
                completeness_review.get('strengths', []) +
                quality_review.get('strengths', []) +
                competitiveness_review.get('strengths', [])
            ),
            'weaknesses': (
                compliance_review.get('weaknesses', []) +
                completeness_review.get('weaknesses', []) +
                quality_review.get('weaknesses', []) +
                competitiveness_review.get('weaknesses', [])
            ),
            'suggestions': (
                compliance_review.get('suggestions', []) +
                completeness_review.get('suggestions', []) +
                quality_review.get('suggestions', []) +
                competitiveness_review.get('suggestions', [])
            ),
            'risk_points': compliance_review.get('risks', []),
            'comparison_with_tender': compliance_review.get('comparison', '')
        }

    async def _review_compliance(
        self,
        tender_data: Dict[str, Any],
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审核合规性
        """
        message = f"""请审核以下投标文件是否符合招标要求：

招标要求：
{tender_data.get('requirements')}

投标文件内容：
{document.get('content', '')[:3000]}

请评估合规性得分(0-100)，并列出：
1. 符合要求的方面
2. 不符合要求的方面
3. 改进建议"""

        result = await self.llm_chat(message=message, system_prompt=self.SYSTEM_PROMPT)

        try:
            import json
            content = result.get('content', '')

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())
        except:
            return {
                'score': 70,
                'strengths': ['基本符合要求'],
                'weaknesses': ['需要进一步核实'],
                'suggestions': ['请仔细对照招标要求检查']
            }

    async def _review_completeness(
        self,
        tender_data: Dict[str, Any],
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        审核完整性
        """
        required_sections = [
            '投标函', '授权书', '报价表', '技术方案', '企业资质', '业绩证明'
        ]

        existing_sections = [s.get('title') for s in sections]

        missing = []
        for req in required_sections:
            if not any(req in existing for existing in existing_sections):
                missing.append(req)

        score = 100 - len(missing) * 15
        score = max(0, score)

        return {
            'score': score,
            'strengths': [s for s in existing_sections if s],
            'weaknesses': [f"缺少：{m}" for m in missing],
            'suggestions': [f"请补充：{m}" for m in missing] if missing else ['文档结构完整']
        }

    async def _review_quality(self, document_content: str) -> Dict[str, Any]:
        """
        审核质量
        """
        message = f"""请评估以下投标文件的内容质量：

{document_content[:3000]}

请评估质量得分(0-100)，考虑：
1. 内容是否专业、规范
2. 表述是否清晰、准确
3. 逻辑是否严谨
4. 是否有错别字或语病"""

        result = await self.llm_chat(message=message, system_prompt=self.SYSTEM_PROMPT)

        try:
            import json
            content = result.get('content', '')

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())
        except:
            return {
                'score': 75,
                'strengths': ['内容基本完整'],
                'weaknesses': ['可以进一步优化'],
                'suggestions': ['建议增加更多细节']
            }

    async def _review_competitiveness(
        self,
        tender_data: Dict[str, Any],
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        审核竞争力
        """
        message = f"""请评估以下投标文件的竞争力：

项目要求：{tender_data.get('requirements')}
投标文件：{document.get('content', '')[:2000]}

请评估竞争力得分(0-100)，考虑：
1. 是否突出了企业优势
2. 技术方案是否有创新点
3. 报价是否有竞争力
4. 服务承诺是否有吸引力"""

        result = await self.llm_chat(message=message, system_prompt=self.SYSTEM_PROMPT)

        try:
            import json
            content = result.get('content', '')

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())
        except:
            return {
                'score': 70,
                'strengths': ['有基本竞争力'],
                'weaknesses': ['竞争力有待提升'],
                'suggestions': ['建议进一步突出优势']
            }
