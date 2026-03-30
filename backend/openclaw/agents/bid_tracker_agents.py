"""
结果查询Agent和质量提升Agent
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from openclaw.base_agent import AgentType, TaskResult
from openclaw.agents.bid_collector_agent import BaseBidAgent


logger = logging.getLogger(__name__)


class BidResultTrackerAgent(BaseBidAgent):
    """
    结果查询Agent
    负责跟踪投标结果
    """
    agent_type = AgentType.UPLOADER

    SYSTEM_PROMPT = """你是一个专业的投标结果跟踪专家。你的任务是：
1. 定期查询投标项目的中标结果
2. 分析中标/未中标原因
3. 总结经验教训
4. 提供改进建议

请以JSON格式输出跟踪结果：
{
    "status": "won/lost/pending",
    "winner_name": "中标单位名称",
    "winner_amount": "中标金额",
    "our_rank": "我方排名",
    "analysis": "结果分析",
    "lessons_learned": "经验教训",
    "improvement_suggestions": ["改进建议1", "改进建议2"]
}"""

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行结果查询任务
        """
        tender_id = task.get('tender_id')
        tender_data = task.get('tender_data', {})
        bid_date = task.get('bid_date')

        try:
            result_info = await self._query_bid_result(tender_id, tender_data)

            analysis = await self._analyze_result(tender_data, result_info)

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_id,
                    'result_info': result_info,
                    'analysis': analysis,
                    'query_time': datetime.now().isoformat()
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"结果查询失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _query_bid_result(
        self,
        tender_id: int,
        tender_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        查询投标结果
        """
        from apps.bids.models import BidRecord, BidResult

        result_info = {
            'status': 'pending',
            'winner_name': None,
            'winner_amount': None,
            'our_rank': None
        }

        try:
            bid_record = BidRecord.objects.filter(tender_id=tender_id).first()

            if bid_record:
                result_info['bid_status'] = bid_record.status

                bid_result = BidResult.objects.filter(bid_record=bid_record).first()

                if bid_result:
                    result_info['status'] = 'won' if bid_result.result_type == 'win' else 'lost'
                    result_info['winner_name'] = bid_result.winner_name
                    result_info['winner_amount'] = str(bid_result.winner_amount) if bid_result.winner_amount else None
                    result_info['our_rank'] = bid_result.our_rank
                    result_info['announce_date'] = str(bid_result.announce_date) if bid_result.announce_date else None

        except Exception as e:
            logger.warning(f"查询投标记录失败: {str(e)}")

        if result_info['status'] == 'pending':
            crawled_result = await self._crawl_result_from_source(tender_data)
            if crawled_result:
                result_info.update(crawled_result)

        return result_info

    async def _crawl_result_from_source(
        self,
        tender_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从来源网站爬取结果
        """
        source_url = tender_data.get('source_url')

        if not source_url:
            return {}

        message = f"""请分析以下招标项目是否有中标结果公告：

项目名称：{tender_data.get('title')}
来源网址：{source_url}

如果有结果，请提取：
1. 中标单位名称
2. 中标金额
3. 公告日期"""

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
            return {}

    async def _analyze_result(
        self,
        tender_data: Dict[str, Any],
        result_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析投标结果
        """
        status = result_info.get('status', 'pending')

        if status == 'pending':
            return {
                'analysis': '结果尚未公布，请继续关注',
                'next_check_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            }

        message = f"""请分析以下投标结果：

项目名称：{tender_data.get('title')}
投标结果：{'中标' if status == 'won' else '未中标'}
中标单位：{result_info.get('winner_name', '未知')}
中标金额：{result_info.get('winner_amount', '未知')}
我方排名：{result_info.get('our_rank', '未知')}

请给出：
1. 结果分析
2. 经验教训
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
                'analysis': result.get('content', ''),
                'lessons_learned': [],
                'improvement_suggestions': []
            }


