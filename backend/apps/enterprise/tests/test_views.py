"""
企业模块单元测试
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.enterprise.models import (
    Enterprise, EnterpriseQualification, EnterprisePerformance,
    EnterpriseKeyPersonnel, EnterpriseDocument
)

User = get_user_model()


@pytest.mark.django_db
class TestEnterpriseModel:
    """
    企业模型测试
    """
    
    def test_create_enterprise(self, user):
        """
        测试创建企业
        """
        enterprise = Enterprise.objects.create(
            name='测试企业有限公司',
            credit_code='91310000MA1FL5XX0X',
            enterprise_type='limited',
            created_by=user
        )
        
        assert enterprise.id is not None
        assert enterprise.name == '测试企业有限公司'
        assert enterprise.credit_code == '91310000MA1FL5XX0X'
        assert enterprise.is_active is True
    
    def test_enterprise_str(self, user):
        """
        测试企业字符串表示
        """
        enterprise = Enterprise.objects.create(
            name='测试企业',
            created_by=user
        )
        assert str(enterprise) == '测试企业'
    
    def test_enterprise_unique_credit_code(self, user):
        """
        测试统一社会信用代码唯一性
        """
        Enterprise.objects.create(
            name='企业1',
            credit_code='91310000MA1FL5XX0X',
            created_by=user
        )
        
        with pytest.raises(Exception):
            Enterprise.objects.create(
                name='企业2',
                credit_code='91310000MA1FL5XX0X',
                created_by=user
            )


@pytest.mark.django_db
class TestEnterpriseAPI:
    """
    企业API测试
    """
    
    def test_list_enterprises_unauthorized(self, api_client):
        """
        测试未授权访问企业列表
        """
        response = api_client.get('/api/v1/enterprise/enterprises/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_enterprises_authorized(self, authenticated_client, user):
        """
        测试已授权访问企业列表
        """
        Enterprise.objects.create(
            name='测试企业',
            created_by=user
        )
        
        response = authenticated_client.get('/api/v1/enterprise/enterprises/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_enterprise(self, authenticated_client):
        """
        测试创建企业
        """
        data = {
            'name': '新测试企业',
            'credit_code': '91310000MA1FL5XX1X',
            'enterprise_type': 'limited'
        }
        
        response = authenticated_client.post(
            '/api/v1/enterprise/enterprises/',
            data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == '新测试企业'
    
    def test_create_enterprise_missing_name(self, authenticated_client):
        """
        测试创建企业缺少名称
        """
        data = {
            'credit_code': '91310000MA1FL5XX2X'
        }
        
        response = authenticated_client.post(
            '/api/v1/enterprise/enterprises/',
            data
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_search_enterprise(self, authenticated_client, user):
        """
        测试搜索企业
        """
        Enterprise.objects.create(
            name='上海建筑公司',
            credit_code='91310000MA1FL5XX0X',
            created_by=user
        )
        Enterprise.objects.create(
            name='北京科技公司',
            credit_code='91310000MA1FL5XX1X',
            created_by=user
        )
        
        response = authenticated_client.get(
            '/api/v1/enterprise/enterprises/',
            {'search': '上海'}
        )
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestEnterpriseQualification:
    """
    企业资质测试
    """
    
    def test_create_qualification(self, user):
        """
        测试创建资质
        """
        enterprise = Enterprise.objects.create(
            name='测试企业',
            created_by=user
        )
        
        qualification = EnterpriseQualification.objects.create(
            enterprise=enterprise,
            qualification_type='construction_general',
            qualification_name='建筑工程施工总承包一级',
            certificate_number='D123000001'
        )
        
        assert qualification.id is not None
        assert qualification.qualification_name == '建筑工程施工总承包一级'


@pytest.mark.django_db
class TestEnterpriseKeyPersonnel:
    """
    企业关键人员测试
    """
    
    def test_create_key_personnel(self, user):
        """
        测试创建关键人员
        """
        enterprise = Enterprise.objects.create(
            name='测试企业',
            created_by=user
        )
        
        personnel = EnterpriseKeyPersonnel.objects.create(
            enterprise=enterprise,
            personnel_type='project_manager',
            name='张三',
            id_number='310101199001011234'
        )
        
        assert personnel.id is not None
        assert personnel.name == '张三'
        assert personnel.personnel_type == 'project_manager'
    
    def test_personnel_availability_toggle(self, user):
        """
        测试人员可用性切换
        """
        enterprise = Enterprise.objects.create(
            name='测试企业',
            created_by=user
        )
        
        personnel = EnterpriseKeyPersonnel.objects.create(
            enterprise=enterprise,
            personnel_type='project_manager',
            name='张三'
        )
        
        assert personnel.is_available is True
        
        personnel.is_available = False
        personnel.save()
        
        personnel.refresh_from_db()
        assert personnel.is_available is False


@pytest.mark.django_db
class TestEnterprisePerformance:
    """
    企业业绩测试
    """
    
    def test_create_performance(self, user):
        """
        测试创建业绩
        """
        enterprise = Enterprise.objects.create(
            name='测试企业',
            created_by=user
        )
        
        performance = EnterprisePerformance.objects.create(
            enterprise=enterprise,
            performance_type='construction',
            project_name='测试项目',
            contract_amount=1000000.00
        )
        
        assert performance.id is not None
        assert performance.project_name == '测试项目'
