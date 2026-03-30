"""
数据源验证API接口
"""
import asyncio
import logging
import uuid
from datetime import datetime

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models_verification import DataSourceVerification, CollectionWorkflow, CrawlerSourceConfig
from crawler.data_source_validator import DataSourceValidator
from crawler.staged_collection_workflow import workflow_manager

logger = logging.getLogger(__name__)


class DataSourceValidationView(APIView):
    """
    数据源验证接口
    POST /api/v1/crawler/validate/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        执行数据源验证

        Request Body:
        {
            "source_name": "中国政府采购网",
            "source_url": "http://www.ccgp.gov.cn",
            "source_type": "government",
            "check_compliance": true,
            "check_technical": true,
            "check_quality": true
        }
        """
        source_name = request.data.get('source_name')
        source_url = request.data.get('source_url')
        source_type = request.data.get('source_type', 'unknown')

        if not source_name or not source_url:
            return Response({
                'success': False,
                'message': 'source_name 和 source_url 不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        existing = DataSourceVerification.objects.filter(
            source_url=source_url,
            status__in=['passed', 'requires_review']
        ).first()

        if existing:
            return Response({
                'success': True,
                'message': '该数据源已验证过',
                'data': {
                    'id': existing.id,
                    'status': existing.status,
                    'can_proceed': existing.can_proceed,
                    'validation_report': existing.validation_report,
                    'warnings': existing.warnings,
                    'recommendations': existing.recommendations,
                    'validated_at': existing.validated_at,
                }
            })

        verification = DataSourceVerification.objects.create(
            source_name=source_name,
            source_url=source_url,
            source_type=source_type,
            status='validating',
            validated_by=request.user
        )

        try:
            validator = DataSourceValidator()
            report = validator.validate(
                source_name=source_name,
                source_url=source_url,
                check_compliance=request.data.get('check_compliance', True),
                check_technical=request.data.get('check_technical', True),
                check_quality=request.data.get('check_quality', True)
            )

            verification.compliance_passed = all(r.passed for r in report.compliance_results)
            verification.technical_passed = all(r.passed for r in report.technical_results)
            verification.quality_passed = all(r.passed for r in report.quality_results)

            verification.validation_report = {
                'compliance': [vars(r) for r in report.compliance_results],
                'technical': [vars(r) for r in report.technical_results],
                'quality': [vars(r) for r in report.quality_results],
            }

            verification.warnings = report.warnings
            verification.recommendations = report.recommendations
            verification.can_proceed = report.can_proceed
            verification.requires_manual_review = not report.can_proceed or len(report.warnings) > 0

            if report.overall_passed:
                verification.status = 'requires_review' if verification.requires_manual_review else 'passed'
            else:
                verification.status = 'failed'

            verification.validated_at = datetime.now()
            verification.save()

            return Response({
                'success': True,
                'message': '验证完成',
                'data': {
                    'id': verification.id,
                    'status': verification.status,
                    'can_proceed': verification.can_proceed,
                    'requires_manual_review': verification.requires_manual_review,
                    'compliance_passed': verification.compliance_passed,
                    'technical_passed': verification.technical_passed,
                    'quality_passed': verification.quality_passed,
                    'validation_report': verification.validation_report,
                    'warnings': verification.warnings,
                    'recommendations': verification.recommendations,
                    'validated_at': verification.validated_at,
                }
            })

        except Exception as e:
            logger.error(f"数据源验证失败: {str(e)}")
            verification.status = 'failed'
            verification.validation_report = {'error': str(e)}
            verification.save()

            return Response({
                'success': False,
                'message': f'验证失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataSourceValidationListView(APIView):
    """
    数据源验证列表接口
    GET /api/v1/crawler/validations/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')
        source_type = request.query_params.get('source_type')

        queryset = DataSourceVerification.objects.all()

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if source_type:
            queryset = queryset.filter(source_type=source_type)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        items = []
        for v in queryset[start:end]:
            items.append({
                'id': v.id,
                'source_name': v.source_name,
                'source_url': v.source_url,
                'source_type': v.source_type,
                'status': v.status,
                'compliance_passed': v.compliance_passed,
                'technical_passed': v.technical_passed,
                'quality_passed': v.quality_passed,
                'can_proceed': v.can_proceed,
                'warnings_count': len(v.warnings) if v.warnings else 0,
                'recommendations_count': len(v.recommendations) if v.recommendations else 0,
                'validated_at': v.validated_at,
            })

        return Response({
            'success': True,
            'data': {
                'list': items,
                'total': queryset.count(),
                'page': page,
                'page_size': page_size,
            }
        })


class DualStageCollectionView(APIView):
    """
    双阶段采集工作流接口
    POST /api/v1/crawler/collection/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        执行双阶段采集工作流

        Request Body:
        {
            "source_name": "中国政府采购网",
            "source_url": "http://www.ccgp.gov.cn",
            "source_type": "government",
            "crawler_type": "china_gov",
            "notice_types": ["gkzb"],
            "page": 1,
            "page_size": 20
        }
        """
        source_name = request.data.get('source_name')
        source_url = request.data.get('source_url')
        source_type = request.data.get('source_type', 'unknown')
        crawler_type = request.data.get('crawler_type')
        notice_types = request.data.get('notice_types', ['gkzb'])
        page = request.data.get('page', 1)
        page_size = request.data.get('page_size', 20)

        if not source_name or not source_url:
            return Response({
                'success': False,
                'message': 'source_name 和 source_url 不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        workflow_id = f"wf_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        async def collection_task(**params):
            from crawler.china_gov_crawler import ChinaGovCrawler
            crawler = ChinaGovCrawler()
            return crawler.crawl(
                notice_types=params.get('notice_types', ['gkzb']),
                keywords=params.get('keywords'),
                page=params.get('page', 1),
                page_size=params.get('page_size', 20),
                region=params.get('region')
            )

        collection_params = {
            'notice_types': notice_types,
            'page': page,
            'page_size': page_size,
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            workflow = loop.run_until_complete(
                workflow_manager.execute_workflow(
                    workflow_id=workflow_id,
                    source_name=source_name,
                    source_url=source_url,
                    source_type=source_type,
                    collection_func=collection_task,
                    collection_params=collection_params,
                    skip_validation=request.data.get('skip_validation', False)
                )
            )
        finally:
            loop.close()

        return Response({
            'success': True,
            'data': workflow.to_dict()
        })


class CollectionWorkflowStatusView(APIView):
    """
    采集工作流状态查询接口
    GET /api/v1/crawler/workflow/<workflow_id>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, workflow_id):
        workflow = workflow_manager.get_workflow(workflow_id)

        if not workflow:
            return Response({
                'success': False,
                'message': '工作流不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'data': workflow.to_dict()
        })
