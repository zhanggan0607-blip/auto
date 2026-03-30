"""
Agent协调器
负责编排多Agent协作工作流
集成故障自愈机制
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from openclaw.base_agent import AgentType, AgentStatus, TaskResult
from openclaw.agent_manager import agent_manager
from openclaw.agents.bid_collector_agent import BidCollectorAgent, BidMatcherAgent, BidAnalystAgent
from openclaw.agents.bid_document_agents import BidDocumentGeneratorAgent, BidDocumentReviewerAgent
from openclaw.agents.bid_tracker_agents import BidResultTrackerAgent, BidQualityOptimizerAgent
from services.error_diagnoser import error_diagnoser, FallbackAction


logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """
    工作流状态
    """
    workflow_id: str
    session_id: str
    current_stage: str
    status: str = 'pending'
    context: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, str] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class BidWorkflowOrchestrator:
    """
    投标工作流协调器
    编排整个投标流程的多Agent协作
    """

    WORKFLOW_STAGES = [
        ('collect', '信息收集', ['collector']),
        ('match', '企业比对', ['matcher']),
        ('analyze', '投标论证', ['analyst']),
        ('decision', '投标决策', ['orchestrator']),
        ('generate', '标书制作', ['generator']),
        ('review', '标书审核', ['reviewer']),
        ('optimize', '标书优化', ['optimizer']),
        ('upload', '标书上传', ['uploader']),
        ('track', '结果跟踪', ['tracker']),
    ]

    DECISION_THRESHOLD = 60
    REVIEW_PASS_THRESHOLD = 90
    MAX_OPTIMIZATION_ITERATIONS = 3

    def __init__(self):
        self._workflows: Dict[str, WorkflowState] = {}
        self._register_agent_classes()

    def _register_agent_classes(self):
        """
        注册Agent类
        """
        agent_manager.register_agent_class(AgentType.COLLECTOR, BidCollectorAgent)
        agent_manager.register_agent_class(AgentType.PARSER, BidMatcherAgent)
        agent_manager.register_agent_class(AgentType.GENERATOR, BidDocumentGeneratorAgent)
        agent_manager.register_agent_class(AgentType.ORCHESTRATOR, BidDocumentReviewerAgent)

    async def start_workflow(
        self,
        tender_id: int,
        enterprise_id: int = None,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        启动工作流

        Args:
            tender_id: 招标项目ID
            enterprise_id: 企业ID
            config: 工作流配置

        Returns:
            dict: 工作流信息
        """
        workflow_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        state = WorkflowState(
            workflow_id=workflow_id,
            session_id=session_id,
            current_stage='init',
            status='pending',
            context={
                'tender_id': tender_id,
                'enterprise_id': enterprise_id,
                'config': config or {}
            }
        )

        self._workflows[workflow_id] = state

        try:
            await self._create_workflow_record(state)

            asyncio.create_task(self._run_workflow(state))

            return {
                'workflow_id': workflow_id,
                'session_id': session_id,
                'status': 'started',
                'message': '工作流已启动'
            }

        except Exception as e:
            logger.error(f"启动工作流失败: {str(e)}")
            state.status = 'failed'
            state.errors.append(str(e))
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e)
            }

    async def _create_workflow_record(self, state: WorkflowState):
        """
        创建工作流记录
        """
        from apps.openclaw.workflow_models import BidWorkflow, WorkflowStage

        workflow = BidWorkflow.objects.create(
            name=f"投标工作流-{state.context.get('tender_id')}",
            tender_id=state.context.get('tender_id'),
            session_id=state.session_id,
            status='pending',
            context=state.context
        )

        state.context['workflow_db_id'] = workflow.id

        for order, (stage_type, stage_name, _) in enumerate(self.WORKFLOW_STAGES):
            WorkflowStage.objects.create(
                workflow=workflow,
                stage_type=stage_type,
                stage_name=stage_name,
                stage_order=order,
                status='pending'
            )

    async def _run_workflow(self, state: WorkflowState):
        """
        运行工作流
        """
        try:
            state.status = 'running'
            await self._update_workflow_status(state, 'running')

            for stage_type, stage_name, agent_types in self.WORKFLOW_STAGES:
                state.current_stage = stage_type
                logger.info(f"工作流 {state.workflow_id} 进入阶段: {stage_name}")

                should_continue = await self._execute_stage(state, stage_type, stage_name, agent_types)

                if not should_continue:
                    logger.info(f"工作流 {state.workflow_id} 在阶段 {stage_name} 停止")
                    break

            state.status = 'completed'
            await self._update_workflow_status(state, 'completed')

        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            state.status = 'failed'
            state.errors.append(str(e))
            await self._update_workflow_status(state, 'failed')

    async def _execute_stage(
        self,
        state: WorkflowState,
        stage_type: str,
        stage_name: str,
        agent_types: List[str]
    ) -> bool:
        """
        执行工作流阶段（集成故障自愈机制）

        Returns:
            bool: 是否继续执行下一阶段
        """
        from apps.openclaw.workflow_models import WorkflowStage

        stage = WorkflowStage.objects.filter(
            workflow_id=state.context.get('workflow_db_id'),
            stage_type=stage_type
        ).first()

        if stage:
            stage.start()
            stage.agent_type = agent_types[0] if agent_types else None
            stage.save()

        retry_count = 0
        max_retries = 3

        while retry_count <= max_retries:
            try:
                if stage_type == 'collect':
                    result = await self._stage_collect(state)

                elif stage_type == 'match':
                    result = await self._stage_match(state)

                elif stage_type == 'analyze':
                    result = await self._stage_analyze(state)

                elif stage_type == 'decision':
                    result = await self._stage_decision(state)

                elif stage_type == 'generate':
                    result = await self._stage_generate(state)

                elif stage_type == 'review':
                    result = await self._stage_review(state)

                elif stage_type == 'optimize':
                    result = await self._stage_optimize(state)

                elif stage_type == 'upload':
                    result = await self._stage_upload(state)

                elif stage_type == 'track':
                    result = await self._stage_track(state)

                else:
                    result = {'success': True, 'continue': True}

                if stage:
                    stage.complete(output_data=result)

                return result.get('continue', True)

            except Exception as e:
                retry_count += 1

                diagnosis = error_diagnoser.diagnose(
                    error=e,
                    stage=stage_type,
                    context={
                        'workflow_id': state.workflow_id,
                        'session_id': state.session_id,
                        'tender_id': state.context.get('tender_id'),
                        'retry_count': retry_count
                    }
                )

                logger.warning(
                    f"[故障自愈] 阶段 {stage_name} 失败 (尝试 {retry_count}/{max_retries}): "
                    f"错误类型={diagnosis.error_type.value}, "
                    f"降级动作={diagnosis.fallback_action.value}, "
                    f"解决方案={diagnosis.solution}"
                )

                if diagnosis.should_notify:
                    await self._send_failure_notification(
                        stage_name=stage_name,
                        diagnosis=diagnosis,
                        state=state
                    )

                if diagnosis.fallback_action == FallbackAction.RETRY:
                    if retry_count <= max_retries:
                        logger.info(f"执行重试策略，等待后重试...")
                        await asyncio.sleep(min(2 ** retry_count, 10))
                        continue

                elif diagnosis.fallback_action == FallbackAction.RETRY_WITH_BACKUP:
                    if retry_count <= max_retries:
                        logger.info(f"执行备用方案重试策略...")
                        await self._execute_with_backup(state, stage_type)
                        retry_count += 1
                        continue

                elif diagnosis.fallback_action == FallbackAction.USE_PARTIAL_DATA:
                    logger.info(f"使用部分数据继续执行...")
                    if stage:
                        stage.complete(output_data={'partial': True, 'error': str(e)})
                    return True

                elif diagnosis.fallback_action == FallbackAction.USE_DEFAULT_VALUE:
                    logger.info(f"使用默认值继续...")
                    if stage:
                        stage.complete(output_data={'use_default': True})
                    return True

                elif diagnosis.fallback_action == FallbackAction.SKIP_AND_CONTINUE:
                    logger.info(f"跳过当前阶段继续执行...")
                    if stage:
                        stage.complete(output_data={'skipped': True, 'reason': str(e)})
                    return True

                elif diagnosis.fallback_action == FallbackAction.SKIP_AND_LOG:
                    logger.info(f"跳过并记录...")
                    if stage:
                        stage.complete(output_data={'skipped_with_log': True})
                    return True

                elif diagnosis.fallback_action == FallbackAction.WAIT_FOR_MANUAL:
                    logger.warning(f"等待人工处理...")
                    if stage:
                        stage.fail(f"等待人工处理: {diagnosis.solution}")
                    state.errors.append(f"{stage_name}: 等待人工处理 - {diagnosis.solution}")
                    return False

                elif diagnosis.fallback_action == FallbackAction.ABORT_WORKFLOW:
                    logger.error(f"终止工作流...")
                    if stage:
                        stage.fail(str(e))
                    state.errors.append(f"{stage_name}: {str(e)}")
                    return False

                else:
                    if retry_count > max_retries:
                        logger.error(f"超过最大重试次数，终止阶段...")
                        if stage:
                            stage.fail(str(e))
                        state.errors.append(f"{stage_name}: {str(e)}")
                        return False
                    continue

        if stage:
            stage.fail("超过最大重试次数")
        state.errors.append(f"{stage_name}: 超过最大重试次数")
        return False

    async def _execute_with_backup(self, state: WorkflowState, stage_type: str):
        """
        使用备用方案执行阶段
        """
        logger.info(f"切换到备用数据源或方法...")

        if stage_type == 'collect':
            state.context['use_backup_source'] = True
        elif stage_type == 'match':
            state.context['use_backup_matcher'] = True
        elif stage_type == 'generate':
            state.context['use_backup_generator'] = True

    async def _stage_collect(self, state: WorkflowState) -> Dict[str, Any]:
        """
        信息收集阶段
        """
        tender_id = state.context.get('tender_id')

        agent = await agent_manager.create_agent(
            agent_type=AgentType.COLLECTOR,
            session_id=state.session_id
        )
        state.agents['collector'] = agent.agent_id

        task = {
            'tender_id': tender_id,
            'tender_title': state.context.get('tender_title'),
            'source_url': state.context.get('source_url')
        }

        result = await agent.run(task)

        if result.success:
            state.context['tender_data'] = result.data.get('collected_info', {})
            state.context['tender_analysis'] = result.data.get('analysis', {})
            state.results['collect'] = result.data

        return {
            'success': result.success,
            'continue': result.success,
            'data': result.data
        }

    async def _stage_match(self, state: WorkflowState) -> Dict[str, Any]:
        """
        企业比对阶段
        """
        agent = await agent_manager.create_agent(
            agent_type=AgentType.PARSER,
            session_id=state.session_id
        )
        state.agents['matcher'] = agent.agent_id

        task = {
            'tender_data': state.context.get('tender_data', {}),
            'enterprise_id': state.context.get('enterprise_id')
        }

        result = await agent.run(task)

        if result.success:
            state.context['enterprise_data'] = result.data.get('enterprise_data', {})
            state.context['match_result'] = result.data.get('match_result', {})
            state.results['match'] = result.data

        return {
            'success': result.success,
            'continue': result.success,
            'data': result.data
        }

    async def _stage_analyze(self, state: WorkflowState) -> Dict[str, Any]:
        """
        投标论证阶段
        """
        agent = await agent_manager.create_agent(
            agent_type=AgentType.GENERATOR,
            session_id=state.session_id
        )
        state.agents['analyst'] = agent.agent_id

        task = {
            'tender_data': state.context.get('tender_data', {}),
            'enterprise_data': state.context.get('enterprise_data', {}),
            'match_result': state.context.get('match_result', {})
        }

        result = await agent.run(task)

        if result.success:
            state.context['analysis'] = result.data.get('analysis', {})
            state.context['recommendation'] = result.data.get('recommendation')
            state.context['recommendation_score'] = result.data.get('recommendation_score', 0)
            state.results['analyze'] = result.data

        return {
            'success': result.success,
            'continue': result.success,
            'data': result.data
        }

    async def _stage_decision(self, state: WorkflowState) -> Dict[str, Any]:
        """
        投标决策阶段
        """
        from apps.openclaw.workflow_models import BidDecision

        recommendation = state.context.get('recommendation', 'pending')
        score = state.context.get('recommendation_score', 0)

        decision = 'proceed' if recommendation == 'participate' and score >= self.DECISION_THRESHOLD else 'skip'

        try:
            BidDecision.objects.create(
                workflow_id=state.context.get('workflow_db_id'),
                decision_type='participate' if decision == 'proceed' else 'skip',
                match_score=state.context.get('match_result', {}).get('match_score', 0),
                match_details=state.context.get('match_result', {}),
                risk_analysis=state.context.get('analysis', {}).get('risks', ''),
                opportunity_analysis=state.context.get('analysis', {}).get('opportunities', ''),
                recommendation=state.context.get('analysis', {}).get('strategy', ''),
                recommendation_score=score,
                reasoning_process=state.context.get('analysis', {}).get('reasoning', ''),
                final_decision=decision
            )
        except Exception as e:
            logger.warning(f"保存决策记录失败: {str(e)}")

        state.context['decision'] = decision
        state.results['decision'] = {
            'decision': decision,
            'recommendation': recommendation,
            'score': score
        }

        return {
            'success': True,
            'continue': decision == 'proceed',
            'data': {
                'decision': decision,
                'reason': f"推荐分数: {score}, 阈值: {self.DECISION_THRESHOLD}"
            }
        }

    async def _stage_generate(self, state: WorkflowState) -> Dict[str, Any]:
        """
        标书制作阶段
        """
        agent = await agent_manager.create_agent(
            agent_type=AgentType.GENERATOR,
            session_id=state.session_id
        )
        state.agents['generator'] = agent.agent_id

        task = {
            'tender_data': state.context.get('tender_data', {}),
            'enterprise_data': state.context.get('enterprise_data', {}),
            'match_result': state.context.get('match_result', {}),
            'template_id': state.context.get('config', {}).get('template_id')
        }

        result = await agent.run(task)

        if result.success:
            state.context['document'] = result.data.get('document', {})
            state.context['sections'] = result.data.get('sections', [])
            state.results['generate'] = result.data

        return {
            'success': result.success,
            'continue': result.success,
            'data': result.data
        }

    async def _stage_review(self, state: WorkflowState) -> Dict[str, Any]:
        """
        标书审核阶段
        """
        agent = await agent_manager.create_agent(
            agent_type=AgentType.ORCHESTRATOR,
            session_id=state.session_id
        )
        state.agents['reviewer'] = agent.agent_id

        task = {
            'tender_data': state.context.get('tender_data', {}),
            'document': state.context.get('document', {}),
            'sections': state.context.get('sections', [])
        }

        result = await agent.run(task)

        if result.success:
            state.context['review_result'] = result.data.get('review_result', {})
            state.context['overall_score'] = result.data.get('overall_score', 0)
            state.context['needs_optimization'] = result.data.get('needs_optimization', False)
            state.results['review'] = result.data

        return {
            'success': result.success,
            'continue': result.success,
            'data': result.data,
            'needs_optimization': result.data.get('needs_optimization', False)
        }

    async def _stage_optimize(self, state: WorkflowState) -> Dict[str, Any]:
        """
        标书优化阶段
        """
        needs_optimization = state.context.get('needs_optimization', False)

        if not needs_optimization:
            return {
                'success': True,
                'continue': True,
                'data': {'message': '标书已达标，无需优化'}
            }

        iteration = state.context.get('optimization_iteration', 0)

        if iteration >= self.MAX_OPTIMIZATION_ITERATIONS:
            return {
                'success': True,
                'continue': True,
                'data': {'message': f'已达到最大优化次数({self.MAX_OPTIMIZATION_ITERATIONS})'}
            }

        optimizer = BidQualityOptimizerAgent(session_id=state.session_id)
        state.agents[f'optimizer_{iteration}'] = optimizer.agent_id

        task = {
            'tender_data': state.context.get('tender_data', {}),
            'document': state.context.get('document', {}),
            'review_result': state.context.get('review_result', {})
        }

        result = await optimizer.run(task)

        if result.success:
            state.context['document'] = result.data.get('optimized_document', {})
            state.context['optimization_iteration'] = iteration + 1

            state.results[f'optimize_{iteration}'] = result.data

            reviewer = BidDocumentReviewerAgent(session_id=state.session_id)
            review_task = {
                'tender_data': state.context.get('tender_data', {}),
                'document': state.context.get('document', {}),
                'sections': state.context.get('document', {}).get('sections', [])
            }
            review_result = await reviewer.run(review_task)

            if review_result.success:
                new_score = review_result.data.get('overall_score', 0)
                state.context['overall_score'] = new_score
                state.context['needs_optimization'] = new_score < self.REVIEW_PASS_THRESHOLD

                if new_score >= self.REVIEW_PASS_THRESHOLD:
                    return {
                        'success': True,
                        'continue': True,
                        'data': {'message': f'优化成功，得分: {new_score}'}
                    }

        return {
            'success': result.success,
            'continue': True,
            'data': result.data
        }

    async def _stage_upload(self, state: WorkflowState) -> Dict[str, Any]:
        """
        标书上传阶段
        """
        document = state.context.get('document', {})

        state.results['upload'] = {
            'status': 'pending',
            'document': document.get('title'),
            'message': '标书待上传'
        }

        return {
            'success': True,
            'continue': True,
            'data': state.results['upload']
        }

    async def _stage_track(self, state: WorkflowState) -> Dict[str, Any]:
        """
        结果跟踪阶段
        """
        agent = BidResultTrackerAgent(session_id=state.session_id)
        state.agents['tracker'] = agent.agent_id

        task = {
            'tender_id': state.context.get('tender_id'),
            'tender_data': state.context.get('tender_data', {}),
            'bid_date': datetime.now().strftime('%Y-%m-%d')
        }

        result = await agent.run(task)

        if result.success:
            state.results['track'] = result.data

        return {
            'success': result.success,
            'continue': False,
            'data': result.data
        }

    async def _send_failure_notification(
        self,
        stage_name: str,
        diagnosis,
        state: WorkflowState
    ):
        """
        发送故障通知
        """
        try:
            from services.dingtalk_service import dingtalk_service

            message = f"""## 🔴 工作流执行异常

**工作流ID**: `{state.workflow_id}`
**招标项目**: `{state.context.get('tender_id')}`
**异常阶段**: `{stage_name}`

---

### 错误诊断

| 项目 | 内容 |
|------|------|
| 错误类型 | `{diagnosis.error_type.value}` |
| 根本原因 | `{diagnosis.root_cause}` |
| 建议方案 | `{diagnosis.solution}` |
| 降级动作 | `{diagnosis.fallback_action.value}` |

---

### 上下文

- Session ID: `{state.session_id}`
- 当前重试次数: `{diagnosis.metadata.get('retry_count', 'N/A')}`

> 此通知由系统自动发送，请及时处理。
"""

            await dingtalk_service.send_markdown(
                title=f"⚠️ 工作流异常: {stage_name}",
                content=message
            )

            logger.info(f"故障通知已发送")

        except Exception as e:
            logger.warning(f"发送故障通知失败: {str(e)}")

    async def _update_workflow_status(self, state: WorkflowState, status: str):
        """
        更新工作流状态
        """
        from apps.openclaw.workflow_models import BidWorkflow

        try:
            workflow = BidWorkflow.objects.filter(
                session_id=state.session_id
            ).first()

            if workflow:
                workflow.status = status
                workflow.current_stage = state.current_stage
                workflow.context = state.context
                workflow.result_summary = str(state.results)

                if status == 'completed':
                    workflow.completed_at = datetime.now()
                elif status == 'running':
                    workflow.started_at = datetime.now()

                workflow.save()

        except Exception as e:
            logger.error(f"更新工作流状态失败: {str(e)}")

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        """
        state = self._workflows.get(workflow_id)

        if state:
            return {
                'workflow_id': state.workflow_id,
                'session_id': state.session_id,
                'status': state.status,
                'current_stage': state.current_stage,
                'context': state.context,
                'results': state.results,
                'errors': state.errors
            }

        return None

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        取消工作流
        """
        state = self._workflows.get(workflow_id)

        if state:
            state.status = 'cancelled'
            await self._update_workflow_status(state, 'cancelled')

            for agent_id in state.agents.values():
                await agent_manager.destroy_agent(agent_id)

            return True

        return False


bid_workflow_orchestrator = BidWorkflowOrchestrator()
