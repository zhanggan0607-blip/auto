"""
Chroma向量数据库客户端
统一管理Chroma连接和集合，支持用户级访问控制
安全改进：集合名UUID化，添加访问审计和防猜测机制
"""
import hashlib
import logging
import secrets
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from chromadb import PersistentClient
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.info("chromadb模块未安装，向量库功能将不可用")


class ChromaAccessControl:
    """
    Chroma访问控制类
    实现用户级数据隔离和操作审计
    安全改进：使用UUID集合名防止猜测，强制访问审计
    """

    SYSTEM_COLLECTIONS = [
        'enterprise_embeddings',
        'enterprise_vectors',
        'document_library',
        'bid_document_library',
        'shared_knowledge',
    ]

    _collection_name_cache: Dict[str, Dict[str, str]] = {}

    @staticmethod
    def _generate_collection_uuid(base_name: str, user_id: int) -> str:
        """
        生成不可预测的集合UUID

        Args:
            base_name: 基础集合名称
            user_id: 用户ID

        Returns:
            str: UUID格式的集合名
        """
        cache_key = f"{user_id}:{base_name}"
        if cache_key in ChromaAccessControl._collection_name_cache:
            return ChromaAccessControl._collection_name_cache[cache_key]

        random_suffix = secrets.token_hex(8)
        uuid_name = f"u_{user_id}_{base_name}_{random_suffix}"

        ChromaAccessControl._collection_name_cache[cache_key] = uuid_name
        return uuid_name

    @staticmethod
    def get_user_collection_name(collection_name: str, user_id: int = None) -> str:
        """
        获取用户隔离后的集合名称（UUID格式）

        Args:
            collection_name: 基础集合名称
            user_id: 用户ID

        Returns:
            str: 用户隔离后的UUID集合名称
        """
        if collection_name in ChromaAccessControl.SYSTEM_COLLECTIONS:
            return collection_name

        if user_id:
            return ChromaAccessControl._generate_collection_uuid(collection_name, user_id)
        return collection_name

    @staticmethod
    def can_access_collection(collection_name: str, user_id: int = None) -> bool:
        """
        检查用户是否有权访问集合

        Args:
            collection_name: 集合名称
            user_id: 用户ID

        Returns:
            bool: 是否有权访问
        """
        if collection_name in ChromaAccessControl.SYSTEM_COLLECTIONS:
            return True

        if not collection_name.startswith('u_'):
            return False

        if user_id and f"_{user_id}_" in collection_name:
            return True

        ChromaAccessControl.log_access(
            'access_check', collection_name, user_id, success=False,
            error='collection_name format invalid or user_id mismatch'
        )
        return False

    @staticmethod
    def log_access(
        operation: str,
        collection_name: str,
        user_id: int = None,
        doc_id: str = None,
        success: bool = True,
        error: str = None
    ):
        """
        记录集合访问日志（强制执行）

        Args:
            operation: 操作类型 (add, search, delete, get, access_check)
            collection_name: 集合名称
            user_id: 用户ID
            doc_id: 文档ID
            success: 是否成功
            error: 错误信息
        """
        log_data = {
            'operation': operation,
            'collection': collection_name,
            'user_id': user_id,
            'doc_id': doc_id,
            'success': success,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
        }
        if error:
            log_data['error'] = error[:200]

        if success:
            logger.info(f"Chroma访问: {log_data}")
        else:
            logger.warning(f"Chroma访问被拒绝: {log_data}")


