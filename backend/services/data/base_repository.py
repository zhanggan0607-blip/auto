"""
仓储基类
提供通用的数据访问接口
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from django.db import models
from django.db.models import QuerySet

T = TypeVar('T', bound=models.Model)


class BaseRepository(Generic[T]):
    """
    数据仓储基类
    定义通用的CRUD操作接口
    """

    def __init__(self, model: Type[T]):
        """
        初始化仓储

        Args:
            model: Django模型类
        """
        self.model = model

    def get_queryset(self) -> QuerySet:
        """
        获取查询集

        Returns:
            QuerySet: Django查询集
        """
        return self.model.objects.all()

    def filter(self, **kwargs) -> QuerySet:
        """
        过滤查询

        Args:
            **kwargs: 过滤条件

        Returns:
            QuerySet: 过滤后的查询集
        """
        return self.get_queryset().filter(**kwargs)

    def get(self, **kwargs) -> Optional[T]:
        """
        获取单个对象

        Args:
            **kwargs: 查询条件

        Returns:
            Optional[T]: 模型实例或None
        """
        try:
            return self.get_queryset().get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def get_or_404(self, **kwargs) -> T:
        """
        获取单个对象，不存在则抛出404

        Args:
            **kwargs: 查询条件

        Returns:
            T: 模型实例

        Raises:
            Http404: 对象不存在
        """
        from django.http import Http404
        try:
            return self.get_queryset().get(**kwargs)
        except self.model.DoesNotExist:
            raise Http404(f"{self.model.__name__} not found")

    def create(self, **kwargs) -> T:
        """
        创建对象

        Args:
            **kwargs: 对象属性

        Returns:
            T: 创建的模型实例
        """
        return self.model.objects.create(**kwargs)

    def update(self, pk: int, **kwargs) -> Optional[T]:
        """
        更新对象

        Args:
            pk: 对象主键
            **kwargs: 更新的属性

        Returns:
            Optional[T]: 更新后的模型实例或None
        """
        instance = self.get(pk=pk)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
        return instance

    def delete(self, pk: int) -> bool:
        """
        删除对象

        Args:
            pk: 对象主键

        Returns:
            bool: 是否删除成功
        """
        instance = self.get(pk=pk)
        if instance:
            instance.delete()
            return True
        return False

    def bulk_create(self, data: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建

        Args:
            data: 对象数据列表

        Returns:
            List[T]: 创建的模型实例列表
        """
        return self.model.objects.bulk_create([
            self.model(**item) for item in data
        ])

    def exists(self, **kwargs) -> bool:
        """
        检查对象是否存在

        Args:
            **kwargs: 查询条件

        Returns:
            bool: 是否存在
        """
        return self.get_queryset().filter(**kwargs).exists()

    def count(self, **kwargs) -> int:
        """
        统计数量

        Args:
            **kwargs: 过滤条件

        Returns:
            int: 数量
        """
        return self.get_queryset().filter(**kwargs).count()

    def first(self, **kwargs) -> Optional[T]:
        """
        获取第一个对象

        Args:
            **kwargs: 查询条件

        Returns:
            Optional[T]: 模型实例或None
        """
        return self.get_queryset().filter(**kwargs).first()

    def last(self, **kwargs) -> Optional[T]:
        """
        获取最后一个对象

        Args:
            **kwargs: 查询条件

        Returns:
            Optional[T]: 模型实例或None
        """
        return self.get_queryset().filter(**kwargs).last()

    def all(self) -> QuerySet:
        """
        获取所有对象

        Returns:
            QuerySet: 所有对象的查询集
        """
        return self.get_queryset().all()

    def paginate(self, page: int = 1, page_size: int = 20, **kwargs) -> Dict[str, Any]:
        """
        分页查询

        Args:
            page: 页码
            page_size: 每页数量
            **kwargs: 过滤条件

        Returns:
            Dict: 包含items和pagination的分页结果
        """
        queryset = self.get_queryset().filter(**kwargs)
        total = queryset.count()
        items = queryset[(page - 1) * page_size:page * page_size]

        return {
            'items': list(items),
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        }