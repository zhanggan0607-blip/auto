"""
OpenClaw Agent引擎模块

目录结构：
openclaw/
├── base_agent.py           # Agent基类
├── agents/                 # Agent实现
│   ├── professional_agents.py  # 专业Agent
│   ├── bid_collector_agent.py
│   ├── bid_document_agents.py
│   ├── bid_tracker_agents.py
│   └── bid_workflow_orchestrator.py
├── skills/                 # 技能实现
│   ├── collector/
│   ├── generator/
│   ├── parser/
│   └── uploader/
├── ai_extractors/          # AI提取器
└── messaging/              # 消息协议

注意：
- Django模型在 apps/openclaw/ 目录
- 此目录只包含Agent引擎实现代码
- LLM服务请使用 services.unified_llm_service.UnifiedLLMService
"""
