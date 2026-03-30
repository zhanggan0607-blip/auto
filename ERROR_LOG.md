# 项目错误记录与功能更新文档

> 本文档用于记录项目中遇到的所有错误和问题，以及功能更新记录，避免重复出现相同问题。
> 每次操作前请先查阅本文档，确保不犯同样的错误。

---

## 错误记录索引

| 编号 | 错误类型 | 简要描述 | 状态 | 日期 |
|------|----------|----------|------|------|
| E001 | 数据库迁移 | 500错误 - 模型字段tech_manager_name未迁移 | 已解决 | 2025-03-19 |
| E002 | 类型错误 | TypeError: unsupported operand type(s) for +: 'int' and 'str' | 已解决 | 2025-03-17 |
| E003 | 配置错误 | NoReverseMatch: 'djdt' is not a registered namespace | 已解决 | 2025-03-17 |
| E004 | Redis连接 | TypeError: AbstractConnection.__init__() unexpected keyword 'CLIENT_CLASS' | 已解决 | 2025-03-17 |
| E005 | 数据库迁移 | ProgrammingError: 表token_blacklist_outstandingtoken不存在 | 已解决 | 2025-03-17 |
| E006 | 数据库迁移 | UndefinedColumn: 字段qualification_types不存在 | 已解决 | 2025-03-18 |
| E007 | 认证错误 | Token验证失败 - token_not_valid | 已解决 | 2025-03-17 |
| E008 | 前端数据格式 | ElTable data属性期望数组但收到对象 | 已解决 | 2026-03-19 |
| E009 | 序列化器错误 | IPAddressField导致ValueError | 已解决 | 2026-03-19 |
| E010 | 导入错误 | admin.py导入不存在的模型类 | 已解决 | 2026-03-20 |
| E011 | 语法错误 | f-string中不能使用反斜杠 | 已解决 | 2026-03-20 |
| E012 | 模块依赖 | 缺少openai/sentence_transformers/chromadb模块 | 已解决 | 2026-03-20 |
| E013 | 数据库迁移 | 新增字段缺少默认值 | 已解决 | 2026-03-20 |
| E014 | 前端运行时 | ResizeObserver loop completed错误 | 已解决 | 2026-03-20 |
| E015 | 前端组件 | ElOption value属性为undefined | 已解决 | 2026-03-20 |
| E016 | 模型废弃 | CompanyInfo模型已废弃，使用Enterprise替代 | 已解决 | 2026-03-20 |
| E017 | LLM服务 | openclaw.llm_service已废弃，使用UnifiedLLMService | 已解决 | 2026-03-20 |
| E018 | 缓存配置 | 缓存从LocMemCache迁移到Redis | 已解决 | 2026-03-20 |
| E019 | 分页错误 | AttributeError: 'StandardPagination' object has no attribute 'count' | 已解决 | 2026-03-20 |
| E020 | API路径错误 | 前端API缺少v1前缀导致404错误 | 已解决 | 2026-03-20 |
| E021 | Django启动 | AppRegistryNotReady: Apps aren't loaded yet | 已解决 | 2026-03-20 |
| E022 | 图标注册 | Element Plus图标组件未正确注册 | 已解决 | 2026-03-20 |
| E023 | 架构重构 | API管理渐进式三层架构重构 | 已完成 | 2026-03-20 |
| E024 | 前后端不一致 | 企业类型定义不一致导致400错误 | 已解决 | 2026-03-20 |
| E025 | 前端逻辑 | 编辑企业保存后未正确刷新选中项 | 已解决 | 2026-03-20 |
| E026 | 异步上下文 | Django ORM在异步上下文中调用错误 | 已解决 | 2026-03-20 |
| E027 | SSL证书验证 | 企业信息采集SSL证书验证失败 | 已解决 | 2026-03-20 |
| E028 | 认证错误 | 401 Unauthorized - Token过期未自动刷新 | 已解决 | 2026-03-21 |
| E029 | 前端组件 | Element Plus图标组件未导入 | 已解决 | 2026-03-21 |
| E030 | 后端模型 | 模型choices属性引用错误 | 已解决 | 2026-03-21 |
| E031 | 前端图标 | Element Plus不存在的Scan图标 | 已解决 | 2026-03-21 |
| E032 | 前后端不一致 | 企业类型选项与后端定义不匹配 | 已解决 | 2026-03-21 |
| E033 | 前端数据格式 | 数字字段空字符串导致400错误 | 已解决 | 2026-03-21 |
| E034 | 字段移除 | 企业信息移除6个冗余字段 | 已完成 | 2026-03-22 |
| E035 | 序列化器字段 | 序列化器引用模型中不存在的short_name/industry字段 | 已解决 | 2026-03-22 |
| E036 | 前端样式 | el-descriptions标签换行和宽度不一致 | 已解决 | 2026-03-22 |
| E037 | 代码重复 | VECTOR_STATUS_CHOICES重复定义 | 已解决 | 2026-03-22 |
| E038 | 代码重复 | Agent类重复定义 | 已解决 | 2026-03-22 |
| E039 | 未使用代码 | repositories.py等文件未被调用 | 已解决 | 2026-03-22 |
| E040 | 代码分散 | 状态枚举定义分散在多个文件 | 已解决 | 2026-03-22 |
| E041 | 安全漏洞 | 爬虫执行接口缺少权限控制 | 已解决 | 2026-03-22 |
| E042 | 性能问题 | N+1查询问题导致性能下降 | 已解决 | 2026-03-22 |
| E043 | DevOps配置 | 缺少健康检查端点和nginx配置 | 已解决 | 2026-03-22 |
| E044 | API完整性 | 投标记录缺少删除接口 | 已解决 | 2026-03-22 |
| E045 | 频率限制 | 企业采集接口缺少频率限制 | 已解决 | 2026-03-22 |
| E046 | 认证错误 | Token刷新请求体为空导致401 | 已解决 | 2026-03-22 |
| E047 | API方法缺失 | enterpriseApi缺少getQualifications/getPerformances方法 | 已解决 | 2026-03-22 |
| E048 | AI搜索失败 | AI全网搜索失败-未配置LLM提供商 | 已解决 | 2026-03-22 |
| E049 | 异步视图 | Django REST Framework不支持async视图方法 | 已解决 | 2026-03-22 |
| E050 | 前端组件 | Element Plus Input组件收到数组值导致警告 | 已解决 | 2026-03-22 |
| E051 | 认证错误 | 401 Unauthorized错误排查 | 已解决 | 2026-03-23 |
| E052 | 前端缓存 | Sass导入路径缓存导致编译失败 | 已解决 | 2026-03-23 |
| E053 | 端口配置 | 前端端口不固定自动切换 | 已解决 | 2026-03-23 |
| E054 | 服务阻塞 | EmbeddingService初始化阻塞服务启动 | 已解决 | 2026-03-23 |
| E055 | 配置兼容 | webpack-dev-server不支持strictPort | 已解决 | 2026-03-23 |
| E056 | 认证错误 | AllowAny视图无效Token导致401 | 已解决 | 2026-03-23 |
| E057 | 数据加密 | 银行账号双重加密导致数据不一致 | 已解决 | 2026-03-25 |
| E058 | 前端重构 | 页面简化 - 移除可自动处理的内容 | 已完成 | 2026-03-26 |
| E059 | 导航栏重构 | 层级化设计，隐藏非高频选项 | 已完成 | 2026-03-26 |
| E060 | 新增功能 | 自动化监控面板 AutomationMonitor | 已完成 | 2026-03-26 |
| E061 | 架构统一 | 统一API响应 UnifiedResponse 应用 | 已完成 | 2026-03-26 |
| E062 | 架构统一 | Agent消息格式 MessageRole/MessageType 枚举 | 已完成 | 2026-03-26 |
| E063 | 前端监控 | StatusBadge组件引用不存在的导出 | 已解决 | 2026-03-26 |
| E064 | 端口配置 | 8081端口被占用导致前端切换到8082 | 已解决 | 2026-03-26 |
| E065 | 代码错误 | Celery配置缺少Celery导入 | 已解决 | 2026-03-26 |
| E066 | 模块依赖缺失 | FastAPI缺少sse-starlette依赖 | 已解决 | 2026-03-26 |
| E067 | 模块依赖缺失 | Milvus客户端pymilvus未安装(网络超时) | 已解决 | 2026-03-26 |
| E068 | 模块依赖缺失 | Scrapy-Redis网络超时无法安装 | 已解决 | 2026-03-26 |
| E069 | 前端API路径错误 | userAdmin.js路径重复/api/导致404 | 已解决 | 2026-03-26 |
| E070 | 前端数据格式 | el-table data prop期望数组但收到对象/null | 已解决 | 2026-03-26 |
| E071 | 前端API不存在 | AutomationMonitor调用不存在的后端API | 已解决 | 2026-03-26 |
| E072 | 前端API路径错误 | constants.js路径重复/api/导致404 | 已解决 | 2026-03-26 |
| E073 | 前后端字段不一致 | 中标结果录入bid_record_id字段名错误 | 已解决 | 2026-03-26 |
| E074 | 前后端字段缺失 | 投标记录team_members字段前端表单缺失 | 已解决 | 2026-03-26 |
| E075 | 前后端字段不一致 | 投标记录tender_id/bid_manager_id字段名错误 | 已解决 | 2026-03-26 |
| E076 | 前端表单缺失 | 企业扩展字段auto_bid_keywords等前端控件缺失 | 已解决 | 2026-03-26 |
| E077 | ESLint清理 | ConfirmDialog等组件未使用的import导入 | 已解决 | 2026-03-26 |
| E078 | ESLint清理 | StatCard等组件未使用的图标组件导入 | 已解决 | 2026-03-26 |
| E079 | ESLint清理 | Layout等视图未使用的vue导入和图标导入 | 已解决 | 2026-03-26 |
| E080 | ESLint清理 | useStatistics未使用的watch/cards/message | 已解决 | 2026-03-26 |
| E081 | ESLint清理 | directives/index.js未使用的createApp | 已解决 | 2026-03-26 |
| E082 | ESLint清理 | AutomationDashboard未使用的viewWorkflow函数 | 已解决 | 2026-03-26 |
| E083 | ESLint清理 | AIPlayground等文件未使用的变量/e参数 | 已解决 | 2026-03-26 |
| E084 | Vue事件处理 | checkOllamaStatus接收到[object PointerEvent]导致400错误 | 已解决 | 2026-03-26 |
| E085 | Ollama集成 | ollama_status和ollama_models接口未返回完整数据 | 已解决 | 2026-03-26 |
| E086 | 前端功能 | ModelConfig页面Ollama未自动检测和加载模型列表 | 已解决 | 2026-03-26 |
| E087 | 异步视图错误 | test_connection视图未await异步chat方法导致400错误 | 已解决 | 2026-03-26 |
| E088 | 前端localStorage key错误 | AIPlayground.vue使用错误key'access_token'导致401 | 已解决 | 2026-03-26 |
| E089 | Agent模型配置为空 | AgentModelConfig表无数据导致页面表格无数据 | 已解决 | 2026-03-26 |
| E090 | LLM模型列表为空 | LLMModel表无数据导致对话模型下拉框无选项 | 已解决 | 2026-03-26 |
| E091 | LLMProvider属性错误 | 代码使用max_context但模型只有max_tokens字段 | 已解决 | 2026-03-26 |
| E092 | LLMModelSerializer错误 | 直接序列化字典而不是ModelSerializer能处理的对象 | 已解决 | 2026-03-26 |
| E093 | 前端ElOption值错误 | model.id为null导致el-option验证失败 | 已解决 | 2026-03-26 |
| E094 | 前端API路径错误 | test_connection路径缺少provider_id导致404 | 已解决 | 2026-03-27 |
| E095 | 前端功能简化 | 移除提供商管理功能，只保留Ollama专用 | 已完成 | 2026-03-27 |
| E096 | Ollama api_key检查错误 | test_connection对Ollama类型也检查api_key导致400 | 已解决 | 2026-03-27 |
| E097 | batch_update类型错误 | chat_model_id传模型标识符但外键期望数字ID | 已解决 | 2026-03-27 |
| E098 | SystemModelsView字段错误 | 使用context_length但模型只有context_window字段 | 已解决 | 2026-03-27 |
| E099 | AgentModelConfigSerializer字段错误 | 返回chat_model数字ID但前端期望chat_model_id字符串 | 已解决 | 2026-03-27 |
| E100 | Ollama模型不存在 | Playground测试失败-数据库配置模型qwen2.5:14b在Ollama中未安装 | 已解决 | 2026-03-27 |
| E101 | 项目清理 | 审计清理未使用组件、API模块和分布式爬虫 | 已完成 | 2026-03-27 |
| E102 | 架构重构 | 爬虫模块重复类合并+依赖优化 | 已完成 | 2026-03-27 |
| E103 | 数据库连接失败500错误 | .env中DB_PASSWORD配置为CHANGE-ME-IN-PRODUCTION导致Django无法连接数据库 | 已解决 | 2026-03-27 |
| E104 | 后端服务器未运行 | 前端8081端口代理到后端8000端口但Django服务器未启动导致ECONNREFUSED | 已解决 | 2026-03-27 |
| E105 | 流式响应问题 | AI Playground流式回复一次性出来而不是逐步显示 | 已解决 | 2026-03-27 |
| E106 | httpx缓冲问题 | httpx.AsyncClient的aiter_lines()内部缓冲导致无法流式返回 | 已解决 | 2026-03-27 |
| E107 | Django流式缓冲 | StreamingHttpResponse对异步生成器有缓冲导致流式失效 | 已解决 | 2026-03-27 |
| E108 | 浏览器XHR缓冲 | XMLHttpRequest的onprogress事件不能真正流式接收SSE数据 | 已解决 | 2026-03-27 |
| E109 | 模型列表不一致 | 数据库Ollama配置5个模型但实际部署7个模型 | 已解决 | 2026-03-27 |
| E110 | 自动同步功能 | Ollama模型新增后需手动同步到数据库，已实现自动同步 | 已完成 | 2026-03-27 |
| E111 | 服务器启动时序问题 | 前端请求时后端未完全就绪导致500/CONNREFUSED | 已解决 | 2026-03-27 |
| E112 | HTTP头设置错误 | StreamingHttpResponse设置hop-by-hop头Connection导致500错误 | 已解决 | 2026-03-27 |
| E113 | 前端字段不匹配 | API返回`type`字段但前端读取`provider_type`导致模型选择失效 | 已解决 | 2026-03-27 |
| E114 | 对话框样式问题 | AI Playground对话框宽度不固定、可拖动改变大小 | 已解决 | 2026-03-27 |
| E115 | 错误诊断自动化 | 实现ErrorDiagnoser实现错误自动分类、诊断、解决方案推荐 | 已完成 | 2026-03-27 |
| E116 | 生产环境安全检查 | 生产环境DJANGO_SECRET_KEY弱密钥/短密钥导致安全风险 | 已解决 | 2026-03-27 |
| E117 | Agent消息签名缺失 | AgentRouter.route_message无签名验证导致恶意消息注入风险 | 已解决 | 2026-03-27 |
| E118 | 沙箱代码执行隔离 | SandboxExecutor使用exec()导致代码可绕过限制访问系统资源 | 已解决 | 2026-03-27 |
| E119 | 租户边界校验缺失 | IsEnterpriseOwner.has_permission返回True绕过对象级权限校验 | 已解决 | 2026-03-27 |
| E120 | 生产环境堆栈泄露 | DEBUG模式下traceback.format_exc()输出完整堆栈信息到日志 | 已解决 | 2026-03-27 |
| E121 | 代码重复清理 | 删除未使用的BidWorkflowViewSet(views.py)、清理workflow_models导入 | 已完成 | 2026-03-27 |
| E122 | 前端status.js迁移 | 将6处引用从utils/status.js迁移到store/constants | 已完成 | 2026-03-27 |
| E123 | 权限文件重复合并 | 删除有安全bug的enterprise_permissions.py，统一使用permissions/enterprise.py | 已完成 | 2026-03-27 |
| E124 | 注释代码清理 | 删除debug_toolbar相关注释代码和配置 | 已完成 | 2026-03-27 |
| E125 | 前端认证不一致 | AIPlayground streamChat使用localStorage token但应用使用Cookie认证导致401 | 已解决 | 2026-03-28 |
| E126 | 前端错误处理 | DRF ValidationError返回errors对象但前端未正确提取message导致显示[object Object] | 已解决 | 2026-03-28 |
| E127 | 模型配置页面UI | 模型列表按大小排序功能 + Ollama文本替换为投标精灵 | 已完成 | 2026-03-28 |
| E128 | 对话框UI优化 | 移除模型下拉选项中的"(投标精灵)"后缀 | 已完成 | 2026-03-28 |
| E129 | 数据库配置不一致 | 项目多处数据库配置不统一（bid_user/bid_password与实际postgres/123456不一致） | 已解决 | 2026-03-28 |
| E130 | Element Plus图标组件错误 | el-avatar的icon prop传入字符串'User'而非组件对象导致debugWarn警告 | 已解决 | 2026-03-28 |
| E131 | UserLoginLog约束错误 | 登录失败时创建UserLoginLog记录user_id为null违反非空约束导致503错误 | 已解决 | 2026-03-28 |
| E132 | 默认提供商指定 | AI Playground未自动选择默认LLM提供商，现优先使用is_default设置否则回退到Ollama | 已完成 | 2026-03-28 |
| E133 | formatDate未导入 | ScheduleList.vue使用formatDate但未导入导致$setup.formatDate is not a function错误 | 已解决 | 2026-03-28 |
| E134 | 进度API路由未注册 | 进度追踪API已实现但未在URL配置中注册导致404 | 已解决 | 2026-03-28 |
| E135 | Serializer字段缺失 | BidRecordListSerializer缺少team_member_ids字段导致编辑时无法回填团队成员 | 已解决 | 2026-03-28 |
| E136 | 前端路由逻辑错误 | ScheduleList.vue的showCreateDialog/showEditDialog跳转到不存在的路由 | 已解决 | 2026-03-28 |
| E137 | 响应格式不统一 | scheduler_views.py直接使用Response而非APIResponse导致响应格式不一致 | 已解决 | 2026-03-28 |
| E138 | 错误码不完整 | 缺少调度器相关错误码(SCHEDULE_*, QUALIFICATION_MATCH_*) | 已解决 | 2026-03-28 |
| F001 | 计划名称唯一性验证 | 实现客户端+服务端计划名称唯一性检查，防止重复提交 | 已完成 | 2026-03-28 |
| F002 | 网站模板多模式输入 | 实现选择模板、分类选择、手动输入三种网站模板输入方式 | 已完成 | 2026-03-28 |
| E139 | 前端错误处理 | 创建关键词时后端返回400唯一性错误但前端显示"保存失败"而非详细错误信息 | 已解决 | 2026-03-28 |
| F003 | 关键词选择功能 | 采集计划搜索关键词从自由输入改为从关键词管理中选择，支持多选 | 已完成 | 2026-03-28 |
| E140 | API参数双重嵌套 | crawler.js checkScheduleNameDuplicate参数被双重嵌套导致404错误 | 已解决 | 2026-03-28 |
| E141 | website_template验证错误 | CrawlScheduleCreateSerializer website_template字段必填导致400错误 | 已解决 | 2026-03-28 |
| E142 | 代理连接错误 | 前端代理ECONNREFUSED错误导致500状态码（后端未启动时的时序问题） | 已记录 | 2026-03-28 |
| E143 | BaseViewSet MRO错误 | BaseViewSet继承顺序导致Mixin的list方法未生效，API返回数组而非统一格式 | 已解决 | 2026-03-28 |
| E144 | 资质类型选项不匹配 | 前端资质类型选项值与后端ENTERPRISE_QUAL_TYPE_CHOICES不一致+日期格式问题 | 已解决 | 2026-03-28 |
| E145 | filterset_fields字段错误 | EnterpriseQualificationViewSet filterset_fields使用qualification_type但模型字段是qualification_category导致500 | 已解决 | 2026-03-28 |
| E146 | 资质名称值不在choices中 | 前端发送building_construction但QUALIFICATION_NAME_CHOICES中不存在该值，只有construction_general_building等 | 已解决 | 2026-03-28 |
| E147 | 模型连接自动重连 | 实现自动模型连接功能，包含登录后自动连接、状态检测、指数退避重连 | 已完成 | 2026-03-28 |
| E148 | onUnmounted警告 | Layout.vue中onUnmounted在异步上下文中被调用导致警告 | 已解决 | 2026-03-28 |
| E149 | 模型连接失败错误处理 | testAllConnections设置isConnecting但未重置，且无模型时抛出错误 | 已解决 | 2026-03-28 |
| E150 | document_store缺少chroma_client导入 | DocumentVectorStore使用chroma_client但未导入，且is_available是属性不是方法 | 已解决 | 2026-03-28 |
| E151 | Ollama模型qwen2.5:14b未安装 | AI搜索404错误：Ollama默认模型qwen2.5:14b未安装，实际可用模型为qwen3:4b等 | 已解决 | 2026-03-28 |
| E152 | AI搜索Serializer使用错误 | AISearchTaskViewSet未重写get_serializer_class导致create时使用AISearchTaskSerializer（需要keyword字段）而非AISearchTaskCreateSerializer（使用keywords字段），返回400错误 | 已解决 | 2026-03-28 |
| E153 | ProgressTracker缺少steps支持 | ProgressTracker.create_task方法不支持steps参数，导致前端无法显示详细步骤进度 | 已解决 | 2026-03-28 |
| E154 | 后端开发服务器意外退出 | Django开发服务器因未捕获异常退出，导致所有API请求超时ECONNREFUSED | 已解决 | 2026-03-28 |
| E155 | axios超时配置过短 | 前端axios timeout为30秒但Ollama冷启动需42秒导致超时，将timeout改为120秒 | 已解决 | 2026-03-28 |
| E156 | qualification_type字段不存在 | EnterpriseQualification模型使用qualification_category但代码引用qualification_type导致属性错误 | 已解决 | 2026-03-28 |
| E157 | 浏览器驱动未安装 | 采集无数据-目标网站是Vue SPA需浏览器渲染，但pyppeteer未安装且ChromeDriver未安装导致Selenium降级失败 | 已解决 | 2026-03-29 |
| E158 | batch_test导入路径错误 | `apps.crawler.views.batch_test`中使用`from .tasks`导入，但`run_batch_template_test`实际定义在`crawler.tasks`，导致ModuleNotFoundError 500错误 | 已解决 | 2026-03-29 |
| E159 | CrawlSchedule缺少字段 | CrawlSchedule模型缺少regions/enterprise_ids/exec_datetime字段导致前端调用API时500错误 | 已解决 | 2026-03-29 |
| E160 | 前端API数据格式错误 | tenderApi.getList返回DRF分页格式{count,results}但前端错误访问res.data.results | 已解决 | 2026-03-29 |
| E161 | TenderList切换模式失败 | pageMode computed属性使用route.query但onMounted时route可能未更新，导致tenders模式不生效 | 已解决 | 2026-03-29 |
| E162 | SearchForm数据绑定错误 | handleSearch传递formData但fetchData忽略参数使用searchForm，导致搜索条件不同步 | 已解决 | 2026-03-29 |
| E163 | CrawlScheduleUpdateSerializer缺少字段 | 更新序列化器没有包含regions/enterprise_ids/exec_datetime字段，导致编辑保存时这些字段被丢弃 | 已解决 | 2026-03-29 |
| E164 | 前端表单缺少新字段 | CreateSchedule/EditSchedule/AutomationDashboard的form对象没有初始化regions/enterprise_ids/exec_datetime字段 | 已解决 | 2026-03-29 |
| E165 | 企业API数据格式解析错误 | loadEnterprises使用res?.results但DRF分页返回的是res?.data?.results，导致企业列表为空 | 已解决 | 2026-03-29 |
| E166 | el-cascader多选配置错误 | multiple属性写成条件表达式而非直接绑定布尔值，导致多选模式不生效 | 已解决 | 2026-03-29 |
| E167 | robotsparse模块导入错误 | data_source_validator.py中导入`robotsparse`但实际应为`urllib.robotparser.RobotFileParser` | 已解决 | 2026-03-29 |
| E168 | 异步工作流调用错误 | DualStageCollectionView直接调用async方法未创建event loop，导致工作流无法执行 | 已解决 | 2026-03-29 |
| E169 | 原始链接失效无提示 | Dashboard和TenderList点击原始链接失效后显示"页面不存在"无友好提示 | 已解决 | 2026-03-29 |
| E170 | ccgp.gov.cn URL路径缺失 | 爬虫解析URL时使用urljoin导致/cggg/dfgg/gkzb/路径前缀丢失，原始链接跳转到错误页面 | 已解决 | 2026-03-29 |
| E171 | 测试对话框缺少关闭按钮 | testDialogVisible对话框无footer和关闭按钮，用户无法直接关闭 | 已解决 | 2026-03-29 |
| F004 | 采集任务进度展示增强 | 增强进度展示系统：显示步骤名称、进度百分比、开始时间、预计剩余时间、实际耗时；异常步骤标记并显示错误信息；整体任务进度综合展示 | 已完成 | 2026-03-28 |
| F005 | 采集计划表单增强 | 采集计划新增省市区选择器、执行时间选择器、企业资质匹配选择功能 | 已完成 | 2026-03-29 |
| F006 | Dashboard页面优化 | Dashboard页面新增原始链接列、采集数量统计卡片、卡片点击跳转、招标项目分页功能 | 已完成 | 2026-03-29 |
| F007 | OPENCLAW架构统一 | 统一采集架构：one_click_automation和scheduled_crawl_with_match统一使用skill_registry，消除Selenium阻塞问题 | 已完成 | 2026-03-29 |
| F008 | 采集计划执行模式增强 | 新增单次执行/每天循环选择，时间选择器支持24小时制，采集地区支持单选/多选切换 | 已完成 | 2026-03-29 |
| F010 | 新建模板先检验再保存 | 新建模板时先创建临时模板进行检验，检验通过才保存，失败则删除临时模板不保存 | 已完成 | 2026-03-29 |
| E172 | CrawlResult状态不一致 | 采集任务设置状态为processed但同步服务查找matched状态，导致同步失败 | 已解决 | 2026-03-29 |
| E173 | website_type选项值不匹配 | 前端website_type值(government_procurement)与后端choices(government)不匹配导致400错误 | 已解决 | 2026-03-29 |
| E174 | 采集数据未同步到tender | 采集完成直接同步到TenderProject但未清除统计缓存导致Dashboard显示旧数据 | 已解决 | 2026-03-29 |
| E175 | 前端数据格式不一致 | 前端API返回格式res vs res.data导致列表数据读取失败 | 已解决 | 2026-03-29 |
| E176 | 编辑页面缺少选择企业 | ScheduleList.vue编辑对话框中"选择企业"使用v-if="form.auto_match"限制，auto_match为false时不显示 | 已解决 | 2026-03-29 |
| E177 | ScheduleForm缺少自动删除选项 | ScheduleForm.vue组件中缺少"自动删除不匹配"选项，与新建计划页面不一致 | 已解决 | 2026-03-29 |
| E178 | 前端错误处理无法解析DRF格式 | DRF ValidationError返回{"field": ["error"]}格式，但前端只获取error.response?.data?.name?.[0]，无法正确显示具体错误 | 已解决 | 2026-03-29 |
| E179 | CrawlScheduleUpdateSerializer crontab字段验证问题 | crontab字段CharField默认required=True，当用户发送crontab: null时报错；且validate_crontab调用value.strip()时value可能为None | 已解决 | 2026-03-29 |
| E180 | ccgp.gov.cn URL路径前缀丢失 | 爬虫解析URL时，页面链接为./202603/t20260329_xxx.htm，但_fix_ccgp_url正则期望/202603/t20260329_xxx.htm，导致路径拼接错误 | 已解决 | 2026-03-29 |
| E181 | 爬虫URL验证使用HEAD请求被拒绝 | _validate_url使用HEAD请求验证URL，但政府网站对HEAD返回403，而GET实际返回200，导致有效链接被误判为无效 | 已解决 | 2026-03-29 |
| E182 | regionsMultiple状态未保存 | 多选/单选模式状态存储在组件变量中，每次进入编辑页面都重新推断默认值，没有持久化到数据库 | 已解决 | 2026-03-29 |
| F011 | 数据同步机制优化 | CrawlToTenderSyncService同步服务+CrawlSyncView API+采集任务自动同步 | 已完成 | 2026-03-29 |
| F012 | 登录页面记住用户名 | 添加"记住用户名"复选框，用户名保存到localStorage，下次打开自动填充 | 已完成 | 2026-03-29 |
| F013 | 项目知识库功能 | 新增 `/api/v1/knowledge/` API 和前端页面，提供项目结构、模块、数据库模型、API路由、错误日志摘要等信息，供AI了解项目 | 已完成 | 2026-03-29 |
| F014 | 多视图切换对话框组件 | 新增 `MultiViewDialog.vue` 组件，支持选项卡切换、平滑过渡动画、active状态视觉标识，可用于 AI Playground 等多视图场景 | 已完成 | 2026-03-29 |
| F015 | 系统服务状态监控 | 新增 `/api/v1/system/services/` API 和 `ServiceStatusCard.vue` 组件，服务状态显示在左侧导航栏底部（SidebarNav组件内），包含12个服务：PostgreSQL、Redis、Celery Worker/Beat、Chroma、Milvus、MinIO、Ollama、前端等，每30秒自动刷新 | 已完成 | 2026-03-29 |
| E183 | Dashboard招标项目列表为空 | Dashboard.vue获取tendersRes.data?.list，但request.js拦截器返回res而非response.data，导致数据解析路径错误 | 已解决 | 2026-03-29 |
| E184 | 原始链接404检测不准确 | openSourceUrl只检测about:blank和空页面，无法检测政府网站404错误页面（如"对不起，您所访问的页面不存在"） | 已解决 | 2026-03-29 |
| E185 | ccgp URL正则无法匹配无前缀路径 | `_fix_ccgp_url`正则`^/(\d{4})(\d{2})/t...`要求开头必须有`/`，但相对路径`./202603/t...`去掉`./`后变成无前缀，导致匹配失败 | 已解决 | 2026-03-29 |
| E186 | ScheduleList日志数据格式错误 | viewLogs API返回{data:{list:[]}}格式但前端直接用res.data作为数组，导致ElTable prop类型检查失败 | 已解决 | 2026-03-29 |
| E187 | 前端regionsMultiple字段名与后端不匹配 | 前端发送`regionsMultiple`（驼峰）但后端模型期望`regions_multiple`（下划线），导致500错误 | 已解决 | 2026-03-29 |
| E188 | CrawlScheduleCreateSerializer重复create方法 | `CrawlScheduleCreateSerializer`类中定义了两个`create`方法，第二个覆盖第一个，导致`regions_multiple`未被正确移除，创建采集计划时500错误 | 已解决 | 2026-03-29 |
| E189 | Celery Beat未运行导致定时任务不执行 | Celery Beat调度器进程未启动，所有定时任务（包括20:25/20:35上海政府采购采集）均未执行 | 已解决 | 2026-03-29 |
| E190 | Crontab与CrawlSchedule未同步 | CrawlSchedule的crontab设置与PeriodicTask的crontab不一致，如上海政府采购设置20:35但PeriodicTask实际是08:00 | 已解决 | 2026-03-29 |
| E191 | Celery Worker未运行 | Celery Worker进程未启动，即使Beat发送任务也没有执行器处理 | 已解决 | 2026-03-29 |
| E192 | Celery队列名不匹配 | 任务发送到`celery`队列但Worker监听`default`队列，导致任务堆积无法执行 | 已解决 | 2026-03-29 |
| E193 | Windows Celery配置兼容性问题 | `CELERY_TASK_TRACK_STARTED = True`在Windows上与billiard不兼容，导致`ValueError: not enough values to unpack` | 已解决 | 2026-03-29 |
| E194 | 前端API路径缺少v1前缀 | system.js中API路径为`/system/services/`应为`/v1/system/services/`，导致404错误 | 已解决 | 2026-03-29 |
| E195 | MonitoredServiceAdmin status字段错误 | Django Admin中list_filter引用不存在的status字段（status是property不是数据库字段） | 已解决 | 2026-03-29 |
| E196 | 前端请求处理函数不正确 | SidebarNav.vue的fetchServices和ScheduleList.vue的toggleStatus未正确处理API响应，直接检查response.status但response.data才是实际数据 | 已解决 | 2026-03-29 |
| E197 | monitor数据库迁移文件错误 | 0001_initial.py中AddIndex操作使用model_name='servicalert'但实际模型名是'servicealert'，导致migrate失败，monitor_dashboard返回503 | 已解决 | 2026-03-29 |
| E198 | MonitoredService.status是property不是字段 | MonitoredService模型的status是@property，Django不会生成get_status_display()方法，但__str__和views.py中调用了该方法，导致500错误 | 已解决 | 2026-03-29 |
| E199 | 前端用户创建API路径错误 | userAdmin.js的create方法调用POST /v1/auth/，但该路由对应UserListView（ListAPIView，只支持GET），应调用POST /v1/auth/register/，导致405错误 | 已解决 | 2026-03-30 |
| F016 | 实时服务监控与自动恢复系统 | 新增完整的monitor应用模块，包含MonitoredService/ServiceHealthRecord/ServiceAlert/ServiceActionLog数据模型，CeleryHealthChecker健康检查，支持HTTP/TCP/进程/Celery多种检测方式，自动重启机制（冷却策略），钉钉告警通知，24小时历史记录 | 已完成 | 2026-03-29 |

----
*最后更新: 2026-03-30*
*本次更新：新增 E199 错误记录，修复用户创建API路径错误导致的405错误*

---

## E170: ccgp.gov.cn URL路径缺失

**发生时间**: 2026-03-29

**错误类型**: URL解析错误

**错误描述**:
- 中国政府采购网(ccgp.gov.cn)的公告列表页HTML中，链接是相对路径如 `/202603/t20260329_26331188.htm`
- 爬虫使用 `urljoin(BASE_URL, link)` 拼接时得到 `http://www.ccgp.gov.cn/202603/t20260329_26331188.htm`
- 正确URL应为 `https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202603/t20260329_26331188.htm`
- 导致数据库中85条记录的原始链接全部错误，点击后跳转到"错误页面"

**发生场景**:
- 采集中国政府采购网招标公告时
- 用户点击Dashboard或TenderList中的"原始链接"按钮

**原因分析**:
- HTML中的链接是简化路径，缺少 `/cggg/dfgg/gkzb/` 路径段
- urljoin 只做简单拼接，不会智能补全路径

**解决方案**:
1. ~~修复数据库中已有错误URL~~（E170 时已通过数据库迁移修复）
2. 修复爬虫代码 china_gov_crawler.py：添加 `_fix_ccgp_url()` 方法，根据公告类型补全正确的路径前缀
3. **E185 补充修复**：正则表达式 `^/(\d{4})(\d{2})/t...` 改为 `^/?(\d{4})(\d{2})/t...`，支持无 `/` 前缀的路径

**预防措施**:
1. 爬虫解析URL后验证格式是否符合预期
2. 定期抽检数据库中的source_url是否可访问

**相关文件**:
- `backend/crawler/china_gov_crawler.py`
- `apps/tenders/models.py`

---

## E171: 测试对话框缺少关闭按钮

**发生时间**: 2026-03-29

**错误类型**: UI组件缺陷

**错误描述**:
- testDialogVisible 对话框只有内容区域，没有 footer 和关闭按钮
- 用户在检验完成后无法直接关闭对话框，必须点击外部或按ESC

**发生场景**:
- 点击"测试配置"按钮后
- 新建模板检验完成后

**原因分析**:
- 开发时遗漏了对话框的 footer 部分

**解决方案**:
```vue
<el-dialog v-model="testDialogVisible" ... :close-on-click-modal="false">
  ...
  <template #footer>
    <el-button @click="testDialogVisible = false">关闭</el-button>
  </template>
</el-dialog>
```

**预防措施**:
1. 对话框组件默认添加 footer 和关闭按钮
2. 使用 :close-on-click-modal="false" 防止误关

**相关文件**:
- `frontend/src/views/system/WebsiteTemplateList.vue`

---

## F010: 新建模板先检验再保存

**完成时间**: 2026-03-29

**功能描述**:
- 新建网站模板时，系统先创建一个临时模板
- 对临时模板执行检验测试
- 检验通过则正式保存，检验失败则删除临时模板并提示错误
- 编辑模式保持原有的直接保存逻辑

**实现逻辑**:
1. 用户填写表单点击"创建"
2. 先调用 `createWebsiteTemplate` 创建临时模板
3. 调用 `testWebsiteTemplate` 检验配置
4. 检验成功：显示成功消息，关闭对话框，刷新列表
5. 检验失败：删除临时模板，显示失败消息，**不保存**

**相关文件**:
- `frontend/src/views/system/WebsiteTemplateList.vue`

---

## E172: CrawlResult状态不一致

**发生时间**: 2026-03-29

**错误类型**: 数据状态不一致

**错误描述**:
- 采集任务 `scheduled_crawl_with_match` 在保存招标项目后设置 `CrawlResult.status = 'processed'`
- 但 `CrawlToTenderSyncService.sync_all()` 只查询 `status='matched'` 的记录
- 导致已处理的记录不会被同步

