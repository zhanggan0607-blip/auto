"""
公共模型Mixins
提供通用的模型功能混入类
"""
from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    """
    时间戳Mixin
    自动管理创建时间和更新时间
    """
    created_at = models.DateTimeField('创建时间', default=timezone.now, editable=False)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    软删除Mixin
    支持数据的软删除，不真正从数据库移除
    """
    is_deleted = models.BooleanField('已删除', default=False, db_index=True)
    deleted_at = models.DateTimeField('删除时间', blank=True, null=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        """执行软删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """恢复软删除"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class UserTrackMixin(models.Model):
    """
    用户追踪Mixin
    自动记录创建人和更新人
    """
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='创建人'
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='更新人'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """保存时自动设置创建人/更新人"""
        from django.conf import settings
        from rest_framework.request import Request

        if not self.pk:
            try:
                request = kwargs.pop('request', None)
                if request and hasattr(request, 'user') and request.user.is_authenticated:
                    self.created_by = request.user
            except Exception:
                pass
        else:
            try:
                request = kwargs.pop('request', None)
                if request and hasattr(request, 'user') and request.user.is_authenticated:
                    self.updated_by = request.user
            except Exception:
                pass

        super().save(*args, **kwargs)


class StatusMixin(models.Model):
    """
    状态Mixin
    提供通用状态管理
    """
    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
    ]

    is_active = models.BooleanField('是否启用', default=True, db_index=True)

    class Meta:
        abstract = True

    def enable(self):
        """启用"""
        self.is_active = True
        self.save(update_fields=['is_active'])

    def disable(self):
        """禁用"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class OrderingMixin(models.Model):
    """
    排序Mixin
    提供通用排序字段
    """
    order = models.IntegerField('排序', default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ['order', '-created_at']


class DescriptionMixin(models.Model):
    """
    描述Mixin
    提供通用描述字段
    """
    description = models.TextField('描述', blank=True, null=True)
    remarks = models.TextField('备注', blank=True, null=True)

    class Meta:
        abstract = True


class CompositeModelMixin(
    TimestampMixin,
    SoftDeleteMixin,
    UserTrackMixin,
    StatusMixin,
    OrderingMixin,
    DescriptionMixin,
    models.Model
):
    """
    复合模型Mixin
    组合所有通用Mixin，适用于大多数业务模型
    使用方式：
        class MyModel(CompositeModelMixin, models.Model):
            name = models.CharField('名称', max_length=100)
    """
    class Meta:
        abstract = True
