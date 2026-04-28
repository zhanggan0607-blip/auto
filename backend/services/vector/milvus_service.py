"""
Milvus向量数据库服务
企业向量检索模块

升级说明：
- 从Chroma升级到Milvus
- Milvus支持分布式向量检索，性能更强
- 支持更大的向量规模
"""
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """向量检索结果"""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]


class MilvusService:
    """
    Milvus向量数据库服务
    提供企业向量检索功能
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = None
        self._connected = False
        self._collection = None
        self._embedding_service = None
        self._initialized = True

    def _initialize(self):
        """初始化Milvus连接"""
        try:
            from pymilvus import connections, Collection

            host = os.getenv('MILVUS_HOST', 'localhost')
            port = int(os.getenv('MILVUS_PORT', '19530'))

            connections.connect(
                alias="default",
                host=host,
                port=port,
            )

            self._connected = True
            logger.info(f"Milvus连接成功: {host}:{port}")

            self._initialized = True

        except ImportError:
            logger.warning("pymilvus未安装，Milvus服务不可用")
            self._connected = False
        except Exception as e:
            logger.error(f"Milvus初始化失败: {e}")
            self._connected = False

    def _get_embedding_service(self):
        """获取embedding服务"""
        if self._embedding_service is None:
            from services.vector.embedding import embedding_service
            self._embedding_service = embedding_service
        return self._embedding_service

    def _get_or_create_collection(self, collection_name: str, dimension: int = 1536):
        """获取或创建集合"""
        try:
            from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, utility

            if not utility.has_collection(collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.JSON),
                ]

                schema = CollectionSchema(
                    fields=fields,
                    description=f"{collection_name} collection"
                )

                collection = Collection(name=collection_name, schema=schema)

                index_params = {
                    "metric_type": "IP",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128},
                }
                collection.create_index(field_name="vector", index_params=index_params)

                logger.info(f"Milvus集合已创建: {collection_name}, dimension={dimension}")
            else:
                collection = Collection(collection_name)

            collection.load()
            return collection

        except Exception as e:
            logger.error(f"获取/创建集合失败: {e}")
            raise

    def search_enterprise(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """
        搜索企业向量

        Args:
            query_text: 查询文本
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            匹配的企业列表
        """
        if not self._connected:
            logger.warning("Milvus未连接，尝试重新连接...")
            self._initialize()
            if not self._connected:
                return []

        try:
            embedding_service = self._get_embedding_service()
            query_vector = embedding_service.embed(query_text)

            if not query_vector:
                logger.error("生成embedding失败")
                return []

            collection_name = settings.CHROMA_CONFIG.get('COLLECTION_NAME', 'enterprise_embeddings')
            collection = self._get_or_create_collection(collection_name, dimension=len(query_vector))

            search_params = {"metric_type": "IP", "params": {"nprobe": 10}}

            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["text", "metadata"],
            )

            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append(VectorSearchResult(
                        id=str(hit.id),
                        score=hit.score,
                        text=hit.entity.get("text", ""),
                        metadata=hit.entity.get("metadata", {}),
                    ))

            logger.info(f"Milvus检索完成: query='{query_text[:50]}...', 结果数={len(search_results)}")
            return search_results

        except Exception as e:
            logger.error(f"Milvus企业检索失败: {e}")
            return []

    def add_enterprise_vector(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        添加企业向量

        Args:
            texts: 文本列表
            embeddings: 向量列表
            metadatas: 元数据列表

        Returns:
            插入的ID列表
        """
        if not self._connected:
            self._initialize()
            if not self._connected:
                raise ConnectionError("Milvus not connected")

        try:
            collection_name = settings.CHROMA_CONFIG.get('COLLECTION_NAME', 'enterprise_embeddings')
            dimension = len(embeddings[0]) if embeddings else 1536
            collection = self._get_or_create_collection(collection_name, dimension)

            entities = [
                embeddings,
                texts,
                [m if m else {} for m in (metadatas or [{}] * len(texts))],
            ]

            result = collection.insert(entities)

            ids = [str(id) for id in result.primary_keys]
            logger.info(f"Milvus插入成功: {len(ids)} 条向量")
            return ids

        except Exception as e:
            logger.error(f"Milvus插入失败: {e}")
            raise

    def delete_enterprise_vectors(self, ids: List[str]) -> bool:
        """
        删除企业向量

        Args:
            ids: 向量ID列表

        Returns:
            是否成功
        """
        if not self._connected:
            return False

        try:
            collection_name = settings.CHROMA_CONFIG.get('COLLECTION_NAME', 'enterprise_embeddings')
            collection = self._get_or_create_collection(collection_name)

            safe_ids = []
            for id_val in ids:
                try:
                    safe_ids.append(str(int(id_val)))
                except (ValueError, TypeError):
                    logger.warning(f"跳过无效的向量ID: {id_val}")
                    continue

            if not safe_ids:
                logger.warning("没有有效的向量ID可删除")
                return False

            expr = f"id in [{','.join(safe_ids)}]"
            collection.delete(expr)
            collection.flush()

            logger.info(f"Milvus删除成功: {len(safe_ids)} 条向量")
            return True

        except Exception as e:
            logger.error(f"Milvus删除失败: {e}")
            return False

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        if not self._connected:
            return {"status": "disconnected"}

        try:
            from pymilvus import Collection, utility

            if not utility.has_collection(collection_name):
                return {"status": "not_found", "entities": 0}

            collection = Collection(collection_name)
            collection.load()

            stats = collection.num_entities

            return {
                "status": "connected",
                "entities": stats,
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {"status": "error", "error": str(e)}

    def health_check(self) -> bool:
        """健康检查"""
        if not self._connected:
            self._initialize()
        return self._connected


class ChromaToMilvusMigrator:
    """
    Chroma到Milvus的数据迁移工具
    用于将现有的Chroma数据迁移到Milvus
    """

    def __init__(self):
        self._milvus_service = MilvusService()
        self._chroma_client = None

    def _get_chroma_client(self):
        """获取Chroma客户端"""
        if self._chroma_client is None:
            try:
                import chromadb
                from django.conf import settings as django_settings

                persist_dir = str(django_settings.CHROMA_CONFIG.get('PERSIST_DIRECTORY', './chroma_db'))
                self._chroma_client = chromadb.PersistentClient(path=persist_dir)

            except ImportError:
                logger.warning("Chroma未安装，无法迁移")
                return None
            except Exception as e:
                logger.error(f"Chroma连接失败: {e}")
                return None

        return self._chroma_client

    def migrate_collection(
        self,
        collection_name: str,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        迁移集合

        Args:
            collection_name: 集合名称
            batch_size: 批大小

        Returns:
            迁移结果
        """
        chroma_client = self._get_chroma_client()
        if not chroma_client:
            return {"status": "error", "message": "Chroma client unavailable"}

        try:
            collection = chroma_client.get_collection(collection_name)
            total = collection.count()

            logger.info(f"开始迁移集合: {collection_name}, 总数={total}")

            migrated = 0
            for offset in range(0, total, batch_size):
                batch = collection.get(
                    limit=batch_size,
                    offset=offset,
                )

                texts = batch.get("documents", [])
                embeddings = batch.get("embeddings", [])
                metadatas = batch.get("metadatas", [])

                if texts and embeddings:
                    ids = self._milvus_service.add_enterprise_vector(
                        texts=texts,
                        embeddings=embeddings,
                        metadatas=metadatas,
                    )
                    migrated += len(ids)
                    logger.info(f"迁移进度: {migrated}/{total}")

            return {
                "status": "success",
                "collection": collection_name,
                "migrated_count": migrated,
                "total_count": total,
            }

        except Exception as e:
            logger.error(f"迁移失败: {e}")
            return {"status": "error", "message": str(e)}


milvus_service = MilvusService()
milvus_migrator = ChromaToMilvusMigrator()
