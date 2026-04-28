"""
一键自动化投标服务
操作员只需输入企业资料和指定网站，系统自动完成全流程
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from django.conf import settings
from django.utils import timezone

from openclaw.agents.bid_workflow_orchestrator import bid_workflow_orchestrator
from services.unified_llm_service import unified_llm_service
from services.enterprise_matching_engine import enterprise_matching_engine
from services.dingtalk_service import bid_result_notification_service


logger = logging.getLogger(__name__)


@dataclass
class AutomationConfig:
    """
    自动化配置
    """
    enterprise_id: int
    website_ids: List[int]
    keywords: List[str] = field(default_factory=list)
    auto_bid_threshold: int = 60
    auto_document_threshold: int = 90
    max_concurrent_tasks: int = 5
    notification_enabled: bool = True
    auto_upload: bool = False


@dataclass
class AutomationTask:
    """
    自动化任务
    """
    task_id: str
    config: AutomationConfig
    status: str = 'pending'
    current_step: str = ''
    progress: int = 0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None


class OneClickAutomationService:
    """
    一键自动化投标服务
    实现从采集到投标的全自动流程
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._tasks: Dict[str, AutomationTask] = {}
        self._running = False

    def start_automation(
        self,
        enterprise_id: int,
        website_ids: List[int] = None,
        keywords: List[str] = None,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        一键启动自动化投标流程

        Args:
            enterprise_id: 企业ID
            website_ids: 指定网站ID列表（为空则使用所有启用的网站）
            keywords: 搜索关键词
            config: 其他配置

        Returns:
            dict: 任务信息
        """
        import threading

        task_id = str(uuid.uuid4())

        automation_config = AutomationConfig(
            enterprise_id=enterprise_id,
            website_ids=website_ids or [],
            keywords=keywords or [],
            auto_bid_threshold=config.get('auto_bid_threshold', 60),
            auto_document_threshold=config.get('auto_document_threshold', 90),
            max_concurrent_tasks=config.get('max_concurrent_tasks', 5),
            notification_enabled=config.get('notification_enabled', True),
            auto_upload=config.get('auto_upload', False)
        )

        task = AutomationTask(
            task_id=task_id,
            config=automation_config
        )

        self._tasks[task_id] = task

        def run_async_automation():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_automation(task))
            finally:
                loop.close()

        thread = threading.Thread(target=run_async_automation, daemon=True)
        thread.start()

        return {
            'task_id': task_id,
            'status': 'started',
            'message': '自动化任务已启动',
            'enterprise_id': enterprise_id,
            'websites': len(website_ids) if website_ids else 'all'
        }

    async def _run_automation(self, task: AutomationTask):
        """
        运行自动化流程
        """
        try:
            task.status = 'running'
            task.started_at = datetime.now()
            logger.info(f"自动化任务 {task.task_id} 开始执行")

            task.current_step = 'collecting'
            task.progress = 10
            tenders = await self._step_collect_tenders(task)

            if not tenders:
                task.status = 'completed'
                task.results['message'] = '未找到符合条件的招标项目'
                return

            task.current_step = 'matching'
            task.progress = 30
            matched_tenders = await self._step_match_tenders(task, tenders)

            if not matched_tenders:
                task.status = 'completed'
                task.results['message'] = '未找到匹配的招标项目'
                return

            task.current_step = 'analyzing'
            task.progress = 50
            bid_decisions = await self._step_analyze_and_decide(task, matched_tenders)

            task.current_step = 'generating'
            task.progress = 70
            documents = await self._step_generate_documents(task, bid_decisions)

            task.current_step = 'reviewing'
            task.progress = 85
            reviewed_docs = await self._step_review_and_optimize(task, documents)

            task.current_step = 'uploading'
            task.progress = 95
            await self._step_upload_documents(task, reviewed_docs)

            task.status = 'completed'
            task.completed_at = datetime.now()
            task.progress = 100
            task.current_step = 'completed'

            if task.config.notification_enabled:
                await self._send_completion_notification(task)

            logger.info(f"自动化任务 {task.task_id} 完成")

        except Exception as e:
            logger.error(f"自动化任务执行失败: {str(e)}")
            task.status = 'failed'
            task.errors.append(str(e))
            task.completed_at = datetime.now()

    async def _step_collect_tenders(self, task: AutomationTask) -> List[Dict[str, Any]]:
        """
        步骤1：自动采集招标信息
        """
        from apps.tenders.models import TenderSource, TenderProject
        from apps.crawler.models import WebsiteTemplate

        tenders = []

        try:
            if task.config.website_ids:
                websites = WebsiteTemplate.objects.filter(
                    id__in=task.config.website_ids,
                    is_active=True
                )
            else:
                websites = WebsiteTemplate.objects.filter(is_active=True)

            for website in websites:
                try:
                    crawled_data = await self._crawl_website(website, task.config.keywords)

                    for item in crawled_data:
                        tender, created = TenderProject.objects.get_or_create(
                            project_code=item.get('project_code', ''),
                            defaults={
                                'title': item.get('title'),
                                'source_url': item.get('source_url'),
                                'publish_date': item.get('publish_date'),
                                'deadline_date': item.get('deadline_date'),
                                'region': item.get('region'),
                                'industry': item.get('industry'),
                                'budget': item.get('budget'),
                                'description': item.get('description'),
                                'requirements': item.get('requirements'),
                                'purchaser_name': item.get('purchaser_name'),
                                'status': 'pending'
                            }
                        )
                        if created:
                            tenders.append({
                                'id': tender.id,
                                'title': tender.title,
                                'budget': str(tender.budget) if tender.budget else None,
                                'deadline': str(tender.deadline_date) if tender.deadline_date else None,
                                'source': website.name
                            })

                except Exception as e:
                    logger.warning(f"采集网站 {website.name} 失败: {str(e)}")
                    continue

            task.results['collected_tenders'] = tenders
            task.results['collected_count'] = len(tenders)

        except Exception as e:
            logger.error(f"采集招标信息失败: {str(e)}")
            task.errors.append(f"采集失败: {str(e)}")

        return tenders

    async def _crawl_website(
        self,
        website: Any,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        爬取网站招标信息 - 统一使用 skill_registry
        """
        from openclaw.skill_registry import skill_registry

        website_code = getattr(website, 'code', '') or ''
        website_type = getattr(website, 'website_type', '') or ''

        from crawler.crawl_source_registry import crawl_source_registry

        if crawl_source_registry.is_registered(website_code) or website_type == 'government':
            source = crawl_source_registry.resolve_source(website_code)

            try:
                result = await skill_registry.execute_skill(
                    'government_tender_collector',
                    source=source,
                    keywords=keywords,
                    notice_types=['gkzb', 'jzxcs', 'jzxtp', 'xjcg'],
                    page=1,
                    page_size=20
                )

                if result.success and result.data:
                    logger.info(f"通过 skill_registry 成功采集 {website.name}，获取 {len(result.data)} 条数据")
                    return result.data
                else:
                    logger.warning(f"skill_registry 采集 {website.name} 返回空结果: {result.error}")
                    return []

            except Exception as e:
                logger.error(f"skill_registry 采集 {website.name} 失败: {str(e)}")
                return []
        else:
            from crawler.configurable_crawler import ConfigurableCrawler

            try:
                crawler = ConfigurableCrawler(website)
                loop = asyncio.get_running_loop()
                results = await loop.run_in_executor(None, lambda: crawler.crawl(keywords=keywords))
                return results
            except Exception as e:
                logger.error(f"ConfigurableCrawler 爬取 {website.name} 失败: {str(e)}")
                return []

    async def _step_match_tenders(
        self,
        task: AutomationTask,
        tenders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        步骤2：自动匹配招标项目
        """
        from apps.enterprise.models import Enterprise

        matched_tenders = []

        try:
            enterprise = Enterprise.objects.get(id=task.config.enterprise_id)

            for tender in tenders:
                try:
                    tender_data = {
                        'id': tender['id'],
                        'title': tender.get('title'),
                        'description': tender.get('description'),
                        'requirements': tender.get('requirements'),
                        'budget': tender.get('budget'),
                        'region': tender.get('region'),
                        'industry': tender.get('industry')
                    }

                    results = enterprise_matching_engine.match_tender(
                        tender_data=tender_data,
                        top_k=1,
                        min_score=0.4
                    )

                    if results:
                        match = results[0]
                        if match.match_score >= 0.4:
                            matched_tenders.append({
                                **tender,
                                'match_score': match.match_score,
                                'match_level': match.match_level,
                                'match_reasons': match.matched_reasons
                            })

                except Exception as e:
                    logger.warning(f"匹配招标项目失败: {str(e)}")
                    continue

            matched_tenders.sort(key=lambda x: x['match_score'], reverse=True)

            task.results['matched_tenders'] = matched_tenders
            task.results['matched_count'] = len(matched_tenders)

        except Exception as e:
            logger.error(f"匹配招标项目失败: {str(e)}")
            task.errors.append(f"匹配失败: {str(e)}")

        return matched_tenders

    async def _step_analyze_and_decide(
        self,
        task: AutomationTask,
        matched_tenders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        步骤3：自动分析和决策
        """
        from apps.enterprise.models import Enterprise

        bid_decisions = []

        try:
            enterprise = Enterprise.objects.get(id=task.config.enterprise_id)
            enterprise_data = self._get_enterprise_data(enterprise)

            for tender in matched_tenders:
                try:
                    analysis = await self._analyze_bid_opportunity(
                        tender,
                        enterprise_data,
                        task.config.enterprise_id
                    )

                    recommendation = analysis.get('recommendation', 'skip')
                    score = analysis.get('recommendation_score', 0)

                    should_bid = (
                        recommendation == 'participate' and
                        score >= task.config.auto_bid_threshold
                    )

                    bid_decisions.append({
                        'tender': tender,
                        'analysis': analysis,
                        'should_bid': should_bid,
                        'score': score
                    })

                except Exception as e:
                    logger.warning(f"分析招标项目失败: {str(e)}")
                    continue

            task.results['bid_decisions'] = bid_decisions
            task.results['decision_count'] = len([d for d in bid_decisions if d['should_bid']])

        except Exception as e:
            logger.error(f"分析决策失败: {str(e)}")
            task.errors.append(f"分析失败: {str(e)}")

        return bid_decisions

    async def _analyze_bid_opportunity(
        self,
        tender: Dict[str, Any],
        enterprise_data: Dict[str, Any],
        enterprise_id: int
    ) -> Dict[str, Any]:
        """
        分析投标机会
        """
        context = f"""
招标项目：{tender.get('title')}
预算金额：{tender.get('budget')}
匹配得分：{tender.get('match_score', 0)}
匹配原因：{tender.get('match_reasons', [])}

企业信息：
- 名称：{enterprise_data.get('name')}
- 资质：{enterprise_data.get('qualifications', [])}
- 业绩：{enterprise_data.get('performances', [])}
"""

        question = """请分析企业是否应该参与此项目的投标，给出：
1. 推荐分数(0-100)
2. 最终建议(participate/skip)
3. 简要理由"""

        result = await unified_llm_service.reasoning(
            question=question,
            context=context,
            agent_type='analyst'
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
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"解析自动化分析结果失败: {str(e)}")
            return {
                'recommendation': 'skip',
                'recommendation_score': 50,
                'reasoning': result.get('content', '')
            }

    def _get_enterprise_data(self, enterprise) -> Dict[str, Any]:
        """
        获取企业数据
        """
        from apps.enterprise.models import EnterpriseQualification, EnterprisePerformance

        data = {
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
        data['qualifications'] = [
            {
                'name': q.qualification_name,
                'type': q.qualification_category,
                'grade': q.grade,
            }
            for q in qualifications
        ]

        performances = EnterprisePerformance.objects.filter(enterprise=enterprise)[:10]
        data['performances'] = [
            {
                'name': p.project_name,
                'type': p.performance_type,
                'amount': str(p.contract_amount) if p.contract_amount else None
            }
            for p in performances
        ]

        return data

    async def _step_generate_documents(
        self,
        task: AutomationTask,
        bid_decisions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        步骤4：自动生成标书
        """
        from openclaw.agents.bid_document_agents import BidDocumentGeneratorAgent

        documents = []

        for decision in bid_decisions:
            if not decision['should_bid']:
                continue

            tender = decision['tender']

            try:
                agent = BidDocumentGeneratorAgent()

                doc_task = {
                    'tender_data': tender,
                    'enterprise_id': task.config.enterprise_id,
                    'match_result': {
                        'match_score': tender.get('match_score'),
                        'match_reasons': tender.get('match_reasons')
                    }
                }

                result = await agent.run(doc_task)

                if result.success:
                    documents.append({
                        'tender_id': tender['id'],
                        'tender_title': tender['title'],
                        'document': result.data.get('document'),
                        'sections': result.data.get('sections')
                    })

            except Exception as e:
                logger.warning(f"生成标书失败: {str(e)}")
                continue

        task.results['generated_documents'] = documents
        task.results['document_count'] = len(documents)

        return documents

    async def _step_review_and_optimize(
        self,
        task: AutomationTask,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        步骤5：自动审核和优化标书
        """
        from openclaw.agents.bid_document_agents import BidDocumentReviewerAgent, BidDocumentGeneratorAgent
        from openclaw.agents.bid_tracker_agents import BidQualityOptimizerAgent

        reviewed_docs = []
        max_iterations = 3

        for doc in documents:
            try:
                reviewer = BidDocumentReviewerAgent()

                review_task = {
                    'tender_data': {'id': doc['tender_id'], 'title': doc['tender_title']},
                    'document': doc['document'],
                    'sections': doc['sections']
                }

                review_result = await reviewer.run(review_task)

                if not review_result.success:
                    continue

                score = review_result.data.get('overall_score', 0)
                doc['review_score'] = score
                doc['review_result'] = review_result.data

                iteration = 0
                while score < task.config.auto_document_threshold and iteration < max_iterations:
                    optimizer = BidQualityOptimizerAgent()

                    optimize_task = {
                        'tender_data': {'id': doc['tender_id'], 'title': doc['tender_title']},
                        'document': doc['document'],
                        'review_result': doc['review_result']
                    }

                    optimize_result = await optimizer.run(optimize_task)

                    if optimize_result.success:
                        doc['document'] = optimize_result.data.get('optimized_document')

                        re_review_result = await reviewer.run(review_task)
                        if re_review_result.success:
                            score = re_review_result.data.get('overall_score', 0)
                            doc['review_score'] = score
                            doc['review_result'] = re_review_result.data

                    iteration += 1

                doc['final_score'] = score
                doc['passed'] = score >= task.config.auto_document_threshold
                reviewed_docs.append(doc)

            except Exception as e:
                logger.warning(f"审核标书失败: {str(e)}")
                continue

        task.results['reviewed_documents'] = reviewed_docs
        task.results['passed_count'] = len([d for d in reviewed_docs if d.get('passed')])

        return reviewed_docs

    async def _step_upload_documents(
        self,
        task: AutomationTask,
        documents: List[Dict[str, Any]]
    ):
        """
        步骤6：上传标书（如果启用）
        """
        if not task.config.auto_upload:
            task.results['upload_status'] = 'skipped'
            return

        uploaded = []

        for doc in documents:
            if not doc.get('passed'):
                continue

            uploaded.append({
                'tender_id': doc['tender_id'],
                'tender_title': doc['tender_title'],
                'status': 'pending',
                'message': '标书待人工上传'
            })

        task.results['uploaded_documents'] = uploaded
        task.results['upload_count'] = len(uploaded)

    async def _send_completion_notification(self, task: AutomationTask):
        """
        发送完成通知
        """
        try:
            message = f"""## 自动化投标任务完成

**任务ID**: {task.task_id}

**执行结果**:
- 采集招标项目：{task.results.get('collected_count', 0)} 个
- 匹配成功：{task.results.get('matched_count', 0)} 个
- 建议投标：{task.results.get('decision_count', 0)} 个
- 生成标书：{task.results.get('document_count', 0)} 份
- 审核通过：{task.results.get('passed_count', 0)} 份

**耗时**: {(task.completed_at - task.started_at).total_seconds():.1f} 秒

> 请登录系统查看详情
"""
            bid_result_notification_service.dingtalk.send_markdown(
                title='自动化投标任务完成',
                content=message
            )
        except Exception as e:
            logger.warning(f"发送通知失败: {str(e)}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        """
        task = self._tasks.get(task_id)
        if task:
            return {
                'task_id': task.task_id,
                'status': task.status,
                'current_step': task.current_step,
                'progress': task.progress,
                'results': task.results,
                'errors': task.errors,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            }
        return None

    def list_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """
        列出任务
        """
        tasks = []
        for task in self._tasks.values():
            if status and task.status != status:
                continue
            tasks.append({
                'task_id': task.task_id,
                'status': task.status,
                'current_step': task.current_step,
                'progress': task.progress,
                'created_at': task.created_at.isoformat() if task.created_at else None
            })
        return sorted(tasks, key=lambda x: x['created_at'], reverse=True)


one_click_automation_service = OneClickAutomationService()
