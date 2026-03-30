"""
企业仓储
提供企业相关的数据访问接口
"""
from typing import List, Dict, Any, Optional
from django.db import transaction

from .base_repository import BaseRepository
from apps.enterprise.models import (
    Enterprise,
    EnterpriseQualification,
    EnterprisePerformance,
    EnterpriseContact,
    EnterpriseKeyPersonnel,
)


class EnterpriseRepository(BaseRepository[Enterprise]):
    """
    企业仓储
    提供企业的数据访问接口
    """

    def __init__(self):
        super().__init__(Enterprise)

    def get_by_user(self, user_id: int) -> List[Enterprise]:
        """
        获取用户创建的所有企业

        Args:
            user_id: 用户ID

        Returns:
            List[Enterprise]: 企业列表
        """
        return list(self.model.objects.filter(created_by_id=user_id))

    def get_with_qualifications(self, enterprise_id: int) -> Optional[Enterprise]:
        """
        获取企业及其资质信息

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[Enterprise]: 企业实例
        """
        return self.model.objects.prefetch_related('qualifications').filter(id=enterprise_id).first()

    def get_with_performances(self, enterprise_id: int) -> Optional[Enterprise]:
        """
        获取企业及其业绩信息

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[Enterprise]: 企业实例
        """
        return self.model.objects.prefetch_related('performances').filter(id=enterprise_id).first()

    def get_user_enterprises(self, user_id: int) -> List[Enterprise]:
        """
        获取用户有权访问的所有企业

        Args:
            user_id: 用户ID

        Returns:
            List[Enterprise]: 企业列表
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()

        if not user:
            return []

        if user.is_admin():
            return list(self.model.objects.all())

        return list(self.model.objects.filter(created_by_id=user_id))

    def search(self, keyword: str, user_id: int = None) -> List[Enterprise]:
        """
        搜索企业

        Args:
            keyword: 搜索关键词
            user_id: 用户ID（可选，用于权限过滤）

        Returns:
            List[Enterprise]: 匹配的企业列表
        """
        queryset = self.model.objects.filter(
            models.Q(name__icontains=keyword) |
            models.Q(credit_code__icontains=keyword) |
            models.Q(business_scope__icontains=keyword)
        )

        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(id=user_id).first()
            if user and not user.is_admin():
                queryset = queryset.filter(created_by_id=user_id)

        return list(queryset)

    @transaction.atomic
    def create_with_relations(self, data: Dict[str, Any]) -> Enterprise:
        """
        创建企业及其关联数据

        Args:
            data: 包含企业基本信息和关联数据的字典

        Returns:
            Enterprise: 创建的企业实例
        """
        from apps.enterprise.models import EnterpriseBidConfig, EnterpriseMatchRule

        enterprise_data = data.copy()
        qualifications_data = enterprise_data.pop('qualifications', [])
        contacts_data = enterprise_data.pop('contacts', [])
        bid_config_data = enterprise_data.pop('bid_config', None)

        enterprise = self.create(**enterprise_data)

        if qualifications_data:
            for qual_data in qualifications_data:
                qual_data['enterprise_id'] = enterprise.id
                EnterpriseQualification.objects.create(**qual_data)

        if contacts_data:
            for contact_data in contacts_data:
                contact_data['enterprise_id'] = enterprise.id
                EnterpriseContact.objects.create(**contact_data)

        if bid_config_data:
            bid_config_data['enterprise_id'] = enterprise.id
            EnterpriseBidConfig.objects.create(**bid_config_data)

        if not EnterpriseMatchRule.objects.filter(enterprise=enterprise).exists():
            EnterpriseMatchRule.objects.create(
                enterprise=enterprise,
                name='默认规则',
                rule_type='auto',
                is_active=True
            )

        return enterprise

    def get_qualifications(self, enterprise_id: int) -> List[EnterpriseQualification]:
        """
        获取企业的资质列表

        Args:
            enterprise_id: 企业ID

        Returns:
            List[EnterpriseQualification]: 资质列表
        """
        return list(EnterpriseQualification.objects.filter(enterprise_id=enterprise_id))

    def get_performances(self, enterprise_id: int) -> List[EnterprisePerformance]:
        """
        获取企业的业绩列表

        Args:
            enterprise_id: 企业ID

        Returns:
            List[EnterprisePerformance]: 业绩列表
        """
        return list(EnterprisePerformance.objects.filter(enterprise_id=enterprise_id))

    def get_contacts(self, enterprise_id: int) -> List[EnterpriseContact]:
        """
        获取企业的联系人列表

        Args:
            enterprise_id: 企业ID

        Returns:
            List[EnterpriseContact]: 联系人列表
        """
        return list(EnterpriseContact.objects.filter(enterprise_id=enterprise_id))

    def get_key_personnel(self, enterprise_id: int) -> List[EnterpriseKeyPersonnel]:
        """
        获取企业的关键人员列表

        Args:
            enterprise_id: 企业ID

        Returns:
            List[EnterpriseKeyPersonnel]: 关键人员列表
        """
        return list(EnterpriseKeyPersonnel.objects.filter(enterprise_id=enterprise_id))


from django.db import models