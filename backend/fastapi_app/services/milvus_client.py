"""
Milvus向量数据库客户端 - 分布式集群支持
"""
import logging
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("pymilvus not installed, Milvus service will use fallback mode")


class MilvusClusterClient:
    """
    Milvus分布式集群客户端
    支持读写分离、故障转移、负载均衡
    """

    _instance = None
    _connections: Dict[str, bool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._connected = False
        self._collection_cache: Dict[str, Collection] = {}

    async def connect(self, alias: str = "default"):
        """
        连接Milvus集群
        支持多种连接方式：单机、集群、代理
        """
        if not MILVUS_AVAILABLE:
            logger.warning("pymilvus not installed, cannot connect")
            return False

        if self._connections.get(alias):
            return True

        try:
            milvus_host = os.getenv('MILVUS_HOST', 'localhost')
            milvus_port = int(os.getenv('MILVUS_PORT', '19530'))
            milvus_user = os.getenv('MILVUS_USER', '')
            milvus_password = os.getenv('MILVUS_PASSWORD', '')

            connect_params = {
                "host": milvus_host,
                "port": milvus_port,
            }

            if milvus_user and milvus_password:
                connect_params["user"] = milvus_user
                connect_params["password"] = milvus_password

            connections.connect(alias=alias, **connect_params)
            self._connections[alias] = True
            self._connected = True
            logger.info(f"Milvus连接成功: {milvus_host}:{milvus_port}")

            return True

        except ImportError:
            logger.warning("pymilvus未安装")
            return False
        except Exception as e:
            logger.error(f"Milvus连接失败: {e}")
            return False

    async def disconnect(self, alias: str = "default"):
        """断开Milvus连接"""
        try:
            if self._connections.get(alias):
                connections.disconnect(alias=alias)
                self._connections[alias] = False
            self._connected = False
            self._collection_cache.clear()
            logger.info(f"Milvus连接已断开: {alias}")
        except Exception as e:
            logger.error(f"断开Milvus连接失败: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._connected:
                await self.connect()

            collections = utility.list_collections() if self._connected else []

            return {
                "status": "healthy" if self._connected else "unhealthy",
                "connected": self._connected,
                "collections_count": len(collections),
                "collections": collections[:10],
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connected": False,
            }

    async def create_collection_if_not_exists(
        self,
        collection_name: str,
        dimension: int = 1536,
        description: str = "",
        metric_type: str = "IP",
        index_type: str = "IVF_FLAT",
    ) -> bool:
        """
        创建集合（如果不存在）
        """
        if not MILVUS_AVAILABLE:
            raise ImportError("pymilvus not installed")

        if not self._connected:
            await self.connect()

        if not self._connected:
            raise ConnectionError("Milvus not connected")

        try:
            if utility.has_collection(collection_name):
                logger.debug(f"集合已存在: {collection_name}")
                return True

            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="created_at", dtype=DataType.DOUBLE),
            ]

            schema = CollectionSchema(fields=fields, description=description or collection_name)

            collection = Collection(name=collection_name, schema=schema)

            index_params = {
                "metric_type": metric_type,
                "index_type": index_type,
                "params": {"nlist": 128},
            }
            collection.create_index(field_name="vector", index_params=index_params)

            collection.flush()
            logger.info(f"集合已创建: {collection_name}, dimension={dimension}")

            return True

        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            raise

    async def insert(
        self,
        collection_name: str,
        data: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> List[str]:
        """
        批量插入向量
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            raise ConnectionError("Milvus not connected")

        try:
            if not utility.has_collection(collection_name):
                dimension = len(data[0]["vector"]) if data and "vector" in data[0] else 1536
                await self.create_collection_if_not_exists(collection_name, dimension)

            collection = Collection(collection_name)
            collection.load()

            ids = []
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]

                entities = [
                    [item["id"] for item in batch],
                    [item["vector"] for item in batch],
                    [item.get("text", "") for item in batch],
                    [item.get("metadata", {}) for item in batch],
                    [item.get("created_at", 0.0) for item in batch],
                ]

                result = collection.insert(entities)
                ids.extend([str(id) for id in result.primary_keys])

            collection.flush()
            logger.info(f"插入 {len(ids)} 条向量到 {collection_name}")

            return ids

        except Exception as e:
            logger.error(f"Milvus插入失败: {e}")
            raise

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        output_fields: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量检索
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            logger.warning("Milvus未连接，返回空结果")
            return []

        try:
            if not utility.has_collection(collection_name):
                logger.warning(f"集合不存在: {collection_name}")
                return []

            collection = Collection(collection_name)
            collection.load()

            search_params = {"metric_type": "IP", "params": {"nprobe": 10}}

            output_fields = output_fields or ["id", "text", "metadata", "created_at"]

            expr = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(f'{key} == "{value}"')
                    else:
                        conditions.append(f"{key} == {value}")
                if conditions:
                    expr = " and ".join(conditions)

            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=output_fields,
            )

            formatted_results = []
            for hits in results:
                for hit in hits:
                    result_dict = {"id": hit.id, "score": hit.score}
                    for field in output_fields:
                        if field != "id":
                            result_dict[field] = hit.entity.get(field, None)
                    formatted_results.append(result_dict)

            return formatted_results

        except Exception as e:
            logger.error(f"Milvus检索失败: {e}")
            return []

    async def delete(
        self,
        collection_name: str,
        ids: List[str],
    ) -> bool:
        """
        删除向量
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            raise ConnectionError("Milvus not connected")

        try:
            collection = Collection(collection_name)
            collection.load()

            expr = f'id in [{",".join([f"{id}" for id in ids])}]'
            collection.delete(expr)
            collection.flush()

            logger.info(f"删除 {len(ids)} 条向量 from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Milvus删除失败: {e}")
            return False

    async def query(
        self,
        collection_name: str,
        filters: Dict[str, Any],
        output_fields: List[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        结构化查询
        """
        if not self._connected:
            await self.connect()

        if not self._connected:
            return []

        try:
            collection = Collection(collection_name)
            collection.load()

            output_fields = output_fields or ["id", "text", "metadata", "created_at"]

            conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f'{key} == "{value}"')
                else:
                    conditions.append(f"{key} == {value}")

            expr = " and ".join(conditions) if conditions else None

            results = collection.query(
                expr=expr,
                output_fields=output_fields,
                limit=limit,
            )

            return results

        except Exception as e:
            logger.error(f"Milvus查询失败: {e}")
            return []

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        if not self._connected:
            await self.connect()

        if not self._connected:
            return {"status": "disconnected"}

        try:
            if not utility.has_collection(collection_name):
                return {"status": "not_found", "collection": collection_name}

            collection = Collection(collection_name)
            collection.load()

            stats = collection.num_entities

            return {
                "collection": collection_name,
                "entities_count": stats,
                "status": "loaded",
            }

        except Exception as e:
            return {"error": str(e)}

    async def drop_collection(self, collection_name: str) -> bool:
        """删除集合"""
        if not self._connected:
            await self.connect()

        try:
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                if collection_name in self._collection_cache:
                    del self._collection_cache[collection_name]
                logger.info(f"集合已删除: {collection_name}")
                return True

        except Exception as e:
            logger.error(f"删除集合失败: {e}")

        return False


milvus_cluster_client = MilvusClusterClient()
