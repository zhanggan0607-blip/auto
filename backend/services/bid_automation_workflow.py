"""
投标自动化工作流系统
实现24小时不间断投标任务执行，由9个专职Agent负责全流程

集成自动错误诊断功能：
- 任务执行失败时自动诊断错误类型和根因
- 根据诊断结果执行降级策略
- 记录失败案例到知识库学习
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """
    任务类型枚举 - 9个专职任务
    """
    TASK_1_QUALIFICATION_MATCH = 'task_1_qualification_match'
    TASK_2_DOWNLOAD_TENDER = 'task_2_download_tender'
    TASK_3_PARSE_TENDER = 'task_3_parse_tender'
    TASK_4_GENERATE_BID = 'task_4_generate_bid'
    TASK_5_REVIEW_BID = 'task_5_review_bid'
    TASK_6_UPLOAD_BID = 'task_6_upload_bid'
    TASK_7_OPTIMIZE_BID = 'task_7_optimize_bid'
    TASK_8_TRACK_PROJECT = 'task_8_track_project'
    TASK_9_NOTIFY_RESULT = 'task_9_notify_result'


class TaskStatus(Enum):
    """
    任务状态枚举
    """
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'
    WAITING_REVIEW = 'waiting_review'


@dataclass
class TaskContext:
    """
    任务上下文数据
    """
    tender_id: Optional[int] = None
    enterprise_id: Optional[int] = None
    workflow_id: Optional[str] = None
    
    tender_data: Dict[str, Any] = field(default_factory=dict)
    enterprise_data: Dict[str, Any] = field(default_factory=dict)
    qualification_requirements: Dict[str, Any] = field(default_factory=dict)
    match_result: Dict[str, Any] = field(default_factory=dict)
    downloaded_files: List[Dict[str, Any]] = field(default_factory=list)
    parsed_content: Dict[str, Any] = field(default_factory=dict)
    scoring_criteria: Dict[str, Any] = field(default_factory=dict)
    generated_document: Dict[str, Any] = field(default_factory=dict)
    review_result: Dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    upload_result: Dict[str, Any] = field(default_factory=dict)
    tracking_data: Dict[str, Any] = field(default_factory=dict)
    notification_result: Dict[str, Any] = field(default_factory=dict)
    
    bid_score: float = 0.0
    iteration_count: int = 0
    error_message: str = ''


@dataclass
class TaskResult:
    """
    任务执行结果
    """
    task_type: TaskType
    status: TaskStatus
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    next_action: str = ''
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class DiagnosisDecision:
    """
    错误诊断决策
    用于工作流执行中错误处理决策
    """
    should_continue: bool
    error_type: str
    root_cause: str
    solution: str
    fallback_action: str
    confidence: float = 0.0
    stage: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'should_continue': self.should_continue,
            'error_type': self.error_type,
            'root_cause': self.root_cause,
            'solution': self.solution,
            'fallback_action': self.fallback_action,
            'confidence': self.confidence,
            'stage': self.stage,
            'metadata': self.metadata
        }


class BidAutomationWorkflow:
    """
    投标自动化工作流
    
    9个专职Agent任务流程：
    1. 资质比对Agent - 访问招标网站，提取报名条件，与企业资质智能比对
    2. 文件下载Agent - 比对通过后，自动下载招标文件及附件
    3. 文件解析Agent - 结构化解析招标文件，提取关键信息和评分标准
    4. 标书生成Agent - 基于解析结果和企业数据，自动生成标书文档
    5. 标书审核Agent - 废标风险检查和模拟打分审核
    6. 标书上传Agent - 90分以上自动完成标书上传
    7. 标书优化Agent - 未达标标书提供修改建议，支持二次审核
    8. 项目跟踪Agent - 投标项目跟踪，每日扫描中标公告
    9. 结果通知Agent - 中标公告匹配，钉钉自动通知
    """
    
    REVIEW_PASS_THRESHOLD = 90
    MAX_OPTIMIZATION_ITERATIONS = 3
    WORKFLOW_TIMEOUT_HOURS = 24
    
    def __init__(self):
        self._workflows: Dict[str, Dict[str, Any]] = {}
        self._task_handlers = {
            TaskType.TASK_1_QUALIFICATION_MATCH: self._task_1_qualification_match,
            TaskType.TASK_2_DOWNLOAD_TENDER: self._task_2_download_tender,
            TaskType.TASK_3_PARSE_TENDER: self._task_3_parse_tender,
            TaskType.TASK_4_GENERATE_BID: self._task_4_generate_bid,
            TaskType.TASK_5_REVIEW_BID: self._task_5_review_bid,
            TaskType.TASK_6_UPLOAD_BID: self._task_6_upload_bid,
            TaskType.TASK_7_OPTIMIZE_BID: self._task_7_optimize_bid,
            TaskType.TASK_8_TRACK_PROJECT: self._task_8_track_project,
            TaskType.TASK_9_NOTIFY_RESULT: self._task_9_notify_result,
        }
    
    async def start_workflow(
        self,
        tender_id: int,
        enterprise_id: int,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        启动投标自动化工作流
        
        Args:
            tender_id: 招标项目ID
            enterprise_id: 企业ID
            config: 工作流配置
            
        Returns:
            dict: 工作流启动结果
        """
        workflow_id = str(uuid.uuid4())
        
        context = TaskContext(
            tender_id=tender_id,
            enterprise_id=enterprise_id,
            workflow_id=workflow_id
        )
        
        workflow_state = {
            'workflow_id': workflow_id,
            'status': TaskStatus.PENDING.value,
            'current_task': None,
            'completed_tasks': [],
            'context': context,
            'results': {},
            'logs': [],
            'created_at': timezone.now(),
            'started_at': None,
            'completed_at': None,
            'config': config or {}
        }
        
        self._workflows[workflow_id] = workflow_state
        
        try:
            await self._create_workflow_record(workflow_state)
            
            import asyncio
            asyncio.create_task(self._run_workflow(workflow_id))
            
            return {
                'workflow_id': workflow_id,
                'status': 'started',
                'message': '投标自动化工作流已启动',
                'tender_id': tender_id,
                'enterprise_id': enterprise_id
            }
            
        except Exception as e:
            logger.error(f"启动工作流失败: {str(e)}")
            workflow_state['status'] = TaskStatus.FAILED.value
            workflow_state['error'] = str(e)
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def _create_workflow_record(self, workflow_state: Dict[str, Any]):
        """
        创建工作流数据库记录
        """
        try:
            from apps.openclaw.workflow_models import BidWorkflow
            
            workflow = BidWorkflow.objects.create(
                name=f"投标自动化-{workflow_state['workflow_id'][:8]}",
                tender_id=workflow_state['context'].tender_id,
                session_id=workflow_state['workflow_id'],
                status='pending',
                context={
                    'enterprise_id': workflow_state['context'].enterprise_id,
                    'config': workflow_state.get('config', {})
                }
            )
            workflow_state['db_id'] = workflow.id
        except Exception as e:
            logger.warning(f"创建工作流记录失败: {str(e)}")
    
    async def _run_workflow(self, workflow_id: str):
        """
        运行工作流主循环
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow['status'] = TaskStatus.RUNNING.value
        workflow['started_at'] = timezone.now()
        
        task_sequence = [
            TaskType.TASK_1_QUALIFICATION_MATCH,
            TaskType.TASK_2_DOWNLOAD_TENDER,
            TaskType.TASK_3_PARSE_TENDER,
            TaskType.TASK_4_GENERATE_BID,
            TaskType.TASK_5_REVIEW_BID,
        ]
        
        try:
            for task_type in task_sequence:
                workflow['current_task'] = task_type.value
                self._log_task(workflow, f"开始执行任务: {task_type.value}")
                
                result = await self._execute_task(workflow, task_type)
                workflow['results'][task_type.value] = {
                    'status': result.status.value,
                    'success': result.success,
                    'message': result.message,
                    'data': result.data,
                    'completed_at': result.completed_at.isoformat() if result.completed_at else None
                }
                
                if result.status == TaskStatus.COMPLETED:
                    workflow['completed_tasks'].append(task_type.value)
                    self._log_task(workflow, f"任务完成: {task_type.value} - {result.message}")
                elif result.status == TaskStatus.SKIPPED:
                    self._log_task(workflow, f"任务跳过: {task_type.value} - {result.message}")
                    break
                elif result.status == TaskStatus.FAILED:
                    workflow['status'] = TaskStatus.FAILED.value
                    workflow['error'] = result.error
                    self._log_task(workflow, f"任务失败: {task_type.value} - {result.error}")
                    break
                elif result.status == TaskStatus.WAITING_REVIEW:
                    workflow['status'] = TaskStatus.WAITING_REVIEW.value
                    self._log_task(workflow, f"等待人工审核: {result.message}")
                    break
            
            if workflow['status'] == TaskStatus.RUNNING.value:
                workflow['status'] = TaskStatus.COMPLETED.value
            
            workflow['completed_at'] = timezone.now()
            await self._update_workflow_record(workflow)
            
        except Exception as e:
            logger.error(f"工作流执行异常: {str(e)}")
            workflow['status'] = TaskStatus.FAILED.value
            workflow['error'] = str(e)
            self._log_task(workflow, f"工作流异常: {str(e)}")
    
    async def _execute_task(
        self,
        workflow: Dict[str, Any],
        task_type: TaskType
    ) -> TaskResult:
        """
        执行单个任务（集成错误诊断）
        """
        handler = self._task_handlers.get(task_type)
        if not handler:
            return TaskResult(
                task_type=task_type,
                status=TaskStatus.FAILED,
                success=False,
                message='任务处理器未找到',
                error='Handler not found'
            )

        started_at = timezone.now()
        workflow_id = workflow.get('workflow_id', '')
        stage_name = task_type.value

        try:
            result = await handler(workflow['context'])
            result.started_at = started_at
            result.completed_at = timezone.now()

            if result.success:
                self._log_task(workflow, f"任务成功: {stage_name}")

            return result

        except Exception as e:
            logger.error(f"任务执行异常 {stage_name}: {str(e)}")

            diagnosis = await self._diagnose_and_handle_error(
                error=e,
                stage=stage_name,
                workflow_id=workflow_id,
                workflow=workflow
            )

            if diagnosis.should_continue:
                self._log_task(workflow, f"任务异常但继续: {stage_name} - {diagnosis.fallback_action}")
                return TaskResult(
                    task_type=task_type,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message=f'异常已自动处理: {diagnosis.root_cause}，使用{diagnosis.fallback_action}继续',
                    data={'diagnosis': diagnosis.to_dict(), 'original_error': str(e)}
                )
            else:
                self._log_task(workflow, f"任务失败需人工处理: {stage_name} - {diagnosis.root_cause}")
                return TaskResult(
                    task_type=task_type,
                    status=TaskStatus.FAILED,
                    success=False,
                    message=f'任务执行异常: {diagnosis.root_cause}',
                    error=str(e),
                    started_at=started_at,
                    completed_at=timezone.now()
                )

    async def _diagnose_and_handle_error(
        self,
        error: Exception,
        stage: str,
        workflow_id: str,
        workflow: Dict[str, Any]
    ) -> 'DiagnosisDecision':
        """
        诊断错误并决定处理方式

        Returns:
            DiagnosisDecision: 包含是否继续、使用的降级动作等信息
        """
        try:
            from services.error_diagnoser import error_diagnoser, FallbackAction
            from services.failure_knowledge_base import failure_knowledge_base

            diagnosis = error_diagnoser.diagnose(error, stage, {
                'workflow_id': workflow_id,
                'tender_id': workflow.get('context', {}).get('tender_id')
            })

            failure_knowledge_base.record_failure(
                error_type=diagnosis.error_type_name,
                error_message=str(error)[:500],
                stage=stage,
                root_cause=diagnosis.root_cause,
                solution=diagnosis.solution,
                workflow_id=workflow_id
            )

            should_continue = diagnosis.fallback_action in [
                FallbackAction.RETRY,
                FallbackAction.RETRY_WITH_BACKUP,
                FallbackAction.SKIP_AND_CONTINUE,
                FallbackAction.USE_PARTIAL_DATA,
                FallbackAction.USE_DEFAULT_VALUE,
            ]

            return DiagnosisDecision(
                should_continue=should_continue,
                error_type=diagnosis.error_type_name,
                root_cause=diagnosis.root_cause,
                solution=diagnosis.solution,
                fallback_action=diagnosis.fallback_action.value,
                confidence=diagnosis.confidence,
                stage=stage
            )

        except ImportError as ie:
            logger.warning(f"错误诊断模块导入失败: {ie}")
            return DiagnosisDecision(
                should_continue=False,
                error_type='import_error',
                root_cause=str(ie),
                solution='错误诊断模块不可用',
                fallback_action='abort',
                confidence=0.0,
                stage=stage
            )
        except Exception as diag_error:
            logger.error(f"错误诊断过程出错: {diag_error}")
            return DiagnosisDecision(
                should_continue=False,
                error_type='diagnosis_error',
                root_cause=str(diag_error),
                solution='错误诊断失败，请人工检查',
                fallback_action='abort',
                confidence=0.0,
                stage=stage
            )
    
    async def _task_1_qualification_match(self, ctx: TaskContext) -> TaskResult:
        """
        任务1: 资质比对Agent
        访问招标网站，提取报名条件，与企业资质智能比对
        """
        from apps.tenders.models import TenderProject
        from apps.enterprise.models import Enterprise
        from services.qualification_matcher import QualificationMatcher
        
        try:
            tender = TenderProject.objects.get(pk=ctx.tender_id)
            enterprise = Enterprise.objects.get(pk=ctx.enterprise_id)
            
            ctx.tender_data = {
                'id': tender.id,
                'title': tender.title,
                'source_url': tender.source_url,
                'content': tender.description,
                'requirements': tender.requirements or {}
            }
            
            ctx.enterprise_data = {
                'id': enterprise.id,
                'name': enterprise.name,
                'credit_code': enterprise.credit_code,
                'enterprise_type': enterprise.enterprise_type,
                'qualifications': list(enterprise.qualifications.values(
                    'id', 'qualification_name', 'qualification_category',
                    'grade', 'certificate_no', 'expiry_date'
                )),
                'performances': list(enterprise.performances.values(
                    'id', 'project_name', 'contract_amount',
                    'completion_date', 'project_type'
                )[:10])
            }
            
            matcher = QualificationMatcher()
            match_result = await matcher.match(
                tender_requirements=ctx.tender_data.get('requirements', {}),
                enterprise_data=ctx.enterprise_data
            )
            
            ctx.match_result = match_result
            
            if match_result.get('is_qualified', False):
                return TaskResult(
                    task_type=TaskType.TASK_1_QUALIFICATION_MATCH,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message=f"资质比对通过，匹配度: {match_result.get('score', 0):.1f}%",
                    data=match_result,
                    next_action='download_tender'
                )
            else:
                return TaskResult(
                    task_type=TaskType.TASK_1_QUALIFICATION_MATCH,
                    status=TaskStatus.SKIPPED,
                    success=False,
                    message=f"资质比对未通过: {match_result.get('reason', '不符合要求')}",
                    data=match_result
                )
                
        except TenderProject.DoesNotExist:
            return TaskResult(
                task_type=TaskType.TASK_1_QUALIFICATION_MATCH,
                status=TaskStatus.FAILED,
                success=False,
                message='招标项目不存在',
                error='TenderProject not found'
            )
        except Enterprise.DoesNotExist:
            return TaskResult(
                task_type=TaskType.TASK_1_QUALIFICATION_MATCH,
                status=TaskStatus.FAILED,
                success=False,
                message='企业不存在',
                error='Enterprise not found'
            )
    
    async def _task_2_download_tender(self, ctx: TaskContext) -> TaskResult:
        """
        任务2: 文件下载Agent
        自动下载招标文件及相关附件
        """
        from apps.tenders.models import TenderProject, TenderFile
        from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
        
        try:
            tender = TenderProject.objects.get(pk=ctx.tender_id)
            source_url = ctx.tender_data.get('source_url') or tender.source_url
            
            if not source_url:
                return TaskResult(
                    task_type=TaskType.TASK_2_DOWNLOAD_TENDER,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message='无下载链接，跳过下载步骤',
                    data={'files': []}
                )
            
            crawler = ShanghaiGovCrawler()
            download_result = await crawler.download_tender_files(
                url=source_url,
                tender_id=ctx.tender_id
            )
            
            downloaded_files = download_result.get('files', [])
            ctx.downloaded_files = downloaded_files
            
            for file_info in downloaded_files:
                TenderFile.objects.get_or_create(
                    tender=tender,
                    file_name=file_info.get('name'),
                    defaults={
                        'file_path': file_info.get('path'),
                        'file_type': file_info.get('type', 'unknown'),
                        'file_size': file_info.get('size', 0)
                    }
                )
            
            return TaskResult(
                task_type=TaskType.TASK_2_DOWNLOAD_TENDER,
                status=TaskStatus.COMPLETED,
                success=True,
                message=f"成功下载 {len(downloaded_files)} 个文件",
                data={'files': downloaded_files, 'source_url': source_url},
                next_action='parse_tender'
            )
            
        except Exception as e:
            logger.error(f"下载招标文件失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_2_DOWNLOAD_TENDER,
                status=TaskStatus.COMPLETED,
                success=True,
                message=f'下载失败但继续执行: {str(e)}',
                data={'error': str(e)}
            )
    
    async def _task_3_parse_tender(self, ctx: TaskContext) -> TaskResult:
        """
        任务3: 文件解析Agent
        结构化解析招标文件，提取关键信息和评分标准
        """
        from openclaw.skills.parser.tender_document_parser import TenderDocumentParserSkill
        
        try:
            parser = TenderDocumentParserSkill()
            
            files_to_parse = ctx.downloaded_files
            if not files_to_parse:
                files_to_parse = [{'content': ctx.tender_data.get('content', '')}]
            
            parsed_results = []
            for file_info in files_to_parse:
                try:
                    result = await parser.execute({
                        'file_path': file_info.get('path'),
                        'content': file_info.get('content'),
                        'tender_id': ctx.tender_id
                    })
                    if result.get('success'):
                        parsed_results.append(result.get('data', {}))
                except Exception as e:
                    logger.warning(f"解析文件失败: {str(e)}")
            
            if parsed_results:
                merged_content = self._merge_parsed_results(parsed_results)
                ctx.parsed_content = merged_content
                ctx.scoring_criteria = merged_content.get('scoring_criteria', {})
                ctx.qualification_requirements = merged_content.get('qualification_requirements', {})
                
                return TaskResult(
                    task_type=TaskType.TASK_3_PARSE_TENDER,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message='招标文件解析完成',
                    data={
                        'parsed_content': ctx.parsed_content,
                        'scoring_criteria': ctx.scoring_criteria,
                        'requirements': ctx.qualification_requirements
                    },
                    next_action='generate_bid'
                )
            else:
                return TaskResult(
                    task_type=TaskType.TASK_3_PARSE_TENDER,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message='使用原始内容继续',
                    data={'message': '无解析结果，使用原始内容'}
                )
                
        except Exception as e:
            logger.error(f"解析招标文件失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_3_PARSE_TENDER,
                status=TaskStatus.COMPLETED,
                success=True,
                message=f'解析失败但继续: {str(e)}',
                data={'error': str(e)}
            )
    
    async def _task_4_generate_bid(self, ctx: TaskContext) -> TaskResult:
        """
        任务4: 标书生成Agent
        基于解析结果和企业数据，自动生成标书文档
        """
        from openclaw.skills.generator.bid_document_generator import BidDocumentGeneratorSkill
        from apps.documents.models import GeneratedDocument
        
        try:
            generator = BidDocumentGeneratorSkill()
            
            generate_result = await generator.execute({
                'tender_id': ctx.tender_id,
                'enterprise_id': ctx.enterprise_id,
                'tender_data': ctx.tender_data,
                'enterprise_data': ctx.enterprise_data,
                'parsed_content': ctx.parsed_content,
                'scoring_criteria': ctx.scoring_criteria
            })
            
            if generate_result.get('success'):
                document_data = generate_result.get('data', {})
                ctx.generated_document = document_data
                
                return TaskResult(
                    task_type=TaskType.TASK_4_GENERATE_BID,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message='标书文档生成完成',
                    data=document_data,
                    next_action='review_bid'
                )
            else:
                return TaskResult(
                    task_type=TaskType.TASK_4_GENERATE_BID,
                    status=TaskStatus.FAILED,
                    success=False,
                    message=generate_result.get('message', '标书生成失败'),
                    error=generate_result.get('error')
                )
                
        except Exception as e:
            logger.error(f"生成标书失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_4_GENERATE_BID,
                status=TaskStatus.FAILED,
                success=False,
                message='标书生成异常',
                error=str(e)
            )
    
    async def _task_5_review_bid(self, ctx: TaskContext) -> TaskResult:
        """
        任务5: 标书审核Agent
        废标风险检查和模拟打分审核
        """
        from openclaw.agents.bid_document_agents import BidDocumentReviewerAgent
        
        try:
            reviewer = BidDocumentReviewerAgent(session_id=ctx.workflow_id)
            
            review_result = await reviewer.run({
                'tender_data': ctx.tender_data,
                'document': ctx.generated_document,
                'scoring_criteria': ctx.scoring_criteria,
                'enterprise_data': ctx.enterprise_data
            })
            
            if review_result.success:
                result_data = review_result.data
                ctx.review_result = result_data
                ctx.bid_score = result_data.get('overall_score', 0)
                
                risk_issues = result_data.get('risk_issues', [])
                if risk_issues:
                    ctx.optimization_suggestions = result_data.get('suggestions', [])
                
                if ctx.bid_score >= self.REVIEW_PASS_THRESHOLD:
                    return TaskResult(
                        task_type=TaskType.TASK_5_REVIEW_BID,
                        status=TaskStatus.COMPLETED,
                        success=True,
                        message=f"审核通过，得分: {ctx.bid_score}分",
                        data=result_data,
                        next_action='upload_bid'
                    )
                else:
                    return TaskResult(
                        task_type=TaskType.TASK_5_REVIEW_BID,
                        status=TaskStatus.WAITING_REVIEW,
                        success=True,
                        message=f"得分{ctx.bid_score}分，需要优化至{self.REVIEW_PASS_THRESHOLD}分以上",
                        data=result_data,
                        next_action='optimize_bid'
                    )
            else:
                return TaskResult(
                    task_type=TaskType.TASK_5_REVIEW_BID,
                    status=TaskStatus.FAILED,
                    success=False,
                    message='标书审核失败',
                    error=review_result.error
                )
                
        except Exception as e:
            logger.error(f"审核标书失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_5_REVIEW_BID,
                status=TaskStatus.FAILED,
                success=False,
                message='标书审核异常',
                error=str(e)
            )
    
    async def _task_6_upload_bid(self, ctx: TaskContext) -> TaskResult:
        """
        任务6: 标书上传Agent
        90分以上自动完成标书上传
        """
        from openclaw.skills.uploader.bid_submission import BidSubmissionSkill
        
        try:
            if ctx.bid_score < self.REVIEW_PASS_THRESHOLD:
                return TaskResult(
                    task_type=TaskType.TASK_6_UPLOAD_BID,
                    status=TaskStatus.SKIPPED,
                    success=False,
                    message=f"得分{ctx.bid_score}分，未达到{self.REVIEW_PASS_THRESHOLD}分上传阈值",
                    next_action='optimize_bid'
                )
            
            uploader = BidSubmissionSkill()
            
            upload_result = await uploader.execute({
                'tender_id': ctx.tender_id,
                'enterprise_id': ctx.enterprise_id,
                'document': ctx.generated_document,
                'submit_url': ctx.tender_data.get('submit_url')
            })
            
            if upload_result.get('success'):
                ctx.upload_result = upload_result.get('data', {})
                
                return TaskResult(
                    task_type=TaskType.TASK_6_UPLOAD_BID,
                    status=TaskStatus.COMPLETED,
                    success=True,
                    message='标书上传成功',
                    data=ctx.upload_result,
                    next_action='track_project'
                )
            else:
                return TaskResult(
                    task_type=TaskType.TASK_6_UPLOAD_BID,
                    status=TaskStatus.FAILED,
                    success=False,
                    message=upload_result.get('message', '标书上传失败'),
                    error=upload_result.get('error')
                )
                
        except Exception as e:
            logger.error(f"上传标书失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_6_UPLOAD_BID,
                status=TaskStatus.FAILED,
                success=False,
                message='标书上传异常',
                error=str(e)
            )
    
    async def _task_7_optimize_bid(self, ctx: TaskContext) -> TaskResult:
        """
        任务7: 标书优化Agent
        未达标标书提供修改建议，支持二次审核
        """
        from openclaw.agents.bid_tracker_agents import BidQualityOptimizerAgent
        
        try:
            if ctx.iteration_count >= self.MAX_OPTIMIZATION_ITERATIONS:
                return TaskResult(
                    task_type=TaskType.TASK_7_OPTIMIZE_BID,
                    status=TaskStatus.WAITING_REVIEW,
                    success=False,
                    message=f"已达到最大优化次数({self.MAX_OPTIMIZATION_ITERATIONS})，需要人工审核",
                    data={'suggestions': ctx.optimization_suggestions}
                )
            
            optimizer = BidQualityOptimizerAgent(session_id=ctx.workflow_id)
            
            optimize_result = await optimizer.run({
                'tender_data': ctx.tender_data,
                'document': ctx.generated_document,
                'review_result': ctx.review_result,
                'scoring_criteria': ctx.scoring_criteria
            })
            
            if optimize_result.success:
                ctx.generated_document = optimize_result.data.get('optimized_document', ctx.generated_document)
                ctx.optimization_suggestions = optimize_result.data.get('applied_suggestions', [])
                ctx.iteration_count += 1
                
                reviewer_result = await self._task_5_review_bid(ctx)
                ctx.bid_score = reviewer_result.data.get('overall_score', ctx.bid_score)
                
                if ctx.bid_score >= self.REVIEW_PASS_THRESHOLD:
                    return TaskResult(
                        task_type=TaskType.TASK_7_OPTIMIZE_BID,
                        status=TaskStatus.COMPLETED,
                        success=True,
                        message=f"优化成功，得分: {ctx.bid_score}分",
                        data={
                            'iteration': ctx.iteration_count,
                            'score': ctx.bid_score,
                            'suggestions': ctx.optimization_suggestions
                        },
                        next_action='upload_bid'
                    )
                else:
                    return TaskResult(
                        task_type=TaskType.TASK_7_OPTIMIZE_BID,
                        status=TaskStatus.WAITING_REVIEW,
                        success=True,
                        message=f"优化后得分{ctx.bid_score}分，需要继续优化或人工审核",
                        data={
                            'iteration': ctx.iteration_count,
                            'score': ctx.bid_score,
                            'suggestions': ctx.optimization_suggestions
                        }
                    )
            else:
                return TaskResult(
                    task_type=TaskType.TASK_7_OPTIMIZE_BID,
                    status=TaskStatus.FAILED,
                    success=False,
                    message='标书优化失败',
                    error=optimize_result.error
                )
                
        except Exception as e:
            logger.error(f"优化标书失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_7_OPTIMIZE_BID,
                status=TaskStatus.FAILED,
                success=False,
                message='标书优化异常',
                error=str(e)
            )
    
    async def _task_8_track_project(self, ctx: TaskContext) -> TaskResult:
        """
        任务8: 项目跟踪Agent
        投标项目跟踪，每日扫描中标公告
        """
        from apps.crawler.models import BidProjectTracking
        
        try:
            tracking, created = BidProjectTracking.objects.get_or_create(
                tender_id=ctx.tender_id,
                defaults={
                    'enterprise_id': ctx.enterprise_id,
                    'bid_date': timezone.now().date(),
                    'status': 'submitted',
                    'tracking_config': {
                        'workflow_id': ctx.workflow_id,
                        'bid_score': ctx.bid_score
                    }
                }
            )
            
            ctx.tracking_data = {
                'tracking_id': tracking.id,
                'status': tracking.status,
                'bid_date': tracking.bid_date.isoformat() if tracking.bid_date else None
            }
            
            return TaskResult(
                task_type=TaskType.TASK_8_TRACK_PROJECT,
                status=TaskStatus.COMPLETED,
                success=True,
                message='项目跟踪已建立',
                data=ctx.tracking_data,
                next_action='notify_result'
            )
            
        except Exception as e:
            logger.error(f"建立项目跟踪失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_8_TRACK_PROJECT,
                status=TaskStatus.COMPLETED,
                success=True,
                message=f'跟踪建立失败但继续: {str(e)}',
                data={'error': str(e)}
            )
    
    async def _task_9_notify_result(self, ctx: TaskContext) -> TaskResult:
        """
        任务9: 结果通知Agent
        中标公告匹配，钉钉自动通知
        """
        from services.dingtalk_service import DingtalkService
        
        try:
            notification_result = {
                'notified': False,
                'channels': [],
                'message': ''
            }
            
            enterprise_name = ctx.enterprise_data.get('name', '')
            tender_title = ctx.tender_data.get('title', '')
            
            message = f"""【投标任务完成通知】