**发生场景**:
- 执行采集任务后
- 调用同步接口时

**原因分析**:
- 采集任务和同步服务对 CrawlResult 状态的定义不一致
- 采集任务认为"已处理"即同步完成
- 同步服务只查找"已匹配"状态的记录

**解决方案**:
```python
# tenders/services.py
queryset = CrawlResult.objects.filter(
    status__in=['matched', 'processed']  # 支持两种状态
).exclude(source_url__isnull=True).exclude(source_url='')
```

**相关文件**:
- `crawler/tasks.py` (L817-818)
- `tenders/services.py` (L365-366)

---

## E173: website_type选项值不匹配

**发生时间**: 2026-03-29

**错误类型**: 前后端字段值不一致

**错误描述**:
- 创建网站模板时前端发送 `website_type: 'government_procurement'`
- 后端 `WEBSITE_TYPE_CHOICES` 定义的值是 `'government'`
- DRF 验证失败返回 400 错误: `"government_procurement" 不是合法选项`

**发生场景**:
- 前端选择"政府采购网"类型
- 点击创建按钮提交表单

**原因分析**:
- 前端硬编码的值与后端 choices 定义不一致
- 前端使用更详细的业务名称，后端使用简短的代码

**解决方案**:
统一前端选项值与后端 choices 一致:
```javascript
// 前端 WebsiteTemplateList.vue
<el-option label="政府采购网" value="government" />
<el-option label="企业招标平台" value="enterprise" />
<el-option label="工程建设平台" value="construction" />
```

**预防措施**:
1. 前端选项值必须与后端 choices 严格一致
2. 修改后端 choices 时同步更新前端

**相关文件**:
- `frontend/src/views/system/WebsiteTemplateList.vue`
- `core/constants.py` (WEBSITE_TYPE_CHOICES)

---

## E174: 采集数据未同步到tender

**发生时间**: 2026-03-29

**错误类型**: 缓存未清除

**错误描述**:
- 采集任务已完成，数据已同步到 `tender_projects` 表
- 但 Dashboard 显示的统计数字仍然是旧数据
- 刷新页面后数据才更新

**发生场景**:
- 采集任务执行完成后
- 查看 Dashboard 统计卡片

**原因分析**:
- `TenderService.get_statistics()` 使用 Django 缓存
- 采集任务同步数据后没有清除缓存

**解决方案**:
```python
# crawler/tasks.py 任务完成后添加
from apps.tenders.services import TenderService
TenderService.invalidate_tender_cache()
```

**相关文件**:
- `crawler/tasks.py` (L866-867)
- `tenders/services.py` (invalidate_tender_cache)

---

## E175: 前端数据格式不一致

**发生时间**: 2026-03-29

**错误类型**: API响应格式处理不一致

**错误描述**:
- 部分前端代码直接使用 `res.results` 访问数据
- 但 DRF 分页返回格式是 `res.data.results`
- 导致列表数据读取失败，显示为空

**发生场景**:
- 调用 `tenderApi.getSyncStatus()` 获取同步状态
- 调用其他分页 API 时

**原因分析**:
- `createApi` 封装了响应，直接返回 `res.data`
- 但部分代码直接访问 `res.results`

**解决方案**:
```javascript
// 统一使用 res?.data 或根据实际情况调整
syncStatus.value = res?.data || res
```

**预防措施**:
1. 统一 API 响应格式处理方式
2. 使用 `createApi` 封装时确认返回格式

**相关文件**:
- `frontend/src/api/tender.js`
- `frontend/src/api/base.js`

---

## F011: 数据同步机制优化

**完成时间**: 2026-03-29

**功能描述**:
- 实现 crawler 模块到 tender 模块的自动数据同步机制
- 采集任务完成后自动同步到 TenderProject
- 同步后自动清除统计缓存确保 Dashboard 实时更新

**实现组件**:

1. **同步服务** (`tenders/services.py`)
   - `CrawlToTenderSyncService` 类
   - `sync_all()` - 批量同步
   - `sync_single()` - 单条同步
   - `get_sync_status()` - 获取同步状态

2. **API接口** (`tenders/views.py`)
   - `GET /api/v1/tenders/sync/` - 获取同步状态
   - `POST /api/v1/tenders/sync/` - 执行同步

3. **Celery任务** (`crawler/tasks.py`)
   - `sync_crawl_results_to_tenders()` - 定时同步任务

4. **前端** (已移除手动同步按钮，改为自动同步)

**数据流程**:
```
采集任务 scheduled_crawl_with_match
    ↓
CrawlSession 创建
    ↓
网页采集 (skill_registry)
    ↓
CrawlResult 创建
    ↓
TenderProject 创建/更新 (直接同步)
    ↓
CrawlResult.status = 'processed'
    ↓
执行企业资质匹配
    ↓
TenderService.invalidate_tender_cache() ← 清除缓存
    ↓
任务完成，Dashboard 实时更新
```

**相关文件**:
- `backend/apps/tenders/services.py`
- `backend/apps/tenders/views.py`
- `backend/apps/tenders/urls.py`
- `backend/crawler/tasks.py`

---

## E167: robotsparse模块导入错误

**发生时间**: 2026-03-29

**错误类型**: Python模块导入错误

**错误描述**:
- data_source_validator.py中导入`from urllib.parse import urlparse, robotsparse`
- 但Python标准库中没有`robotsparse`模块
- 正确导入应为`from urllib.robotparser import RobotFileParser`

**发生场景**:
- 创建数据源验证模块时
- 尝试检查robots.txt文件

**原因分析**:
- urllib.parse只包含urlparse函数
- robots.txt解析功能在urllib.robotparser模块的RobotFileParser类

**解决方案**:
```python
# 错误写法
from urllib.parse import urlparse, robotsparse

# 正确写法
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
```

**预防措施**:
1. 使用标准库前先确认模块路径
2. 编写代码后运行测试验证导入正确性

**相关文件**:
- `backend/crawler/data_source_validator.py`

---

## E168: 异步工作流调用错误

**发生时间**: 2026-03-29

**错误类型**: 异步编程错误

**错误描述**:
- DualStageCollectionView直接调用async方法`workflow_manager.execute_workflow()`
- 但没有创建event loop，导致异步工作流无法执行

**发生场景**:
- 调用双阶段采集工作流API接口
- POST /api/v1/crawler/collection/

**原因分析**:
- async函数必须通过event loop执行
- DRF的view是同步函数，不能直接await异步函数

**解决方案**:
```python
# 错误写法
workflow = workflow_manager.execute_workflow(...)  # 这是async函数

# 正确写法
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    workflow = loop.run_until_complete(
        workflow_manager.execute_workflow(...)
    )
finally:
    loop.close()
```

**预防措施**:
1. 在DRF View中调用async函数必须创建event loop
2. 使用finally确保event loop正确关闭
3. 考虑使用sync_to_background等异步任务框架

**相关文件**:
- `backend/apps/crawler/views_verification.py`

---

## E169: 原始链接失效无提示

**发生时间**: 2026-03-29

**错误类型**: 前端用户体验问题

**错误描述**:
- Dashboard和TenderList页面点击原始链接后
- 如果链接已失效（404），浏览器显示"对不起，您所访问的页面不存在"
- 用户体验差，没有友好提示

**发生场景**:
- 政府网站定期清理过期公告
- 早期采集的链接已失效

**原因分析**:
- 爬虫采集的URL可能已过期（政府网站清理旧数据）
- 前端直接window.open()打开链接，无任何检测

**解决方案**:
1. 在openSourceUrl函数中检测链接是否有效
2. 2秒后检测新窗口是否正常加载
3. 检测三种失效情况：
   - about:blank（窗口未打开）
   - 空页面（body.innerHTML 为空）
   - 404页面（内容包含"不存在"、"404"、"无法访问"）
4. 如果检测到失效，关闭新窗口并显示友好提示
5. 提供跳转搜索选项

```javascript
const openSourceUrl = async (url) => {
  if (!url) return
  const openedWindow = window.open(url, '_blank', 'noopener,noreferrer')
  if (openedWindow) {
    setTimeout(() => {
      try {
        const doc = openedWindow.document
        const isAboutBlank = doc.domain === 'about:blank'
        const isEmptyPage = doc.readyState === 'complete' && doc.body?.innerHTML === ''
        const pageContent = doc.body?.innerText || ''
        const is404Page = pageContent.includes('不存在') || pageContent.includes('404') || pageContent.includes('无法访问')
        if (isAboutBlank || isEmptyPage || is404Page) {
          openedWindow.close()
          ElMessageBox.confirm(
            '原始链接可能已失效（网页已被删除或移动）。<br/><br/>是否跳转到中国政府采购网首页搜索相关项目？',
            '链接失效提示',
            { ... }
          )
        }
      } catch (e) {}
    }, 2000)
  }
}
```

**预防措施**:
1. 采集时添加URL有效性验证（已完成）
2. 前端对失效链接提供友好提示
3. 定期清理数据库中的失效链接

**相关文件**:
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/tender/TenderList.vue`

---

## E183: Dashboard招标项目列表为空

**发生时间**: 2026-03-29

**错误类型**: 前端数据解析错误

**错误描述**:
- Dashboard页面招标项目列表显示为空
- 但 TenderList 页面数据正常显示

**发生场景**:
- 打开 Dashboard 页面
- 查看"最新招标项目"列表

**原因分析**:
- Dashboard.vue 使用 `tendersRes.data?.list` 获取列表数据
- 但 request.js 响应拦截器对于成功响应直接返回 `res.data`
- 所以实际数据在 `tendersRes.results` 而非 `tendersRes.data.list`

**解决方案**:
```javascript
// 修复前
recentTenders.value = tendersRes.data?.list || []

// 修复后
recentTenders.value = tendersRes.results || tendersRes.data?.list || []
```

**预防措施**:
1. 统一 API 响应格式规范
2. 使用 project_rules.md 中定义的数据解析方式

**相关文件**:
- `frontend/src/views/Dashboard.vue`

---

## E184: 原始链接404检测不准确

**发生时间**: 2026-03-29

**错误类型**: 前端用户体验问题

**错误描述**:
- 点击原始链接后，如果链接已失效（404），浏览器显示"对不起，您所访问的页面不存在"
- 但系统没有检测到这个404页面，用户体验差

**发生场景**:
- 政府网站定期清理过期公告
- 早期采集的链接已失效
- 点击原始链接后显示404页面

**原因分析**:
- openSourceUrl 只检测 about:blank 和空页面
- 政府网站的404页面有实际内容（"对不起，您所访问的页面不存在"）
- 所以空页面检测无法识别404

**解决方案**:
增强 openSourceUrl 函数的404检测逻辑：
```javascript
const pageContent = doc.body?.innerText || ''
const is404Page = pageContent.includes('不存在') ||
                  pageContent.includes('404') ||
                  pageContent.includes('无法访问')
if (isAboutBlank || isEmptyPage || is404Page) {
  // 显示友好提示
}
```

**预防措施**:
1. 采集时添加URL有效性验证
2. 前端对失效链接提供友好提示
3. 定期清理数据库中的失效链接

**相关文件**:
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/tender/TenderList.vue`

---

## E185: ccgp URL正则无法匹配无前缀路径

**发生时间**: 2026-03-29

**错误类型**: URL解析错误

**错误描述**:
- 爬虫解析URL时，部分链接相对路径去掉 `./` 后变成 `202603/t20260329_xxx.htm`
- 正则表达式 `^/(\d{4})(\d{2})/t...` 要求开头必须有 `/`
- 导致匹配失败，URL没有被正确拼接

**发生场景**:
- 采集中国政府采购网招标公告时
- 某些页面链接格式为 `./202603/t20260329_xxx.htm`

**原因分析**:
- HTML 中的相对路径如 `./202603/t20260329_26331192.htm`
- 代码去掉 `./` 后变成 `202603/t20260329_26331192.htm`
- 正则 `^/(\d{4})(\d{2})/t...` 要求开头必须是 `/`，无法匹配

**解决方案**:
修复 china_gov_crawler.py 中的正则表达式：
```python
# 修复前
ccgp_url_pattern = re.compile(r'^/(\d{4})(\d{2})/t(\d{8}_\d+)\.htm$')

# 修复后
ccgp_url_pattern = re.compile(r'^/?(\d{4})(\d{2})/t(\d{8}_\d+)\.htm$')
```

**预防措施**:
1. 爬虫解析URL后验证格式是否符合预期
2. 定期抽检数据库中的source_url是否可访问

**相关文件**:
- `backend/crawler/china_gov_crawler.py`

---

## E186: ScheduleList日志数据格式错误

**发生时间**: 2026-03-29

**错误类型**: 前端数据格式解析错误

**错误描述**:
- 点击"日志"按钮查看采集计划执行日志
- ElTable报错: `Invalid prop: type check failed for prop "data". Expected Array, got Object`
- 控制台报错: `TypeError: data is not iterable`

**发生场景**:
- ScheduleList.vue 点击日志按钮
- viewLogs 函数获取到 API 响应后赋值给 `logs.value`

**原因分析**:
1. 后端 CrawlScheduleLogViewSet 的 logs/ 接口返回格式: `{code: 0, data: {list: [...]}}`
2. 前端 request.js 拦截器返回整个 `res` 对象（包含 code, message, data）
3. viewLogs 函数中 `logs.value = res.data || []` 直接使用 `res.data`
4. 但 `res.data` 是 `{list: [...]}` 对象，不是数组，导致 ElTable prop 类型检查失败

**解决方案**:
```javascript
// 修改前
logs.value = res.data || []

// 修改后
logs.value = res.data?.list || res.data || []
```

**预防措施**:
1. 统一 API 响应格式，明确区分 `res`（外层响应）和 `res.data`（数据部分）
2. 使用可选链操作符 `?.` 避免访问 undefined 属性
3. 当 API 返回 `{list: [...]}` 格式时，明确使用 `res.data.list`

**相关文件**:
- `frontend/src/views/ScheduleList.vue` (L972)
- `backend/apps/crawler/scheduler_views.py` (L188-191)

---

## E188: CrawlScheduleCreateSerializer重复create方法

**发生时间**: 2026-03-29

**错误类型**: 后端代码重复定义错误

**错误描述**:
- 创建采集计划时返回 500 错误
- 日志显示：`CrawlSchedule() got unexpected keyword arguments: 'regions_multiple'`

**发生场景**:
- 用户在前端点击"创建采集计划"按钮
- POST /api/v1/crawler/schedules/

**原因分析**:
1. `CrawlScheduleCreateSerializer` 类中定义了两个 `create` 方法
2. 第一个 `create` 方法（第92-99行）正确地从 `validated_data` 中 `pop` 了 `regions_multiple`
3. 第二个 `create` 方法（第141-147行）没有 `pop` 操作
4. Python 类只保留最后一个方法定义，所以第二个 `create` 覆盖了第一个
5. 调用 `CrawlSchedule.objects.create(**validated_data)` 时，`regions_multiple` 仍在 `validated_data` 中
6. Django 模型 `CrawlSchedule` 没有 `regions_multiple` 字段，导致 TypeError

**解决方案**:
删除 `CrawlScheduleCreateSerializer` 中重复的 `create` 方法（原第141-147行）

**预防措施**:
1. 代码审查时注意检查类中是否有重复的方法定义
2. 使用 IDE 的代码检查功能检测重复定义
3. 避免在同一个类中复制粘贴相似代码

**相关文件**:
- `backend/apps/crawler/scheduler_serializers.py` (L92-99, L141-147 已删除)

---

## E189: Celery Beat未运行导致定时任务不执行

**发生时间**: 2026-03-29

**错误类型**: 系统服务未运行

**错误描述**:
- 上海政府采购定时任务设置20:35执行，但到时间后无任何反应
- 数据库中 PeriodicTask 的 `total_run_count` 为0，任务从未执行

**发生场景**:
- 定时任务计划时间到达后
- Celery Beat调度器进程未启动

**原因分析**:
1. Celery Beat调度器需要单独启动，不是Django服务的一部分
2. 系统重启后Celery Beat进程未自动启动
3. 没有使用Windows服务或supervisor管理Celery进程

**解决方案**:
```bash
cd d:\共享文件\AUTO\backend
python -m celery -A config.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**预防措施**:
1. 使用Windows服务或supervisor确保Celery Beat开机自启动
2. 添加监控告警，当Celery Beat进程停止时及时发现
3. 在Dashboard添加Celery服务状态监控

**相关文件**:
- 终端进程：Celery Beat

---

## E190: Crontab与CrawlSchedule未同步

**发生时间**: 2026-03-29

**错误类型**: 数据一致性错误

**错误描述**:
- CrawlSchedule数据库中crontab设置为"35 20 * * *"（20:35）
- 但PeriodicTask的crontab实际是"00 08 * * *"（08:00）
- 用户修改CrawlSchedule后，PeriodicTask未同步更新

**发生场景**:
- 用户在新建/编辑采集计划时设置执行时间
- 保存后CrawlSchedule正确，但PeriodicTask未同步

**原因分析**:
1. CrawlSchedule模型保存时触发PeriodicTask更新逻辑
2. 但更新PeriodicTask时没有正确同步crontab字段
3. 或者创建PeriodicTask时使用的是默认crontab而不是用户设置的

**解决方案**:
```python
from django_celery_beat.models import PeriodicTask, CrontabSchedule
task = PeriodicTask.objects.get(name='crawl_schedule_6')
schedule = CrontabSchedule.objects.get(id=task.crontab_id)
schedule.minute = '35'
schedule.hour = '20'
schedule.save()
task.save()
```

**预防措施**:
1. 在CrawlSchedule的save方法中确保PeriodicTask同步更新
2. 添加信号(Signal)机制，当CrawlSchedule保存时自动同步PeriodicTask
3. 定期检查CrawlSchedule和PeriodicTask的crontab是否一致

**相关文件**:
- `backend/apps/crawler/scheduler_models.py`

---

## E191: Celery Worker未运行

**发生时间**: 2026-03-29

**错误类型**: 系统服务未运行

**错误描述**:
- Celery Beat发送任务到队列，但任务永远不会被执行
- Redis队列中有任务堆积（如 celery 队列有314个任务）

**发生场景**:
- Beat发送任务后
- Celery Worker进程未启动

**原因分析**:
1. Celery Worker是实际执行任务的进程
2. 系统重启后Worker进程未自动启动
3. Worker必须和Beat同时运行

**解决方案**:
```bash
cd d:\共享文件\AUTO\backend
python -m celery -A config.celery worker -l info --concurrency=2
```

**预防措施**:
1. 使用Windows服务或supervisor确保Worker开机自启动
2. 添加监控告警，当Worker进程停止时及时发现
3. 在Dashboard添加Celery服务状态监控

---

## E192: Celery队列名不匹配

**发生时间**: 2026-03-29

**错误类型**: 配置不一致

**错误描述**:
- Beat发送任务到`celery`队列
- 但Worker监听`default`队列
- 任务堆积在celery队列中，Worker从不处理

**原因分析**:
1. Django-Celery-Beat默认使用`celery`作为队列名
2. 但启动Worker时如果使用`-Q default`则监听`default`队列
3. 队列名不匹配导致任务无法传递

**解决方案**:
启动Worker时指定正确的队列名：
```bash
python -m celery -A config.celery worker -l info -Q celery,crawler,workflow,vector,notification
```
或修改配置确保默认队列名一致：
```python
CELERY_TASK_DEFAULT_QUEUE = 'celery'
```

**预防措施**:
1. 统一配置所有队列名，避免混用
2. Worker启动时显式指定所有需要监听的队列
3. 在系统文档中记录队列配置

**相关文件**:
- `backend/config/celery.py`

---

## E193: Windows Celery配置兼容性问题

**发生时间**: 2026-03-29

**错误类型**: 配置兼容性错误

**错误描述**:
```
ValueError: not enough values to unpack (expected 3, got 0)
billiard.einfo.RemoteTraceback
```
任务处理时崩溃，错误指向`celery/app/trace.py`和`billiard/pool.py`

**原因分析**:
1. `CELERY_TASK_TRACK_STARTED = True` 在Windows上与billiard有兼容性问题
2. Windows上Celery使用billiard作为Pool实现
3. `CELERY_TASK_TRACK_STARTED`会启用任务跟踪功能，但在Windows+billiard组合下有bug

**解决方案**:
```python
# 在 config/celery.py 中
CELERY_TASK_TRACK_STARTED = False  # 禁用任务跟踪
```

**预防措施**:
1. Windows环境使用简化的Celery配置
2. 生产环境使用Linux以获得更好的Celery支持
3. 查阅Celery官方文档确认Windows兼容的配置

**相关文件**:
- `backend/config/celery.py`

---

## E194: 前端API路径缺少v1前缀

**发生时间**: 2026-03-29

**错误类型**: 前端路由配置错误

**错误描述**:
- 前端请求 `GET /api/system/services/` 返回404
- 但后端API实际路径是 `/api/v1/system/services/`

**原因分析**:
1. 后端所有API都在 `/api/v1/` 前缀下
2. 前端API模块 `system.js` 中写的是 `/system/services/`
3. 没有使用统一的API基础路径配置

**解决方案**:
```javascript
// frontend/src/api/system.js
export function getSystemServices() {
  return request.get('/v1/system/services/')  // 添加v1前缀
}
```

**预防措施**:
1. 统一使用API基础路径配置
2. 在 `request.js` 中设置 `baseURL: '/api/v1'`
3. API模块中只写相对路径

**相关文件**:
- `frontend/src/api/system.js`
- `frontend/src/utils/request.js`

---

## F009: 双阶段采集审核机制

**实现时间**: 2026-03-29

**功能描述**:
建立"验证-采集"双阶段审核机制，确保所有采集活动均符合预设标准与流程要求。

**核心组件**:

1. **数据源验证模块** (`data_source_validator.py`)
   - 合规性验证：robots.txt检查、数据授权确认、隐私政策评估
   - 技术可行性验证：URL可访问性、反爬机制检测、页面结构分析
   - 数据质量预验证：字段完整性、内容语言检测、编码格式检查

2. **双阶段采集工作流** (`staged_collection_workflow.py`)
   - Stage 1: 验证阶段 - 执行数据源验证
   - Stage 2: 采集阶段 - 执行正式数据采集（仅验证通过后）

3. **验证报告模型** (`models_verification.py`)
   - DataSourceVerification: 数据源验证记录
   - CollectionWorkflow: 采集工作流记录
   - CrawlerSourceConfig: 爬虫数据源配置

4. **验证API接口** (`views_verification.py`)
   - POST /api/v1/crawler/validate/ - 执行数据源验证
   - GET /api/v1/crawler/validations/ - 获取验证列表
   - POST /api/v1/crawler/collection/ - 执行双阶段采集
   - GET /api/v1/crawler/workflow/<id>/ - 查询工作流状态

**技术特点**:
- 异步验证：使用aiohttp进行并发URL检测
- 先验证后采集：所有采集任务必须先通过验证
- 人工审核机制：发现警告时暂停等待人工确认
- 完整日志：记录每个阶段的开始时间、结束时间、耗时

**相关文件**:
- `backend/crawler/data_source_validator.py`
- `backend/crawler/staged_collection_workflow.py`
- `backend/apps/crawler/models_verification.py`
- `backend/apps/crawler/views_verification.py`
- `backend/apps/crawler/urls.py`

---

## E159: CrawlSchedule缺少regions/enterprise_ids/exec_datetime字段

**发生时间**: 2026-03-28

**错误描述**:
前端登录后自动连接模型时调用`/api/v1/openclaw/llm-providers/test_all_providers/`返回`timeout of 30000ms exceeded`错误。

**错误分析**:
1. 检查终端发现Django开发服务器（terminal_id 8）已经退出（Exited状态）
2. 服务器退出导致前端所有API请求无法到达后端
3. 前端axios默认超时时间是30秒，所以显示`timeout of 30000ms exceeded`
4. 直接测试Ollama服务（`curl http://localhost:11434/api/tags`）确认Ollama服务正常运行
5. 直接使用Python测试Ollama适配器工作正常，返回了正确的聊天结果

**根本原因**:
Django开发服务器因未捕获的异常而意外退出。可能的原因包括：
1. 请求处理过程中的未捕获异常
2. 数据库连接问题
3. 异步任务（Celery）相关问题导致的连锁反应

**解决方案**:
重新启动Django开发服务器。

**预防措施**:
1. 使用生产级服务器（如Gunicorn/Uvicorn）替代开发服务器
2. 配置进程管理器（supervisor/systemd）监控服务状态
3. 添加健康检查端点定期检测服务可用性
4. 记录服务退出前的异常信息便于排查

---

## E155: axios超时配置过短导致模型连接超时

**发生时间**: 2026-03-28

**错误描述**:
登录后自动连接模型时显示 `timeout of 30000ms exceeded` 错误，后端日志显示 `test_all_providers` 请求花了42.877秒才完成。

**错误日志**:
```
# 前端错误
modelConnection.js:159 测试连接失败: AxiosError: timeout of 30000ms exceeded

# 后端日志
INFO 2026-03-28 22:38:51,950 API请求: {"method": "POST", "path": "/api/v1/openclaw/llm-providers/test_all_providers/", "status": 200, "duration": "42.877s"}
```

**根本原因**:
1. Ollama模型首次调用时需要将模型加载到内存（冷启动）
2. 前端axios默认超时时间为30秒
3. 模型冷启动花了42秒，超过30秒限制导致超时

**问题代码** (frontend/src/utils/request.js):
```javascript
const axiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,  // ❌ 过短，Ollama冷启动可能需要42秒以上
  // ...
})
```

**修复方案**:
增加axios超时配置到120秒（2分钟），为模型冷启动留出足够时间：
```javascript
const axiosInstance = axios.create({
  baseURL: '/api',
  timeout: 120000,  // ✅ 120秒
  // ...
})
```

**修改的文件**:
- `frontend/src/utils/request.js` - 增加timeout从30000到120000

**预防措施**:
1. 对于模型服务相关的API，使用更长的超时配置
2. 考虑在Ollama配置中启用模型预热
3. 或者在首次调用前先发送一个轻量级请求预热模型

---

## E156: qualification_type字段不存在导致属性错误

**发生时间**: 2026-03-28

**错误描述**:
采集任务执行时失败，日志显示 `'EnterpriseQualification' object has no attribute 'qualification_type'`

**错误日志**:
```
ERROR 2026-03-28 20:33:33,905 tasks 22504 24652 定时采集任务执行失败: 'EnterpriseQualification' object has no attribute 'qualification_type'
ERROR 2026-03-28 20:33:33,905 progress_tracker 22504 24652 任务失败: crawl_schedule_3 - 'EnterpriseQualification' object has no attribute 'qualification_type'
```

**根本原因**:
- `EnterpriseQualification` 模型的字段名是 `qualification_category` 和 `qualification_name`
- 但有两处代码错误地使用了 `qualification_type` 属性

**问题代码**:
```python
# apps/enterprise/views.py 第765行
if req_type and qual.qualification_type == req_type:  # ❌ 错误

# openclaw/agents/bid_collector_agent.py 第350行
'type': q.qualification_type,  # ❌ 错误
```

**修复方案**:
```python
# apps/enterprise/views.py
if req_type and qual.qualification_category == req_type:  # ✅ 正确

# openclaw/agents/bid_collector_agent.py
'category': q.qualification_category,  # ✅ 正确
```

**修改的文件**:
- `apps/enterprise/views.py` - 第765、778行
- `openclaw/agents/bid_collector_agent.py` - 第350行

**影响范围**:
- 资质匹配功能完全失败
- 采集任务执行报错退出
- 即使数据采集成功也无法正确匹配合适的企业资质

**预防措施**:
1. 在代码中使用模型字段前先确认字段名
2. 使用IDE的代码补全功能避免拼写错误
3. 添加单元测试验证模型字段访问

---

## E157: 浏览器驱动未安装导致采集无数据

**发生时间**: 2026-03-29

**错误描述**:
采集任务执行完成但返回0条数据。日志显示：
- `第 1 页没有数据，尝试降级到Selenium模式`
- Selenium爬取失败，因为ChromeDriver未正确配置

**错误分析**:
1. 目标网站（上海政府采购网 zfcg.sh.gov.cn）是Vue SPA应用，数据通过JavaScript动态加载
2. HTTP请求只能获取初始HTML壳，无法获取实际数据
3. 代码设计有Selenium降级机制，但ChromeDriver路径未正确配置导致降级失败
4. WebsiteTemplate配置错误：`requires_javascript=False`，但实际需要JS渲染
5. Pyppeteer未安装，代码中的pyppeteer爬虫无法使用

**根本原因**:
1. `apps/crawler/models.py` 中 WebsiteTemplate 的 `requires_javascript` 字段设置为 False
2. `apps/crawler/services.py` 中 `_crawl_with_selenium` 方法未配置Chrome路径
3. `crawler/base_crawler.py` 中 `init_driver` 方法未配置ChromeDriver路径
4. ChromeDriver虽然存在于 `C:\Users\Administrator\.cache\selenium\chromedriver\win64\146.0.7680.165\chromedriver.exe`，但代码未正确查找

**验证测试**:
```python
# 直接使用Selenium测试 - 成功
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chromedriver_path = r"C:\Users\Administrator\.cache\selenium\chromedriver\win64\146.0.7680.165\chromedriver.exe"
driver = webdriver.Chrome(service=Service(executable_path=chromedriver_path), options=options)
# 结果: 页面源码长度 3143265 字符，链接数量 97 ✅
```

**修复方案**:

1. 更新 WebsiteTemplate 配置：
```python
# 将 requires_javascript 设置为 True
```

2. 增强 `apps/crawler/services.py` 中 `_crawl_with_selenium` 方法：
```python
def _crawl_with_selenium(self, url: str, wait_time: int = 10) -> Optional[str]:
    # 添加Chrome路径和ChromeDriver路径配置
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            options.binary_location = chrome_path
            break

    chromedriver_path = self._find_chromedriver()
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)

def _find_chromedriver(self) -> Optional[str]:
    # 查找ChromeDriver的多种路径
    cache_dir = os.path.join(os.environ.get('USERPROFILE', ''), '.cache', 'selenium', 'chromedriver', 'win64')
    if os.path.exists(cache_dir):
        versions = sorted(glob.glob(os.path.join(cache_dir, '*', 'chromedriver.exe')), reverse=True)
        if versions:
            return versions[0]
    # ... 其他路径
```

3. 同样增强 `crawler/base_crawler.py` 中 `init_driver` 方法

**修改的文件**:
- `apps/crawler/models.py` - WebsiteTemplate.requires_javascript 改为 True
- `apps/crawler/services.py` - 增强 Selenium 配置和 ChromeDriver 路径查找
- `crawler/base_crawler.py` - 增强 Selenium 配置和 ChromeDriver 路径查找

**影响范围**:
- 采集任务返回0条数据
- Selenium降级机制失效

**预防措施**:
1. Vue SPA网站必须标记 `requires_javascript=True`
2. Selenium爬虫需要正确配置ChromeDriver路径
3. 添加浏览器渲染功能的前置检查
4. 部署时确保ChromeDriver与Chrome版本匹配

---

## E101: 项目清理 - 审计清理未使用代码和配置


*本次更新：新增 E151 Ollama模型未安装错误修复、E150 document_store缺少chroma_client导入错误修复*

*本次更新：新增 E147-E149，记录模型连接自动重连功能及修复的问题*

*本次更新：新增 E145 filterset_fields字段错误、E146 资质名称值不在choices中*

*本次更新：新增 E144 资质类型选项不匹配错误修复*
*本次更新：新增 E142 代理连接错误记录、E143 BaseViewSet MRO错误修复*
*本次更新：新增 F001-F003 功能记录，包括计划名称唯一性验证、网站模板多模式输入和关键词选择功能*
*本次更新：新增 E139 前端错误处理修复记录*
*本次更新：新增 E140-E141 采集计划API错误修复记录 (参数双重嵌套、website_template验证)*

---

## E134: 进度追踪API路由未注册导致404错误

**发生时间**: 2026-03-28

**错误类型**: 前端组件属性类型错误

**错误描述**:
- 浏览器控制台显示 `error.mjs:22 {name: Array(1)}` 警告
- 来自 Element Plus 的 `debugWarn` 函数

**根本原因**:
- `AIPlayground.vue` 中 el-avatar 组件的 icon prop 传入字符串 `'User'`
- Element Plus 期望的是组件对象，不是字符串

**解决方案**:
1. 将 `User` 添加到图标导入列表
2. icon prop 使用组件对象而非字符串

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

**预防措施**:
1. Element Plus 图标组件的 icon prop 需要传入组件对象
2. 避免在模板中使用字符串引用图标组件

---

## E131: UserLoginLog约束错误导致503错误

**发生时间**: 2026-03-28

**错误类型**: 数据库约束错误

**错误描述**:
- 登录接口返回 503 Service Unavailable
- 后端日志显示: `IntegrityError: null value in column "user_id" violates not-null constraint`

**根本原因**:
- `views.py` 中登录失败时尝试创建 `UserLoginLog` 记录
- 传入 `user_id=None`，但该字段有非空约束

**问题代码**:
```python
# 错误写法
if user is None:
    UserLoginLog.objects.create(
        user_id=None,  # 违反非空约束
        login_ip=get_client_ip(request),
        login_status='failed'
    )
    return APIResponse.error(message='用户名或密码错误', ...)
```

**解决方案**:
移除登录失败时的日志创建逻辑（失败日志非关键数据）

**修改的文件**:
- `backend/apps/users/views.py`

**预防措施**:
1. 创建关联对象记录时，确保外键字段不为 null
2. 如外键可选，使用 `blank=True, null=True`
3. 失败操作可以不记录日志

---

## E132: AI Playground未自动选择默认LLM提供商

**发生时间**: 2026-03-28

**错误类型**: 前端业务逻辑

**功能描述**:
- 用户要求指定 Ollama 为默认提供商
- 数据库中"投标精灵"(ollama) 已标记 `is_default=True`

**解决方案**:
修改前端加载逻辑，优先使用 `is_default` 设置：

```javascript
// 修改后逻辑
const defaultProvider = providers.value.find(p => p.is_default)
if (defaultProvider) {
  selectedProvider.value = defaultProvider.id
} else {
  const ollamaProvider = providers.value.find(p => p.provider_type === 'ollama')
  if (ollamaProvider) {
    selectedProvider.value = ollamaProvider.id
  }
}
```

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

**预防措施**:
1. 前端加载提供商列表后，优先使用后端指定的默认提供商
2. 提供降级逻辑，防止默认提供商不可用时无法选择

---

## E113: 前端字段不匹配导致模型选择失效

**发生时间**: 2026-03-27

**错误类型**: 前后端字段不一致

**错误描述**:
- 用户在模型选择下拉框选择 gemma3:1b 模型后，对话没有使用选择的模型
- 原因：后端 API 返回的字段名是 `type`，但前端代码读取的是 `provider_type`

**解决方案**:
修改前端代码兼容两种字段名：

```javascript
// 修改前
provider_type: p.provider_type,

// 修改后
provider_type: p.type || p.provider_type,
```

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

**预防措施**:
1. 前后端字段命名要保持一致
2. 不确定字段名时，先检查后端 Serializer 的 fields 定义

---

## E114: AI Playground对话框样式优化

**发生时间**: 2026-03-27

**错误类型**: UI/UX改进

**问题描述**:
- AI Playground 页面的对话框可以被用户拖动改变宽度
- 对话框外尺寸不固定，用户体验不一致

**解决方案**:
1. 移除内联样式，添加 CSS class `.fixed-dialog` 统一处理
2. 设置固定宽度和内容区域最大高度

```scss
.fixed-dialog {
  width: 900px;
  max-width: 900px;
  :deep(.el-dialog__body) {
    max-height: 70vh;
    overflow-y: auto;
    overflow-x: hidden;
  }
}
```

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

---

## E115: 错误诊断自动化模块实现

**发生时间**: 2026-03-27

**错误类型**: 新功能开发

**问题描述**:
- 投标工作流执行中遇到错误时，无法自动诊断原因
- 缺乏错误知识库积累，相同错误反复出现
- 缺少自动降级和重试机制

**解决方案**:

#### 1. 创建错误诊断器 `error_diagnoser.py`

```python
# 核心功能
class ErrorDiagnoser:
    ERROR_PATTERNS = [
        # 网络错误模式
        (r"ECONNREFUSED", "后端服务拒绝连接", ErrorType.NETWORK_ERROR, "启动Django服务器"),
        (r"timeout|timed out", "网络请求超时", ErrorType.TIMEOUT_ERROR, "增加超时或切换代理"),
        # ... 共40个错误模式
    ]

    STAGE_FALLBACK_MAP = {
        "collect": {
            ErrorType.NETWORK_ERROR: [
                {"action": FallbackAction.RETRY_WITH_BACKUP, "max_retry": 3},
            ],
        },
        # ... 各阶段降级策略
    }

    def diagnose(self, error, stage, context) -> DiagnosisResult:
        """诊断错误并返回处理方案"""
```

#### 2. 创建失败知识库 `failure_knowledge_base.py`

```python
class FailureKnowledgeBase:
    def record_failure(self, error_type, root_cause, solution, ...):
        """记录失败案例"""

    def get_solution_for_error(self, error_type, root_cause):
        """查询已知解决方案"""

    def get_frequent_errors(self, top_n=10):
        """获取高频错误统计"""
```

#### 3. 创建自动错误处理器 `error_handler.py`

