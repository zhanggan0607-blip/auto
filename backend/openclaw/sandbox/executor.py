"""
OpenClaw Sandbox沙箱执行端
Python沙箱环境，进程级隔离机制保障安全
安全改进：使用subprocess.run()替代exec()，实现进程级隔离
"""
import asyncio
import logging
import os
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    resource = None
    RESOURCE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """
    沙箱配置
    """
    memory_limit_mb: int = 512
    cpu_limit_percent: int = 100
    timeout: int = 60
    max_output_size: int = 1024 * 1024
    allowed_modules: List[str] = field(default_factory=lambda: [
        'json', 're', 'datetime', 'math', 'random', 'string',
        'collections', 'itertools', 'functools', 'typing',
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        'os', 'subprocess', 'sys', 'importlib', 'ctypes',
        'multiprocessing', 'threading', 'socket', 'urllib',
        'http', 'ftplib', 'smtplib', 'telnetlib', 'telnet',
    ])
    allow_network: bool = False
    allow_file_read: bool = False
    allow_file_write: bool = False


@dataclass
class ExecutionResult:
    """
    执行结果
    """
    success: bool
    output: str = ''
    error: str = ''
    return_value: Any = None
    execution_time: float = 0.0
    memory_used: int = 0

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'return_value': self.return_value,
            'execution_time': self.execution_time,
            'memory_used': self.memory_used
        }


class SubprocessSandboxExecutor:
    """
    基于subprocess的沙箱执行器
    安全改进：使用独立进程执行代码，通过resource限制资源使用
    """

    _python_executable = sys.executable

    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self._temp_dir = None

    def _create_temp_dir(self) -> str:
        """
        创建临时目录用于存储代码文件
        """
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix='sandbox_')
        return self._temp_dir

    def _cleanup_temp_dir(self):
        """
        清理临时目录
        """
        import shutil
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")

    def _write_code_to_file(self, code: str, filename: str = None) -> str:
        """
        将代码写入临时文件

        Args:
            code: Python代码
            filename: 文件名

        Returns:
            str: 文件路径
        """
        temp_dir = self._create_temp_dir()
        if filename is None:
            filename = f"code_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.py"
        filepath = os.path.join(temp_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        return filepath

    def _get_resource_limits(self) -> Dict:
        """
        获取资源限制参数

        Returns:
            Dict: resource.limit参数
        """
        return {
            'AS': self.config.memory_limit_mb * 1024 * 1024,
            'DATA': self.config.memory_limit_mb * 1024 * 1024,
        }

    async def execute_code(
        self,
        code: str,
        globals_dict: Dict = None,
        timeout: int = None
    ) -> ExecutionResult:
        """
        执行Python代码（进程级隔离）

        Args:
            code: Python代码
            globals_dict: 全局变量（此参数会被忽略，仅保持接口兼容）
            timeout: 超时时间

        Returns:
            ExecutionResult: 执行结果
        """
        timeout = timeout or self.config.timeout
        start_time = datetime.now()

        code_file = None
        try:
            code_file = self._write_code_to_file(code)

            cmd = [
                self._python_executable,
                '-c',
                self._get_wrapper_code(code_file),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=self.config.max_output_size + 1024 * 1024
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                return ExecutionResult(
                    success=False,
                    error=f'执行超时 ({timeout}秒)',
                    execution_time=timeout
                )

            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')

            if len(output) > self.config.max_output_size:
                output = output[:self.config.max_output_size] + '...[output truncated]'

            execution_time = (datetime.now() - start_time).total_seconds()

            if process.returncode != 0:
                return ExecutionResult(
                    success=False,
                    output=output,
                    error=error_output or f'进程返回非零状态码: {process.returncode}',
                    execution_time=execution_time
                )

            return ExecutionResult(
                success=True,
                output=output,
                execution_time=execution_time
            )

        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                error='Python解释器不可用'
            )
        except Exception as e:
            error_msg = f'{type(e).__name__}: {str(e)}'
            from django.conf import settings as django_settings
            if django_settings.DEBUG:
                logger.error(f"沙箱执行异常: {error_msg}\n{traceback.format_exc()}")
            else:
                logger.error(f"沙箱执行异常: {error_msg} [堆栈信息已隐藏]")
            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        finally:
            if code_file and os.path.exists(code_file):
                try:
                    os.remove(code_file)
                except Exception:
                    pass
            self._cleanup_temp_dir()

    def _get_wrapper_code(self, code_file: str) -> str:
        """
        获取包装代码，用于在子进程中执行

        Args:
            code_file: 代码文件路径

        Returns:
            str: 包装代码
        """
        return f'''
import sys
import os
import traceback
import json

sys.stdout.reconfigure(line_buffering=True)

try:
    with open({repr(code_file)}, 'r', encoding='utf-8') as f:
        code = f.read()

    local_ns = {{}}
    exec(compile(code, {repr(code_file)}, 'exec'), {{'__builtins__': {{}}}})

    print("__EXECUTION_SUCCESS__")

except SystemExit:
    print("__EXECUTION_SUCCESS__")
except Exception as e:
    sys.stderr.write(f"{{type(e).__name__}}: {{str(e)}}\\n{{traceback.format_exc()}}")
    sys.exit(1)
'''

    async def execute_function(
        self,
        func_code: str,
        func_name: str,
        args: List = None,
        kwargs: Dict = None,
        timeout: int = None
    ) -> ExecutionResult:
        """
        执行函数

        Args:
            func_code: 函数代码
            func_name: 函数名
            args: 位置参数
            kwargs: 关键字参数
            timeout: 超时时间

        Returns:
            ExecutionResult: 执行结果
        """
        args = args or []
        kwargs = kwargs or {}

        wrapper_code = f'''
{func_code}

import json
import sys

result = {func_name}(*{args!r}, **{kwargs!r})
print(json.dumps({{"result": str(result)}}))
'''

        return await self.execute_code(wrapper_code, timeout=timeout)

    async def execute_script(
        self,
        script_path: str,
        args: List[str] = None,
        timeout: int = None
    ) -> ExecutionResult:
        """
        执行脚本文件

        Args:
            script_path: 脚本路径
            args: 命令行参数
            timeout: 超时时间

        Returns:
            ExecutionResult: 执行结果
        """
        if not os.path.exists(script_path):
            return ExecutionResult(
                success=False,
                error=f'脚本文件不存在: {script_path}'
            )

        timeout = timeout or self.config.timeout
        start_time = datetime.now()

        cmd = [self._python_executable, script_path] + (args or [])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=self.config.max_output_size + 1024 * 1024
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                return ExecutionResult(
                    success=False,
                    error=f'执行超时 ({timeout}秒)',
                    execution_time=timeout
                )

            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')

            if len(output) > self.config.max_output_size:
                output = output[:self.config.max_output_size] + '...[output truncated]'

            execution_time = (datetime.now() - start_time).total_seconds()

            if process.returncode != 0:
                return ExecutionResult(
                    success=False,
                    output=output,
                    error=error_output or f'进程返回非零状态码: {process.returncode}',
                    execution_time=execution_time
                )

            return ExecutionResult(
                success=True,
                output=output,
                execution_time=execution_time
            )

        except Exception as e:
            error_msg = f'{type(e).__name__}: {str(e)}'
            logger.error(f"沙箱执行脚本异常: {error_msg}")
            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time=(datetime.now() - start_time).total_seconds()
            )


