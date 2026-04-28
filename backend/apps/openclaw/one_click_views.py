"""
一键自动化投标API视图
操作员只需输入企业资料和指定网站，系统自动完成全流程
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from common.views.base import APIResponseMixin
from services.one_click_automation import one_click_automation_service
from utils.permissions.enterprise import verify_enterprise_ownership


logger = logging.getLogger(__name__)


class OneClickAutomationViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    一键自动化投标API
    """
    permission_classes = [IsAuthenticated]

    def _verify_enterprise_access(self, request, enterprise_id):
        """
        验证用户是否有权操作指定企业

        Args:
            request: 请求对象
            enterprise_id: 企业ID

        Returns:
            tuple: (is_verified: bool, enterprise_obj or error_msg)
        """
        from apps.enterprise.models import Enterprise

        if not enterprise_id:
            return False, "请提供企业ID"

        try:
            enterprise = Enterprise.objects.get(id=enterprise_id)
        except Enterprise.DoesNotExist:
            return False, "企业不存在"

        if not verify_enterprise_ownership(request.user, enterprise):
            return False, "无权限操作该企业"

        return True, enterprise

    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        一键启动自动化投标

        请求参数:
        - enterprise_id: 企业ID（必填）
        - website_ids: 网站ID列表（可选，为空则使用所有启用的网站）
        - keywords: 搜索关键词（可选）
        - auto_bid_threshold: 自动投标阈值（默认60）
        - auto_document_threshold: 标书自动通过阈值（默认90）
        - notification_enabled: 是否启用通知（默认True）
        - auto_upload: 是否自动上传（默认False）

        返回:
        - task_id: 任务ID
        - status: 任务状态
        """
        enterprise_id = request.data.get('enterprise_id')

        is_verified, enterprise = self._verify_enterprise_access(request, enterprise_id)
        if not is_verified:
            return Response({
                'success': False,
                'message': enterprise
            }, status=status.HTTP_403_FORBIDDEN)

        website_ids = request.data.get('website_ids', [])
        keywords = request.data.get('keywords', [])
        config = {
            'auto_bid_threshold': request.data.get('auto_bid_threshold', 60),
            'auto_document_threshold': request.data.get('auto_document_threshold', 90),
            'notification_enabled': request.data.get('notification_enabled', True),
            'auto_upload': request.data.get('auto_upload', False)
        }

        try:
            result = one_click_automation_service.start_automation(
                enterprise_id=enterprise.id,
                website_ids=website_ids,
                keywords=keywords,
                config=config
            )

            return Response({
                'success': True,
                'data': result
            })

        except Exception as e:
            logger.error(f"启动自动化任务失败: {str(e)}")
            return Response({
                'success': False,
                'message': f'启动失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        获取任务状态

        参数:
        - task_id: 任务ID
        """
        task_id = request.query_params.get('task_id')

        if not task_id:
            return Response({
                'success': False,
                'message': '请提供任务ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = one_click_automation_service.get_task_status(task_id)

        if result:
            return Response({
                'success': True,
                'data': result
            })
        else:
            return Response({
                'success': False,
                'message': '任务不存在'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def tasks(self, request):
        """
        获取任务列表

        参数:
        - status: 任务状态过滤（可选）
        """
        status_filter = request.query_params.get('status')
        tasks = one_click_automation_service.list_tasks(status=status_filter)

        return Response({
            'success': True,
            'data': tasks
        })

    @action(detail=False, methods=['post'])
    def quick_start(self, request):
        """
        快速启动（简化版）

        只需提供企业名称，系统自动：
        1. 查找或创建企业（仅创建者可以使用自己的企业）
        2. 使用所有启用的网站
        3. 启动自动化流程
        """
        enterprise_name = request.data.get('enterprise_name')
        keywords = request.data.get('keywords', [])
        websites = request.data.get('websites', [])

        if not enterprise_name:
            return Response({
                'success': False,
                'message': '请提供企业名称'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.enterprise.models import Enterprise
            from apps.crawler.models import WebsiteTemplate

            enterprise = Enterprise.objects.filter(name=enterprise_name).first()

            if enterprise:
                if not verify_enterprise_ownership(request.user, enterprise):
                    return Response({
                        'success': False,
                        'message': '无权限操作该企业'
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                enterprise = Enterprise.objects.create(
                    name=enterprise_name,
                    created_by=request.user
                )

            website_ids = []
            if websites:
                website_ids = list(WebsiteTemplate.objects.filter(
                    name__in=websites,
                    is_active=True
                ).values_list('id', flat=True))

            result = one_click_automation_service.start_automation(
                enterprise_id=enterprise.id,
                website_ids=website_ids,
                keywords=keywords
            )

            return Response({
                'success': True,
                'data': {
                    **result,
                    'enterprise_name': enterprise_name,
                    'enterprise_created': not Enterprise.objects.filter(name=enterprise_name, created_by=request.user).exists()
                }
            })

        except Exception as e:
            logger.error(f"快速启动失败: {str(e)}")
            return Response({
                'success': False,
                'message': f'启动失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EnterpriseQuickSetupViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    企业快速设置API
    """
    permission_classes = [IsAuthenticated]

    def _verify_enterprise_modification(self, request, enterprise_id):
        """
        验证用户是否有权修改指定企业

        Args:
            request: 请求对象
            enterprise_id: 企业ID

        Returns:
            tuple: (is_verified: bool, enterprise_obj or error_msg)
        """
        from apps.enterprise.models import Enterprise

        if not enterprise_id:
            return False, "请提供企业ID"

        try:
            enterprise = Enterprise.objects.get(id=enterprise_id)
        except Enterprise.DoesNotExist:
            return False, "企业不存在"

        if not verify_enterprise_ownership(request.user, enterprise):
            return False, "无权限修改该企业"

        return True, enterprise

    @action(detail=False, methods=['post'])
    def setup(self, request):
        """
        快速设置企业资料

        一次性提交企业所有资料，包括：
        - 基本信息
        - 资质信息
        - 业绩信息
        - 联系人信息
        """
        from apps.enterprise.models import (
            Enterprise, EnterpriseQualification, EnterprisePerformance, EnterpriseContact
        )

        data = request.data
        credit_code = data.get('credit_code')

        try:
            if credit_code:
                existing_enterprise = Enterprise.objects.filter(credit_code=credit_code).first()
                if existing_enterprise:
                    if not verify_enterprise_ownership(request.user, existing_enterprise):
                        return Response({
                            'success': False,
                            'message': '无权限修改该企业'
                        }, status=status.HTTP_403_FORBIDDEN)
                    enterprise = existing_enterprise
                    created = False
                    for field in ['name', 'legal_person', 'registered_capital', 'province', 'city',
                                  'address', 'business_scope', 'contact_person', 'contact_phone',
                                  'contact_email', 'bank_name', 'bank_account']:
                        if data.get(field):
                            setattr(enterprise, field, data.get(field))
                    enterprise.save()
                else:
                    enterprise = Enterprise.objects.create(
                        credit_code=credit_code,
                        name=data.get('name'),
                        legal_person=data.get('legal_person'),
                        registered_capital=data.get('registered_capital'),
                        province=data.get('province'),
                        city=data.get('city'),
                        address=data.get('address'),
                        business_scope=data.get('business_scope'),
                        contact_person=data.get('contact_person'),
                        contact_phone=data.get('contact_phone'),
                        contact_email=data.get('contact_email'),
                        bank_name=data.get('bank_name'),
                        bank_account=data.get('bank_account'),
                        created_by=request.user
                    )
                    created = True
            else:
                enterprise = Enterprise.objects.create(
                    name=data.get('name', f'企业-{request.user.id}'),
                    created_by=request.user
                )
                created = True

            qualifications = data.get('qualifications', [])
            for q in qualifications:
                EnterpriseQualification.objects.update_or_create(
                    enterprise=enterprise,
                    qualification_name=q.get('name'),
                    defaults={
                        'qualification_type': q.get('type', 'other'),
                        'grade': q.get('grade'),
                        'scope': q.get('scope'),
                        'issue_date': q.get('issue_date'),
                        'expiry_date': q.get('expiry_date'),
                        'issuing_authority': q.get('issuing_authority'),
                        'is_valid': True
                    }
                )

            performances = data.get('performances', [])
            for p in performances:
                EnterprisePerformance.objects.create(
                    enterprise=enterprise,
                    project_name=p.get('project_name'),
                    project_code=p.get('project_code'),
                    performance_type=p.get('type', 'project'),
                    client_name=p.get('client_name'),
                    contract_amount=p.get('contract_amount'),
                    start_date=p.get('start_date'),
                    end_date=p.get('end_date'),
                    project_location=p.get('location'),
                    description=p.get('description')
                )

            contacts = data.get('contacts', [])
            for c in contacts:
                EnterpriseContact.objects.create(
                    enterprise=enterprise,
                    contact_type=c.get('type', 'business'),
                    name=c.get('name'),
                    position=c.get('position'),
                    phone=c.get('phone'),
                    mobile=c.get('mobile'),
                    email=c.get('email'),
                    is_primary=c.get('is_primary', False)
                )

            return Response({
                'success': True,
                'data': {
                    'enterprise_id': enterprise.id,
                    'enterprise_name': enterprise.name,
                    'created': created,
                    'qualifications_count': len(qualifications),
                    'performances_count': len(performances),
                    'contacts_count': len(contacts)
                }
            })

        except Exception as e:
            logger.error(f"设置企业资料失败: {str(e)}")
            return Response({
                'success': False,
                'message': f'设置失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def import_from_file(self, request):
        """
        从文件导入企业资料

        支持：
        - Excel文件
        - PDF文件（使用OCR识别）
        """
        from services.aliyun_ocr_service import aliyun_ocr_service

        file = request.FILES.get('file')

        if not file:
            return Response({
                'success': False,
                'message': '请上传文件'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_ext = file.name.split('.')[-1].lower()

            if file_ext in ['xlsx', 'xls']:
                import pandas as pd
                df = pd.read_excel(file)

                enterprise_data = {
                    'name': df.iloc[0].get('企业名称') if '企业名称' in df.columns else None,
                    'credit_code': df.iloc[0].get('统一社会信用代码') if '统一社会信用代码' in df.columns else None,
                    'legal_person': df.iloc[0].get('法人代表') if '法人代表' in df.columns else None,
                    'province': df.iloc[0].get('省份') if '省份' in df.columns else None,
                    'city': df.iloc[0].get('城市') if '城市' in df.columns else None,
                    'address': df.iloc[0].get('地址') if '地址' in df.columns else None,
                    'industry': df.iloc[0].get('行业') if '行业' in df.columns else None,
                    'business_scope': df.iloc[0].get('经营范围') if '经营范围' in df.columns else None,
                }

            elif file_ext == 'pdf':
                ocr_result = aliyun_ocr_service.recognize_document(file.read())

                enterprise_data = self._parse_ocr_result(ocr_result)

            else:
                return Response({
                    'success': False,
                    'message': f'不支持的文件格式: {file_ext}'
                }, status=status.HTTP_400_BAD_REQUEST)

            enterprise_data['created_by'] = request.user

            from apps.enterprise.models import Enterprise
            enterprise = Enterprise.objects.create(**enterprise_data)

            return Response({
                'success': True,
                'data': {
                    'enterprise_id': enterprise.id,
                    'enterprise_name': enterprise.name,
                    'imported_data': enterprise_data
                }
            })

        except Exception as e:
            logger.error(f"导入企业资料失败: {str(e)}")
            return Response({
                'success': False,
                'message': f'导入失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_ocr_result(self, ocr_result: dict) -> dict:
        """
        解析OCR结果
        """
        content = ocr_result.get('content', '')

        enterprise_data = {
            'name': None,
            'credit_code': None,
            'legal_person': None,
            'address': None,
        }

        lines = content.split('\n')
        for line in lines:
            if '名称' in line:
                enterprise_data['name'] = line.split('名称')[-1].strip(':： ')
            elif '信用代码' in line or '统一社会信用代码' in line:
                enterprise_data['credit_code'] = line.split('代码')[-1].strip(':： ')
            elif '法人' in line or '法定代表人' in line:
                enterprise_data['legal_person'] = line.split('人')[-1].strip(':： ')
            elif '地址' in line or '住所' in line:
                enterprise_data['address'] = line.split('址')[-1].strip(':： ')

        return enterprise_data


class WebsiteQuickSelectViewSet(APIResponseMixin, viewsets.ViewSet):
    """
    网站快速选择API
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_active(self, request):
        """
        获取所有启用的网站列表
        """
        from apps.crawler.models import WebsiteTemplate

        websites = WebsiteTemplate.objects.filter(is_active=True).values(
            'id', 'name', 'website_type', 'base_url'
        )

        return Response({
            'success': True,
            'data': list(websites)
        })

    @action(detail=False, methods=['post'])
    def select_by_type(self, request):
        """
        按类型选择网站

        参数:
        - types: 网站类型列表 ['government', 'enterprise', 'construction']
        """
        from apps.crawler.models import WebsiteTemplate

        types = request.data.get('types', [])

        websites = WebsiteTemplate.objects.filter(
            website_type__in=types,
            is_active=True
        ).values('id', 'name', 'website_type', 'base_url')

        return Response({
            'success': True,
            'data': list(websites)
        })

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        获取热门网站
        """
        from apps.crawler.models import WebsiteTemplate

        websites = WebsiteTemplate.objects.filter(
            is_active=True,
            priority__gte=0
        ).order_by('-priority').values('id', 'name', 'website_type', 'base_url')[:10]

        return Response({
            'success': True,
            'data': list(websites)
        })