```python
class AutoErrorHandler:
    async def handle_error(self, error, stage, workflow_id, operation):
        """统一错误处理入口"""
        # 1. 自动诊断
        # 2. 查询知识库
        # 3. 执行降级策略
        # 4. 记录失败
```

**新增文件**:
- `backend/services/error_diagnoser.py` - 错误诊断器
- `backend/services/failure_knowledge_base.py` - 失败知识库
- `backend/services/error_handler.py` - 自动错误处理器

**相关文件**:
- `backend/services/bid_automation_workflow.py` - 投标自动化工作流（待集成）

**技术特点**:
- 40+ 错误模式覆盖
- 9 大错误类型分类
- 7 种降级动作策略
- 知识库自学习机制
- 统计分析和优化建议

**下一步**:
- 在 `BidAutomationWorkflow` 中集成错误处理器
- 开发一键启动前端界面

---

### E111: 服务器启动时序问题导致请求失败

**发生时间**: 2026-03-27

**错误类型**: 服务器时序/连接问题

**错误描述**:
- 前端页面加载时发送 API 请求收到 500 Internal Server Error 或 ERR_CONNECTION_REFUSED
- WebSocket 连接失败
- batch_update POST 请求返回 net::ERR_CONNECTION_REFUSED

**错误信息**:
```
GET http://localhost:8081/api/v1/notifications/unread-count/ 500 (Internal Server Error)
WebSocket connection to 'ws://localhost:8081/ws' failed
POST http://localhost:8081/api/v1/openclaw/agent-model-configs/batch_update/ net::ERR_CONNECTION_REFUSED
```

**发生场景**:
- Django 后端服务器启动时需要初始化多个组件（Milvus、Chroma、Ollama等）
- 后端日志显示 `System check identified no issues` 才表示完全就绪
- 如果前端在此之前发送请求，会收到连接错误

**后端启动日志（正常顺序）**:
```
INFO 2026-03-27 18:07:51,442 Milvus初始化失败: <MilvusException: ...>
INFO 2026-03-27 18:07:51,577 Chroma访问: {'operation': 'count', ...}
INFO 2026-03-27 18:07:51,578 当前向量库中有 0 条企业数据
System check identified no issues (0 silenced).   <-- 到这里才完全就绪
March 27, 2026 - 18:07:51
Django version 5.2.12, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
```

**解决方案**:
1. **等待后端完全启动**：看到 `System check identified no issues` 后再使用前端
2. **重启后端**：如果长时间不响应，执行以下命令重启
   ```bash
   cd D:\共享文件\AUTO\backend
   # 停止现有服务器 (Ctrl+Break)
   python manage.py runserver 8000
   ```

3. **检查端口占用**：
   ```powershell
   netstat -ano | Select-String "8000|8081"
   ```

**WebSocket 说明**:
- `WebSocketClient.js:18` 错误来自 **Vite 开发服务器的 HMR 客户端**，不是我们应用的问题
- 我们的应用目前没有实现 WebSocket 客户端

**预防措施**:
1. 开发时先启动后端，等待看到 `System check identified no issues` 再启动前端
2. 前端开发服务器会自动代理到后端，不需要单独启动
3. 如果遇到连接问题，先检查后端日志

---

### E112: StreamingHttpResponse设置hop-by-hop头导致500错误

**发生时间**: 2026-03-27

**错误类型**: HTTP协议/响应头错误

**错误描述**:
- `stream_chat` API返回500 Internal Server Error
- 错误信息: `AssertionError: Hop-by-hop header, 'Connection: keep-alive', not allowed`
- 非流式的`chat` API正常工作，只有流式的`stream_chat`有问题

**错误信息**:
```
AssertionError: Hop-by-hop header, 'Connection: keep-alive', not allowed
```

**发生场景**:
- 访问 `POST /api/v1/openclaw/playground/stream_chat/` 端点
- 使用Ollama模型的流式聊天功能

**根本原因**:
Django的`StreamingHttpResponse`不允许设置hop-by-hop头，如`Connection`、`Transfer-Encoding`等。这些头应该由HTTP服务器（如nginx）设置，而不是应用程序设置。

**解决方案**:
移除响应头中的`Connection: keep-alive`：

```python
response = StreamingHttpResponse(
    generate(),
    content_type='text/event-stream'
)
response['X-Accel-Buffering'] = 'no'
response['Cache-Control'] = 'no-cache'
# 移除了 response['Connection'] = 'keep-alive'
return response
```

**修改的文件**:
- `backend/apps/openclaw/views.py` - `AIPlaygroundViewSet.stream_chat`方法

**正确的SSE响应头**:
```python
response['Content-Type'] = 'text/event-stream'
response['X-Accel-Buffering'] = 'no'  # 禁用nginx缓冲
response['Cache-Control'] = 'no-cache'  # 禁止缓存
```

**Hop-by-hop头列表** (不应在应用层设置):
- Connection
- Keep-Alive
- Proxy-Authenticate
- Proxy-Authorization
- TE
- Trailers
- Transfer-Encoding
- Upgrade

**预防措施**:
1. 不要在`StreamingHttpResponse`上设置hop-by-hop头
2. 使用`X-Accel-Buffering`等代理特定头时，先确认是否属于hop-by-hop类型
3. 生产环境中确保nginx配置正确处理SSE流的缓冲

---

## 操作前检查清单详细错误记录

### E001: API返回500错误 - 模型字段未迁移

**发生时间**: 2025-03-19

**错误类型**: 数据库迁移

**错误描述**:
- 前端调用API时返回500 Internal Server Error
- 原因：在models.py中新增了字段，但未执行数据库迁移

**发生场景**:
- 在CompanyInfo模型中新增技术负责人相关字段后
- 直接调用API，未先执行makemigrations和migrate

**错误信息**:
```
500 Internal Server Error
column "tech_manager_name" of relation "documents_companyinfo" does not exist
```

**解决方案**:
```bash
# 生成迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate
```

**预防措施**:
1. 每次修改models.py后，必须执行数据库迁移
2. 迁移顺序：先makemigrations，再migrate
3. 迁移完成后重启服务

**相关文件**:
- `backend/apps/documents/models.py`
- `backend/apps/documents/migrations/`

---

### E002: 类型错误 - int和str无法相加

**发生时间**: 2025-03-17

**错误类型**: 类型错误

**错误描述**:
- API返回500错误
- 原因：代码中尝试将int类型和str类型相加

**发生场景**:
- 调用 `/api/tenders/?page_size=5` 接口时
- 视图代码中存在类型不一致的运算

**错误信息**:
```
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

**解决方案**:
1. 检查视图代码中的运算操作
2. 确保参与运算的变量类型一致
3. 使用 `str()` 或 `int()` 进行类型转换

**预防措施**:
1. 运算前检查变量类型
2. 使用类型注解明确变量类型
3. 编写单元测试覆盖边界情况

**相关文件**:
- `backend/apps/tenders/views.py`

---

### E003: Django Debug Toolbar命名空间未注册

**发生时间**: 2025-03-17

**错误类型**: 配置错误

**错误描述**:
- API返回500错误
- 原因：代码中引用了'djdt'命名空间，但Django Debug Toolbar未正确配置

**发生场景**:
- 调用多个API接口时触发
- 模板或视图中使用了 `{% url 'djdt:...' %}`

**错误信息**:
```
KeyError: 'djdt'
django.urls.exceptions.NoReverseMatch: 'djdt' is not a registered namespace
```

**解决方案**:
1. 在settings.py的INSTALLED_APPS中添加 'debug_toolbar'
2. 在settings.py的MIDDLEWARE中添加 'debug_toolbar.middleware.DebugToolbarMiddleware'
3. 在urls.py中配置debug_toolbar的URL

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# urls.py
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
```

**预防措施**:
1. DEBUG模式下才启用debug_toolbar
2. 确保urls.py中正确配置debug_toolbar路由
3. 生产环境禁用debug_toolbar

**相关文件**:
- `backend/config/settings.py`
- `backend/config/urls.py`

---

### E004: Redis连接参数错误

**发生时间**: 2025-03-17

**错误类型**: Redis连接

**错误描述**:
- Redis连接初始化失败
- 原因：使用了不支持的参数CLIENT_CLASS

**发生场景**:
- 项目启动时初始化Redis连接
- 使用了旧版本的Redis客户端参数

**错误信息**:
```
TypeError: AbstractConnection.__init__() got an unexpected keyword argument 'CLIENT_CLASS'
```

**解决方案**:
1. 检查Redis客户端版本
2. 移除不支持的CLIENT_CLASS参数
3. 使用正确的连接参数格式

```python
# 旧版本写法（错误）
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',  # 移除此参数
        }
    }
}

# 新版本写法（正确）
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

**预防措施**:
1. 检查第三方库版本兼容性
2. 参考官方文档使用正确的参数
3. 升级库时检查Breaking Changes

**相关文件**:
- `backend/config/settings.py`

---

### E005: 数据库表不存在 - token_blacklist

**发生时间**: 2025-03-17

**错误类型**: 数据库迁移

**错误描述**:
- 数据库表不存在错误
- 原因：rest_framework_simplejwt的token_blacklist应用未迁移

**发生场景**:
- 使用JWT Token认证时
- Token黑名单功能需要的表未创建

**错误信息**:
```
django.db.utils.ProgrammingError: 关系 "token_blacklist_outstandingtoken" 不存在
```

**解决方案**:
```bash
# 执行simplejwt的迁移
python manage.py migrate token_blacklist
```

或在settings.py中确保已添加应用：
```python
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt.token_blacklist',
]
```

**预防措施**:
1. 添加新应用后执行迁移
2. 确保INSTALLED_APPS中包含所需应用
3. 部署前检查所有迁移是否已执行

**相关文件**:
- `backend/config/settings.py`

---

### E006: 数据库字段不存在 - qualification_types

**发生时间**: 2025-03-18

**错误类型**: 数据库迁移

**错误描述**:
- API返回500错误
- 原因：CompanyInfo模型中新增了qualification_types字段，但未迁移

**发生场景**:
- 调用 `/api/v1/documents/company/` 接口时
- 模型字段已定义但数据库表结构未更新

**错误信息**:
```
psycopg2.errors.UndefinedColumn: 字段 company_infos.qualification_types 不存在
django.db.utils.ProgrammingError: 字段 company_infos.qualification_types 不存在
```

**解决方案**:
```bash
python manage.py makemigrations
python manage.py migrate
```

**预防措施**:
1. 修改模型后立即执行迁移
2. 提交代码前确认迁移文件已生成
3. 部署前执行所有迁移

**相关文件**:
- `backend/apps/documents/models.py`

---

### E007: Token验证失败

**发生时间**: 2025-03-17

**错误类型**: 认证错误

**错误描述**:
- API返回认证失败
- 原因：Token已过期或无效

**发生场景**:
- 前端请求API时携带过期Token
- 用户长时间未登录后再次访问

**错误信息**:
```
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [{
        "token_class": "AccessToken",
        "token_type": "access",
        "message": "Token is invalid"
    }]
}
```

**解决方案**:
1. 前端清除本地存储的Token
2. 重新登录获取新Token
3. 实现Token自动刷新机制

```javascript
// 前端处理
localStorage.removeItem('token');
localStorage.removeItem('refresh_token');
// 跳转到登录页
router.push('/login');
```

**预防措施**:
1. 前端实现Token过期自动刷新
2. 设置合理的Token过期时间
3. 使用refresh_token机制

**相关文件**:
- `frontend/src/utils/auth.js`
- `frontend/src/api/user.js`

---

### E008: ElTable data属性类型错误

**发生时间**: 2026-03-19

**错误类型**: 前端数据格式

**错误描述**:
- 前端控制台报错：Invalid prop: type check failed for prop "data". Expected Array, got Object
- 原因：后端分页返回的数据格式与前端期望不一致

**发生场景**:
- 访问定时采集计划页面时
- ElTable组件期望data属性为数组，但收到了对象

**错误信息**:
```
Invalid prop: type check failed for prop "data". Expected Array, got Object Proxy(Object) {…}
```

**后端返回格式**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "list": [...],
    "pagination": { "page": 1, "total": 100 }
  }
}
```

**前端错误处理**:
```javascript
// 错误写法
schedules.value = res.data.results || res.data  // res.data是对象，不是数组

// 正确写法
if (res.data && res.data.list) {
  schedules.value = res.data.list
  pagination.total = res.data.pagination?.total || 0
} else if (res.data && res.data.results) {
  schedules.value = res.data.results
  pagination.total = res.data.count || 0
} else if (Array.isArray(res.data)) {
  schedules.value = res.data
}
```

**解决方案**:
修改前端代码，正确处理后端分页响应格式，依次检查 `res.data.list`、`res.data.results`、`Array.isArray(res.data)` 三种情况。

**预防措施**:
1. 前端处理API响应时需考虑多种数据格式
2. 使用可选链操作符 `?.` 避免空值错误
3. 添加数组类型检查 `Array.isArray()`

**相关文件**:
- `frontend/src/views/ScheduleList.vue`
- `backend/core/pagination.py`

---

### E009: DRF IPAddressField序列化器错误

**发生时间**: 2026-03-19

**错误类型**: 序列化器错误

**错误描述**:
- API返回500错误
- 原因：DRF的IPAddressField在序列化器中使用时存在兼容性问题

**发生场景**:
- 调用 `/api/v1/auth/login-logs/` 接口时
- UserLoginLogSerializer中使用了IPAddressField

**错误信息**:
```
ValueError: not enough values to unpack (expected 2, got 1)
File "rest_framework/fields.py", line 862, in __init__
    validators, error_message = ip_address_validators(protocol, self.unpack_ipv4)
```

**错误代码**:
```python
class UserLoginLogSerializer(serializers.ModelSerializer):
    login_ip = serializers.IPAddressField(protocol='both', read_only=True)
```

**解决方案**:
使用CharField替代IPAddressField：
```python
class UserLoginLogSerializer(serializers.ModelSerializer):
    login_ip = serializers.CharField(read_only=True, allow_null=True)
```

**预防措施**:
1. DRF的IPAddressField在某些版本存在兼容性问题
2. 对于IP地址字段，可使用CharField作为替代方案
3. 数据库层面仍可使用GenericIPAddressField，只在序列化器层面改用CharField

**相关文件**:
- `backend/apps/users/serializers.py`
- `backend/apps/users/models.py`

---

### E010: Admin导入不存在的模型类

**发生时间**: 2026-03-20

**错误类型**: 导入错误

**错误描述**:
- 服务器启动失败
- 原因：admin.py中导入了models.py中不存在的模型类

**发生场景**:
- 启动Django服务器时
- openclaw应用的admin.py导入了AgentSession、AgentInstance等不存在的模型

**错误信息**:
```
ImportError: cannot import name 'AgentSession' from 'apps.openclaw.models'
```

**解决方案**:
修改admin.py，只导入models.py中实际存在的模型类：
```python
# 错误写法
from .models import (
    AgentSession, AgentInstance, AgentTask,
    SkillExecution, LLMCall, SandboxExecution
)

# 正确写法
from .models import (
    LLMProvider, LLMModel, AgentModelConfig, LLMUsageLog
)
```

**预防措施**:
1. 修改models.py后同步更新admin.py
2. 确保admin.py中注册的模型与models.py一致
3. 使用IDE的自动导入检查功能

**相关文件**:
- `backend/apps/openclaw/admin.py`
- `backend/apps/openclaw/models.py`

---

### E011: f-string中不能使用反斜杠

**发生时间**: 2026-03-20

**错误类型**: 语法错误

**错误描述**:
- Python语法错误
- 原因：f-string表达式中不能直接使用反斜杠转义字符

**发生场景**:
- bid_document_agents.py中生成技术方案时
- 在f-string中使用了 `\n` 换行符

**错误信息**:
```
SyntaxError: f-string expression part cannot include a backslash
```

**错误代码**:
```python
# 错误写法
message = f"""...
{chr(10).join(f'- {s}' for s in subsections) if subsections else '- 技术路线\n- 实施方案\n- 质量保证'}
..."""
```

**解决方案**:
将反斜杠表达式移到f-string外部：
```python
# 正确写法
default_sections = '- 技术路线' + chr(10) + '- 实施方案' + chr(10) + '- 质量保证'
sections_text = chr(10).join(f'- {s}' for s in subsections) if subsections else default_sections
message = f"""...
{sections_text}
..."""
```

**预防措施**:
1. f-string中避免使用反斜杠
2. 使用chr(10)替代\n
3. 将复杂表达式提取到变量中

**相关文件**:
- `backend/openclaw/agents/bid_document_agents.py`

---

### E012: 缺少Python依赖模块

**发生时间**: 2026-03-20

**错误类型**: 模块依赖

**错误描述**:
- 服务器启动失败
- 原因：缺少openai、sentence_transformers、chromadb等可选依赖

**发生场景**:
- 启动Django服务器时
- embedding_service.py和chroma_service.py尝试导入可选模块

**错误信息**:
```
ModuleNotFoundError: No module named 'openai'
ModuleNotFoundError: No module named 'sentence_transformers'
ModuleNotFoundError: No module named 'chromadb'
```

**解决方案**:
添加后备方案，当模块不可用时使用Dummy实现：
```python
# embedding_service.py
class DummyEmbeddingModel(BaseEmbeddingModel):
    def embed(self, text: str) -> List[float]:
        return []
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return []

# chroma_service.py
try:
    from chromadb import Client, PersistentClient
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

class DummyChromaService:
    def search_similar(self, query_text: str, n_results: int = 10) -> List[Dict]:
        return []
```

**预防措施**:
1. 可选依赖使用try/except包裹
2. 提供后备实现方案
3. 记录警告日志提示用户安装依赖

**相关文件**:
- `backend/services/embedding_service.py`
- `backend/services/chroma_service.py`

---

### E013: 数据库迁移新增字段缺少默认值

**发生时间**: 2026-03-20

**错误类型**: 数据库迁移

**错误描述**:
- 迁移失败
- 原因：新增的非空字段没有提供默认值，数据库无法为已有记录填充值

**发生场景**:
- 执行makemigrations时
- AgentTask模型新增了agent_type、task_name等非空字段

**错误信息**:
```
It is impossible to add a non-nullable field 'agent_type' to agenttask without specifying a default.
```

**解决方案**:
为新增字段添加默认值：
```python
# 错误写法
agent_type = models.CharField('Agent类型', max_length=50)

# 正确写法
agent_type = models.CharField('Agent类型', max_length=50, default='collector')
task_name = models.CharField('任务名称', max_length=200, default='')
```

**预防措施**:
1. 新增非空字段时必须指定default值
2. 或者设置null=True, blank=True
3. 执行makemigrations前检查模型定义

**相关文件**:
- `backend/apps/openclaw/workflow_models.py`

---

### E014: ResizeObserver运行时错误

**发生时间**: 2026-03-20

**错误类型**: 前端运行时

**错误描述**:
- 前端控制台报错：ResizeObserver loop completed with undelivered notifications
- 原因：Element Plus等UI库在元素尺寸变化时触发ResizeObserver，但回调中又触发了新的尺寸变化

**发生场景**:
- 使用Element Plus的el-table、el-dialog等组件时
- 组件内部尺寸计算触发ResizeObserver循环

**错误信息**:
```
ERROR: ResizeObserver loop completed with undelivered notifications.
at handleError (webpack-internal:///./node_modules/webpack-dev-server/client/overlay.js:307:58)
```

**解决方案**:
在main.js中添加全局错误处理，忽略ResizeObserver非致命错误：
```javascript
// Vue全局错误处理
app.config.errorHandler = (err, vm, info) => {
  if (err.message && err.message.includes('ResizeObserver')) {
    return
  }
  console.error('Vue Error:', err, info)
}

// 全局错误监听
window.addEventListener('error', (event) => {
  if (event.message && event.message.includes('ResizeObserver')) {
    event.preventDefault()
    return false
  }
})

window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && event.reason.message.includes('ResizeObserver')) {
    event.preventDefault()
    return false
  }
})
```

**预防措施**:
1. ResizeObserver错误通常是非致命的，可以安全忽略
2. 使用全局错误处理过滤此类错误
3. 避免在ResizeObserver回调中同步修改DOM尺寸

**相关文件**:
- `frontend/src/main.js`

---

### E015: ElOption value属性为undefined

**发生时间**: 2026-03-20

**错误类型**: 前端组件

**错误描述**:
- 前端控制台报错：Invalid prop: type check failed for prop "value". Expected String | Number | Boolean | Object, got Undefined
- 原因：两个问题叠加导致
  1. 前端axios响应拦截器检查`res.code === 0`，但DRF直接返回数据没有code字段
  2. 使用`v-for="(label, value) in object"`遍历时，如果对象为空或未定义，value会是undefined

**发生场景**:
- 访问企业文档页面时
- el-select组件中使用v-for遍历对象属性
- API返回数据被拦截器错误处理后，documentOptions为空对象

**错误信息**:
```
Invalid prop: type check failed for prop "value". Expected String | Number | Boolean | Object, got Undefined
at <ElOption> at <ElSelect> at <CompanyDocuments>
```

**错误代码**:
```vue
<!-- 错误写法：直接遍历对象，value可能为undefined -->
<el-option v-for="(label, value) in documentOptions.document_types" 
           :key="value" :label="label" :value="value" />
```

```javascript
// request.js 错误逻辑：DRF返回的数据没有code字段
request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 0) {  // DRF数据没有code，这里会失败
      return res
    } else {
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  }
)
```

**解决方案**:

1. 修复request.js响应拦截器，兼容DRF直接返回的数据：
```javascript
request.interceptors.response.use(
  response => {
    const res = response.data
    
    // 兼容DRF直接返回的数据（没有code字段）
    if (res.code === undefined) {
      return res
    }
    
    if (res.code === 0) {
      return res
    } else {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  }
)
```

2. 使用计算属性转换对象为数组，确保value不会是undefined：
```vue
<!-- 正确写法：使用计算属性 -->
<el-option v-for="item in documentTypeOptions" 
           :key="item.value" :label="item.label" :value="item.value" />
```

```javascript
const documentTypeOptions = computed(() => {
  const types = documentOptions.value.document_types || {}
  return Object.entries(types)
    .filter(([value, label]) => value !== undefined && value !== null && value !== '')
    .map(([value, label]) => ({ value, label }))
})
```

**预防措施**:
1. 前端响应拦截器需兼容多种API响应格式
2. 使用v-for遍历对象时，优先转换为数组格式
3. 为可能为空的数据提供默认值（如 `|| {}`）
4. 使用计算属性处理数据转换，确保数据格式稳定
5. 在转换时过滤掉 undefined/null/空字符串的值，防止 ElOption 报错

**相关文件**:
- `frontend/src/utils/request.js`
- `frontend/src/views/company/CompanyDocuments.vue`

---

### E016: CompanyInfo模型废弃迁移

**发生时间**: 2026-03-20

**错误类型**: 模型废弃

**错误描述**:
- CompanyInfo模型已废弃，需要迁移到Enterprise + EnterpriseBidConfig
- 原因：模型设计不合理，企业信息和投标配置耦合

**发生场景**:
- 使用CompanyInfo API时收到废弃警告
- 新功能开发需要使用Enterprise模型

**解决方案**:
1. 使用迁移服务迁移数据：
```python
from services.company_info_migration import CompanyInfoMigrationService
results = CompanyInfoMigrationService.migrate_all_company_infos()
```

2. 或调用API迁移：
```bash
POST /api/v1/enterprise/enterprises/migrate_company_infos/
```

3. 更新代码引用：
```python
# 旧代码
from apps.documents.models import CompanyInfo
company = CompanyInfo.objects.get(user=user, is_default=True)

# 新代码
from apps.enterprise.models import Enterprise, EnterpriseBidConfig
enterprise = Enterprise.objects.filter(created_by=user, is_active=True).first()
bid_config = enterprise.bid_config
```

**预防措施**:
1. 新功能开发使用Enterprise模型
2. 定期检查废弃模型的使用情况
3. 计划删除日期前完成迁移

**相关文件**:
- `backend/apps/documents/models.py` - CompanyInfo模型（已废弃）
- `backend/apps/enterprise/models.py` - Enterprise + EnterpriseBidConfig
- `backend/services/qualification_matcher.py` - 已更新使用Enterprise

---

### E017: LLM服务统一迁移

**发生时间**: 2026-03-20

**错误类型**: 服务重构

**错误描述**:
- openclaw.llm_service.LLMService已废弃
- 需要统一使用UnifiedLLMService

**发生场景**:
- 使用旧LLM服务时收到废弃警告
- 需要多模型提供商支持

**解决方案**:
更新代码使用统一LLM服务：
```python
# 旧代码
from openclaw.llm_service import LLMService
llm = LLMService()
response = await llm.chat("Hello")

# 新代码
from services.unified_llm_service import unified_llm_service
result = await unified_llm_service.chat(
    message="Hello",
    agent_type="bid_collector"  # 自动选择模型
)
content = result['content']
```

**UnifiedLLMService优势**:
- 支持6种提供商：Ollama/vLLM/OpenAI/智谱/通义千问/DeepSeek
- 数据库配置管理
- 使用日志记录
- Agent模型自动选择

**预防措施**:
1. 新功能开发使用UnifiedLLMService
2. 旧代码逐步迁移
3. 配置数据库中的LLMProvider

**相关文件**:
- `backend/openclaw/llm_service.py` - 已废弃
- `backend/services/unified_llm_service.py` - 新服务
- `backend/openclaw/skills/parser/tender_parser.py` - 已更新

---

### E018: 缓存配置迁移到Redis

**发生时间**: 2026-03-20

**错误类型**: 配置更新

**错误描述**:
- 缓存从LocMemCache迁移到Redis
- 多进程环境下本地缓存不共享

**发生场景**:
- 生产环境部署时缓存不一致
- 多worker进程缓存不共享

**解决方案**:
1. 确保Redis服务运行：
```bash
redis-server
```

2. 配置环境变量：
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_CACHE_DB=1
```

3. 使用缓存服务：
```python
from core.cache import cache_service, cache_result

# 使用装饰器
@cache_result('user_info', timeout=60, key_params=['user_id'])
def get_user_info(user_id):
    return User.objects.get(id=user_id)

# 使用服务类
cache_service.set('key', 'value', timeout=300)
value = cache_service.get('key')
cache_service.delete_pattern('user_*')
```

**缓存TTL配置**:
```python
CACHE_TTL = {
    'DEFAULT': 300,
    'USER_PERMISSIONS': 60,
    'ENTERPRISE_INFO': 600,
    'TENDER_LIST': 120,
    'DOCUMENT_OPTIONS': 3600,
}
```

**预防措施**:
1. 生产环境必须使用Redis
2. 设置合理的缓存过期时间
3. 关键数据更新时清除相关缓存

**相关文件**:
- `backend/config/settings/base.py` - 缓存配置
- `backend/core/cache.py` - 缓存工具类

---

### E019: 分页器count属性错误

**发生时间**: 2026-03-20

**错误类型**: 分页错误

**错误描述**:
- API返回500错误
- 原因：在BidRecordListView的list方法中错误使用了`self.paginator.count`
- DRF的paginator对象没有count属性，count在page.paginator上

**发生场景**:
- 调用 `/api/v1/bids/records/?page=1&page_size=20&status=` 接口时
- 自定义list方法中访问分页总数

**错误信息**:
```
AttributeError: 'StandardPagination' object has no attribute 'count'
File "apps/bids/views.py", line 68, in list
    'total': self.paginator.count if self.paginator else len(queryset),
```

**错误代码**:
```python
# 错误写法
def list(self, request, *args, **kwargs):
    page = self.paginate_queryset(queryset)
    if page is not None:
        return APIResponse.success(data={
            'list': serializer.data,
            'pagination': {
                'total': self.paginator.count if self.paginator else len(queryset),
            }
        })
```

**解决方案**:
使用`page.paginator.count`获取总数：
```python
# 正确写法
def list(self, request, *args, **kwargs):
    page = self.paginate_queryset(queryset)
    if page is not None:
        total_count = page.paginator.count if hasattr(page, 'paginator') else len(queryset)
        return APIResponse.success(data={
            'list': serializer.data,
            'pagination': {
                'total': total_count,
            }
        })
```

**预防措施**:
1. DRF分页器中，`paginate_queryset()`返回的是page对象
2. 总数通过`page.paginator.count`获取
3. 使用`hasattr()`检查属性存在性

**相关文件**:
- `backend/apps/bids/views.py`

---

### E020: 前端API路径缺少v1前缀导致404错误

**发生时间**: 2026-03-20

**错误类型**: API路径错误

**错误描述**:
- 前端调用API返回404 Not Found
- 原因：前端API文件中的URL路径缺少`v1`前缀

**发生场景**:
- 访问向量库页面 http://localhost:8007/vectorlib 时
- API请求 `/api/vectorlib/documents/statistics/` 返回404
- API请求 `/api/vectorlib/documents/` 返回404

**错误信息**:
```
GET http://localhost:8081/api/vectorlib/documents/statistics/ 404 (Not Found)
GET http://localhost:8081/api/vectorlib/documents/?page=1&page_size=20 404 (Not Found)
```

**错误代码**:
```javascript
// 错误写法 - 缺少v1前缀
export const vectorlibApi = {
  getDocuments(params = {}) {
    return request({
      url: '/vectorlib/documents/',  // 错误：缺少/v1前缀
      method: 'get',
      params
    })
  },
  getStatistics() {
    return request({
      url: '/vectorlib/documents/statistics/',  // 错误：缺少/v1前缀
      method: 'get'
    })
  }
}
```

**后端路由配置**:
```python
# backend/config/urls.py
path('api/v1/vectorlib/', include('apps.vectorlib.urls')),
```

**解决方案**:
修改前端API文件，添加`v1`前缀：
```javascript
// 正确写法 - 添加v1前缀
export const vectorlibApi = {
  getDocuments(params = {}) {
    return request({
      url: '/v1/vectorlib/documents/',  // 正确：添加/v1前缀
      method: 'get',
      params
    })
  },
  getStatistics() {
    return request({
      url: '/v1/vectorlib/documents/statistics/',  // 正确：添加/v1前缀
      method: 'get'
    })
  }
}
```

**预防措施**:
1. 前端API路径必须与后端urls.py中的路由配置保持一致
2. 后端路由格式为 `/api/v1/模块名/`，前端request.js的baseURL为 `/api`，所以URL需要以 `/v1/模块名/` 开头
3. 新增API模块时，先检查后端路由配置，再编写前端API
4. 使用统一的API路径规范：`/v1/{module}/{resource}/`

**相关文件**:
- `frontend/src/api/vectorlib.js` - 前端API文件
- `backend/config/urls.py` - 后端路由配置
- `backend/apps/vectorlib/urls.py` - 向量库模块路由

---

### E021: Django启动错误 - AppRegistryNotReady

**发生时间**: 2026-03-20

**错误类型**: Django启动错误

**错误描述**:
- Django服务器启动失败
- 错误信息: `AppRegistryNotReady: Apps aren't loaded yet.`

**发生场景**:
- 启动Django开发服务器时
- 访问前端页面时后端API返回500错误

**错误信息**:
```
django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
  File "D:\共享文件\AUTO\backend\core\__init__.py", line 36, in <module>
    from .exceptions import custom_exception_handler
  File "D:\共享文件\AUTO\backend\core\exceptions.py", line 5, in <module>
    from rest_framework.views import exception_handler
  ...
```

**错误原因**:
- `core/__init__.py` 文件中包含 `default_app_config = 'core.apps.CoreConfig'`
- 该配置导致Django在加载应用之前就尝试导入DRF相关模块
- DRF模块需要访问Django的AppRegistry，但此时应用尚未加载

**解决方案**:
删除 `core/__init__.py` 中的 `default_app_config` 配置行：
```python
# 删除以下行：
default_app_config = 'core.apps.CoreConfig'
```

**预防措施**:
1. 避免在 `__init__.py` 文件中使用 `default_app_config`
2. Django应用配置应放在 `apps.py` 文件中
3. 避免在模块顶层过早导入需要Django AppRegistry的模块

**相关文件**:
- `backend/core/__init__.py` - 已删除 default_app_config 配置

---

### E022: Element Plus图标组件未正确注册

**发生时间**: 2026-03-20

**错误类型**: 前端图标注册错误

**错误描述**:
- 页面按钮上的图标无法显示
- 错误信息: `Invalid vnode type when creating vnode: undefined`

**发生场景**:
- 访问 /company/documents 页面上传证书、批量识别、批量删除按钮
- 按钮显示为禁用状态且图标无法渲染

**错误信息**:
```
Invalid vnode type when creating vnode: undefined
at <ElIcon> 
at <ElButton> 
at <CompanyDocuments>
```

**错误原因**:
- main.js 中使用 `import * as ElementPlusIconsVue from '@element-plus/icons-vue'` 批量导入所有图标
- 然后使用 `Object.entries(ElementPlusIconsVue)` 遍历注册
- 这种方式可能导致某些图标组件在Vue组件注册前未正确解析

**解决方案**:
修改 `frontend/src/main.js`，明确导入需要的图标组件并注册：

```javascript
import {
  Upload,
  Delete,
  View,
  Download,
  Star,
  CircleCheck,
  CircleClose,
  ArrowDown,
  Document,
  Scan,
  Connection,
  Refresh,
  Edit
} from '@element-plus/icons-vue'

const icons = {
  Upload,
  Delete,
  View,
  Download,
  Star,
  CircleCheck,
  CircleClose,
  ArrowDown,
  Document,
  Scan,
  Connection,
  Refresh,
  Edit
}

for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}
```

**预防措施**:
1. 使用明确的导入方式而不是批量导入 `*`
2. 在项目初期就验证图标组件是否正常工作
3. 可以使用全局图标组件方式，在组件内部导入需要的图标

**相关文件**:
- `frontend/src/main.js` - 已修改图标导入方式

---

### E023: API管理渐进式三层架构重构

**发生时间**: 2026-03-20

**错误类型**: 架构重构

**更新描述**:
- 将API管理重构为渐进式三层架构
- 支持v1和v2两个版本的API同时运行

**架构设计**:

```
┌─────────────────────────────────────────────────────────────┐
│                      ViewSet层 (控制器)                       │
│  - 处理HTTP请求                                               │
│  - 参数验证和转换                                              │
│  - 调用Service层                                              │
│  - 返回响应                                                   │
├─────────────────────────────────────────────────────────────┤
│                      Service层 (业务逻辑)                      │
│  - 业务规则处理                                                │
│  - 数据验证                                                   │
│  - 事务管理                                                   │
│  - 调用Repository层                                           │
├─────────────────────────────────────────────────────────────┤
│                      Repository层 (数据访问)                   │
│  - 数据库CRUD操作                                              │
│  - 查询构建                                                   │
│  - 数据过滤和排序                                              │
└─────────────────────────────────────────────────────────────┘
```

**新增文件**:

1. **核心基础类**:
   - `backend/core/repository/base.py` - BaseRepository基类
   - `backend/core/repository/__init__.py` - Repository层入口
   - `backend/core/service/base.py` - BaseService基类和ServiceResult
   - `backend/core/service/__init__.py` - Service层入口
   - `backend/core/viewset/base.py` - BaseViewSet/ModelViewSet/ReadOnlyViewSet/ActionViewSet
   - `backend/core/viewset/__init__.py` - ViewSet层入口
   - `backend/core/versioning.py` - API版本控制

2. **Enterprise模块实现**:
   - `backend/apps/enterprise/repositories.py` - 企业模块Repository层
   - `backend/apps/enterprise/services_v2.py` - 企业模块Service层
   - `backend/apps/enterprise/views_v2.py` - 企业模块ViewSet层
   - `backend/apps/enterprise/urls_v2.py` - 支持版本化的URL配置

**使用示例**:

```python
# Repository层
class EnterpriseRepository(BaseRepository[Enterprise]):
    model = Enterprise
    
    def find_by_credit_code(self, credit_code: str):
        return self.find_one(credit_code=credit_code)

# Service层
class EnterpriseService(BaseService[Enterprise]):
    repository_class = EnterpriseRepository
    serializer_class = EnterpriseSerializer
    
    def create_enterprise(self, data: dict, user) -> ServiceResult:
        with self.transaction():
            instance = self.repository.create(**data, created_by=user)
            return ServiceResult.ok(data=instance)

# ViewSet层
class EnterpriseViewSetV2(ModelViewSet):
    service_class = EnterpriseService
    serializer_class = EnterpriseSerializer
    
    def create(self, request):
        result = self.service.create_enterprise(request.data, request.user)
        return self.from_result(result)
```

**API版本控制**:

```python
# v1 API (旧架构)
/api/v1/enterprise/enterprises/

# v2 API (新架构)
/api/v2/enterprise/enterprises/

# 默认API (指向v2)
/api/enterprise/enterprises/
```

**功能开关**:

```python
# settings.py
API_FEATURE_FLAGS = {
    'use_new_architecture': True,
    'use_v2_serializers': True,
    'use_v2_response_format': True,
}
```

**迁移指南**:

1. 新功能开发使用新架构
2. 旧API保持兼容，通过版本号区分
3. 逐步迁移其他模块到新架构
4. 计划废弃日期：2025-12-31

**架构优势**:

1. **职责分离**: 每层只关注自己的职责
2. **可测试性**: 每层可独立测试
3. **可维护性**: 修改不影响其他层
4. **渐进式迁移**: 新旧架构可共存
5. **版本控制**: API版本化管理

