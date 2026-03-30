"""
公共模型基类
为业务模型提供统一的基类功能
"""
from django.db import models
from common.models.mixins import CompositeModelMixin


class BaseModel(CompositeModelMixin, models.Model):
    """
    基础模型类
    所有业务模型建议继承此类

    已集成的功能：
    - TimestampMixin: 创建/更新时间
    - SoftDeleteMixin: 软删除
    - UserTrackMixin: 创建人/更新人追踪
    - StatusMixin: 启用/停用状态
    - OrderingMixin: 排序
    - DescriptionMixin: 描述/备注

    使用示例：
        class Enterprise(BaseModel):
            name = models.CharField('企业名称', max_length=300)

            class Meta:
                db_table = 'enterprises'
                verbose_name = '企业'
                verbose_name_plural = verbose_name
    """

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """
    单例模型基类
    用于配置表等需要全局唯一实例的场景
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is None:
            existing = self.__class__.objects.filter(pk=self.pk).first()
            if existing:
                raise ValueError(f"{self.__class__.__name__} 只能存在一个实例")
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """获取唯一实例，不存在则创建"""
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance
