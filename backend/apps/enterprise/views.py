"""
SAAS企业资料库模块 - 视图
"""
import asyncio
import logging
from typing import Optional
from rest_framework import viewsets, status
from rest_framework.decorators import action, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.db import models, transaction

from utils.responses import UnifiedResponse
from common.views.base import BaseViewSet, AuthenticatedModelViewSet, AuthenticatedReadOnlyViewSet


class EnterpriseCollectThrottle(UserRateThrottle):
    """
    企业采集频率限制
    每小时最多10次
    """
    rate = '10/hour'


class EnterpriseBatchCollectThrottle(UserRateThrottle):
    """
    批量采集频率限制
    每小时最多3次
    """
    rate = '3/hour'

from .models import (
    Enterprise, EnterpriseQualification, EnterprisePerformance,
    EnterpriseMatchRule, EnterpriseMatchResult, EnterpriseContact,
    EnterpriseBidConfig, EnterpriseDocument, DocumentAuditLog,
    EnterpriseKeyPersonnel
)
from .serializers import (
    EnterpriseSerializer, EnterpriseListSerializer,
    EnterpriseQualificationSerializer, EnterprisePerformanceSerializer,
    EnterpriseContactSerializer, EnterpriseMatchRuleSerializer,
    EnterpriseMatchResultSerializer, EnterpriseMatchResultListSerializer,
    MatchTenderSerializer, EnterpriseStatisticsSerializer,
    EnterpriseBidConfigSerializer, EnterpriseBidConfigCreateSerializer,
    EnterpriseWithBidConfigSerializer,
    EnterpriseDocumentSerializer, EnterpriseDocumentListSerializer,
    EnterpriseDocumentUploadSerializer, EnterpriseDocumentStatisticsSerializer,
    DocumentAuditLogSerializer,
    EnterpriseKeyPersonnelSerializer, EnterpriseKeyPersonnelListSerializer
)
from .services import EnterpriseMatcher, EnterpriseService
from utils.helpers import get_client_ip
from services.vector import embedding_service, enterprise_vector_store
from services.vector.transaction import VectorTransaction

logger = logging.getLogger(__name__)