**预防措施**:
1. 新功能开发使用新架构
2. 旧代码逐步迁移
3. 保持API向后兼容

**相关文件**:
- `backend/core/repository/` - Repository层基础类
- `backend/core/service/` - Service层基础类
- `backend/core/viewset/` - ViewSet层基础类
- `backend/core/versioning.py` - API版本控制
- `backend/apps/enterprise/repositories.py` - 企业Repository实现
- `backend/apps/enterprise/services_v2.py` - 企业Service实现
- `backend/apps/enterprise/views_v2.py` - 企业ViewSet实现
- `backend/apps/enterprise/urls_v2.py` - 版本化URL配置

---

### E024: 前后端企业类型定义不一致导致400错误

**发生时间**: 2026-03-20

**错误类型**: 前后端不一致

**错误描述**:
- 前端提交企业信息时返回400 Bad Request
- 原因：前端和后端的`enterprise_type`字段选项定义不一致

**发生场景**:
- 编辑企业信息，选择"股份有限公司"后保存
- 前端发送 `enterprise_type: "joint_stock"`，但后端没有这个选项

**错误信息**:
```
ERROR 2026-03-20 21:57:14,696 API异常: enterprise_type: "joint_stock" 不是合法选项。
WARNING 2026-03-20 21:57:14,722 Bad Request: /api/v1/enterprise/enterprises/1/
```

**问题对比**:
| 前端定义 | 后端定义（修复前） |
|---------|------------------|
| limited (有限责任公司) | supplier (供应商) |
| joint_stock (股份有限公司) | purchaser (采购方) |
| sole_proprietorship (个人独资企业) | agent (代理机构) |
| partnership (合伙企业) | other (其他) |
| other (其他) | |

**根本原因**:
- 前端定义的是**企业法律形式**（有限责任公司、股份有限公司等）
- 后端定义的是**企业业务角色**（供应商、采购方等）
- 这是两个完全不同的概念

**解决方案**:

1. 修改后端常量定义 `backend/core/constants.py`:
```python
# 修复前
ENTERPRISE_TYPE_SUPPLIER = 'supplier'
ENTERPRISE_TYPE_PURCHASER = 'purchaser'
ENTERPRISE_TYPE_AGENT = 'agent'
ENTERPRISE_TYPE_OTHER = 'other'

ENTERPRISE_TYPE_CHOICES = [
    (ENTERPRISE_TYPE_SUPPLIER, '供应商'),
    (ENTERPRISE_TYPE_PURCHASER, '采购方'),
    (ENTERPRISE_TYPE_AGENT, '代理机构'),
    (ENTERPRISE_TYPE_OTHER, '其他'),
]

# 修复后
ENTERPRISE_TYPE_LIMITED = 'limited'
ENTERPRISE_TYPE_JOINT_STOCK = 'joint_stock'
ENTERPRISE_TYPE_SOLE_PROPRIETORSHIP = 'sole_proprietorship'
ENTERPRISE_TYPE_PARTNERSHIP = 'partnership'
ENTERPRISE_TYPE_OTHER = 'other'

ENTERPRISE_TYPE_CHOICES = [
    (ENTERPRISE_TYPE_LIMITED, '有限责任公司'),
    (ENTERPRISE_TYPE_JOINT_STOCK, '股份有限公司'),
    (ENTERPRISE_TYPE_SOLE_PROPRIETORSHIP, '个人独资企业'),
    (ENTERPRISE_TYPE_PARTNERSHIP, '合伙企业'),
    (ENTERPRISE_TYPE_OTHER, '其他'),
]
```

2. 修改模型字段 `backend/apps/enterprise/models.py`:
```python
# 修复前
enterprise_type = models.CharField('企业类型', max_length=20, 
                                    choices=ENTERPRISE_TYPE_CHOICES, default='supplier')

# 修复后
enterprise_type = models.CharField('企业类型', max_length=25, 
                                    choices=ENTERPRISE_TYPE_CHOICES, blank=True, null=True)
```

3. 更新服务文件 `backend/apps/enterprise/services.py`，移除硬编码的默认值

4. 执行数据库迁移:
```bash
python manage.py makemigrations enterprise --name update_enterprise_type_choices
python manage.py migrate enterprise
```

**预防措施**:
1. 前后端枚举/选项类字段必须保持一致
2. 新增选项时先检查后端是否已定义
3. 使用共享的类型定义文件或API获取选项列表
4. 前端可通过API获取后端定义的选项，避免硬编码

**相关文件**:
- `backend/core/constants.py` - 企业类型常量定义
- `backend/apps/enterprise/models.py` - Enterprise模型
- `backend/apps/enterprise/services.py` - 企业服务
- `frontend/src/views/CompanyInfo.vue` - 企业信息表单

---

### E025: 编辑企业保存后未正确刷新选中项

**发生时间**: 2026-03-20

**错误类型**: 前端逻辑

**错误描述**:
- 编辑企业信息保存成功后，页面显示的不是刚编辑的企业
- 原因：保存成功后调用`fetchEnterpriseList()`会自动选中列表第一个企业

**发生场景**:
- 编辑企业信息，点击保存
- 保存成功后，页面刷新但显示的是列表第一个企业，而不是刚才编辑的企业

**错误代码**:
```javascript
const saveEnterprise = async () => {
  try {
    if (isEdit.value) {
      await enterpriseApi.updateEnterprise(enterpriseForm.id, enterpriseForm)
    } else {
      await enterpriseApi.createEnterprise(enterpriseForm)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchEnterpriseList()  // 问题：会自动选中第一个企业
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message))
  }
}

const fetchEnterpriseList = async () => {
  const res = await enterpriseApi.getEnterprises()
  enterpriseList.value = res.data?.list || res.results || res.data || []
  if (enterpriseList.value.length > 0) {
    selectEnterprise(enterpriseList.value[0])  // 问题：总是选中第一个
  }
}
```

**解决方案**:
修改保存逻辑，保存成功后重新选中刚才编辑/创建的企业:
```javascript
const saveEnterprise = async () => {
  try {
    const savedId = enterpriseForm.id
    if (isEdit.value) {
      await enterpriseApi.updateEnterprise(enterpriseForm.id, enterpriseForm)
    } else {
      const res = await enterpriseApi.createEnterprise(enterpriseForm)
      enterpriseForm.id = res.data?.id || res.id  // 获取新建企业ID
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchEnterpriseList()
    // 重新选中刚才编辑/创建的企业
    if (enterpriseForm.id) {
      const savedEnterprise = enterpriseList.value.find(e => e.id === enterpriseForm.id)
      if (savedEnterprise) {
        selectEnterprise(savedEnterprise)
      }
    }
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message))
  }
}
```

**预防措施**:
1. 保存成功后需要保持用户当前的操作上下文
2. 刷新列表后应重新选中之前操作的项目
3. 新建项目时需要从响应中获取新ID
4. 使用`await`确保列表刷新完成后再选中

**相关文件**:
- `frontend/src/views/CompanyInfo.vue` - 企业信息管理页面

---

### E026: Django ORM在异步上下文中调用错误

**发生时间**: 2026-03-20

**错误类型**: 异步上下文

**错误描述**:
- 调用企业信息采集API返回400 Bad Request
- 原因：在async上下文中直接调用Django ORM同步操作

**发生场景**:
- 调用 `/api/v1/enterprise/enterprises/collect_info/` 接口时
- EnterpriseInfoCollectorAgent的`_save_to_database`方法中直接使用了Django ORM同步操作

**错误信息**:
```
ERROR 2026-03-20 22:27:49,507 enterprise_collector_agent 5236 19484 企业信息采集失败: You cannot call this from an async context - use a thread or sync_to_async.
```

**错误代码**:
```python
# 错误写法 - 在async方法中直接调用Django ORM
async def _save_to_database(self, data: Dict, update_existing: bool = False) -> int:
    from apps.enterprise.models import Enterprise, EnterpriseQualification
    
    enterprise = Enterprise.objects.get(credit_code=credit_code)  # 同步ORM调用
    enterprise.save()  # 同步ORM调用
```

**解决方案**:
使用`asgiref.sync.sync_to_async`装饰器包装同步数据库操作：

```python
from asgiref.sync import sync_to_async

async def _save_to_database(self, data: Dict, update_existing: bool = False) -> int:
    return await self._save_enterprise_sync(data, update_existing)

@sync_to_async
def _save_enterprise_sync(self, data: Dict, update_existing: bool = False) -> int:
    """同步保存企业数据到数据库（通过sync_to_async包装后可在异步上下文调用）"""
    from apps.enterprise.models import Enterprise, EnterpriseQualification
    
    enterprise = Enterprise.objects.get(credit_code=credit_code)
    enterprise.save()
    return enterprise.id
```

**预防措施**:
1. 在async函数中调用Django ORM必须使用`sync_to_async`装饰器
2. 或者使用`database_sync_to_async`（来自channels.db）
3. 将所有数据库操作封装到单独的同步方法中，然后用装饰器包装

**相关文件**:
- `backend/openclaw/agents/enterprise_collector_agent.py` - 企业信息采集Agent

---

### E027: 企业信息采集SSL证书验证失败

**发生时间**: 2026-03-20

**错误类型**: SSL证书验证

**错误描述**:
- 调用企业信息采集API返回400 Bad Request
- 原因：访问国家企业信用信息公示系统(gsxt.gov.cn)时SSL证书验证失败

**发生场景**:
- 调用 `/api/v1/enterprise/enterprises/collect_info/` 接口时
- 尝试从爱企查和国家企业信用信息公示系统采集企业信息

**错误信息**:
```
ERROR 2026-03-20 22:52:57,757 公示系统采集失败: Cannot connect to host www.gsxt.gov.cn:443 ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1007)')]
WARNING 2026-03-20 22:52:57,763 企业信息采集失败: 无法从公开渠道获取企业信息: 上海天齐智能建筑股份有限公司
```

**解决方案**:
在aiohttp请求中禁用SSL证书验证：

```python
import ssl
import aiohttp

# 创建SSL上下文，禁用证书验证
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 使用自定义SSL上下文创建连接器
connector = aiohttp.TCPConnector(ssl=ssl_context)

# 使用连接器创建会话
async with aiohttp.ClientSession(connector=connector) as session:
    # 发送请求...
```

**预防措施**:
1. 对于内部工具或开发环境，可以禁用SSL验证
2. 生产环境应考虑使用代理或配置正确的证书
3. 添加友好的错误提示，建议用户手动录入信息

**相关文件**:
- `backend/openclaw/skills/collector/enterprise_collector.py` - 企业信息采集技能
- `backend/apps/enterprise/views.py` - 企业视图

---

### E028: 401 Unauthorized - Token过期未自动刷新

**发生时间**: 2026-03-21

**错误类型**: 认证错误

**错误描述**:
- 前端API请求返回401 Unauthorized错误
- 原因：JWT access token过期后未自动刷新
- 用户需要重新登录才能继续使用系统

**发生场景**:
- 页面加载时自动请求 `/api/v1/notifications/unread-count/`
- 页面加载时自动请求 `/api/v1/enterprise/enterprises/`
- Token过期后所有需要认证的API请求

**错误信息**:
```
GET http://localhost:8081/api/v1/notifications/unread-count/ 401 (Unauthorized)
GET http://localhost:8081/api/v1/enterprise/enterprises/ 401 (Unauthorized)
```

**解决方案**:
1. 在前端请求拦截器中添加token自动刷新机制
2. 在user store中保存refresh_token
3. 当收到401错误时，自动使用refresh_token获取新的access_token

**核心代码**:
```javascript
// request.js - Token自动刷新机制
let isRefreshing = false
let refreshSubscribers = []

async function refreshToken() {
  const refreshTokenValue = localStorage.getItem('refresh_token')
  if (!refreshTokenValue) return null
  
  const response = await axios.post('/api/v1/auth/token/refresh/', {
    refresh: refreshTokenValue
  })
  
  const newAccessToken = response.data.access
  userStore.setToken(newAccessToken)
  
  if (response.data.refresh) {
    localStorage.setItem('refresh_token', response.data.refresh)
  }
  
  return newAccessToken
}

// 响应拦截器处理401错误
if (status === 401 && !originalRequest._retry) {
  originalRequest._retry = true
  const newToken = await refreshToken()
  if (newToken) {
    originalRequest.headers.Authorization = `Bearer ${newToken}`
    return request(originalRequest)
  }
}
```

**预防措施**:
1. 登录时同时保存access_token和refresh_token
2. 退出登录时清除所有token
3. Token过期前主动刷新（可选优化）

**相关文件**:
- `frontend/src/utils/request.js` - 请求拦截器
- `frontend/src/store/user.js` - 用户状态管理

---

### E029: Element Plus图标组件未导入

**发生时间**: 2026-03-21

**错误类型**: 前端组件

**错误描述**:
- Vue警告：Failed to resolve component: Search, Files
- 控制台显示多个图标组件无法解析

**发生场景**:
- 在 `VectorLibrary.vue` 中使用了多个 Element Plus 图标组件
- 但未在 `<script setup>` 中从 `@element-plus/icons-vue` 导入

**错误信息**:
```
[Vue warn]: Failed to resolve component: Search
[Vue warn]: Failed to resolve component: Files
```

**解决方案**:
```javascript
// 在 <script setup> 中添加图标导入
import { Search, Files, Upload, CircleCheck, Star, Download, DocumentCopy } from '@element-plus/icons-vue'
```

**预防措施**:
1. 使用 Element Plus 图标时，必须从 `@element-plus/icons-vue` 导入
2. 常用图标：Search, Files, Upload, Download, Star, CircleCheck, DocumentCopy, Plus, Edit, Delete, View
3. 可在 `main.js` 中全局注册常用图标，避免每次导入

**相关文件**:
- `frontend/src/views/vectorlib/VectorLibrary.vue`
- `frontend/src/main.js` - 可在此全局注册图标

---

### E030: 模型choices属性引用错误

**发生时间**: 2026-03-21

**错误类型**: 后端模型

**错误描述**:
- API返回500 Internal Server Error
- 原因：代码引用了模型上不存在的 `DOCUMENT_TYPE_CHOICES` 属性

**发生场景**:
- `vectorlib/views.py` 的 `statistics` 方法中
- 代码写为 `BidDocumentLibrary.DOCUMENT_TYPE_CHOICES`
- 但模型中定义的是从 `core.constants` 导入的 `VECTOR_DOC_TYPE_CHOICES`

**错误信息**:
```
AttributeError: type object 'BidDocumentLibrary' has no attribute 'DOCUMENT_TYPE_CHOICES'
```

**解决方案**:
```python
# 错误写法
for choice in BidDocumentLibrary.DOCUMENT_TYPE_CHOICES:

# 正确写法 - 从constants模块导入
from core.constants import VECTOR_DOC_TYPE_CHOICES
for choice in VECTOR_DOC_TYPE_CHOICES:
```

**预防措施**:
1. 模型的 `choices` 参数值来自 `core/constants.py`，不是模型自身的属性
2. 需要遍历choices时，直接从 `core.constants` 导入对应的常量
3. 常量命名规则：`模型用途_CHOICES`，如 `VECTOR_DOC_TYPE_CHOICES`

**相关文件**:
- `backend/apps/vectorlib/views.py`
- `backend/apps/vectorlib/models.py`
- `backend/core/constants.py`

---

### E031: Element Plus不存在的Scan图标

**发生时间**: 2026-03-21

**错误类型**: 前端图标

**错误描述**:
- Vue警告：Invalid vnode type when creating vnode: undefined
- 控制台显示 `Proxy(Object) {…}` 错误
- 原因：Element Plus图标库中不存在 `Scan` 图标

**发生场景**:
- 在 `CompanyDocuments.vue` 中使用了 `Scan` 图标
- 在 `main.js` 中导入并注册了 `Scan` 图标
- 但 Element Plus 图标库中没有这个图标

**错误信息**:
```
Invalid vnode type when creating vnode: undefined. Proxy(Object) {…}
at <ElIcon>
at <ElButton>
at <CompanyDocuments>
```

**解决方案**:
将 `Scan` 图标替换为存在的 `Camera` 图标：

```javascript
// main.js 和 CompanyDocuments.vue
// 错误写法
import { Scan } from '@element-plus/icons-vue'

// 正确写法
import { Camera } from '@element-plus/icons-vue'
```

**Element Plus 可用的类似图标**:
- `Camera` - 相机图标（推荐替代Scan）
- `View` - 查看图标
- `Search` - 搜索图标
- `ZoomIn` - 放大图标

**预防措施**:
1. 使用 Element Plus 图标前，先查阅官方图标列表
2. 官方图标列表：https://element-plus.org/en-US/component/icon.html
3. 常见不存在的图标：`Scan`（用`Camera`替代）
4. 如果图标导入为 `undefined`，说明该图标不存在

**相关文件**:
- `frontend/src/main.js` - 全局图标注册
- `frontend/src/views/company/CompanyDocuments.vue` - 使用图标

---

### E032: 企业类型选项与后端定义不匹配

**发生时间**: 2026-03-21

**错误类型**: 前后端不一致

**错误描述**:
- 前端调用PATCH `/api/v1/enterprise/enterprises/4/` 返回400 Bad Request
- 原因：前端企业类型下拉选项包含后端未定义的值

**发生场景**:
- 用户在企业编辑表单中选择"国有企业"、"集体企业"或"外商投资企业"
- 提交保存时后端验证失败，因为这些选项值不在后端ENTERPRISE_TYPE_CHOICES中

**错误信息**:
```
enterprise.js:15 PATCH http://localhost:8081/api/v1/enterprise/enterprises/4/ 400 (Bad Request)
```

**前后端对比**:

| 前端选项(错误) | 后端定义(正确) |
|---------------|---------------|
| limited | limited ✅ |
| joint_stock | joint_stock ✅ |
| sole_proprietorship | sole_proprietorship ✅ |
| partnership | partnership ✅ |
| state_owned | ❌ 不存在 |
| collective | ❌ 不存在 |
| foreign | ❌ 不存在 |
| other | other ✅ |

**解决方案**:
移除前端多余的企业类型选项，保持与后端一致：

```vue
<!-- CompanyInfo.vue -->
<el-select v-model="enterpriseForm.enterprise_type">
  <el-option label="有限责任公司" value="limited" />
  <el-option label="股份有限公司" value="joint_stock" />
  <el-option label="个人独资企业" value="sole_proprietorship" />
  <el-option label="合伙企业" value="partnership" />
  <el-option label="其他" value="other" />
</el-select>
```

**预防措施**:
1. 前端下拉选项必须与后端choices定义保持一致
2. 后端choices定义位置：`backend/core/constants.py` - `ENTERPRISE_TYPE_CHOICES`
3. 新增选项时需同时修改前后端代码

**相关文件**:
- `backend/core/constants.py` - 企业类型常量定义
- `frontend/src/views/CompanyInfo.vue` - 企业编辑表单

---

## 功能更新记录

### F002: 系统重构 - 清理废弃代码与统一服务

**更新时间**: 2026-03-20

**更新内容**:
1. **清理废弃的CompanyInfo模型**
   - 移除前端对CompanyInfo API的调用
   - 更新前端CompanyInfo.vue使用Enterprise API
   - 更新后端scheduler_views.py使用Enterprise模型
   - 更新qualification_matcher.py使用Enterprise和EnterpriseBidConfig

2. **统一LLM服务**
   - 所有LLM调用统一使用UnifiedLLMService
   - 更新bid_generator.py使用unified_llm_service
   - 更新vectorlib/views.py使用unified_llm_service

3. **缓存配置迁移到Redis**
   - 已确认使用Redis作为缓存后端
   - 配置位于config/settings/base.py

4. **前端TypeScript支持**
   - 添加tsconfig.json配置
   - 添加vite-env.d.ts类型声明
   - 添加types/index.ts类型定义文件
   - 更新package.json添加TypeScript依赖

5. **完善错误处理**
   - 新增utils/exceptions.py自定义异常类
   - 新增utils/exception_handler.py全局异常处理

**修改文件**:
1. `frontend/src/views/CompanyInfo.vue` - 使用Enterprise API
2. `frontend/src/api/document.js` - 移除CompanyInfo相关API
3. `frontend/src/router/index.js` - 更新路由名称
4. `frontend/tsconfig.json` - TypeScript配置
5. `frontend/src/vite-env.d.ts` - 类型声明
6. `frontend/src/types/index.ts` - 类型定义
7. `frontend/package.json` - 添加TypeScript依赖
8. `backend/apps/documents/views.py` - 清理CompanyInfo代码
9. `backend/apps/documents/serializers.py` - 清理CompanyInfo代码
10. `backend/apps/documents/urls.py` - 清理CompanyInfo路由
11. `backend/apps/documents/admin.py` - 清理CompanyInfo注册
12. `backend/apps/crawler/scheduler_views.py` - 使用Enterprise模型
13. `backend/apps/vectorlib/views.py` - 使用UnifiedLLMService
14. `backend/openclaw/skills/generator/bid_generator.py` - 使用UnifiedLLMService
15. `backend/services/qualification_matcher.py` - 使用Enterprise模型
16. `backend/utils/exceptions.py` - 新增自定义异常类
17. `backend/utils/exception_handler.py` - 新增全局异常处理

**注意事项**:
- 前端需要重新安装依赖：`npm install`
- 后端需要确保Redis服务运行正常

---

### F001: 采集公告改为每天全量采集

**更新时间**: 2026-03-20

**更新内容**:
- 新增采集模式字段 `crawl_mode`，支持全量采集和增量采集两种模式
- 默认采集时间改为每天6点执行
- 全量采集模式下默认采集50页，增量采集模式下默认采集5页
- **新增当天日期过滤**：全量采集模式下自动添加当天日期范围参数（start_date 和 end_date）

**修改文件**:
1. `backend/apps/crawler/scheduler_models.py` - 新增 `crawl_mode` 字段
2. `backend/apps/crawler/scheduler_serializers.py` - 序列化器支持新字段
3. `backend/crawler/tasks.py` - 根据采集模式调整采集页数，添加当天日期参数
4. `backend/apps/crawler/services.py` - 支持日期范围参数传递
5. `backend/apps/crawler/models.py` - 更新URL模式帮助文本，支持日期变量
6. `frontend/src/views/ScheduleList.vue` - 前端界面支持采集模式选择

**数据库迁移**:
```bash
python manage.py makemigrations crawler
python manage.py migrate crawler
```

**使用说明**:
- 全量采集：采集当天发布的所有公告，自动设置日期范围为当天
- 增量采集：仅采集最新数据，不限制日期范围

**URL模式变量支持**:
- `{page}` - 页码
- `{keyword}` - 搜索关键词
- `{category}` - 分类
- `{start_date}` - 开始日期（YYYY-MM-DD格式）
- `{end_date}` - 结束日期（YYYY-MM-DD格式）

---

## 常见问题速查表

### Django相关

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 500错误 | 模型字段未迁移 | 执行 makemigrations 和 migrate |
| 字段不存在 | 迁移未执行 | 检查迁移文件，执行迁移 |
| 外键错误 | 关联模型不存在 | 确保关联模型已创建并迁移 |
| CORS错误 | 跨域配置缺失 | 配置django-cors-headers |
| NoReverseMatch | URL命名空间未注册 | 检查urls.py配置 |
| 表不存在 | 应用未迁移 | 执行对应应用的迁移 |

### Vue/前端相关

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 接口404 | 路由未配置 | 检查urls.py和api路径 |
| 数据不显示 | 响应格式不匹配 | 检查序列化器字段 |
| 文件上传失败 | 未使用FormData | 使用FormData格式上传 |
| Token无效 | Token过期或无效 | 清除Token重新登录 |
| 401 Unauthorized | Token过期未刷新 | 检查request.js的token刷新机制 |
| 401持续出现 | refresh_token未保存 | 检查user.js登录时是否保存refresh_token |

### 认证相关

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 401 Unauthorized | access_token过期 | 自动使用refresh_token刷新 |
| 刷新失败 | refresh_token过期 | 清除所有token，重新登录 |
| 并发请求401 | 多个请求同时刷新token | 使用队列管理，只刷新一次 |
| 登录后仍401 | token未正确保存 | 检查localStorage中token值 |

### 数据库相关

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 连接失败 | 配置错误 | 检查.env数据库配置 |
| 表不存在 | 迁移未执行 | 执行数据库迁移 |
| 字段类型错误 | 模型定义不匹配 | 修改模型并迁移 |
| 字段不存在 | 新字段未迁移 | 执行makemigrations和migrate |

### Redis相关

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 连接失败 | Redis服务未启动 | 启动Redis服务 |
| 参数错误 | 版本不兼容 | 检查参数格式 |

---

## 操作前检查清单

每次开发前请确认：

- [ ] 检查本文档是否有相关错误记录
- [ ] 确认数据库迁移是否已执行
- [ ] 确认服务是否正常运行
- [ ] 确认API路由是否已配置
- [ ] 确认Token是否有效
- [ ] 确认refresh_token是否正确保存
- [ ] 检查前端请求拦截器是否包含token刷新逻辑

---

## 记录规范

新增错误记录时请遵循以下规范：

1. **编号**: E + 三位数字，如E001、E002
2. **去重检查**: 记录前先搜索是否已存在相同问题
3. **信息完整**: 必须包含错误描述、场景、解决方案
4. **更新索引**: 在索引表中添加新记录
5. **添加预防措施**: 避免再次发生

---

## 自动化错误记录系统

本项目已集成自动化错误记录系统，支持多种方式自动记录错误。

### 1. Python装饰器方式

```python
from utils.error_decorators import catch_and_log, async_catch_and_log

# 同步函数装饰器
@catch_and_log(
    scenario="调用用户API时",
    solution="检查用户是否存在",
    prevention="添加用户存在性检查",
    related_files=["apps/users/views.py"]
)
def get_user(user_id):
    return User.objects.get(id=user_id)

# 异步函数装饰器
@async_catch_and_log(
    scenario="异步调用LLM服务时",
    solution="检查LLM服务配置"
)
async def call_llm(prompt):
    return await llm_service.chat(prompt)
```

### 2. 上下文管理器方式

```python
from utils.error_decorators import ErrorContext

with ErrorContext("数据库操作", "检查数据库连接"):
    result = User.objects.get(id=1)
```

### 3. 直接调用服务

```python
from utils.error_logger_service import error_logger

# 记录错误
error_logger.log_error(
    error_type="数据库迁移",
    description="字段不存在",
    scenario="调用API时",
    error_message="column xxx does not exist",
    solution="执行 makemigrations 和 migrate",
    prevention="修改模型后立即执行迁移"
)

# 从异常对象记录
try:
    # some code
except Exception as e:
    error_logger.log_exception(e, scenario="执行任务时", solution="检查错误原因")
```

### 4. Django管理命令

```bash
# 列出最近的错误
python manage.py error_log list --limit=20

# 搜索错误
python manage.py error_log search "数据库"

# 显示统计
python manage.py error_log stats

# 添加错误记录
python manage.py error_log add --type="数据库迁移" --desc="字段不存在" --scenario="调用API时" --solution="执行迁移"
```

### 5. API接口

```bash
# 获取错误列表
GET /api/v1/error-log/?limit=10

# 搜索错误
GET /api/v1/error-log/search/?keyword=数据库

# 添加错误记录
POST /api/v1/error-log/add/
{
    "error_type": "数据库迁移",
    "description": "字段不存在",
    "scenario": "调用API时",
    "error_message": "column xxx does not exist",
    "solution": "执行迁移"
}

# 获取统计信息
GET /api/v1/error-log/stats/
```

### 自动化特性

- **自动去重**: 相同错误不会重复记录
- **自动编号**: 新错误自动分配编号
- **自动类型检测**: 根据错误信息自动识别错误类型
- **线程安全**: 支持多线程环境使用

---

### E033: 企业保存400错误 - 数字字段空字符串

**发生时间**: 2026-03-21

**错误类型**: 前端数据格式

**错误描述**:
- 前端调用企业更新API时返回400 Bad Request
- 错误信息：`staff_count: 请填写合法的整数值。; insured_count: 请填写合法的整数值。`
- 原因：前端发送空字符串`''`，但后端IntegerField不接受空字符串，只接受`null`

**发生场景**:
- 在企业编辑页面点击保存按钮
- 数字类型输入框（员工人数、参保人数等）为空时

**错误信息**:
```
PATCH /api/v1/enterprise/enterprises/4/ 400 (Bad Request)
{"code":400,"message":"staff_count: 请填写合法的整数值。; insured_count: 请填写合法的整数值。","data":null}
```

**解决方案**:
修改前端`saveEnterprise`函数，增强数字字段的处理逻辑：

```javascript
const numericFields = ['registered_capital', 'staff_count', 'insured_count', 'auto_bid_threshold']
numericFields.forEach(field => {
  const value = submitData[field]
  if (value === '' || value === undefined || value === null || (typeof value === 'string' && value.trim() === '')) {
    submitData[field] = null
  } else if (typeof value === 'string' && value !== '') {
    const num = Number(value)
    submitData[field] = isNaN(num) ? null : num
  } else if (typeof value === 'number' && isNaN(value)) {
    submitData[field] = null
  }
})
```

**预防措施**:
1. 数字类型字段发送空值时，必须发送`null`而不是空字符串
2. 前端提交数据前，统一处理空字符串转`null`
3. 后端IntegerField只接受整数或`null`，不接受空字符串

**相关文件**:
- `frontend/src/views/CompanyInfo.vue`
- `backend/apps/enterprise/serializers.py`

---

### E034: 企业信息字段移除

**发生时间**: 2026-03-22

**错误描述**:
企业信息中存在冗余字段，需要移除以下6个字段：
- 企业简称 (short_name)
- 注册号 (registration_number)
- 传真 (fax)
- 企业网站 (website)
- 国标行业代码 (industry_code)
- 所属行业 (industry)

**发生场景**:
企业信息管理模块字段精简优化

**解决方案**:

1. 后端模型修改 (`backend/apps/enterprise/models.py`):
```python
# 移除以下字段
short_name = models.CharField('企业简称', max_length=100, blank=True, null=True)
registration_number = models.CharField('注册号', max_length=50, blank=True, null=True)
fax = models.CharField('传真', max_length=50, blank=True, null=True)
website = models.URLField('企业网站', max_length=200, blank=True, null=True)
industry = models.CharField('所属行业', max_length=100, blank=True, null=True)
industry_code = models.CharField('国标行业代码', max_length=50, blank=True, null=True)
```

2. 后端序列化器修改 (`backend/apps/enterprise/serializers.py`):
```python
# EnterpriseListSerializer fields 移除 short_name, industry
fields = ['id', 'name', 'enterprise_type', 'enterprise_type_display',
          'credit_code', 'province', 'city', 'contact_person', 'contact_phone',
          'is_active', 'is_verified', 'qualification_count', 
          'performance_count', 'created_at']
```

3. 后端Admin修改 (`backend/apps/enterprise/admin.py`):
```python
# list_display 移除 short_name
# search_fields 移除 short_name, industry
# fieldsets 移除相关字段
```

4. 前端表单修改 (`frontend/src/views/CompanyInfo.vue`):
- 移除详情显示中的企业简称、所属行业、国标行业、网址字段
- 移除表单中的企业简称、注册号、企业网站、传真、所属行业、国标行业代码字段
- 更新 defaultForm 移除对应字段
- 更新 emptyStringFields 移除对应字段

5. 数据库迁移:
```bash
python manage.py makemigrations enterprise --name remove_unused_fields
python manage.py migrate enterprise
```

**预防措施**:
1. 移除字段时需同步更新：模型、序列化器、Admin、前端表单
2. 移除字段后必须创建并执行数据库迁移
3. 更新相关模板变量引用（如 to_template_variables 方法）

**相关文件**:
- `backend/apps/enterprise/models.py`
- `backend/apps/enterprise/serializers.py`
- `backend/apps/enterprise/admin.py`
- `frontend/src/views/CompanyInfo.vue`
- `backend/apps/enterprise/migrations/0007_remove_unused_fields.py`

---

### E035: 序列化器引用模型中不存在的字段

**发生时间**: 2026-03-22

**错误类型**: 序列化器字段错误

**错误描述**:
- API返回500 Internal Server Error
- 原因：`EnterpriseListSerializer` 的 fields 列表中包含 `short_name` 和 `industry` 字段，但 `Enterprise` 模型中这些字段已被移除

**发生场景**:
- 在E034中移除了Enterprise模型的short_name、industry等字段
- 但序列化器中的fields列表未同步更新，仍然引用了这些字段

**错误信息**:
```
GET http://localhost:8081/api/v1/enterprise/enterprises/ 500 (Internal Server Error)

django.core.exceptions.ImproperlyConfigured: Field name `short_name` is not valid for model `Enterprise`.
django.core.exceptions.ImproperlyConfigured: Field name `industry` is not valid for model `Enterprise`.
```

**解决方案**:

修改 `backend/apps/enterprise/serializers.py` 中的 `EnterpriseListSerializer`:
```python
# 修改前（错误）
class Meta:
    model = Enterprise
    fields = ['id', 'name', 'short_name', 'enterprise_type', 'enterprise_type_display',
              'credit_code', 'province', 'city', 'contact_person', 'contact_phone',
              'legal_person', 'industry', 'is_active', 'is_verified', 'qualification_count', 
              'performance_count', 'created_at']

# 修改后（正确）- 移除 short_name 和 industry
class Meta:
    model = Enterprise
    fields = ['id', 'name', 'enterprise_type', 'enterprise_type_display',
              'credit_code', 'province', 'city', 'contact_person', 'contact_phone',
              'legal_person', 'is_active', 'is_verified', 'qualification_count', 
              'performance_count', 'created_at']
```

**预防措施**:
1. 移除模型字段时，必须同步检查并更新所有序列化器的fields列表
2. 使用 `fields = '__all__'` 时会自动同步，但明确指定fields时需手动维护
3. 修改模型后应立即测试相关API，确保无遗漏

**相关文件**:
- `backend/apps/enterprise/serializers.py`
- `backend/apps/enterprise/models.py`

---

### E036: el-descriptions标签换行和宽度不一致

**发生时间**: 2026-03-22

**错误类型**: 前端样式

**错误描述**:
- 企业详情页面基本信息Tab中的字段标签文字换行显示
- 不同标签宽度不一致，影响页面美观
- 原因：el-descriptions组件默认会根据文字内容自动计算宽度

**发生场景**:
- 访问 `/company` 页面查看企业详情
- 标签如"统一社会信用代码"等较长文字自动换行

**解决方案**:

在 `CompanyInfo.vue` 的样式中添加固定宽度和禁止换行：

```css
.info-descriptions :deep(.el-descriptions__label) {
  font-weight: 500;
  color: #606266;
  background-color: #fafafa;
  white-space: nowrap;  /* 禁止换行 */
  width: 110px;         /* 固定宽度 */
}
```

**预防措施**:
1. 使用el-descriptions组件时，建议统一设置标签宽度
2. 添加 `white-space: nowrap` 防止中文标签换行
3. 根据最长标签文字确定合适的固定宽度

**相关文件**:
- `frontend/src/views/CompanyInfo.vue`

---

### E037: VECTOR_STATUS_CHOICES重复定义

**发生时间**: 2026-03-22

**错误类型**: 代码重复

**错误描述**:
- `core/constants.py` 和 `apps/crawler/models.py` 中都定义了 `VECTOR_STATUS_CHOICES`
- 两处定义的值不同，可能导致状态不一致

**发生场景**:
- 代码审查时发现重复定义

**解决方案**:

1. 删除 `apps/crawler/models.py` 中的重复定义
2. 统一从 `core/constants.py` 导入

```python
# apps/crawler/models.py 修改前
VECTOR_STATUS_CHOICES = [
    ('pending', '待处理'),
    ('completed', '已完成'),
    ('failed', '失败'),
]

# 修改后
from core.constants import (
    VECTOR_STATUS_CHOICES,
    LOG_LEVEL_CHOICES,
)
```

**预防措施**:
1. 所有状态常量统一在 `core/constants.py` 中定义
2. 其他模块通过导入使用，不要重复定义
3. 定期检查代码重复

**相关文件**:
- `core/constants.py`
- `apps/crawler/models.py`

---

### E038: Agent类重复定义

**发生时间**: 2026-03-22

**错误类型**: 代码重复

**错误描述**:
- `professional_agents.py` 和 `bid_document_agents.py` 中都定义了 `BidDocumentGeneratorAgent` 类
- `professional_agents.py` 和 `bid_tracker_agents.py` 中都定义了 `BidReviewAgent` 类
- 重复定义导致代码冗余，且可能导致功能不一致

**发生场景**:
- 代码审查时发现重复定义

**解决方案**:

1. 保留 `bid_document_agents.py` 中使用 `BaseBidAgent` 基类的专业版本
2. 删除 `professional_agents.py` 中的重复定义
3. 改为从 `bid_document_agents.py` 导入

```python
# professional_agents.py 修改后
from openclaw.agents.bid_document_agents import (
    BidDocumentGeneratorAgent,
    BidDocumentReviewerAgent
)
```

**预防措施**:
1. 新增类前先搜索是否已存在相同功能的类
2. 使用基类继承减少代码重复
3. 定期进行代码审查

**相关文件**:
- `openclaw/agents/professional_agents.py`
- `openclaw/agents/bid_document_agents.py`
- `openclaw/agents/bid_tracker_agents.py`

