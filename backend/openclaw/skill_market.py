"""
OpenClaw SkillMarket - Agent工具标准化市场

提供Agent工具的标准化注册、发现、调用和管理功能

核心概念：
- Tool：标准化的工具单元
- SkillMarket：工具注册和管理中心
- Capability：能力抽象接口

使用示例：
    from openclaw.skill_market import skill_market, Tool, Capability

    # 注册工具
    skill_market.register_tool(my_tool)

    # 发现工具
    tools = skill_market.discover_tools(category='web')

    # 调用工具
    result = await skill_market.execute_tool('web_search', query='...')
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from functools import wraps

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具分类枚举"""
    WEB = 'web'              # 网络工具
    DATA = 'data'            # 数据处理
    FILE = 'file'            # 文件操作
    DATABASE = 'database'    # 数据库操作
    API = 'api'              # API调用
    LLM = 'llm'              # LLM相关
    CRAWLER = 'crawler'      # 爬虫工具
    DOCUMENT = 'document'     # 文档处理
    NOTIFICATION = 'notification'  # 通知工具
    UTILITY = 'utility'       # 通用工具


class ToolScope(Enum):
    """工具作用域"""
    AGENT = 'agent'          # Agent级别工具
    GLOBAL = 'global'        # 全局工具
    SESSION = 'session'      # 会话级别工具


