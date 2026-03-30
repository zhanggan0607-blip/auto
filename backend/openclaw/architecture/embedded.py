"""
Embedded层 - 嵌入执行层
沙箱环境 + 技能执行 + 代码运行 + 外部API调用
"""
import asyncio
import json
import logging
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.constants import ExecutionStatus


logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """
    执行结果
    """
    execution_id: str
    status: ExecutionStatus
    output: str = ''
    error: str = ''
    return_value: Any = None
    execution_time: float = 0.0
    memory_used: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'execution_id': self.execution_id,
            'status': self.status.value,
            'output': self.output,
            'error': self.error,
            'return_value': self.return_value,
            'execution_time': self.execution_time,
            'memory_used': self.memory_used,
            'metadata': self.metadata
        }


@dataclass
class SandboxConfig:
    """
    沙箱配置
    """
    enabled: bool = True
    memory_limit_mb: int = 512
    cpu_limit_percent: float = 50.0
    timeout_seconds: int = 60
    max_output_size: int = 1024 * 1024
    allowed_modules: List[str] = field(default_factory=lambda: [
        'json', 'math', 're', 'datetime', 'collections', 'itertools',
        'functools', 'typing', 'copy', 'decimal', 'fractions', 'random',
        'string', 'textwrap', 'unicodedata', 'struct', 'codecs',
        'csv', 'configparser', 'io', 'os', 'sys', 'pathlib'
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        'subprocess', 'socket', 'multiprocessing', 'threading',
        'ctypes', 'pickle', 'shelve', 'marshal', 'imp'
    ])
    network_enabled: bool = False
    file_access_enabled: bool = False
    allowed_paths: List[str] = field(default_factory=list)


