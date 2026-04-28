"""
向量库同步管理器
实现 PostgreSQL 与向量库之间的自动同步

通过 Django signals 实现：
- Enterprise 创建/更新/删除 -> 同步 enterprise_vectors
- Document 创建/更新/删除 -> 同步 document_vectors

使用方式：
1. 在 App 的 ready() 方法中调用 register_vector_signals()
2. 或者在 settings.py 中导入此模块

配置项（settings.py）：
    VECTOR_SYNC_ENABLED = True  # 是否启用同步
    VECTOR_SYNC_ASYNC = True    # 是否异步执行
"""
import logging
import threading
from typing import Any, Dict, Optional

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class VectorSyncManager:
    """
    向量同步管理器

    负责管理 Django 模型与向量库之间的数据同步
    """

    _instance = None
    _enabled = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sync_handlers = {}
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """设置默认同步处理器"""
        from services.vector.enterprise_store import enterprise_vector_store
        from services.vector.document_store import document_vector_store

        self._sync_handlers['enterprise'] = {
            'create': self._create_enterprise_vector,
            'update': self._update_enterprise_vector,
            'delete': self._delete_enterprise_vector,
            'store': enterprise_vector_store
        }

        self._sync_handlers['document'] = {
            'create': self._create_document_vector,
            'update': self._update_document_vector,
            'delete': self._delete_document_vector,
            'store': document_vector_store
        }

    def _create_enterprise_vector(self, instance, **kwargs):
        """创建企业向量"""
        try:
            from services.vector.enterprise_store import enterprise_vector_store

            vector_text = self._build_enterprise_vector_text(instance)
            metadata = {
                'name': instance.name,
                'enterprise_type': getattr(instance, 'enterprise_type', ''),
                'province': getattr(instance, 'province', ''),
                'city': getattr(instance, 'city', '')
            }

            enterprise_vector_store.add_enterprise(
                str(instance.id),
                vector_text,
                metadata
            )
            logger.info(f"企业向量创建成功: {instance.id}")

        except Exception as e:
            logger.error(f"企业向量创建失败: {e}")

    def _update_enterprise_vector(self, instance, **kwargs):
        """更新企业向量"""
        try:
            from services.vector.enterprise_store import enterprise_vector_store

            vector_text = self._build_enterprise_vector_text(instance)
            metadata = {
                'name': instance.name,
                'enterprise_type': getattr(instance, 'enterprise_type', ''),
                'province': getattr(instance, 'province', ''),
                'city': getattr(instance, 'city', '')
            }

            enterprise_vector_store.add_enterprise(
                str(instance.id),
                vector_text,
                metadata
            )
            logger.info(f"企业向量更新成功: {instance.id}")

        except Exception as e:
            logger.error(f"企业向量更新失败: {e}")

    def _delete_enterprise_vector(self, instance, **kwargs):
        """删除企业向量"""
        try:
            from services.vector.enterprise_store import enterprise_vector_store

            enterprise_vector_store.delete_enterprise(str(instance.id))
            logger.info(f"企业向量删除成功: {instance.id}")

        except Exception as e:
            logger.error(f"企业向量删除失败: {e}")

    def _build_enterprise_vector_text(self, enterprise) -> str:
        """构建企业向量文本"""
        parts = []

        if enterprise.name:
            parts.append(enterprise.name)

        if getattr(enterprise, 'enterprise_type', None):
            parts.append(enterprise.enterprise_type)

        if getattr(enterprise, 'business_scope', None):
            parts.append(enterprise.business_scope)

        if getattr(enterprise, 'province', None):
            parts.append(enterprise.province)

        if getattr(enterprise, 'city', None):
            parts.append(enterprise.city)

        try:
            qualifications = enterprise.qualifications.all()
            if qualifications:
                qual_names = [q.qualification_name for q in qualifications[:10]]
                parts.append(' '.join(qual_names))
        except Exception:
            pass

        try:
            performances = enterprise.performances.all()
            if performances:
                perf_names = [p.project_name for p in performances[:5]]
                parts.append(' '.join(perf_names))
        except Exception:
            pass

        return ' '.join(filter(None, parts))

    def _create_document_vector(self, instance, **kwargs):
        """创建文档向量"""
        try:
            from services.vector.document_store import document_vector_store

            vector_text = self._build_document_vector_text(instance)
            metadata = {
                'title': getattr(instance, 'document_name', '') or getattr(instance, 'title', ''),
                'document_type': getattr(instance, 'document_type', ''),
            }

            document_vector_store.add_document(
                str(instance.id),
                getattr(instance, 'document_name', '') or getattr(instance, 'title', ''),
                vector_text,
                metadata
            )
            logger.info(f"文档向量创建成功: {instance.id}")

        except Exception as e:
            logger.error(f"文档向量创建失败: {e}")

    def _update_document_vector(self, instance, **kwargs):
        """更新文档向量"""
        try:
            from services.vector.document_store import document_vector_store

            vector_text = self._build_document_vector_text(instance)
            metadata = {
                'title': getattr(instance, 'document_name', '') or getattr(instance, 'title', ''),
                'document_type': getattr(instance, 'document_type', ''),
            }

            document_vector_store.add_document(
                str(instance.id),
                getattr(instance, 'document_name', '') or getattr(instance, 'title', ''),
                vector_text,
                metadata
            )
            logger.info(f"文档向量更新成功: {instance.id}")

        except Exception as e:
            logger.error(f"文档向量更新失败: {e}")

    def _delete_document_vector(self, instance, **kwargs):
        """删除文档向量"""
        try:
            from services.vector.document_store import document_vector_store

            document_vector_store.delete_document(str(instance.id))
            logger.info(f"文档向量删除成功: {instance.id}")

        except Exception as e:
            logger.error(f"文档向量删除失败: {e}")

    def _build_document_vector_text(self, document) -> str:
        """构建文档向量文本"""
        parts = []

        title = getattr(document, 'document_name', None) or getattr(document, 'title', None)
        if title:
            parts.append(title)

        content = getattr(document, 'content', None) or getattr(document, 'extracted_content', None)
        if content:
            parts.append(content[:5000])

        doc_type = getattr(document, 'document_type', None)
        if doc_type:
            parts.append(doc_type)

        return ' '.join(filter(None, parts))

    def enable(self):
        """启用同步"""
        self._enabled = True
        logger.info("向量同步已启用")

    def disable(self):
        """禁用同步"""
        self._enabled = False
        logger.info("向量同步已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled


vector_sync_manager = VectorSyncManager()


def register_vector_signals():
    """
    注册向量同步信号处理器

    在 App 的 ready() 方法中调用：
        from common.utils.vector_sync_manager import register_vector_signals

        class MyApp(App):
            def ready(self):
                register_vector_signals()
    """
    from apps.enterprise.models import Enterprise
    from apps.documents.models import GeneratedDocument

    def _run_in_thread(handler, instance, **kwargs):
        if not vector_sync_manager.is_enabled():
            return
        try:
            t = threading.Thread(target=handler, args=(instance,), kwargs=kwargs, daemon=True)
            t.start()
        except Exception as e:
            logger.error(f"启动向量同步线程失败: {e}")
            try:
                handler(instance, **kwargs)
            except Exception as e2:
                logger.error(f"向量同步回退执行失败: {e2}")

    @receiver(post_save, sender=Enterprise)
    def on_enterprise_save(sender, instance, created, **kwargs):
        action = 'create' if created else 'update'
        handler = vector_sync_manager._sync_handlers.get('enterprise', {}).get(action)
        if handler:
            _run_in_thread(handler, instance, **kwargs)

    @receiver(post_delete, sender=Enterprise)
    def on_enterprise_delete(sender, instance, **kwargs):
        handler = vector_sync_manager._sync_handlers.get('enterprise', {}).get('delete')
        if handler:
            _run_in_thread(handler, instance, **kwargs)

    @receiver(post_save, sender=GeneratedDocument)
    def on_document_save(sender, instance, created, **kwargs):
        action = 'create' if created else 'update'
        handler = vector_sync_manager._sync_handlers.get('document', {}).get(action)
        if handler:
            _run_in_thread(handler, instance, **kwargs)

    @receiver(post_delete, sender=GeneratedDocument)
    def on_document_delete(sender, instance, **kwargs):
        handler = vector_sync_manager._sync_handlers.get('document', {}).get('delete')
        if handler:
            _run_in_thread(handler, instance, **kwargs)

    logger.info("向量同步信号已注册")
