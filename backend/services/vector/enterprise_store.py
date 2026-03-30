"""
企业向量存储服务
统一管理企业信息的向量化存储和语义检索

使用BaseVectorStore基类，复用通用能力
"""
import logging
from typing import List, Dict, Any

from .base_store import BaseVectorStore

logger = logging.getLogger(__name__)


class EnterpriseVectorStore(BaseVectorStore):
    """
    企业向量存储
    管理企业资质、经营范围、业绩等信息的向量化存储
    """

    @property
    def collection_name(self) -> str:
        return 'enterprise_vectors'

    @property
    def collection_description(self) -> str:
        return "企业信息向量存储，包含资质、经营范围、业绩等"

    @property
    def doc_id_prefix(self) -> str:
        return 'enterprise_'

    def _build_default_metadata(self, entity_id: str, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        重写元数据构建，添加企业专用字段
        """
        metadata = {
            'enterprise_id': str(entity_id),
            'created_at': self._get_timestamp(),
        }
        if extra:
            metadata.update({k: v for k, v in extra.items() if v is not None})
        return metadata

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

    def _format_result(self, doc_id: str, result: dict, distance: float, min_similarity: float) -> Any:
        """
        重写结果格式化
        """
        from .base_store import Optional
        import typing

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

    def add_enterprise(
        self,
        enterprise_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        添加企业向量

        Args:
            enterprise_id: 企业ID
            text: 用于向量化的文本（资质+经营范围+业绩）
            metadata: 元数据（企业名称、行业等）

        Returns:
            bool: 是否成功
        """
        return self.add(enterprise_id, text, metadata)

    def batch_add_enterprises(self, enterprises: List[Dict[str, Any]]) -> int:
        """
        批量添加企业向量

        Args:
            enterprises: 企业列表，每个元素包含 id, text, metadata

        Returns:
            int: 成功添加的数量
        """
        if not enterprises:
            return 0

        entities = []
        for e in enterprises:
            entities.append({
                'id': e['id'],
                'text': e['text'],
                'metadata': e.get('metadata', {})
            })

        return self.batch_add(entities)

    def match_tender(
        self,
        tender_content: str,
        enterprise_ids: List[str] = None,
        n_results: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        招标公告与企业匹配

        Args:
            tender_content: 招标公告内容
            enterprise_ids: 限定企业ID列表（可选）
            n_results: 返回结果数量
            min_similarity: 最小相似度阈值

        Returns:
            list: 匹配的企业列表
        """
        where_filter = None
        if enterprise_ids:
            where_filter = {
                'enterprise_id': {'$in': [str(eid) for eid in enterprise_ids]}
            }

        results = self.search_similar(
            query_text=tender_content,
            n_results=n_results,
            where_filter=where_filter,
            min_similarity=min_similarity
        )

        return results

    def delete_enterprise(self, enterprise_id: str) -> bool:
        """
        删除企业向量

        Args:
            enterprise_id: 企业ID

        Returns:
            bool: 是否成功
        """
        return self.delete(enterprise_id)

    def get_enterprise(self, enterprise_id: str) -> Any:
        """
        获取单个企业的向量信息

        Args:
            enterprise_id: 企业ID

        Returns:
            dict: 企业向量信息
        """
        return self.get(enterprise_id)


enterprise_vector_store = EnterpriseVectorStore()