class SandboxManager:
    """
    沙箱管理器
    提供安全的代码执行环境
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
        
        self._executions: Dict[str, ExecutionResult] = {}
        self._config = SandboxConfig()
        self._running_processes: Dict[str, subprocess.Popen] = {}
    
    def configure(self, config: SandboxConfig):
        """
        配置沙箱
        """
        self._config = config
    
    async def execute_code(
        self,
        code: str,
        language: str = 'python',
        timeout: int = None,
        input_data: Dict = None
    ) -> ExecutionResult:
        """
        执行代码
        """
        execution_id = str(uuid.uuid4())
        
        result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING
        )
        
        self._executions[execution_id] = result
        
        start_time = time.time()
        
        try:
            if language == 'python':
                output = await self._execute_python(code, timeout, input_data)
            elif language == 'javascript':
                output = await self._execute_javascript(code, timeout, input_data)
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            result.status = ExecutionStatus.COMPLETED
            result.output = output.get('output', '')
            result.return_value = output.get('return_value')
            result.error = output.get('error', '')
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Execution timeout after {timeout or self._config.timeout_seconds}s"
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            
        finally:
            result.execution_time = time.time() - start_time
        
        return result
    
    async def _execute_python(
        self,
        code: str,
        timeout: int = None,
        input_data: Dict = None
    ) -> Dict:
        """
        执行Python代码
        """
        timeout = timeout or self._config.timeout_seconds
        
        wrapped_code = self._wrap_python_code(code, input_data)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=self._config.max_output_size
            )
            
            self._running_processes[temp_file] = process
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise
            
            output = stdout.decode('utf-8', errors='replace')
            error = stderr.decode('utf-8', errors='replace')
            
            return {
                'output': output,
                'error': error,
                'return_value': None
            }
            
        finally:
            if temp_file in self._running_processes:
                del self._running_processes[temp_file]
            Path(temp_file).unlink(missing_ok=True)
    
    def _wrap_python_code(self, code: str, input_data: Dict = None) -> str:
        """
        包装Python代码
        """
        input_json = json.dumps(input_data or {})
        
        return f'''
import json
import sys
from io import StringIO

_input_data = json.loads(\'\'\'{input_json}\'\'\')

_old_stdout = sys.stdout
_old_stderr = sys.stderr
_stdout_capture = StringIO()
_stderr_capture = StringIO()
sys.stdout = _stdout_capture
sys.stderr = _stderr_capture

_result = None
_error = None

try:
{self._indent_code(code, 4)}
except Exception as e:
    _error = str(e)

sys.stdout = _old_stdout
sys.stderr = _old_stderr

_output = {{
    'stdout': _stdout_capture.getvalue(),
    'stderr': _stderr_capture.getvalue(),
    'result': _result,
    'error': _error
}}

print(json.dumps(_output, ensure_ascii=False))
'''
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """
        缩进代码
        """
        indent = ' ' * spaces
        return '\n'.join(indent + line if line.strip() else line for line in code.split('\n'))
    
    async def _execute_javascript(
        self,
        code: str,
        timeout: int = None,
        input_data: Dict = None
    ) -> Dict:
        """
        执行JavaScript代码
        """
        timeout = timeout or self._config.timeout_seconds
        
        wrapped_code = self._wrap_javascript_code(code, input_data)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.js',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            process = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise
            
            output = stdout.decode('utf-8', errors='replace')
            error = stderr.decode('utf-8', errors='replace')
            
            return {
                'output': output,
                'error': error,
                'return_value': None
            }
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def _wrap_javascript_code(self, code: str, input_data: Dict = None) -> str:
        """
        包装JavaScript代码
        """
        input_json = json.dumps(input_data or {})
        
        return f'''
const inputData = {input_json};
let result = null;
let error = null;

try {{
{code}
}} catch (e) {{
    error = e.message;
}}

const output = {{
    result: result,
    error: error
}};

console.log(JSON.stringify(output));
'''
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        取消执行
        """
        result = self._executions.get(execution_id)
        if not result:
            return False
        
        if result.status == ExecutionStatus.RUNNING:
            result.status = ExecutionStatus.CANCELLED
            return True
        
        return False
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """
        获取执行结果
        """
        return self._executions.get(execution_id)
    
    def cleanup_old_executions(self, max_age_seconds: int = 3600):
        """
        清理旧执行记录
        """
        now = time.time()
        to_remove = []
        
        for execution_id, result in self._executions.items():
            if result.execution_time > 0:
                age = now - result.execution_time
                if age > max_age_seconds:
                    to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self._executions[execution_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old executions")


class EmbeddedExecutor:
    """
    嵌入执行器
    执行技能、调用外部API
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
        
        self.sandbox = SandboxManager()
        self._api_clients: Dict[str, Any] = {}
    
    async def execute_skill(
        self,
        skill_name: str,
        params: Dict = None
    ) -> Dict:
        """
        执行技能
        """
        from openclaw.skill_registry import skill_registry
        
        result = await skill_registry.execute_skill(skill_name, **(params or {}))
        
        return result.to_dict()
    
    async def execute_code(
        self,
        code: str,
        language: str = 'python',
        timeout: int = None
    ) -> Dict:
        """
        执行代码
        """
        result = await self.sandbox.execute_code(code, language, timeout)
        return result.to_dict()
    
    async def call_api(
        self,
        api_name: str,
        method: str,
        endpoint: str,
        data: Dict = None,
        headers: Dict = None,
        timeout: int = 30
    ) -> Dict:
        """
        调用外部API
        """
        import requests
        
        try:
            if method.upper() == 'GET':
                response = requests.get(
                    endpoint,
                    params=data,
                    headers=headers,
                    timeout=timeout
                )
            elif method.upper() == 'POST':
                response = requests.post(
                    endpoint,
                    json=data,
                    headers=headers,
                    timeout=timeout
                )
            elif method.upper() == 'PUT':
                response = requests.put(
                    endpoint,
                    json=data,
                    headers=headers,
                    timeout=timeout
                )
            elif method.upper() == 'DELETE':
                response = requests.delete(
                    endpoint,
                    headers=headers,
                    timeout=timeout
                )
            else:
                return {'error': f'Unsupported method: {method}'}
            
            return {
                'success': True,
                'status_code': response.status_code,
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
        except requests.Timeout:
            return {'error': 'Request timeout'}
        except requests.RequestException as e:
            return {'error': str(e)}
    
    async def run_crawler(
        self,
        source: str,
        config: Dict = None
    ) -> Dict:
        """
        运行爬虫
        """
        try:
            if source == 'china_gov':
                from crawler.china_gov_crawler import ChinaGovCrawler
                crawler = ChinaGovCrawler()
            elif source == 'shanghai_gov':
                from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
                crawler = ShanghaiGovCrawler()
            elif source == 'shanghai_construction':
                from crawler.shanghai_construction_crawler import ShanghaiConstructionCrawler
                crawler = ShanghaiConstructionCrawler()
            else:
                return {'error': f'Unknown crawler source: {source}'}
            
            results = crawler.crawl(**(config or {}))
            
            return {
                'success': True,
                'data': results,
                'count': len(results) if results else 0
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def generate_document(
        self,
        template_id: int,
        context: Dict
    ) -> Dict:
        """
        生成文档
        """
        try:
            from services.document_generator import DocumentGenerator
            generator = DocumentGenerator()
            
            result = generator.generate(template_id, context)
            
            return {
                'success': True,
                'document': result
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def recognize_document(
        self,
        file_path: str,
        doc_type: str = None
    ) -> Dict:
        """
        文档识别
        """
        try:
            from services.aliyun_ocr_service import AliyunOCRService
            ocr_service = AliyunOCRService()
            
            result = ocr_service.recognize(file_path, doc_type)
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def send_notification(
        self,
        channel: str,
        message: str,
        recipients: List[str] = None
    ) -> Dict:
        """
        发送通知
        """
        try:
            if channel == 'dingtalk':
                from services.dingtalk_service import DingTalkService
                service = DingTalkService()
                result = service.send_message(message)
            else:
                return {'error': f'Unknown channel: {channel}'}
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        """
        return {
            'sandbox': {
                'executions': len(self.sandbox._executions),
                'config': {
                    'memory_limit_mb': self.sandbox._config.memory_limit_mb,
                    'timeout_seconds': self.sandbox._config.timeout_seconds
                }
            },
            'api_clients': len(self._api_clients)
        }


sandbox_manager = SandboxManager()
embedded_executor = EmbeddedExecutor()