项目名称: {tender_title}
投标企业: {enterprise_name}
模拟得分: {ctx.bid_score}分
工作流ID: {ctx.workflow_id[:8]}
状态: {'已上传' if ctx.upload_result else '待处理'}
"""
            
            try:
                dingtalk = DingtalkService()
                notify_result = await dingtalk.send_message(message)
                if notify_result.get('success'):
                    notification_result['notified'] = True
                    notification_result['channels'].append('dingtalk')
                    notification_result['message'] = '钉钉通知发送成功'
            except Exception as e:
                logger.warning(f"钉钉通知发送失败: {str(e)}")
                notification_result['message'] = f'通知发送失败: {str(e)}'
            
            ctx.notification_result = notification_result
            
            return TaskResult(
                task_type=TaskType.TASK_9_NOTIFY_RESULT,
                status=TaskStatus.COMPLETED,
                success=True,
                message='工作流完成，通知已发送',
                data=notification_result
            )
            
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
            return TaskResult(
                task_type=TaskType.TASK_9_NOTIFY_RESULT,
                status=TaskStatus.COMPLETED,
                success=True,
                message=f'通知失败但工作流已完成: {str(e)}',
                data={'error': str(e)}
            )
    
    def _merge_parsed_results(self, results: List[Dict]) -> Dict:
        """
        合并多个解析结果
        """
        merged = {
            'title': '',
            'requirements': {},
            'scoring_criteria': {},
            'qualification_requirements': {},
            'key_dates': {},
            'contact_info': {},
            'sections': []
        }
        
        for result in results:
            for key in merged.keys():
                if key in result and result[key]:
                    if isinstance(merged[key], dict):
                        merged[key].update(result[key])
                    elif isinstance(merged[key], list):
                        merged[key].extend(result[key] if isinstance(result[key], list) else [result[key]])
                    elif not merged[key]:
                        merged[key] = result[key]
        
        return merged
    
    def _log_task(self, workflow: Dict[str, Any], message: str):
        """
        记录任务日志
        """
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'message': message
        }
        workflow['logs'].append(log_entry)
        logger.info(f"[Workflow {workflow['workflow_id'][:8]}] {message}")
    
    async def _update_workflow_record(self, workflow: Dict[str, Any]):
        """
        更新工作流数据库记录
        """
        try:
            from apps.openclaw.workflow_models import BidWorkflow
            
            db_id = workflow.get('db_id')
            if db_id:
                BidWorkflow.objects.filter(pk=db_id).update(
                    status=workflow['status'],
                    current_stage=workflow.get('current_task', ''),
                    context={
                        'enterprise_id': workflow['context'].enterprise_id,
                        'bid_score': workflow['context'].bid_score,
                        'iteration_count': workflow['context'].iteration_count,
                        'results': workflow['results']
                    },
                    result_summary=str(workflow['results'])
                )
        except Exception as e:
            logger.warning(f"更新工作流记录失败: {str(e)}")
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        """
        workflow = self._workflows.get(workflow_id)
        if workflow:
            return {
                'workflow_id': workflow['workflow_id'],
                'status': workflow['status'],
                'current_task': workflow.get('current_task'),
                'completed_tasks': workflow['completed_tasks'],
                'bid_score': workflow['context'].bid_score,
                'iteration_count': workflow['context'].iteration_count,
                'created_at': workflow['created_at'].isoformat() if workflow.get('created_at') else None,
                'started_at': workflow['started_at'].isoformat() if workflow.get('started_at') else None,
                'completed_at': workflow['completed_at'].isoformat() if workflow.get('completed_at') else None,
                'logs': workflow['logs'][-20:]
            }
        return None
    
    async def resume_workflow(self, workflow_id: str, action: str = 'continue') -> Dict[str, Any]:
        """
        恢复暂停的工作流
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {'error': '工作流不存在'}
        
        if workflow['status'] not in [TaskStatus.WAITING_REVIEW.value]:
            return {'error': '工作流不在等待状态'}
        
        if action == 'continue':
            workflow['status'] = TaskStatus.RUNNING.value
            
            if workflow['context'].bid_score < self.REVIEW_PASS_THRESHOLD:
                import asyncio
                asyncio.create_task(self._continue_from_optimize(workflow))
            else:
                import asyncio
                asyncio.create_task(self._continue_from_upload(workflow))
            
            return {'status': 'resumed', 'message': '工作流已恢复'}
        elif action == 'cancel':
            workflow['status'] = TaskStatus.FAILED.value
            return {'status': 'cancelled', 'message': '工作流已取消'}
        
        return {'error': '未知操作'}
    
    async def _continue_from_optimize(self, workflow: Dict[str, Any]):
        """
        从优化阶段继续
        """
        result = await self._task_7_optimize_bid(workflow['context'])
        workflow['results'][TaskType.TASK_7_OPTIMIZE_BID.value] = {
            'status': result.status.value,
            'success': result.success,
            'message': result.message
        }
        
        if result.status == TaskStatus.COMPLETED and result.success:
            upload_result = await self._task_6_upload_bid(workflow['context'])
            if upload_result.status == TaskStatus.COMPLETED:
                await self._task_8_track_project(workflow['context'])
                await self._task_9_notify_result(workflow['context'])
        
        workflow['status'] = TaskStatus.COMPLETED.value
        workflow['completed_at'] = timezone.now()
    
    async def _continue_from_upload(self, workflow: Dict[str, Any]):
        """
        从上传阶段继续
        """
        await self._task_6_upload_bid(workflow['context'])
        await self._task_8_track_project(workflow['context'])
        await self._task_9_notify_result(workflow['context'])
        
        workflow['status'] = TaskStatus.COMPLETED.value
        workflow['completed_at'] = timezone.now()


bid_automation_workflow = BidAutomationWorkflow()