---

### E039: 未使用代码文件

**发生时间**: 2026-03-22

**错误类型**: 代码冗余

**错误描述**:
- 多个文件定义了代码但从未被调用
- 增加了代码维护成本和项目体积

**发生场景**:
- 代码审查时发现未使用的文件

**解决方案**:

删除以下未使用的文件：

| 文件 | 行数 | 原因 |
|------|------|------|
| `apps/enterprise/repositories.py` | 535行 | 未被任何代码调用 |
| `core/repository/base.py` | - | 仅被repositories.py使用 |
| `core/viewset/base.py` | - | 未被任何代码引用 |
| `core/service/base.py` | - | 未被任何代码引用 |
| `core/throttling.py` | - | 未被任何代码引用 |
| `core/validators.py` | - | 未被任何代码引用 |
| `core/versioning.py` | - | 未被任何代码引用 |
| `apps/search_config/` 目录 | - | 仅包含编译缓存，无源代码 |

**预防措施**:
1. 定期检查未使用的代码
2. 使用工具如 `pylint` 或 `vulture` 检测未使用代码
3. 删除代码前确认无引用

**相关文件**:
- `apps/enterprise/repositories.py` (已删除)
- `core/repository/` (已删除)
- `core/viewset/` (已删除)
- `core/service/` (已删除)
- `apps/search_config/` (已删除)

---

### E040: 状态枚举定义分散

**发生时间**: 2026-03-22

**错误类型**: 代码分散

**错误描述**:
- 多个文件中独立定义了状态枚举类
- 相同功能的枚举分散在不同位置，难以维护

**发生场景**:
- 代码审查时发现分散的枚举定义

**涉及的枚举**:

| 枚举类 | 原位置 | 统一后位置 |
|--------|--------|-----------|
| `AgentStatus` | `openclaw/base_agent.py` | `core/constants.py` |
| `AgentType` | `openclaw/base_agent.py` | `core/constants.py` |
| `AgentCapability` | `openclaw/base_agent.py` | `core/constants.py` |
| `ExecutionStatus` | `openclaw/architecture/embedded.py` | `core/constants.py` |
| `WorkflowStatus` | `openclaw/architecture/pi.py` | `core/constants.py` |
| `StageStatus` | `openclaw/architecture/pi.py` | `core/constants.py` |
| `CrawlStrategy` | `crawler/pyppeteer_crawler.py` | `core/constants.py` |
| `CrawlStatus` | `crawler/pyppeteer_crawler.py` | `core/constants.py` |

**解决方案**:

1. 将所有枚举定义统一到 `core/constants.py`
2. 更新各文件的导入语句

```python
# 修改前 (各文件独立定义)
from enum import Enum

class AgentStatus(Enum):
    IDLE = 'idle'
    RUNNING = 'running'
    ...

# 修改后 (统一导入)
from core.constants import AgentStatus, AgentType, AgentCapability
```

**预防措施**:
1. 所有状态枚举统一在 `core/constants.py` 中定义
2. 新增枚举前先检查是否已存在
3. 使用 `from core.constants import xxx` 导入

**相关文件**:
- `core/constants.py`
- `openclaw/base_agent.py`
- `openclaw/architecture/embedded.py`
- `openclaw/architecture/pi.py`
- `crawler/pyppeteer_crawler.py`
- `crawler/stealth_crawler.py`

---

### E041: 爬虫执行接口缺少权限控制

**发生时间**: 2026-03-22

**错误类型**: 安全漏洞

**错误描述**:
- `CrawlerExecuteView` 和 `CrawlerSyncExecuteView` 仅使用 `IsAuthenticated` 权限
- 任何登录用户都可以执行爬虫任务，存在安全风险

**发生场景**:
- 全面安全检查时发现

**解决方案**:

```python
# 修改前
class CrawlerExecuteView(APIView):
    permission_classes = [IsAuthenticated]

# 修改后
from utils.permissions import IsAdminUser

class CrawlerExecuteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
```

**预防措施**:
1. 敏感操作接口必须添加管理员权限
2. 定期进行安全审计

**相关文件**:
- `backend/apps/tenders/views.py`

---

### E042: N+1查询问题导致性能下降

**发生时间**: 2026-03-22

**错误类型**: 性能问题

**错误描述**:
- 多个ViewSet的queryset未使用 `select_related` 或 `prefetch_related`
- 导致列表查询时产生大量数据库查询

**发生场景**:
- 性能优化检查时发现

**涉及的ViewSet**:

| ViewSet | 修复前 | 修复后 |
|---------|--------|--------|
| `EnterpriseQualificationViewSet` | `.all()` | `.select_related('enterprise')` |
| `EnterprisePerformanceViewSet` | `.all()` | `.select_related('enterprise')` |
| `EnterpriseContactViewSet` | `.all()` | `.select_related('enterprise')` |
| `EnterpriseBidConfigViewSet` | `.all()` | `.select_related('enterprise')` |
| `EnterpriseMatchRuleViewSet` | `.all()` | `.select_related('enterprise')` |
| `EnterpriseMatchResultViewSet` | `.all()` | `.select_related('enterprise')` |
| `EnterpriseDocumentViewSet` | `.all()` | `.select_related('enterprise', 'created_by')` |
| `EnterpriseKeyPersonnelViewSet` | `.all()` | `.select_related('enterprise')` |

**解决方案**:

```python
# 修改前
queryset = EnterpriseQualification.objects.all()

# 修改后
queryset = EnterpriseQualification.objects.select_related('enterprise')
```

**预防措施**:
1. 所有包含外键的模型列表查询必须使用 `select_related`
2. 多对多关系使用 `prefetch_related`
3. 使用 Django Debug Toolbar 检测 N+1 问题

**相关文件**:
- `backend/apps/enterprise/views.py`

---

### E043: 缺少健康检查端点和nginx配置

**发生时间**: 2026-03-22

**错误类型**: DevOps配置缺失

**错误描述**:
1. Docker健康检查引用 `/health/` 端点但未实现
2. 前端Dockerfile引用 `nginx.conf` 但文件不存在
3. `requirements.txt` 缺少 `gunicorn` 依赖

**发生场景**:
- DevOps配置检查时发现

**解决方案**:

1. 添加健康检查端点:

```python
# config/urls.py
def health_check(request):
    health_status = {
        'status': 'healthy',
        'database': 'ok',
        'cache': 'ok',
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        health_status['database'] = 'error'
        health_status['status'] = 'unhealthy'
    
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception('Cache not working')
    except Exception:
        health_status['cache'] = 'error'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)

urlpatterns = [
    path('health/', health_check, name='health_check'),
    # ...
]
```

2. 创建 `frontend/nginx.conf` 配置文件

3. 添加 `gunicorn==21.2.0` 到 `requirements.txt`

**预防措施**:
1. Docker配置引用的文件必须存在
2. 生产环境依赖必须完整

**相关文件**:
- `backend/config/urls.py`
- `frontend/nginx.conf`
- `backend/requirements.txt`

---

### E044: 投标记录缺少删除接口

**发生时间**: 2026-03-22

**错误类型**: API完整性缺失

**错误描述**:
- `BidRecordDetailView` 继承 `RetrieveUpdateDestroyAPIView` 但未实现 `destroy` 方法
- 缺少权限控制逻辑

**发生场景**:
- API接口完整性检查时发现

**解决方案**:

```python
class BidRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    # ...
    
    def destroy(self, request, *args, **kwargs):
        """
        删除投标记录
        只有创建者或管理员可以删除
        """
        instance = self.get_object()
        
        if not (request.user.is_staff or instance.created_by == request.user):
            return APIResponse.error(
                message='无权限删除此记录',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return APIResponse.success(message='删除成功')
```

**预防措施**:
1. 删除操作必须添加权限控制
2. API设计时确保CRUD完整性

**相关文件**:
- `backend/apps/bids/views.py`

---

### E045: 企业采集接口缺少频率限制

**发生时间**: 2026-03-22

**错误类型**: 频率限制缺失

**错误描述**:
- `collect_info` 和 `batch_collect` 接口无频率限制
- 可能被滥用导致服务器压力过大

**发生场景**:
- 安全检查时发现

**解决方案**:

```python
from rest_framework.decorators import throttle_classes
from rest_framework.throttling import UserRateThrottle

class EnterpriseCollectThrottle(UserRateThrottle):
    rate = '10/hour'

class EnterpriseBatchCollectThrottle(UserRateThrottle):
    rate = '3/hour'

class EnterpriseViewSet(viewsets.ModelViewSet):
    # ...
    
    @action(detail=False, methods=['post'])
    @throttle_classes([EnterpriseCollectThrottle])
    def collect_info(self, request):
        # ...
    
    @action(detail=False, methods=['post'])
    @throttle_classes([EnterpriseBatchCollectThrottle])
    def batch_collect(self, request):
        # ...
```

**预防措施**:
1. 资源密集型接口必须添加频率限制
2. 根据接口复杂度设置合理的限制值

**相关文件**:
- `backend/apps/enterprise/views.py`

---

### E046: Token刷新请求体为空导致401错误

**发生时间**: 2026-03-22

**错误类型**: 认证错误

**错误描述**:
- 前端API请求返回401 Unauthorized错误
- Token刷新失败，导致所有后续请求都返回401
- 原因：前端 `refreshAccessToken()` 函数发送空的请求体 `{}`，没有传递 `refresh_token`

**发生场景**:
- 用户登录后，access_token过期时自动刷新
- 页面加载时自动请求需要认证的API
- 后端日志显示：`'body': {}` - 请求体为空

**错误信息**:
```
POST /api/v1/auth/token/refresh/ 401 (Unauthorized)
WARNING 2026-03-22 21:38:41,038 API请求失败: {'method': 'POST', 'path': '/api/v1/auth/token/refresh/', 'status': 401, 'duration': '0.243s', 'user_id': 'anonymous', 'ip': '127.0.0.1', 'body': {}}
```

**错误代码**:
```javascript
// 错误写法 - 发送空请求体
async function refreshAccessToken() {
  const response = await axios.post('/api/v1/auth/token/refresh/', {}, {
    withCredentials: true
  })
  // ...
}
```

**解决方案**:

修改前端 `frontend/src/utils/request.js`，在请求体中传递 `refresh_token`：

```javascript
// 正确写法 - 从store或localStorage获取refresh_token并传递
async function refreshAccessToken() {
  const userStore = useUserStore()
  
  const refreshToken = userStore.refreshToken || localStorage.getItem('refresh_token')
  
  if (!refreshToken) {
    console.error('No refresh token available')
    return null
  }
  
  try {
    const response = await axios.post('/api/v1/auth/token/refresh/', 
      { refresh: refreshToken },
      { withCredentials: true }
    )
    
    const newAccessToken = response.data.data?.access || response.data.access
    
    if (newAccessToken) {
      userStore.setToken(newAccessToken)
    }
    
    return newAccessToken
  } catch (error) {
    console.error('Token refresh failed:', error)
    return null
  }
}
```

**后端处理逻辑**:
```python
# backend/apps/users/views.py - CookieTokenRefreshView
def post(self, request):
    # 优先从cookie中读取，其次从请求体中读取
    refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
    
    if not refresh_token:
        return APIResponse.error(
            message='Refresh token不存在，请重新登录',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    # ...
```

**预防措施**:
1. Token刷新请求必须在请求体中传递 `refresh_token`
2. 后端支持从Cookie或请求体两种方式获取refresh_token
3. 登录时确保同时保存 `access_token` 和 `refresh_token` 到localStorage
4. 刷新失败时清除所有token并跳转登录页

**相关文件**:
- `frontend/src/utils/request.js` - Token刷新逻辑
- `frontend/src/store/user.js` - 用户状态管理
- `backend/apps/users/views.py` - CookieTokenRefreshView

---

## E047 - API方法缺失：enterpriseApi缺少getQualifications/getPerformances方法

**错误描述**:
前端调用 `enterpriseApi.getQualifications()` 和 `enterpriseApi.getPerformances()` 时报错：
```
TypeError: enterpriseApi.getQualifications is not a function
TypeError: enterpriseApi.getPerformances is not a function
```

**发生场景**:
- 用户访问企业信息管理页面
- 选择某个企业时，前端尝试获取该企业的资质和业绩信息
- `fetchQualifications()` 和 `fetchPerformances()` 函数调用了不存在的API方法

**根本原因**:
前端 `enterprise.js` API文件中缺少资质和业绩相关的CRUD方法定义，但 `CompanyInfo.vue` 组件中已经调用了这些方法。

**解决方案**:
在 `frontend/src/api/enterprise.js` 中添加缺失的API方法：

```javascript
// 资质相关API
getQualifications(params) {
  return request.get(`${BASE_URL}/qualifications/`, { params })
},

createQualification(data) {
  return request.post(`${BASE_URL}/qualifications/`, data)
},

updateQualification(id, data) {
  return request.patch(`${BASE_URL}/qualifications/${id}/`, data)
},

deleteQualification(id) {
  return request.delete(`${BASE_URL}/qualifications/${id}/`)
},

// 业绩相关API
getPerformances(params) {
  return request.get(`${BASE_URL}/performances/`, { params })
},

createPerformance(data) {
  return request.post(`${BASE_URL}/performances/`, data)
},

updatePerformance(id, data) {
  return request.patch(`${BASE_URL}/performances/${id}/`, data)
},

deletePerformance(id) {
  return request.delete(`${BASE_URL}/performances/${id}/`)
}
```

**预防措施**:
1. 新增后端API端点后，必须同步添加对应的前端API方法
2. 前端组件调用API前，先检查API文件中是否存在该方法
3. 建立前后端API对照检查机制，确保API完整性
4. 代码审查时重点检查API调用与方法定义的对应关系

**相关文件**:
- `frontend/src/api/enterprise.js` - 前端API定义
- `frontend/src/views/CompanyInfo.vue` - 企业信息管理组件
- `backend/apps/enterprise/urls.py` - 后端路由（qualifications/performances端点）

---

## E048 - AI全网搜索失败：未配置LLM提供商

**错误描述**:
用户在向量库页面点击"AI全网搜索"按钮时，搜索任务创建成功但执行失败，后端日志显示：
```
WARNING AI搜索失败，使用模拟数据: 没有可用的模型提供商
```

**发生场景**:
- 用户访问投标文档向量库页面
- 点击"AI全网搜索"按钮，输入关键词后提交
- 搜索任务状态显示"completed"但实际使用的是模拟数据

**根本原因**:
数据库中 `llm_providers` 表为空，没有配置任何LLM模型提供商，导致 `unified_llm_service.get_provider()` 返回 `None`。

**解决方案**:

1. 创建数据迁移初始化默认LLM提供商配置：
```python
# backend/apps/openclaw/migrations/0003_init_llm_providers.py
providers_data = [
    {
        'name': 'Ollama本地部署',
        'provider_type': 'ollama',
        'code': 'ollama_local',
        'base_url': 'http://localhost:11434',
        'default_model': 'qwen2.5:14b',
        'is_active': True,
        'is_default': True,
    },
    {
        'name': '智谱AI',
        'provider_type': 'zhipu',
        'code': 'zhipu',
        'default_model': 'glm-4-flash',
        'is_active': True,
        'is_default': False,
    },
    # ... 其他提供商
]
```

2. 改进AI搜索错误提示：
```python
# backend/apps/vectorlib/views.py
provider = unified_llm_service.get_provider()
if not provider:
    raise ValueError(
        "未配置LLM模型提供商。请在后台配置Ollama本地服务或配置API密钥。\n"
        "配置方法：\n"
        "1. 启动Ollama服务: ollama serve\n"
        "2. 或在系统设置中配置智谱AI/通义千问/DeepSeek的API密钥"
    )

if provider.provider_type == 'ollama':
    # 检查Ollama服务是否可用
    response = requests.get(f"{provider.base_url}/api/tags", timeout=5)
    # ...
elif not provider.api_key:
    raise ValueError(f"LLM提供商 '{provider.name}' 未配置API密钥")
```

3. 前端优化错误提示显示：
```javascript
// frontend/src/views/vectorlib/VectorLibrary.vue
if (errorMsg.includes('LLM') || errorMsg.includes('Ollama') || errorMsg.includes('API')) {
  ElMessage({
    type: 'error',
    message: errorMsg,
    duration: 5000,
    showClose: true
  })
}
```

**预防措施**:
1. 系统初始化时自动创建默认LLM提供商配置
2. AI搜索功能执行前检查提供商配置状态
3. 提供清晰的配置指引和错误提示
4. 前端显示配置状态，引导用户完成配置

**相关文件**:
- `backend/apps/openclaw/migrations/0003_init_llm_providers.py` - 数据迁移
- `backend/apps/vectorlib/views.py` - AI搜索视图
- `backend/services/unified_llm_service.py` - 统一LLM服务
- `frontend/src/views/vectorlib/VectorLibrary.vue` - 向量库页面

---

## E049 - Django REST Framework不支持async视图方法

**错误描述**:
访问 `/api/v1/openclaw/scheduler/status/` 接口时返回500错误：
```
AssertionError: Expected a `Response`, `HttpResponse` or `HttpStreamingResponse` to be returned from the view, but received a `<class 'coroutine'>`
RuntimeWarning: coroutine 'TaskSchedulerViewSet.status' was never awaited
```

**发生场景**:
- 用户访问自动化工作台页面
- 前端调用 `fetchSchedulerStatus()` 获取调度器状态
- 后端 `TaskSchedulerViewSet.status` 方法被定义为 `async def`，但DRF不支持异步视图

**根本原因**:
Django REST Framework默认不支持异步视图方法。当视图方法被定义为 `async def` 时，DRF会将其视为普通函数调用，不会await协程，导致返回一个coroutine对象而不是Response对象。

**解决方案**:
创建 `run_async()` 辅助函数，在同步上下文中运行异步协程：

```python
import asyncio

def run_async(coro):
    """
    在同步上下文中运行异步协程
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class TaskSchedulerViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def status(self, request):  # 注意：移除async关键字
        result = run_async(bid_task_scheduler.get_scheduler_status())
        return APIResponse.success(data=result)
```

**预防措施**:
1. Django REST Framework视图方法不要使用 `async def`
2. 如需调用异步函数，使用 `run_async()` 或 `asyncio.run()` 包装
3. Django 4.1+ 支持异步视图，但DRF需要额外配置
4. 使用 `asgiref.sync.sync_to_async` 和 `async_to_sync` 进行转换

**相关文件**:
- `backend/apps/openclaw/workflow_views.py` - 工作流视图
- `backend/services/bid_task_scheduler.py` - 异步任务调度器
- `backend/services/bid_automation_workflow.py` - 异步工作流服务

---

## E050 - Element Plus Input组件收到数组值导致警告

**错误描述**:
前端控制台显示警告：
```
{name: Array(1)}
debugWarn @ error.mjs:22
```
Element Plus 的 Input 组件收到了数组值，而它期望的是字符串。

**发生场景**:
- 在企业信息管理页面点击"编辑"按钮编辑人员、资质、业绩等信息时
- `el-input` 组件的 `v-model` 绑定的值是数组而不是字符串

**根本原因**:
前端编辑函数（如 `editPersonnel`、`editQualification` 等）在赋值时没有进行类型检查，当后端返回的数据中某个字段值为数组时（可能是验证规则数组或其他原因），会直接赋值给表单字段，导致 `el-input` 组件收到数组值。

**错误代码**:
```javascript
const editPersonnel = (row) => {
  Object.assign(personnelForm, { ...defaultPersonnelForm })
  Object.keys(row).forEach(key => {
    if (key in personnelForm) {
      personnelForm[key] = row[key]  // 没有类型检查，可能赋值数组
    }
  })
  // ...
}
```

**解决方案**:
在编辑函数中添加类型检查，防止数组值被赋值给字符串字段：

```javascript
const editPersonnel = (row) => {
  Object.assign(personnelForm, { ...defaultPersonnelForm })
  Object.keys(row).forEach(key => {
    if (key in personnelForm) {
      const value = row[key]
      if (key === 'name' && Array.isArray(value)) {
        console.warn('name字段收到数组值，已忽略:', value)
        return
      }
      personnelForm[key] = value
    }
  })
  // ...
}
```

**预防措施**:
1. 表单字段赋值前进行类型检查
2. 对于字符串字段，检查值是否为数组
3. 添加警告日志以便调试
4. 后端确保返回的数据格式正确

**相关文件**:
- `frontend/src/views/CompanyInfo.vue` - 企业信息管理页面
- `frontend/src/views/CompanyInfo.vue` - editPersonnel/editQualification/editPerformance/editContact/editMatchRule/editEnterprise 函数

---

## E051 - 401 Unauthorized错误排查

**错误描述**:
前端API请求返回401 Unauthorized错误：
```
GET http://localhost:8081/api/v1/crawler/templates/?page_size=100 401 (Unauthorized)
GET http://localhost:8081/api/v1/crawler/schedules/?page=1&page_size=10 401 (Unauthorized)
GET http://localhost:8081/api/v1/notifications/unread-count/ 401 (Unauthorized)
```

**发生场景**:
- 页面加载时自动请求需要认证的API
- Token过期后刷新失败
- 用户未登录直接访问需要认证的页面

**根本原因分析**:
1. **Token过期**: JWT access token有效期2小时，过期后需要刷新
2. **刷新失败**: refresh_token不存在或过期导致无法获取新token
3. **认证异常处理不当**: 后端认证类捕获异常后返回None而不是抛出AuthenticationFailed

**解决方案**:

1. 改进后端认证类 `backend/utils/authentication.py`:
```python
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # ... 获取token逻辑 ...
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            logger.debug(f'Token验证失败(InvalidToken): {e}')
            raise AuthenticationFailed('Token无效或已过期', code='token_invalid')
        except TokenError as e:
            logger.debug(f'Token验证失败(TokenError): {e}')
            raise AuthenticationFailed('Token验证失败', code='token_error')
```

2. 前端token刷新机制已实现（`frontend/src/utils/request.js`）:
   - 检测401错误
   - 使用refresh_token获取新access_token
   - 重试原始请求

3. 用户登录时保存token（`frontend/src/store/user.js`）:
   - 保存access_token到localStorage
   - 保存refresh_token到localStorage

**排查步骤**:
1. 检查localStorage中是否有token和refresh_token
2. 检查后端日志确认token刷新请求是否成功
3. 检查后端日志确认API请求的user_id

**预防措施**:
1. 登录时确保同时保存access_token和refresh_token
2. Token过期前主动刷新（可选优化）
3. 后端认证异常应抛出AuthenticationFailed而不是返回None
4. 前端401错误处理应尝试刷新token

**相关文件**:
- `backend/utils/authentication.py` - JWT认证类
- `frontend/src/utils/request.js` - 请求拦截器和token刷新
- `frontend/src/store/user.js` - 用户状态管理
- `backend/apps/users/views.py` - CookieTokenRefreshView

---

## E052 - Sass导入路径缓存导致编译失败

**错误描述**:
前端编译失败，报错：
```
Module build failed (from ./node_modules/sass-loader/dist/cjs.js): 
Can't find stylesheet to import. 
  ╷ 
1 │ @import "@/styles/variables.scss"; 
  │         ^^^^^^^^^^^^^^^^^^^^^^^^^ 
  ╵ 
  src\assets\styles\main.scss 1:9  root stylesheet
```

**发生场景**:
- 前端开发服务器运行时
- 修改了SCSS文件后重新编译
- Webpack缓存中保存了旧的导入路径
- sass-loader无法解析`@/`路径别名

**根本原因**:
1. **Webpack缓存**: node_modules/.cache目录缓存了旧的SCSS编译结果
2. **sass-loader配置缺失**: vue.config.js中的scss loaderOptions缺少`includePaths`配置，导致无法解析`@/`路径

**解决方案**:

1. 修改 `vue.config.js` 添加sass-loader的includePaths配置：
```javascript
css: {
  loaderOptions: {
    scss: {
      additionalData: `@use "@/assets/styles/variables.scss" as *;`,
      sassOptions: {
        silenceDeprecations: ['legacy-js-api'],
        includePaths: [path.resolve(__dirname, 'src')]  // 添加此行
      }
    }
  }
}
```

2. 清理Webpack缓存并重启开发服务器：
```bash
# Windows PowerShell
Remove-Item -Recurse -Force "frontend\node_modules\.cache" -ErrorAction SilentlyContinue
Set-Location frontend
npm run serve
```

3. 终止占用端口的旧进程：
```bash
# 查找占用8081端口的进程
netstat -ano | findstr :8081
# 终止进程
taskkill /F /PID <PID>
```

**预防措施**:
1. 修改SCSS文件路径或导入方式后，清理缓存
2. 遇到奇怪的编译错误时，首先尝试清理缓存
3. 使用 `@use` 替代 `@import`（Sass新语法）
4. sass-loader使用`@/`路径时必须配置`includePaths`
5. 定期清理node_modules/.cache目录

**相关文件**:
- `frontend/vue.config.js` - Vue CLI配置文件
- `frontend/src/assets/styles/main.scss` - 主样式文件
- `frontend/src/assets/styles/variables.scss` - 变量定义文件
- `frontend/node_modules/.cache/` - Webpack缓存目录

---

## E053 - 前端端口配置不固定

**错误描述**:
前端开发服务器端口不固定，当8081端口被占用时自动切换到8082端口，导致用户需要频繁更换访问地址。

**发生场景**:
- 启动前端开发服务器时
- 8081端口被旧进程占用
- Vue CLI自动切换到下一个可用端口

**根本原因**:
vue.config.js中的devServer配置缺少`strictPort: true`，导致端口被占用时自动切换而不是报错。

**解决方案**:
修改 `vue.config.js` 固定端口配置：
```javascript
devServer: {
  port: 8081,           // 固定端口，不使用环境变量
  host: '0.0.0.0',
  open: false,
  strictPort: true,     // 端口被占用时报错而不是自动切换
  proxy: {
    '/api': {
      target: 'http://localhost:8007',
      changeOrigin: true,
      ws: true
    }
  }
}
```

**预防措施**:
1. 使用`strictPort: true`固定端口
2. 启动前检查端口是否被占用
3. 定期清理残留的node进程

**相关文件**:
- `frontend/vue.config.js` - Vue CLI配置文件

---

## E054 - EmbeddingService初始化阻塞服务启动

**错误描述**:
Django后端服务启动时卡住，无法完成启动，日志显示在加载EmbeddingService时阻塞：
```
正在下载模型 from huggingface...
```

**发生场景**:
- 启动Django开发服务器时
- EmbeddingService在模块导入时尝试初始化SentenceTransformer模型
- 模型尝试从huggingface下载，但网络不通导致阻塞

**根本原因**:
`EmbeddingService`类在模块导入时就执行初始化逻辑（`__init__`中调用`_initialize_model()`），而模型初始化需要从网络下载资源。这种"急切初始化"模式导致整个服务启动被阻塞。

**错误代码**:
```python
class EmbeddingService:
    _instance = None
    _model = None
    
    def __init__(self):
        if self._model is None:
            self._initialize_model()  # 问题：模块导入时就执行
    
    def _initialize_model(self):
        self._model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
```

**解决方案**:
改为延迟初始化模式，只在真正需要使用时才初始化模型：

```python
class EmbeddingService:
    _instance = None
    _model = None
    _initialized = False  # 新增初始化标志
    
    def __init__(self):
        pass  # 不再在初始化时加载模型
    
    def _ensure_initialized(self):
        """确保模型已初始化（延迟初始化）"""
        if not self._initialized:
            self._initialize_model()
            self._initialized = True
    
    def embed(self, text: str) -> List[float]:
        self._ensure_initialized()  # 使用时才初始化
        return self._model.embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._ensure_initialized()  # 使用时才初始化
        return self._model.embed_batch(texts)
```

**预防措施**:
1. 涉及网络I/O或耗时操作的初始化应使用延迟加载模式
2. 服务启动时不应阻塞在可选依赖的初始化上
3. 使用`_initialized`标志避免重复初始化
4. 为可选依赖提供后备方案或优雅降级

**相关文件**:
- `backend/services/embedding_service.py` - Embedding服务

---

## E055 - webpack-dev-server不支持strictPort配置

**错误描述**:
前端启动时报错：
```
ValidationError: Invalid options object. Dev Server has been initialized using an options object that does not match the API schema.
- options has an unknown property 'strictPort'
```

**发生场景**:
- 运行`npm run serve`启动前端开发服务器
- vue.config.js中配置了`strictPort: true`

**根本原因**:
项目使用的webpack-dev-server版本不支持`strictPort`配置项。该配置在某些版本中已被移除或改名。

**错误配置**:
```javascript
// vue.config.js
devServer: {
  port: 8081,
  host: '0.0.0.0',
  open: false,
  strictPort: true,  // 不支持的配置
  proxy: { ... }
}
```

**解决方案**:
移除不支持的`strictPort`配置：

```javascript
// vue.config.js
devServer: {
  port: 8081,
  host: '0.0.0.0',
  open: false,
  // 移除 strictPort: true
  proxy: {
    '/api': {
      target: 'http://localhost:8007',
      changeOrigin: true,
      ws: true
    }
  }
}
```

**替代方案**:
如果需要固定端口，可以在启动脚本中检查端口占用：
```bash
# package.json
"scripts": {
  "serve": "node scripts/check-port.js && vue-cli-service serve"
}
```

**预防措施**:
1. 添加配置前确认webpack-dev-server版本支持该配置
2. 查阅对应版本的官方文档
3. 遇到unknown property错误时，检查配置兼容性

**相关文件**:
- `frontend/vue.config.js` - Vue CLI配置文件
- `frontend/package.json` - 依赖版本

---

## E056 - AllowAny视图无效Token导致401错误

**错误描述**:
登录接口返回401 Unauthorized错误：
```
POST http://localhost:8081/api/v1/auth/login/ 401 (Unauthorized)
{"code":401,"message":"Token无效或已过期","data":null}
```

**发生场景**:
- 用户访问登录页面
- 输入用户名密码后点击登录
- 后端返回401错误，但登录接口应该允许匿名访问

**根本原因**:
`CookieJWTAuthentication`认证类在验证Token失败时抛出`AuthenticationFailed`异常。但对于配置了`AllowAny`权限的视图（如登录接口），无效的Token应该被忽略而不是抛出异常。

**错误代码**:
```python
# backend/utils/authentication.py
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # ... 获取token ...
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            raise AuthenticationFailed('Token无效或已过期')  # 问题：抛出异常
        except TokenError as e:
            raise AuthenticationFailed('Token验证失败')  # 问题：抛出异常
```

**Django REST Framework认证机制**:
- 当认证类返回`None`时，表示"跳过认证"，请求继续进行
- 当认证类抛出`AuthenticationFailed`异常时，请求被拒绝，返回401
- 对于`AllowAny`权限的视图，应该返回`None`让请求继续

**解决方案**:
修改认证类，对于无效Token返回`None`而不是抛出异常：

```python
# backend/utils/authentication.py
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # ... 获取token ...
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            logger.debug(f'Token验证失败: {e}')
            return None  # 返回None，不抛出异常
        except TokenError as e:
            logger.debug(f'Token验证失败: {e}')
            return None  # 返回None，不抛出异常
        except Exception as e:
            logger.warning(f'Token验证异常: {e}')
            return None
```

**权限与认证的关系**:
| 权限类 | 有效Token | 无效Token(抛异常) | 无效Token(返回None) |
|--------|----------|------------------|-------------------|
| IsAuthenticated | ✅ 通过 | ❌ 401 | ❌ 401 |
| AllowAny | ✅ 通过 | ❌ 401 | ✅ 通过 |
| IsAdminUser | 视角色 | ❌ 401 | ❌ 403 |

**预防措施**:
1. 对于可能被匿名访问的接口，认证类不应抛出异常
2. 理解DRF的认证-授权机制：认证确定"你是谁"，授权确定"你能做什么"
3. `AllowAny`权限的视图，认证失败应返回`None`
4. 需要强制认证的视图使用`IsAuthenticated`权限

**相关文件**:
- `backend/utils/authentication.py` - JWT认证类
- `backend/apps/users/views.py` - 登录视图（使用AllowAny权限）

---

*最后更新: 2026-03-25*

---

## E057 - 银行账号双重加密导致数据不一致

**错误描述**:
编辑企业信息时保存失败，或者保存后银行账号无法正确解密显示。

**发生场景**:
1. 用户编辑企业信息
2. 前端获取企业详情（包含解密的银行账号）
3. 用户提交表单，后端序列化器对银行账号再次加密
4. 数据库中存储的是双重加密的数据

**根本原因**:
`EnterpriseSerializer.to_internal_value()` 方法在处理 `bank_account` 字段时，无论提交的值是否已经是加密的，都会执行 `AESCrypto.encrypt()` 操作，导致双重加密。

**解决方案**:
修改 `to_internal_value` 方法，在加密前先尝试解密：
- 如果解密成功且结果与原值不同，说明原值是明文，需要加密
- 如果解密失败或结果与原值相同，说明原值已经是加密的，直接保存原值

**错误代码**:
```python
# backend/apps/enterprise/serializers.py
if data.get('bank_account'):
    bank_account = data['bank_account']
    if bank_account and isinstance(bank_account, str):
        try:
            decrypted = AESCrypto.decrypt(bank_account)
            if decrypted and decrypted != bank_account:
                data['bank_account'] = bank_account
            else:
                data['bank_account'] = AESCrypto.encrypt(bank_account)
        except Exception:
            data['bank_account'] = AESCrypto.encrypt(bank_account)
```

**测试验证**:
1. 提交普通文本（如 `6217855000000000001`）→ 正确加密并保存
2. 提交已加密文本 → 不会被重复加密，保持不变

**相关文件**:
- `backend/apps/enterprise/serializers.py` - 企业序列化器

---

## F003: 前端开发环境端口配置与冲突自动处理

**更新时间**: 2026-03-26

**更新内容**:

1. **创建端口检测与冲突处理脚本**

   新建 `frontend/scripts/port-check.js`，实现以下功能：

   - 启动时自动检测8081端口是否被占用
   - 获取占用端口的进程PID和详情
   - 自动执行 `taskkill /PID xxx /F` 终止占用进程
   - 等待端口释放后再启动开发服务器
   - 无法终止时提示手动处理

2. **修改package.json启动脚本**

   ```json
   "serve": "node scripts/port-check.js"
   ```

3. **vue.config.js保持端口8081配置**

   ```javascript
   devServer: {
     port: 8081,
     host: '0.0.0.0',
     open: false,
   }
   ```

**新增文件**:
- `frontend/scripts/port-check.js` - 端口检测与冲突处理脚本

**修改文件**:
- `frontend/package.json` - 修改serve脚本
- `frontend/vue.config.js` - 已确认端口配置

**预防措施**:

1. 前端开发服务器端口固定为8081
2. 启动时自动处理端口冲突，无需手动终止进程
3. 如遇无法终止的进程（如系统进程），会提示手动处理

---

### E058: 前端页面重构 - 简化交互

**发生时间**: 2026-03-26

**错误类型**: 前端重构

**错误描述**:
- 前端页面存在大量可由系统自动处理的内容和交互元素
- 需要移除可自动计算/填充的内容，保留必须手动操作的关键功能

**解决方案**:

1. **Dashboard页面简化**
   - 移除投标统计面板（8个字段的重复显示）
   - 移除el-card的hover阴影效果
   - 简化recentTenders表格列宽
   - 移除多余的bidStatistics API调用

2. **ScheduleList页面简化**
   - 移除crontab快捷选项（5个可点击标签）
   - 移除setCrontab函数和crontab-help样式
   - 保留核心的执行时间输入和说明

3. **VectorLibrary页面简化**
   - 统计卡片移除shadow="hover"和图标装饰
   - 表格移除: 质量分progress、查看/引用次数、行业列、is_featured图标
   - 移除"引用到标书"功能（自动化操作）
   - 简化样式：居中显示、文本截断

4. **AutomationDashboard页面简化**
   - 统计卡片移除shadow="hover"和彩色图标
   - 简化样式：居中显示、移除彩色stat-icon
   - 移除crontab快捷选项