class ChromaClient:
    """
    Chroma向量数据库客户端
    单例模式，统一管理所有集合，支持用户级访问控制
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
            cls._instance._collections = {}
            cls._instance._collection_timestamps = {}
            cls._instance._collection_ttl = 300
            cls._instance._available = False
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        初始化Chroma客户端
        """
        if not CHROMA_AVAILABLE:
            logger.info("Chroma不可用，跳过初始化")
            self._available = False
            return

        try:
            persist_dir = Path(settings.CHROMA_CONFIG.get('PERSIST_DIRECTORY', 'data/chroma'))
            persist_dir.mkdir(parents=True, exist_ok=True)

            self._client = PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            self._available = True
            logger.info(f"Chroma客户端初始化成功，持久化目录: {persist_dir}")

        except Exception as e:
            logger.error(f"Chroma客户端初始化失败: {str(e)}")
            self._available = False

    @property
    def is_available(self) -> bool:
        """
        检查Chroma是否可用
        """
        return self._available

    def get_collection(
        self,
        name: str,
        description: str = None,
        user_id: int = None
    ) -> Optional[Any]:
        """
        获取或创建集合（带访问控制）

        Args:
            name: 集合名称
            description: 集合描述
            user_id: 用户ID，用于数据隔离

        Returns:
            Collection对象
        """
        if not self._available:
            logger.debug(f"Chroma不可用，无法获取集合: {name}")
            return None

        isolated_name = ChromaAccessControl.get_user_collection_name(name, user_id)

        if not ChromaAccessControl.can_access_collection(isolated_name, user_id):
            ChromaAccessControl.log_access('get', name, user_id, success=False)
            logger.warning(f"用户 {user_id} 无权访问集合: {name}")
            return None

        if isolated_name in self._collections:
            ts = self._collection_timestamps.get(isolated_name, 0)
            import time
            if time.time() - ts < self._collection_ttl:
                return self._collections[isolated_name]
            else:
                del self._collections[isolated_name]
                self._collection_timestamps.pop(isolated_name, None)

        try:
            collection = self._client.get_or_create_collection(
                name=isolated_name,
                metadata={
                    "description": description or name,
                    "owner_user_id": str(user_id) if user_id else "shared",
                    "base_collection": name
                }
            )
            self._collections[isolated_name] = collection
            import time
            self._collection_timestamps[isolated_name] = time.time()
            ChromaAccessControl.log_access('get', name, user_id, success=True)
            logger.info(f"获取/创建集合: {isolated_name} (base: {name})")
            return collection

        except Exception as e:
            logger.error(f"获取集合失败 {name}: {str(e)}")
            ChromaAccessControl.log_access('get', name, user_id, success=False, error=str(e))
            return None

    def delete_collection(self, name: str, user_id: int = None) -> bool:
        """
        删除集合（带访问控制）

        Args:
            name: 集合名称
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        if not self._available:
            return True

        isolated_name = ChromaAccessControl.get_user_collection_name(name, user_id)

        if not ChromaAccessControl.can_access_collection(isolated_name, user_id):
            ChromaAccessControl.log_access('delete', name, user_id, success=False)
            logger.warning(f"用户 {user_id} 无权删除集合: {name}")
            return False

        try:
            self._client.delete_collection(isolated_name)
            if isolated_name in self._collections:
                del self._collections[isolated_name]
            ChromaAccessControl.log_access('delete', name, user_id, success=True)
            logger.info(f"删除集合: {isolated_name}")
            return True

        except Exception as e:
            logger.error(f"删除集合失败 {name}: {str(e)}")
            ChromaAccessControl.log_access('delete', name, user_id, success=False, error=str(e))
            return False

    def get_collection_count(self, name: str, user_id: int = None) -> int:
        """
        获取集合中的文档数量

        Args:
            name: 集合名称
            user_id: 用户ID

        Returns:
            int: 文档数量
        """
        collection = self.get_collection(name, user_id=user_id)
        if collection:
            try:
                count = collection.count()
                ChromaAccessControl.log_access('count', name, user_id, success=True)
                return count
            except Exception as e:
                logger.error(f"获取集合数量失败: {str(e)}")
                ChromaAccessControl.log_access('count', name, user_id, success=False, error=str(e))
        return 0

    def add_document(
        self,
        collection_name: str,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        user_id: int = None
    ) -> bool:
        """
        添加文档到集合（带访问控制）

        Args:
            collection_name: 集合名称
            doc_id: 文档ID
            content: 文档内容
            metadata: 元数据
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        collection = self.get_collection(collection_name, user_id=user_id)
        if not collection:
            return False

        try:
            metadata = metadata or {}
            metadata['user_id'] = str(user_id) if user_id else 'system'
            metadata['created_by'] = 'chroma_client'

            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
            ChromaAccessControl.log_access('add', collection_name, user_id, doc_id, success=True)
            logger.info(f"文档添加成功: {doc_id} -> {collection_name}")
            return True

        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            ChromaAccessControl.log_access('add', collection_name, user_id, doc_id, success=False, error=str(e))
            return False

    def search(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 10,
        user_id: int = None,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索集合（带访问控制）

        Args:
            collection_name: 集合名称
            query_text: 查询文本
            n_results: 返回结果数量
            user_id: 用户ID
            filter_metadata: 元数据过滤条件

        Returns:
            List[Dict]: 搜索结果
        """
        collection = self.get_collection(collection_name, user_id=user_id)
        if not collection:
            return []

        try:
            where_filter = None
            if filter_metadata and user_id:
                where_filter = {
                    "$and": [
                        {"user_id": str(user_id)},
                        filter_metadata
                    ]
                }
            elif filter_metadata:
                where_filter = filter_metadata
            elif user_id:
                where_filter = {"user_id": str(user_id)}

            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )

            formatted_results = []
            if results and 'documents' in results:
                for i, doc in enumerate(results.get('documents', [[]])[0]):
                    formatted_results.append({
                        'id': results.get('ids', [[]])[0][i] if i < len(results.get('ids', [[]])[0]) else None,
                        'content': doc,
                        'distance': results.get('distances', [[]])[0][i] if i < len(results.get('distances', [[]])[0]) else None,
                        'metadata': results.get('metadatas', [[]])[0][i] if i < len(results.get('metadatas', [[]])[0]) else None,
                    })

            ChromaAccessControl.log_access('search', collection_name, user_id, success=True)
            logger.debug(f"搜索完成: {collection_name}, 返回 {len(formatted_results)} 条结果")
            return formatted_results

        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            ChromaAccessControl.log_access('search', collection_name, user_id, success=False, error=str(e))
            return []

    def delete_document(
        self,
        collection_name: str,
        doc_id: str,
        user_id: int = None
    ) -> bool:
        """
        删除文档（带访问控制）

        Args:
            collection_name: 集合名称
            doc_id: 文档ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        collection = self.get_collection(collection_name, user_id=user_id)
        if not collection:
            return False

        try:
            collection.delete(ids=[doc_id])
            ChromaAccessControl.log_access('delete_doc', collection_name, user_id, doc_id, success=True)
            logger.info(f"文档删除成功: {doc_id} from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {str(e)}")
            ChromaAccessControl.log_access('delete_doc', collection_name, user_id, doc_id, success=False, error=str(e))
            return False


chroma_client = ChromaClient()