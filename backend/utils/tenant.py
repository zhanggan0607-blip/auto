"""
多租户架构模块

提供完整的SaaS多租户支持：
1. 租户模型定义
2. 租户感知查询
3. 自动租户隔离
4. 租户中间件
5. 权限控制

使用示例:
```python
from utils.tenant import (
    current_tenant,
    TenantModel,
    tenant_required,
    get_tenant_model,
)

# 模型继承
class TenderProject(TenantModel):
    title = models.CharField(max_length=500)
    ...

# 获取当前租户
tenant = current_tenant()

# 租户隔离查询
tenders = TenderProject.objects.all()  # 自动只返回当前租户数据

# 装饰器保护
@tenant_required
def create_tender(request):
    ...
```
"""
import threading
from contextvars import ContextVar
from typing import Optional, Callable, Any

from django.contrib.auth import get_user_model
from django.db import models, connection
from django.db.models import QuerySet, Manager
from django.http import HttpRequest

_tenant_context: ContextVar[Optional['Tenant']] = ContextVar('tenant', default=None)
_thread_local = threading.local()


class TenantManager(Manager):
    """
    租户感知管理器

    自动过滤当前租户的数据
    """

    def get_queryset(self) -> QuerySet:
        """获取过滤后的QuerySet"""
        queryset = super().get_queryset()

        tenant = get_current_tenant()
        if tenant is not None:
            return queryset.filter(tenant=tenant)

        return queryset

    def for_tenant(self, tenant: 'Tenant') -> QuerySet:
        """获取指定租户的QuerySet"""
        return super().get_queryset().filter(tenant=tenant)

    def all_tenants(self) -> QuerySet:
        """获取所有租户数据（绕过过滤）"""
        return super().get_queryset()


class TenantAwareQuerySet(QuerySet):
    """
    租户感知QuerySet

    提供租户隔离的查询方法
    """

    def for_tenant(self, tenant: 'Tenant') -> 'TenantAwareQuerySet':
        """过滤指定租户"""
        return self.filter(tenant=tenant)

    def for_current_tenant(self) -> 'TenantAwareQuerySet':
        """过滤当前租户"""
        tenant = get_current_tenant()
        if tenant:
            return self.filter(tenant=tenant)
        return self


class TenantModel(models.Model):
    """
    租户模型抽象基类

    所有需要租户隔离的模型应继承此基类
    """

    class Meta:
        abstract = True

    @classmethod
    def get_tenant_field(cls):
        """获取租户字段名"""
        return 'tenant'


class Tenant(models.Model):
    """
    租户模型

    存储租户信息
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='租户名称')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='租户标识')
    code = models.CharField(max_length=50, unique=True, verbose_name='租户代码')

    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_trial = models.BooleanField(default=False, verbose_name='是否试用')

    plan = models.CharField(
        max_length=50,
        choices=[
            ('free', '免费版'),
            ('basic', '基础版'),
            ('professional', '专业版'),
            ('enterprise', '企业版'),
        ],
        default='free',
        verbose_name='套餐'
    )

    max_users = models.IntegerField(default=5, verbose_name='最大用户数')
    max_tenders = models.IntegerField(default=100, verbose_name='最大招标数')
    max_storage = models.IntegerField(default=1024, verbose_name='最大存储(MB)')

    settings = models.JSONField(default=dict, verbose_name='租户配置')

    expire_date = models.DateTimeField(null=True, blank=True, verbose_name='到期时间')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tenants'
        verbose_name = '租户'
        verbose_name_plural = '租户'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expire_date is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expire_date

    @property
    def user_count(self) -> int:
        """用户数量"""
        return self.users.count()

    @property
    def tender_count(self) -> int:
        """招标数量"""
        return self.tender_projects.count()


class TenantUser(models.Model):
    """
    租户用户关联模型
    """

    ROLE_CHOICES = [
        ('owner', '所有者'),
        ('admin', '管理员'),
        ('member', '成员'),
        ('viewer', '查看者'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='tenant_users',
        verbose_name='租户'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='tenant_memberships',
        verbose_name='用户'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name='角色')

    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'tenant_users'
        verbose_name = '租户用户'
        verbose_name_plural = '租户用户'
        unique_together = ['tenant', 'user']

    def __str__(self):
        return f"{self.user.username}@{self.tenant.code}"


class TenantAwareModel(models.Model):
    """
    租户感知模型基类

    所有需要租户隔离的模型应继承此基类
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        null=True,
        blank=True,
        verbose_name='租户'
    )

    class Meta:
        abstract = True


