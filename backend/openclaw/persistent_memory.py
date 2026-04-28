"""
Agent记忆持久化服务
将Agent的会话内存升级为跨会话持久化，积累企业投标历史经验
借鉴Hermes的持久化记忆设计
"""
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)


class PersistentMemoryService:
    """
    持久化记忆服务
    在PiLayerManager的内存存储之上，增加Django ORM持久化层

    记忆层级：
    - L1: 进程内存（最快，进程重启丢失）
    - L2: Django ORM（跨会话持久化）
    - L3: 企业经验库（跨Agent共享）
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

    def save_memory(
        self,
        agent_id: str,
        agent_type: str,
        key: str,
        value: Any,
        session_id: str = None,
        scope: str = 'session',
        enterprise_id: int = None,
        ttl_seconds: int = None
    ) -> bool:
        """
        持久化保存Agent记忆

        Args:
            agent_id: Agent ID
            agent_type: Agent类型
            key: 记忆键
            value: 记忆值
            session_id: 会话ID
            scope: 记忆范围 (session/agent_type/enterprise/global)
            enterprise_id: 企业ID
            ttl_seconds: 生存时间（秒），None表示永不过期

        Returns:
            bool: 是否成功
        """
        from apps.openclaw.memory_models import AgentMemoryStore

        try:
            expires_at = None
            if ttl_seconds:
                expires_at = timezone.now() + timedelta(seconds=ttl_seconds)

            lookup = {
                'agent_type': agent_type,
                'scope': scope,
                'memory_key': key,
            }
            if enterprise_id:
                lookup['enterprise_id'] = enterprise_id
            else:
                lookup['enterprise_id__isnull'] = True

            defaults = {
                'agent_id': agent_id,
                'session_id': session_id,
                'memory_value': value,
                'expires_at': expires_at,
            }

            store, created = AgentMemoryStore.objects.update_or_create(
                defaults=defaults,
                **lookup
            )

            if not created:
                store.access_count += 1
                store.last_accessed_at = timezone.now()
                store.save(update_fields=['access_count', 'last_accessed_at', 'updated_at'])

            return True

        except Exception as e:
            logger.error(f"持久化记忆失败: agent={agent_id}, key={key}, error={str(e)}")
            return False

    def load_memory(
        self,
        agent_type: str,
        key: str = None,
        scope: str = None,
        enterprise_id: int = None,
        session_id: str = None
    ) -> Any:
        """
        加载持久化记忆

        Args:
            agent_type: Agent类型
            key: 记忆键（None则返回该类型所有记忆）
            scope: 记忆范围
            enterprise_id: 企业ID
            session_id: 会话ID

        Returns:
            记忆值或记忆字典
        """
        from apps.openclaw.memory_models import AgentMemoryStore

        try:
            self._cleanup_expired()

            query = AgentMemoryStore.objects.filter(agent_type=agent_type)

            if key:
                query = query.filter(memory_key=key)
            if scope:
                query = query.filter(scope=scope)
            if enterprise_id:
                query = query.filter(enterprise_id=enterprise_id)
            if session_id:
                query = query.filter(session_id=session_id)

            if key:
                store = query.first()
                if store and not store.is_expired():
                    store.access_count += 1
                    store.last_accessed_at = timezone.now()
                    store.save(update_fields=['access_count', 'last_accessed_at'])
                    return store.memory_value
                return None

            result = {}
            for store in query:
                if not store.is_expired():
                    result[store.memory_key] = store.memory_value
                    store.access_count += 1
                    store.last_accessed_at = timezone.now()
                    store.save(update_fields=['access_count', 'last_accessed_at'])

            return result

        except Exception as e:
            logger.error(f"加载记忆失败: agent_type={agent_type}, key={key}, error={str(e)}")
            return None if key else {}

    def search_memory(
        self,
        agent_type: str = None,
        scope: str = None,
        enterprise_id: int = None,
        key_prefix: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        搜索记忆

        Returns:
            List[Dict]: 匹配的记忆列表
        """
        from apps.openclaw.memory_models import AgentMemoryStore

        try:
            self._cleanup_expired()

            query = AgentMemoryStore.objects.all()

            if agent_type:
                query = query.filter(agent_type=agent_type)
            if scope:
                query = query.filter(scope=scope)
            if enterprise_id:
                query = query.filter(enterprise_id=enterprise_id)
            if key_prefix:
                query = query.filter(memory_key__startswith=key_prefix)

            results = []
            for store in query.order_by('-updated_at')[:limit]:
                if not store.is_expired():
                    results.append({
                        'id': store.id,
                        'agent_id': store.agent_id,
                        'agent_type': store.agent_type,
                        'scope': store.scope,
                        'key': store.memory_key,
                        'value': store.memory_value,
                        'enterprise_id': store.enterprise_id,
                        'access_count': store.access_count,
                        'updated_at': store.updated_at.isoformat() if store.updated_at else None,
                    })

            return results

        except Exception as e:
            logger.error(f"搜索记忆失败: error={str(e)}")
            return []

    def delete_memory(
        self,
        agent_type: str,
        key: str,
        scope: str = None,
        enterprise_id: int = None
    ) -> bool:
        """
        删除记忆
        """
        from apps.openclaw.memory_models import AgentMemoryStore

        try:
            query = AgentMemoryStore.objects.filter(
                agent_type=agent_type,
                memory_key=key
            )
            if scope:
                query = query.filter(scope=scope)
            if enterprise_id:
                query = query.filter(enterprise_id=enterprise_id)

            deleted_count, _ = query.delete()
            return deleted_count > 0

        except Exception as e:
            logger.error(f"删除记忆失败: error={str(e)}")
            return False

    def save_enterprise_experience(
        self,
        enterprise_id: int,
        experience_type: str,
        title: str,
        content: Dict,
        source_tender_id: int = None,
        source_workflow_id: int = None,
        confidence: float = 0.5
    ) -> bool:
        """
        保存企业投标经验

        Args:
            enterprise_id: 企业ID
            experience_type: 经验类型
            title: 经验标题
            content: 经验内容
            source_tender_id: 来源招标ID
            source_workflow_id: 来源工作流ID
            confidence: 置信度

        Returns:
            bool: 是否成功
        """
        from apps.openclaw.memory_models import EnterpriseBidExperience

        try:
            EnterpriseBidExperience.objects.create(
                enterprise_id=enterprise_id,
                experience_type=experience_type,
                title=title,
                content=content,
                source_tender_id=source_tender_id,
                source_workflow_id=source_workflow_id,
                confidence=confidence,
            )

            logger.info(
                f"企业经验已保存: enterprise={enterprise_id}, "
                f"type={experience_type}, title={title}"
            )
            return True

        except Exception as e:
            logger.error(f"保存企业经验失败: error={str(e)}")
            return False

    def get_enterprise_experiences(
        self,
        enterprise_id: int,
        experience_type: str = None,
        min_confidence: float = 0.3,
        limit: int = 20
    ) -> List[Dict]:
        """
        获取企业投标经验

        Returns:
            List[Dict]: 经验列表
        """
        from apps.openclaw.memory_models import EnterpriseBidExperience

        try:
            query = EnterpriseBidExperience.objects.filter(
                enterprise_id=enterprise_id,
                confidence__gte=min_confidence
            )

            if experience_type:
                query = query.filter(experience_type=experience_type)

            experiences = query.order_by('-confidence', '-usage_count')[:limit]

            result = []
            for exp in experiences:
                exp.usage_count += 1
                exp.last_used_at = timezone.now()
                exp.save(update_fields=['usage_count', 'last_used_at'])

                result.append({
                    'id': exp.id,
                    'type': exp.experience_type,
                    'title': exp.title,
                    'content': exp.content,
                    'confidence': exp.confidence,
                    'usage_count': exp.usage_count,
                    'source_tender_id': exp.source_tender_id,
                })

            return result

        except Exception as e:
            logger.error(f"获取企业经验失败: error={str(e)}")
            return []

    def build_enterprise_context(
        self,
        enterprise_id: int,
        tender_data: Dict = None
    ) -> str:
        """
        构建企业投标经验上下文，注入到Agent的system prompt中

        Returns:
            str: 企业经验上下文文本
        """
        experiences = self.get_enterprise_experiences(
            enterprise_id=enterprise_id,
            min_confidence=0.4,
            limit=10
        )

        if not experiences:
            return ''

        parts = ["## 📚 企业历史投标经验"]

        type_labels = {
            'win_pattern': '中标模式',
            'loss_pattern': '失标教训',
            'strength': '企业优势',
            'weakness': '企业劣势',
            'pricing_strategy': '报价策略',
            'technical_preference': '技术偏好',
            'competitor_intel': '竞争对手情报',
            'region_preference': '区域偏好',
        }

        grouped = {}
        for exp in experiences:
            exp_type = exp['type']
            if exp_type not in grouped:
                grouped[exp_type] = []
            grouped[exp_type].append(exp)

        for exp_type, items in grouped.items():
            label = type_labels.get(exp_type, exp_type)
            parts.append(f"\n### {label}")
            for item in items[:3]:
                parts.append(
                    f"- **{item['title']}** (置信度: {item['confidence']:.0%}, "
                    f"使用{item['usage_count']}次)"
                )
                if isinstance(item['content'], dict):
                    for k, v in list(item['content'].items())[:3]:
                        parts.append(f"  - {k}: {str(v)[:100]}")

        parts.append("\n> 以上经验来自历史投标数据，请在生成标书时参考。")

        return '\n'.join(parts)

    def _cleanup_expired(self):
        """
        清理过期记忆
        """
        from apps.openclaw.memory_models import AgentMemoryStore

        try:
            expired_count, _ = AgentMemoryStore.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
            if expired_count > 0:
                logger.info(f"已清理 {expired_count} 条过期记忆")
        except Exception as e:
            logger.error(f"清理过期记忆失败: {str(e)}")

    def get_stats(self) -> Dict:
        """
        获取记忆统计
        """
        from apps.openclaw.memory_models import AgentMemoryStore, EnterpriseBidExperience

        try:
            memory_count = AgentMemoryStore.objects.count()
            experience_count = EnterpriseBidExperience.objects.count()

            scope_dist = dict(
                AgentMemoryStore.objects.values_list('scope').annotate(
                    count=Count('id')
                )
            )

            type_dist = dict(
                EnterpriseBidExperience.objects.values_list('experience_type').annotate(
                    count=Count('id')
                )
            )

            return {
                'total_memories': memory_count,
                'total_experiences': experience_count,
                'memory_scope_distribution': scope_dist,
                'experience_type_distribution': type_dist,
            }
        except Exception as e:
            logger.error(f"获取记忆统计失败: {str(e)}")
            return {}


persistent_memory_service = PersistentMemoryService()