**修改文件**:
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/ScheduleList.vue`
- `frontend/src/views/vectorlib/VectorLibrary.vue`
- `frontend/src/views/automation/AutomationDashboard.vue`

**预防措施**:

1. 保留必须由用户手动操作的功能（增删改查、表单输入）
2. 移除可自动计算/填充的内容（质量分、快捷选项）
3. 移除装饰性交互元素（hover效果、图标装饰）
4. 简化布局，提高信息密度

---

### E059: 导航栏重构 - 层级化设计

**发生时间**: 2026-03-26

**错误类型**: 前端重构

**错误描述**:
- 导航栏功能入口过多，视觉复杂度高
- 需要采用层级化设计，隐藏非高频使用选项

**解决方案**:

1. **重构SidebarNav.vue组件**
   - 采用层级化设计，将功能分为一级入口和子菜单
   - 核心功能入口：
     - 首页 - Dashboard
     - 招标采集 - 定时采集、关键词管理（子菜单）
     - 投标管理 - 已投标项目、投标记录（子菜单）
     - 企业管理 - 公司信息、文档管理、文档向量库（子菜单）
     - 自动化工作台 - 一键启动
     - 自动化监控 - 新增监控面板入口
   - 顶部显示自动化运行状态指示器
   - 收折模式支持tooltip显示

**修改文件**:
- `frontend/src/components/SidebarNav.vue`

**预防措施**:

1. 仅保留高频功能为一级入口
2. 低频功能归入子菜单
3. 顶部显示系统状态指示器

---

### E060: 新增自动化监控面板

**发生时间**: 2026-03-26

**错误类型**: 新增功能

**错误描述**:
- 需要一个统一的自动化状态监控面板
- 实时展示各业务模块的运行状态及自动化完成率指标

**解决方案**:

1. **新增AutomationMonitor.vue组件**
   - 实时状态显示：整体自动化运行状态（运行中/空闲/异常）
   - 今日统计：采集、匹配、投标、中标数量及趋势
   - 自动化流程图：可视化展示5个关键环节
     1. 招标采集
     2. 资质匹配
     3. 标书生成
     4. 标书审核
     5. 标书上交
   - 异常告警：自动记录的异常情况和处理状态
   - 人工干预队列：仅在系统无法自动解决时显示需人工确认的项目
   - 自动化效率统计：整体自动化率、平均处理时长、异常自愈率

2. **更新路由配置**
   - 添加 `/automation-monitor` 路由

**新增文件**:
- `frontend/src/views/automation/AutomationMonitor.vue`

**修改文件**:
- `frontend/src/router/index.js`

**预防措施**:

1. 自动化流程端到端可视化
2. 异常自动记录，仅在无法解决时触发人工干预
3. 实时更新，30秒自动刷新

---

### E061: 统一API响应格式

**发生时间**: 2026-03-26

**错误类型**: 架构统一

**错误描述**:
- 不同模块的API响应格式不一致
- 需要全面应用UnifiedResponse类

**解决方案**:

1. **修改openclaw/views.py**
   - 添加 `from utils.responses import UnifiedResponse` 导入
   - 将25处 `Response({...})` 替换为 `UnifiedResponse.success/error/not_found()`

2. **修改crawler/views.py**
   - 添加导入
   - 将12处 `Response({...})` 替换为 `UnifiedResponse.success/error()`

3. **修改enterprise/views.py**
   - 添加导入
   - CRUD操作已由AuthenticatedModelViewSet处理

**修改文件**:
- `backend/apps/openclaw/views.py`
- `backend/apps/crawler/views.py`
- `backend/apps/enterprise/views.py`

**预防措施**:

1. 统一使用UnifiedResponse类处理API响应
2. 保持响应格式一致性
3. 便于前端统一处理

---

### E062: Agent消息格式标准化

**发生时间**: 2026-03-26

**错误类型**: 架构统一

**错误描述**:
- Agent消息格式不统一
- 需要定义标准AgentMessage消息格式

**解决方案**:

1. **在core/constants.py中添加枚举**
   ```python
   class MessageRole(Enum):
       """Agent消息角色枚举 - 标准消息格式"""
       SYSTEM = 'system'
       USER = 'user'
       ASSISTANT = 'assistant'
       AGENT = 'agent'
       TOOL = 'tool'

   class MessageType(Enum):
       """Agent消息类型枚举"""
       TEXT = 'text'
       CODE = 'code'
       TOOL_CALL = 'tool_call'
       TOOL_RESULT = 'tool_result'
       ERROR = 'error'
       STATUS = 'status'
       HEARTBEAT = 'heartbeat'
   ```

**修改文件**:
- `backend/core/constants.py`

**预防措施**:

1. 所有Agent消息使用标准MessageRole和MessageType
2. 便于消息序列化和反序列化
3. 统一日志和监控格式

---

### E063: StatusBadge组件引用不存在的导出

**发生时间**: 2026-03-26

**错误类型**: 前端监控

**错误描述**:
- StatusBadge.vue组件引用了不存在的导出
- `CRAWLER_STATUS` 和 `ENTERPRISE_DOC_STATUS` 未从 `@/utils/status` 导出

**错误信息**:
```
export 'CRAWLER_STATUS' (imported as 'CRAWLER_STATUS') was not found in '@/utils/status'
export 'ENTERPRISE_DOC_STATUS' (imported as 'ENTERPRISE_DOC_STATUS') was not found in '@/utils/status'
```

**解决方案**:

1. 在 `store/constants.js` 中添加常量定义:
```javascript
export const CRAWLER_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

export const ENTERPRISE_DOC_STATUS = {
  VALID: 'valid',
  EXPIRING: 'expiring',
  EXPIRED: 'expired',
  PENDING: 'pending'
}
```

2. 更新 `utils/status.js` 导出这些常量

**修改文件**:
- `frontend/src/store/constants.js`
- `frontend/src/utils/status.js`

**预防措施**:

1. 确保引用的导出都已在源文件中正确定义
2. 使用前进行验证

---

### E064: 8081端口被占用导致前端切换到8082

**发生时间**: 2026-03-26

**错误类型**: 端口配置

**错误描述**:
- 前端开发服务器端口不固定，当8081端口被占用时自动切换到8082端口
- PID 29984的node.exe进程占用了8081端口

**解决方案**:

1. 终止占用8081端口的进程
   ```bash
   taskkill /PID 29984 /F
   ```

2. 重启前端开发服务器

**预防措施**:

1. 端口固定为8081
2. 如遇端口占用，手动终止占用进程
3. 考虑添加端口检测脚本自动处理

---

---

*最后更新: 2026-03-28*

*本次更新：新增 E129 数据库配置不一致错误记录*

---

## E125: AIPlayground streamChat认证不一致导致401

**发生时间**: 2026-03-28

**错误类型**: 前端认证错误

**错误描述**:
- AI Playground 页面调用 stream_chat API 返回 401 Unauthorized
- 错误信息: `POST http://localhost:8081/api/v1/openclaw/playground/stream_chat/ 401 (Unauthorized)`

**根本原因**:
- `streamChat` 函数使用 `localStorage.getItem('token')` 获取认证 token
- 但应用其他地方使用 Cookie 存储的 httpOnly token，通过 `userStore.token` 访问
- Cookie 中的 token 无法被 JavaScript 直接读取（httpOnly=True）

**解决方案**:
```javascript
// 修改前
const token = document.cookie.match(/access_token=([^;]+)/)?.[1] || localStorage.getItem('token')

// 修改后
import { useUserStore } from '@/store/user'
const userStore = useUserStore()
const token = userStore.token || document.cookie.match(/access_token=([^;]+)/)?.[1]
```

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

**预防措施**:
1. 统一使用 userStore 获取认证信息
2. 避免直接操作 localStorage 存储 token
3. 统一认证方式：Cookie httpOnly + 降级读取

---

## E126: DRF ValidationError 前端错误处理不完整

**发生时间**: 2026-03-28

**错误类型**: 前端错误处理

**错误描述**:
- 用户登录时输入空用户名，后端返回 ValidationError
- 前端控制台显示 `{username: Array(1)}` 错误对象
- 用户界面没有正确显示验证错误信息

**错误数据结构**:
```javascript
// 后端返回格式
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "message": "数据验证失败",
  "data": null,
  "errors": {
    "username": [
      {
        "message": "请输入用户名",
        "fieldValue": "",
        "field": "username"
      }
    ]
  }
}
```

**解决方案**:
```javascript
// user.js login 函数错误处理
async function login(credentials) {
  try {
    // ... 正常登录逻辑
  } catch (error) {
    let errorMessage = '登录失败'
    if (error.response?.data) {
      const data = error.response.data
      if (data.errors) {
        const errors = data.errors
        if (errors.username) {
          const usernameErr = Array.isArray(errors.username) ? errors.username[0] : errors.username
          errorMessage = usernameErr.message || '用户名验证失败'
        } else if (errors.password) {
          const passwordErr = Array.isArray(errors.password) ? errors.password[0] : errors.password
          errorMessage = passwordErr.message || '密码验证失败'
        }
      } else if (data.message) {
        errorMessage = data.message
      }
    }
    return { success: false, message: errorMessage }
  }
}
```

**修改的文件**:
- `frontend/src/store/user.js`

**预防措施**:
1. API 错误响应统一格式
2. 前端错误处理考虑嵌套的 errors 对象结构
3. 单元测试验证各种错误格式的处理

---

## E127: 模型配置页面UI优化

**发生时间**: 2026-03-28

**错误类型**: UI功能改进

**改进内容**:

### 1. 模型列表按大小排序功能
- 默认按大小升序排列（从小到大）
- 添加排序切换按钮，点击可在升序/降序间切换
- 按钮显示当前排序方向：按大小↑ 或 按大小↓
- 表头显示当前排序状态：从小到大 或 从大到小

### 2. Ollama 文本替换为投标精灵
- "Ollama 本地模型配置" → "投标精灵 本地模型配置"
- "Ollama 地址" → "投标精灵地址"
- "Ollama 连接成功..." → "投标精灵连接成功..."
- "Ollama 服务未启动..." → "投标精灵服务未启动..."

**修改的文件**:
- `frontend/src/views/system/ModelConfig.vue`

**技术实现**:
```javascript
const sortAscending = ref(true)

const toggleSort = () => {
  sortAscending.value = !sortAscending.value
}

const sortedOllamaModels = computed(() => {
  const models = [...ollamaModels.value]
  models.sort((a, b) => {
    const sizeA = a.size || 0
    const sizeB = b.size || 0
    return sortAscending.value ? sizeA - sizeB : sizeB - sizeA
  })
  return models
})
```

**预防措施**:
1. 保持UI文本与后端配置一致
2. 添加排序功能时使用 computed 避免直接修改原数据

---

## E128: 对话框模型选项文本优化

**发生时间**: 2026-03-28

**错误类型**: UI文本优化

**问题描述**:
- Agent 模型配置页面的"对话模型"下拉框选项显示 `{model.name} (投标精灵)`
- 冗余的后缀信息

**解决方案**:
```javascript
// 修改前
:label="`${model.name} (${model.provider_name})`"

// 修改后
:label="model.name"
```

**修改的文件**:
- `frontend/src/views/system/ModelConfig.vue`

**预防措施**:
1. 下拉框选项只显示必要信息
2. 避免冗余的后缀重复显示

---

## E129: 数据库配置不一致导致连接失败

**发生时间**: 2026-03-28

**错误类型**: 数据库配置不一致

**问题描述**:
- Django应用无法连接PostgreSQL数据库
- 错误信息：`psycopg2.OperationalError` - Password 认证失败
- 原因：项目多处配置文件中的数据库默认密码与实际数据库密码不一致

**影响范围**:
- `.env` 文件配置：`DB_PASSWORD=123456`（正确）
- 系统环境变量：`DB_PASSWORD=postgres`（错误）
- `docker-compose.yml` 默认值：`bid_user` / `bid_password`（错误）
- `.env.example` 默认值：`your-db-password`（错误）
- `db_backup.py` 默认值：`bid_user`（错误）

**解决方案**:

1. **统一系统环境变量**：
```powershell
[System.Environment]::SetEnvironmentVariable('DB_PASSWORD', '123456', 'User')
```

2. **修改 docker-compose.yml 默认值**：
```yaml
# 修改前
POSTGRES_USER: ${DB_USER:-bid_user}
POSTGRES_PASSWORD: ${DB_PASSWORD:-bid_password}

# 修改后
POSTGRES_USER: ${DB_USER:-postgres}
POSTGRES_PASSWORD: ${DB_PASSWORD:-123456}
```

3. **修改 .env.example**：
```bash
# 修改前
DB_NAME=bid_auto_system
DB_PASSWORD=your-db-password

# 修改后
DB_NAME=bid_auto
DB_PASSWORD=123456
```

4. **修改 db_backup.py**：
```python
# 修改前
self.db_user = os.getenv('DB_USER', 'bid_user')

# 修改后
self.db_user = os.getenv('DB_USER', 'postgres')
```

**修改的文件**:
- `docker-compose.yml`（8处 bid_user → postgres，10处密码统一为 123456）
- `.env.example`
- `backend/scripts/db_backup.py`

**预防措施**:
1. 所有数据库配置文件必须使用统一的默认用户名 `postgres` 和密码 `123456`
2. 如需修改密码，必须同步修改所有相关配置文件
3. 在修改任何配置前，先检查 ERROR_LOG.md 是否已有相关记录
4. Docker Compose 和本地开发环境使用相同的数据库配置模板
5. 建议使用环境变量文件管理敏感配置，避免硬编码

---

## E130: Element Plus图标组件错误导致debugWarn警告

**发生时间**: 2026-03-28

**错误类型**: 前端组件属性类型错误

**错误描述**:
- 浏览器控制台显示 `error.mjs:22 {name: Array(1)}` 警告
- 来自 Element Plus 的 `debugWarn` 函数

**根本原因**:
- `AIPlayground.vue` 中 el-avatar 组件的 icon prop 传入字符串 `'User'`
- Element Plus 期望的是组件对象，不是字符串

**问题代码**:
```vue
<!-- 错误写法 -->
<el-avatar :size="36" :icon="msg.role === 'user' ? 'User' : 'ChatDotRound'" />

<!-- 正确写法 -->
<el-avatar :size="36" :icon="msg.role === 'user' ? User : ChatDotRound" />
```

**解决方案**:
1. 将 `User` 添加到图标导入列表
2. icon prop 使用组件对象而非字符串

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

**预防措施**:
1. Element Plus 图标组件的 icon prop 需要传入组件对象
2. 避免在模板中使用字符串引用图标组件

---

## E131: UserLoginLog约束错误导致503错误

**发生时间**: 2026-03-28

**错误类型**: 数据库约束错误

**错误描述**:
- 登录接口返回 503 Service Unavailable
- 后端日志显示: `IntegrityError: null value in column "user_id" violates not-null constraint`

**根本原因**:
- `views.py` 中登录失败时尝试创建 `UserLoginLog` 记录
- 传入 `user_id=None`，但该字段有非空约束

**问题代码**:
```python
# 错误写法
if user is None:
    UserLoginLog.objects.create(
        user_id=None,  # 违反非空约束
        login_ip=get_client_ip(request),
        login_status='failed'
    )
    return APIResponse.error(message='用户名或密码错误', ...)
```

**解决方案**:
移除登录失败时的日志创建逻辑（失败日志非关键数据）

**修改的文件**:
- `backend/apps/users/views.py`

**预防措施**:
1. 创建关联对象记录时，确保外键字段不为 null
2. 如外键可选，使用 `blank=True, null=True`
3. 失败操作可以不记录日志

---

## E132: AI Playground未自动选择默认LLM提供商

**发生时间**: 2026-03-28

**错误类型**: 前端业务逻辑

**功能描述**:
- 用户要求指定 Ollama 为默认提供商
- 数据库中"投标精灵"(ollama) 已标记 `is_default=True`

**解决方案**:
修改前端加载逻辑，优先使用 `is_default` 设置：

```javascript
// 修改后逻辑
const defaultProvider = providers.value.find(p => p.is_default)
if (defaultProvider) {
  selectedProvider.value = defaultProvider.id
} else {
  const ollamaProvider = providers.value.find(p => p.provider_type === 'ollama')
  if (ollamaProvider) {
    selectedProvider.value = ollamaProvider.id
  }
}
```

**修改的文件**:
- `frontend/src/views/system/AIPlayground.vue`

**预防措施**:
1. 前端加载提供商列表后，优先使用后端指定的默认提供商
2. 提供降级逻辑，防止默认提供商不可用时无法选择

---

## E133: formatDate未导入导致$setup.formatDate is not a function错误

**发生时间**: 2026-03-28

**错误类型**: 前端模块导入错误

**错误描述**:
- 控制台报错: `TypeError: $setup.formatDate is not a function`
- 错误来源: `error.mjs:22`

**根本原因**:
- `ScheduleList.vue` 模板中使用了 `formatDate` 函数（第53行和第175行）
- 但在 `<script setup>` 中没有导入该函数
- `formatDate` 定义在 `@/utils/date.js` 中

**问题代码**:
```javascript
// ScheduleList.vue 模板中使用
{{ row.last_run_at ? formatDate(row.last_run_at) : '-' }}

// 但 script setup 中没有导入
import { ref, reactive, onMounted } from 'vue'
// 缺少: import { formatDate } from '@/utils/date'
```

**解决方案**:
在 `ScheduleList.vue` 的 import 语句中添加:
```javascript
import { formatDate } from '@/utils/date'
```

**修改的文件**:
- `frontend/src/views/ScheduleList.vue`

**预防措施**:
1. 在 Vue 组件中使用任何工具函数前，必须先导入
2. 可以创建 ESLint 规则检查未定义的全局函数调用
3. 使用 VS Code 插件如 Volar 进行类型检查

---

## E134: 进度追踪API路由未注册导致404错误

**发生时间**: 2026-03-28

**错误类型**: URL路由配置错误

**错误描述**:
- 前端调用 `/api/v1/progress/tasks/` 返回 404
- 进度追踪功能无法使用

**根本原因**:
- `core/progress_views.py` 已创建并实现
- `core/progress_urls.py` 也已创建
- 但未在 `config/urls.py` 中注册路由

**问题代码**:
```python
# config/urls.py 缺少
path('api/v1/progress/', include('core.progress_urls')),
```

**解决方案**:
1. 创建 `backend/core/progress_urls.py` 路由配置
2. 在 `config/urls.py` 中添加进度API路由注册

**修改的文件**:
- `backend/core/progress_urls.py` (新建)
- `backend/config/urls.py`

**预防措施**:
1. 创建新的API模块时，必须同时注册URL路由
2. 使用脚手架工具自动生成完整的模块结构

---

## E135: BidRecordListSerializer缺少team_member_ids字段

**发生时间**: 2026-03-28

**错误类型**: Serializer字段缺失

**错误描述**:
- 编辑投标记录时，无法回填团队成员选择
- `bidForm.team_member_ids` 始终为空数组

**根本原因**:
- `BidRecordListSerializer` 只有 `team_members` (用于写入) 和 `team_member_names` (用于显示)
- 缺少 `team_member_ids` 字段用于列表数据的回填

**解决方案**:
在 `BidRecordListSerializer` 中添加:
```python
team_member_ids = serializers.SerializerMethodField()

def get_team_member_ids(self, obj):
    return list(obj.team_members.values_list('id', flat=True))
```

**修改的文件**:
- `backend/apps/bids/serializers.py`

**预防措施**:
1. Serializer的列表视图和详情视图需要包含不同的字段
2. 编辑功能需要的字段必须能从列表API返回
3. 前后端字段命名必须保持一致

---

## E136: ScheduleList.vue路由跳转逻辑错误

**发生时间**: 2026-03-28

**错误类型**: 前端业务逻辑错误

**错误描述**:
- 点击"新建计划"和"编辑"按钮跳转到不存在的路由
- 页面实际已有对话框模板，但未被使用

**问题代码**:
```javascript
// 错误的实现
const showCreateDialog = () => {
  router.push('/schedules/create')  // 路由不存在
}

const showEditDialog = (row) => {
  router.push(`/schedules/edit/${row.id}`)  // 路由不存在
}
```

**解决方案**:
修改为直接使用页面内的对话框:
```javascript
const showCreateDialog = () => {
  isEdit.value = false
  currentId.value = null
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = async (row) => {
  isEdit.value = true
  currentId.value = row.id
  const res = await crawlerApi.getCrawlScheduleDetail(row.id)
  // 回填表单数据...
  dialogVisible.value = true
}
```

**修改的文件**:
- `frontend/src/views/ScheduleList.vue`

**预防措施**:
1. 对话框模式应直接显示/隐藏，而非页面跳转
2. 页面跳转适用于完全不同的视图，不适合模态对话框
3. 先检查是否存在对应的路由，再决定使用哪种方式

---

## E137: scheduler_views.py响应格式不统一

**发生时间**: 2026-03-28

**错误类型**: API响应格式不一致

**错误描述**:
- 部分接口返回 `Response({...})` 直接格式
- 部分接口返回 `APIResponse.success(...)` 统一格式
- 前端需要处理多种响应格式

**问题代码**:
```python
# 不统一的写法
return Response({
    'message': '采集计划已启用',
    'schedule': CrawlScheduleSerializer(schedule).data
})

# 正确的写法
return APIResponse.success(
    message='采集计划已启用',
    data={'schedule': CrawlScheduleSerializer(schedule).data}
)
```

**解决方案**:
将所有 `Response({...})` 替换为 `APIResponse.success(...)` 或 `APIResponse.not_found(...)`

**修改的文件**:
- `backend/apps/crawler/scheduler_views.py`

**预防措施**:
1. 统一使用 `APIResponse` 类处理所有响应
2. 在代码审查时检查响应格式一致性
3. 可以创建 ESLint 规则禁止直接使用 `Response({`

---

## E138: 缺少调度器相关错误码

**发生时间**: 2026-03-28

**错误类型**: 错误码体系不完整

**错误描述**:
- 调度器模块缺少专用的错误码
- 使用通用错误码无法精确描述问题

**解决方案**:
在 `error_codes.py` 中添加调度器相关错误码:
```python
# 调度器相关错误 (81xx)
SCHEDULE_NOT_FOUND = ("8101", "采集计划不存在", 404)
SCHEDULE_RUNNING = ("8102", "采集计划正在执行中", 409)
SCHEDULE_DISABLED = ("8103", "采集计划已禁用", 400)
SCHEDULE_INVALID_CRON = ("8104", "定时表达式无效", 400)
SCHEDULE_TEMPLATE_NOT_FOUND = ("8105", "网站模板不存在", 404)
SCHEDULE_EXECUTION_FAILED = ("8106", "采集执行失败", 500)
QUALIFICATION_MATCH_FAILED = ("8107", "资质匹配执行失败", 500)
```

**修改的文件**:
- `backend/common/constants/error_codes.py`

**预防措施**:
1. 创建新模块时，同时添加该模块专用的错误码
2. 使用错误码枚举而非硬编码数字
3. 错误码应覆盖该模块的所有常见错误场景

---

*本文档已更新 E134-E138 架构一致性审查错误记录*

---

## E141: crawler.js API调用参数双重嵌套导致check_duplicate_name 404错误

**发生时间**: 2026-03-28

**错误描述**:
前端调用 `checkScheduleNameDuplicate` API时返回404错误，URL显示参数被双重嵌套为 `params%5Bname%5D=test` 而不是 `name=test`。

**错误日志**:
```
GET http://localhost:8081/api/v1/crawler/schedules/check_duplicate_name/?params%5Bname%5D=%E5%BC%A0%E5%B9%B2%E7%9A%84%E8%AE%A1%E5%88%92 404 (Not Found)
```

**根因分析**:
- `request.get(url, { params })` 导致 params 对象被嵌套两次
- request.js 内部实现: `axiosInstance.get(url, { params, ...options })`
- 当传入 `{ params: { name: 'xxx' } }` 时，实际发送的URL参数变成 `params[name]=xxx`

**问题代码** (frontend/src/api/crawler.js):
```javascript
checkScheduleNameDuplicate(name, excludeId = null) {
  const params = { name }
  if (excludeId) {
    params.exclude_id = excludeId
  }
  return request.get(`${BASE_URL}/schedules/check_duplicate_name/`, { params })  // 错误：双重嵌套
}
```

**修复方案**:
```javascript
checkScheduleNameDuplicate(name, excludeId = null) {
  const params = { name }
  if (excludeId) {
    params.exclude_id = excludeId
  }
  return request.get(`${BASE_URL}/schedules/check_duplicate_name/`, params)  // 直接传递params对象
}
```

**修改的文件**:
- `frontend/src/api/crawler.js`

**预防措施**:
1. 使用request.get/post等方法时，直接传递参数对象，不要再包装一层params
2. 注意request.js的实现差异：`request.get(url, params)` vs `axios.get(url, { params })`
3. 编写API调用后，使用浏览器开发者工具检查实际发送的URL参数

---

## E142: CrawlScheduleCreateSerializer website_template字段必填导致400错误

**发生时间**: 2026-03-28

**错误描述**:
前端在"手动输入"模式创建采集计划时返回400 Bad Request错误，后端验证失败。

**错误日志**:
```
POST http://localhost:8081/api/v1/crawler/schedules/ 400 (Bad Request)
保存失败: AxiosError: Request failed with status code 400
```

**根因分析**:
- 后端 `CrawlScheduleCreateSerializer` 中 `website_template` 是 ForeignKey 字段，默认必填
- 前端在 `inputMode === 'manual'` 时不选择网站模板，但提交时仍包含 `website_template: null`
- DRF serializer 将 `null` 视为验证失败（对于非 nullable 的 ForeignKey）

**问题代码** (backend/apps/crawler/scheduler_serializers.py):
```python
class CrawlScheduleCreateSerializer(serializers.ModelSerializer):
    """
    创建采集计划序列化器
    """
    class Meta:
        model = CrawlSchedule
        fields = [
            'name', 'website_template', 'crontab', 'is_active',  # website_template 默认可选但实际必填
            ...
        ]
```

**修复方案**:
```python
class CrawlScheduleCreateSerializer(serializers.ModelSerializer):
    """
    创建采集计划序列化器
    """
    website_template = serializers.PrimaryKeyRelatedField(
        queryset=WebsiteTemplate.objects.all(),
        required=False,
        allow_null=True,
        help_text='网站模板ID'
    )
    # ... rest of serializer
```

**修改的文件**:
- `backend/apps/crawler/scheduler_serializers.py` - 添加了 website_template 显式定义
- 同时需要为 `CrawlScheduleUpdateSerializer` 添加相同修改

**预防措施**:
1. ForeignKey 字段在前端可选的情况下，后端 serializer 必须显式设置 `required=False, allow_null=True`
2. 不要依赖 Django model 的 null=True/blank=True 设置，必须在 DRF serializer 中显式声明
3. 创建/更新 serializer 时，检查所有前端可能不提交的字段，确保它们都设置了正确的可选性

---

## E142: 前端代理ECONNREFUSED错误导致500状态码

**发生时间**: 2026-03-28

**错误描述**:
浏览器控制台显示 `POST http://localhost:8081/api/v1/enterprise/enterprises/ 500 (Internal Server Error)`，但后端日志中实际没有对应的500错误记录。

**错误日志**:
```
request.js:300  POST http://localhost:8081/api/v1/enterprise/enterprises/ 500 (Internal Server Error)
Proxy error: Could not proxy request /api/v1/enterprise/enterprises/ from localhost:8081 to http://localhost:8000.
See https://nodejs.org/api/errors.html#errors_common_system_errors for more information (ECONNREFUSED).
```

**根本原因**:
- 前端开发服务器(vue-cli-service)启动时后端服务器尚未启动
- Node.js的http-proxy代理无法连接到后端服务器，返回ECONNREFUSED
- 代理错误被映射为500状态码返回给前端

**发生场景**:
1. 前端服务先启动，后端服务后启动
2. 后端服务崩溃或无响应
3. 网络配置问题导致代理无法连接到目标服务器

**验证方法**:
1. 检查后端服务是否正常运行: `netstat -an | Select-String "8000.*LISTENING"`
2. 直接用curl测试后端: `curl http://localhost:8000/api/v1/enterprise/enterprises/`
3. 查看后端日志确认是否有实际请求

**解决方案**:
1. 确保启动顺序正确：先启动后端，再启动前端
2. 如果后端崩溃，重启后端服务
3. 检查端口占用: `netstat -ano | Select-String ":8000"`

**预防措施**:
1. 使用docker-compose或脚本确保启动顺序
2. 添加健康检查endpoint让前端可以检测后端状态
3. 在前端添加更好的错误提示，区分"后端未启动"和"服务器内部错误"

---

## E143: BaseViewSet MRO错误导致API返回数组而非统一格式

**发生时间**: 2026-03-28

**错误描述**:
新增企业时显示"保存成功"，但企业列表为空。前端显示"保存成功"是因为create响应正确，但fetchEnterpriseList获取的数据格式错误导致列表无法显示。

**错误日志**:
```
# 后端API返回（错误格式）：
[
  {"id": 1, "name": "企业1", ...},
  {"id": 2, "name": "企业2", ...}
]

# 前端期望格式：
{
  "success": true,
  "code": 0,
  "message": "操作成功",
  "data": [...]
}
```

**根本原因**:
`BaseViewSet` 的多继承顺序问题：
```python
# 错误顺序 - viewsets.ModelViewSet优先
class BaseViewSet(
    viewsets.ModelViewSet,  # list方法来自这里
    ListActionMixin,          # 被忽略
    ...
):
```

DRF的 `ModelViewSet.list` 方法优先于 `ListActionMixin.list` 被调用，导致响应格式不统一。

**问题代码** (common/views/base.py):
```python
class BaseViewSet(
    viewsets.ModelViewSet,  # ❌ 错误：应在最后
    ListActionMixin,
    CreateActionMixin,
    ...
):
```

**修复方案**:
调整继承顺序，让Mixin的方法优先：
```python
class BaseViewSet(
    ListActionMixin,         # ✅ 正确：Mixin优先
    CreateActionMixin,
    UpdateActionMixin,
    DestroyActionMixin,
    RetrieveActionMixin,
    viewsets.ModelViewSet,  # ✅ 正确
):
```

**修改的文件**:
- `common/views/base.py` - 调整 BaseViewSet 和 ReadOnlyModelViewSet 的继承顺序

**预防措施**:
1. 在设计多继承ViewSet时，确保Mixin在基类之前
2. 编写单元测试验证API响应格式
3. 使用统一响应格式装饰器确保一致性

---

## E144: 资质类型选项不匹配导致400错误（更新）

**发生时间**: 2026-03-28

**错误描述**:
保存资质信息时返回400 Bad Request错误，前端显示"保存失败"，后端日志显示:
1. `"municipal_engineering" 不是合法选项`
2. `"日期格式错误。请从这些格式中选择：YYYY-MM-DD"`

**错误日志**:
```
# 后端错误
WARNING 2026-03-28 11:52:45,096 [EnterpriseQualificationViewSet] POST /api/v1/enterprise/qualifications/ - Status: 400, Error: {
  'qualification_type': [ErrorDetail(string='"municipal_engineering" 不是合法选项。', code='invalid_choice')],
  'issue_date': [ErrorDetail(string='日期格式错误。请从这些格式中选择：YYYY-MM-DD。', code='invalid')],
  'expiry_date': [ErrorDetail(string='日期格式错误。请从这些格式中选择：YYYY-MM-DD。', code='invalid')]
}
```

**根本原因**:
1. 前端使用错误的常量 `QUALIFICATION_TYPE_CHOICES`（建筑施工类型）
2. 后端实际使用的是 `ENTERPRISE_QUAL_TYPE_CHOICES`（企业证照类型）
3. 日期字段为空时前端发送空字符串 `""` 而非 `null`

**问题代码** (frontend/src/views/CompanyInfo.vue):
```javascript
// 前端错误的选项（第一次修复使用了错误的常量）
<el-option label="建筑工程施工总承包" value="building_construction" />  // ❌ 应该用business_license等
```

**后端正确选项** (core/constants.py):
```python
# 企业证照类型（模型实际使用的）
ENTERPRISE_QUAL_TYPE_CHOICES = [
    ('business_license', '营业执照'),
    ('qualification_cert', '资质证书'),
    ('safety_cert', '安全生产许可证'),
    ('iso_cert', 'ISO认证'),
    ('industry_cert', '行业资质'),
    ('other', '其他'),
]
```

**修复方案**:
1. 修改资质类型选项为正确的 `ENTERPRISE_QUAL_TYPE_CHOICES` 值
2. 保存前将空日期字符串转换为 `null`

**修改的文件**:
- `frontend/src/views/CompanyInfo.vue` - 修复资质类型选项值和日期字段处理

**预防措施**:
1. 前后端选项值必须保持一致，优先从后端API获取选项列表
2. 空日期字段应发送 `null` 而非空字符串
3. 建立选项值对照表，避免前后端不一致

---

## E145: filterset_fields字段名错误导致500错误

**发生时间**: 2026-03-28

**错误描述**:
GET `/api/v1/enterprise/qualifications/?params[enterprise]=3` 返回 500 Internal Server Error

**错误日志**:
```
django.core.exceptions.FieldError: Unsupported lookup 'qualification_type' for EnterpriseQualification or join on the field not permitted.
```

**根本原因**:
`EnterpriseQualificationViewSet` 中的 `filterset_fields` 使用了 `qualification_type`，但模型中实际的字段名是 `qualification_category`

**问题代码** (backend/apps/enterprise/views.py):
```python
class EnterpriseQualificationViewSet(AuthenticatedModelViewSet):
    queryset = EnterpriseQualification.objects.select_related('enterprise')
    serializer_class = EnterpriseQualificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'qualification_type', 'is_valid', 'is_primary']  # ❌
    # 应该是 'qualification_category'
```

**修复方案**:
```python
filterset_fields = ['enterprise', 'qualification_category', 'is_valid', 'is_primary']
```

**修改的文件**:
- `backend/apps/enterprise/views.py` - 修复 filterset_fields 字段名

**预防措施**:
1. DjangoFilterBackend 的 filterset_fields 必须与模型字段名完全一致
2. 新增模型字段后，检查所有使用 filterset_fields 的视图集

---

## E146: 资质名称值不在choices中导致400错误

**发生时间**: 2026-03-28

**错误描述**:
POST `/api/v1/enterprise/qualifications/` 返回 400 Bad Request

**错误日志**:
```json
{"qualification_name": "「building_construction」不是合法选项。"}
```

**根本原因**:
前端发送的 `qualification_name` 值为 `building_construction`，但 `QUALIFICATION_NAME_CHOICES` 中不存在该值

**问题代码**:
```javascript
// 前端 CompanyInfo.vue 中可能的错误选项
<el-option label="建筑工程施工总承包" value="building_construction" />
```

**后端正确的值** (core/constants.py):
```python
QUALIFICATION_NAME_CHOICES = [
    # 建筑业企业资质 - 施工总承包
    ('construction_general_building', '建筑工程施工总承包'),  # ✅ 正确
    ('construction_general_municipal', '市政公用工程施工总承包'),
    # ...
]
```

**修复方案**:
前端资质名称选项值必须使用后端 `QUALIFICATION_NAME_CHOICES` 中定义的值：
- `construction_general_building` (不是 `building_construction`)
- `construction_general_municipal` (不是 `municipal_engineering`)

**修改的文件**:
- `frontend/src/views/CompanyInfo.vue` - 确保资质名称选项值与后端一致

**预防措施**:
1. 前后端选项值必须保持一致，优先从后端API获取选项列表
2. 避免硬编码选项值，建立统一的常量管理

---

## E147: 模型连接自动重连功能实现

**发生时间**: 2026-03-28

**功能类型**: 新功能开发

**功能描述**:
实现自动模型连接功能，用户登录后无需手动点击"模型选择"按钮，系统自动完成模型连接。

**实现内容**:

### 1. 新增文件
- `frontend/src/store/modelConnection.js` - 模型连接状态管理Store（Pinia）
  - 管理连接状态、自动重连和健康检测
  - 每30秒自动检测连接健康状态
  - 指数退避重连策略（5秒 → 10秒 → 20秒 → 最大60秒）
  - 连续3次失败后进入高级重试模式
  - 空闲30分钟后自动释放连接

- `frontend/src/composables/useModelAutoConnect.js` - 自动连接Composable
  - 提供登录后自动连接触发
  - 状态监控和用户反馈功能

### 2. 修改文件
- `frontend/src/views/Layout.vue` - 添加模型连接状态指示器
- `frontend/src/store/index.js` - 导出新增Store
- `frontend/src/composables/index.js` - 导出新增Composable

### 3. 功能特性
- **登录后自动连接**: 用户成功登录后自动触发模型连接
- **状态指示器**: 顶部导航栏显示连接状态（绿色已连接、黄色连接中、红色异常）
- **自动恢复**: 连接异常时自动重新建立连接
- **用户反馈**: ElMessage显示状态提示

**预防措施**:
1. 状态管理统一使用Pinia Store
2. 定时器需要在组件卸载时清理
3. 错误处理需要考虑服务未启动等边界情况

---

## E148: onUnmounted警告 - Vue生命周期钩子使用错误

**发生时间**: 2026-03-28

**错误类型**: 前端组件生命周期错误

**错误描述**:
浏览器控制台显示警告：`[Vue warn]: onUnmounted is called when there is no active component instance to be associated with.`

**错误原因**:
在`<script setup>`的异步`onMounted`回调函数内部调用`onUnmounted`，但`onUnmounted`需要在同步代码中调用才能正确关联组件实例。

**问题代码**:
```javascript
onMounted(async () => {
  // ...
  onUnmounted(() => clearInterval(interval)) // 错误：在异步上下文中调用
})
```

**修复方案**:
使用`onMounted`的返回值进行清理，而不是在异步回调中调用`onUnmounted`：

```javascript
onMounted(() => {
  const interval = setInterval(fetchUnreadCount, 60000)
  return () => {
    clearInterval(interval)
  }
})
```

**修改的文件**:
- `frontend/src/views/Layout.vue`

**预防措施**:
1. 生命周期钩子必须在同步代码中调用
2. 使用返回值进行异步清理操作
3. 避免在`onMounted`的异步回调中使用其他生命周期钩子

---

## E149: 模型连接失败 - 状态管理错误

**发生时间**: 2026-03-28

**错误类型**: 前端状态管理逻辑错误

**错误描述**:
登录后自动连接模型时显示"所有模型连接失败"错误，但实际是状态管理问题。

**错误原因**:
1. `testAllConnections`函数设置`isConnecting.value = true`但没有在finally中重置
2. 当没有模型配置或所有连接都失败时，抛出异常而不是友好处理

