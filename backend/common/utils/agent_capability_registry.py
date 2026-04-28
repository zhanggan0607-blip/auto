"""
Agent能力注册中心
统一管理Agent能力，支持任务智能分发和Agent协作
"""
import logging
from typing import Dict, List, Optional, Set, Type
from dataclasses import dataclass, field

from core.constants import AgentType, AgentCapability

logger = logging.getLogger(__name__)


@dataclass
class CapabilityInfo:
    """
    能力信息
    """
    capability: AgentCapability
    agent_types: List[AgentType] = field(default_factory=list)
    description: str = ""
    priority: int = 0


class AgentCapabilityRegistry:
    """
    Agent能力注册中心

    功能：
    1. 注册Agent及其能力
    2. 根据任务类型查询可用的Agent
    3. 能力优先级管理
    4. Agent协作调度

    使用示例：
        # 注册Agent能力
        registry = AgentCapabilityRegistry()
        registry.register_capability(
            AgentCapability.CRAWLING,
            [AgentType.COLLECTOR],
            description="网页数据采集"
        )

        # 获取可执行任务的Agent
        agents = registry.get_agents_for_capability(AgentCapability.CRAWLING)
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
        self._capabilities: Dict[AgentCapability, CapabilityInfo] = {}
        self._agent_capabilities: Dict[AgentType, Set[AgentCapability]] = {}
        self._task_capability_map: Dict[str, AgentCapability] = {}

        self._init_default_capabilities()

    def _init_default_capabilities(self):
        """初始化默认能力映射"""
        self.register_capability(
            AgentCapability.CRAWLING,
            [AgentType.COLLECTOR],
            description="网页数据采集",
            priority=1
        )
        self.register_capability(
            AgentCapability.PARSING,
            [AgentType.COLLECTOR],
            description="网页内容解析",
            priority=1
        )
        self.register_capability(
            AgentCapability.MATCHING,
            [AgentType.MATCHER],
            description="企业招标匹配",
            priority=1
        )
        self.register_capability(
            AgentCapability.ANALYZING,
            [AgentType.ANALYST],
            description="数据分析处理",
            priority=1
        )
        self.register_capability(
            AgentCapability.GENERATING,
            [AgentType.GENERATOR],
            description="文档生成",
            priority=1
        )
        self.register_capability(
            AgentCapability.REVIEWING,
            [AgentType.REVIEWER],
            description="文档审核",
            priority=1
        )
        self.register_capability(
            AgentCapability.OPTIMIZING,
            [AgentType.OPTIMIZER],
            description="流程优化",
            priority=1
        )
        self.register_capability(
            AgentCapability.TRACKING,
            [AgentType.TRACKER],
            description="中标追踪",
            priority=1
        )
        self.register_capability(
            AgentCapability.ORCHESTRATING,
            [AgentType.ORCHESTRATOR],
            description="任务编排协调",
            priority=1
        )
        self.register_capability(
            AgentCapability.UPLOADING,
            [AgentType.COLLECTOR, AgentType.GENERATOR],
            description="文件上传",
            priority=2
        )
        self.register_capability(
            AgentCapability.CHATTING,
            [AgentType.ORCHESTRATOR],
            description="对话交互",
            priority=1
        )

        self._task_capability_map = {
            'collect_tender': AgentCapability.CRAWLING,
            'collect_enterprise': AgentCapability.CRAWLING,
            'parse_content': AgentCapability.PARSING,
            'match_enterprise': AgentCapability.MATCHING,
            'analyze_tender': AgentCapability.ANALYZING,
            'generate_document': AgentCapability.GENERATING,
            'review_document': AgentCapability.REVIEWING,
            'track_result': AgentCapability.TRACKING,
            'orchestrate_workflow': AgentCapability.ORCHESTRATING,
            'upload_file': AgentCapability.UPLOADING,
        }

    def register_capability(
        self,
        capability: AgentCapability,
        agent_types: List[AgentType],
        description: str = "",
        priority: int = 0
    ):
        """
        注册能力

        Args:
            capability: 能力枚举
            agent_types: 支持该能力的Agent类型列表
            description: 能力描述
            priority: 优先级（数字越大优先级越高）
        """
        if capability not in self._capabilities:
            self._capabilities[capability] = CapabilityInfo(
                capability=capability,
                description=description,
                priority=priority
            )

        info = self._capabilities[capability]
        for agent_type in agent_types:
            if agent_type not in info.agent_types:
                info.agent_types.append(agent_type)

            if agent_type not in self._agent_capabilities:
                self._agent_capabilities[agent_type] = set()
            self._agent_capabilities[agent_type].add(capability)

        if priority > info.priority:
            info.priority = priority

        logger.info(f"Registered capability: {capability.value} for agents: {[a.value for a in agent_types]}")

    def get_agents_for_capability(
        self,
        capability: AgentCapability,
        min_priority: int = 0
    ) -> List[AgentType]:
        """
        获取支持特定能力的Agent类型

        Args:
            capability: 能力枚举
            min_priority: 最小优先级

        Returns:
            List[AgentType]: 支持该能力的Agent类型列表（按优先级排序）
        """
        info = self._capabilities.get(capability)
        if not info:
            return []

        return [
            agent_type for agent_type in info.agent_types
            if self._capabilities[capability].priority >= min_priority
        ]

    def get_capabilities_for_agent(self, agent_type: AgentType) -> Set[AgentCapability]:
        """
        获取Agent支持的所有能力

        Args:
            agent_type: Agent类型

        Returns:
            Set[AgentCapability]: 能力集合
        """
        return self._agent_capabilities.get(agent_type, set())

    def get_capability_for_task(self, task_type: str) -> Optional[AgentCapability]:
        """
        根据任务类型获取所需能力

        Args:
            task_type: 任务类型标识

        Returns:
            AgentCapability: 所需能力
        """
        return self._task_capability_map.get(task_type)

    def get_agent_for_task(self, task_type: str) -> List[AgentType]:
        """
        根据任务类型获取最适合的Agent

        Args:
            task_type: 任务类型标识

        Returns:
            List[AgentType]: 适合的Agent类型列表
        """
        capability = self.get_capability_for_task(task_type)
        if not capability:
            return []
        return self.get_agents_for_capability(capability)

    def has_capability(self, agent_type: AgentType, capability: AgentCapability) -> bool:
        """
        检查Agent是否具有特定能力

        Args:
            agent_type: Agent类型
            capability: 能力枚举

        Returns:
            bool: 是否具有该能力
        """
        return capability in self._agent_capabilities.get(agent_type, set())

    def register_task_capability_mapping(self, task_type: str, capability: AgentCapability):
        """
        注册任务类型到能力的映射

        Args:
            task_type: 任务类型标识
            capability: 能力枚举
        """
        self._task_capability_map[task_type] = capability
        logger.info(f"Mapped task '{task_type}' to capability '{capability.value}'")

    def list_all_capabilities(self) -> List[CapabilityInfo]:
        """
        列出所有注册的能力

        Returns:
            List[CapabilityInfo]: 能力信息列表
        """
        return list(self._capabilities.values())

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        capability_stats = {}
        for cap, info in self._capabilities.items():
            capability_stats[cap.value] = {
                'description': info.description,
                'priority': info.priority,
                'agent_count': len(info.agent_types),
                'agents': [a.value for a in info.agent_types]
            }

        return {
            'total_capabilities': len(self._capabilities),
            'total_agents': len(self._agent_capabilities),
            'task_mappings': len(self._task_capability_map),
            'capabilities': capability_stats
        }


agent_capability_registry = AgentCapabilityRegistry()
