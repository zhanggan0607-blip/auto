"""
文档向量存储服务
统一管理投标文档的向量化存储和语义检索

使用BaseVectorStore基类，复用通用能力
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from .base_store import BaseVectorStore
from .chroma_client import chroma_client

logger = logging.getLogger(__name__)


class DocumentVectorStore(BaseVectorStore):
    """
    文档向量存储
    管理投标文档的向量化存储和语义检索
    """

    @property
    def collection_name(self) -> str:
        return 'bid_document_library'

    @property
    def collection_description(self) -> str:
        return "投标文档向量库，存储历史投标文档供参考"

    @property
    def doc_id_prefix(self) -> str:
        return 'doc_'

    def _build_default_metadata(self, entity_id: str, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        重写元数据构建，添加文档专用字段
        """
        metadata = {
            'doc_id': str(entity_id),
            'created_at': datetime.now().isoformat(),
        }

        if extra:
            metadata.update({k: v for k, v in extra.items() if v is not None})

        return metadata

    def _clean_text(self, text: str, max_length: int = 8000) -> str:
        """
        重写文本清理，文档需要更严格的清理
        """
        if not text:
            return ""

        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()（）。，；：！？]', '', text)
        text = text.strip()

        if len(text) > max_length:
            text = text[:max_length]

        return text

    def _format_result(self, doc_id: str, result: dict, distance: float, min_similarity: float) -> Optional[Dict[str, Any]]:
        """
        重写结果格式化，文档需要不同的ID提取
        """
        similarity = 1 - distance
        if similarity < min_similarity:
            return None

        return {
            'id': int(doc_id.replace(self.doc_id_prefix, '')),
            'document': result.get('documents', [''])[0] if result.get('documents') else '',
            'metadata': result.get('metadatas', [{}])[0] if result.get('metadatas') else {},
            'distance': distance,
            'similarity': similarity
        }

    def add_document(
        self,
        doc_id: int,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        添加文档向量

        Args:
            doc_id: 文档ID
            title: 文档标题
            content: 文档内容
            metadata: 元数据（文档类型、行业等）

        Returns:
            bool: 是否成功
        """
        if not chroma_client.is_available:
            logger.warning("向量库不可用，无法添加文档向量")
            return False

        try:
            vector_text = f"{title}\n{content}"
            vector_text = self._clean_text(vector_text)

            if len(vector_text) < 50:
                logger.warning(f"文档内容过短，跳过向量化: {doc_id}")
                return False

            extra_metadata = {
                'title': title[:200] if title else '',
                'doc_type': metadata.get('document_type', 'other') if metadata else 'other',
                'source_type': metadata.get('source_type', 'upload') if metadata else 'upload',
                'industry': metadata.get('industry', '') if metadata else '',
                'project_type': metadata.get('project_type', '') if metadata else '',
            }

            return self.add(str(doc_id), vector_text, extra_metadata)

        except Exception as e:
            logger.error(f"添加文档向量失败: {str(e)}")
            return False

    def batch_add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        批量添加文档向量

        Args:
            documents: 文档列表，每个元素包含 id, title, content, metadata

        Returns:
            int: 成功添加的数量
        """
        if not chroma_client.is_available:
            return 0

        entities = []
        for doc in documents:
            vector_text = f"{doc.get('title', '')}\n{doc.get('content', '')}"
            vector_text = self._clean_text(vector_text)

            if len(vector_text) < 50:
                continue

            metadata = doc.get('metadata', {})
            extra_metadata = {
                'title': doc.get('title', '')[:200],
                'doc_type': metadata.get('document_type', 'other'),
                'source_type': metadata.get('source_type', 'upload'),
                'industry': metadata.get('industry', ''),
                'project_type': metadata.get('project_type', ''),
            }

            entities.append({
                'id': str(doc['id']),
                'text': vector_text,
                'metadata': extra_metadata
            })

        if not entities:
            return 0

        return self.batch_add(entities)

    def search_similar(
        self,
        query_text: str,
        n_results: int = 10,
        filters: Dict = None,
        doc_types: List[str] = None,
        industries: List[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        语义相似度搜索（文档专用）

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            filters: 元数据过滤条件
            doc_types: 文档类型过滤
            industries: 行业过滤
            min_similarity: 最小相似度阈值

        Returns:
            list: 匹配结果列表
        """
        if not chroma_client.is_available:
            return []

        try:
            self._ensure_collection()

            where_filter = None
            if filters or doc_types or industries:
                conditions = []

                if doc_types:
                    conditions.append({"doc_type": {"$in": doc_types}})
                if industries:
                    conditions.append({"industry": {"$in": industries}})

                if filters:
                    for key, value in filters.items():
                        if value:
                            conditions.append({key: value})

                if len(conditions) == 1:
                    where_filter = conditions[0]
                elif len(conditions) > 1:
                    where_filter = {"$and": conditions}

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

            logger.info(f"文档语义搜索完成，返回 {len(formatted_results)} 条结果")
            return formatted_results
        except Exception as e:
            logger.error(f"文档语义搜索失败: {str(e)}")
            return []

    def delete_document(self, doc_id: int) -> bool:
        """
        删除文档向量

        Args:
            doc_id: 文档ID

        Returns:
            bool: 是否成功
        """
        return self.delete(str(doc_id))

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个文档的向量信息

        Args:
            doc_id: 文档ID

        Returns:
            dict: 文档向量信息
        """
        return self.get(str(doc_id))

    def search_by_project_type(
        self,
        query_text: str,
        project_type: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        按项目类型搜索相似文档

        Args:
            query_text: 查询文本
            project_type: 项目类型
            n_results: 返回结果数量

        Returns:
            list: 匹配结果列表
        """
        return self.search_similar(
            query_text=query_text,
            n_results=n_results,
            filters={'project_type': project_type}
        )

    def search_by_industry(
        self,
        query_text: str,
        industry: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        按行业搜索相似文档

        Args:
            query_text: 查询文本
            industry: 行业
            n_results: 返回结果数量

        Returns:
            list: 匹配结果列表
        """
        return self.search_similar(
            query_text=query_text,
            n_results=n_results,
            industries=[industry]
        )


document_vector_store = DocumentVectorStore()