class BidQualityOptimizerAgent(BaseBidAgent):
    """
    质量提升Agent
    负责优化标书质量
    """
    agent_type = AgentType.ORCHESTRATOR

    SYSTEM_PROMPT = """你是一个专业的投标文件优化专家。你的任务是：
1. 根据审核反馈优化标书
2. 提升标书的合规性、完整性、质量和竞争力
3. 确保优化后的标书达到90分以上
4. 保持内容的专业性和准确性

优化原则：
- 针对性：针对审核发现的问题进行优化
- 专业性：确保内容专业、规范
- 竞争力：突出企业优势，提升竞争力
- 合规性：严格符合招标要求

请以JSON格式输出优化方案：
{
    "optimization_plan": [
        {
            "section": "章节名称",
            "issues": ["问题1", "问题2"],
            "solutions": ["解决方案1", "解决方案2"],
            "optimized_content": "优化后的内容"
        }
    ],
    "expected_score_improvement": "预期分数提升",
    "key_improvements": ["关键改进点1", "关键改进点2"]
}"""

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行质量优化任务
        """
        tender_data = task.get('tender_data', {})
        document = task.get('document', {})
        review_result = task.get('review_result', {})
        current_score = review_result.get('overall_score', 0)

        try:
            optimization_plan = await self._create_optimization_plan(
                tender_data,
                document,
                review_result
            )

            optimized_document = await self._apply_optimizations(
                document,
                optimization_plan
            )

            expected_score = current_score + optimization_plan.get('expected_score_improvement', 10)

            return TaskResult(
                success=True,
                data={
                    'tender_id': tender_data.get('id'),
                    'original_score': current_score,
                    'expected_score': min(expected_score, 100),
                    'optimization_plan': optimization_plan,
                    'optimized_document': optimized_document,
                    'iterations': 1
                },
                metadata={'agent_id': self.agent_id}
            )

        except Exception as e:
            logger.error(f"质量优化失败: {str(e)}")
            return TaskResult(success=False, error=str(e))

    async def _create_optimization_plan(
        self,
        tender_data: Dict[str, Any],
        document: Dict[str, Any],
        review_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建优化方案
        """
        weaknesses = review_result.get('weaknesses', [])
        suggestions = review_result.get('suggestions', [])

        message = f"""请根据以下审核结果创建标书优化方案：

项目名称：{tender_data.get('title')}
当前得分：{review_result.get('overall_score', 0)}

审核发现的问题：
{chr(10).join(f'- {w}' for w in weaknesses)}

改进建议：
{chr(10).join(f'- {s}' for s in suggestions)}

当前标书内容摘要：
{document.get('content', '')[:2000]}

请制定详细的优化方案，确保优化后得分达到90分以上。"""

        result = await self.llm_chat(
            message=message,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=8000
        )

        try:
            import json
            content = result.get('content', '')

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            plan = json.loads(content.strip())
            plan['expected_score_improvement'] = self._estimate_improvement(review_result)
            return plan
        except:
            return {
                'optimization_plan': [],
                'expected_score_improvement': 10,
                'key_improvements': suggestions[:5]
            }

    def _estimate_improvement(self, review_result: Dict[str, Any]) -> int:
        """
        估算分数提升
        """
        current_score = review_result.get('overall_score', 0)
        weaknesses_count = len(review_result.get('weaknesses', []))

        improvement = min(weaknesses_count * 3, 100 - current_score)
        improvement = max(improvement, 5)

        return improvement

    async def _apply_optimizations(
        self,
        document: Dict[str, Any],
        optimization_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用优化方案
        """
        optimized_sections = []

        for section in document.get('sections', []):
            section_title = section.get('title')
            original_content = section.get('content', '')

            optimization = self._find_section_optimization(
                section_title,
                optimization_plan.get('optimization_plan', [])
            )

            if optimization:
                optimized_content = optimization.get('optimized_content', original_content)
            else:
                optimized_content = await self._enhance_section(section_title, original_content)

            optimized_sections.append({
                'title': section_title,
                'subsections': section.get('subsections', []),
                'content': optimized_content,
                'optimized': bool(optimization)
            })

        full_content = self._rebuild_document(optimized_sections, document.get('title', ''))

        return {
            'title': document.get('title', ''),
            'content': full_content,
            'sections': optimized_sections,
            'format': 'markdown'
        }

    def _find_section_optimization(
        self,
        section_title: str,
        optimizations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        查找章节优化方案
        """
        for opt in optimizations:
            if opt.get('section') in section_title or section_title in opt.get('section', ''):
                return opt
        return {}

    async def _enhance_section(self, section_title: str, content: str) -> str:
        """
        增强章节内容
        """
        if len(content) < 100:
            return content

        message = f"""请优化以下"{section_title}"章节的内容，使其更加专业、完整：

{content}

优化要求：
1. 保持原有结构和要点
2. 增加专业性和规范性
3. 确保内容完整、准确
4. 突出竞争优势"""

        result = await self.llm_chat(
            message=message,
            system_prompt=self.SYSTEM_PROMPT
        )

        return result.get('content', content)

    def _rebuild_document(
        self,
        sections: List[Dict[str, Any]],
        title: str
    ) -> str:
        """
        重建文档
        """
        full_content = f"# 投标文件\n\n"

        for section in sections:
            full_content += f"## {section['title']}\n\n"
            full_content += section['content']
            full_content += "\n\n"

        return full_content
