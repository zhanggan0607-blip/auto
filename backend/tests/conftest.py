"""
测试配置和 fixtures
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """
    API客户端 fixture
    """
    return APIClient()


@pytest.fixture
def user(db):
    """
    创建测试用户
    """
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    return user


@pytest.fixture
def admin_user(db):
    """
    创建管理员用户
    """
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpassword123'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, user):
    """
    已认证的API客户端
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """
    管理员API客户端
    """
    api_client.force_authenticate(user=admin_user)
    return api_client
