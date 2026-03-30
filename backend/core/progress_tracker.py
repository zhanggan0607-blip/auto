"""
进度追踪模块
提供任务进度管理、手动结束机制
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    进度追踪器
    支持实时进度更新、手动结束机制
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._subscribers: Dict[str, list] = {}

    def create_task(
        self,
        task_id: str,
        task_name: str,
        total_steps: int = 100,
        description: str = "",
        steps: list = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建新任务进度追踪

        Args:
            task_id: 任务唯一标识
            task_name: 任务名称
            total_steps: 总步骤数
            description: 任务描述
            steps: 步骤详情列表，每个步骤包含 title, description, progress

        Returns:
            任务信息字典
        """
        with self._lock:
            step_list = []
            if steps:
                for i, step in enumerate(steps):
                    step_list.append({
                        'index': i,
                        'title': step.get('title', f'步骤 {i+1}'),
                        'description': step.get('description', ''),
                        'progress': step.get('progress', 0),
                        'status': 'waiting',
                        'started_at': None,
                        'finished_at': None,
                        'elapsed_seconds': None,
                        'error': None
                    })

            self._tasks[task_id] = {
                'task_id': task_id,
                'task_name': task_name,
                'description': description,
                'total_steps': total_steps,
                'current_step': 0,
                'progress': 0.0,
                'status': 'pending',
                'created_at': timezone.now(),
                'updated_at': timezone.now(),
                'started_at': None,
                'finished_at': None,
                'can_manually_end': True,
                'is_manually_ended': False,
                'result': None,
                'error': None,
                'steps': step_list,
                'metadata': kwargs
            }
            logger.info(f"创建进度任务: {task_id} - {task_name}")
            return self._tasks[task_id]

    def start_task(self, task_id: str) -> bool:
        """
        开始任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            if task['status'] == 'running':
                logger.warning(f"任务已在运行: {task_id}")
                return False

            task['status'] = 'running'
            task['started_at'] = timezone.now()
            task['updated_at'] = timezone.now()
            self._notify_subscribers(task_id, task)
            logger.info(f"任务已开始: {task_id}")
            return True

    def update_progress(
        self,
        task_id: str,
        current_step: int,
        progress: float = None,
        message: str = "",
        step_status: str = None,
        step_error: str = None,
        **kwargs
    ) -> bool:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            current_step: 当前步骤
            progress: 进度百分比 (0-100)
            message: 进度消息
            step_status: 步骤状态 (active/completed/error/waiting)
            step_error: 步骤错误信息
            **kwargs: 其他元数据

        Returns:
            是否成功
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            if task['status'] in ['completed', 'failed', 'cancelled']:
                logger.warning(f"任务已结束，无法更新: {task_id}, status={task['status']}")
                return False

            task['current_step'] = current_step
            if progress is not None:
                task['progress'] = min(100, max(0, progress))
            else:
                task['progress'] = (current_step / task['total_steps']) * 100 if task['total_steps'] > 0 else 0

            task['updated_at'] = timezone.now()
            if 'message' in kwargs or message:
                task['message'] = message or kwargs.get('message', '')

            if task['steps'] and len(task['steps']) > 0:
                step_index = current_step - 1
                for i, step in enumerate(task['steps']):
                    if i < step_index:
                        step['status'] = 'completed'
                        if step['started_at'] and not step['finished_at']:
                            step['finished_at'] = timezone.now()
                            if step['started_at']:
                                step['elapsed_seconds'] = (step['finished_at'] - step['started_at']).total_seconds()
                    elif i == step_index:
                        step['status'] = step_status or 'active'
                        if not step['started_at']:
                            step['started_at'] = timezone.now()
                        if progress is not None:
                            step['progress'] = progress
                        if message:
                            step['description'] = message
                        if step_error:
                            step['error'] = step_error
                    else:
                        if step['status'] == 'waiting':
                            step['status'] = 'waiting'

            for key, value in kwargs.items():
                if key not in ['message']:
                    task['metadata'][key] = value

            self._notify_subscribers(task_id, task)
            return True

    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """
        完成任务

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            是否成功
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            task['status'] = 'completed'
            task['progress'] = 100
            task['current_step'] = task['total_steps']
            task['finished_at'] = timezone.now()
            task['updated_at'] = timezone.now()
            task['result'] = result

            if task['steps']:
                for step in task['steps']:
                    if step['status'] != 'completed':
                        step['status'] = 'completed'
                    if not step['finished_at']:
                        step['finished_at'] = timezone.now()
                    if step['started_at'] and not step.get('elapsed_seconds'):
                        step['elapsed_seconds'] = (step['finished_at'] - step['started_at']).total_seconds()

            self._notify_subscribers(task_id, task)
            logger.info(f"任务已完成: {task_id}")
            return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """
        标记任务失败

        Args:
            task_id: 任务ID
            error: 错误信息

        Returns:
            是否成功
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            task['status'] = 'failed'
            task['error'] = error
            task['finished_at'] = timezone.now()
            task['updated_at'] = timezone.now()

            if task['steps']:
                for step in task['steps']:
                    if step['status'] == 'active':
                        step['status'] = 'error'
                        step['error'] = error
                        step['finished_at'] = timezone.now()
                        if step['started_at']:
                            step['elapsed_seconds'] = (step['finished_at'] - step['started_at']).total_seconds()

            self._notify_subscribers(task_id, task)
            logger.error(f"任务失败: {task_id} - {error}")
            return True

    def manually_end_task(self, task_id: str, result: Any = None) -> bool:
        """
        手动结束任务（用户点击"完成"按钮）

        Args:
            task_id: 任务ID
            result: 最终结果

        Returns:
            是否成功
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            if not task['can_manually_end']:
                logger.warning(f"任务不允许手动结束: {task_id}")
                return False

            if task['is_manually_ended']:
                logger.warning(f"任务已被手动结束: {task_id}")
                return False

            task['status'] = 'manually_ended'
            task['is_manually_ended'] = True
            task['finished_at'] = timezone.now()
            task['updated_at'] = timezone.now()
            task['result'] = result
            self._notify_subscribers(task_id, task)
            logger.info(f"任务已被手动结束: {task_id}")
            return True

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False

            task = self._tasks[task_id]
            task['status'] = 'cancelled'
            task['finished_at'] = timezone.now()
            task['updated_at'] = timezone.now()
            self._notify_subscribers(task_id, task)
            logger.info(f"任务已取消: {task_id}")
            return True

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，不存在则返回None
        """
        with self._lock:
            if task_id not in self._tasks:
                return None
            return self._tasks[task_id].copy()

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有任务状态

        Returns:
            所有任务信息
        """
        with self._lock:
            return {k: v.copy() for k, v in self._tasks.items()}

    def subscribe(self, task_id: str, callback: Callable) -> None:
        """
        订阅任务更新

        Args:
            task_id: 任务ID
            callback: 回调函数，接收任务状态
        """
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(callback)

    def _notify_subscribers(self, task_id: str, task: Dict[str, Any]) -> None:
        """
        通知订阅者
        """
        if task_id in self._subscribers:
            for callback in self._subscribers[task_id]:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"通知订阅者失败: {e}")

    def remove_task(self, task_id: str) -> bool:
        """
        移除任务（清理）

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
            if task_id in self._subscribers:
                del self._subscribers[task_id]
            logger.info(f"任务已移除: {task_id}")
            return True


progress_tracker = ProgressTracker()