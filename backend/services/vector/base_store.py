"""
向量存储基类
为EnterpriseVectorStore和DocumentVectorStore提供通用能力
"""
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from .chroma_client import chroma_client

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """
    向量存储基类
    抽象通用方法，子类只需实现差异化逻辑
    """

    _instance = None

    @property
    @abstractmethod
    def collection_name(self) -> str:
        """子类的集合名称"""
        pass

    @property
    @abstractmethod
    def collection_description(self) -> str:
        """子类的集合描述"""
        pass

    @property
    @abstractmethod
    def doc_id_prefix(self) -> str:
        """文档ID前缀，如 'enterprise_' 或 'doc_'"""
        pass

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._collection = None
            cls._instance._initialized = False
        return cls._instance

    def _ensure_collection(self):
        """
        确保集合已初始化
        """
        if self._initialized:
            return
        self._collection = chroma_client.get_collection(
            self.collection_name,
            description=self.collection_description
        )
        self._initialized = True

    def _clean_text(self, text: str, max_length: int = 8000) -> str:
        """
        清理文本，准备向量化（通用实现）

        Args:
            text: 原始文本
            max_length: 最大长度限制

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()（）。，；：！？]', '', text)
        text = text.strip()

        if len(text) > max_length:
            text = text[:max_length]

        return text

    def _build_default_metadata(self, entity_id: str, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建默认元数据（可被子类重写）

        Args:
            entity_id: 实体ID
            extra: 额外元数据

        Returns:
            dict: 默认元数据
        """
        metadata = {
            'entity_id': str(entity_id),
            'created_at': datetime.now().isoformat(),
        }
        if extra:
            metadata.update({k: v for k, v in extra.items() if v is not None})
        return metadata

    def _format_result(self, doc_id: str, result: dict, distance: float, min_similarity: float) -> Optional[Dict[str, Any]]:
        """
        格式化单条搜索结果（可被子类重写）

        Args:
            doc_id: 文档ID
            result: Chroma返回的原始结果
            distance: 距离
            min_similarity: 最小相似度阈值

        Returns:
            dict: 格式化后的结果，或None（如果相似度低于阈值）
        """
        similarity = 1 - distance
        if similarity < min_similarity:
            return None

        return {
            'id': doc_id.replace(self.doc_id_prefix, ''),
            'document': result.get('documents', [''])[0] if result.get('documents') else '',
            'metadata': result.get('metadatas', [{}])[0] if result.get('metadatas') else {},
            'distance': distance,
            'similarity': similarity
        }

    def add(
        self,
        entity_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        添加向量（通用实现）

        Args:
            entity_id: 实体ID
            text: 用于向量化的文本
            metadata: 元数据

        Returns:
            bool: 是否成功
        """
        if not chroma_client.is_available:
            logger.warning(f"向量库不可用，无法添加{self.collection_name}向量")
            return False

        try:
            self._ensure_collection()

            doc_id = f"{self.doc_id_prefix}{entity_id}"
            default_metadata = self._build_default_metadata(entity_id, metadata)

            self._collection.upsert(
                ids=[doc_id],
                documents=[text],
                metadatas=[default_metadata]
            )

            logger.info(f"{self.collection_name}向量添加成功: {entity_id}")
            return True
        except Exception as e:
            logger.error(f"添加{self.collection_name}向量失败: {str(e)}")
            return False

    def batch_add(self, entities: List[Dict[str, Any]]) -> int:
        """
        批量添加向量（通用实现）

        Args:
            entities: 实体列表，每个元素包含 id, text, metadata

        Returns:
            int: 成功添加的数量
        """
        if not chroma_client.is_available:
            logger.warning(f"向量库不可用，无法批量添加{self.collection_name}向量")
            return 0

        try:
            self._ensure_collection()

            ids = []
            documents = []
            metadatas = []

            for e in entities:
                doc_id = f"{self.doc_id_prefix}{e['id']}"
                ids.append(doc_id)
                documents.append(e['text'])

                metadata = self._build_default_metadata(e['id'], e.get('metadata'))
                metadatas.append(metadata)

            if not ids:
                return 0

            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"批量添加{self.collection_name}向量成功: {len(ids)} 条")
            return len(ids)
        except Exception as e:
            logger.error(f"批量添加{self.collection_name}向量失败: {str(e)}")
            return 0

    def search_similar(
        self,
        query_text: str,
        n_results: int = 10,
        where_filter: Dict = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        语义相似度搜索（通用实现）

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            where_filter: 元数据过滤条件
            min_similarity: 最小相似度阈值

        Returns:
            list: 匹配结果列表
        """
        if not chroma_client.is_available:
            logger.warning(f"向量库不可用，无法进行{self.collection_name}语义搜索")
            return []

        try:
            self._ensure_collection()

            query_params = {
                'query_texts': [query_text],
                'n_results': n_results
            }

            if where_filter:
                query_params['where'] = where_filter

            results = self._collection.query(**query_params)

            formatted_results = []
            if results and results.get('ids'):
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results.get('distances') else 0

                    result = self._format_result(
                        doc_id,
                        {
                            'documents': [results['documents'][0][i]] if results.get('documents') else [''],
                            'metadatas': [results['metadatas'][0][i]] if results.get('metadatas') else [{}]
                        },
                        distance,
                        min_similarity
                    )

                    if result:
                        formatted_results.append(result)

            logger.info(f"{self.collection_name}语义搜索完成，返回 {len(formatted_results)} 条结果")
            return formatted_results
        except Exception as e:
            logger.error(f"{self.collection_name}语义搜索失败: {str(e)}")
            return []

    def search_by_embedding(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where_filter: Dict = None
    ) -> List[Dict[str, Any]]:
        """
        通过向量进行搜索（通用实现）

        Args:
            query_embedding: 查询向量
            n_results: 返回结果数量
            where_filter: 元数据过滤条件

        Returns:
            list: 匹配结果列表
        """
        if not chroma_client.is_available:
            return []

        try:
            self._ensure_collection()

            query_params = {
                'query_embeddings': [query_embedding],
                'n_results': n_results
            }

            if where_filter:
                query_params['where'] = where_filter

            results = self._collection.query(**query_params)

            formatted_results = []
            if results and results.get('ids'):
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results.get('distances') else 0

                    result = self._format_result(
                        doc_id,
                        {
                            'documents': [results['documents'][0][i]] if results.get('documents') else [''],
                            'metadatas': [results['metadatas'][0][i]] if results.get('metadatas') else [{}]
                        },
                        distance,
                        0.0
                    )

                    if result:
                        formatted_results.append(result)

            return formatted_results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []

    def delete(self, entity_id: str) -> bool:
        """
        删除向量（通用实现）

        Args:
            entity_id: 实体ID

        Returns:
            bool: 是否成功
        """
        if not chroma_client.is_available:
            return True

        try:
            self._ensure_collection()
            doc_id = f"{self.doc_id_prefix}{entity_id}"
            self._collection.delete(ids=[doc_id])
            logger.info(f"{self.collection_name}向量删除成功: {entity_id}")
            return True
        except Exception as e:
            logger.error(f"删除{self.collection_name}向量失败: {str(e)}")
            return False

    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个实体的向量信息（通用实现）

        Args:
            entity_id: 实体ID

        Returns:
            dict: 向量信息
        """
        if not chroma_client.is_available:
            return None

        try:
            self._ensure_collection()
            doc_id = f"{self.doc_id_prefix}{entity_id}"
            results = self._collection.get(ids=[doc_id])

            if results and results.get('ids'):
                return {
                    'id': entity_id,
                    'document': results['documents'][0] if results.get('documents') else '',
                    'metadata': results['metadatas'][0] if results.get('metadatas') else {}
                }
            return None
        except Exception as e:
            logger.error(f"获取{self.collection_name}向量失败: {str(e)}")
            return None

    def get_count(self) -> int:
        """
        获取集合中的实体数量

        Returns:
            int: 实体数量
        """
        return chroma_client.get_collection_count(self.collection_name)
