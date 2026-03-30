"""
业务服务层模块

职责：
- 跨应用的业务逻辑封装
- 外部服务集成
- 数据处理和转换服务

服务目录结构：
services/
├── llm/                    # LLM服务
│   ├── __init__.py
│   ├── unified_llm_service.py
│   └── adapters.py
├── vector/                 # 向量服务
│   ├── __init__.py
│   ├── chroma_client.py
│   ├── embedding.py
│   ├── enterprise_store.py
│   ├── document_store.py
│   └── transaction.py
└── *.py                   # 其他业务服务

使用示例：
```python
# LLM服务
from services.llm import UnifiedLLMService
llm_service = UnifiedLLMService()

# 向量服务
from services.vector import enterprise_vector_store, document_vector_store

# 通知服务
from services.dingtalk_service import DingTalkService
```

设计原则：
1. 单一职责：每个服务只负责一个业务领域
2. 依赖注入：服务间通过参数传递依赖
3. 异步优先：耗时操作使用async/await
4. 错误处理：统一异常处理和日志记录
"""

from .llm import UnifiedLLMService, unified_llm_service
from .vector import (
    chroma_client,
    embedding_service,
    enterprise_vector_store,
    document_vector_store,
)

__all__ = [
    'UnifiedLLMService',
    'unified_llm_service',
    'chroma_client',
    'embedding_service',
    'enterprise_vector_store',
    'document_vector_store',
]