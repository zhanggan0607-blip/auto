"""
向量事务管理器
解决PostgreSQL与向量库(Chroma)之间的数据一致性问题

使用Django事务与向量库操作联动，确保PG数据与向量数据同步
"""
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from django.db import transaction

from .chroma_client import chroma_client

logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """
    事务状态
    """
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class VectorOperation:
    """
    向量操作记录
    """
    operation_type: str  # 'upsert', 'delete'
    collection_name: str
    doc_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class VectorTransaction:
    """
    向量事务管理器

    用于在Django ORM事务中批量执行向量库操作，
    确保PostgreSQL数据与向量库数据的一致性

    使用方式:
    ```python
    with VectorTransaction() as vt:
        # 1. 先保存PG数据
        enterprise = Enterprise.objects.create(name='xxx', ...)

        # 2. 添加向量操作
        vt.add_vector('enterprise_vectors', str(enterprise.id), vector_text, metadata)

        # 3. 提交时会同时执行向量操作
        # 如果向量操作失败，整个事务会回滚
    ```
    """

    def __init__(self):
        self._operations: List[VectorOperation] = []
        self._status = TransactionStatus.PENDING
        self._chroma_available = chroma_client.is_available

    def add_vector(
        self,
        collection_name: str,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ):
        """
        添加向量操作到事务队列

        Args:
            collection_name: 集合名称
            doc_id: 文档ID
            text: 向量化文本
            metadata: 元数据
        """
        if not self._chroma_available:
            logger.warning(f"向量库不可用，跳过添加向量: {doc_id}")
            return

        op = VectorOperation(
            operation_type='upsert',
            collection_name=collection_name,
            doc_id=doc_id,
            data={'text': text, 'metadata': metadata or {}}
        )
        self._operations.append(op)

    def delete_vector(self, collection_name: str, doc_id: str):
        """
        添加删除向量操作到事务队列

        Args:
            collection_name: 集合名称
            doc_id: 文档ID
        """
        if not self._chroma_available:
            logger.warning(f"向量库不可用，跳过删除向量: {doc_id}")
            return

        op = VectorOperation(
            operation_type='delete',
            collection_name=collection_name,
            doc_id=doc_id
        )
        self._operations.append(op)

    def batch_add_vectors(self, collection_name: str, vectors: List[Dict[str, Any]]):
        """
        批量添加向量操作

        Args:
            collection_name: 集合名称
            vectors: 向量列表，每项包含 id, text, metadata
        """
        if not self._chroma_available:
            logger.warning(f"向量库不可用，跳过批量添加向量")
            return

        for v in vectors:
            self.add_vector(
                collection_name=collection_name,
                doc_id=v['id'],
                text=v['text'],
                metadata=v.get('metadata')
            )

    def commit(self):
        """
        提交事务，执行所有向量操作
        """
        if not self._operations:
            self._status = TransactionStatus.COMMITTED
            return

        try:
            for op in self._operations:
                self._execute_operation(op)
            self._status = TransactionStatus.COMMITTED
            logger.info(f"向量事务提交成功: {len(self._operations)} 个操作")
        except Exception as e:
            self._status = TransactionStatus.FAILED
            logger.error(f"向量事务提交失败: {str(e)}")
            raise

    def rollback(self):
        """
        回滚事务，清空操作队列
        """
        self._operations.clear()
        self._status = TransactionStatus.ROLLED_BACK
        logger.info("向量事务已回滚")

    def _execute_operation(self, op: VectorOperation):
        """
        执行单个向量操作
        """
        collection = chroma_client.get_collection(
            op.collection_name,
            description=f"Transaction collection: {op.collection_name}"
        )

        if op.operation_type == 'upsert':
            collection.upsert(
                ids=[op.doc_id],
                documents=[op.data.get('text', '')],
                metadatas=[op.data.get('metadata', {})]
            )
            logger.debug(f"向量upsert成功: {op.doc_id}")

        elif op.operation_type == 'delete':
            collection.delete(ids=[op.doc_id])
            logger.debug(f"向量delete成功: {op.doc_id}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
            return False

        if self._status == TransactionStatus.PENDING:
            self.commit()

        return True


@contextmanager
def vector_transaction():
    """
    向量事务上下文管理器

    使用示例:
    ```python
    from services.vector import vector_transaction, enterprise_vector_store

    def create_enterprise_with_vector(data):
        with vector_transaction() as vt:
            # 1. 创建PG数据
            enterprise = Enterprise.objects.create(**data)

            # 2. 构建向量文本
            vector_text = f"{enterprise.name} {enterprise.business_scope}"

            # 3. 添加向量操作
            vt.add_vector(
                collection_name='enterprise_vectors',
                doc_id=str(enterprise.id),
                text=vector_text,
                metadata={'name': enterprise.name}
            )

            return enterprise
    ```
    """
    tx = VectorTransaction()
    try:
        yield tx
        if tx._status == TransactionStatus.PENDING:
            tx.commit()
    except Exception as e:
        tx.rollback()
        raise


class AtomicVectorOperation:
    """
    原子性向量操作类

    用于需要同时操作PostgreSQL和向量库的场景
    提供简单的API来确保数据一致性

    使用示例:
    ```python
    atomic = AtomicVectorOperation()

    # 添加企业（PG + 向量）
    atomic.create_enterprise({
        'name': '测试企业',
        'business_scope': '软件开发',
        'industry': 'IT'
    })

    # 添加文档（PG + 向量）
    atomic.create_document({
        'title': '投标书',
        'content': '....',
        'enterprise_id': 1
    })

    # 批量执行
    atomic.execute_all()
    ```
    """

    def __init__(self):
        self._enterprise_ops: List[Dict] = []
        self._document_ops: List[Dict] = []
        self._other_ops: List[Dict] = []
        self._executed = False

    def create_enterprise(self, data: Dict[str, Any]):
        """
        添加创建企业操作

        Args:
            data: 企业数据，包含 name, business_scope, industry 等
        """
        self._enterprise_ops.append({
            'operation': 'create',
            'data': data
        })

    def update_enterprise(self, enterprise_id: int, data: Dict[str, Any]):
        """
        添加更新企业操作

        Args:
            enterprise_id: 企业ID
            data: 更新数据
        """
        self._enterprise_ops.append({
            'operation': 'update',
            'enterprise_id': enterprise_id,
            'data': data
        })

    def delete_enterprise(self, enterprise_id: int):
        """
        添加删除企业操作

        Args:
            enterprise_id: 企业ID
        """
        self._enterprise_ops.append({
            'operation': 'delete',
            'enterprise_id': enterprise_id
        })

    def create_document(self, data: Dict[str, Any]):
        """
        添加创建文档操作

        Args:
            data: 文档数据，包含 title, content, enterprise_id 等
        """
        self._document_ops.append({
            'operation': 'create',
            'data': data
        })

    def delete_document(self, doc_id: int):
        """
        添加删除文档操作

        Args:
            doc_id: 文档ID
        """
        self._document_ops.append({
            'operation': 'delete',
            'doc_id': doc_id
        })

    def add_custom_operation(
        self,
        collection_name: str,
        doc_id: str,
        operation_type: str,
        data: Dict[str, Any] = None
    ):
        """
        添加自定义操作

        Args:
            collection_name: 集合名称
            doc_id: 文档ID
            operation_type: 操作类型 'upsert' 或 'delete'
            data: 操作数据
        """
        self._other_ops.append({
            'collection_name': collection_name,
            'doc_id': doc_id,
            'operation_type': operation_type,
            'data': data or {}
        })

    def execute_all(self) -> Dict[str, Any]:
        """
        执行所有操作

        Returns:
            dict: 执行结果统计
        """
        if self._executed:
            raise RuntimeError("操作已执行，不能重复执行")

        self._executed = True
        results = {
            'enterprise': {'success': 0, 'failed': 0},
            'document': {'success': 0, 'failed': 0},
            'other': {'success': 0, 'failed': 0}
        }

        with transaction.atomic():
            try:
                for op in self._enterprise_ops:
                    self._execute_enterprise_op(op, results['enterprise'])

                for op in self._document_ops:
                    self._execute_document_op(op, results['document'])

                for op in self._other_ops:
                    self._execute_other_op(op, results['other'])

                return results

            except Exception as e:
                logger.error(f"原子操作执行失败: {str(e)}")
                raise

    def _execute_enterprise_op(self, op: Dict, result_stats: Dict):
        """
        执行企业操作
        """
        from apps.enterprise.models import Enterprise

        try:
            if op['operation'] == 'create':
                enterprise = Enterprise.objects.create(**op['data'])
                vector_text = f"{enterprise.name} {enterprise.business_scope or ''}"
                enterprise_vector_store.add_enterprise(
                    str(enterprise.id),
                    vector_text,
                    {'name': enterprise.name, 'industry': getattr(enterprise, 'industry', '')}
                )
                result_stats['success'] += 1

            elif op['operation'] == 'update':
                Enterprise.objects.filter(id=op['enterprise_id']).update(**op['data'])
                result_stats['success'] += 1

            elif op['operation'] == 'delete':
                Enterprise.objects.filter(id=op['enterprise_id']).delete()
                enterprise_vector_store.delete_enterprise(str(op['enterprise_id']))
                result_stats['success'] += 1

        except Exception as e:
            result_stats['failed'] += 1
            logger.error(f"企业操作失败: {str(e)}")
            raise

    def _execute_document_op(self, op: Dict, result_stats: Dict):
        """
        执行文档操作
        """
        from apps.documents.models import Document

        try:
            if op['operation'] == 'create':
                doc = Document.objects.create(**op['data'])
                vector_text = f"{doc.title} {doc.content or ''}"
                document_vector_store.add_document(
                    doc.id,
                    doc.title,
                    doc.content or '',
                    {'doc_type': getattr(doc, 'document_type', 'other')}
                )
                result_stats['success'] += 1

            elif op['operation'] == 'delete':
                Document.objects.filter(id=op['doc_id']).delete()
                document_vector_store.delete_document(op['doc_id'])
                result_stats['success'] += 1

        except Exception as e:
            result_stats['failed'] += 1
            logger.error(f"文档操作失败: {str(e)}")
            raise

    def _execute_other_op(self, op: Dict, result_stats: Dict):
        """
        执行自定义操作
        """
        try:
            if op['operation_type'] == 'upsert':
                collection = chroma_client.get_collection(op['collection_name'])
                collection.upsert(
                    ids=[op['doc_id']],
                    documents=[op['data'].get('text', '')],
                    metadatas=[op['data'].get('metadata', {})]
                )
            elif op['operation_type'] == 'delete':
                collection = chroma_client.get_collection(op['collection_name'])
                collection.delete(ids=[op['doc_id']])

            result_stats['success'] += 1

        except Exception as e:
            result_stats['failed'] += 1
            logger.error(f"自定义操作失败: {str(e)}")
            raise