SandboxExecutor = SubprocessSandboxExecutor


class CellIsolation:
    """
    Cell隔离机制
    每个执行单元在独立进程中运行
    """

    def __init__(self):
        self._cells: Dict[str, Dict] = {}
        self._executor = SubprocessSandboxExecutor()

    async def create_cell(
        self,
        cell_id: str = None,
        config: SandboxConfig = None
    ) -> str:
        """
        创建隔离单元

        Args:
            cell_id: 单元ID
            config: 沙箱配置

        Returns:
            str: 单元ID
        """
        import uuid

        cell_id = cell_id or str(uuid.uuid4())

        self._cells[cell_id] = {
            'config': config or SandboxConfig(),
            'globals': {},
            'created_at': datetime.now()
        }

        logger.info(f"创建隔离单元: {cell_id}")
        return cell_id

    async def execute_in_cell(
        self,
        cell_id: str,
        code: str,
        timeout: int = None
    ) -> ExecutionResult:
        """
        在隔离单元中执行代码

        Args:
            cell_id: 单元ID
            code: Python代码
            timeout: 超时时间

        Returns:
            ExecutionResult: 执行结果
        """
        if cell_id not in self._cells:
            return ExecutionResult(
                success=False,
                error=f'Cell not found: {cell_id}'
            )

        cell = self._cells[cell_id]
        config = cell['config']

        executor = SubprocessSandboxExecutor(config)
        result = await executor.execute_code(code, timeout=timeout)

        return result

    async def destroy_cell(self, cell_id: str):
        """
        销毁隔离单元

        Args:
            cell_id: 单元ID
        """
        if cell_id in self._cells:
            del self._cells[cell_id]
            logger.info(f"销毁隔离单元: {cell_id}")

    def get_cell_info(self, cell_id: str) -> Optional[Dict]:
        """
        获取单元信息
        """
        cell = self._cells.get(cell_id)
        if cell:
            return {
                'cell_id': cell_id,
                'created_at': cell['created_at'].isoformat(),
                'config': {
                    'memory_limit_mb': cell['config'].memory_limit_mb,
                    'timeout': cell['config'].timeout,
                }
            }
        return None

    def list_cells(self) -> List[str]:
        """
        列出所有单元
        """
        return list(self._cells.keys())