class EnterpriseViewSet(BaseViewSet):
    """
    企业视图集
    """
    queryset = Enterprise.objects.all().select_related(
        'bid_config'
    ).prefetch_related(
        'qualifications',
        'performances',
        'contacts',
        'key_personnel'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise_type', 'province', 'city', 'is_active', 'is_verified']
    search_fields = ['name', 'credit_code']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        return Enterprise.objects.all().select_related(
            'bid_config'
        ).prefetch_related(
            'qualifications',
            'performances',
            'contacts',
            'key_personnel'
        )
    
    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return EnterpriseListSerializer
        return EnterpriseSerializer
    
    def perform_create(self, serializer):
        """
        创建时设置创建人
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        获取企业统计信息
        """
        enterprise = self.get_object()
        stats = EnterpriseService.get_enterprise_statistics(enterprise)
        
        serializer = EnterpriseStatisticsSerializer(stats)
        return UnifiedResponse.success(data=serializer.data)
    
    @action(detail=True, methods=['get'])
    def expiring_qualifications(self, request, pk=None):
        """
        获取即将过期的资质
        """
        enterprise = self.get_object()
        days = request.query_params.get('days', 30)
        
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        qualifications = EnterpriseService.check_qualification_expiry(enterprise, days)
        serializer = EnterpriseQualificationSerializer(qualifications, many=True)
        
        return UnifiedResponse.success(data=serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_enterprise(self, request):
        from services.data import EnterpriseRepository
        repo = EnterpriseRepository()
        try:
            enterprise = Enterprise.objects.get(
                Q(created_by=request.user) | Q(name=request.user.company_name)
            )
            serializer = self.get_serializer(enterprise)
            return UnifiedResponse.success(data=serializer.data)
        except Enterprise.DoesNotExist:
            return UnifiedResponse.not_found('未找到关联企业')
        except Enterprise.MultipleObjectsReturned:
            enterprises = repo.get_user_enterprises(request.user.id)
            serializer = EnterpriseListSerializer(enterprises, many=True)
            return UnifiedResponse.success(data=serializer.data)
    
    @action(detail=False, methods=['post'])
    @throttle_classes([EnterpriseCollectThrottle])
    def collect_info(self, request):
        """
        采集企业信息
        从天眼查、企查查等平台采集企业信息
        
        请求参数:
        - company_name: 企业全称（必填）
        - source: 数据源 (tianyancha/qichacha/auto，默认auto)
        - save_to_db: 是否保存到数据库（默认True）
        - update_existing: 是否更新已存在的企业（默认False）
        """
        logger.info(f"collect_info called with data: {request.data}")
        
        company_name = request.data.get('company_name')
        source = request.data.get('source', 'auto')
        save_to_db = request.data.get('save_to_db', True)
        update_existing = request.data.get('update_existing', False)
        
        logger.info(f"Extracted values - company_name: '{company_name}', source: '{source}', save_to_db: {save_to_db}, update_existing: {update_existing}")
        
        if not company_name:
            logger.warning(f"Company name is empty or None: {company_name}")
            return UnifiedResponse.error(
                message='企业名称不能为空',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from openclaw.agents.enterprise_collector_agent import EnterpriseInfoCollectorAgent
            
            async def collect():
                agent = EnterpriseInfoCollectorAgent()
                result = await agent.run({
                    'company_name': company_name,
                    'source': source,
                    'save_to_db': save_to_db,
                    'update_existing': update_existing
                })
                return result
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(collect())
            loop.close()
            
            if result.success:
                return UnifiedResponse.success(
                    data=result.data,
                    message='企业信息采集成功'
                )
            else:
                error_msg = result.error or '采集失败'
                sources_tried = result.metadata.get('sources_tried', []) if result.metadata else []
                
                if '无法从公开渠道获取企业信息' in error_msg:
                    error_msg = f'未能从公开渠道获取"{company_name}"的企业信息。可能原因：\n1. 企业名称不正确或不完整\n2. 该企业信息尚未公开\n3. 网络访问受限\n\n建议：请手动录入企业信息'
                
                response_data = {
                    'company_name': company_name
                }
                if sources_tried:
                    response_data['sources'] = ', '.join(sources_tried)
                
                return UnifiedResponse.error(
                    message=error_msg,
                    data=response_data,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"企业信息采集失败: {str(e)}")
            return UnifiedResponse.error(
                message='采集服务异常，请稍后重试或手动录入企业信息',
                data={'error_detail': str(e), 'company_name': company_name},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    @throttle_classes([EnterpriseBatchCollectThrottle])
    def batch_collect(self, request):
        """
        批量采集企业信息
        
        请求参数:
        - company_names: 企业名称列表（必填）
        - source: 数据源 (tianyancha/qichacha/auto，默认auto)
        - save_to_db: 是否保存到数据库（默认True）
        - update_existing: 是否更新已存在的企业（默认False）
        - max_concurrent: 最大并发数（默认5）
        """
        company_names = request.data.get('company_names', [])
        source = request.data.get('source', 'auto')
        save_to_db = request.data.get('save_to_db', True)
        update_existing = request.data.get('update_existing', False)
        max_concurrent = request.data.get('max_concurrent', 5)
        
        if not company_names:
            return UnifiedResponse.error(
                message='企业名称列表不能为空',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from openclaw.agents.enterprise_collector_agent import EnterpriseBatchCollectorAgent
            
            async def batch_collect():
                agent = EnterpriseBatchCollectorAgent()
                result = await agent.run({
                    'company_names': company_names,
                    'source': source,
                    'save_to_db': save_to_db,
                    'update_existing': update_existing,
                    'max_concurrent': max_concurrent
                })
                return result
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(batch_collect())
            loop.close()
            
            if result.success:
                return UnifiedResponse.success(
                    data=result.data,
                    message=f'批量采集完成，成功{result.data["success_count"]}个，失败{result.data["failed_count"]}个'
                )
            else:
                return UnifiedResponse.error(message=result.error, status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"批量采集失败: {str(e)}")
            return UnifiedResponse.error(
                message='批量采集失败，请稍后重试',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def search_online(self, request):
        """
        在线搜索企业（不保存到数据库）
        仅用于预览企业信息
        
        请求参数:
        - company_name: 企业全称或关键词（必填）
        - source: 数据源 (tianyancha/qichacha/auto，默认auto)
        """
        company_name = request.data.get('company_name')
        source = request.data.get('source', 'auto')
        
        if not company_name:
            return UnifiedResponse.error(
                message='企业名称不能为空',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from openclaw.skill_registry import skill_registry
            
            async def search():
                result = await skill_registry.execute_skill(
                    'enterprise_info_collector',
                    company_name=company_name,
                    source=source
                )
                return result
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(search())
            loop.close()
            
            if result.success:
                return UnifiedResponse.success(
                    data=result.data,
                    message='搜索成功'
                )
            else:
                return UnifiedResponse.error(message=result.error, status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"在线搜索企业失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'搜索失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def index_to_vector(self, request, pk=None):
        """
        将企业信息索引到向量存储
        """
        enterprise = self.get_object()

        try:
            text = self._build_enterprise_text(enterprise)
            metadata = {
                'name': enterprise.name,
                'industry': getattr(enterprise, 'industry', '') or '',
                'province': getattr(enterprise, 'province', '') or '',
                'city': getattr(enterprise, 'city', '') or '',
            }
            success = enterprise_vector_store.add_enterprise(
                enterprise_id=str(enterprise.id),
                text=text,
                metadata=metadata
            )

            if success:
                return UnifiedResponse.success(message='企业信息已成功索引到向量存储')
            else:
                return UnifiedResponse.error(
                    message='索引失败，请检查企业信息是否完整',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"索引企业失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'索引失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_enterprise_text(self, enterprise):
        """
        构建企业文本描述（用于向量化）
        """
        parts = []
        parts.append(enterprise.name or '')

        if hasattr(enterprise, 'business_scope') and enterprise.business_scope:
            parts.append(f"经营范围: {enterprise.business_scope}")

        if hasattr(enterprise, 'enterprise_type') and enterprise.enterprise_type:
            parts.append(f"行业: {enterprise.enterprise_type}")

        if hasattr(enterprise, 'qualifications'):
            for qual in enterprise.qualifications.filter(is_valid=True)[:5]:
                if qual.qualification_name:
                    parts.append(f"资质: {qual.qualification_name}")
                if qual.qualification_category:
                    parts.append(f"资质范围: {qual.qualification_category}")

        if hasattr(enterprise, 'performances'):
            for perf in enterprise.performances.all()[:5]:
                if perf.project_name:
                    parts.append(f"业绩项目: {perf.project_name}")
                if perf.description:
                    parts.append(f"项目描述: {perf.description}")

        return ' '.join([p for p in parts if p])

    @action(detail=False, methods=['post'])
    def batch_index(self, request):
        """
        批量索引企业到向量存储（使用VectorTransaction保证数据一致性）
        """
        enterprise_ids = request.data.get('enterprise_ids', [])

        if not enterprise_ids:
            enterprises = Enterprise.objects.filter(is_active=True).prefetch_related(
                'qualifications', 'performances'
            )
        else:
            enterprises = Enterprise.objects.filter(
                id__in=enterprise_ids, is_active=True
            ).prefetch_related('qualifications', 'performances')

        try:
            batch_data = []
            for enterprise in enterprises:
                try:
                    text = self._build_enterprise_text(enterprise)
                    metadata = {
                        'name': enterprise.name,
                        'industry': getattr(enterprise, 'industry', '') or '',
                        'province': getattr(enterprise, 'province', '') or '',
                        'city': getattr(enterprise, 'city', '') or '',
                    }
                    batch_data.append({
                        'id': str(enterprise.id),
                        'text': text,
                        'metadata': metadata
                    })
                except Exception as e:
                    logger.error(f"构建企业文本失败 {enterprise.name}: {str(e)}")

            if batch_data:
                with VectorTransaction() as vt:
                    vt.batch_add_vectors('enterprise_vectors', batch_data)

                return UnifiedResponse.success(data={
                    'success_count': len(batch_data),
                    'failed_count': 0,
                    'total': len(batch_data)
                }, message='批量索引完成（VectorTransaction模式）')
            else:
                return UnifiedResponse.success(data={
                    'success_count': 0,
                    'failed_count': 0,
                    'total': 0
                }, message='没有可索引的企业')
        except Exception as e:
            logger.error(f"批量索引失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'批量索引失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def cookie_status(self, request):
        """
        获取各平台Cookie状态
        """
        from common.crawler import cookie_manager

        status_data = cookie_manager.get_status()

        return UnifiedResponse.success(data=status_data)
    
    @action(detail=False, methods=['post'])
    def import_cookies(self, request):
        """
        导入平台登录Cookie
        
        请求参数:
        - platform: 平台名称 (tianyancha/qichacha/aiqicha/qixin)
        - cookies: Cookie数据，支持以下格式:
          - cookie_string: "name=value; name2=value2"
          - cookie_json: JSON字符串
          - cookie_list: Cookie列表 [{"name": "xxx", "value": "xxx"}]
        - expire_hours: 过期时间（小时），默认24
        """
        from common.crawler import cookie_manager

        platform = request.data.get('platform')
        cookie_string = request.data.get('cookie_string')
        cookie_json = request.data.get('cookie_json')
        cookie_list = request.data.get('cookie_list')
        expire_hours = request.data.get('expire_hours', 24)
        
        if not platform:
            return UnifiedResponse.error(message='请指定平台名称', status_code=status.HTTP_400_BAD_REQUEST)

        if not any([cookie_string, cookie_json, cookie_list]):
            return UnifiedResponse.error(message='请提供Cookie数据', status_code=status.HTTP_400_BAD_REQUEST)

        success = cookie_manager.import_from_browser(
            platform=platform,
            cookie_string=cookie_string,
            cookie_json=cookie_json,
            cookie_list=cookie_list
        )

        if success:
            cookie_manager.save_cookies(
                platform=platform,
                cookies=cookie_manager.get_cookies(platform),
                expire_hours=expire_hours
            )

            return UnifiedResponse.success(
                data={'expire_hours': expire_hours},
                message=f'{platform} Cookie导入成功'
            )
        else:
            return UnifiedResponse.error(
                message='Cookie导入失败，请检查格式',
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def clear_cookies(self, request):
        """
        清除平台Cookie
        
        请求参数:
        - platform: 平台名称（可选，不传则清除所有）
        """
        from common.crawler import cookie_manager

        platform = request.data.get('platform')

        cookie_manager.clear_cookies(platform)
        
        return UnifiedResponse.success(message=f'已清除 {platform or "所有平台"} 的Cookie')
    
    @action(detail=False, methods=['post'])
    def collect_with_cookies(self, request):
        """
        使用登录态Cookie采集企业信息
        
        请求参数:
        - company_name: 企业名称（必填）
        - source: 数据源 (tianyancha/qichacha/aiqicha/qixin/auto)
        - save_to_db: 是否保存到数据库（默认True）
        """
        from crawler.cookie_based_collector import collect_with_cookies
        
        company_name = request.data.get('company_name')
        source = request.data.get('source', 'auto')
        save_to_db = request.data.get('save_to_db', True)
        
        if not company_name:
            return UnifiedResponse.error(message='请提供企业名称', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(collect_with_cookies(company_name, source))
            finally:
                loop.close()

            if result.get('success'):
                data = result.get('data', {})

                if save_to_db:
                    saved = self._save_enterprise_data(data, request.user)
                    if saved:
                        data['saved_to_db'] = True
                        data['enterprise_id'] = saved.id

                return UnifiedResponse.success(
                    data=data,
                    message='采集成功'
                )
            else:
                return UnifiedResponse.error(
                    message=result.get('error', '采集失败'),
                    data={'sources_tried': result.get('sources_tried', [])},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Cookie采集失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'采集失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _save_enterprise_data(self, data: dict, user) -> Optional['Enterprise']:
        """保存企业数据到数据库"""
        try:
            credit_code = data.get('credit_code')
            
            if not credit_code:
                logger.warning("缺少统一社会信用代码，无法保存")
                return None
            
            enterprise, created = Enterprise.objects.update_or_create(
                credit_code=credit_code,
                defaults={
                    'name': data.get('name', ''),
                    'legal_person': data.get('legal_person', ''),
                    'registered_capital': data.get('registered_capital'),
                    'address': data.get('address', ''),
                    'business_scope': data.get('business_scope', ''),
                    'industry': data.get('industry', ''),
                    'province': data.get('province', ''),
                    'city': data.get('city', ''),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'is_verified': True,
                    'created_by': user,
                }
            )

            logger.info(f"企业数据已保存: {enterprise.name}")
            return enterprise
            
        except Exception as e:
            logger.error(f"保存企业数据失败: {str(e)}")
            return None

    @action(detail=False, methods=['post'])
    def semantic_match(self, request):
        """
        语义匹配招标信息
        仅使用向量相似度进行匹配
        """
        serializer = MatchTenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tender_data = serializer.validated_data
        enterprise_ids = tender_data.pop('enterprise_ids', None)
        threshold = request.data.get('threshold', 0.6)
        
        try:
            matcher = EnterpriseMatcher(use_semantic=True)
            results = matcher.match_tender_semantic_only(
                tender_data, 
                enterprise_ids, 
                threshold
            )
            
            enterprise_ids_in_results = [r['enterprise_id'] for r in results]
            enterprises = Enterprise.objects.filter(id__in=enterprise_ids_in_results)
            enterprise_map = {e.id: e for e in enterprises}

            enriched_results = []
            for result in results:
                enterprise = enterprise_map.get(result['enterprise_id'])
                if enterprise:
                    enriched_results.append({
                        'enterprise_id': enterprise.id,
                        'enterprise_name': enterprise.name,
                        'similarity': result['similarity'],
                        'match_type': result['match_type'],
                        'industry': enterprise.industry,
                        'province': enterprise.province,
                        'city': enterprise.city
                    })
            
            return UnifiedResponse.success(data={
                'total_count': len(enriched_results),
                'threshold': threshold,
                'results': enriched_results
            })

        except Exception as e:
            logger.error(f"语义匹配失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'匹配失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnterpriseQualificationViewSet(AuthenticatedModelViewSet):
    """
    企业资质视图集
    """
    queryset = EnterpriseQualification.objects.select_related('enterprise')
    serializer_class = EnterpriseQualificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'qualification_category', 'is_valid', 'is_primary']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """
        获取即将过期的资质
        """
        from datetime import date, timedelta
        
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        today = date.today()
        expiry_date = today + timedelta(days=days)
        
        qualifications = self.queryset.filter(
            is_valid=True,
            expiry_date__lte=expiry_date,
            expiry_date__gte=today
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(qualifications, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['post'])
    def match_requirements(self, request):
        """
        匹配资质要求
        根据招标资质要求匹配企业资质
        
        请求参数:
        - requirements: 资质要求列表 [{'type': '资质类型', 'grade': '等级', 'name': '资质名称'}]
        - enterprise_id: 指定企业ID（可选）
        """
        requirements = request.data.get('requirements', [])
        enterprise_id = request.data.get('enterprise_id')
        
        if not requirements:
            return UnifiedResponse.error(
                message='请提供资质要求列表',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        qualifications = self.queryset.filter(is_valid=True)
        if enterprise_id:
            qualifications = qualifications.filter(enterprise_id=enterprise_id)
        
        results = []
        for req in requirements:
            req_type = req.get('type', '')
            req_grade = req.get('grade', '')
            req_name = req.get('name', '')
            
            matched_quals = []
            for qual in qualifications:
                match_score = 0
                match_details = []
                
                if req_name and req_name in qual.qualification_name:
                    match_score += 40
                    match_details.append(f'资质名称匹配: {req_name}')
                
                if req_type and qual.qualification_category == req_type:
                    match_score += 30
                    match_details.append(f'资质类型匹配')

                if req_grade:
                    if qual.grade and self._compare_qualification_grade(qual.grade, req_grade):
                        match_score += 30
                        match_details.append(f'资质等级满足要求')

                if match_score > 0:
                    matched_quals.append({
                        'qualification_id': qual.id,
                        'qualification_name': qual.qualification_name,
                        'qualification_category': qual.qualification_category,
                        'grade': qual.grade,
                        'enterprise_name': qual.enterprise.name,
                        'match_score': match_score,
                        'match_details': match_details,
                        'expiry_date': qual.expiry_date
                    })
            
            matched_quals.sort(key=lambda x: x['match_score'], reverse=True)
            results.append({
                'requirement': req,
                'matched_count': len(matched_quals),
                'matches': matched_quals[:5]
            })
        
        return UnifiedResponse.success(data={
            'total_requirements': len(requirements),
            'results': results
        })

    def _compare_qualification_grade(self, enterprise_grade: str, required_grade: str) -> bool:
        """
        比较资质等级
        企业资质等级需要满足或高于要求等级
        """
        grade_order = {
            'special': 5,
            '特级': 5,
            'first': 4,
            '一级': 4,
            'second': 3,
            '二级': 3,
            'third': 2,
            '三级': 2,
            '三级（无等级）': 1,
        }
        
        enterprise_level = grade_order.get(enterprise_grade, 0)
        required_level = grade_order.get(required_grade, 0)
        
        return enterprise_level >= required_level


class EnterprisePerformanceViewSet(AuthenticatedModelViewSet):
    """
    企业业绩视图集
    """
    queryset = EnterprisePerformance.objects.select_related('enterprise')
    serializer_class = EnterprisePerformanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'performance_type', 'is_verified']
    search_fields = ['project_name', 'client_name', 'project_code']
    ordering = ['-end_date', '-created_at']


class EnterpriseContactViewSet(AuthenticatedModelViewSet):
    """
    企业联系人视图集
    """
    queryset = EnterpriseContact.objects.select_related('enterprise')
    serializer_class = EnterpriseContactSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'contact_type', 'is_primary', 'is_active']
    ordering = ['-created_at']

class EnterpriseMatchRuleViewSet(AuthenticatedModelViewSet):
    """
    企业匹配规则视图集
    """
    queryset = EnterpriseMatchRule.objects.select_related('enterprise')
    serializer_class = EnterpriseMatchRuleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'rule_type', 'is_active']
    ordering = ['-created_at']

class EnterpriseDocumentViewSet(AuthenticatedModelViewSet):
    """
    企业证书视图集 - 集中管理企业各类证书资料
    支持双用途：AI招标公告比对 + 标书生成素材
    """
    queryset = EnterpriseDocument.objects.select_related('enterprise', 'created_by')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'document_type', 'status', 'is_primary', 'is_verified', 'recognition_status', 'is_ai_reference', 'is_bid_material']
    search_fields = ['document_name', 'document_no', 'description']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return EnterpriseDocumentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EnterpriseDocumentUploadSerializer
        return EnterpriseDocumentSerializer

    def perform_create(self, serializer):
        """
        创建时设置上传人和文件信息
        """
        auto_recognize = serializer.validated_data.pop('auto_recognize', False)
        document = serializer.save(created_by=self.request.user)
        
        if document.file_path:
            document.file_size = document.file_path.size
            document.file_type = document.file_path.file.content_type
            document.save()
        
        if auto_recognize:
            self._run_recognition_async(document.id)

    def perform_update(self, serializer):
        """
        更新时更新文件信息
        """
        document = serializer.save()
        
        if document.file_path:
            document.file_size = document.file_path.size
            document.file_type = document.file_path.file.content_type
            document.save()

    def _run_recognition_async(self, document_id: int):
        """
        异步执行识别
        """
        from django.core.management import call_command
        from django.db import connection
        import threading
        
        def run():
            try:
                from services.document_recognition_service import DocumentRecognitionService
                document = EnterpriseDocument.objects.get(id=document_id)
                service = DocumentRecognitionService()
                service.recognize_document(document)
            except Exception as e:
                logger.error(f"异步识别失败: {str(e)}")
        
        thread = threading.Thread(target=run)
        thread.start()

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """
        获取即将过期的证书
        """
        from datetime import date, timedelta
        
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        today = date.today()
        expiry_date = today + timedelta(days=days)
        
        documents = self.queryset.filter(
            expiry_date__lte=expiry_date,
            expiry_date__gte=today
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(documents, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """
        获取已过期的证书
        """
        from datetime import date
        
        today = date.today()
        documents = self.queryset.filter(
            expiry_date__lt=today
        ).order_by('-expiry_date')
        
        serializer = self.get_serializer(documents, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取证书统计信息
        """
        enterprise_id = request.query_params.get('enterprise_id')
        
        queryset = self.queryset
        if enterprise_id:
            queryset = queryset.filter(enterprise_id=enterprise_id)
        
        stats = queryset.aggregate(
            total_count=Count('id'),
            valid_count=Count('id', filter=models.Q(status='valid')),
            expiring_count=Count('id', filter=models.Q(status='expiring')),
            expired_count=Count('id', filter=models.Q(status='expired')),
            pending_count=Count('id', filter=models.Q(status='pending')),
        )
        
        by_type = queryset.values('document_type').annotate(count=Count('id'))
        by_type_dict = {item['document_type']: item['count'] for item in by_type}
        
        stats['by_type'] = by_type_dict
        
        recognition_stats = queryset.aggregate(
            pending_count=Count('id', filter=models.Q(recognition_status='pending')),
            processing_count=Count('id', filter=models.Q(recognition_status='processing')),
            completed_count=Count('id', filter=models.Q(recognition_status='completed')),
            failed_count=Count('id', filter=models.Q(recognition_status='failed')),
        )
        stats['recognition'] = recognition_stats
        
        serializer = EnterpriseDocumentStatisticsSerializer(stats)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        按类型获取证书
        """
        document_type = request.query_params.get('document_type')
        enterprise_id = request.query_params.get('enterprise_id')
        
        if not document_type:
            return UnifiedResponse.error(message='请提供证书类型')
        
        queryset = self.queryset.filter(document_type=document_type)
        if enterprise_id:
            queryset = queryset.filter(enterprise_id=enterprise_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        验证证书
        """
        document = self.get_object()
        document.is_verified = True
        document.save()
        
        from .models import DocumentAuditLog
        DocumentAuditLog.objects.create(
            document=document,
            action_type='verify',
            is_success=True,
            operated_by=request.user,
            ip_address=get_client_ip(request)
        )
        
        return UnifiedResponse.success(message='证书已验证')

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        设置为主要证书
        """
        document = self.get_object()
        
        EnterpriseDocument.objects.filter(
            enterprise=document.enterprise,
            document_type=document.document_type,
            is_primary=True
        ).update(is_primary=False)
        
        document.is_primary = True
        document.save()
        
        from .models import DocumentAuditLog
        DocumentAuditLog.objects.create(
            document=document,
            action_type='set_primary',
            is_success=True,
            operated_by=request.user,
            ip_address=get_client_ip(request)
        )
        
        return UnifiedResponse.success(message='已设置为主要证书')

    @action(detail=False, methods=['get'])
    def options(self, request):
        """
        获取选项配置
        """
        from .models import EnterpriseDocument
        
        return UnifiedResponse.success(data={
            'document_types': dict(EnterpriseDocument.DOCUMENT_TYPE_CHOICES),
            'document_statuses': dict(EnterpriseDocument.DOCUMENT_STATUS_CHOICES),
            'recognition_statuses': {
                'pending': '待识别',
                'processing': '识别中',
                'completed': '已完成',
                'failed': '识别失败'
            }
        })

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        批量删除证书
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return UnifiedResponse.error(message='请提供要删除的证书ID列表')
        
        deleted_count = 0
        for doc_id in ids:
            try:
                document = EnterpriseDocument.objects.get(id=doc_id)
                DocumentAuditLog.objects.create(
                    document=document,
                    action_type='delete',
                    is_success=True,
                    operated_by=request.user,
                    ip_address=get_client_ip(request),
                    action_detail=f'批量删除证书: {document.document_name}'
                )
                deleted_count += 1
            except EnterpriseDocument.DoesNotExist:
                pass
        
        deleted, _ = self.queryset.filter(id__in=ids).delete()
        
        DocumentAuditLog.objects.create(
            action_type='batch_delete',
            is_success=True,
            operated_by=request.user,
            ip_address=get_client_ip(request),
            action_detail=f'批量删除了 {deleted} 个证书'
        )
        
        return UnifiedResponse.success(
            data={'deleted_count': deleted},
            message=f'成功删除 {deleted} 个证书'
        )

    @action(detail=True, methods=['post'])
    def recognize(self, request, pk=None):
        """
        识别证书内容
        """
        document = self.get_object()
        
        try:
            from services.document_recognition_service import DocumentRecognitionService
            service = DocumentRecognitionService()
            
            validation = service.validate_file(document.file_path)
            if not validation.get('valid'):
                return UnifiedResponse.error(
                    message=validation.get('error', '文件验证失败'),
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            result = service.recognize_document(document, user=request.user)

            return UnifiedResponse.success(data=result)

        except Exception as e:
            logger.error(f"证书识别失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'证书识别失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def compare(self, request, pk=None):
        """
        与数据库比对
        """
        document = self.get_object()

        if document.recognition_status != 'completed':
            return UnifiedResponse.error(
                message='证书尚未完成识别，请先进行识别',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            from services.document_recognition_service import DocumentRecognitionService
            service = DocumentRecognitionService()
            result = service.compare_with_database(document, user=request.user)

            return UnifiedResponse.success(data=result)

        except Exception as e:
            logger.error(f"比对失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'比对失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_from_recognition(self, request, pk=None):
        """
        根据识别结果更新记录
        """
        document = self.get_object()
        
        if document.recognition_status != 'completed':
            return UnifiedResponse.error(
                message='证书尚未完成识别，请先进行识别',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        fields = request.data.get('fields', None)

        try:
            from services.document_recognition_service import DocumentRecognitionService
            service = DocumentRecognitionService()
            result = service.update_from_recognition(document, fields=fields, user=request.user)

            return UnifiedResponse.success(data=result)

        except Exception as e:
            logger.error(f"更新失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'更新失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def batch_recognize(self, request):
        """
        批量识别证书
        """
        ids = request.data.get('ids', [])
        
        if not ids:
            return UnifiedResponse.validation_error(errors=None, message='请提供要识别的证书ID列表')

        try:
            from services.document_recognition_service import DocumentRecognitionService
            service = DocumentRecognitionService()
            result = service.batch_recognize(ids, user=request.user)

            return UnifiedResponse.success(data=result)

        except Exception as e:
            logger.error(f"批量识别失败: {str(e)}")
            return UnifiedResponse.error(
                message=f'批量识别失败: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def audit_logs(self, request):
        """
        获取审计日志
        """
        document_id = request.query_params.get('document_id')
        
        queryset = DocumentAuditLog.objects.all()
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        queryset = queryset[:100]
        serializer = DocumentAuditLogSerializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)


class EnterpriseKeyPersonnelViewSet(BaseViewSet):
    """
    企业关键人员视图集
    """
    queryset = EnterpriseKeyPersonnel.objects.select_related('enterprise')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'personnel_type', 'certificate_status', 'is_available']
    search_fields = ['name', 'certificate_major', 'certificate_number', 'builder_certificate']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        根据动作选择序列化器
        """
        if self.action == 'list':
            return EnterpriseKeyPersonnelListSerializer
        return EnterpriseKeyPersonnelSerializer

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """
        获取证书即将过期的人员
        """
        from datetime import date, timedelta

        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30

        today = date.today()
        expiry_date = today + timedelta(days=days)

        personnel = self.queryset.filter(
            is_available=True,
            expiry_date__lte=expiry_date,
            expiry_date__gte=today
        ).order_by('expiry_date')

        serializer = self.get_serializer(personnel, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """
        获取证书已过期的人员
        """
        from datetime import date

        today = date.today()
        personnel = self.queryset.filter(
            expiry_date__lt=today
        ).order_by('-expiry_date')

        serializer = self.get_serializer(personnel, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        获取可用于投标的人员
        """
        enterprise_id = request.query_params.get('enterprise')
        personnel_type = request.query_params.get('personnel_type')

        queryset = self.queryset.filter(is_available=True)
        if enterprise_id:
            queryset = queryset.filter(enterprise_id=enterprise_id)
        if personnel_type:
            queryset = queryset.filter(personnel_type=personnel_type)

        serializer = self.get_serializer(queryset, many=True)
        return UnifiedResponse.success(data=serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """
        切换可用状态
        """
        personnel = self.get_object()
        personnel.is_available = not personnel.is_available
        personnel.save()

        return UnifiedResponse.success(
            data={'is_available': personnel.is_available},
            message='已设置为可用' if personnel.is_available else '已设置为不可用'
        )
