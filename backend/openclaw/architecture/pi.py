"""
Pi层 - 业务处理层
Agent管理 + 工作流编排 + 技能注册 + 记忆系统 + 工具箱
"""
import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from core.constants import WorkflowStatus, StageStatus


logger = logging.getLogger(__name__)


@dataclass
class WorkflowStage:
    """
    工作流阶段
    """
    stage_id: str
    stage_name: str
    stage_type: str
    agent_type: str
    status: StageStatus = StageStatus.PENDING
    order: int = 0
    input_data: Dict = field(default_factory=dict)
    output_data: Dict = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def start(self):
        self.status = StageStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self, output_data: Dict = None):
        self.status = StageStatus.COMPLETED
        self.completed_at = datetime.now()
        if output_data:
            self.output_data = output_data
    
    def fail(self, error: str):
        self.status = StageStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()
    
    def skip(self):
        self.status = StageStatus.SKIPPED
        self.completed_at = datetime.now()


@dataclass
class WorkflowContext:
    """
    工作流上下文
    """
    workflow_id: str
    session_id: str
    user_id: Optional[int] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_stage: int = 0
    stages: List[WorkflowStage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def get_current_stage(self) -> Optional[WorkflowStage]:
        if 0 <= self.current_stage < len(self.stages):
            return self.stages[self.current_stage]
        return None
    
    def advance_stage(self) -> bool:
        self.current_stage += 1
        return self.current_stage < len(self.stages)
    
    def to_dict(self) -> Dict:
        return {
            'workflow_id': self.workflow_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'status': self.status.value,
            'current_stage': self.current_stage,
            'total_stages': len(self.stages),
            'context': self.context,
            'errors': self.errors,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class WorkflowDefinition(ABC):
    """
    工作流定义基类
    """
    
    name: str = ''
    description: str = ''
    version: str = '1.0.0'
    
    @abstractmethod
    def get_stages(self) -> List[Dict]:
        """
        获取阶段定义
        """
        pass
    
    @abstractmethod
    async def execute_stage(self, stage: WorkflowStage, context: WorkflowContext) -> Dict:
        """
        执行阶段
        """
        pass
    
    def should_continue(self, stage_result: Dict, context: WorkflowContext) -> bool:
        """
        判断是否继续执行下一阶段
        """
        return stage_result.get('continue', True)


class AgentOrchestrator:
    """
    Agent编排器
    负责多Agent协作和工作流管理
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
        
        self._workflows: Dict[str, WorkflowContext] = {}
        self._workflow_definitions: Dict[str, Type[WorkflowDefinition]] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def register_workflow(self, workflow_class: Type[WorkflowDefinition]):
        """
        注册工作流定义
        """
        if not workflow_class.name:
            raise ValueError("Workflow must have a name")
        
        self._workflow_definitions[workflow_class.name] = workflow_class
        logger.info(f"Registered workflow: {workflow_class.name}")
    
    def get_workflow_definition(self, name: str) -> Optional[Type[WorkflowDefinition]]:
        """
        获取工作流定义
        """
        return self._workflow_definitions.get(name)
    
    async def create_workflow(
        self,
        workflow_name: str,
        user_id: int = None,
        initial_context: Dict = None
    ) -> WorkflowContext:
        """
        创建工作流实例
        """
        definition_class = self.get_workflow_definition(workflow_name)
        if not definition_class:
            raise ValueError(f"Workflow not found: {workflow_name}")
        
        workflow_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        definition = definition_class()
        stage_definitions = definition.get_stages()
        
        stages = []
        for i, stage_def in enumerate(stage_definitions):
            stage = WorkflowStage(
                stage_id=str(uuid.uuid4()),
                stage_name=stage_def.get('name', f'Stage {i+1}'),
                stage_type=stage_def.get('type', 'default'),
                agent_type=stage_def.get('agent_type', 'orchestrator'),
                order=i,
                input_data=stage_def.get('input', {})
            )
            stages.append(stage)
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            session_id=session_id,
            user_id=user_id,
            stages=stages,
            context=initial_context or {}
        )
        
        self._workflows[workflow_id] = context
        
        return context
    
    async def start_workflow(self, workflow_id: str) -> Dict:
        """
        启动工作流
        """
        context = self._workflows.get(workflow_id)
        if not context:
            return {'error': f'Workflow not found: {workflow_id}'}
        
        if context.status != WorkflowStatus.PENDING:
            return {'error': f'Workflow already started: {context.status.value}'}
        
        context.status = WorkflowStatus.RUNNING
        context.started_at = datetime.now()
        
        task = asyncio.create_task(self._run_workflow(workflow_id))
        self._running_tasks[workflow_id] = task
        
        return {
            'workflow_id': workflow_id,
            'status': 'started',
            'total_stages': len(context.stages)
        }
    
    async def _run_workflow(self, workflow_id: str):
        """
        运行工作流
        """
        context = self._workflows.get(workflow_id)
        if not context:
            return
        
        definition_class = self.get_workflow_definition(
            context.context.get('workflow_name', '')
        )
        if not definition_class:
            context.status = WorkflowStatus.FAILED
            context.errors.append('Workflow definition not found')
            return
        
        definition = definition_class()
        
        try:
            for stage in context.stages:
                current = context.get_current_stage()
                if not current or current.stage_id != stage.stage_id:
                    continue
                
                stage.start()
                logger.info(f"Workflow {workflow_id} executing stage: {stage.stage_name}")
                
                try:
                    result = await definition.execute_stage(stage, context)
                    
                    if result.get('success', True):
                        stage.complete(result.get('data'))
                        
                        if not definition.should_continue(result, context):
                            logger.info(f"Workflow {workflow_id} stopped at stage: {stage.stage_name}")
                            break
                        
                        context.advance_stage()
                    else:
                        stage.fail(result.get('error', 'Unknown error'))
                        context.errors.append(f"{stage.stage_name}: {stage.error}")
                        
                        if not stage.input_data.get('optional', False):
                            context.status = WorkflowStatus.FAILED
                            break
                        else:
                            stage.skip()
                            context.advance_stage()
                            
                except Exception as e:
                    stage.fail(str(e))
                    context.errors.append(f"{stage.stage_name}: {str(e)}")
                    context.status = WorkflowStatus.FAILED
                    break
            
            if context.status == WorkflowStatus.RUNNING:
                context.status = WorkflowStatus.COMPLETED
            
            context.completed_at = datetime.now()
            
            await self._save_workflow_result(context)
            
        except Exception as e:
            context.status = WorkflowStatus.FAILED
            context.errors.append(str(e))
            context.completed_at = datetime.now()
        
        finally:
            if workflow_id in self._running_tasks:
                del self._running_tasks[workflow_id]
    
    async def _save_workflow_result(self, context: WorkflowContext):
        """
        保存工作流结果
        """
        try:
            from apps.openclaw.workflow_models import BidWorkflow
            
            workflow = BidWorkflow.objects.filter(
                session_id=context.session_id
            ).first()
            
            if workflow:
                workflow.status = context.status.value
                workflow.current_stage = context.stages[context.current_stage].stage_type if context.current_stage < len(context.stages) else 'completed'
                workflow.context = context.context
                workflow.result_summary = json.dumps(context.results, ensure_ascii=False)
                
                if context.status == WorkflowStatus.COMPLETED:
                    workflow.completed_at = datetime.now()
                elif context.started_at:
                    workflow.started_at = context.started_at
                
                workflow.save()
                
        except Exception as e:
            logger.error(f"Failed to save workflow result: {str(e)}")
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """
        获取工作流状态
        """
        context = self._workflows.get(workflow_id)
        if context:
            return context.to_dict()
        return None
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        取消工作流
        """
        context = self._workflows.get(workflow_id)
        if not context:
            return False
        
        if workflow_id in self._running_tasks:
            task = self._running_tasks[workflow_id]
            task.cancel()
            del self._running_tasks[workflow_id]
        
        context.status = WorkflowStatus.CANCELLED
        context.completed_at = datetime.now()
        
        return True
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """
        暂停工作流
        """
        context = self._workflows.get(workflow_id)
        if not context or context.status != WorkflowStatus.RUNNING:
            return False
        
        context.status = WorkflowStatus.PAUSED
        return True
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """
        恢复工作流
        """
        context = self._workflows.get(workflow_id)
        if not context or context.status != WorkflowStatus.PAUSED:
            return False
        
        context.status = WorkflowStatus.RUNNING
        
        task = asyncio.create_task(self._run_workflow(workflow_id))
        self._running_tasks[workflow_id] = task
        
        return True
    
    def list_workflows(
        self,
        user_id: int = None,
        status: WorkflowStatus = None
    ) -> List[Dict]:
        """
        列出工作流
        """
        workflows = []
        
        for context in self._workflows.values():
            if user_id and context.user_id != user_id:
                continue
            if status and context.status != status:
                continue
            workflows.append(context.to_dict())
        
        return workflows


class PiLayerManager:
    """
    Pi层管理器
    整合Agent管理、工作流编排、技能注册
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
        
        self.orchestrator = AgentOrchestrator()
        
        self._memory_store: Dict[str, Dict] = {}
        self._tool_registry: Dict[str, Callable] = {}
        
        self._register_default_tools()
    
    def _register_default_tools(self):
        """
        注册默认工具
        """
        self.register_tool('http_get', self._tool_http_get)
        self.register_tool('http_post', self._tool_http_post)
        self.register_tool('read_file', self._tool_read_file)
        self.register_tool('write_file', self._tool_write_file)
        self.register_tool('execute_code', self._tool_execute_code)
    
    def register_tool(self, name: str, handler: Callable):
        """
        注册工具
        """
        self._tool_registry[name] = handler
        logger.info(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """
        获取工具
        """
        return self._tool_registry.get(name)
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """
        执行工具
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        return tool(**kwargs)
    
    async def _tool_http_get(self, url: str, headers: Dict = None, timeout: int = 30) -> Dict:
        """
        HTTP GET工具
        """
        import requests
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            return {
                'success': True,
                'status_code': response.status_code,
                'content': response.text
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _tool_http_post(self, url: str, data: Dict = None, headers: Dict = None, timeout: int = 30) -> Dict:
        """
        HTTP POST工具
        """
        import requests
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
            return {
                'success': True,
                'status_code': response.status_code,
                'content': response.text
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _tool_read_file(self, path: str) -> Dict:
        """
        读取文件工具
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {'success': True, 'content': content}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _tool_write_file(self, path: str, content: str) -> Dict:
        """
        写入文件工具
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _tool_execute_code(self, code: str, language: str = 'python') -> Dict:
        """
        执行代码工具
        """
        from openclaw.architecture.embedded import embedded_executor
        
        return await embedded_executor.execute_code(code, language)
    
    def store_memory(self, agent_id: str, key: str, value: Any):
        """
        存储Agent记忆
        """
        if agent_id not in self._memory_store:
            self._memory_store[agent_id] = {}
        self._memory_store[agent_id][key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_memory(self, agent_id: str, key: str = None) -> Any:
        """
        获取Agent记忆
        """
        agent_memory = self._memory_store.get(agent_id, {})
        if key:
            return agent_memory.get(key, {}).get('value')
        return agent_memory
    
    def clear_memory(self, agent_id: str):
        """
        清除Agent记忆
        """
        if agent_id in self._memory_store:
            del self._memory_store[agent_id]
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        """
        return {
            'workflows': len(self.orchestrator._workflows),
            'running_tasks': len(self.orchestrator._running_tasks),
            'tools': len(self._tool_registry),
            'memory_entries': sum(len(m) for m in self._memory_store.values())
        }


pi_layer_manager = PiLayerManager()
agent_orchestrator = AgentOrchestrator()
