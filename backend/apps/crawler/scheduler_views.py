"""
定时采集任务 - 视图
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .scheduler_models import CrawlSchedule, CrawlScheduleLog
from .scheduler_serializers import (
    CrawlScheduleSerializer, CrawlScheduleListSerializer, CrawlScheduleCreateSerializer,
    CrawlScheduleUpdateSerializer, CrawlScheduleLogSerializer,
    QualificationMatchResultSerializer, QualificationMatchRequestSerializer
)
from .models import WebsiteTemplate
from services.qualification_matcher import QualificationMatcher, tender_qualification_matcher
from apps.tenders.models import TenderProject
from apps.enterprise.models import Enterprise, EnterpriseBidConfig

from utils.responses import APIResponse
from core.viewsets import APIResponseMixin
from core.progress_tracker import progress_tracker

logger = logging.getLogger(__name__)


class CrawlScheduleViewSet(APIResponseMixin, viewsets.ModelViewSet):
    """
    采集计划视图集
    """
    queryset = CrawlSchedule.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'is_active', 'website_template']
    search_fields = ['name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return CrawlScheduleListSerializer
        if self.action == 'create':
            return CrawlScheduleCreateSerializer
        if self.action in ['update', 'partial_update']:
            return CrawlScheduleUpdateSerializer
        return CrawlScheduleSerializer

    def perform_create(self, serializer):
        """
        创建时设置创建人
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        更新时同步更新Celery任务
        """
        instance = serializer.save()
        instance.update_celery_task()

    def perform_destroy(self, instance):
        """
        删除时同时删除Celery任务
        """
        instance.delete_celery_task()
        instance.delete()

    @extend_schema(
        summary='启用采集计划',
        description='启用指定的采集计划'
    )
    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """
        启用采集计划
        """
        schedule = self.get_object()
        schedule.is_active = True
        schedule.status = 'active'
        schedule.save()
        schedule.update_celery_task()

        return APIResponse.success(
            message='采集计划已启用',
            data={'schedule': CrawlScheduleSerializer(schedule).data}
        )

    @extend_schema(
        summary='暂停采集计划',
        description='暂停指定的采集计划'
    )
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        暂停采集计划
        """
        schedule = self.get_object()
        schedule.is_active = False
        schedule.status = 'paused'
        schedule.save()
        schedule.update_celery_task()

        return APIResponse.success(
            message='采集计划已暂停',
            data={'schedule': CrawlScheduleSerializer(schedule).data}
        )

    @extend_schema(
        summary='立即执行',
        description='立即执行一次采集任务'
    )
    @action(detail=True, methods=['post'])
    def execute_now(self, request, pk=None):
        """
        立即执行采集任务
        """
        schedule = self.get_object()

        task_id = f"crawl_schedule_{schedule.id}"

        try:
            progress_tracker.create_task(
                task_id=task_id,
                task_name=f"采集任务: {schedule.name}",
                total_steps=100,
                description=f"网站: {schedule.website_template.name}",
                schedule_id=schedule.id
            )
            progress_tracker.start_task(task_id)
            progress_tracker.update_progress(task_id, 5, 5, "正在初始化采集环境...")
        except Exception as e:
            logger.warning(f"创建进度追踪失败: {e}")

        try:
            from crawler.tasks import scheduled_crawl_with_match
            task = scheduled_crawl_with_match.delay(schedule.id)

            return APIResponse.success(
                message='采集任务已提交执行',
                data={
                    'task_id': task_id,
                    'celery_task_id': task.id,
                    'schedule_id': schedule.id
                }
            )
        except Exception as e:
            logger.warning(f"Celery不可用，改用后台线程执行: {str(e)}")

            import threading

            def run_crawl():
                try:
                    scheduled_crawl_with_match(schedule.id)
                except Exception as ex:
                    logger.error(f"后台采集任务执行失败: {str(ex)}")
                    try:
                        progress_tracker.fail_task(task_id, str(ex))
                    except:
                        pass

            thread = threading.Thread(target=run_crawl)
            thread.daemon = True
            thread.start()

            return APIResponse.success(
                message='采集任务已在后台启动，请稍后刷新查看结果',
                data={
                    'task_id': task_id,
                    'schedule_id': schedule.id
                }
            )

    @extend_schema(
        summary='获取执行日志',
        description='获取采集计划的执行日志'
    )
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        获取执行日志
        """
        schedule = self.get_object()
        logs = CrawlScheduleLog.objects.filter(schedule=schedule)[:50]

        serializer = CrawlScheduleLogSerializer(logs, many=True)
        return APIResponse.success(data={'list': serializer.data})

    @extend_schema(
        summary='获取统计信息',
        description='获取采集计划的统计信息'
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取统计信息
        """
        total = CrawlSchedule.objects.count()
        active = CrawlSchedule.objects.filter(status='active', is_active=True).count()
        paused = CrawlSchedule.objects.filter(status='paused').count()

        return APIResponse.success(
            data={
                'total': total,
                'active': active,
                'paused': paused
            }
        )

    @extend_schema(
        summary='检查计划名称唯一性',
        description='检查计划名称是否已被使用',
        parameters=[
            OpenApiParameter(name='name', description='计划名称', required=True, type=str),
            OpenApiParameter(name='exclude_id', description='排除的计划ID（编辑时使用）', required=False, type=int)
        ]
    )
    @action(detail=False, methods=['get'])
    def check_duplicate_name(self, request):
        """
        检查计划名称是否重复
        """
        name = request.query_params.get('name', '').strip()
        exclude_id = request.query_params.get('exclude_id')

        if not name:
            return APIResponse.error(message='计划名称不能为空')

        queryset = CrawlSchedule.objects.filter(name=name)

        if exclude_id:
            try:
                queryset = queryset.exclude(pk=int(exclude_id))
            except (ValueError, TypeError):
                pass

        is_duplicate = queryset.exists()

        return APIResponse.success(
            data={
                'is_duplicate': is_duplicate,
                'name': name
            }
        )


