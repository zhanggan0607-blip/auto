"""
OpenClaw Skill注册表
插件化技能仓库管理
"""
import asyncio
import importlib
import importlib.util
import inspect
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from .config import OPENCLAW_CONFIG


logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """
    Skill元数据
    """
    name: str
    description: str
    version: str = '1.0.0'
    author: str = ''
    category: str = 'general'
    tags: List[str] = field(default_factory=list)
    input_schema: Dict = field(default_factory=dict)
    output_schema: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SkillResult:
    """
    Skill执行结果
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict = field(default_factory=dict)


class Skill:
    """
    Skill基类
    """
    
    metadata: SkillMetadata = None
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行Skill
        """
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_input(self, **kwargs) -> bool:
        """
        验证输入参数
        """
        if not self.metadata or not self.metadata.input_schema:
            return True
        
        required = self.metadata.input_schema.get('required', [])
        for field_name in required:
            if field_name not in kwargs:
                return False
        
        return True
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        从缓存获取
        """
        return self._cache.get(key)
    
    def cache_set(self, key: str, value: Any, ttl: int = None):
        """
        设置缓存
        """
        self._cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'ttl': ttl or OPENCLAW_CONFIG.skill.cache_ttl
        }
    
    def cache_clear(self):
        """
        清除缓存
        """
        self._cache.clear()


class SkillRegistry:
    """
    Skill注册表
    管理所有注册的技能
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
        self.config = OPENCLAW_CONFIG.skill
        
        self._skills: Dict[str, Skill] = {}
        self._skill_metadata: Dict[str, SkillMetadata] = {}
        self._skill_handlers: Dict[str, Callable] = {}
        
        self._load_builtin_skills()
    
    def _load_builtin_skills(self):
        """
        加载内置技能
        """
        skills_dir = Path(self.config.skills_dir)
        if not skills_dir.exists():
            logger.warning(f"Skills directory not found: {skills_dir}")
            return
        
        for category_dir in skills_dir.iterdir():
            if category_dir.is_dir():
                self._load_skills_from_dir(category_dir)
    
    def _load_skills_from_dir(self, category_dir: Path):
        """
        从目录加载技能
        """
        category = category_dir.name
        
        for skill_file in category_dir.glob('*.py'):
            if skill_file.name.startswith('_'):
                continue
            
            try:
                module_name = f"openclaw.skills.{category}.{skill_file.stem}"
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    skill_file
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Skill) and 
                            obj is not Skill):
                            skill_instance = obj()
                            if skill_instance.metadata:
                                skill_instance.metadata.category = category
                                self.register_skill(skill_instance)
                                
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_file}: {str(e)}")
    
    def register_skill(self, skill: Skill):
        """
        注册技能
        """
        if not skill.metadata:
            logger.warning(f"Skill missing metadata: {skill.__class__.__name__}")
            return
        
        name = skill.metadata.name
        self._skills[name] = skill
        self._skill_metadata[name] = skill.metadata
        
        logger.info(f"Registered skill: {name}, category: {skill.metadata.category}")
    
    def register_handler(self, name: str, handler: Callable, metadata: SkillMetadata = None):
        """
        注册技能处理器（函数式）
        """
        self._skill_handlers[name] = handler
        if metadata:
            self._skill_metadata[name] = metadata
        
        logger.info(f"Registered skill handler: {name}")
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取技能
        """
        return self._skills.get(name)
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """
        获取技能处理器
        """
        return self._skill_handlers.get(name)
    
    def get_metadata(self, name: str) -> Optional[SkillMetadata]:
        """
        获取技能元数据
        """
        return self._skill_metadata.get(name)
    
    def list_skills(
        self,
        category: str = None,
        tag: str = None
    ) -> List[SkillMetadata]:
        """
        列出技能
        """
        skills = []
        
        for name, metadata in self._skill_metadata.items():
            if category and metadata.category != category:
                continue
            if tag and tag not in metadata.tags:
                continue
            skills.append(metadata)
        
        return skills
    
    def list_categories(self) -> List[str]:
        """
        列出所有分类
        """
        categories = set()
        for metadata in self._skill_metadata.values():
            categories.add(metadata.category)
        return sorted(list(categories))
    
    async def execute_skill(
        self,
        name: str,
        **kwargs
    ) -> SkillResult:
        """
        执行技能
        """
        start_time = datetime.now()
        
        skill = self.get_skill(name)
        handler = self.get_handler(name)
        
        if not skill and not handler:
            return SkillResult(
                success=False,
                error=f"Skill not found: {name}"
            )
        
        try:
            if skill:
                if not skill.validate_input(**kwargs):
                    return SkillResult(
                        success=False,
                        error="Input validation failed"
                    )
                result = await skill.execute(**kwargs)
            else:
                if asyncio.iscoroutinefunction(handler):
                    result_data = await handler(**kwargs)
                else:
                    result_data = handler(**kwargs)
                
                result = SkillResult(success=True, data=result_data)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Skill execution failed: {name}, error: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def reload_skills(self):
        """
        重新加载技能
        """
        self._skills.clear()
        self._skill_metadata.clear()
        self._skill_handlers.clear()
        
        self._load_builtin_skills()
        logger.info("Skills reloaded")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        """
        categories = {}
        for metadata in self._skill_metadata.values():
            cat = metadata.category
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_skills': len(self._skill_metadata),
            'total_handlers': len(self._skill_handlers),
            'categories': categories
        }


skill_registry = SkillRegistry()