**问题代码**:
```javascript
async function testAllConnections() {
  isConnecting.value = true // 设置了但未重置
  // ...
  if (successCount > 0) {
    return true
  } else {
    throw new Error('所有模型连接失败') // 错误：不考虑服务未启动等正常情况
  }
}
```

**修复方案**:
1. 将`isConnecting.value = true`移到`autoConnect`函数中统一管理
2. 在`testAllConnections`的finally中重置`isConnecting`
3. 当没有模型或所有连接失败时，显示"模型服务已就绪"而不是报错

```javascript
async function autoConnect() {
  isConnecting.value = true
  try {
    const testResults = await testAllConnections()
    const successCount = testResults.filter(r => r.status === 'success').length
    const totalCount = testResults.length

    if (totalCount === 0) {
      connectionStatus.value = 'connected'
      statusMessage.value = '模型服务已就绪'
      return true
    }
    // ...
  } finally {
    isConnecting.value = false
  }
}
```

**修改的文件**:
- `frontend/src/store/modelConnection.js`

**预防措施**:
1. 状态标志位需要在所有代码路径中正确重置（使用finally）
2. 区分"服务未启动"和"连接失败"两种情况
3. 避免在边界情况下抛出异常，提供友好提示

---

## E101: 项目清理 - 审计清理未使用代码和配置

**发生时间**: 2026-03-27

**清理类型**: 项目架构优化

**清理内容**:

### 1. 前端未使用组件清理
删除以下未使用组件：
- `components/SearchBox.vue`
- `components/TableActions.vue`
- `components/VirtualTable.vue`
- `components/SectionHeader.vue`
- `components/PageTemplate.vue`
- `composables/usePagination.js`

同步更新导出文件：
- `components/index.js`
- `composables/index.js`

### 2. 重复API模块清理
删除 `common/api/` 目录（5个文件）：
- `ApiClient.js`
- `tenderApi.js`
- `bidApi.js`
- `enterpriseApi.js`
- `formatters.js`
- `index.js`

### 3. 分布式爬虫清理
删除 `backend/distributed_crawler/` 目录（8个文件）
删除 `Dockerfile.scrapy`
从 `requirements.txt` 移除 scrapy 相关依赖
从 `docker-compose.yml` 移除 scrapy-worker 服务配置

### 4. 前端工具函数
新增 `utils/date.js` 日期格式化工具

**预防措施**:
1. 定期进行项目审计
2. 删除代码后同时清理import语句
3. 删除文件后同时清理导出声明

<!-- 今日新增 E097, E098, E099 -->

<!-- E077-E083: ESLint清理 - 今天完成的所有代码质量修复 -->

---

## E065: Celery配置缺少Celery导入

**发生时间**: 2026-03-26

**错误类型**: 代码错误

**错误描述**:
- `config/celery.py` 第11行引用 `Celery` 但未导入
- 导致Celery应用无法初始化

**错误信息**:
```
NameError: name 'Celery' is not defined
```

**错误代码**:
```python
# config/celery.py
from kombu import Queue, Exchange
from kombu.transport.redis import Transport  # 导入了Transport但没导入Celery

app = Celery('bid_auto_system')  # Celery未导入
```

**解决方案**:
在第6行添加Celery导入：
```python
from celery import Celery
from kombu import Queue, Exchange
from kombu.transport.redis import Transport
```

**预防措施**:
1. 配置文件头部添加所有需要的导入
2. 使用IDE的导入检查功能

**相关文件**:
- `backend/config/celery.py`

---

## E066: FastAPI缺少sse-starlette依赖

**发生时间**: 2026-03-26

**错误类型**: 模块依赖缺失

**错误描述**:
- FastAPI应用无法启动
- `sse_starlette` 模块未安装

**错误信息**:
```
ModuleNotFoundError: No module named 'sse_starlette'
```

**发生场景**:
- 尝试导入 `from sse_starlette.sse import EventSourceResponse` 时

**解决方案**:
```bash
pip install sse-starlette==1.8.2
```

**预防措施**:
1. requirements.txt中已列出依赖，确认安装完整
2. 新增依赖后执行 `pip install -r requirements.txt`

**相关文件**:
- `backend/fastapi_app/api/crawler.py`
- `backend/requirements.txt`

---

## E067: Milvus客户端pymilvus未安装

**发生时间**: 2026-03-26

**错误类型**: 模块依赖缺失

**错误描述**:
- Milvus向量数据库客户端未安装
- 向量检索功能无法使用

**错误信息**:
```
ModuleNotFoundError: No module named 'pymilvus'
```

**发生场景**:
- 尝试连接Milvus服务时

**解决方案**:
使用阿里云镜像安装（解决网络超时问题）：
```bash
pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com pymilvus
```

**预防措施**:
1. requirements.txt中已列出依赖 `pymilvus`
2. 配置国内镜像源避免网络超时

**相关文件**:
- `backend/services/vector/milvus_service.py`
- `backend/fastapi_app/services/milvus_client.py`
- `backend/requirements.txt`

---

## E068: Scrapy-Redis分布式爬虫模块未安装

**发生时间**: 2026-03-26

**错误类型**: 模块依赖缺失

**错误描述**:
- Scrapy和Scrapy-Redis未安装
- 分布式爬虫功能无法使用

**错误信息**:
```
ModuleNotFoundError: No module named 'scrapy'
ModuleNotFoundError: No module named 'scrapy_redis'
```

**解决方案**:
使用阿里云镜像安装（解决网络超时问题）：
```bash
pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com scrapy==2.11.0 scrapy-redis==0.7.3
```

**预防措施**:
1. requirements.txt中已列出依赖
2. 配置国内镜像源避免网络超时

---

## 可用性检查总结 (2026-03-26)

### 正常运行的组件
| 组件 | 状态 |
|------|------|
| Django后端 | ✅ 正常 |
| 前端Vue | ✅ 正常 |
| PostgreSQL | ✅ 正常 |
| Redis驱动 | ✅ 正常 |
| Docker Compose | ✅ 配置完整 |

### 需要修复的问题
| 优先级 | 问题 | 解决方案 |
|--------|------|----------|
| 高 | Celery配置缺少导入 | 添加 `from celery import Celery` |
| 高 | 缺少sse-starlette | `pip install sse-starlette` |
| 中 | 缺少pymilvus | `pip install pymilvus` |

---

## E073: 中标结果录入字段名错误

**发生时间**: 2026-03-26

**错误类型**: 前后端字段不一致

**错误描述**:
- 前端提交中标结果时返回400 Bad Request错误
- 原因：前端发送的字段名为 `bid_record_id`，但后端序列化器期望的是 `bid_record`

**发生场景**:
- 在 `TenderList.vue` 的 `submitResultForm` 函数中
- 用户填写中标结果表单后点击提交
- 后端返回400错误，无法创建中标结果记录

**错误代码**:
```javascript
// TenderList.vue 第698行 - 错误写法
const data = {
  bid_record_id: resultForm.bid_record_id,  // ❌ 字段名错误
  result_type: resultForm.result_type,
  winner_name: resultForm.winner_name || null,
  // ...
}
```

**后端序列化器期望** (`BidResultCreateSerializer`):
```python
class BidResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidResult
        fields = [
            'bid_record',  # ✅ 后端期望这个字段名
            'result_type',
            'winner_name',
            # ...
        ]
```

**错误信息**:
```
PATCH/POST /api/v1/bids/results/ 400 (Bad Request)
```

**解决方案**:
修改前端 `TenderList.vue` 第698行，将 `bid_record_id` 改为 `bid_record`：

```javascript
// 正确写法
const data = {
  bid_record: resultForm.bid_record_id,  // ✅ 修正为 bid_record
  result_type: resultForm.result_type,
  winner_name: resultForm.winner_name || null,
  // ...
}
```

**影响范围**:
- 中标结果录入功能完全无法使用
- 所有用户点击"录入中标结果"按钮都会失败

**预防措施**:
1. 前后端字段命名必须保持一致
2. 在创建序列化器时，同时创建对应的前端类型定义
3. API字段变更时，同步更新前后端代码
4. 使用API文档工具（如Swagger）自动生成前端API类型

**相关文件**:
- `frontend/src/views/tender/TenderList.vue` - 已修复
- `backend/apps/bids/serializers.py` - BidResultCreateSerializer

---

## E074: 投标记录team_members字段前端表单缺失

**发生时间**: 2026-03-26

**错误类型**: 前后端字段缺失

**错误描述**:
- 后端序列化器 `BidRecordCreateSerializer` 包含 `team_members` 字段
- 但前端 `TenderList.vue` 的表单中没有团队成员输入控件
- 导致无法通过前端为投标记录添加团队成员

**发生场景**:
- 用户在 `TenderList.vue` 创建或编辑投标记录时
- 表单中缺少"团队成员"选择字段

**错误代码**:
```javascript
// 前端 bidForm 缺少 team_member_ids 字段
const bidForm = reactive({
  tender_id: null,
  bid_code: '',
  // ... 缺少 team_member_ids
})
```

**后端序列化器** (`BidRecordCreateSerializer`):
```python
class Meta:
    model = BidRecord
    fields = [
        'tender', 'bid_code', 'bid_price', 'bid_date', 'status',
        'bid_documents', 'bid_manager', 'team_members',  # ✅ 后端有
        'notes', 'win_probability', 'competitor_count'
    ]
```

**解决方案**:
1. 在 `TenderList.vue` 表单中添加多选团队成员控件
2. 在 `bidForm` reactive 对象中添加 `team_member_ids: []`
3. 在 `submitBidForm()` 提交数据中添加 `team_members: bidForm.team_member_ids`

**相关文件**:
- `frontend/src/views/tender/TenderList.vue` - 已修复
- `backend/apps/bids/serializers.py` - BidRecordCreateSerializer

---

## E075: 投标记录API字段名错误

**发生时间**: 2026-03-26

**错误类型**: 前后端字段不一致

**错误描述**:
- 前端提交投标记录时使用 `tender_id` 和 `bid_manager_id`
- 但后端序列化器期望的是 `tender` 和 `bid_manager`

**错误代码**:
```javascript
// 错误写法 - TenderList.vue
const data = {
  tender_id: bidForm.tender_id,       // ❌ 应该是 tender
  bid_manager_id: bidForm.bid_manager_id,  // ❌ 应该是 bid_manager
}
```

**正确写法**:
```javascript
const data = {
  tender: bidForm.tender_id,           // ✅ 正确
  bid_manager: bidForm.bid_manager_id,  // ✅ 正确
  team_members: bidForm.team_member_ids, // ✅ 新增
}
```

**解决方案**:
修改前端 `TenderList.vue` 的 `submitBidForm()` 函数，将字段名改为与后端序列化器一致

**相关文件**:
- `frontend/src/views/tender/TenderList.vue` - 已修复

---

## E076: 企业扩展字段前端控件缺失

**发生时间**: 2026-03-26

**错误类型**: 前端表单缺失

**错误描述**:
- 后端 `Enterprise` 模型包含 `auto_bid_keywords`、`notification_channels`、`tags` 等扩展字段
- `EnterpriseSerializer` 序列化器也包含这些字段
- 但 `EnterpriseForm.vue` 中只有部分字段的输入控件

**发生场景**:
- 用户编辑企业信息时
- 无法配置自动投标关键词、通知渠道等扩展功能

**错误代码**:
```javascript
// EnterpriseForm.vue defaultForm 已有字段，但模板缺少控件
const defaultForm = {
  auto_bid_keywords: [],      // ✅ 数据结构存在
  notification_channels: [],  // ✅ 数据结构存在
  tags: [],                   // ✅ 数据结构存在
  // ...
}
```

**解决方案**:
1. 在 `EnterpriseForm.vue` 模板中添加"自动投标关键词"多选输入控件
2. 添加"通知渠道"复选框组（钉钉、企业微信、邮件、短信）
3. 重构 `handleSave()` 函数，确保数组字段正确处理和提交

**相关文件**:
- `frontend/src/views/company/EnterpriseForm.vue` - 已修复

---

### E077: ESLint清理 - ConfirmDialog等组件未使用的import导入

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- ConfirmDialog.vue、CrudTable.vue、PageTemplate.vue等组件中导入了未使用的vue API
- ConfirmDialog导入了`ref`, `watch`但未使用
- CrudTable导入了`ref`, `watch`但未使用
- PageTemplate导入了`ref`, `watch`但未使用

**发生场景**:
- 代码重构后删除使用了这些变量的代码，但忘记清理导入语句

**解决方案**:
```javascript
// ConfirmDialog.vue - 移除
import { ref, computed, watch } from 'vue'
// 改为
import { computed } from 'vue'

// CrudTable.vue - 移除
import { ref, computed, watch } from 'vue'
// 改为
import { computed } from 'vue'

// PageTemplate.vue - 移除
import { ref, reactive, computed, watch } from 'vue'
// 改为
import { reactive, computed, watch } from 'vue'
```

**预防措施**:
1. 删除使用的变量后，立即清理对应的import语句
2. 使用IDE的"Optimize Imports"功能自动清理
3. 运行`npm run lint`检查未使用的导入

**相关文件**:
- `frontend/src/components/ConfirmDialog.vue`
- `frontend/src/components/CrudTable.vue`
- `frontend/src/components/PageTemplate.vue`

---

### E078: ESLint清理 - StatCard等组件未使用的图标组件导入

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- StatCard.vue导入了`Top`, `Bottom`, `TrendCharts`, `DataLine`, `Odometer`但未使用
- ConfirmDialog.vue导入了`WarningFilled`, `CircleCheckFilled`, `CircleCloseFilled`, `InfoFilled`但未使用

**发生场景**:
- 最初设计需要这些图标，但后来通过动态组件方式实现了相同功能

**解决方案**:
```javascript
// StatCard.vue - 移除所有图标导入
import { computed } from 'vue'

// ConfirmDialog.vue - 移除所有图标导入
import { computed } from 'vue'
```

**预防措施**:
1. 使用动态图标时，直接在模板中使用字符串名称，不需要导入
2. 删除使用的图标组件后，立即清理import语句

**相关文件**:
- `frontend/src/components/StatCard.vue`
- `frontend/src/components/ConfirmDialog.vue`

---

### E079: ESLint清理 - Layout等视图未使用的vue导入和图标导入

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- Layout.vue导入了`watch`, `Fold`, `Expand`但未使用
- SidebarNav.vue定义了props但只使用了部分属性

**发生场景**:
- 重构过程中删除了使用这些变量/属性的代码，但忘记清理

**解决方案**:
```javascript
// Layout.vue
import { ref, computed, onMounted, watch } from 'vue'
// 改为
import { ref, computed, onMounted } from 'vue'

import { Fold, Expand, Bell, User, Setting, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
// 改为
import { Bell, User, Setting, ArrowDown, SwitchButton } from '@element-plus/icons-vue'

// SidebarNav.vue
const props = defineProps({ ... })
// 改为
const { isCollapse, unreadCount } = defineProps({ ... })
```

**预防措施**:
1. 使用解构方式定义props，只获取实际使用的属性
2. 删除使用的变量后，立即清理对应的import语句

**相关文件**:
- `frontend/src/views/Layout.vue`
- `frontend/src/components/SidebarNav.vue`

---

### E080: ESLint清理 - useStatistics未使用的watch/cards/message

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- useStatistics.js导入了`watch`但未使用
- useStatistics.js定义了`cards`变量但未使用
- useStatistics.js调用了`useMessage()`但未使用返回值

**发生场景**:
- 最初设计需要这些功能，但后来删除了相关代码

**解决方案**:
```javascript
// useStatistics.js
import { ref, reactive, computed, onMounted, watch } from 'vue'
// 改为
import { ref, reactive, computed, onMounted } from 'vue'

// 删除 useMessage 导入
import { useMessage } from './usePagination'
// 删除此行

// 删除 cards 和 message
const {
  fetchApi,
  defaultParams = {},
  immediate = true
} = options
// 删除了 cards = [] 和 message = useMessage()
```

**预防措施**:
1. composable函数中只导入实际使用的API
2. 解构选项对象时只获取实际使用的属性

**相关文件**:
- `frontend/src/composables/useStatistics.js`

---

### E081: ESLint清理 - directives/index.js未使用的createApp

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- directives/index.js导入了`createApp`但未使用

**发生场景**:
- 最初设计可能需要创建独立Vue应用，但后来删除了相关代码

**解决方案**:
```javascript
// directives/index.js
/**
 * 图片懒加载指令
 * 用于优化图片加载性能
 */
import { createApp } from 'vue'  // 删除此行
```

**预防措施**:
1. 删除使用的函数后，立即清理对应的import语句

**相关文件**:
- `frontend/src/directives/index.js`

---

### E082: ESLint清理 - AutomationDashboard未使用的viewWorkflow函数

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- AutomationDashboard.vue定义了`viewWorkflow`函数但从未被调用

**发生场景**:
- 最初设计需要此功能，但后来需求变更，函数未被删除

**解决方案**:
```javascript
// 删除整个 viewWorkflow 函数
const viewWorkflow = async (row) => {
  try {
    const res = await request.get(`/v1/openclaw/automation/status/?workflow_id=${row.workflow_id}`)
    if (res.data?.success) {
      currentWorkflow.value = res.data.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}
```

**预防措施**:
1. 删除不再使用的函数，保持代码整洁
2. 使用IDE的"Find Usages"功能确认函数是否被调用后再删除

**相关文件**:
- `frontend/src/views/automation/AutomationDashboard.vue`

---

### E083: ESLint清理 - AIPlayground等文件未使用的变量/e参数

**发生时间**: 2026-03-26

**错误类型**: ESLint代码质量

**错误描述**:
- AIPlayground.vue导入了`User`图标但未使用
- AIPlayground.vue定义了`handleShiftEnter(e)`但从未使用e参数
- AIPlayground.vue的catch块中定义了`e`但未使用
- AIPlayground.vue有空的catch块
- EnterpriseForm.vue导入了`computed`但未使用
- ModelConfig.vue导入了`computed`但未使用
- DocumentsTab.vue定义了`props`但只使用了部分属性

**发生场景**:
- 重构过程中删除了使用这些变量的代码，但忘记清理

**解决方案**:
```javascript
// AIPlayground.vue
import { ChatDotRound, Promotion, Clock, Connection, User } from '@element-plus/icons-vue'
// 改为
import { ChatDotRound, Promotion, Clock, Connection } from '@element-plus/icons-vue'

const handleShiftEnter = (e) => {  // 删除e参数
// 改为
const handleShiftEnter = () => {

} catch (e) {}  // 改为
} catch {
  // Ignore parse errors during streaming, as partial data may be incomplete
}

// EnterpriseForm.vue
import { ref, reactive, watch, computed } from 'vue'
// 改为
import { ref, reactive, watch } from 'vue'

// ModelConfig.vue
import { ref, reactive, onMounted, computed } from 'vue'
// 改为
import { ref, reactive, onMounted } from 'vue'

// DocumentsTab.vue
const props = defineProps({ ... })
// 改为
const { list, loading, typeOptions, statusOptions } = defineProps({ ... })
```

**预防措施**:
1. 删除使用的变量后，立即清理对应的import语句
2. catch块使用空标识符`{}`而不是定义未使用的变量
3. 函数参数如果不需要，使用空标识符而不是具体参数名

**相关文件**:
- `frontend/src/views/system/AIPlayground.vue`
- `frontend/src/views/company/EnterpriseForm.vue`
- `frontend/src/views/system/ModelConfig.vue`
- `frontend/src/views/company/DocumentsTab.vue`

---

### E084: Vue事件处理 - checkOllamaStatus接收到[object PointerEvent]导致400错误

**发生时间**: 2026-03-26

**错误类型**: Vue事件处理

**错误描述**:
- 点击"检测状态"按钮时，请求 URL 变为 `?url=[object PointerEvent]`
- 原因是 `@click="checkOllamaStatus"` 直接传入事件对象而非调用函数

**错误信息**:
```
GET http://localhost:8081/api/v1/openclaw/llm-providers/ollama_models/?url=%5Bobject+PointerEvent%5D 400 (Bad Request)
```

**发生场景**:
- Vue 模板中使用 `@click="functionName"` 而非 `@click="functionName()"` 时，事件对象会被作为参数传入

**解决方案**:
```html
<!-- 错误写法 -->
<el-button @click="checkOllamaStatus">检测状态</el-button>

<!-- 正确写法 -->
<el-button @click="checkOllamaStatus()">检测状态</el-button>
```

**预防措施**:
1. Vue 模板中调用函数时始终加 `()`
2. 如果函数需要参数，使用 `@click="functionName(arg)"` 明确传参
3. 避免使用 `@click="functionName"` 这种隐式传入事件对象的写法

**相关文件**:
- `frontend/src/views/system/ModelConfig.vue`

---

### E085: Ollama集成 - ollama_status和ollama_models接口未返回完整数据

**发生时间**: 2026-03-26

**错误类型**: API数据不完整

**错误描述**:
- `ollama_status` 接口只返回 `connected` 和 `version`，缺少 `models` 列表
- `ollama_models` 接口返回 `models` 但缺少 `version` 信息

**发生场景**:
- 前端需要同时获取连接状态、版本和模型列表，但后端接口设计不完整

**解决方案**:
```python
# ollama_status 改进
if response.status_code == 200:
    data = response.json()
    return UnifiedResponse.success(data={
        'connected': True,
        'version': data.get('version', 'unknown'),
        'models': data.get('models', [])
    })

# ollama_models 改进
if response.status_code == 200:
    data = response.json()
    models = data.get('models', [])
    return UnifiedResponse.success(data={
        'models': models,
        'version': data.get('version', 'unknown')
    })
```

**预防措施**:
1. API 设计时考虑前端所有数据需求
2. 相关接口尽量返回一致的数据结构
3. 使用统一的响应格式 UnifiedResponse

**相关文件**:
- `backend/apps/openclaw/views.py`

---

### E086: 前端功能 - ModelConfig页面Ollama未自动检测和加载模型列表

**发生时间**: 2026-03-26

**错误类型**: 前端功能缺失

**错误描述**:
- 进入"模型选择"页面时，不会自动检测 Ollama 连接状态
- 需要手动点击"检测状态"按钮才能获取模型列表
- 用户体验不佳

**发生场景**:
- 页面加载时只获取了 Provider 和 Model 列表，但没有获取 Ollama 状态

**解决方案**:
```javascript
// onMounted 中添加自动检测
onMounted(() => {
  fetchData()
  checkOllamaStatus()  // 添加自动检测
})

// API 支持自定义 URL
getOllamaModels: (url = 'http://localhost:11434') => {
  return request.get('/v1/openclaw/llm-providers/ollama_models/', {
    params: { url }
  })
}

// 前端检测函数支持自定义 URL
const checkOllamaStatus = async (url = null) => {
  checkingOllama.value = true
  try {
    const targetUrl = url || ollamaConfig.base_url
    const res = await modelApi.getOllamaModels(targetUrl)
    ollamaModels.value = res.data.models || []
    ollamaStatus.connected = true
    ollamaStatus.version = res.data.version || ''
    ElMessage.success(`Ollama 连接成功，发现 ${ollamaModels.value.length} 个模型`)
  } catch (error) {
    ollamaStatus.connected = false
    ollamaModels.value = []
    ElMessage.warning('Ollama 服务未启动，请确保 Ollama 已启动')
  } finally {
    checkingOllama.value = false
  }
}
```

**预防措施**:
1. 页面加载时应自动获取必要数据，减少用户操作步骤
2. API 函数提供默认参数，方便调用
3. 添加加载状态和错误提示，提升用户体验

**相关文件**:
- `frontend/src/views/system/ModelConfig.vue`
- `frontend/src/api/model.js`

---

### E087: 异步视图错误 - test_connection视图未await异步chat方法

**发生时间**: 2026-03-26

**错误类型**: 异步视图错误

**错误描述**:
- 前端调用 `POST /api/v1/openclaw/llm-providers/test_connection/` 返回 400 Bad Request
- 后端日志显示 `RuntimeWarning: coroutine 'UnifiedLLMService.chat' was never awaited`
- 原因：`test_connection` 视图调用 `unified_llm_service.chat()` 时没有使用 `await`

**发生场景**:
- 在"模型选择"页面点击"测试连接"按钮时
- 前端传入 `provider_id: null, model_id: 'qwen3:8b'`

**错误信息**:
```
RuntimeWarning: coroutine 'UnifiedLLMService.chat' was never awaited
WARNING 2026-03-26 API请求失败: {'method': 'POST', 'path': '/api/v1/openclaw/llm-providers/test_connection/', 'status': 400, ...}
```

**解决方案**:
```python
# 修改前
@action(detail=False, methods=['post'])
def test_connection(self, request):
    ...
    result = unified_llm_service.chat(...)

# 修改后
@action(detail=False, methods=['post'])
async def test_connection(self, request):
    ...
    result = await unified_llm_service.chat(...)
```

**预防措施**:
1. 调用异步方法时必须使用 `await`
2. 定义视图方法时需要添加 `async def`
3. 在调用第三方服务前先确认方法是否为异步

**相关文件**:
- `backend/apps/openclaw/views.py`

---

### E088: 前端localStorage key错误 - AIPlayground.vue使用错误的token key

**发生时间**: 2026-03-26

**错误类型**: 前端认证错误

**错误描述**:
- AI Playground 页面调用 `stream_chat` API 返回 401 Unauthorized
- 后端日志显示: `身份认证信息未提供。`
- 原因: AIPlayground.vue 中 XHR 请求使用 `localStorage.getItem('access_token')` 获取 token
- 但 user store 存储 token 使用的 key 是 `'token'` 而不是 `'access_token'`

**发生场景**:
- 用户登录后在 AI Playground 页面发送聊天消息时
- XHR 请求中 Authorization header 为 `Bearer null`

**错误信息**:
```
POST http://localhost:8081/api/v1/openclaw/playground/stream_chat/ 401 (Unauthorized)
```

**解决方案**:
```javascript
// 修改前 (AIPlayground.vue:414)
xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('access_token')}`)

// 修改后
xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
```

**预防措施**:
1. 统一 token 存储的 localStorage key
2. 不要硬编码 localStorage key，应从 store 统一获取
3. 或者在 user store 中定义常量 `TOKEN_KEY`

**相关文件**:
- `frontend/src/views/system/AIPlayground.vue`
- `frontend/src/store/user.js`

---

### E089: Agent模型配置为空 - 数据库无记录导致页面无数据

**发生时间**: 2026-03-26

**错误类型**: 数据初始化问题

**错误描述**:
- Agent 模型配置页面表格无数据
- 数据库 `AgentModelConfig` 表为空，没有任何配置记录
- 前端表格显示空白

**发生场景**:
- 访问 `/system/models` 页面的 "Agent 模型配置" 标签页
- 点击后表格为空

**错误信息**:
- 数据库查询: `AgentModelConfig.objects.all()` 返回空 queryset

**解决方案**:
在 `AgentModelConfigViewSet.list()` 方法中添加默认值返回逻辑：
- 当数据库无记录时，自动返回 AgentModelConfig.AGENT_TYPE_CHOICES 中定义的所有默认配置
- 默认配置包含：collector, matcher, analyst, generator, reviewer, tracker, optimizer, orchestrator
- 每个配置默认温度 0.7，最大 token 4096

**预防措施**:
1. 数据表设计时应考虑初始化数据的 Migration
2. ViewSet 的 list 方法应处理空数据集的情况
3. 前端应设计默认配置保存功能

**相关文件**:
- `backend/apps/openclaw/views.py` - AgentModelConfigViewSet
- `backend/apps/openclaw/models.py` - AgentModelConfig

---

### E090: LLM模型列表为空 - LLMModel表无数据导致下拉框无选项

**发生时间**: 2026-03-26

**错误类型**: 数据初始化问题

**错误描述**:
- Agent 模型配置页面的"对话模型"下拉框没有选项
- 数据库 `LLMModel` 表为空（0条记录）
- 但 `LLMProvider` 表有6条记录，每条都有 `default_model`

**发生场景**:
- 访问 `/system/models` 页面的 "Agent 模型配置" 标签页
- 点击"对话模型"下拉框时显示空白

**错误信息**:
- API 返回: `GET /api/v1/openclaw/llm-models/` 返回空数组

**解决方案**:
在 `LLMModelViewSet.list()` 方法中添加默认值返回逻辑：
- 当 LLMModel 表无记录时，自动从 LLMProvider 表获取默认模型
- 遍历所有激活的 Provider，返回其 `default_model` 作为默认模型列表

**预防措施**:
1. 数据表设计时应考虑初始化数据的 Migration
2. ViewSet 的 list 方法应处理空数据集的情况
3. 提供商创建时应自动创建对应的模型记录

**相关文件**:
- `backend/apps/openclaw/views.py` - LLMModelViewSet
- `backend/apps/openclaw/models.py` - LLMModel, LLMProvider

---

### E091: LLMProvider属性错误 - 使用了不存在的max_context字段

**发生时间**: 2026-03-26

**错误类型**: 代码错误

**错误描述**:
- API 返回 500 Internal Server Error
- 错误信息: `'LLMProvider' object has no attribute 'max_context'`
- 代码中使用了 `provider.max_context` 但 LLMProvider 模型只有 `max_tokens` 字段

**发生场景**:
- 访问 `/system/models` 页面加载模型列表时

**错误信息**:
```
AttributeError: 'LLMProvider' object has no attribute 'max_context'
```

**解决方案**:
- 将 `provider.max_context` 改为 `provider.max_tokens`

**预防措施**:
1. 使用模型字段前先检查模型定义
2. 编写单元测试验证字段存在

**相关文件**:
- `backend/apps/openclaw/views.py`

---

### E092: LLMModelSerializer错误 - 直接序列化字典导致500

**发生时间**: 2026-03-26

**错误类型**: 序列化器错误

**错误描述**:
- API 返回 500 Internal Server Error
- 错误信息: `'int' object has no attribute 'pk'`
- 原因: 使用 `ModelSerializer` 直接序列化字典，serializer 期望 `provider` 是对象而不是 ID

**发生场景**:
- 访问 `/system/models` 页面加载模型列表时

**错误信息**:
```
AttributeError: 'int' object has no attribute 'pk'
```

**解决方案**:
- 直接返回字典列表而不是使用 serializer.serialize()
- 添加必要的字段如 `id`, `provider_name`

**预防措施**:
1. 当返回非 ORM 对象时，直接返回字典
2. 不要混用 serializer 和字典

**相关文件**:
- `backend/apps/openclaw/views.py`

---

### E093: 前端ElOption值错误 - model.id为null导致验证失败

**发生时间**: 2026-03-26

**错误类型**: 前端验证错误

**错误描述**:
- 控制台警告: `Invalid prop: type check failed for prop "value". Expected String | Number | Boolean | Object, got Null`
- 原因: 后端返回的模型数据中 `id` 字段为 `null`，但 `el-option` 的 `:value` 不能是 `null`

**发生场景**:
- 访问 `/system/models` 页面的 "Agent 模型配置" 标签页时

**错误信息**:
```
Invalid prop: type check failed for prop "value". Expected String | Number | Boolean | Object, got Null
```

**解决方案**:
- 使用 `model.model_id` 代替 `model.id` 作为 el-option 的 key 和 value

**预防措施**:
1. 确保 API 返回的数据中 ID 字段不为 null
2. 前端使用唯一且非空的字段作为选项值

**相关文件**:
- `frontend/src/views/system/ModelConfig.vue`

---

### E094: 前端API路径错误 - test_connection路径缺少provider_id

**发生时间**: 2026-03-27

**错误类型**: 前端API路径错误

**错误描述**:
- 前端调用 `POST /v1/openclaw/llm-providers/test_connection/` 返回 404
- 原因：后端 `test_connection` 是 detail action（`@action(detail=True)`），路径应为 `{provider_id}/test_connection/`

**发生场景**:
- 访问 `/system/models` 页面，点击"测试连接"按钮时

**错误信息**:
```
POST http://localhost:8081/api/v1/openclaw/llm-providers/test_connection/ 404 (Not Found)
```

**解决方案**:
- 修改 `frontend/src/api/model.js` 中的 `testConnection` 函数
- 将路径从 `/v1/openclaw/llm-providers/test_connection/` 改为 `/v1/openclaw/llm-providers/${providerId}/test_connection/`

**预防措施**:
1. DRF 的 `@action(detail=True)` 会在路径中添加 `/{pk}/`
2. 前端调用 detail action 时必须将 ID 放在路径中

**相关文件**:
- `frontend/src/api/model.js`
- `backend/apps/openclaw/views.py`

---

### E096: Ollama api_key检查错误 - test_connection对Ollama类型也检查api_key导致400

**发生时间**: 2026-03-27

**错误类型**: 后端逻辑错误

**错误描述**:
- 前端调用 `POST /api/v1/openclaw/llm-providers/test_connection/` 返回 400 Bad Request
- 错误信息: "API Key未配置"

**发生场景**:
- 用户在 ModelConfig 页面点击"测试"按钮测试 Ollama 模型连接时
- 后端 `test_connection` 视图对所有提供商类型都检查 `api_key`
- 但 Ollama 类型的 `api_key` 字段为 `None`（本地部署不需要）

**错误信息**:
```
model.js:75  POST http://localhost:8081/api/v1/openclaw/llm-providers/test_connection/ 400 (Bad Request)
```

**原因分析**:
1. 后端 `test_connection` 视图第100-101行:
   ```python
   if not provider.api_key:
       return UnifiedResponse.error(message='API Key未配置', status_code=status.HTTP_400_BAD_REQUEST)
   ```
2. Ollama 是本地部署模型，不需要 `api_key`，所以数据库中该字段为 `None`
3. 检查逻辑对所有提供商类型一视同仁，导致 Ollama 无法通过测试

**解决方案**:
- 修改 `backend/apps/openclaw/views.py` 第100行
- 将 `if not provider.api_key:` 改为 `if not provider.api_key and provider.provider_type not in ('ollama',):`
- 这样 Ollama 类型会跳过 api_key 检查

**预防措施**:
1. 不同提供商类型有不同的认证方式，应该分别处理
2. 本地部署的 Ollama 不需要 API Key，应该特殊处理

**相关文件**:
- `backend/apps/openclaw/views.py`

---

### E097: batch_update类型错误 - chat_model_id传模型标识符但外键期望数字ID

**发生时间**: 2026-03-27

**错误类型**: 前后端字段类型不匹配

**错误描述**:
- 前端调用 `POST /api/v1/openclaw/agent-model-configs/batch_update/` 返回 500 Internal Server Error
- 错误信息: "Field 'id' expected a number but got 'deepseek-r1:8b'"

**发生场景**:
- 用户在 ModelConfig 页面修改 Agent 模型配置后点击"保存配置"按钮
- 后端 `batch_update` 方法直接使用前端传来的 `chat_model_id` 作为外键值
- 前端发送的是模型标识符字符串（如 `deepseek-r1:8b`），但 `AgentModelConfig.chat_model` 外键期望数据库数字ID

**错误信息**:
```
ValueError: Field 'id' expected a number but got 'deepseek-r1:8b'.
```

**原因分析**:
1. 前端从 `/system/models/` 接口获取模型列表，模型的标识符是 `model_id`（字符串）
2. 前端发送 `chat_model_id: 'deepseek-r1:8b'` 到后端
3. 后端 `batch_update` 方法直接将此值传给 `update_or_create` 的 `defaults` 参数
4. Django 尝试将字符串作为外键ID处理，导致类型错误

**解决方案**:
- 修改 `backend/apps/openclaw/views.py` 的 `batch_update` 方法
- 在 `defaults` 中将 `chat_model_id` 字符串转换为 `LLMModel` 对象
- 添加代码：
  ```python
  defaults = config_data.copy()
  chat_model_id = defaults.pop('chat_model_id', None)
  if chat_model_id:
      try:
          chat_model = LLMModel.objects.get(model_id=chat_model_id)
          defaults['chat_model'] = chat_model
      except LLMModel.DoesNotExist:
          pass
  ```

**预防措施**:
1. 前后端字段类型必须一致
2. 外键字段需要将标识符转换为数据库对象后再存入
3. 批量更新操作中注意处理外键字段的类型转换

**相关文件**:
- `backend/apps/openclaw/views.py`
- `frontend/src/api/model.js`

---

### E098: SystemModelsView字段错误 - 使用context_length但模型只有context_window字段

**发生时间**: 2026-03-27

**错误类型**: 代码字段名与模型字段名不一致

**错误描述**:
- 前端访问 `/system/models` 页面时返回 400 Bad Request
- 错误信息: "'LLMModel' object has no attribute 'context_length'"

**发生场景**:
- 用户访问模型配置页面，页面加载时调用 `/api/system/models/` 接口
- 后端 `SystemModelsView` 返回的数据中使用了 `context_length` 字段
- 但 `LLMModel` 模型的字段名是 `context_window`

**错误信息**:
```
ERROR 获取模型列表失败: 'LLMModel' object has no attribute 'context_length'
```

**原因分析**:
1. 后端 `SystemModelsView.get()` 方法第1265行使用了 `model.context_length`
2. `LLMModel` 模型的定义是 `context_window = models.IntegerField(...)`
3. 字段名不一致导致 AttributeError

**解决方案**:
- 修改 `backend/apps/openclaw/views.py` 第1265行
- 将 `'context_length': model.context_length` 改为 `'context_length': model.context_window`

**预防措施**:
1. 定期检查代码中使用的字段名是否与模型定义一致
2. 使用 IDE 的代码补全功能避免拼写错误
3. 模型字段变更时及时更新相关代码

**相关文件**:
- `backend/apps/openclaw/views.py`
- `backend/apps/openclaw/models.py`

---

### E099: AgentModelConfigSerializer字段错误 - 返回chat_model数字ID但前端期望chat_model_id字符串

**发生时间**: 2026-03-27

**错误类型**: 序列化器字段与前端期望不一致

**错误描述**:
- Agent 模型配置保存后，刷新页面显示不正确
- 保存的是模型A但显示的是模型B，或者显示为空

**发生场景**:
- 用户在 ModelConfig 页面修改 Agent 模型配置后保存
- 保存成功返回 200，但重新加载页面后下拉框显示不正确

**原因分析**:
1. 后端 `AgentModelConfigSerializer` 返回的字段是 `chat_model`（数据库外键ID，数字）
2. 前端下拉框的 `:value` 是 `model.model_id`（模型标识符，字符串）
3. 保存时前端发送 `chat_model_id`（字符串），但读取时返回的是 `chat_model`（数字）
4. 数字和字符串不匹配，导致下拉框无法正确选中

**解决方案**:
- 修改 `backend/apps/openclaw/serializers.py`
- 添加 `chat_model_id` 字段，使用 `source='chat_model.model_id'` 返回模型标识符
- 添加 `reasoning_model_id` 字段同理
- 代码：
  ```python
  chat_model_id = serializers.CharField(source='chat_model.model_id', read_only=True, allow_null=True)
  reasoning_model_id = serializers.CharField(source='reasoning_model.model_id', read_only=True, allow_null=True)
  ```

**预防措施**:
1. 前后端字段命名必须保持一致
2. 外键字段的序列化要考虑前端的使用场景
3. 批量更新和查询使用不同的字段格式时要注意兼容

**相关文件**:
- `backend/apps/openclaw/serializers.py`
- `frontend/src/views/system/ModelConfig.vue`

---

### E163: CrawlScheduleUpdateSerializer缺少字段

**发生时间**: 2026-03-29

**错误类型**: 序列化器字段缺失

**错误描述**:
- 编辑采集计划后保存，新增加的"采集地区"、"参与资质匹配的企业"、"执行时间"三个字段丢失

**发生场景**:
- 用户编辑已存在的采集计划
- 修改采集地区、企业选择、执行时间后保存
- 保存成功但数据库中这些字段为空

**原因分析**:
1. `CrawlScheduleUpdateSerializer` 的 `fields` 列表中缺少 `regions`、`enterprise_ids`、`exec_datetime` 字段
2. 模型和迁移已正确添加这些字段，但序列化器没有同步更新
3. DRF 序列化器只处理 `fields` 中定义的字段

**解决方案**:
在 `backend/apps/crawler/scheduler_serializers.py` 的 `CrawlScheduleUpdateSerializer` 中添加这三个字段:

```python
class Meta:
    model = CrawlSchedule
    fields = [
        'name', 'website_template', 'crontab', 'is_active',
        'max_pages', 'crawl_mode', 'keywords', 'params',
        'regions', 'enterprise_ids', 'exec_datetime',  # 添加这3个字段
        'auto_match', 'auto_delete_unmatched', 'match_threshold'
    ]
