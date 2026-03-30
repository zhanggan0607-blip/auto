"""
OpenCAL 专业Agent实现
基于增强版BaseAgent的专业Agent
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from openclaw.base_agent import (
    BaseAgent, AgentType, AgentCapability, AgentConfig, TaskResult
)

from openclaw.agents.bid_document_agents import (
    BidDocumentGeneratorAgent,
    BidDocumentReviewerAgent
)


logger = logging.getLogger(__name__)


class TenderCollectorAgent(BaseAgent):
    """
    招标信息采集Agent
    负责从各网站采集招标公告
    """
    
    agent_type = AgentType.COLLECTOR
    capabilities = [
        AgentCapability.CRAWLING,
        AgentCapability.PARSING
    ]
    default_tools = ['http_request', 'execute_code']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sources = {
            'china_gov': '中国政府采购网',
            'shanghai_gov': '上海市政府采购网',
            'shanghai_construction': '上海市建设工程交易服务中心'
        }
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行采集任务
        
        Args:
            task: {
                'source': '数据源代码',
                'keywords': ['关键词列表'],
                'page': 页码,
                'page_size': 每页数量,
                'start_date': '开始日期',
                'end_date': '结束日期'
            }
        """
        source = task.get('source')
        keywords = task.get('keywords', [])
        page = task.get('page', 1)
        page_size = task.get('page_size', 20)
        start_date = task.get('start_date')
        end_date = task.get('end_date')
        
        if not source:
            return TaskResult(
                success=False,
                error='数据源不能为空'
            )
        
        try:
            results = await self._collect_from_source(
                source=source,
                keywords=keywords,
                page=page,
                page_size=page_size,
                start_date=start_date,
                end_date=end_date
            )
            
            processed_results = await self._process_results(results)
            
            self.add_memory('last_collection', {
                'source': source,
                'count': len(processed_results),
                'timestamp': datetime.now().isoformat()
            })
            
            return TaskResult(
                success=True,
                data={
                    'source': source,
                    'total': len(processed_results),
                    'items': processed_results
                }
            )
            
        except Exception as e:
            logger.error(f"采集失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e)
            )
    
    async def _collect_from_source(
        self,
        source: str,
        keywords: List[str],
        page: int,
        page_size: int,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        从指定源采集
        """
        from openclaw.architecture.embedded import embedded_executor
        
        result = await embedded_executor.run_crawler(
            source=source,
            config={
                'keywords': keywords,
                'page': page,
                'page_size': page_size,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        if result.get('error'):
            raise Exception(result['error'])
        
        return result.get('data', [])
    
    async def _process_results(self, results: List[Dict]) -> List[Dict]:
        """
        处理采集结果
        """
        processed = []
        
        for item in results:
            processed_item = {
                'title': item.get('title', ''),
                'project_code': item.get('project_code', ''),
                'publish_date': item.get('publish_date', ''),
                'source_url': item.get('source_url', ''),
                'content': item.get('content', ''),
                'collected_at': datetime.now().isoformat()
            }
            processed.append(processed_item)
        
        return processed


class EnterpriseMatcherAgent(BaseAgent):
    """
    企业匹配Agent
    负责将招标信息与企业资质进行匹配
    """
    
    agent_type = AgentType.MATCHER
    capabilities = [
        AgentCapability.MATCHING,
        AgentCapability.ANALYZING
    ]
    default_tools = ['llm_chat', 'read_memory', 'write_memory']
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行匹配任务
        
        Args:
            task: {
                'tender_data': 招标信息,
                'enterprise_id': 企业ID
            }
        """
        tender_data = task.get('tender_data', {})
        enterprise_id = task.get('enterprise_id')
        
        if not tender_data:
            return TaskResult(
                success=False,
                error='招标信息不能为空'
            )
        
        try:
            enterprise_data = await self._get_enterprise_data(enterprise_id)
            
            match_result = await self._perform_matching(tender_data, enterprise_data)
            
            analysis = await self._analyze_match(match_result)
            
            return TaskResult(
                success=True,
                data={
                    'match_score': match_result.get('score', 0),
                    'match_details': match_result,
                    'analysis': analysis,
                    'enterprise_data': enterprise_data
                }
            )
            
        except Exception as e:
            logger.error(f"匹配失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e)
            )
    
    async def _get_enterprise_data(self, enterprise_id: int) -> Dict:
        """
        获取企业数据
        """
        from apps.enterprise.models import Enterprise, EnterpriseQualification
        
        try:
            enterprise = Enterprise.objects.get(id=enterprise_id)
            qualifications = EnterpriseQualification.objects.filter(
                enterprise=enterprise, 
                is_valid=True
            ).values_list('qualification_name', flat=True)
            
            return {
                'id': enterprise.id,
                'name': enterprise.name,
                'qualifications': list(qualifications),
                'business_scope': enterprise.business_scope or ''
            }
        except Enterprise.DoesNotExist:
            return {}
    
    async def _perform_matching(
        self,
        tender_data: Dict,
        enterprise_data: Dict
    ) -> Dict:
        """
        执行匹配
        """
        from services.enterprise_matching_engine import EnterpriseMatchingEngine
        
        engine = EnterpriseMatchingEngine()
        
        result = engine.match(
            tender_data=tender_data,
            enterprise_data=enterprise_data
        )
        
        return result
    
    async def _analyze_match(self, match_result: Dict) -> Dict:
        """
        分析匹配结果
        """
        prompt = f"""请分析以下匹配结果，给出投标建议：

匹配分数: {match_result.get('score', 0)}
匹配详情: {json.dumps(match_result.get('details', {}), ensure_ascii=False)}

请从以下方面分析：
1. 资质匹配情况
2. 投标优势
3. 潜在风险
4. 投标建议"""
        
        analysis = await self.think(prompt)
        
        return {
            'summary': analysis,
            'recommendation': 'participate' if match_result.get('score', 0) >= 60 else 'skip'
        }


class SupervisorAgent(BaseAgent):
    """
    监督Agent
    负责协调多个Agent协作
    """
    
    agent_type = AgentType.SUPERVISOR
    capabilities = [
        AgentCapability.ORCHESTRATING,
        AgentCapability.ANALYZING
    ]
    default_tools = ['llm_chat', 'read_memory', 'write_memory']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._child_agents: Dict[str, BaseAgent] = {}
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行协调任务
        
        Args:
            task: {
                'workflow': 工作流类型,
                'params': 参数
            }
        """
        workflow = task.get('workflow', 'default')
        params = task.get('params', {})
        
        try:
            plan = await self._create_plan(workflow, params)
            
            results = await self._execute_plan(plan, params)
            
            final_result = await self._aggregate_results(results)
            
            return TaskResult(
                success=True,
                data=final_result
            )
            
        except Exception as e:
            logger.error(f"协调执行失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e)
            )
    
    async def _create_plan(
        self,
        workflow: str,
        params: Dict
    ) -> List[Dict]:
        """
        创建执行计划
        """
        if workflow == 'bid_full':
            return [
                {'agent_type': 'collector', 'task': 'collect'},
                {'agent_type': 'matcher', 'task': 'match'},
                {'agent_type': 'generator', 'task': 'generate'},
                {'agent_type': 'reviewer', 'task': 'review'}
            ]
        elif workflow == 'bid_quick':
            return [
                {'agent_type': 'collector', 'task': 'collect'},
                {'agent_type': 'matcher', 'task': 'match'}
            ]
        else:
            return []
    
    async def _execute_plan(
        self,
        plan: List[Dict],
        params: Dict
    ) -> List[Dict]:
        """
        执行计划
        """
        results = []
        context = params.copy()
        
        for step in plan:
            agent_type = step['agent_type']
            
            agent = await self._create_child_agent(agent_type)
            
            task_data = self._prepare_task_data(step, context)
            
            result = await agent.run(task_data)
            
            results.append({
                'agent_type': agent_type,
                'result': result.to_dict()
            })
            
            if result.success:
                context.update(result.data or {})
            else:
                break
        
        return results
    
    async def _create_child_agent(
        self,
        agent_type: str
    ) -> BaseAgent:
        """
        创建子Agent
        """
        agent_map = {
            'collector': TenderCollectorAgent,
            'matcher': EnterpriseMatcherAgent,
            'generator': BidDocumentGeneratorAgent,
            'reviewer': BidDocumentReviewerAgent
        }
        
        agent_class = agent_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent = agent_class(session_id=self.session_id)
        self._child_agents[agent.agent_id] = agent
        
        return agent
    
    def _prepare_task_data(
        self,
        step: Dict,
        context: Dict
    ) -> Dict:
        """
        准备任务数据
        """
        task_type = step['task']
        
        if task_type == 'collect':
            return {
                'source': context.get('source', 'shanghai_gov'),
                'keywords': context.get('keywords', [])
            }
        elif task_type == 'match':
            return {
                'tender_data': context.get('tender_data', {}),
                'enterprise_id': context.get('enterprise_id')
            }
        elif task_type == 'generate':
            return {
                'tender_data': context.get('tender_data', {}),
                'enterprise_data': context.get('enterprise_data', {})
            }
        elif task_type == 'review':
            return {
                'document': context.get('document', {}),
                'tender_data': context.get('tender_data', {})
            }
        else:
            return {}
    
    async def _aggregate_results(
        self,
        results: List[Dict]
    ) -> Dict:
        """
        汇总结果
        """
        return {
            'workflow_completed': all(
                r['result'].get('success', False) for r in results
            ),
            'steps': len(results),
            'results': results
        }