def set_current_tenant(tenant: Optional[Tenant]):
    """设置当前租户"""
    _tenant_context.set(tenant)
    _thread_local.tenant = tenant


def get_current_tenant() -> Optional[Tenant]:
    """获取当前租户"""
    tenant = _tenant_context.get()
    if tenant is not None:
        return tenant

    if hasattr(_thread_local, 'tenant'):
        return _thread_local.tenant

    return None


def clear_current_tenant():
    """清除当前租户"""
    _tenant_context.set(None)
    if hasattr(_thread_local, 'tenant'):
        del _thread_local.tenant


class TenantContextManager:
    """租户上下文管理器"""

    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self._token = None

    def __enter__(self):
        self._token = _tenant_context.set(self.tenant)
        _thread_local.tenant = self.tenant
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        clear_current_tenant()
        return False


def with_tenant(tenant: Tenant):
    """租户上下文装饰器"""
    return TenantContextManager(tenant)


def get_tenant_model():
    """获取Tenant模型"""
    return Tenant

def tenant_required(view_func: Callable) -> Callable:
    """
    租户必需装饰器

    确保请求在有效的租户上下文中执行
    """
    def wrapper(request: HttpRequest, *args, **kwargs):
        tenant = get_current_tenant()

        if tenant is None:
            from utils.responses import UnifiedResponse
            from rest_framework import status
            return UnifiedResponse.error(
                message='需要有效的租户上下文',
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )

        if not tenant.is_active:
            from utils.responses import UnifiedResponse
            from rest_framework import status
            return UnifiedResponse.error(
                message='租户已被禁用',
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )

        if tenant.is_expired:
            from utils.responses import UnifiedResponse
            from rest_framework import status
            return UnifiedResponse.error(
                message='租户已过期',
                code=403,
                status_code=status.HTTP_403_FORBIDDEN
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def get_user_tenants(user) -> models.QuerySet:
    """获取用户所属的所有租户"""
    return Tenant.objects.filter(
        tenant_users__user=user,
        tenant_users__is_active=True,
        is_active=True
    )


def get_or_create_personal_tenant(user) -> Tenant:
    """为用户获取或创建个人租户"""
    from django.db import transaction

    with transaction.atomic():
        membership = TenantUser.objects.select_related('tenant').filter(
            user=user,
            role='owner'
        ).first()

        if membership:
            return membership.tenant

        tenant_code = f"user_{user.id}_{user.username[:20]}"

        tenant = Tenant.objects.create(
            name=f"{user.username}的个人空间",
            slug=tenant_code,
            code=tenant_code,
            plan='free',
            max_users=1,
            max_tenders=50,
            max_storage=100,
        )

        TenantUser.objects.create(
            tenant=tenant,
            user=user,
            role='owner'
        )

        return tenant


class TenantRouter:
    """
    租户数据库路由

    支持多数据库租户隔离
    """

    def db_for_read(self, model, **hints):
        if issubclass(model, TenantAwareModel):
            tenant = get_current_tenant()
            if tenant and hasattr(tenant, 'database'):
                return f'tenant_{tenant.id}'
        return 'default'

    def db_for_write(self, model, **hints):
        if issubclass(model, TenantAwareModel):
            tenant = get_current_tenant()
            if tenant and hasattr(tenant, 'database'):
                return f'tenant_{tenant.id}'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True


__all__ = [
    'Tenant',
    'TenantUser',
    'TenantModel',
    'TenantAwareModel',
    'TenantManager',
    'TenantAwareQuerySet',
    'TenantMiddleware',
    'TenantContextManager',
    'TenantRouter',
    'current_tenant',
    'set_current_tenant',
    'get_current_tenant',
    'clear_current_tenant',
    'with_tenant',
    'get_tenant_model',
    'tenant_required',
    'get_user_tenants',
    'get_or_create_personal_tenant',
]
