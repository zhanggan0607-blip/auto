"""
UnifiedDataService - 向量+PG统一数据操作服务

提供统一的PG+向量库双写接口，保证数据一致性

使用示例：
    from services.unified_data_service import unified_data_service

    # 保存企业数据（PG + 向量）
    enterprise = unified_data_service.save_enterprise({
        'name': 'xxx公司',
        'qualifications': ['资质1', '资质2'],
        ...
    })

    # 搜索企业（向量检索 + PG过滤）
    results = unified_data_service.search_enterprises(
        query='招标内容',
        filters={'province': '北京'},
        top_k=10
    )

    # 删除企业数据
    unified_data_service.delete_enterprise(enterprise_id)
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type
from django.db import transaction

logger = logging.getLogger(__name__)


@dataclass
class DataSyncResult:
    """数据同步结果"""
    success: bool
    pg_saved: bool = False
    vector_saved: bool = False
    error: Optional[str] = None
    pg_id: Optional[int] = None
    vector_id: Optional[str] = None


class UnifiedDataService:
    """
    统一数据服务

    统一管理结构化数据(PG)和向量数据(Chroma)的双写/同步操作
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._vector_store = None
        self._embedding_service = None
        self._sync_handlers: Dict[str, Callable] = {}

    @property
    def vector_store(self):
        """延迟加载向量存储"""
        if self._vector_store is None:
            from services.vector import enterprise_vector_store, document_vector_store
            self._vector_store = enterprise_vector_store
        return self._vector_store

    @property
    def embedding_service(self):
        """延迟加载embedding服务"""
        if self._embedding_service is None:
            from services.vector import embedding_service
            self._embedding_service = embedding_service
        return self._embedding_service

    def register_sync_handler(self, model_name: str, handler: Callable):
        """
        注册同步处理器

        当PG数据变更时，自动调用handler进行向量同步

        Args:
            model_name: 模型名称
            handler: 处理函数，签名: handler(instance, operation) -> bool
        """
        self._sync_handlers[model_name] = handler
        logger.info(f"Registered sync handler for model: {model_name}")

    def _generate_vector_text(self, enterprise_data: Dict) -> str:
        """
        生成向量化的文本

        Args:
            enterprise_data: 企业数据字典

        Returns:
            用于向量化的文本
        """
        parts = []

        if enterprise_data.get('name'):
            parts.append(f"企业名称: {enterprise_data['name']}")

        if enterprise_data.get('business_scope'):
            parts.append(f"经营范围: {enterprise_data['business_scope']}")

        if enterprise_data.get('qualifications'):
            quals = enterprise_data['qualifications']
            if isinstance(quals, list):
                parts.append(f"资质: {', '.join(quals)}")
            else:
                parts.append(f"资质: {quals}")

        if enterprise_data.get('past_performance'):
            perf = enterprise_data['past_performance']
            if isinstance(perf, list):
                parts.append(f"业绩: {', '.join(perf)}")
            else:
                parts.append(f"业绩: {perf}")

        if enterprise_data.get('industry'):
            parts.append(f"行业: {enterprise_data['industry']}")

        if enterprise_data.get('province') or enterprise_data.get('city'):
            location = ' '.join(filter(None, [enterprise_data.get('province'), enterprise_data.get('city')]))
            parts.append(f"地区: {location}")

        return ' | '.join(parts)

    def save_enterprise(
        self,
        enterprise_data: Dict[str, Any],
        model_class: Type = None,
        sync_vector: bool = True
    ) -> DataSyncResult:
        """
        保存企业数据（PG + 向量）

        Args:
            enterprise_data: 企业数据字典
            model_class: Django模型类（可选，默认使用Enterprise）
            sync_vector: 是否同步向量

        Returns:
            DataSyncResult: 同步结果
        """
        result = DataSyncResult(success=False)

        try:
            with transaction.atomic():
                if model_class is None:
                    from apps.enterprise.models import Enterprise
                    model_class = Enterprise

                pg_data = {k: v for k, v in enterprise_data.items()
                           if k not in ['id', 'created_at', 'updated_at']}

                if enterprise_data.get('id'):
                    instance = model_class.objects.filter(id=enterprise_data['id']).first()
                    if instance:
                        for key, value in pg_data.items():
                            setattr(instance, key, value)
                        instance.save()
                        result.pg_saved = True
                        result.pg_id = instance.id
                else:
                    instance = model_class.objects.create(**pg_data)
                    result.pg_saved = True
                    result.pg_id = instance.id

                if sync_vector:
                    vector_text = self._generate_vector_text(enterprise_data)
                    vector_metadata = {
                        'enterprise_id': str(instance.id),
                        'name': enterprise_data.get('name', ''),
                        'industry': enterprise_data.get('industry', ''),
                        'province': enterprise_data.get('province', ''),
                        'city': enterprise_data.get('city', ''),
                    }

                    vector_success = self.vector_store.add_enterprise(
                        enterprise_id=str(instance.id),
                        text=vector_text,
                        metadata=vector_metadata
                    )

                    if vector_success:
                        result.vector_saved = True
                        result.vector_id = f"enterprise_{instance.id}"
                    else:
                        logger.warning(f"向量保存失败，但PG已保存: enterprise_id={instance.id}")

                result.success = result.pg_saved
                return result

        except Exception as e:
            logger.error(f"保存企业数据失败: {str(e)}")
            result.error = str(e)
            return result

    def delete_enterprise(
        self,
        enterprise_id: int,
        model_class: Type = None,
        sync_vector: bool = True
    ) -> DataSyncResult:
        """
        删除企业数据（PG + 向量）

        Args:
            enterprise_id: 企业ID
            model_class: Django模型类
            sync_vector: 是否同步删除向量

        Returns:
            DataSyncResult: 同步结果
        """
        result = DataSyncResult(success=False)

        try:
            with transaction.atomic():
                if model_class is None:
                    from apps.enterprise.models import Enterprise
                    model_class = Enterprise

                instance = model_class.objects.filter(id=enterprise_id).first()
                if instance:
                    instance.delete()
                    result.pg_saved = True
                    result.pg_id = enterprise_id

                if sync_vector:
                    vector_success = self.vector_store.delete_enterprise(str(enterprise_id))
                    result.vector_saved = vector_success

                result.success = result.pg_saved
                return result

        except Exception as e:
            logger.error(f"删除企业数据失败: {str(e)}")
            result.error = str(e)
            return result

    def search_enterprises(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 10,
        min_similarity: float = 0.5,
        model_class: Type = None
    ) -> List[Dict[str, Any]]:
        """
        搜索企业（向量检索 + PG过滤）

        Args:
            query: 搜索查询文本
            filters: PG过滤条件
            top_k: 返回数量
            min_similarity: 最小相似度
            model_class: Django模型类

        Returns:
            匹配的企业列表
        """
        try:
            vector_results = self.vector_store.search_similar(
                query_text=query,
                n_results=top_k * 2,
                min_similarity=min_similarity
            )

            if not vector_results:
                return []

            candidate_ids = [r['id'] for r in vector_results]
            candidate_similarity = {r['id']: r['similarity'] for r in vector_results}

            if model_class is None:
                from apps.enterprise.models import Enterprise
                model_class = Enterprise

            pg_filter = {'id__in': candidate_ids}
            if filters:
                pg_filter.update(filters)

            enterprises = model_class.objects.filter(**pg_filter).only(
                'id', 'name', 'credit_code', 'industry', 'province', 'city',
                'business_scope', 'qualifications'
            )

            results = []
            for enterprise in enterprises:
                ent_dict = {
                    'id': enterprise.id,
                    'name': enterprise.name,
                    'credit_code': enterprise.credit_code,
                    'industry': enterprise.industry,
                    'province': enterprise.province,
                    'city': enterprise.city,
                    'business_scope': enterprise.business_scope,
                    'similarity': candidate_similarity.get(str(enterprise.id), 0)
                }
                results.append(ent_dict)

            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"搜索企业失败: {str(e)}")
            return []

    def batch_sync_enterprises(
        self,
        enterprise_ids: List[int] = None,
        model_class: Type = None
    ) -> Dict[str, int]:
        """
        批量同步企业向量

        Args:
            enterprise_ids: 企业ID列表（None表示同步所有）
            model_class: Django模型类

        Returns:
            同步统计 {"success": x, "failed": y}
        """
        stats = {'success': 0, 'failed': 0}

        try:
            if model_class is None:
                from apps.enterprise.models import Enterprise
                model_class = Enterprise

            queryset = model_class.objects.all()
            if enterprise_ids:
                queryset = queryset.filter(id__in=enterprise_ids)

            enterprises = []
            for ent in queryset:
                ent_data = {
                    'id': ent.id,
                    'name': ent.name,
                    'industry': ent.industry,
                    'province': ent.province,
                    'city': ent.city,
                    'business_scope': ent.business_scope,
                    'qualifications': ent.qualifications,
                    'past_performance': ent.past_performance
                }
                enterprises.append({
                    'id': str(ent.id),
                    'text': self._generate_vector_text(ent_data),
                    'metadata': {
                        'enterprise_id': str(ent.id),
                        'name': ent.name,
                        'industry': ent.industry or ''
                    }
                })

            if enterprises:
                count = self.vector_store.batch_add_enterprises(enterprises)
                stats['success'] = count
                stats['failed'] = len(enterprises) - count

            logger.info(f"批量同步企业向量完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"批量同步企业向量失败: {str(e)}")
            stats['failed'] = -1
            return stats

    def save_document(
        self,
        document_data: Dict[str, Any],
        model_class: Type = None,
        sync_vector: bool = True
    ) -> DataSyncResult:
        """
        保存文档数据（PG + 向量）

        Args:
            document_data: 文档数据字典
            model_class: Django模型类
            sync_vector: 是否同步向量

        Returns:
            DataSyncResult: 同步结果
        """
        result = DataSyncResult(success=False)

        try:
            with transaction.atomic():
                if model_class is None:
                    from apps.documents.models import Document
                    model_class = Document

                pg_data = {k: v for k, v in document_data.items()
                           if k not in ['id', 'created_at', 'updated_at']}

                if document_data.get('id'):
                    instance = model_class.objects.filter(id=document_data['id']).first()
                    if instance:
                        for key, value in pg_data.items():
                            setattr(instance, key, value)
                        instance.save()
                        result.pg_saved = True
                        result.pg_id = instance.id
                else:
                    instance = model_class.objects.create(**pg_data)
                    result.pg_saved = True
                    result.pg_id = instance.id

                if sync_vector and instance.content:
                    from services.vector import document_vector_store
                    vector_success = document_vector_store.add_document(
                        doc_id=str(instance.id),
                        text=instance.content,
                        metadata={
                            'title': instance.title,
                            'doc_type': instance.doc_type
                        }
                    )
                    result.vector_saved = vector_success

                result.success = result.pg_saved
                return result

        except Exception as e:
            logger.error(f"保存文档数据失败: {str(e)}")
            result.error = str(e)
            return result

    def search_documents(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 10,
        min_similarity: float = 0.5,
        model_class: Type = None
    ) -> List[Dict[str, Any]]:
        """
        搜索文档（向量检索 + PG过滤）

        Args:
            query: 搜索查询文本
            filters: PG过滤条件
            top_k: 返回数量
            min_similarity: 最小相似度
            model_class: Django模型类

        Returns:
            匹配的文档列表
        """
        try:
            from services.vector import document_vector_store

            vector_results = document_vector_store.search_similar(
                query_text=query,
                n_results=top_k * 2,
                min_similarity=min_similarity
            )

            if not vector_results:
                return []

            candidate_ids = [r['id'] for r in vector_results]
            candidate_similarity = {r['id']: r['similarity'] for r in vector_results}

            if model_class is None:
                from apps.documents.models import Document
                model_class = Document

            pg_filter = {'id__in': candidate_ids}
            if filters:
                pg_filter.update(filters)

            documents = model_class.objects.filter(**pg_filter).only(
                'id', 'title', 'doc_type', 'created_at'
            )

            results = []
            for doc in documents:
                doc_dict = {
                    'id': doc.id,
                    'title': doc.title,
                    'doc_type': doc.doc_type,
                    'created_at': doc.created_at.isoformat() if doc.created_at else None,
                    'similarity': candidate_similarity.get(str(doc.id), 0)
                }
                results.append(doc_dict)

            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return []


unified_data_service = UnifiedDataService()
