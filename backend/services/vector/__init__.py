"""
向量服务模块
整合企业向量存储和文档向量存储

支持Chroma和Milvus两种向量数据库:
- Chroma: 轻量级，适合中小规模
- Milvus: 分布式，适合大规模向量检索
"""
from .chroma_client import chroma_client, ChromaClient
from .embedding import embedding_service, EmbeddingService
from .base_store import BaseVectorStore
from .enterprise_store import EnterpriseVectorStore, enterprise_vector_store
from .document_store import DocumentVectorStore, document_vector_store
from .milvus_service import milvus_service, milvus_migrator, MilvusService
from .transaction import (
    VectorTransaction,
    VectorOperation,
    TransactionStatus,
    vector_transaction,
    AtomicVectorOperation
)

__all__ = [
    'chroma_client',
    'ChromaClient',
    'embedding_service',
    'EmbeddingService',
    'BaseVectorStore',
    'EnterpriseVectorStore',
    'enterprise_vector_store',
    'DocumentVectorStore',
    'document_vector_store',
    'milvus_service',
    'milvus_migrator',
    'MilvusService',
    'VectorTransaction',
    'VectorOperation',
    'TransactionStatus',
    'vector_transaction',
    'AtomicVectorOperation',
]