@dataclass
class ToolMetadata:
    """
    工具元数据
    """
    name: str
    description: str
    version: str = '1.0.0'
    category: ToolCategory = ToolCategory.UTILITY
    scope: ToolScope = ToolScope.GLOBAL
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    returns: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict] = field(default_factory=list)
    author: str = ''
    dependencies: List[str] = field(default_factory=list)
    rate_limit: Optional[int] = None
    timeout: int = 30
    retryable: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """
    工具执行结果
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_name: str = ''
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'execution_time': self.execution_time,
            'tool_name': self.tool_name,
            'metadata': self.metadata
        }


class Tool:
    """
    标准化工具基类

    所有Agent工具都应继承此类或实现相同接口
    """

    metadata: ToolMetadata = None

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._execution_count: int = 0
        self._last_executed: Optional[datetime] = None

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        raise NotImplementedError("Subclasses must implement execute method")

    def validate(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        验证参数

        Args:
            **kwargs: 待验证的参数

        Returns:
            (是否有效, 错误消息)
        """
        if not self.metadata or not self.metadata.parameters:
            return True, None

        required = self.metadata.parameters.get('required', [])
        for field_name in required:
            if field_name not in kwargs:
                return False, f"Missing required parameter: {field_name}"

        return True, None

    def get_cache_key(self, **kwargs) -> str:
        """
        生成缓存键
        """
        import hashlib
        import json
        key_data = {
            'tool': self.metadata.name if self.metadata else self.__class__.__name__,
            'params': kwargs
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def get_cached(self, **kwargs) -> Optional[Any]:
        """获取缓存"""
        key = self.get_cache_key(**kwargs)
        return self._cache.get(key)

    def set_cache(self, **kwargs):
        """设置缓存"""
        key = self.get_cache_key(**kwargs)
        self._cache[key] = {
            'result': None,
            'created_at': datetime.now()
        }

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()

    @property
    def execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        return {
            'total_executions': self._execution_count,
            'last_executed': self._last_executed.isoformat() if self._last_executed else None
        }


def tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.UTILITY,
    tags: List[str] = None,
    parameters: Dict = None,
    returns: Dict = None,
    timeout: int = 30,
    retryable: bool = True
):
    """
    工具装饰器

    用于将函数注册为标准化工具

    Example:
        @tool(
            name='web_search',
            description='Search the web',
            category=ToolCategory.WEB,
            tags=['search', 'web']
        )
        async def web_search(query: str, limit: int = 10):
            # 实现
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            parameters=parameters or {},
            returns=returns or {},
            timeout=timeout,
            retryable=retryable
        )

        wrapper.metadata = metadata
        wrapper._is_tool = True

        return wrapper
    return decorator


class Capability:
    """
    能力抽象基类

    用于定义Agent可以调用的标准能力接口
    """

    name: str = ''
    description: str = ''
    version: str = '1.0.0'

    async def execute(self, context: Dict, **kwargs) -> ToolResult:
        """
        执行能力

        Args:
            context: 执行上下文
            **kwargs: 能力参数

        Returns:
            ToolResult: 执行结果
        """
        raise NotImplementedError


class SkillMarket:
    """
    Skill市场 - Agent工具管理中心

    功能：
    - 工具注册和发现
    - 工具分类和检索
    - 工具执行和调度
    - 执行统计和监控
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
        self._tools: Dict[str, Tool] = {}
        self._tool_functions: Dict[str, Callable] = {}
        self._capabilities: Dict[str, Capability] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._execution_history: List[ToolResult] = []
        self._max_history: int = 1000

        self._standard_tools = self._register_standard_tools()

    def _register_standard_tools(self) -> Dict[str, Callable]:
        """
        注册标准工具

        这些工具是系统内置的，所有Agent都可以使用
        """
        standard_tools = {}

        @tool(
            name='http_request',
            description='发送HTTP请求',
            category=ToolCategory.API,
            tags=['network', 'http', 'request'],
            parameters={
                'required': ['url', 'method'],
                'properties': {
                    'url': {'type': 'string', 'description': '请求URL'},
                    'method': {'type': 'string', 'enum': ['GET', 'POST', 'PUT', 'DELETE']},
                    'headers': {'type': 'object'},
                    'data': {'type': 'object'}
                }
            },
            timeout=30
        )
        async def http_request(url: str, method: str = 'GET', headers: Dict = None, data: Dict = None):
            import requests
            try:
                response = requests.request(method, url, headers=headers, json=data, timeout=30)
                return {
                    'status': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.text
                }
            except Exception as e:
                return {'error': str(e)}

        standard_tools['http_request'] = http_request

        @tool(
            name='sleep',
            description='暂停执行',
            category=ToolCategory.UTILITY,
            tags=['utility', 'delay'],
            parameters={
                'required': ['seconds'],
                'properties': {
                    'seconds': {'type': 'number', 'description': '暂停秒数'}
                }
            },
            timeout=60
        )
        async def sleep(seconds: float):
            await asyncio.sleep(seconds)
            return {'slept': seconds}

        standard_tools['sleep'] = sleep

        @tool(
            name='current_time',
            description='获取当前时间',
            category=ToolCategory.UTILITY,
            tags=['utility', 'time']
        )
        async def current_time():
            return {'datetime': datetime.now().isoformat()}

        standard_tools['current_time'] = current_time

        return standard_tools

    def register_tool(self, tool_instance: Tool):
        """
        注册工具实例

        Args:
            tool_instance: Tool子类实例
        """
        if not isinstance(tool_instance, Tool):
            raise TypeError("tool_instance must be a Tool subclass")

        name = tool_instance.metadata.name if tool_instance.metadata else tool_instance.__class__.__name__
        self._tools[name] = tool_instance
        self._metadata[name] = tool_instance.metadata
        logger.info(f"Registered tool: {name}")

    def register_function(
        self,
        name: str,
        func: Callable,
        metadata: ToolMetadata = None
    ):
        """
        注册函数式工具

        Args:
            name: 工具名称
            func: 异步函数
            metadata: 元数据
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Function must be async")

        self._tool_functions[name] = func
        if metadata:
            self._metadata[name] = metadata
        logger.info(f"Registered function tool: {name}")

    def register_capability(self, capability: Capability):
        """
        注册能力

        Args:
            capability: Capability子类实例
        """
        name = capability.name
        self._capabilities[name] = capability
        logger.info(f"Registered capability: {name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具实例"""
        return self._tools.get(name)

    def get_function(self, name: str) -> Optional[Callable]:
        """获取函数工具"""
        if name in self._standard_tools:
            return self._standard_tools[name]
        return self._tool_functions.get(name)

    def get_capability(self, name: str) -> Optional[Capability]:
        """获取能力"""
        return self._capabilities.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """获取工具元数据"""
        return self._metadata.get(name)

    def discover_tools(
        self,
        category: ToolCategory = None,
        tag: str = None,
        scope: ToolScope = None,
        search: str = None
    ) -> List[ToolMetadata]:
        """
        发现工具

        Args:
            category: 按分类筛选
            tag: 按标签筛选
            scope: 按作用域筛选
            search: 搜索名称或描述

        Returns:
            匹配的工具元数据列表
        """
        results = []

        for name, metadata in self._metadata.items():
            if category and metadata.category != category:
                continue
            if tag and tag not in metadata.tags:
                continue
            if scope and metadata.scope != scope:
                continue
            if search:
                search_lower = search.lower()
                if search_lower not in name.lower() and search_lower not in metadata.description.lower():
                    continue

            results.append(metadata)

        return sorted(results, key=lambda m: m.name)

    def discover_functions(
        self,
        category: ToolCategory = None,
        tag: str = None
    ) -> List[str]:
        """
        发现函数工具

        Args:
            category: 按分类筛选
            tag: 按标签筛选

        Returns:
            匹配的函数名称列表
        """
        results = []

        for name, metadata in self._metadata.items():
            if metadata.name in self._tool_functions or name in self._standard_tools:
                if category and metadata.category != category:
                    continue
                if tag and tag not in metadata.tags:
                    continue
                results.append(name)

        return results

    async def execute_tool(
        self,
        name: str,
        context: Dict = None,
        **kwargs
    ) -> ToolResult:
        """
        执行工具

        Args:
            name: 工具名称
            context: 执行上下文
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        from datetime import datetime as dt
        start_time = dt.now()

        tool_instance = self.get_tool(name)
        tool_func = self.get_function(name)

        if not tool_instance and not tool_func:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
                tool_name=name
            )

        try:
            result_data = None

            if tool_instance:
                valid, error = tool_instance.validate(**kwargs)
                if not valid:
                    return ToolResult(
                        success=False,
                        error=error,
                        tool_name=name
                    )

                result_data = await tool_instance.execute(**kwargs)
                tool_instance._execution_count += 1
                tool_instance._last_executed = dt.now()
            else:
                if asyncio.iscoroutinefunction(tool_func):
                    result_data = await tool_func(**kwargs)
                else:
                    result_data = tool_func(**kwargs)

            execution_time = (dt.now() - start_time).total_seconds()

            result = ToolResult(
                success=True,
                data=result_data,
                execution_time=execution_time,
                tool_name=name
            )

            self._add_to_history(result)
            return result

        except Exception as e:
            execution_time = (dt.now() - start_time).total_seconds()
            logger.error(f"Tool execution failed: {name}, error: {str(e)}")

            result = ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                tool_name=name
            )

            self._add_to_history(result)
            return result

    def _add_to_history(self, result: ToolResult):
        """添加执行历史"""
        self._execution_history.append(result)
        if len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)

    def get_execution_history(
        self,
        tool_name: str = None,
        limit: int = 100
    ) -> List[ToolResult]:
        """
        获取执行历史

        Args:
            tool_name: 筛选工具名称
            limit: 返回数量

        Returns:
            执行结果列表
        """
        history = self._execution_history

        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        category_stats = {}
        tool_stats = {}

        for metadata in self._metadata.values():
            cat = metadata.category.value
            category_stats[cat] = category_stats.get(cat, 0) + 1

        for name, tool in self._tools.items():
            stats = tool.execution_stats
            tool_stats[name] = stats

        total_executions = sum(s.get('total_executions', 0) for s in tool_stats.values())

        return {
            'total_tools': len(self._tools),
            'total_functions': len(self._tool_functions) + len(self._standard_tools),
            'total_capabilities': len(self._capabilities),
            'total_metadata': len(self._metadata),
            'total_executions': total_executions,
            'category_stats': category_stats,
            'tool_stats': tool_stats
        }

    def list_all_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def list_all_functions(self) -> List[str]:
        """列出所有函数工具名称"""
        return list(self._standard_tools.keys()) + list(self._tool_functions.keys())

    def list_categories(self) -> List[str]:
        """列出所有分类"""
        categories = set()
        for metadata in self._metadata.values():
            categories.add(metadata.category.value)
        return sorted(list(categories))


skill_market = SkillMarket()