```

**预防措施**:
1. 添加模型字段时，同时检查并更新相关的序列化器
2. 使用 DRF 的 `ModelSerializer` 时，确保 fields 列表与模型字段同步

**相关文件**:
- `backend/apps/crawler/scheduler_models.py`
- `backend/apps/crawler/scheduler_serializers.py`
- `backend/apps/crawler/migrations/0007_crawlschedule_enterprise_ids_and_more.py`

---

### E164: 前端表单缺少新字段初始化

**发生时间**: 2026-03-29

**错误类型**: 前端状态管理遗漏

**错误描述**:
- 新建采集计划对话框中没有看到省市区选择、企业选择、执行时间选择等功能
- 功能代码已添加但表单对象没有初始化这些字段

**发生场景**:
- 用户打开新建采集计划对话框
- 对话框中没有显示新添加的表单字段

**原因分析**:
1. `form` / `scheduleForm` reactive 对象没有初始化 `regions`、`enterprise_ids`、`exec_datetime` 字段
2. `showCreateDialog` / `showCreateScheduleDialog` 函数没有重置这些字段
3. `showEditDialog` / `showEditScheduleDialog` 函数没有从 API 数据中读取这些字段

**解决方案**:
在表单 reactive 对象中添加默认字段:

```javascript
const form = reactive({
  // ... 其他字段
  regions: [],
  regionsMultiple: false,
  enterprise_ids: [],
  exec_datetime: null,
  exec_mode: 'daily',
  exec_time: '08:00:00',
})
```

在对话框打开函数中初始化:

```javascript
const showCreateDialog = () => {
  // ...
  form.regions = []
  form.regionsMultiple = false
  form.enterprise_ids = []
  form.exec_mode = 'daily'
  form.exec_datetime = null
  form.exec_time = '08:00:00'
  // ...
}
```

在编辑时从 API 数据赋值:

```javascript
const showEditDialog = async (row) => {
  // ...
  form.regions = data.regions || []
  form.regionsMultiple = Array.isArray(data.regions?.[0]?.[0])
  form.enterprise_ids = data.enterprise_ids || []
  form.exec_datetime = data.exec_datetime || null
  // ...
}
```

**预防措施**:
1. 添加新表单字段时，同步更新 form reactive 对象
2. 添加新表单字段时，同步更新 showCreate 和 showEdit 函数
3. 使用 Object.assign 统一处理表单数据赋值

**相关文件**:
- `frontend/src/views/ScheduleList.vue`
- `frontend/src/views/automation/AutomationDashboard.vue`
- `frontend/src/views/schedule/CreateSchedule.vue`
- `frontend/src/views/schedule/EditSchedule.vue`

---

### E165: 企业API数据格式解析错误

**发生时间**: 2026-03-29

**错误类型**: API 数据路径错误

**错误描述**:
- 选择企业下拉框中显示为空
- 企业列表 API 实际有数据返回，但前端解析路径错误

**发生场景**:
- 用户打开新建/编辑采集计划对话框
- 点击企业选择下拉框，发现没有可选企业

**原因分析**:
1. `loadEnterprises` 函数使用 `res?.results` 获取数据
2. 但后端 DRF 分页返回的数据格式是 `{count, results, next, previous}`，即 `res.data.results`
3. 解析路径不匹配导致获取到空数组

**解决方案**:
修正数据解析路径，支持多种可能的返回格式:

```javascript
const loadEnterprises = async () => {
  enterpriseLoading.value = true
  try {
    const res = await enterpriseApi.getEnterprises({ page_size: 100 })
    enterpriseList.value = res?.data?.results ||  // DRF 分页格式
                          res?.results ||           // 封装格式 results
                          res?.data?.list ||       // 封装格式 list
                          res?.list ||             // 直接 list
                          res?.data ||             // 直接 data
                          []                       // 默认空数组
  } catch (error) {
    console.error('获取企业列表失败:', error)
    enterpriseList.value = []
  } finally {
    enterpriseLoading.value = false
  }
}
```

**预防措施**:
1. 统一使用项目中的 API 响应格式规范（见 project_rules.md）
2. 调用 API 后总是使用可选链操作符 `?.` 进行安全访问
3. 提供多层后备选项，避免数据不存在时页面崩溃

**相关文件**:
- `frontend/src/api/enterprise.js`
- `frontend/src/views/ScheduleList.vue`
- `frontend/src/views/automation/AutomationDashboard.vue`

---

### E166: el-cascader多选配置错误

**发生时间**: 2026-03-29

**错误类型**: Vue 组件属性绑定错误

**错误描述**:
- 采集地区选择器切换到"多选"模式后，仍然只能选择单个地区
- 开关切换不起作用

**发生场景**:
- 用户打开新建/编辑采集计划对话框
- 将"采集地区"的"单选/多选"开关切换到"多选"
- 尝试选择多个地区，但只能选择一个

**原因分析**:
错误的写法:
```vue
:props="form.regionsMultiple ? {
  multiple: false  // 这是问题！当为 true 时，multiple 并没有被设为 true
} : {
  multiple: false
}"
```

正确的写法应该是直接将 `multiple` 属性绑定到布尔值，而不是在条件表达式中设置。

**解决方案**:
正确配置 cascader 的 props:

```vue
<el-cascader
  v-model="form.regions"
  :options="regionOptions"
  :placeholder="form.regionsMultiple ? '选择省/市/区（可多选）' : '选择省/市/区'"
  :props="{
    value: 'value',
    label: 'label',
    children: 'children',
    multiple: form.regionsMultiple  // 直接绑定布尔值
  }"
  :clearable="true"
  :filterable="true"
  :collapse-tags="form.regionsMultiple"
/>
```

**预防措施**:
1. Vue 动态属性绑定应该直接使用 `:prop="variable"` 形式
2. 不要在条件表达式中设置应该动态变化的值
3. 查看 Element Plus 官方文档确认正确用法

**相关文件**:
- `frontend/src/views/ScheduleList.vue`
- `frontend/src/views/automation/AutomationDashboard.vue`

---

### E195: MonitoredServiceAdmin status字段错误

**发生时间**: 2026-03-29

**错误类型**: Django Admin配置错误

**错误描述**:
- Django Admin中MonitoredService模型的list_filter包含不存在的status字段
- 导致Admin界面报错或无法正常显示

**发生场景**:
- 访问 `/admin/monitor/monitoredservice/` 页面时

**原因分析**:
1. `MonitoredService` 模型中 `status` 是一个 `@property` 方法，不是数据库字段
2. Django Admin的 `list_filter` 只支持数据库字段，不能直接引用property
3. 之前添加status到list_filter导致错误

**解决方案**:
```python
# 错误写法
list_filter = ['category', 'is_enabled', 'is_critical', 'status']

# 正确写法 - 移除status
list_filter = ['category', 'is_enabled', 'is_critical']
```

**预防措施**:
1. Django Admin的list_filter/ordering等只能使用数据库字段
2. property方法不能直接用于Admin过滤
3. 如需根据property过滤，创建自定义FilterSpec

**相关文件**:
- `backend/apps/monitor/admin.py`

---

### E196: 前端请求处理函数不正确

**发生时间**: 2026-03-29

**错误类型**: 前端API响应处理错误

**错误描述**:
- SidebarNav.vue的fetchServices和ScheduleList.vue的toggleStatus直接检查`response.status`
- 但request.js拦截器已经返回了`response.data`，不是原始的axios response
- 导致即使API返回500错误，前端代码仍尝试处理数据

**发生场景**:
1. SidebarNav.vue - 获取系统服务状态列表时500错误
2. ScheduleList.vue - 暂停采集计划时500错误

**原因分析**:
1. request.js的响应拦截器返回`res`（即`response.data`），而不是完整的`response`对象
2. 前端代码检查`response.status === 200`永远不会为真，因为`response`已经是数据对象
3. 实际应该检查数据内部的成功/失败状态

**解决方案**:
```javascript
// 错误写法 - 来自SidebarNav.vue和ScheduleList.vue
const response = await getSystemServices()
if (response.status === 200 || response.status === 201) {
  const data = response.data || response
  services.value = data.services || []
}

// 正确写法 - request.js已经处理了响应，直接使用
const response = await getSystemServices()
// response已经是数据，不需要检查status
services.value = response.services || []
```

**预防措施**:
1. 使用封装的request方法时，不需要检查response.status
2. request.js已经统一处理了响应和数据提取
3. 直接使用返回的数据对象即可

**相关文件**:
- `frontend/src/components/SidebarNav.vue`
- `frontend/src/views/ScheduleList.vue`
- `frontend/src/utils/request.js`

---

### F016: 实时服务监控与自动恢复系统

**发生时间**: 2026-03-29

**功能类型**: 新增功能

**功能描述**:
设计与实现完整的实时服务监控与自动恢复系统

**实现内容**:

1. **数据模型** (`apps/monitor/models.py`)
   - `MonitoredService`: 被监控服务配置，支持HTTP/TCP/进程/Celery多种检测方式
   - `ServiceHealthRecord`: 健康检查历史记录
   - `ServiceAlert`: 告警记录（支持多级别：通知/警告/错误/严重）
   - `ServiceActionLog`: 操作日志（自动/手动操作）

2. **健康检查模块** (`apps/monitor/health_checker.py`)
   - `HealthChecker`: 通用健康检查器
   - `CeleryHealthChecker`: Celery专用检查器
     - 检测Worker数量、活跃任务、注册任务、队列信息
     - 检测Beat调度器状态、活跃定时任务
   - 支持HTTP请求、TCP端口、进程检测、Celery服务检测

3. **自动重启与告警** (`apps/monitor/restart_manager.py`)
   - `ServiceRestartManager`: 服务重启管理器
     - 冷却策略：防止频繁重启
     - 连续3次失败触发重启
     - 每日重启次数限制
   - `AlertManager`: 告警管理器
     - 钉钉Webhook通知集成
     - 告警升级机制

4. **Celery定时任务** (`apps/monitor/tasks.py`)
   - 每30秒健康检查
   - 自动恢复异常服务
   - 每日重置重启计数
   - 清理过期记录（7天健康记录，30天操作日志）

5. **API端点**
   - `GET /api/v1/monitor/dashboard/` - 仪表盘
   - `GET/POST /api/v1/monitor/services/` - 服务管理
   - `POST /api/v1/monitor/services/{id}/check_health/` - 手动检查
   - `POST /api/v1/monitor/services/{id}/restart/` - 手动重启
   - `GET /api/v1/monitor/health-records/` - 健康记录
   - `GET /api/v1/monitor/alerts/` - 告警列表
   - `GET /api/v1/monitor/action-logs/` - 操作日志

6. **前端组件**
   - `ServiceMonitor.vue`: 服务监控仪表盘
   - `ServiceHealthChart.vue`: 健康历史图表
   - `ServiceActionLogList.vue`: 操作日志列表
   - `ServiceAlertList.vue`: 告警列表

7. **初始化服务**
   - PostgreSQL数据库
   - Redis缓存
   - Celery Worker / Beat
   - Chroma向量数据库
   - MinIO对象存储
   - Ollama AI服务
   - 前端开发服务器

**影响文件**:
- `backend/apps/monitor/` (整个模块)
- `frontend/src/views/system/ServiceMonitor.vue`
- `frontend/src/views/system/components/ServiceHealthChart.vue`
- `frontend/src/views/system/components/ServiceActionLogList.vue`
- `frontend/src/views/system/components/ServiceAlertList.vue`
- `frontend/src/api/monitor.js`
- `frontend/src/router/index.js` (添加路由)
- `frontend/src/components/SidebarNav.vue` (添加导航菜单)
- `config/urls.py` (添加API路由)

---

### E100: Ollama模型不存在 - Playground测试失败-数据库配置模型qwen2.5:14b在Ollama中未安装

**发生时间**: 2026-03-27

**错误类型**: 配置与实际环境不匹配

**错误描述**:
- 在 Playground 页面测试 Ollama 本地部署的 `qwen2.5:14b` 模型时失败
- 错误信息: `model 'qwen2.5:14b' not found`

**发生场景**:
- 用户在 AI Playground 页面点击"测试所有连接"按钮
- 或用户选择 Ollama 提供商后发送消息

**原因分析**:
1. 数据库 `LLMProvider` 表中配置的默认模型是 `qwen2.5:14b`
2. `available_models` 列表也是 `['qwen2.5:14b', 'qwen2.5:72b', 'llama3.1:70b', 'deepseek-r1:14b']`
3. 但实际 Ollama 服务中已安装的模型是: `qwen3:8b`, `deepseek-r1:8b`, `gpt-oss:20b`, `gemma3:12b`, `qwen3-vl:8b`
4. `qwen2.5:14b` 模型从未下载到 Ollama 中

**解决方案**:
更新数据库中的 Ollama 提供商配置，将 `default_model` 和 `available_models` 改为 Ollama 中实际存在的模型:

```python
from apps.openclaw.models import LLMProvider

p = LLMProvider.objects.filter(code='ollama_local').first()
if p:
    p.default_model = 'qwen3:8b'
    p.available_models = ['qwen3:8b', 'deepseek-r1:8b', 'gpt-oss:20b', 'gemma3:12b', 'qwen3-vl:8b']
    p.save()
```

**预防措施**:
1. 部署前检查 Ollama 中实际安装的模型列表
2. 配置默认模型时应选择确实已安装的模型
3. 如需使用特定模型，先执行 `ollama pull <model_name>` 下载

**相关文件**:
- `backend/apps/openclaw/models.py` (LLMProvider 模型)
- `backend/apps/openclaw/migrations/0003_init_llm_providers.py` (初始化数据)

---

### E103: 数据库连接失败导致500错误

**发生时间**: 2026-03-27

**错误类型**: 配置错误

**错误描述**:
- 前端调用 `/api/v1/tenders/statistics/`、`/api/v1/tenders/`、`/api/v1/notifications/unread-count/` 等API时返回500 Internal Server Error
- Django服务器日志显示: `django.db.utils.OperationalError: could not connect to server`

**发生场景**:
- 用户访问 Dashboard 页面时
- tenders/statistics/ API 调用
- notifications/unread-count/ API 调用

**原因分析**:
1. `.env` 文件中的 `DB_PASSWORD` 被错误配置为 `CHANGE-ME-IN-PRODUCTION`
2. 而实际数据库 postgres 的密码是 `123456`
3. Django 无法连接到 PostgreSQL 数据库，导致所有需要数据库的 API 都返回 500

**解决方案**:
1. 修改 `backend/.env` 文件
2. 将 `DB_PASSWORD=CHANGE-ME-IN-PRODUCTION` 改为 `DB_PASSWORD=123456`
3. 重启 Django 开发服务器

**预防措施**:
1. `.env.example` 文件中已标注开发环境密码，实际使用时应复制正确配置
2. 部署前检查所有环境变量配置
3. 使用 `python manage.py check` 验证配置

**相关文件**:
- `backend/.env` (环境变量配置)
- `backend/config/settings/development.py` (开发环境数据库配置)

---

### E104: 后端服务器未运行导致500错误

**发生时间**: 2026-03-27

**错误类型**: 服务配置

**错误描述**:
- 前端调用 `/api/v1/auth/login/` 时返回500 Internal Server Error
- 错误信息: `Proxy error: Could not proxy request /api/v1/auth/login/ from localhost:8081 to http://localhost:8000 (ECONNREFUSED).`

**发生场景**:
- 用户在浏览器登录页面点击登录时
- 前端开发服务器(8081)将API请求代理到后端Django服务器(8000)
- 后端Django服务器未启动，导致ECONNREFUSED

**原因分析**:
1. 前端 `npm run dev` 启动在端口8081
2. 前端通过 vue.config.js 的 proxy 配置将 `/api` 请求代理到 `http://localhost:8000`
3. 后端 Django 开发服务器未启动(端口8000)
4. 代理失败返回500错误给前端

**解决方案**:
1. 启动后端 Django 开发服务器: `cd backend && python manage.py runserver 8000`
2. 确保后端服务器先于前端服务器启动
3. 或使用 `concurrently` 同时启动前后端

**预防措施**:
1. 启动前端前先确认后端是否运行
2. 使用 `python manage.py check` 验证后端配置
3. 查看日志确认服务启动状态

**相关文件**:
- `frontend/vue.config.js` (前端代理配置)
- `backend/manage.py` (Django入口)

---

### E105: AI Playground流式响应问题 - 回复一次性出来

**发生时间**: 2026-03-27

**错误类型**: 流式响应问题

**错误描述**:
- AI Playground页面开启流式输出后，回复仍然是一次性全部显示
- 用户感受不到"打字机"式的逐步显示效果
- 后端日志显示数据是逐步返回的，但前端没有逐步渲染

**发生场景**:
- 用户在AI Playground页面勾选"流式输出"后发送消息
- Ollama后端返回数据正常（验证过每个chunk间隔约0.05-0.06秒）
- 但前端收到的是聚合后的完整响应

**根本原因分析**:
1. **httpx异步客户端缓冲**: `OllamaAdapter.chat_stream()` 使用 `httpx.AsyncClient` 的 `aiter_lines()` 方法，但该方法内部有缓冲
2. **Django StreamingHttpResponse缓冲**: 使用异步生成器时，Django会缓冲数据
3. **浏览器XHR缓冲**: 前端使用XMLHttpRequest的onprogress事件，浏览器会缓冲SSE数据

**解决方案**:

1. **后端: 改用同步httpx.Client**
   ```python
   # llm_adapters.py - OllamaAdapter.chat_stream()
   def chat_stream(self, ...):  # 不再是async def
       with httpx.Client(timeout=300) as client:
           with client.stream('POST', url, json=payload) as response:
               for chunk in response.iter_bytes():
                   # 手动解析和处理
                   yield content
   ```

2. **后端: 使用同步生成器函数**
   ```python
   # views.py - stream_chat
   def generate():  # 不是 async def
       for item in adapter.chat_stream(...):
           yield f"event: message\ndata: {json.dumps({'content': item})}\n\n"
   
   return StreamingHttpResponse(generate(), content_type='text/event-stream')
   ```

3. **前端: 使用Fetch API + ReadableStream**
   ```javascript
   const response = await fetch('/api/v1/openclaw/playground/stream_chat/', {...})
   const reader = response.body.getReader()
   while (true) {
       const { done, value } = await reader.read()
       if (done) break
       // 处理接收到的chunk
   }
   ```

**预防措施**:
1. Django StreamingHttpResponse对异步生成器有缓冲，应用同步生成器
2. httpx的aiter_lines()有内部缓冲，需要用iter_bytes()手动解析
3. 浏览器XHR不适合真正的流式SSE，应使用Fetch API + ReadableStream

**相关文件**:
- `backend/services/llm_adapters.py` - OllamaAdapter.chat_stream()
- `backend/apps/openclaw/views.py` - stream_chat action
- `frontend/src/views/system/AIPlayground.vue` - streamChat函数

---

### E106: httpx AsyncClient缓冲问题导致流式失效

**发生时间**: 2026-03-27

**错误类型**: HTTP客户端缓冲

**错误描述**:
- httpx.AsyncClient的aiter_lines()方法内部有缓冲机制
- 导致本应逐步返回的数据被聚合后一次性返回
- Ollama API本身是正确流式返回的，但适配器层破坏了流式

**发生场景**:
- 使用AsyncClient调用Ollama的流式API时
- for async chunk in response.aiter_lines(): 实际上不会立即yield

**错误代码**:
```python
# 错误的写法 - 有内部缓冲
async with httpx.AsyncClient() as client:
    async with client.stream('POST', url, json=payload) as response:
        async for line in response.aiter_lines():
            # 这里不是实时逐行返回的
            yield line
```

**解决方案**:
改用同步Client + iter_bytes():
```python
# 正确的写法 - 无缓冲
with httpx.Client(timeout=300) as client:
    with client.stream('POST', url, json=payload) as response:
        for chunk in response.iter_bytes():
            # 手动按行分割
            yield chunk
```

**预防措施**:
1. httpx的aiter_lines()适合普通HTTP请求，不适合流式场景
2. 流式场景应使用iter_bytes()并手动处理行分割
3. 同步Client比AsyncClient更简单，缓冲问题更少

**相关文件**:
- `backend/services/llm_adapters.py`

---

### E107: Django StreamingHttpResponse对异步生成器缓冲

**发生时间**: 2026-03-27

**错误类型**: Django流式响应

**错误描述**:
- StreamingHttpResponse与异步生成器结合使用时，Django会缓冲数据
- 导致本应流式返回的内容被聚合后一次性发送
- 异步生成器的yield不会立即传递给HTTP响应

**发生场景**:
- Django视图中使用 async def generate() 生成器
- 返回 StreamingHttpResponse(generate(), ...)

**错误代码**:
```python
# 错误的写法
@action(detail=False, methods=['post'])
async def stream_chat(self, request):
    async def generate():
        async for item in adapter.chat_stream(...):
            yield f"data: {item}\n\n"
    
    return StreamingHttpResponse(generate(), content_type='text/event-stream')
```

**解决方案**:
使用同步生成器函数：
```python
# 正确的写法
@action(detail=False, methods=['post'])
def stream_chat(self, request):
    def generate():
        for item in adapter.chat_stream(...):  # 不再是async for
            yield f"data: {json.dumps({'content': item})}\n\n"
    
    return StreamingHttpResponse(generate(), content_type='text/event-stream')
```

**预防措施**:
1. StreamingHttpResponse应使用同步生成器
2. 避免在generate()函数中使用await
3. 后端LLM调用也应是同步的（不等待另一个异步流）

**相关文件**:
- `backend/apps/openclaw/views.py`

---

### E108: XMLHttpRequest不适合真正的流式SSE接收

**发生时间**: 2026-03-27

**错误类型**: 前端HTTP客户端限制

**错误描述**:
- XMLHttpRequest的onprogress事件不能实现真正的流式接收
- 浏览器会缓冲SSE数据，聚合到一定量后才触发onprogress
- 导致前端无法实时显示LLM返回的每个token

**发生场景**:
- AIPlayground.vue使用XHR实现流式请求
- 虽然后端正确流式返回SSE数据，但前端收到的是聚合后的数据

**错误代码**:
```javascript
// 不推荐的写法
const xhr = new XMLHttpRequest()
xhr.onprogress = (event) => {
    // 这里的event.data不是实时更新的
    // 浏览器会缓冲数据
}
```

**解决方案**:
使用Fetch API + ReadableStream：
```javascript
const response = await fetch(url, options)
const reader = response.body.getReader()
const decoder = new TextDecoder()
let buffer = ''

while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6))
            // 实时处理每个数据块
        }
    }
}
```

**预防措施**:
1. 真正的流式SSE接收应使用Fetch API + ReadableStream
2. XMLHttpRequest适合普通请求，不适合流式SSE
3. ReadableStream.getReader()可以逐块读取响应体

**相关文件**:
- `frontend/src/views/system/AIPlayground.vue` - streamChat函数

---

### E109: Ollama模型列表不一致 - 数据库配置与实际部署不符

**发生时间**: 2026-03-27

**错误类型**: 数据配置与实际环境不匹配

**错误描述**:
- 数据库LLMProvider表中Ollama配置了5个模型
- 但实际Ollama服务部署了7个模型
- 导致前端下拉框只能看到5个模型，缺少2个实际可用的模型

**发生场景**:
- 用户访问AI Playground页面
- 点击模型选择下拉框
- 看不到Ollama实际部署的全部7个模型

**原因分析**:
1. 数据库配置是早期配置的，部分模型已被删除或更新
2. 新增的模型（如qwen3-vl:4b、gemma3:4b）没有添加到数据库配置中
3. 没有机制保证数据库配置与实际Ollama部署同步

**解决方案**:
更新数据库中Ollama提供商的available_models列表：

```python
from apps.openclaw.models import LLMProvider

p = LLMProvider.objects.filter(provider_type='ollama').first()
if p:
    # 实际部署的7个模型
    all_models = [
        'qwen3-vl:4b', 
        'gemma3:4b', 
        'qwen3:8b', 
        'deepseek-r1:8b', 
        'gpt-oss:20b', 
        'gemma3:12b', 
        'qwen3-vl:8b'
    ]
    p.available_models = all_models
    p.save()
```

**当前可用模型列表**:
| 序号 | 模型名称 |
|------|----------|
| 1 | qwen3-vl:4b |
| 2 | gemma3:4b |
| 3 | qwen3:8b |
| 4 | deepseek-r1:8b |
| 5 | gpt-oss:20b |
| 6 | gemma3:12b |
| 7 | qwen3-vl:8b |

**预防措施**:
1. Ollama模型变更后及时更新数据库配置
2. 可以考虑添加自动同步机制，从Ollama API获取实际模型列表
3. 部署文档应记录所有已下载的模型名称

**相关文件**:
- `backend/apps/openclaw/models.py` (LLMProvider模型)
- `backend/apps/openclaw/views.py` (模型列表API)

---

### E110: Ollama模型自动同步功能实现

**发生时间**: 2026-03-27

**功能类型**: 新增功能

**功能描述**:
- 实现了 Ollama 模型自动同步功能
- 当用户在 AI Playground 页面加载时，自动检测并同步 Ollama 模型列表
- 解决了 E109 问题（模型列表不一致）的根本原因

**实现内容**:

1. **后端新增 API 接口**
   - 路径: `POST /api/v1/openclaw/llm-providers/sync_ollama_models/`
   - 功能:
     - 从 Ollama API (`/api/tags`) 获取实际安装的模型列表
     - 自动更新 `LLMProvider.available_models` 字段
     - 自动更新 `LLMModel` 表（添加新模型、更新现有模型）
     - 如果 `default_model` 不在列表中，自动设置为第一个模型

2. **前端自动同步逻辑**
   - 在 `AIPlayground.vue` 的 `loadProviders()` 成功后调用 `checkAndSyncModels()`
   - 对比 Ollama API 返回的模型列表与数据库 `available_models`
   - 如果不一致，自动调用同步接口
   - 同步成功后显示成功消息并更新本地模型列表

3. **前端 API 方法**
   - `modelApi.syncOllamaModels()` - 手动触发同步

**同步逻辑代码**:
```javascript
const checkAndSyncModels = async () => {
  const ollamaProvider = providers.value.find(p => p.provider_type === 'ollama')
  if (!ollamaProvider) return

  const ollamaRes = await modelApi.getOllamaModels()
  const ollamaModelNames = ollamaRes.data?.models?.map(m => m.name) || []

  const dbModels = ollamaProvider.available_models || []
  const needsSync = ollamaModelNames.length !== dbModels.length ||
    !ollamaModelNames.every(m => dbModels.includes(m))

  if (needsSync && ollamaModelNames.length > 0) {
    const syncRes = await modelApi.syncOllamaModels()
    if (syncRes.code === 0) {
      ElMessage.success(`已自动同步 ${syncRes.data.total_models} 个Ollama模型`)
    }
  }
}
```

**同步影响的页面**:
1. **AI Playground** (`/system/playground`) - 模型选择下拉框
2. **模型配置** (`/system/models`) - 已安装模型列表
3. **Agent 模型配置** - 对话模型下拉框

**相关文件**:
- `backend/apps/openclaw/views.py` - 新增 `sync_ollama_models` action
- `frontend/src/api/model.js` - 新增 `syncOllamaModels()` API方法
- `frontend/src/views/system/AIPlayground.vue` - 新增 `checkAndSyncModels()` 函数

**预防措施**:
1. Ollama 模型新增后，下次访问页面时会自动同步
2. 如果同步失败，会在控制台输出警告，不影响页面加载
3. 可以手动调用 `syncOllamaModels()` API 强制同步

---

## 操作前检查清单

每次开发前请确认：

- [x] 检查本文档是否有相关错误记录
- [x] 确认数据库迁移是否已执行
- [x] 确认服务是否正常运行
- [x] 确认API路由是否已配置
- [x] 确认Token是否有效
- [x] 确认refresh_token是否正确保存
- [x] 检查前端请求拦截器是否包含token刷新逻辑
- [x] 前后端字段命名一致性检查
- [x] 删除代码后清理未使用的import导入
- [x] 运行`npm run lint`检查代码质量

---

## 记录规范

新增错误记录时请遵循以下规范：

1. **编号**: E + 三位数字，如E001、E002
2. **去重检查**: 记录前先搜索是否已存在相同问题
3. **信息完整**: 必须包含错误描述、场景、解决方案
4. **更新索引**: 在索引表中添加新记录
5. **添加预防措施**: 避免再次发生

---

## E116: 生产环境安全检查缺失

**发生时间**: 2026-03-27

**错误类型**: 安全配置问题

**错误描述**:
- `.env`文件中包含硬编码的默认密钥如`CHANGE-ME-IN-PRODUCTION`
- 生产环境直接使用这些默认密钥导致严重安全风险
- 数据库密码`123456`等弱密码可直接被破解

**错误配置**:
```bash
DJANGO_SECRET_KEY=CHANGE-ME-IN-PRODUCTION-USE-STRONG-RANDOM-KEY
DB_PASSWORD=123456
SENSITIVE_DATA_ENCRYPTION_KEY=CHANGE-ME-IN-PRODUCTION-32-CHARS-KEY
```

**解决方案**:
在`config/settings/base.py`中添加生产环境强制检查：
```python
def _check_production_security():
    if ENVIRONMENT != 'production':
        return
    errors = []
    secret_key = os.getenv('DJANGO_SECRET_KEY', '')
    if not secret_key or len(secret_key) < 50:
        errors.append('DJANGO_SECRET_KEY must be at least 50 characters')
    if 'CHANGE-ME' in secret_key:
        errors.append('DJANGO_SECRET_KEY contains placeholder value')
    # ... 更多检查
    if errors:
        raise ValueError(f'Production security check failed: {errors}')
```

**预防措施**:
1. 生产环境密钥必须从密钥管理服务（如Vault）注入
2. 禁止在代码仓库中存储生产密钥
3. 定期轮换密钥

---

## E117: Agent消息签名验证缺失

**发生时间**: 2026-03-27

**错误类型**: 安全漏洞

**错误描述**:
- `AgentRouter.route_message()`方法未验证消息发送者身份
- 恶意Agent可注入伪造消息冒充其他Agent执行特权操作
- 消息内容无完整性校验，可能被篡改

**问题代码**:
```python
# openclaw/messaging/protocol.py
def route_message(self, message: AgentMessage) -> bool:
    for middleware in self._middlewares:
        message = middleware(message)  # 中间件可能被绕过
        if message is None:
            return False
```

**解决方案**:
1. 在`AgentMessage`中添加`signature`和`nonce`字段
2. 实现`compute_signature()`和`verify_signature()`方法使用HMAC-SHA256
3. 在`AgentRouter`中添加`_security_middleware()`验证签名和时间新鲜度
4. 添加`send_signed_message()`自动签名发送

**预防措施**:
1. Agent注册时交换共享密钥
2. 消息必须携带时间戳验证新鲜度（5分钟内有效）
3. 添加消息序列号防重放攻击

---

## E118: 沙箱代码执行使用exec()隔离不足

**发生时间**: 2026-03-27

**错误类型**: 安全漏洞

**错误描述**:
- `SandboxExecutor`通过`exec()`执行代码
- Python沙箱机制不安全，可通过`sys`、`importlib`、`ctypes`等绕过限制
- 恶意代码可访问文件系统、网络、执行任意系统调用

**问题代码**:
```python
# openclaw/sandbox/executor.py
with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
    exec(code, execution_globals)  # exec()本身可被攻击利用
```

**解决方案**:
改用`subprocess.run()`进程级隔离：
```python
async def execute_code(self, code: str, timeout: int = None) -> ExecutionResult:
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-c', wrapper_code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    # 子进程被隔离，无法访问主进程资源
```

**预防措施**:
1. 禁止在生产环境使用`exec()/eval()`
2. 代码执行使用独立进程+资源限制
3. 配置`seccomp`或`AppArmor`强制系统调用限制
4. 定期安全审计允许模块列表

---

## E119: IsEnterpriseOwner权限逻辑绕过

**发生时间**: 2026-03-27

**错误类型**: 权限绕过

**错误描述**:
- `IsEnterpriseOwner.has_permission()`直接`return True`
- 绕过了后续`has_object_permission`的对象级权限校验
- 任何认证用户都能访问其他企业的资源

**问题代码**:
```python
# utils/permissions/enterprise.py
def has_permission(self, request, view):
    if not request.user or not request.user.is_authenticated:
        return False
    if request.user.is_admin():
        return True
    return True  # ← 应该是False，无条件返回True导致权限绕过
```

**解决方案**:
```python
def has_permission(self, request, view):
    if not request.user or not request.user.is_authenticated:
        return False
    if request.user.is_admin():
        return True
    return False  # 必须返回False，由has_object_permission判断

def has_object_permission(self, request, view, obj):
    # 对象级权限校验
    if request.user.is_admin():
        return True
    if hasattr(obj, 'created_by'):
        return obj.created_by == request.user
    return False
```

**预防措施**:
1. `has_permission`返回False时`has_object_permission`不会执行
2. 添加单元测试验证权限逻辑
3. 代码审查时重点检查权限判断逻辑

---

## E120: 生产环境堆栈信息泄露

**发生时间**: 2026-03-27

**错误类型**: 信息泄露

**错误描述**:
- `RequestLoggingMiddleware`和异常处理代码在`DEBUG=True`时输出完整堆栈
- 攻击者可通过日志分析系统内部结构、文件路径、依赖版本
- 生产环境不应输出详细错误信息

**问题代码**:
```python
# core/exceptions.py
if status_code >= 500:
    logger.error(f"... Error: {str(exc)}\nTraceback: {traceback.format_exc()}")
```

**解决方案**:
```python
from django.conf import settings

if status_code >= 500:
    if settings.DEBUG:
        logger.error(f"... Error: {str(exc)}\nTraceback: {traceback.format_exc()}")
    else:
        logger.error(f"... Error: {str(exc)} [堆栈信息已隐藏，生产环境禁止输出]")
```

**预防措施**:
1. 生产环境必须设置`DEBUG=False`
2. 日志中过滤敏感路径和配置信息
3. 统一异常处理类自动脱敏

---

*最后更新: 2026-03-27*
