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

from openclaw.agents.bid_collector_agent import BidAnalystAgent


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


class WorkerAgent(BaseAgent):
    """
    Worker Agent基类
    借鉴Hermes的Worker角色：执行具体任务，向Coordinator汇报
    所有专业Agent（Collector/Matcher/Generator等）都是Worker
    """

    worker_type: str = 'generic'
    worker_capabilities: List[str] = []

    async def report_to_coordinator(
        self,
        task_result: TaskResult,
        coordinator_id: str = None
    ) -> bool:
        """
        向Coordinator汇报任务结果

        Args:
            task_result: 任务执行结果
            coordinator_id: Coordinator Agent ID

        Returns:
            bool: 是否汇报成功
        """
        try:
            from openclaw.agent_manager import agent_manager

            if not coordinator_id:
                parent_id = self.context.parent_agent_id
                if not parent_id:
                    return False
                coordinator_id = parent_id

            coordinator = await agent_manager.get_agent(coordinator_id)
            if not coordinator:
                return False

            coordinator.add_message('worker_report', {
                'worker_id': self.agent_id,
                'worker_type': self.worker_type,
                'task_result': task_result.to_dict(),
                'timestamp': datetime.now().isoformat()
            })

            return True

        except Exception as e:
            logger.error(f"向Coordinator汇报失败: {str(e)}")
            return False


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent
    借鉴Hermes的Coordinator角色：分解任务、分配Worker、管理进度、综合结果

    与原SupervisorAgent的区别：
    - 明确的Coordinator/Worker角色分工
    - Worker通过report_to_coordinator汇报，而非被动等待
    - 支持并行Worker执行
    - 内置进度追踪和超时管理
    """

    agent_type = AgentType.SUPERVISOR
    capabilities = [
        AgentCapability.ORCHESTRATING,
        AgentCapability.ANALYZING
    ]
    default_tools = ['llm_chat', 'read_memory', 'write_memory']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._workers: Dict[str, BaseAgent] = {}
        self._worker_results: Dict[str, TaskResult] = {}
        self._task_plan: List[Dict] = []
        self._completed_steps: List[str] = []

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行协调任务

        Args:
            task: {
                'workflow': 工作流类型,
                'params': 参数,
                'parallel': 是否并行执行独立步骤 (default: False)
            }
        """
        workflow = task.get('workflow', 'default')
        params = task.get('params', {})
        parallel = task.get('parallel', False)

        try:
            self._task_plan = await self._decompose_task(workflow, params)

            if parallel:
                results = await self._execute_plan_parallel(params)
            else:
                results = await self._execute_plan_sequential(params)

            final_result = await self._synthesize_results(results)

            return TaskResult(
                success=True,
                data=final_result
            )

        except Exception as e:
            logger.error(f"Coordinator执行失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e)
            )

    async def _decompose_task(
        self,
        workflow: str,
        params: Dict
    ) -> List[Dict]:
        """
        任务分解：将工作流分解为可执行的Worker步骤
        """
        if workflow == 'bid_full':
            return [
                {
                    'step_id': 'collect',
                    'worker_type': 'collector',
                    'task': 'collect',
                    'depends_on': [],
                    'parallel_group': 1,
                    'description': '信息收集'
                },
                {
                    'step_id': 'match',
                    'worker_type': 'matcher',
                    'task': 'match',
                    'depends_on': ['collect'],
                    'parallel_group': 2,
                    'description': '企业比对'
                },
                {
                    'step_id': 'analyze',
                    'worker_type': 'analyst',
                    'task': 'analyze',
                    'depends_on': ['match'],
                    'parallel_group': 3,
                    'description': '投标论证'
                },
                {
                    'step_id': 'generate',
                    'worker_type': 'generator',
                    'task': 'generate',
                    'depends_on': ['analyze'],
                    'parallel_group': 4,
                    'description': '标书制作'
                },
                {
                    'step_id': 'review',
                    'worker_type': 'reviewer',
                    'task': 'review',
                    'depends_on': ['generate'],
                    'parallel_group': 5,
                    'description': '标书审核'
                },
            ]
        elif workflow == 'bid_quick':
            return [
                {
                    'step_id': 'collect',
                    'worker_type': 'collector',
                    'task': 'collect',
                    'depends_on': [],
                    'parallel_group': 1,
                    'description': '信息收集'
                },
                {
                    'step_id': 'match',
                    'worker_type': 'matcher',
                    'task': 'match',
                    'depends_on': ['collect'],
                    'parallel_group': 2,
                    'description': '企业比对'
                },
            ]
        elif workflow == 'bid_collect_only':
            return [
                {
                    'step_id': 'collect',
                    'worker_type': 'collector',
                    'task': 'collect',
                    'depends_on': [],
                    'parallel_group': 1,
                    'description': '信息收集'
                },
            ]
        else:
            return []

    async def _execute_plan_sequential(
        self,
        params: Dict
    ) -> List[Dict]:
        """
        顺序执行计划
        """
        results = []
        context = params.copy()

        for step in self._task_plan:
            step_id = step['step_id']
            logger.info(f"Coordinator: 执行步骤 {step_id} - {step.get('description', '')}")

            worker = await self._create_worker(step['worker_type'])
            self._workers[step_id] = worker

            task_data = self._prepare_worker_task(step, context)

            result = await worker.run(task_data)

            self._worker_results[step_id] = result

            if result.success:
                context.update(result.data or {})
                self._completed_steps.append(step_id)

                await worker.report_to_coordinator(result, self.agent_id)
            else:
                logger.warning(f"Coordinator: 步骤 {step_id} 失败: {result.error}")
                break

            results.append({
                'step_id': step_id,
                'worker_type': step['worker_type'],
                'result': result.to_dict()
            })

        return results

    async def _execute_plan_parallel(
        self,
        params: Dict
    ) -> List[Dict]:
        """
        并行执行计划（同parallel_group的步骤并行执行）
        """
        results = []
        context = params.copy()

        parallel_groups = {}
        for step in self._task_plan:
            group = step.get('parallel_group', 1)
            if group not in parallel_groups:
                parallel_groups[group] = []
            parallel_groups[group].append(step)

        for group_num in sorted(parallel_groups.keys()):
            group_steps = parallel_groups[group_num]

            tasks = []
            for step in group_steps:
                worker = await self._create_worker(step['worker_type'])
                self._workers[step['step_id']] = worker
                task_data = self._prepare_worker_task(step, context)
                tasks.append((step, worker, task_data))

            if len(tasks) == 1:
                step, worker, task_data = tasks[0]
                result = await worker.run(task_data)
                self._worker_results[step['step_id']] = result

                if result.success:
                    context.update(result.data or {})
                    self._completed_steps.append(step['step_id'])
                    await worker.report_to_coordinator(result, self.agent_id)

                results.append({
                    'step_id': step['step_id'],
                    'worker_type': step['worker_type'],
                    'result': result.to_dict()
                })
            else:
                coros = []
                for step, worker, task_data in tasks:
                    coros.append(worker.run(task_data))

                task_results = await asyncio.gather(*coros, return_exceptions=True)

                for (step, worker, task_data), result in zip(tasks, task_results):
                    if isinstance(result, Exception):
                        result = TaskResult(success=False, error=str(result))

                    self._worker_results[step['step_id']] = result

                    if result.success:
                        context.update(result.data or {})
                        self._completed_steps.append(step['step_id'])
                        await worker.report_to_coordinator(result, self.agent_id)

                    results.append({
                        'step_id': step['step_id'],
                        'worker_type': step['worker_type'],
                        'result': result.to_dict()
                    })

        return results

    async def _create_worker(self, worker_type: str) -> BaseAgent:
        """
        创建Worker Agent
        """
        worker_map = {
            'collector': TenderCollectorAgent,
            'matcher': EnterpriseMatcherAgent,
            'analyst': BidAnalystAgent,
            'generator': BidDocumentGeneratorAgent,
            'reviewer': BidDocumentReviewerAgent,
        }

        worker_class = worker_map.get(worker_type)
        if not worker_class:
            raise ValueError(f"Unknown worker type: {worker_type}")

        worker = worker_class(session_id=self.session_id)

        if isinstance(worker, WorkerAgent):
            worker.context.parent_agent_id = self.agent_id

        self._workers[worker_type] = worker
        return worker

    def _prepare_worker_task(
        self,
        step: Dict,
        context: Dict
    ) -> Dict:
        """
        准备Worker任务数据
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
        elif task_type == 'analyze':
            return {
                'tender_data': context.get('tender_data', {}),
                'enterprise_data': context.get('enterprise_data', {}),
                'match_result': context.get('match_result', {})
            }
        elif task_type == 'generate':
            return {
                'tender_data': context.get('tender_data', {}),
                'enterprise_data': context.get('enterprise_data', {}),
                'match_result': context.get('match_result', {})
            }
        elif task_type == 'review':
            return {
                'document': context.get('document', {}),
                'tender_data': context.get('tender_data', {}),
                'sections': context.get('sections', [])
            }
        else:
            return {}

    async def _synthesize_results(self, results: List[Dict]) -> Dict:
        """
        综合所有Worker的结果
        """
        all_success = all(
            r['result'].get('success', False) for r in results
        )

        worker_summaries = {}
        for r in results:
            worker_summaries[r['step_id']] = {
                'worker_type': r['worker_type'],
                'success': r['result'].get('success', False),
                'error': r['result'].get('error'),
            }

        return {
            'workflow_completed': all_success,
            'total_steps': len(results),
            'completed_steps': len(self._completed_steps),
            'worker_summaries': worker_summaries,
            'results': results
        }

    def get_progress(self) -> Dict:
        """
        获取执行进度
        """
        total = len(self._task_plan)
        completed = len(self._completed_steps)

        return {
            'total_steps': total,
            'completed_steps': completed,
            'progress_percent': round(completed / total * 100, 1) if total > 0 else 0,
            'current_step': self._completed_steps[-1] if self._completed_steps else None,
            'pending_steps': [
                s['step_id'] for s in self._task_plan
                if s['step_id'] not in self._completed_steps
            ]
        }


class SupervisorAgent(CoordinatorAgent):
    """
    监督Agent（兼容旧接口）
    继承自CoordinatorAgent，保持向后兼容
    新代码应直接使用CoordinatorAgent
    """

    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        return await super().execute(task)
