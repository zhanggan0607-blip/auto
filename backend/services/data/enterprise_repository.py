from typing import List, Dict, Any, Optional
from django.db import models, transaction

from .base_repository import BaseRepository
from apps.enterprise.models import (
    Enterprise,
    EnterpriseQualification,
    EnterprisePerformance,
    EnterpriseContact,
    EnterpriseKeyPersonnel,
)


class EnterpriseRepository(BaseRepository[Enterprise]):

    def __init__(self):
        super().__init__(Enterprise)

    def get_by_user(self, user_id: int) -> List[Enterprise]:
        return list(self.model.objects.filter(created_by_id=user_id))

    def get_with_qualifications(self, enterprise_id: int) -> Optional[Enterprise]:
        return self.model.objects.prefetch_related('qualifications').filter(id=enterprise_id).first()

    def get_with_performances(self, enterprise_id: int) -> Optional[Enterprise]:
        return self.model.objects.prefetch_related('performances').filter(id=enterprise_id).first()

    def get_user_enterprises(self, user_id: int) -> List[Enterprise]:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(id=user_id).first()

        if not user:
            return []

        if user.is_staff or user.is_superuser:
            return list(self.model.objects.all())

        return list(self.model.objects.filter(created_by_id=user_id))

    def search(self, keyword: str, user_id: int = None) -> List[Enterprise]:
        queryset = self.model.objects.filter(
            models.Q(name__icontains=keyword) |
            models.Q(credit_code__icontains=keyword)
        )

        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(id=user_id).first()
            if user and not (user.is_staff or user.is_superuser):
                queryset = queryset.filter(created_by_id=user_id)

        return list(queryset)

    @transaction.atomic
    def create_with_relations(self, data: Dict[str, Any]) -> Enterprise:
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
        return list(EnterpriseQualification.objects.filter(enterprise_id=enterprise_id))

    def get_performances(self, enterprise_id: int) -> List[EnterprisePerformance]:
        return list(EnterprisePerformance.objects.filter(enterprise_id=enterprise_id))

    def get_contacts(self, enterprise_id: int) -> List[EnterpriseContact]:
        return list(EnterpriseContact.objects.filter(enterprise_id=enterprise_id))

    def get_key_personnel(self, enterprise_id: int) -> List[EnterpriseKeyPersonnel]:
        return list(EnterpriseKeyPersonnel.objects.filter(enterprise_id=enterprise_id))
