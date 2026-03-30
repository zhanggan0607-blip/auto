"""
Sandbox模块初始化
"""
from .executor import SandboxExecutor, SandboxConfig, ExecutionResult, CellIsolation

__all__ = ['SandboxExecutor', 'SandboxConfig', 'ExecutionResult', 'CellIsolation']

sandbox_executor = SandboxExecutor()
cell_isolation = CellIsolation()