class CrawlScheduleLogViewSet(APIResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    采集计划日志视图集（只读）
    """
    queryset = CrawlScheduleLog.objects.all()
    serializer_class = CrawlScheduleLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['schedule', 'status']
    ordering = ['-started_at']


class QualificationMatchViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    资质匹配视图集
    """
    permission_classes = [IsAuthenticated]

    def _get_enterprise_config(self, user):
        """
        获取企业配置
        """
        enterprise = Enterprise.objects.filter(
            created_by=user,
            is_active=True
        ).first()
        
        if not enterprise:
            enterprise = Enterprise.objects.filter(is_active=True).first()
        
        if not enterprise:
            return None, None
        
        bid_config = EnterpriseBidConfig.objects.filter(
            enterprise=enterprise
        ).first()
        
        return enterprise, bid_config

    @extend_schema(
        summary='执行资质匹配',
        description='对招标项目执行企业资质匹配',
        request=QualificationMatchRequestSerializer,
        responses={200: QualificationMatchResultSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def match(self, request):
        """
        执行资质匹配
        """
        serializer = QualificationMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tender_ids = serializer.validated_data.get('tender_ids')
        auto_delete = serializer.validated_data.get('auto_delete', False)
        threshold = serializer.validated_data.get('threshold', 0.6)

        if tender_ids:
            tenders = TenderProject.objects.filter(id__in=tender_ids)
        else:
            tenders = TenderProject.objects.filter(status='pending')

        enterprise, bid_config = self._get_enterprise_config(request.user)
        
        if not enterprise:
            return APIResponse.not_found(message='未找到企业信息，请先配置企业资料')

        matcher = QualificationMatcher(enterprise, bid_config)
        results = matcher.match_tenders_batch(list(tenders[:100]), threshold)

        deleted_count = 0
        if auto_delete:
            unmatched_tenders = [t for t, r in zip(tenders, results) if not r.is_matched]
            if unmatched_tenders:
                from django.db import transaction
                with transaction.atomic():
                    tender_ids_to_delete = [t.id for t in unmatched_tenders]
                    deleted_count = TenderProject.objects.filter(id__in=tender_ids_to_delete).delete()[0]

        matched_count = sum(1 for r in results if r.is_matched)

        for tender, result in zip(tenders, results):
            if result.is_matched:
                tender.status = 'processing'
                tender.keywords_matched = result.match_details
                tender.save(update_fields=['status', 'keywords_matched'])

        return APIResponse.success(
            data={
                'total': len(results),
                'matched': matched_count,
                'unmatched': len(results) - matched_count,
                'deleted': deleted_count,
                'results': [
                    {
                        'tender_id': r.tender_id,
                        'tender_title': r.tender_title,
                        'is_matched': r.is_matched,
                        'match_score': r.match_score,
                        'reject_reasons': r.reject_reasons
                    }
                    for r in results[:20]
                ]
            }
        )

    @extend_schema(
        summary='预览匹配结果',
        description='预览资质匹配结果，不执行删除操作',
        request=QualificationMatchRequestSerializer,
        responses={200: QualificationMatchResultSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def preview(self, request):
        """
        预览匹配结果
        """
        serializer = QualificationMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tender_ids = serializer.validated_data.get('tender_ids')
        threshold = serializer.validated_data.get('threshold', 0.6)

        if tender_ids:
            tenders = TenderProject.objects.filter(id__in=tender_ids)
        else:
            tenders = TenderProject.objects.filter(status='pending')[:20]

        enterprise, bid_config = self._get_enterprise_config(request.user)
        
        if not enterprise:
            return APIResponse.not_found(message='未找到企业信息，请先配置企业资料')

        matcher = QualificationMatcher(enterprise, bid_config)
        results = matcher.match_tenders_batch(list(tenders), threshold)

        return APIResponse.success(
            data={
                'total': len(results),
                'matched': sum(1 for r in results if r.is_matched),
                'unmatched': sum(1 for r in results if not r.is_matched),
                'results': [
                    {
                        'tender_id': r.tender_id,
                        'tender_title': r.tender_title,
                        'is_matched': r.is_matched,
                        'match_score': r.match_score,
                        'match_details': r.match_details,
                        'reject_reasons': r.reject_reasons
                    }
                    for r in results
                ]
            }
        )

    @extend_schema(
        summary='获取匹配规则',
        description='获取当前企业的资质匹配规则'
    )
    @action(detail=False, methods=['get'])
    def rules(self, request):
        """
        获取匹配规则
        """
        enterprise, bid_config = self._get_enterprise_config(request.user)

        if not enterprise:
            return APIResponse.not_found(message='未找到企业信息，请先配置企业资料')

        matcher = QualificationMatcher(enterprise, bid_config)

        return APIResponse.success(
            data={
                'enterprise_name': enterprise.name,
                'rules': matcher.rules
            }
        )
