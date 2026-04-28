---

## E371: 上海建筑建材业采集任务完成但无数据

**错误类型**: 采集源数据迁移/网站改版

**发生场景**: 执行上海建筑建材业采集任务，任务成功完成但采集0条数据

**根因分析**（3个叠加问题）:
1. **公告类型不匹配**: `tasks.py` 默认 `notice_types=['gkzb','jzxcs','jzxtp','xjcg']`（政府采购网代码），但上海建筑建材业使用 `['zbgg','zbjg','gzgg','fbgg','htgg']`，导致所有公告类型被跳过
2. **API策略误判成功**: `ShanghaiConstructionCrawler` 继承 `PyppeteerCrawler`，API策略对SPA页面返回HTTP 200但内容为空壳HTML，被误判为成功，不会降级到headless浏览器
3. **旧平台API无数据**: 旧平台 `/JGBAppZtbInterWeb/interWeb/jygg/list` API不需要认证但返回 `total=0, rows=[]`，数据已迁移到新平台 `JGBXMJYPTInterWeb`（需要SSO认证）

**修复内容**:
1. `tasks.py`: 添加 `source_default_notice_types` 映射，`sh_construction` 默认使用 `['zbgg','zbjg','gzgg','fbgg','htgg']`
2. `shanghai_construction_crawler.py`: 重写为直接使用公开API `/jygg/list`，不再依赖Pyppeteer渲染SPA页面

**当前状态**: 代码已修复，但旧平台API返回空数据。上海建筑建材业网站数据已迁移到新平台（需要SSO认证），旧平台公开API已无数据。需要用户提供SSO认证凭据或联系网站管理员获取API访问权限。

**状态**: **部分修复** | 2026-04-23

---

## E370: 任务执行出错 — "cannot access local variable 'asyncio' where it is not associated with a value"

**错误类型**: 后端/Python变量遮蔽（UnboundLocalError）

**发生场景**: 执行上海建筑建材业采集任务时，`scheduled_crawl_with_match` 函数中 `asyncio` 被局部 `import asyncio` 遮蔽，导致在该 import 语句之前引用 `asyncio` 时触发 `UnboundLocalError`。

**根因分析**:
- `tasks.py` 第1239行在 `scheduled_crawl_with_match` 函数内部有 `import asyncio`（局部导入）
- Python 将 `asyncio` 视为整个函数的局部变量
- 但第1077-1078行在局部 import 之前就使用了 `asyncio.new_event_loop()` 和 `asyncio.set_event_loop()`
- Python 发现 `asyncio` 是局部变量但尚未赋值，抛出 `UnboundLocalError`
- Python 3.12+ 错误信息为 "cannot access local variable 'asyncio' where it is not associated with a value"

**受影响文件及修复**（9个文件，14处局部 import asyncio）:
1. **`crawler/tasks.py`** — 删除第1239行局部 `import asyncio`（已有顶层导入）
2. **`apps/enterprise/views.py`** — 删除第179、255、309行局部 `import asyncio`（已有顶层导入）
3. **`openclaw/agents/professional_agents.py`** — 删除第560行局部 `import asyncio`（已有顶层导入）
4. **`apps/openclaw/automation_tasks.py`** — 添加顶层 `import asyncio`，删除第67、269行局部导入
5. **`crawler/multi_strategy_crawler.py`** — 添加顶层 `import asyncio`，删除第617行局部导入
6. **`apps/vectorlib/views.py`** — 添加顶层 `import asyncio`，删除第865行局部导入
7. **`common/utils/http_client.py`** — 添加顶层 `import asyncio`，删除第211行局部导入
8. **`services/bid_automation_workflow.py`** — 添加顶层 `import asyncio`，删除第202、1242、1245行局部导入
9. **`openclaw/ai_extractors/enterprise_extractor.py`** — 添加顶层 `import asyncio`，删除第134行局部导入

**核心原则**:
- **禁止在函数内部使用 `import asyncio`** — 会导致 Python 将 `asyncio` 视为局部变量，遮蔽顶层导入
- 所有 `import asyncio` 必须放在文件顶部
- 局部导入只适用于可能不存在的模块（try/except import），不适用于标准库

**预防措施**: 代码审查时禁止函数内部的 `import asyncio`；使用 `ruff` 或 `pylint` 的 PLW0406 规则检测局部 import 遮蔽

**状态**: **已修复** | 2026-04-23

---

## E369: 任务执行出错 — "cannot schedule new futures after interpreter shutdown"

**错误类型**: 后端/异步事件循环与线程池

**发生场景**: Celery worker 执行采集任务或其他异步任务时，Python 解释器关闭后仍尝试创建新的 Future，导致 `RuntimeError: cannot schedule new futures after interpreter shutdown`。

**根因分析**（5个问题叠加）:
1. **`tasks.py` 中 `ThreadPoolExecutor` 在 Celery worker 中使用** — `scheduled_crawl_with_match` 函数使用 `ThreadPoolExecutor(max_workers=1)` 来运行异步爬取，当 Celery worker 关闭（任务超时、worker 重启等），解释器开始 shutdown 流程，ThreadPoolExecutor 无法创建新线程
2. **多个文件使用已弃用的 `asyncio.get_event_loop()`** — Python 3.10+ 中，没有运行事件循环时调用 `get_event_loop()` 会产生 DeprecationWarning，且在 Celery worker 中可能获取到已关闭的事件循环，导致后续 `run_in_executor()` 尝试使用已关闭的线程池
3. **`workflow_views.py` 和 `vectorlib/views.py` 中使用 `ThreadPoolExecutor` 嵌套运行 `asyncio.run()`** — 在已有事件循环运行时，通过 `ThreadPoolExecutor` 提交 `asyncio.run()` 创建新事件循环，在解释器关闭时同样触发此错误
4. **`views.py` 中 AI Playground 的 `chat()` 和 `stream_chat()` 使用 `asyncio.run()`** — `asyncio.run()` 内部创建 `ThreadPoolExecutor`，在 Django 请求处理过程中如果解释器正在关闭，会触发此错误
5. **`automation_tasks.py` 和 `enterprise/views.py` 中使用 `asyncio.run()`** — 同样的问题

**受影响文件及修复**:
1. **`crawler/tasks.py`** — 移除 `ThreadPoolExecutor`，直接使用 `loop.run_until_complete()`；所有 `loop.close()` 改为 `try/finally` 保护
2. **`apps/openclaw/workflow_views.py`** — `run_async()` 移除 `ThreadPoolExecutor`，始终使用 `asyncio.new_event_loop()` + `run_until_complete()`
3. **`services/one_click_automation.py`** — `asyncio.get_event_loop()` → `asyncio.get_running_loop()`
4. **`openclaw/base_agent.py`** — `asyncio.get_event_loop().run_until_complete()` → `asyncio.new_event_loop()` + `try/finally`
5. **`services/llm_adapters.py`** — `asyncio.get_event_loop()` → `asyncio.get_running_loop()`
6. **`openclaw/skills/collector/tender_collector.py`** — `asyncio.get_event_loop()` → `asyncio.get_running_loop()`
7. **`common/utils/http_client.py`** — `asyncio.get_event_loop()` → `asyncio.get_running_loop()`
8. **`utils/db_optimizer.py`** — `asyncio.get_event_loop()` → `asyncio.get_running_loop()`
9. **`apps/vectorlib/views.py`** — 移除 `ThreadPoolExecutor` 嵌套，使用 `asyncio.new_event_loop()` + `try/finally`
10. **`crawler/multi_strategy_crawler.py`** — `asyncio.get_event_loop()` → `asyncio.new_event_loop()` + `try/finally`
11. **`apps/openclaw/views.py`** — 新增 `_run_async()` 辅助函数，3处 `asyncio.run()` → `_run_async()`
12. **`apps/openclaw/automation_tasks.py`** — 2处 `asyncio.run()` → `asyncio.new_event_loop()` + `try/finally`
13. **`apps/enterprise/views.py`** — `asyncio.run()` → `asyncio.new_event_loop()` + `try/finally`
14. **`crawler/data_source_validator.py`** — `asyncio.run()` → `asyncio.new_event_loop()` + `try/finally`

**核心原则**:
- 在同步上下文中运行异步代码：始终使用 `asyncio.new_event_loop()` + `loop.run_until_complete()` + `try/finally: loop.close()`
- 在异步上下文中运行同步代码：使用 `asyncio.get_running_loop().run_in_executor()`
- **永远不要**在 Celery worker 中使用 `ThreadPoolExecutor` 来运行 `asyncio.run()` 或 `loop.run_until_complete()`
- **永远不要**使用 `asyncio.get_event_loop()`（Python 3.10+ 已弃用）

**修改文件**: `crawler/tasks.py`, `apps/openclaw/workflow_views.py`, `services/one_click_automation.py`, `openclaw/base_agent.py`, `services/llm_adapters.py`, `openclaw/skills/collector/tender_collector.py`, `common/utils/http_client.py`, `utils/db_optimizer.py`, `apps/vectorlib/views.py`, `crawler/multi_strategy_crawler.py`, `apps/openclaw/views.py`, `apps/openclaw/automation_tasks.py`, `apps/enterprise/views.py`, `crawler/data_source_validator.py`

**预防措施**: Celery worker 中禁止使用 `ThreadPoolExecutor` 运行异步代码；**禁止使用 `asyncio.run()`**（内部创建 ThreadPoolExecutor，在解释器关闭时会触发此错误），改用 `asyncio.new_event_loop()` + `loop.run_until_complete()` + `try/finally: loop.close()`；所有 `asyncio.get_event_loop()` 替换为 `asyncio.get_running_loop()`（异步上下文）或 `asyncio.new_event_loop()`（同步上下文）；所有 `loop.close()` 必须在 `try/finally` 中执行。

**状态**: **已修复** | 2026-04-23

---

## E368: 采集计划 max_pages 设置不生效 — 上海建筑建材业采集200+页超出设定89页

**错误类型**: 后端/爬虫调度逻辑

**发生场景**: 用户设置采集计划（上海建筑建材业）最大采集页数为89页，但实际执行时采集了200多页，max_pages设置完全被忽略。

**根因分析**（5个问题叠加）:
1. **Source映射错误** — `scheduled_crawl_with_match`中，`shanghai_construction`的`website_code`包含`shanghai`，被错误映射为`source='shanghai_gov'`，导致调用了`ShanghaiGovCrawler`（上海政府采购网）而非`ShanghaiConstructionCrawler`（上海建筑建材业）
2. **`GovernmentTenderCollectorSkill`不支持`sh_construction`** — skill的`execute`方法只有`china_gov`和`shanghai_gov`两个分支，没有`sh_construction`
3. **`max_pages`被错误转换为`page_size`** — `page_size=20 * max_pages`将页数限制变成了每页数量，而不是真正的翻页控制
4. **`WebsiteTemplate.pagination_config['max_pages']`硬编码为100** — `UniversalCrawlerEngine._has_next_page`使用模板级别的`max_pages=100`，而非计划级别的`CrawlSchedule.max_pages`，且该检查允许翻到100页而非用户设定的89页
5. **`ShanghaiConstructionCrawler.crawl()`不支持翻页** — 只有`page`和`page_size`参数，没有`max_pages`参数，每次只采集一页
6. **`bid_task_scheduler`调用不存在的`crawl_tenders`方法** — `ShanghaiConstructionCrawler`没有`crawl_tenders`方法
7. **前端`ScheduleForm.vue`缺少`max_pages`字段** — CreateSchedule/EditSchedule页面无法设置最大采集页数

**解决方案**:
1. 修复`scheduled_crawl_with_match`的source映射：优先精确匹配`website_code`，再按关键词降级匹配，添加`sh_construction`映射
2. `GovernmentTenderCollectorSkill`添加`sh_construction`分支和`_crawl_sh_construction`方法
3. `ShanghaiConstructionCrawler.crawl()`添加`max_pages`参数，内置翻页逻辑
4. `scheduled_crawl_with_match`对`sh_construction`直接调用爬虫（绕过skill_registry），传入`max_pages`
5. `UniversalCrawlerEngine._crawl_with_template`和`_crawl_with_multi_strategy`使用`effective_max_pages = min(max_pages, template_max_pages)`，取用户设置和模板配置的较小值
6. `_has_next_page`移除`pagination_config['max_pages']`检查（翻页上限由外层循环控制），添加`next_button`选择器支持
7. `bid_task_scheduler`将`crawl_tenders`改为`crawl`
8. `one_click_automation.py`添加`sh_construction`到`known_gov_sources`和`source_mapping`
9. 前端`ScheduleForm.vue`添加`max_pages`表单字段，`CreateSchedule.vue`和`EditSchedule.vue`添加`max_pages`默认值和回填

**修改文件**: `crawler/tasks.py`, `crawler/shanghai_construction_crawler.py`, `apps/crawler/services.py`, `openclaw/skills/collector/tender_collector.py`, `services/bid_task_scheduler.py`, `services/one_click_automation.py`, `frontend/src/components/schedule/ScheduleForm.vue`, `frontend/src/views/schedule/CreateSchedule.vue`, `frontend/src/views/schedule/EditSchedule.vue`, `frontend/src/views/ScheduleList.vue`

**预防措施**: 新增爬虫必须同步更新skill_registry、source_mapping和CRAWLER_REGISTRY三处注册；max_pages必须作为翻页参数传递而非转换为page_size；模板级max_pages应作为上限而非覆盖用户设置；前端所有创建/编辑表单必须包含所有可配置字段。

**状态**: **已修复** | 2026-04-23

---

## E367: 登录接口 500 — 前端 Vite 代理目标端口与 Django 服务端口不匹配

**错误类型**: 前端/代理配置

**发生场景**: 开发环境中，前端页面登录时 `POST /api/v1/auth/login/` 返回 500 Internal Server Error，浏览器控制台显示 `Failed to load resource: the server responded with a status of 500`。

**根因分析**:
1. **前端 `.env.development` 配置 `VITE_API_URL=http://localhost:8100`** — Vite 代理将 `/api` 请求转发到 8100 端口
2. **Django 开发服务器实际运行在 8000 端口** — `python manage.py runserver 0.0.0.0:8000`
3. **8100 端口无服务监听** — Vite 代理连接被拒绝（`ECONNREFUSED`），返回 500 给浏览器
4. **`vite.config.ts` 代理配置**: `target: env.VITE_API_URL || 'http://localhost:8100'`，回退值也是 8100

**解决方案**:
1. 修改 `frontend/.env.development` 中 `VITE_API_URL=http://localhost:8000`，与 Django 实际端口一致
2. 同时修改 `frontend/.env` 中的 `VITE_API_URL=http://localhost:8000`

**修改文件**: `frontend/.env.development`, `frontend/.env`

**预防措施**: 前端代理目标端口必须与后端实际运行端口一致；修改 Django 运行端口时需同步更新前端环境变量；可在 `vite.config.ts` 中添加代理错误日志便于排查。

**状态**: **已修复** | 2026-04-23

---

## E366: docker-compose.yml YAML兼容性问题 — version过时 + 合并键列表语法不兼容 + certbot-webroot目录缺失

**错误类型**: 运维/YAML配置

**发生场景**: VS Code YAML语言服务器报告docker-compose.yml存在问题（"Source contains mult..."），Docker Compose V2也发出 `version is obsolete` 警告。

**根因分析**:
1. **`version: '3.8'` 已过时** — Docker Compose V2忽略此字段并发出警告
2. **`<<: [*django-env, *celery-env]` 合并键列表语法** — YAML 1.1特性，部分YAML验证器/语言服务器不支持列表形式的合并键，导致解析错误
3. **`certbot-webroot` 目录缺失** — docker-compose.yml引用了 `./docker/nginx/certbot-webroot` 但该目录不存在
4. **`x-celery-env` 锚点成为死代码** — 替换合并键后，原锚点不再被引用
5. **Redis健康检查 `-a` 密码参数产生警告** — `redis-cli -a password ping` 会在日志中产生 "Using a password with '-a' option may not be safe" 警告，而 `REDISCLI_AUTH` 环境变量已设置，`redis-cli ping` 会自动认证

**解决方案**:
1. 移除 `version: '3.8'` 字段
2. 创建 `x-celery-django-env` 合并锚点（使用单锚点 `<<: *django-env` + 显式Celery变量），替换 `<<: [*django-env, *celery-env]`
3. 创建 `docker/nginx/certbot-webroot/` 目录
4. 移除未使用的 `x-celery-env` 锚点
5. Redis健康检查简化为 `redis-cli ping`（依赖 `REDISCLI_AUTH` 环境变量）

**修改文件**: `docker-compose.yml`, `docker/nginx/certbot-webroot/`(新增)

**预防措施**: Docker Compose V2不再需要version字段；YAML合并键应使用单锚点形式 `<<: *anchor` 而非列表形式 `<<: [*a, *b]`；目录引用前确保目录存在；Redis健康检查优先使用 `REDISCLI_AUTH` 环境变量而非 `-a` 命令行参数。

**状态**: **已修复** | 2026-04-22

---

## E365: docker-compose安全配置遗漏 — Redis健康检查缺密码 + SSL证书缺失 + Secret Key泄露风险

**错误类型**: 运维/安全配置

**发生场景**: 生产环境部署后，Redis始终显示unhealthy导致级联启动失败；HTTPS不可用（SSL证书文件不存在）；.env中Secret Key可能已泄露。

**根因分析**:
1. **Redis健康检查** — `redis-cli ping` 在启用 `--requirepass` 后返回 `NOAUTH Authentication required`，healthcheck始终失败
2. **SSL证书缺失** — `docker/nginx/server.crt` 和 `server.key` 从未生成，Gateway容器挂载失败
3. **Secret Key** — .env中的密钥已存在于工作目录中，如果Git历史中曾提交则已泄露
4. **Redis密码默认值** — 5处使用 `${REDIS_PASSWORD:-B1dAut0R3d1s2026Sec}` 明文默认值
5. **CORS含开发端口** — 生产CORS白名单包含localhost:9081等开发端口

**解决方案**:
1. Redis健康检查改为 `redis-cli -a ${REDIS_PASSWORD} ping`
2. 生成10年期自签名证书（SAN: tbjl.sstcp.top, www.tbjl.sstcp.top, 8.153.93.123）
3. 轮换Django Secret Key为新的随机密钥
4. Redis密码全部改为 `${REDIS_PASSWORD:?请在.env中设置REDIS_PASSWORD}` 强制必填
5. CORS白名单清理为仅生产域名
6. etcd/minio/milvus添加 `security_opt: no-new-privileges:true` 和 `logging`
7. postgres/redis/frontend添加 `logging: *default-logging`

**修改文件**: `docker-compose.yml`, `.env`, `docker/nginx/server.crt`, `docker/nginx/server.key`, `tools/gen_self_signed_cert.py`

**预防措施**: Redis启用密码后健康检查必须携带密码；敏感变量使用 `${VAR:?error}` 强制必填；SSL证书应在部署前生成；CORS白名单不应包含localhost。

**状态**: **已修复** | 2026-04-21

---

## E364: 登录接口500错误 — 数据库路由器阻止读写分离跨库关联

**错误类型**: 后端/数据库路由

**发生场景**: 生产环境 `POST /api/v1/auth/login/` 返回 500 Internal Server Error，所有用户无法登录。

**根因分析**:
1. **`ReadWriteRouter.allow_relation()` 过于严格** — 当 `db1='replica'` 且 `db2='default'` 时直接返回 `False`，不允许跨库关联
2. **`authenticate()` 从 `replica` 读取 User** — User 不在 `WRITE_PREFERRED_MODELS` 中，读操作路由到 `replica`，导致 `user._state.db = 'replica'`
3. **`UserLoginLog.objects.create(user=user)` 写入 `default`** — 写操作始终路由到 `default`，Django 检查 FK 关联时发现两个对象在不同数据库
4. **`default` 和 `replica` 是同一数据库的读写分离** — 它们指向同一个 PostgreSQL 实例，理应允许关联

**错误堆栈**:
```
ValueError: Cannot assign "<User: admin>": the current database router prevents this relation.
  File "apps/users/views.py", line 258, in post
    UserLoginLog.objects.create(user=user, ...)
```

**解决方案**:
修改 `core/db_router.py` 的 `allow_relation()` 方法，允许 `default` 和 `replica` 之间的关联：
```python
REPLICAS = {'default', 'replica'}

def allow_relation(self, obj1, obj2, **hints):
    db1 = getattr(obj1, '_state', None) and obj1._state.db
    db2 = getattr(obj2, '_state', None) and obj2._state.db
    if db1 and db2:
        if db1 == db2:
            return True
        if db1 in self.REPLICAS and db2 in self.REPLICAS:
            return True
        return False
    return True
```

**预防措施**: 读写分离路由器的 `allow_relation` 必须考虑主库和从库是同一数据库的情况，不能简单按数据库名称判断；所有涉及 FK 关联的写操作都应测试读写分离场景。

**状态**: **已修复** | 2026-04-22

---

## E363: 系统服务监控显示PostgreSQL为error — PostgresGuardian仅支持Windows

**错误类型**: 后端/监控

**发生场景**: 生产环境Docker部署后，前端左侧导航栏显示红色（unhealthy），点击PostgreSQL服务显示"该服务未在监控数据库中注册，无法远程重启"。系统服务API返回 `PostgreSQL Service: error, 仅支持Windows`。

**根因分析**（4个问题叠加）:
1. **`PostgresGuardian.check_postgres_status()`仅支持Windows** — 非Windows直接返回 `is_running: None, message: '仅支持Windows'`，导致 `system_services_status` 将PostgreSQL显示为 `error`
2. **`'PostgreSQL Service'`不在`display_name_to_db_name`映射中** — 导致 `service_name_to_id.get(db_name)` 返回 `None`，前端无法重启该服务
3. **`system_services_status`将PostgreSQL拆为两个条目** — `PostgreSQL Service`（Windows服务检查）和 `PostgreSQL Database`（连接检查），Docker中前者必然失败
4. **Chroma VectorDB连接失败时显示为`error`** — 导致整体状态变为 `unhealthy`（红色），但Chroma是可选服务
5. **`monitored_services`表中Django Server健康检查URL端口错误** — `localhost:8100` 应为 `localhost:8000`
6. **`_start_process`使用Windows专有`subprocess.STARTUPINFO`** — Linux上会报错

**解决方案**:
1. `PostgresGuardian.check_postgres_status()`: Windows走`sc query`，Linux/Docker走`connection.cursor().execute('SELECT 1')`
2. `display_name_to_db_name`: 添加 `'PostgreSQL Service': 'postgresql_database'` 映射
3. `system_services_status`: 合并两个PostgreSQL检查为一个，统一使用 `PostgreSQL Database` 名称
4. Chroma连接失败时状态从 `error` 改为 `stopped`（可选服务）
5. 修复 `monitored_services` 表中 Django Server 健康检查URL为 `http://localhost:8000/health/`
6. `_start_process`: 仅在Windows上使用 `subprocess.STARTUPINFO`

**文件**: `backend/apps/monitor/restart_manager.py`, `backend/config/urls.py`

**预防措施**: 服务监控代码必须同时支持Windows开发环境和Docker生产环境；可选服务失败不应导致整体状态为unhealthy；服务名映射必须覆盖所有可能的显示名称。

**状态**: **已修复** | 2026-04-22

---

## E362: 登录接口 500 — 数据库读写分离路由器阻止跨库关联（UserLoginLog + User）

**错误类型**: 后端/数据库路由

**发生场景**: 生产环境部署后，用户登录时 `POST /api/v1/auth/login/` 返回 500 Internal Server Error。错误信息：`ValueError: Cannot assign "<User: admin>": the current database router prevents this relation.`

**根因分析**:
1. `production.py` 无条件配置了 `DATABASE_ROUTERS = ['core.db_router.ReadWriteRouter']` 和 `replica` 数据库
2. `replica` 数据库的 HOST 回退到 `DB_HOST`（与 `default` 相同的 PostgreSQL 实例），即没有真正的读副本库
3. `authenticate()` 从 `replica` 读取 User（`user._state.db = 'replica'`），`UserLoginLog.objects.create()` 写入 `default` 库
4. Django 检查跨库关联时 `allow_relation()` 返回 `False`，抛出 ValueError

**解决方案**:
1. `production.py` 中 `replica` 数据库和 `DATABASE_ROUTERS` 仅在配置了 `DB_REPLICA_HOST` 环境变量时才启用
2. 当前生产环境未设置 `DB_REPLICA_HOST`，所有操作走 `default` 库，不再有跨库关联问题
3. `sslmode` 默认值从 `'require'` 改为 `'prefer'`（Docker PostgreSQL 不使用 SSL）

**文件**: `backend/config/settings/production.py`

**预防措施**: 读写分离路由器仅在配置了真正的读副本库时启用；没有读副本时不应配置 `DATABASE_ROUTERS`，否则会导致跨库关联错误。

**状态**: **已修复** | 2026-04-22

---

## E361: Token刷新429 + 401反馈循环 — modelConnection重试不检查登录状态

**错误类型**: 前端/认证

**发生场景**: 访问AIPlayground等页面时，控制台报 `POST /api/v1/auth/token/refresh/ 429 (Too Many Requests)` 和 `获取Agent配置失败: AxiosError: Request failed with status code 401`。

**根因分析**（3个问题叠加）:
1. **`modelConnection.js`重试循环不检查登录状态** — `scheduleRetry()`定时器在`request.js`触发`logout()`后仍继续运行，每5s/10s/20s...触发`autoConnect()` → `fetchAgentConfigs()` → 401 → `refreshAccessToken()` → 失败 → 再重试，形成死循环
2. **`request.js`对429无特殊处理** — 刷新端点返回429时被当作普通刷新失败，触发`onRefreshFailed()` → 所有排队请求失败 → `logout()`，但重试循环仍在继续，持续产生新的刷新请求
3. **`CookieTokenRefreshView`无专用限流** — 使用`AllowAny`权限，受`AnonRateThrottle`限制（100/小时），快速重试很快耗尽配额

**解决方案**:
1. `modelConnection.js`: 导入`useUserStore`，在`autoConnect()`、`scheduleRetry()`、`checkConnectionHealth()`中检查`isLoggedIn`，未登录时停止重试和健康检查；新增`lastAuthFailureTime`+`AUTH_FAILURE_COOLDOWN`(30s)冷却期，401/429后暂停重试
2. `request.js`: 新增`lastRefreshAttempt`+`MIN_REFRESH_INTERVAL`(5s)冷却，防止5秒内重复刷新；429时将冷却期延长至30秒
3. `core/throttling.py`: 新增`TokenRefreshRateThrottle`(30/分钟)专用限流类
4. `apps/users/views.py`: `CookieTokenRefreshView`添加`throttle_classes = [TokenRefreshRateThrottle]`，替代默认的`AnonRateThrottle`

**预防措施**: 任何有重试循环的前端模块必须检查用户登录状态；Token刷新必须有冷却期防止快速重试；后端认证端点应有专用限流而非依赖全局默认限流。

**状态**: **已修复** | 2026-04-21

---

## E360: 中国政府采购网数据采集返回空结果 — 选择器失效+编码问题+缺少分页

**错误类型**: 爬虫/数据采集

**发生场景**: 执行中国政府采购网数据采集任务时，未能获取到任何数据。

**根因分析**（4个问题）:
1. **`ccgp_gov.py`列表页选择器失效** — `ul.list_con` 已不存在，实际为 `ul.c_list_bid`
2. **`ccgp_gov.py`详情页选择器失效** — `h2.detail_title` 不存在，实际为 `h2.tc`；`span.time` 不存在，实际为 `div.vF_detail_header p.tc`
3. **`china_gov_crawler.py`编码硬编码** — `response.encoding = 'utf-8'` 硬编码，当服务器返回其他编码时导致乱码
4. **`china_gov_crawler.py`缺少分页逻辑** — 只采集第1页，未实现 `index_{page}.htm` 分页
5. **`_validate_url()` HEAD请求过于严格** — 与上海爬虫同样的问题，非200状态码即判定无效

**解决方案**:
1. `ccgp_gov.py`: 列表页优先使用 `ul.c_list_bid`，降级到 `ul.list_con`
2. `ccgp_gov.py`: 详情页优先使用 `h2.tc`，降级到 `h2.detail_title`；发布时间优先使用 `div.vF_detail_header p.tc`
3. `china_gov_crawler.py`: 使用 `response.apparent_encoding` 自动检测编码
4. `china_gov_crawler.py`: 增加分页循环，URL模式为 `index_{page}.htm`
5. `_validate_url()`: 改为宽松策略，仅404判定无效

**预防措施**: 爬虫选择器必须定期验证目标网站页面结构变化；编码应使用自动检测而非硬编码；分页是基本功能不应遗漏。

**状态**: **已修复** | 2026-04-21

---

## E359: 上海政府采购网数据采集返回空结果 — 多重原因

**错误类型**: 爬虫/数据采集

**发生场景**: 执行上海政府采购网数据采集任务时，未能获取到任何数据。

**根因分析**（6个问题，按严重程度排列）:
1. **V2爬虫`_crawl_by_api()`硬编码失败** — 降级策略链第一环直接失败，浪费重试机会
2. **`/portal/category`列表API需要JS会话上下文** — 直接HTTP POST返回`data:null`，必须通过浏览器渲染获取数据
3. **V1爬虫使用静态HTTP请求** — 网站是Vue SPA，静态HTML只有壳无数据
4. **`_validate_url_async()` HEAD请求过滤有效URL** — 政府网站不支持HEAD方法返回405/403，导致所有URL被错误过滤
5. **`execute_crawler_task()`未正确处理async方法** — `crawler.crawl()`是async但被同步调用，返回coroutine对象
6. **`childrenCode`参数不精确** — 所有类型都用`ZcyAnnouncement`，实际分类code为`ZcyAnnouncement2`/`ZcyAnnouncement3`等
7. **数据库模板选择器过时** — `list_container: '.list-box'`应为`ul.list`，`requires_javascript: False`应为`True`

**解决方案**:
1. 修复`NOTICE_TYPE_MAP`中每个类型的`parentId`和`childrenCode`为精确值
2. `_crawl_by_headless()`改为`waitUntil:'networkidle2'`并增加`ul.list`到wait_selector
3. 新增`_fetch_detail_via_api()`利用不需要会话的`/portal/detail` API补充详情数据
4. `_validate_url_async()`改为宽松策略：仅404判定无效，其他情况默认通过
5. `execute_crawler_task()`增加`inspect.iscoroutine()`检测+`asyncio.run_until_complete()`处理
6. 创建迁移`0012_update_shanghai_template_selectors.py`更新数据库模板配置

**预防措施**: 爬虫开发必须先验证目标网站的技术栈（SPA/SSR）；API接口需确认是否需要会话上下文；URL验证应采用宽松策略避免误杀。

**状态**: **已修复** | 2026-04-21

---

## E358: Celery Worker 启动失败 — django_redis 缺失 + WorkflowRateThrottle 未定义 + trace_id 日志格式

**错误类型**: 后端/Celery 启动

**发生场景**: 执行 `celery -A config worker --loglevel=info --pool=solo` 时启动失败，三个错误依次暴露。

**根因分析**:
1. `django-redis` 包未安装，Django CACHES 配置引用了 `django_redis.cache.RedisCache`
2. `production.py` 引用 `core.throttling.WorkflowRateThrottle` 但该类未定义
3. `verbose` 日志格式器使用 `{trace_id}` 占位符，Celery 启动阶段 TraceIdFilter 未正确应用

**解决方案**:
1. `pip install django-redis==6.0.0`
2. 在 `core/throttling.py` 新增 `WorkflowRateThrottle` 类
3. 新增 `SafeVerboseFormatter` 类，缺失 `trace_id` 时自动填充 `'-'`

**预防措施**: 新增 DRF 配置引用的类时必须同步创建；日志格式器应处理动态字段缺失的情况。

**状态**: **已修复** | 2026-04-21

---

## E357: TenderList "获取公告内容失败: 网络错误" — 后端服务器未运行

**错误类型**: 前端/网络连接

**发生场景**: 招标列表页点击"链接"按钮查看原始公告时，控制台报错 `获取公告内容失败: AxiosError: 网络错误，请检查网络连接`（TenderList.vue:936）。

**根因分析**: 后端 Django 服务器未运行，Axios 请求无法到达后端，`error.response` 为 `undefined`，触发 request.js 第 261 行的 "网络错误，请检查网络连接" 提示。

**解决方案**: 启动后端服务器 `python manage.py runserver 0.0.0.0:8000`。附带修复 `port-check.js` ESM 兼容问题（重命名为 `.cjs`）。

**预防措施**: 使用前确保后端服务器已启动；可考虑前端增加服务器状态检测提示。

**状态**: **已修复** | 2026-04-21

---

## E356: 正则批量删除导致 Vue/JS 文件语法破坏

**错误类型**: 前端/构建失败

**发生场景**: 阶段三使用 Python `re.sub()` 批量删除 `getStatusType`/`formatTime` 等重复函数定义时，正则表达式只匹配了函数体部分，留下了孤立的 `)` `}` 和不完整的函数定义（如 `const types = {...}` 缺少 `return` 和闭合 `}`），导致 Vite build 失败。

**根因分析**:
1. `re.sub(r'const getStatusType = \([^)]*\) => \{[^}]*\}', '', content)` 只匹配最内层 `{}`，多行函数体中嵌套的对象字面量 `{...}` 导致匹配不完整
2. 删除函数体后，残留的 `return types[status] || 'info'` + `}` 成为孤立代码
3. API 文件中删除方法后，残留的 URL 片段如 `},/templates/${id}/`)` 导致语法错误
4. 括号检查脚本 `check_braces.py` 能有效发现此类问题

**解决方案**:
1. 手动修复所有 Vue 文件中的孤立括号和不完整函数
2. 重写被严重破坏的 API 文件（automationConfig.js, crawler.js, enterprise.js, vectorlib.js, document.js）
3. 修复 vite.config.ts 中 `@element-plus/icons-vue` 同时分配到 vendor 和 element-plus chunk 的冲突
4. 创建括号检查工具 `tools/check_braces.py` 和 `tools/check_js_braces.py` 用于自动化检测

**受影响文件**: AutomationDashboard.vue, CompanyInfo.vue(2处), VectorLibrary.vue, OneClickLaunch.vue, ServiceMonitor.vue, ServiceActionLogList.vue, AIPlayground.vue, automationConfig.js, crawler.js, enterprise.js, vectorlib.js, document.js, vite.config.ts

**预防措施**: 
1. 禁止使用正则表达式批量删除多行代码块
2. 删除函数时应完整删除从声明到闭合括号的所有行
3. 删除后必须运行括号检查工具和 Vite build 验证
4. API 文件删除方法后应检查逗号和花括号平衡

**状态**: **已修复** | 2026-04-21

---

## E355: 查看原始公告没有数据

**错误类型**: 前端/数据展示

**发生场景**: 在招标列表页或详情页点击"链接/查看原始公告"时，弹窗打开但无公告内容显示。之前使用iframe方式只能看到政府网站导航栏，看不到公告正文。

**根因分析**:
1. 上海政府采购网(zfcg.sh.gov.cn)是Vue SPA，公告内容通过JavaScript动态加载
2. 公告正文在嵌套iframe中（class=`content-container-mapFrame`），外层iframe无法显示
3. 爬虫只采集了列表页元数据，TenderProject.description全部为空（107条记录0条有description）

**解决方案**: 新增后端API `/api/v1/tenders/{id}/source-content/`，使用Selenium渲染页面并穿透iframe提取内容，缓存到description字段。前端改为调用API获取内容用v-html渲染。

**文件**: `backend/apps/tenders/views.py`, `frontend/src/views/tender/TenderList.vue`, `frontend/src/views/tender/TenderDetail.vue`

**预防措施**: 爬虫应同时采集详情页内容；iframe方案不适用于SPA嵌套iframe的政府网站。

**状态**: **已修复** | 2026-04-20

---

## E355: 查看原始公告没有数据

**错误类型**: 前端/数据展示

**发生场景**: 在招标列表页点击"链接"按钮查看原始公告时，弹窗打开但只显示政府网站导航栏，公告正文内容为空。

**根因分析**:
1. 上海政府采购网(zfcg.sh.gov.cn)是Vue SPA，公告正文在嵌套iframe中（class=`content-container-mapFrame`），外层iframe无法穿透显示
2. 爬虫只采集了列表页基本元数据，TenderProject.description全部为空
3. 原有iframe方式无法显示嵌套iframe中的内容

**解决方案**:
1. 后端新增`TenderSourceContentView` API端点，使用Selenium渲染页面并穿透iframe提取公告正文
2. 获取成功后自动缓存到TenderProject.description字段
3. 前端将iframe弹窗改为调用后端API获取内容，用v-html直接渲染

**文件**: `backend/apps/tenders/views.py`, `frontend/src/views/tender/TenderList.vue`, `frontend/src/views/tender/TenderDetail.vue`

**预防措施**: 爬虫应同时采集详情页内容；iframe方案不适用于嵌套iframe的SPA网站

**状态**: **已修复** | 2026-04-20

---

## E353: PATCH /api/v1/auth/me/ 断裂 — 用户资料更新返回 405

**错误类型**: 后端/API断裂

**发生场景**: 前端 [Profile.vue:122](file:///D:/共享文件/AUTO/frontend/src/views/Profile.vue#L122) 调用 `authApi.updateProfile()` 发送 `PATCH /api/v1/auth/me/`，后端 `CurrentUserView` 仅实现了 `get` 方法，无 `patch` 方法，返回 405 Method Not Allowed。

**根因分析**: `CurrentUserView` 是只读视图，未实现更新方法。`UserProfileView`（[users/views.py:404](file:///D:/共享文件/AUTO/backend/apps/users/views.py#L404)）已定义但未注册到 urls.py。

**解决方案**: 在 `CurrentUserView` 中添加 `patch` 方法，或将路由指向 `UserProfileView`。

**文件**: `backend/apps/users/views.py`

**预防措施**: 每个 API 端点的前端调用和后端实现必须双向验证；CRUD 视图应完整实现所有需要的 HTTP 方法。

**状态**: **已修复** | 2026-04-21 — 在 `CurrentUserView` 中添加了 `patch` 方法，使用 `UserUpdateSerializer` 验证并更新用户信息

---

## E354: PATCH /api/v1/bids/results/{id}/ 断裂 — 中标结果编辑返回 404

**错误类型**: 后端/API断裂

**发生场景**: 前端 [TenderList.vue:910](file:///D:/共享文件/AUTO/frontend/src/views/tender/TenderList.vue#L910) 调用 `bidApi.updateResult()` 发送 `PATCH /api/v1/bids/results/{id}/`，后端 `BidResultDetailView` 已定义（[bids/views.py:132](file:///D:/共享文件/AUTO/backend/apps/bids/views.py#L132)）但未注册到 urls.py，返回 404 Not Found。

**根因分析**: 视图类已编写但忘记在 urls.py 中注册路由。

**解决方案**: 在 `bids/urls.py` 中添加路由注册。

**文件**: `backend/apps/bids/urls.py`

**预防措施**: 新增视图后必须同步注册路由；可使用 DRF Router 自动注册减少遗漏。

**状态**: **已修复** | 2026-04-21 — 在 `bids/urls.py` 中注册了 `BidResultDetailView` 路由 `results/<int:pk>/`

---

## E355: EnterpriseBidConfig.get_qualification_summary() 引用不存在的字段 q.scope

**错误类型**: 后端/模型字段引用错误

**发生场景**: [bid_config.py:78](file:///D:/共享文件/AUTO/backend/apps/enterprise/models/bid_config.py#L78) 中 `EnterpriseBidConfig.get_qualification_summary()` 访问 `q.scope`，但 `EnterpriseQualification` 模型没有 `scope` 字段，调用时抛出 `AttributeError`。

**根因分析**: 字段名可能已重命名或删除，但方法中的引用未同步更新。

**解决方案**: 检查 EnterpriseQualification 模型的实际字段，修正 `q.scope` 为正确的字段名。

**文件**: `backend/apps/enterprise/models/bid_config.py`

**预防措施**: 模型字段变更时必须全局搜索所有引用点；IDE 重构功能可自动更新引用。

**状态**: **已修复** | 2026-04-21 — 将 `q.scope` 替换为 `q.qualification_category`（资质类别），同时修复了 `EnterpriseViewSet._build_enterprise_text()` 中 `qual.scope` → `qual.qualification_category` 和 `enterprise.industry` → `enterprise.enterprise_type`

---

## E350: 前端硬编码管理员密码 — 安全漏洞

**错误类型**: 安全/凭据泄露

**发生场景**: `frontend/src/router/index.js` 第5行硬编码 `AUTO_LOGIN_CREDENTIALS = { username: 'admin', password: 'admin123' }`，路由守卫自动以管理员身份登录。

**根因分析**: 开发期间为方便调试添加的自动登录机制，未在上线前移除。

**解决方案**: 移除硬编码凭据和自动登录函数，路由守卫改为重定向到登录页。

**文件**: `frontend/src/router/index.js`

**预防措施**: 禁止在前端代码中硬编码任何凭据；使用环境变量或后端 API 获取配置；代码审查时重点检查敏感信息。

**状态**: **已修复** | 2026-04-21

---

## E351: UnifiedApiResponse 导入失败 — 中间件重构后残留引用

**错误类型**: 后端/导入错误

**发生场景**: 重构 `unified_response.py` 删除 `UnifiedApiResponse` 死代码后，`common/middleware/__init__.py` 仍尝试导入该类，导致 Django 启动失败：`ImportError: cannot import name 'UnifiedApiResponse' from 'common.middleware.unified_response'`

**根因分析**: 删除类定义时未同步更新 `__init__.py` 的导入语句。

**解决方案**: 更新 `common/middleware/__init__.py`，移除 `UnifiedApiResponse` 的导入和导出。

**文件**: `backend/common/middleware/__init__.py`

**预防措施**: 删除或重命名模块中的导出项时，必须同步更新 `__init__.py` 和所有引用点。

**状态**: **已修复** | 2026-04-21

---

## E352: constantsApi 命名导出缺失 — Vite 构建错误

**错误类型**: 前端/模块导出

**发生场景**: Vue CLI 迁移至 Vite 后，Vite 的 esbuild 依赖扫描报错：`No matching export in "src/api/constants.js" for import "constantsApi"`。Vue CLI (Webpack) 对此容错，但 Vite (esbuild) 严格检查。

**根因分析**: `constants.js` 使用 `export default` 但 `api/index.js` 使用 `import { constantsApi }` 命名导入，两者不匹配。

**解决方案**: 在 `constants.js` 中添加 `export { constantsApi }` 命名导出，同时保留 `export default`。

**文件**: `frontend/src/api/constants.js`

**预防措施**: 统一使用命名导出或默认导出，避免混用；Vite 对 ESM 规范要求更严格，迁移时需检查所有导出/导入一致性。

**状态**: **已修复** | 2026-04-21

---

## E349: Dashboard页面没有数据 — CrawlResult未同步到TenderProject

**错误类型**: 后端/数据同步

**发生场景**: 访问 `/dashboard` 页面，所有统计数据为0，招标列表为空，趋势图表无数据。

**根因分析**:
1. Dashboard 的数据来源是 `TenderProject` 表，而非 `CrawlResult` 表
2. 爬虫采集的数据存储在 `CrawlResult` 表（107条），但未同步到 `TenderProject` 表（0条）
3. CrawlResult 中有 51 条 `processed` 状态和 56 条 `synced` 状态的记录
4. `CrawlToTenderSyncService.sync_all()` 仅同步 `status__in=['matched', 'processed']` 的记录，已 `synced` 的不会重新同步
5. 可能原因：数据库曾被重置/迁移，TenderProject 记录丢失，但 CrawlResult 记录保留

**解决方案**:
1. 使用 `CrawlToTenderSyncService.sync_all()` 同步 `processed` 状态记录
2. 将 `synced` 状态记录重置为 `processed` 后再次同步
3. 前端"即将截止"部分改用 `deadline_date` 替代 `publish_date`

**文件**: `frontend/src/views/Dashboard.vue`

**预防措施**: 采集任务完成后应确保数据同步到 TenderProject；可定期调用 `CrawlToTenderSyncService.sync_all()` 或通过 API `POST /api/v1/tenders/crawl-sync/` 触发同步

**状态**: **已修复** | 2026-04-20

---

## E348: openpyxl 未安装在 venv 虚拟环境 — Excel导出功能报错

**错误类型**: 后端/依赖安装

**发生场景**: 调用 `/api/v1/tenders/crawl-export/` 导出Excel时返回400错误："请先安装openpyxl: pip install openpyxl (No module named 'openpyxl')"

**根因分析**:
1. Django服务器运行在 `D:\共享文件\AUTO\venv\` 虚拟环境中
2. openpyxl 仅安装在系统Python（`C:\Users\ZhangGan\AppData\Local\Programs\Python\Python312\`）
3. venv 虚拟环境没有 openpyxl 包

**解决方案**:
在venv环境中安装openpyxl：`D:\共享文件\AUTO\venv\Scripts\python.exe -m pip install openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple`

**文件**: `backend/apps/tenders/views.py`（CrawlDataExportView）

**预防措施**: 安装Python包时需确认目标Python环境；Django服务器使用venv时，所有依赖需安装在venv中；可用 `Get-Process python | Select-Object Path` 确认运行中的Python路径

**状态**: **已修复** | 2026-04-20

---

## E347: 通知列表 Vue 3.5 Ref 未解包 — useListPage 返回普通对象导致模板中嵌套 Ref 不自动解包

**错误类型**: 前端/Vue 响应式系统

**发生场景**: 点击通知列表中的未读通知，浏览器控制台输出 `通知ID缺失，无法标记已读 false` 和 `通知ID缺失，无法标记已读 {"version":1,"sc":0,"__v_skip":true}`。TenderList 和 BidList 的表格静默不渲染。

**根因分析**:
1. `useListPage()` 返回普通对象（含 ref/computed 属性），Vue 3.5 模板中仅顶层 ref 自动解包，嵌套 ref（如 `listPage.list`）不解包
2. `v-for` 遍历 Ref 对象的可枚举属性值（`__v_isRef: true`, `__v_isShallow: false`, `_value: [...]`），而非数组
3. `false` 是 RefImpl 的 `__v_isShallow` 属性值；`{"version":1,"sc":0,"__v_skip":true}` 是 Vue 3.5 ComputedRef 的可枚举属性

**解决方案**:
1. `useListPage.js`: 返回值从 `return {...}` 改为 `return reactive({...})`，reactive 对象自动解包嵌套 ref
2. `NotificationList.vue`: `viewNotification()` 和 `markAllRead()` 添加 `item.__v_isRef` 防御检查

**文件**: `frontend/src/composables/useListPage.js`, `frontend/src/views/notification/NotificationList.vue`

**预防措施**: Vue 3.5 Composable 返回值必须用 `reactive()` 包装；模板中访问嵌套 ref 需注意自动解包规则；`v-for` 数据源应确保是数组而非 Ref 对象

**状态**: **已修复** | 2026-04-20

---

## E346: 通知ID缺失无法标记已读 — API参数传递不一致 + 列表数据未过滤

**错误类型**: 前端/参数传递 + 前端/数据验证

**发生场景**: 点击通知列表中的未读通知，浏览器控制台输出 `通知ID缺失，无法标记已读 false`，无法标记已读。

**根因分析**:
1. `notificationApi.getList(params)` 使用 `{ params }` 包装参数，与 `createApi` 生成的 `getList` 直接传递 `params` 风格不一致
2. `is_read: false` 传递 JavaScript 布尔值，Django BooleanField 过滤器可能无法正确识别字符串 `"false"`
3. `viewNotification()` 缺少对 `item` 是否为有效对象的前置检查
4. `v-for` 的 `:key="item.id"` 无 fallback，id 缺失时 Vue 渲染异常
5. `useListPage.fetchData()` 未过滤无效列表项（false/null/undefined）

**解决方案**:
1. `notification.js`: `getList(params)` 从 `request.get(url, { params })` 改为 `request.get(url, params)`
2. `NotificationList.vue`: `is_read: false` 改为 `is_read: 'false'`
3. `NotificationList.vue`: `viewNotification()` 添加 `if (!item || typeof item !== 'object')` 前置检查
4. `NotificationList.vue`: `:key` 从 `item.id` 改为 `item?.id || index`
5. `NotificationList.vue`: 模板中 `item.xxx` 改为 `item?.xxx`
6. `useListPage.js`: `fetchData()` 添加 `items.filter(item => item && typeof item === 'object')`

**文件**: `frontend/src/api/notification.js`, `frontend/src/views/notification/NotificationList.vue`, `frontend/src/composables/useListPage.js`

**预防措施**: API调用风格全项目统一；Django BooleanField 过滤器传字符串；v-for key 应有 fallback；列表数据过滤无效项

**状态**: **已修复** | 2026-04-20

---

## E345: 通知标记已读 404 — NotificationListView 无分页 + item.id 为 undefined

**错误类型**: 后端/分页缺失 + 前端/防御性检查

**发生场景**: 点击通知列表中的未读通知，调用 `POST /api/v1/notifications/undefined/mark-read/` 返回 404。URL 中通知 ID 为 `undefined`。

**根因分析**:
1. `NotificationListView` 覆盖了 `list()` 方法，返回 `APIResponse.success(data={'list': serializer.data})`，完全绕过 DRF 分页机制
2. 响应中无 `pagination` 信息，`parseListResponse` 计算 `total = 0`，分页组件失效
3. 前端发送 `page`/`page_size` 参数但后端忽略，返回全量数据
4. `viewNotification()` 未对 `item.id` 做防御性检查，`undefined` 直接拼入 URL
5. `fetchUnreadCount()` 中 `res.data.unread_count` 无 null 保护

**解决方案**:
1. 后端：移除 `NotificationListView.list()` 覆盖，使用 DRF 标准 `ListAPIView` + `StandardPagination`，添加 `filterset_fields` 替代手动过滤
2. 前端：`viewNotification()` 添加 `if (!item.id)` 防御性检查
3. 前端：`unreadCount.value--` 改为 `Math.max(0, unreadCount.value - 1)` 防止负数
4. 前端：`res.data.unread_count` 改为 `res.data?.unread_count ?? 0` 添加 null 保护

**文件**: `backend/apps/notifications/views.py`, `frontend/src/views/notification/NotificationList.vue`

**预防措施**: ListAPIView 不要覆盖 `list()` 方法绕过分页；前端调用 API 前必须验证必要参数存在；响应数据解包使用可选链 `?.` 和空值合并 `??`

**状态**: **已修复** | 2026-04-16

---

## E344: Login 401 错误 — 拦截器误处理认证端点 401 + admin 密码不匹配

**错误类型**: 前后端交互/认证/拦截器逻辑

**发生场景**: 页面加载时 `autoLoginAsAdmin()` 使用 `admin/admin123` 自动登录，后端返回 401。前端拦截器不区分"登录失败 401"和"Token过期 401"，统一尝试刷新 Token，触发不必要的 `token/refresh/` 请求和误导性"登录已过期"消息。

**根因分析**: 1) admin 用户密码不是 `admin123`（之前被重置为 `Dev@2026changeme`），登录失败返回 401；2) 前端拦截器将认证端点的 401 误判为 Token 过期，触发刷新和登出逻辑

**解决方案**: 
1. 前端 `auth.js` 给 login/register/logout 请求添加 `{ _skipAuthRetry: true }`
2. 前端 `user.js` 的 `logout()` 改用 `authApi.logout()`
3. 重置 admin 用户密码为 `admin123`

**文件**: `frontend/src/api/auth.js`, `frontend/src/store/user.js`, 数据库

**预防措施**: 认证端点请求必须标记 `_skipAuthRetry: true`；`autoLoginAsAdmin` 密码须与数据库一致

**状态**: **已修复** | 2026-04-20

---

## E343: 账户锁定机制多个 Bug — 剩余时间硬编码/不清IP/非原子/DRF限流冲突/无解锁端点

**错误类型**: 后端/认证/安全机制

**发生场景**: 用户登录失败5次后，显示"登录失败次数过多，账户已被锁定，请在15分钟后重试"，但锁定机制存在多个严重 Bug

**根因分析**:

1. **E343-1: `remaining_time` 始终硬编码为15分钟** — `is_login_locked()` 返回 `failure_count`，但 `UserLoginView.post()` 用 `LOGIN_FAILURE_WINDOW // 60` 计算剩余时间，永远显示15分钟，不管实际还剩多少时间

2. **E343-2: `clear_login_failures` 不清除 IP 级别锁定** — 只清除 `login_failure_{username}`，不清除 `login_failure_ip_{ip}`，导致 IP 锁定无法通过成功登录解除

3. **E343-3: `record_login_failure` 非原子操作** — `cache.get() + 1` + `cache.set()` 是 read-modify-write，并发请求时计数丢失

4. **E343-4: `is_login_locked` 使用 `cache.ttl()` 不兼容 LocMemCache** — 开发环境使用 `LocMemCache`，没有 `ttl()` 方法，导致 `AttributeError`

5. **E343-5: DRF `LoginRateThrottle` 与账户锁定机制冲突** — `LoginRateThrottle` 设为 `5/minute`，第5次请求就被 DRF 限流拦截返回429，账户锁定逻辑（5次失败→锁定）根本没机会执行

6. **E343-6: `LOGIN_LOCKOUT_DURATION` 定义了但从未使用** — 锁定时长和失败计数窗口混用同一个 `LOGIN_FAILURE_WINDOW`

7. **E343-7: 没有管理员解锁端点** — 被锁住后只能等15分钟，管理员无法主动解锁

**解决方案**:

1. 新增 `get_user_lockout_key()`/`get_ip_lockout_key()` 函数，锁定状态独立于失败计数
2. `is_login_locked()` 改为存储锁定过期时间戳（`time.time() + LOGIN_LOCKOUT_DURATION`），从时间戳计算实际剩余秒数，兼容所有缓存后端
3. `record_login_failure()` 改用 `cache.incr()` 原子操作，`ValueError` 时 `cache.set(1)`
4. `clear_login_failures(username, ip=None)` 同时清除用户名和 IP 的失败计数及锁定 key
5. `LoginRateThrottle.rate` 从 `5/minute` 调整为 `30/minute`，用户名维度从 `3次→1/minute` 调整为 `10次→5/minute`，避免与账户锁定冲突
6. 新增 `AccountUnlockView`（`POST /api/v1/auth/<pk>/unlock/`），管理员可主动解锁账户
7. `UserLoginView.post()` 中 `clear_login_failures` 传入 `client_ip` 参数

**文件**: `backend/apps/users/views.py`, `backend/apps/users/urls.py`, `backend/core/throttling.py`

**预防措施**: 
1. 锁定状态应独立存储（key + 过期时间戳），不依赖 `cache.ttl()`（LocMemCache 不支持）
2. 缓存计数必须使用 `cache.incr()` 原子操作，禁止 `get+set` read-modify-write
3. DRF 限流器频率必须高于账户锁定阈值，否则会拦截请求导致锁定逻辑无法执行
4. 清除操作必须同时清除用户名和 IP 两个维度的 key
5. 安全机制必须有管理员手动干预入口（解锁端点）

**状态**: **已修复** | 2026-04-20

---

## E342: Logout 401 无限循环 — Token 过期后登出请求触发递归

**错误类型**: 前后端交互/认证/无限循环

**发生场景**: 用户 Token 过期后，前端控制台疯狂输出 `POST /api/v1/auth/logout/ 401 (Unauthorized)`，页面卡死

**根因分析**: 后端 `UserLogoutView` 设置了 `permission_classes = [IsAuthenticated]`，Token 过期时 logout 请求返回 401。前端拦截器捕获 401 后尝试刷新 Token → 失败 → 调用 `userStore.logout()` → logout 再次请求后端 → 再次 401 → 无限循环

**解决方案**: 
1. 后端 `UserLogoutView.permission_classes` 从 `[IsAuthenticated]` 改为 `[AllowAny]`
2. 前端拦截器增加 `_skipAuthRetry` 检查，带此标记的请求不触发 401 重试逻辑
3. 前端 `logout()` 请求添加 `{ _skipAuthRetry: true }` 配置

**文件**: `backend/apps/users/views.py`, `frontend/src/utils/request.js`, `frontend/src/store/user.js`

**预防措施**: 登出/清理类端点不应要求认证；拦截器中由自身发起的请求必须标记跳过 401 重试

**状态**: **已修复** | 2026-04-20

---

## E341: 全面项目审查 — 16项修复（NameError/双重解包/路由缺失/权限/安全/配置）

**错误类型**: 综合/代码质量/安全/配置

**发生场景**: 全面审查项目后端、前端、安全性、配置、数据库六大维度

**根因分析**: 审查发现16项需修复的问题，涵盖：2处运行时NameError、21处前端双重解包、6处API路径404、2处路由未注册、1处响应格式字段丢失、1处分页total计算错误、2处权限缺失、3处asyncio线程安全、1处重复导入、1处默认配置不安全、1处ALLOWED_HOSTS通配符、1处Celery队列缺失、1处Docker镜像版本不兼容

**解决方案**: 
1. 修复 `models.Avg` → `Avg`、`models.Q` → `Q` 导入错误
2. 修复 OneClickLaunch.vue 和 AutomationDashboard.vue 的 `res.data?.success` → `isSuccess(res)` 双重解包
3. 修复 API 路径 `providers` → `llm-providers`、`agent-configs` → `agent-model-configs`
4. 注册 QualificationMatchViewSet 和 `/api/v1/system/health/` 路由
5. UnifiedResponseMiddleware 保留 `success` 字段
6. parseListResponse 优先从 `meta.pagination.total` 取 total
7. 为 scheduler ViewSet 添加权限控制
8. 移除 `asyncio.set_event_loop()` 调用
9. FastAPI 默认配置改为 production
10. ALLOWED_HOSTS 移除通配符
11. production.py 添加 vector 队列
12. Milvus 镜像升级到 v2.4.17

**文件**: `backend/apps/crawler/views.py`, `backend/apps/openclaw/views.py`, `backend/apps/crawler/urls.py`, `backend/config/urls.py`, `backend/common/middleware/unified_response.py`, `backend/apps/scheduler/views.py`, `backend/openclaw/agents/content_recognition_agent.py`, `backend/fastapi_app/main.py`, `backend/config/settings/development.py`, `backend/config/settings/production.py`, `docker-compose.yml`, `frontend/src/views/automation/OneClickLaunch.vue`, `frontend/src/views/automation/AutomationDashboard.vue`, `frontend/src/utils/response-parser.js`

**预防措施**: 
1. 使用 `from django.db.models import Avg, Q` 而非 `models.Avg`/`models.Q`
2. 前端 API 响应已由拦截器解包，直接用 `res.success`/`res.data`，不要 `res.data?.success`/`res.data.data`
3. 新增 ViewSet 必须在 urls.py 注册路由
4. 所有 ViewSet 必须声明 `permission_classes`
5. `asyncio.set_event_loop()` 在多线程环境下不安全，应避免使用
6. 默认配置应使用 production，开发环境通过 .env 覆盖

**状态**: **已修复** | 2026-04-18

---

## E340: 登录接口 500 Internal Server Error — LoginRateThrottle.throttle_failure() 方法签名错误

**错误类型**: 后端/限流器

**发生场景**: 多次登录失败触发限流时，POST /api/v1/auth/login/ 返回 500 Internal Server Error。错误信息：`TypeError: LoginRateThrottle.throttle_failure() missing 2 required positional arguments: 'request' and 'view'`

**根因分析**: `LoginRateThrottle` 重写了 DRF 的 `throttle_failure()` 方法，但添加了 `request` 和 `view` 两个参数。DRF 的 `SimpleRateThrottle.throttle_failure()` 只接受 `self`，内部调用时不传递额外参数，导致 TypeError。此错误只在限流触发时出现（默认5次/分钟后），正常登录不会触发。

**解决方案**: 1) 修改 `throttle_failure()` 方法签名为 `throttle_failure(self)`，与 DRF 父类一致；2) 在 `allow_request()` 中保存 `self._request = request`，供 `throttle_failure()` 使用；3) 调用 `super().throttle_failure()` 时不传额外参数

**文件**: `backend/core/throttling.py`

**预防措施**: 重写 DRF 框架方法时，必须检查父类方法签名是否一致。DRF 的 `SimpleRateThrottle.throttle_failure()` 只接受 `self`，不应添加额外参数

**状态**: **已修复** | 2026-04-20

---

## E339: 网站模板"测试配置"按钮 400 Bad Request — code 唯一约束冲突

**错误类型**: 前后端交互/逻辑错误

**发生场景**: 在网站模板管理页面，点击表单对话框中的"测试配置"按钮时，POST /api/v1/crawler/templates/ 返回 400，错误信息"具有 网站编码 的 网站模板 已存在"

**根因分析**: `testTemplate` 函数采用"先创建临时模板→测试→删除"的方式测试配置。当 `code` 字段与已有模板重复时（特别是编辑已有模板时），`createWebsiteTemplate` 因 `code` 的 `unique=True` 约束返回 400。编辑模式下模板已存在，根本不需要创建。

**解决方案**: 1) 后端新增 `test_config` 端点（POST /api/v1/crawler/templates/test_config/），接受配置数据直接测试不保存；2) 前端编辑模式直接用现有模板 ID 调用 testWebsiteTemplate，新建模式调用 testWebsiteTemplateConfig

**文件**: `backend/apps/crawler/views.py`, `frontend/src/api/crawler.js`, `frontend/src/views/system/WebsiteTemplateList.vue`

**预防措施**: 测试功能不应依赖数据持久化。需要"试运行"的场景，应提供独立的测试端点，而非走创建-测试-删除的流程

**状态**: **已修复** | 2026-04-15

---

## E338: JWT 认证 401 Unauthorized — CookieTokenRefreshView 不处理 Token 轮换 + isLoggedIn 依赖不可读 HttpOnly Cookie

**错误类型**: 认证/JWT

**发生场景**: 页面加载/刷新时，多个 API 返回 401 Unauthorized（tenders/trend、openclaw/agent-model-configs、auth/token/refresh）

**根因分析**: 4个问题叠加：1) CookieTokenRefreshView 在 ROTATE_REFRESH_TOKENS=True 时不生成新 refresh_token 也不更新 Cookie，第二次刷新必然 401；2) isLoggedIn 依赖 getCookie('access_token') 但 Cookie 是 HttpOnly 的，JS 无法读取，页面刷新后 isLoggedIn 始终为 false；3) 前端 logout() 不调用后端，Cookie 中的 token 仍有效；4) refreshAccessToken() 不更新 Store，后续请求使用旧 token

**解决方案**: 1) 重写 CookieTokenRefreshView：blacklist 旧 refresh_token，用 RefreshToken.for_user() 生成新 token，设置新 Cookie；2) isLoggedIn 改为 !!token.value || !!userInfo.value，token 存储改用 sessionStorage；3) logout() 先调用后端 /v1/auth/logout/；4) refreshAccessToken() 成功后调用 userStore.setToken()

**文件**: `backend/apps/users/views.py`, `frontend/src/store/user.js`, `frontend/src/utils/request.js`

**预防措施**: 使用 HttpOnly Cookie 时，前端状态判断不能依赖 document.cookie；Token 轮换必须同步更新 Cookie；logout 必须通知后端清理 token

**状态**: **已修复** | 2026-04-18

---

## E334: Pyppeteer signal 在 Celery Worker 线程中失败 + Chromium 下载404

**错误类型**: 爬虫/浏览器初始化

**发生场景**: Celery Worker 执行采集任务时，Pyppeteer 浏览器初始化失败，报错 "signal only works in main thread of the main interpreter"；后续尝试下载 Chromium 时报404（下载URL已失效）

**根因分析**: 1) Pyppeteer 的 `launch()` 方法内部使用 Python `signal` 模块注册 SIGINT/SIGTERM 处理器，该模块只能在主线程中工作。Celery Worker 在工作线程中执行任务，导致 signal 错误；2) 系统Chrome不存在时，Pyppeteer 尝试下载自带Chromium，但下载URL（`chromium-browser-snapshots/Win_x64/1181205/chrome-win.zip`）已失效返回404；3) `init_browser` 返回False但调用方未检查返回值，导致 `self.page` 为None时调用 `.goto()` 报 AttributeError

**解决方案**: 1) 在 `launch_options` 中添加 `handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False`，禁用 Pyppeteer 的信号处理；2) 在 `PyppeteerCrawler` 基类添加 `find_browser_executable()` 静态方法，自动搜索系统 Chrome/Edge/Brave 浏览器路径；3) 所有调用 `init_browser` 的地方检查返回值，失败时提前返回；4) `stealth_crawler.py` 同步修复

**文件**: `backend/crawler/pyppeteer_crawler.py`, `backend/crawler/shanghai_gov_crawler_v2.py`, `backend/crawler/stealth_crawler.py`

**预防措施**: 在非主线程中使用 Pyppeteer 时，必须禁用信号处理参数（handleSIGINT/TERM/HUP=False）；始终提供系统浏览器路径（executablePath），避免依赖 Pyppeteer 自动下载 Chromium；调用 init_browser 后必须检查返回值

**状态**: **已修复** | 2026-04-16

---

## E335: ShanghaiGovCrawler 仅依赖视觉模型导致采集失败

**错误类型**: 爬虫/数据解析

**发生场景**: 上海政府采购网采集任务执行后，视觉模型（qwen3-vl:8b）返回空内容，采集0条数据

**根因分析**: `ShanghaiGovCrawler._crawl_by_headless` 仅使用 `_parse_with_vision`（视觉模型截图分析），但视觉模型返回空内容。页面实际有数据（`<ul class="list">` → `<li>` 结构），但 `_extract_items` 的选择器不匹配。

**解决方案**: 1) `_crawl_by_headless` 优先 HTML 解析，视觉模型作为降级；2) `_extract_items` 添加 `ul.list > li` 优先选择器；3) `_parse_item` 添加 `raw_data` 字段

**文件**: `backend/crawler/shanghai_gov_crawler_v2.py`

**预防措施**: 爬虫应优先使用 HTML 解析（可靠、快速），视觉模型仅作为降级方案。

**状态**: **已修复** | 2026-04-16

---

## E336: 地区过滤无法匹配上海直辖市区级地区

**错误类型**: 采集任务/数据过滤

**发生场景**: 采集上海政府采购网数据时，所有上海区级地区（松江区、杨浦区等）的数据被地区过滤跳过

**根因分析**: 地区过滤只取省和市两级，不取区级。上海是直辖市，"上海" 不在 "松江区" 中，导致匹配失败。

**解决方案**: 1) 地区配置解析添加区级；2) 匹配时去后缀（区/县）；3) 添加直辖市特殊处理

**文件**: `backend/crawler/tasks.py`

**预防措施**: 地区匹配需考虑直辖市（上海/北京/天津/重庆）的特殊性，区级地名应能匹配到对应的直辖市。

**状态**: **已修复** | 2026-04-16

---

## E337: ContentRecognitionAgent 异步上下文调用 Django ORM 失败

**错误类型**: 后端/异步编程

**发生场景**: 采集任务的内容识别阶段，所有项目识别失败，报错 "You cannot call this from an async context" 或 "sync_to_async can only be applied to sync functions"

**根因分析**: 1) `_load_extraction_rules()` 在 `__init__` 中同步调用 ORM；2) `_save_recognized_content()` 被 `@sync_to_async` 装饰后又用 `sync_to_async` 包装（双重包装）；3) `PROJECT_TYPE_CHOICES` 常量缺失

**解决方案**: 1) `_load_extraction_rules` 检测异步上下文，延迟到 `execute()` 中用 `asyncio.to_thread` 加载；2) 移除 `@sync_to_async` 装饰器，改用 `asyncio.to_thread`；3) 添加 `PROJECT_TYPE_CHOICES`；4) 传递完整 CrawlResult 数据

**文件**: `backend/openclaw/agents/content_recognition_agent.py`, `backend/core/constants.py`, `backend/crawler/tasks.py`

**预防措施**: Django ORM 不能在异步上下文中直接调用，必须使用 `asyncio.to_thread` 或 `sync_to_async`。避免对已装饰的方法再次包装。

**状态**: **已修复** | 2026-04-16

---

## E331: 向量同步信号阻塞请求导致企业编辑保存超时

**错误类型**: 后端/性能阻塞

**发生场景**: 编辑企业信息后点击保存，请求超时（120秒），对话框不关闭

**根因分析**: `vector_sync_manager.py` 的 `post_save` 信号处理器同步执行 ChromaDB 向量同步。ChromaDB 的 `upsert` 操作使用默认嵌入模型（all-MiniLM-L6-v2），该模型需从网络下载（79.3MB），下载极慢导致 upsert 阻塞。Django 开发服务器单线程，整个请求被阻塞。

**解决方案**: 信号处理器改为在 `threading.Thread(daemon=True)` 后台线程中执行向量同步，请求立即返回。线程启动失败时回退到同步执行。

**文件**: `backend/common/utils/vector_sync_manager.py`

**预防措施**: 所有涉及外部服务调用（ChromaDB、网络请求等）的信号处理器必须异步执行，避免阻塞 Django 请求线程。

**状态**: **已修复** | 2026-04-16

---

## E332: BaseViewSet 数据隔离导致无法编辑其他用户创建的企业

**错误类型**: 后端/权限过滤

**发生场景**: admin 用户编辑由 testuser 创建的企业时，PATCH 请求返回 404

**根因分析**: `BaseViewSet.get_queryset()` 按 `created_by=self.request.user` 过滤数据，admin 用户无法看到其他用户创建的企业记录

**解决方案**: 在 `EnterpriseViewSet` 中重写 `get_queryset()`，返回所有企业（不按 created_by 过滤），企业管理是全局操作

**文件**: `backend/apps/enterprise/views.py`

**预防措施**: 需要全局访问的 ViewSet 应重写 `get_queryset()` 取消用户隔离；或使用 `AuthenticatedModelViewSet` 替代 `BaseViewSet`

**状态**: **已修复** | 2026-04-16

---

## E333: EnterpriseListSerializer 未解密银行账号 + 解密异常未捕获

**错误类型**: 后端/序列化器 + 安全

**发生场景**: 1) 前端编辑表单显示加密后的银行账号乱码；2) AESCrypto.decrypt() 抛出未捕获异常导致列表 API 返回 500

**根因分析**: `EnterpriseListSerializer` 没有 `to_representation()` 方法解密 `bank_account`，前端收到加密值后原样发回导致二次加密。`EnterpriseSerializer.to_representation()` 中 `AESCrypto.decrypt()` 无 try/except，解密失败时抛出 ValueError 导致 500。

**解决方案**: 1) 为 `EnterpriseListSerializer` 添加 `to_representation()` 解密 bank_account；2) 两个 Serializer 的 `to_representation()` 都添加 try/except，解密失败返回空字符串；3) 新增 `bank_account_masked` 脱敏字段

**文件**: `backend/apps/enterprise/serializers.py`

**预防措施**: 所有涉及加密字段的 Serializer 必须在 `to_representation()` 中解密，且必须添加 try/except 防止解密异常导致 500 错误

**状态**: **已修复** | 2026-04-16

---

## E330: ProjectKnowledge.vue API 路径重复 /api 前缀 + ServiceMonitor.vue 响应数据未解包

**错误类型**: 前端/URL路径错误 + 前端/响应数据解包

**发生场景**:
1. `GET /api/api/v1/knowledge/ 404` — URL 出现双重 `/api` 前缀
2. `Invalid prop: type check failed for prop "value". Expected String|Number|Boolean|Object, got Undefined` — ServiceMonitor ElOption value 为 undefined

**根因分析**:
1. `ProjectKnowledge.vue` 中 `request.get('/api/v1/knowledge/')` — axios baseURL 已包含 `/api`，导致最终 URL 为 `/api/api/v1/knowledge/`
2. `ServiceMonitor.vue` 中 `fetchCategories` 和 `fetchDashboard` 直接将完整 UnifiedResponse 对象赋给变量，未提取 `.data` 字段。axios 拦截器返回 `response.data`（即 `{success, code, message, data}`），`v-for` 遍历对象属性而非数组，导致 `cat.value` 为 undefined

**解决方案**:
1. `request.get('/api/v1/knowledge/')` → `request.get('/v1/knowledge/')`（去掉多余 `/api` 前缀）
2. `request.get('/api/v1/knowledge/context/')` → `request.get('/v1/knowledge/context/')`
3. `categories.value = res` → `categories.value = res.data || []`
4. `dashboardData.value = res` → `dashboardData.value = res.data || null`

**文件**:
- `frontend/src/views/system/ProjectKnowledge.vue`
- `frontend/src/views/system/ServiceMonitor.vue`

**预防措施**: 使用 `request.get()` 时 URL 路径不应包含 baseURL 已有的 `/api` 前缀；API 响应需通过 `.data` 提取实际数据，不要直接使用整个响应对象。

**状态**: **已修复** | 2026-04-16

---

## E329: ProjectKnowledge.vue 组件未导入 + 数组空值导致渲染崩溃

**错误类型**: 前端/组件未注册 + 前端/空值保护缺失

**发生场景**: 访问"项目知识库"页面时出现两个错误：
1. `[Vue warn]: Failed to resolve component: PageHeader`
2. `TypeError: Cannot read properties of undefined (reading 'slice')`

**根因分析**:
1. `ProjectKnowledge.vue` 模板中使用了 `<PageHeader>` 组件，但 `<script setup>` 中未导入 `import { PageHeader } from '@/components'`
2. 模板中 `knowledge.api_routes.slice(0, 30)` 和 `row.files.slice(0, 5)` 未做空值保护，当 API 返回数据中缺少 `api_routes` 或 `files` 字段时触发 TypeError

**解决方案**:
1. 添加 `import { PageHeader } from '@/components'`
2. 将 `knowledge.api_routes.slice(0, 30)` 改为 `(knowledge.api_routes || []).slice(0, 30)`
3. 将 `row.files.slice(0, 5)` 改为 `(row.files || []).slice(0, 5)`
4. 将 `row.files.length > 5` 改为 `(row.files || []).length > 5`

**文件**: `frontend/src/views/system/ProjectKnowledge.vue`

**预防措施**: Vue 3 `<script setup>` 中使用的组件必须显式 import；模板中对数组调用 `.slice()` 等方法前必须做空值保护（`|| []`）。

**状态**: **已修复** | 2026-04-16

---

## E328: TaskSchedulerViewSet 路由未注册导致 scheduler/status 404 错误

**错误类型**: 后端/路由缺失

**发生场景**: 前端 GET `/api/v1/openclaw/scheduler/status/` 返回 404，AutomationDashboard 的"调度任务"和"系统状态"Tab页数据加载全部失败

**根因分析**:
- `TaskSchedulerViewSet` 在 `apps/openclaw/workflow_views.py` 中已完整定义（含 status/health/start/stop/enable_task/disable_task/run_now 共7个 action）
- 但 `apps/openclaw/urls.py` 中未 import `TaskSchedulerViewSet`，也未 `router.register()` 注册
- DRF Router 不会为未注册的 ViewSet 生成 URL，导致所有 scheduler 相关端点返回 404
- 影响前端5个 API 调用：scheduler/status/、scheduler/health/、scheduler/enable_task/、scheduler/disable_task/、scheduler/run_now/

**解决方案**: 在 `openclaw/urls.py` 中添加 import 和 router.register:
```python
from .workflow_views import BidWorkflowViewSet as AutomationWorkflowViewSet, TaskSchedulerViewSet
router.register(r'scheduler', TaskSchedulerViewSet, basename='scheduler')
```

**文件**: `backend/apps/openclaw/urls.py`

**预防措施**: 新增 ViewSet 后必须同步在 urls.py 中注册路由。建议在 ViewSet 文件中添加注释提醒。

**状态**: **已修复** | 2026-04-16

---

## E327: BaseRepository 缺少 Type 导入导致 bids/statistics 500 错误

**错误类型**: 后端/导入缺失

**发生场景**: 前端 GET `/api/v1/bids/statistics/` 返回 500，错误信息 `NameError: name 'Type' is not defined`

**根因分析**:
- `services/data/base_repository.py` 第5行 `from typing import TypeVar, Generic, List, Optional, Dict, Any` 遗漏了 `Type`
- 第18行 `def __init__(self, model: Type[T])` 使用了 `Type` 作为类型注解
- Python 在运行时求值类型注解时触发 `NameError`
- 影响链路: `BidStatisticsView.update_statistics()` → `from services.data import BidRepository` → `BidRepository.__init__()` → `BaseRepository.__init__(self, model: Type[T])` → **NameError**

**解决方案**: 在 `base_repository.py` 的 typing import 中添加 `Type`:
```python
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
```

**文件**: `backend/services/data/base_repository.py`

**预防措施**: 使用 typing 类型注解时，确保所有引用的类型都已导入。IDE 的类型检查器通常能捕获此类错误。

**状态**: **已修复** | 2026-04-16

---

## E326: restart_manager 重启策略重构 — 统一 Docker 容器优先 + 本地进程回退

**错误类型**: 后端/服务管理（E325 的后续重构）

**发生场景**: 用户确认所有服务（Ollama/Celery/PostgreSQL/Redis/MinIO/Chroma/Django/Milvus）均运行在 Docker 容器中，E325 的修复基于错误的部署假设

**根因分析**:

1. **E326-1: E325 修复假设部分服务是本地进程，实际全部是 Docker 容器**
   - Ollama、Celery Worker/Beat、PostgreSQL、Redis、MinIO、Django、Milvus 都有对应的 Docker 容器
   - 只有 Chroma（嵌入式）和 Ollama（用户选择保持本地进程）例外

2. **E326-2: `_is_docker_available()` 使用 `docker info` 检测，但 Windows Docker Desktop 返回非零 exit code**
   - `docker info` 在 Windows 上即使 Docker 正常运行也可能返回 exit code -1
   - 改用 `docker version` 并检查 stdout 中是否包含 "Version"

3. **E326-3: 旧代码 Windows/Linux 分离逻辑不必要**
   - Docker 容器重启是跨平台的，不需要区分 Windows/Linux
   - 只有本地进程回退才需要平台特定逻辑

**修复内容**:

1. 新增 `DOCKER_CONTAINER_MAP` — 统一管理所有 Docker 容器名映射（基于 docker-compose.yml）:
   - `bid-postgres`, `bid-redis`, `bid-celery-worker`, `bid-celery-beat`, `bid-backend`, `bid-fastapi`, `bid-milvus`, `bid-minio`, `bid-frontend`, `bid-gateway`, `bid-milvus-etcd`

2. 新增 `LOCAL_PROCESS_FALLBACK` — 开发环境本地进程回退配置:
   - Ollama: 本地进程（用户选择保持）
   - Celery Worker/Beat: 本地进程回退
   - PostgreSQL/Redis: Windows 服务回退
   - MinIO: 本地进程回退
   - Django: 本地进程回退

3. 统一重启优先级: 嵌入式检查 → Docker 容器 → 本地进程回退

4. 删除 `_do_restart_windows()` 和 `_do_restart_linux()`，统一为 `_do_restart()`

5. 新增方法:
   - `_try_docker_restart_by_name()`: 通过 DOCKER_CONTAINER_MAP 查找容器名并重启
   - `_try_local_process_restart()`: 本地进程回退（含 Windows 服务支持）
   - `_restart_windows_service()`: Windows 服务重启
   - `_is_docker_available()`: 改用 `docker version` 检测

**文件**:
- `backend/apps/monitor/restart_manager.py`
- `backend/apps/monitor/views.py`

**预防措施**:
1. 重启策略必须以 Docker 容器为第一优先级，本地进程仅作开发环境回退
2. `docker info` 不可靠，使用 `docker version` 检测 Docker 可用性
3. 新增 Docker 容器时，必须更新 `DOCKER_CONTAINER_MAP`

**状态**: **已修复** | 2026-04-16

---

## E325: 服务重启 API 返回 400 — restart_manager 重启策略与实际部署方式不匹配

**错误类型**: 后端/服务管理

**发生场景**: 前端 `POST /api/v1/monitor/services/7/restart/` 重启 MinIO 服务时返回 400 Bad Request，错误信息 "Docker容器 bid-minio 不存在，该服务未通过Docker部署，无法通过此方式重启"

**根因分析**:

1. **E325-1: restart_manager 假设所有非 Windows 服务/进程的服务都运行在 Docker 中**
   - `_do_restart_windows()` 的逻辑链: Windows服务 → 本地进程 → Docker容器
   - MinIO/Chroma/Milvus/Ollama 都被硬编码为 Docker 容器重启方式
   - 但实际部署: Chroma 是嵌入式 Python 库、MinIO 未安装、Milvus 未部署、Ollama 是本地进程

2. **E325-2: Docker 容器不存在时直接返回失败，无回退策略**
   - `docker inspect` 失败后直接返回 `False, "Docker容器 xxx 不存在"`
   - 没有尝试本地进程重启作为回退

3. **E325-3: 缺少对嵌入式服务和不可重启服务的处理**
   - Chroma 以 `PersistentClient` 嵌入式运行，无法独立重启
   - Django Server 重启会终止当前请求处理进程
   - 这些服务缺少明确的错误提示

4. **E325-4: 前端重启按钮仅对 `auto_restart_enabled` 的服务显示**
   - `ServiceMonitor.vue` 中 `v-if="service.auto_restart_enabled"` 限制了手动重启入口
   - 用户无法对未启用自动重启的服务执行手动重启

5. **E325-5: 前端错误消息提取不完整**
   - `ServiceMonitor.vue` 的 `handleRestart` 使用 `error.message` 而非 `error?.response?.data?.message`
   - 后端 UnifiedResponse 中的详细错误消息可能丢失

**修复内容**:

1. `restart_manager.py` 新增 `WINDOWS_PROCESS_COMMANDS` 条目:
   - `ollama`: 本地进程重启 (`C:\Users\ZhangGan\AppData\Local\Programs\Ollama\ollama.exe serve`)
   - `minio`: 本地进程重启 (`minio server D:\共享文件\AUTO\minio_data --console-address :9001`)
   - `django`: 标记 `skip_restart=True`，不支持通过 API 重启

2. `restart_manager.py` 新增 `EMBEDDED_SERVICES` 字典:
   - `chroma`: 标记为嵌入式服务，提示"随 Django 服务自动重启"

3. `restart_manager.py` 重构 `_do_restart_windows()`:
   - 新增嵌入式服务检查（优先级最高）
   - 新增 `skip_restart` 标记检查
   - 新增可执行文件存在性检查 (`_find_executable`)
   - 新增进程运行状态检查 (`_is_process_running`)
   - 可执行文件不存在且进程未运行时，回退到 Docker 重启

4. `restart_manager.py` 新增 `_try_docker_restart()` 方法:
   - 独立的 Docker 重启逻辑
   - 容器不存在时调用 `_fallback_local_process()` 回退

5. `restart_manager.py` 新增 `_fallback_local_process()` 方法:
   - Docker 不可用时尝试本地进程重启
   - 可执行文件不存在时返回明确的"未安装"错误

6. `views.py` 扩展 `unsupported_keywords` 列表:
   - 新增 `'未部署'`, `'嵌入式'`, `'手动重启'` 关键词

7. `ServiceMonitor.vue`:
   - 移除重启按钮的 `v-if="service.auto_restart_enabled"` 限制
   - 改进错误消息提取: `error?.response?.data?.message || error?.message`

**文件**:
- `backend/apps/monitor/restart_manager.py`
- `backend/apps/monitor/views.py`
- `frontend/src/views/system/ServiceMonitor.vue`

**预防措施**:
1. 新增监控服务时，必须同时在 `WINDOWS_PROCESS_COMMANDS` 或 `EMBEDDED_SERVICES` 中配置重启策略
2. 重启策略应支持多级回退: 本地进程 → Docker → 明确错误
3. 对可执行文件路径做存在性检查，避免启动失败
4. 前端重启按钮不应依赖 `auto_restart_enabled`，手动重启是独立功能

**状态**: **已修复** | 2026-04-16

---

## E324: UI全面重新设计 — 靛青蓝配色体系迁移

**错误类型**: 前端/样式系统

**发生场景**: 前端UI全面重新设计，从旧蓝绿配色(#0066CC)迁移到靛青蓝配色(#4F46E5)，涉及40个页面和15个公共组件

**根因分析**:

1. **E324-1: Element Plus 主题覆盖未生效**
   - `main.js` 中 `import 'element-plus/dist/index.css'` 引入预编译CSS，覆盖了 `element-variables.scss` 中的SCSS变量定制
   - 解决：移除预编译CSS引入，改为通过SCSS编译入口引入

2. **E324-2: 旧色值散布在25+个文件中**
   - `#909399`(旧信息色) 出现61次，`#67C23A`/`#E6A23C`/`#F56C6C` 等 Element Plus 默认色值散布在组件中
   - `rgba(0,102,204,...)` 等旧主色rgba值出现在6个文件
   - 解决：批量替换所有旧色值为新配色体系

**解决方案**:
1. 重写 `variables.scss` — 全部CSS变量更新为靛青蓝色系
2. 重写 `element-variables.scss` — Element Plus主题变量覆盖
3. 移除 `main.js` 中 `import 'element-plus/dist/index.css'`
4. 批量替换25个文件中的97处旧色值
5. 重写 Login.vue 为左右分栏布局
6. 重写 Dashboard.vue 为D3混合型仪表盘

**预防措施**:
1. 所有颜色必须使用CSS变量（`var(--color-xxx)`），禁止硬编码hex值
2. Element Plus样式必须通过SCSS编译引入，不使用预编译CSS
3. 新增组件时参考 `variables.scss` 中的变量名

**状态**: **已修复** | 2026-04-16

---

## E323: auto_bid_threshold 字段空值导致企业更新 400 错误

**错误类型**: 后端/数据验证 + 前端/空值处理

**发生场景**: 前端 PATCH `/api/v1/enterprise/enterprises/5/` 更新企业信息时返回 400 Bad Request，错误信息 `auto_bid_threshold: 该字段不能为 null。`

**根因分析**:

1. **E323-1: 后端 `auto_bid_threshold` 空值未处理**
   - `EnterpriseSerializer.to_internal_value()` 的 `integer_fields` 仅包含 `['staff_count', 'insured_count']`，遗漏了 `auto_bid_threshold`
   - `auto_bid_threshold` 模型定义为 `IntegerField(default=60)`，**无 `null=True`**，不允许 null 值
   - 前端发送 `auto_bid_threshold: null` 时，DRF IntegerField 验证失败
   - E322 修复时已意识到此问题但选择不处理，导致前端发送 null 时必然 400

2. **E323-2: 前端 CompanyInfo.vue 将 auto_bid_threshold 转为 null**
   - `numericFields` 数组包含 `'auto_bid_threshold'`，空值时统一转为 `null`
   - 但 `auto_bid_threshold` 不允许 null，应使用默认值 60

3. **E323-3: 前端 EnterpriseForm.vue `|| 60` 运算符误杀合法值 0**
   - `form.auto_bid_threshold || 60`：当值为 `0` 时，`0 || 60` 返回 `60`，误将合法的 0 值替换为默认值
   - 应使用 `?? 60`（nullish coalescing），仅在 `null/undefined` 时使用默认值

**修复内容**:

1. 后端 `EnterpriseSerializer.to_internal_value()` 新增 `default_value_fields = {'auto_bid_threshold': 60}`，空值/null 自动填充默认值
2. 前端 `CompanyInfo.vue` 将 `auto_bid_threshold` 从 `numericFields` 中移除，单独处理：空值→60，有效数字保留
3. 前端 `EnterpriseForm.vue` 将 `|| 60` 改为 `?? 60`

**文件**:
- `backend/apps/enterprise/serializers.py`
- `frontend/src/views/CompanyInfo.vue`
- `frontend/src/views/company/EnterpriseForm.vue`

**预防措施**:
1. `to_internal_value()` 中，无 `null=True` 的字段不能转为 None，应使用 `default_value_fields` 映射填充默认值
2. 前端 `||` 运算符会误杀 falsy 值（0、false），对数值字段应使用 `??`（nullish coalescing）
3. 新增 IntegerField 时，若有 `default` 但无 `null=True`，必须加入 `default_value_fields` 而非 `integer_fields`

**状态**: **已修复** | 2026-04-16

---

## E322: EnterpriseSerializer.to_internal_value 未处理 IntegerField 空字符串 + chroma_client.is_available 属性误用为方法

**错误类型**: 后端/数据验证 + 后端/属性调用错误

**发生场景**: 
1. 前端 POST `/api/v1/enterprise/enterprises/` 创建企业时返回 400，错误信息 `staff_count: 请填写合法的整数值。; insured_count: 请填写合法的整数值。`
2. 企业创建成功后日志报 `[ERROR] 企业向量创建失败: 'bool' object is not callable`

**根因分析**:

1. **E322-1: IntegerField 空字符串未处理**
   - `EnterpriseSerializer.to_internal_value()` 处理了 `date_fields`、`decimal_fields`、`string_fields` 的空字符串→None转换，但遗漏了 `integer_fields`（`staff_count`、`insured_count`）
   - 前端 `<el-input type="number">` 清空后返回空字符串 `''`，虽然前端 `numericFields` 处理会转为 `null`，但后端应防御性处理

2. **E322-2: chroma_client.is_available 属性误用**
   - `chroma_client.is_available` 是 `@property`（返回 `self._available`），但 10 处代码用 `is_available()` 调用
   - Python 调用 `True()` → `'bool' object is not callable` TypeError
   - 注意：`CircuitBreaker.is_available()` 是方法（有 `def`），不需要修改

**修复内容**:

1. `EnterpriseSerializer.to_internal_value()` 新增 `integer_fields = ['staff_count', 'insured_count']`，空字符串→None
   - 注意：`auto_bid_threshold` 不是 nullable（有 `default=60` 但无 `null=True`），不能转为 None，不包含在内
2. 10 处 `chroma_client.is_available()` → `chroma_client.is_available`：
   - `services/vector/base_store.py`：6 处
   - `services/vector/transaction.py`：1 处
   - `services/bid_automation_workflow.py`：2 处

**文件**:
- `backend/apps/enterprise/serializers.py`
- `backend/services/vector/base_store.py`
- `backend/services/vector/transaction.py`
- `backend/services/bid_automation_workflow.py`

**预防措施**:
1. `to_internal_value()` 应覆盖所有 nullable 字段类型（CharField、DecimalField、IntegerField、DateField），不可遗漏
2. `@property` 定义的属性不能加 `()` 调用，IDE 类型检查应捕获此类错误
3. 新增 nullable IntegerField 时，必须同步更新 `to_internal_value()` 的 `integer_fields` 列表

**状态**: **已修复** | 2026-04-15

---

## E321: 表单草稿自动缓存功能实现

**错误类型**: 功能缺失/用户体验

**发生场景**: 用户在填写表单过程中（企业信息、文档生成、自动化配置、采集计划等），如果关闭浏览器或意外离开页面，所有已输入的数据将丢失，无法恢复

**修复内容**:

1. **E321-1: 创建 useFormDraft composable**
   - 问题: 项目无任何表单自动保存/草稿功能，所有表单提交都是用户手动点击后直接调用API
   - 修复: 创建 `frontend/src/composables/useFormDraft.js`，提供通用表单草稿缓存机制
   - 功能:
     - 实时监测用户输入，5秒防抖自动保存 + 30秒周期性保存
     - 重新打开页面时检测草稿并提示恢复（ElMessageBox.confirm）
     - 7天过期自动清理
     - 敏感字段自动脱敏（password/api_key/bank_account/credit_code等→`••••••••`）
     - 成功保存后自动清除草稿
     - 存储空间不足时自动清理过期草稿后重试
   - 文件: `frontend/src/composables/useFormDraft.js`（新增）

2. **E321-2: 集成到7个表单页面**
   - EnterpriseForm.vue: 缓存企业表单（排除bank_account/credit_code），保存后清除
   - DocumentGenerate.vue: 缓存文档生成表单，生成成功后清除
   - AutomationConfig.vue: 6个配置表单合并缓存，任一保存后清除
   - CreateSchedule.vue: 缓存新建采集计划，创建成功后清除
   - EditSchedule.vue: 缓存编辑采集计划，更新成功后清除
   - OneClickLaunch.vue: 分别缓存企业表单和LLM配置，各自保存后清除
   - Profile.vue: 缓存用户信息（密码自动排除），保存后清除
   - 文件: 7个Vue组件（修改）

**预防措施**:
1. 新增表单页面应集成 `useFormDraft`，避免用户输入丢失
2. `useFormDraft` 必须在 `reactive()` 定义之后调用
3. 含密码字段的表单无需额外配置，SENSITIVE_FIELDS 自动排除
4. 存储前缀 `form_draft_`，新增缓存Key应避免与已有Key冲突

**状态**: **已完成** | 2026-04-15

---

## E320: ollama_models 端点 Ollama 不可用时返回 HTTP 400 导致双重错误提示

**错误类型**: 后端/响应状态码 + 前端/错误处理

**发生场景**: 前端调用 `GET /api/v1/openclaw/llm-providers/ollama_models/?url=http://localhost:11434` 时，Ollama 服务未运行，后端返回 HTTP 400，触发 axios 拦截器弹出 `ElMessage.error`，同时 `checkOllamaStatus` 的 catch 块又弹出 `ElMessage.warning`，用户看到两条错误消息

**根因分析**:

1. **后端**: `ollama_models` 视图在 Ollama 不可用时调用 `UnifiedResponse.error(message='连接测试失败')` ，默认 `status_code=400`，将"服务不可用"语义错误地表达为"客户端请求错误"
2. **前端**: axios 响应拦截器对非 2xx 响应自动弹出 `ElMessage.error`，然后 `Promise.reject` 传递到 `checkOllamaStatus` 的 catch 块又弹出 `ElMessage.warning`
3. **对比**: 同文件的 `ollama_status` 端点已使用正确模式：返回 HTTP 200 + `{ connected: False, error: str(e) }`

**修复内容**:

1. **后端 `ollama_models`**: Ollama 不可用时返回 `UnifiedResponse.success(data={ models: [], version: '', connected: False, error: str(e) })`，与 `ollama_status` 端点保持一致
2. **前端 `checkOllamaStatus`**: 检查 `res.data.connected` 字段，区分"连接成功"和"服务不可用"两种业务状态

**文件**:
- `backend/apps/openclaw/views.py` — `ollama_models` action
- `frontend/src/views/system/ModelConfig.vue` — `checkOllamaStatus` 函数

**预防措施**:
1. 外部服务不可用属于业务状态而非客户端错误，应返回 HTTP 200 + 业务状态码（如 `connected: False`），不应返回 HTTP 4xx
2. 前端调用外部服务检查类 API 时，应优先检查响应体中的业务状态字段，而非依赖 HTTP 状态码
3. 新增类似端点时参考 `ollama_status` 的正确模式

**状态**: **已修复** | 2026-04-15

---

## E319: request.get/delete 参数双重包装导致查询参数丢失

**错误类型**: 前端/参数传递

**发生场景**: 前端调用 `request.get()` 传递查询参数时，API 返回 400 错误。例如 `GET /api/v1/openclaw/llm-providers/ollama_models/?params%5Burl%5D=http://localhost:11434` 返回 400

**根因分析**:

`request.js` 中 `request.get(url, params, options)` 方法内部会将第二个参数包装为 `{ params }` 传给 axios：
```javascript
get(url, params = {}, options = {}) {
    return axiosInstance.get(url, { params, ...options })
}
```

但 API 调用方又多包了一层 `params:`：
```javascript
request.get('/v1/openclaw/llm-providers/ollama_models/', {
    params: { url }  // ← 多包了一层！
})
```

导致实际发送 `?params[url]=...` 而非 `?url=...`，后端 `request.query_params.get('url')` 收不到参数。

**影响范围**: 所有使用 `{ params }` 或 `{ params: { ... } }` 模式的 `request.get/delete` 调用，涉及 model.js、monitor.js、enterprise.js、document.js、tender.js、crawler.js、notification.js、userAdmin.js、auth.js、bid.js、automationConfig.js、base.js 等文件

**修复内容**:

更新 `request.get` 和 `request.delete` 方法，智能检测参数格式：
- 如果第二个参数包含 `params` 键且值为对象，视为 axios 配置格式，直接展开
- 否则视为纯参数对象，包装为 `{ params }`

```javascript
get(url, paramsOrConfig = {}, options = {}) {
    if (paramsOrConfig && typeof paramsOrConfig === 'object' && paramsOrConfig.params && typeof paramsOrConfig.params === 'object') {
      return axiosInstance.get(url, { ...paramsOrConfig, ...options })
    }
    return axiosInstance.get(url, { params: paramsOrConfig, ...options })
},
```

**文件**: `frontend/src/utils/request.js`

**预防措施**:
1. `request.get(url, params)` 的第二个参数应该是扁平的查询参数对象，如 `{ page: 1, url: '...' }`
2. 不要再额外包装为 `{ params: { ... } }`，因为方法内部已自动包装
3. 新增 API 调用时参考 `vectorlib.js` 的正确写法：`request.get('/path/', params)`

**状态**: **已修复** | 2026-04-15

---

## E318: 非关键服务健康检查反复刷屏 WARNING 日志

**错误类型**: 日志噪音/性能浪费

**发生场景**: 前端每10秒轮询 `/api/v1/system/services/`，当 Milvus/Chroma/MinIO/Ollama 未运行时，每次缓存过期都重新检查并打印 WARNING 日志，导致终端被刷屏

**修复内容**:

1. **日志级别降级**: 非关键服务（Milvus/Chroma/MinIO/Ollama）检查失败从 `logger.warning()` 降为 `logger.debug()`，避免终端刷屏
2. **已知不可用跳过机制**: 新增 `_optional_services_down` 字典，记录已知不可用的服务及时间戳。120秒内跳过实际网络检查，直接返回 stopped 状态，避免反复发起注定失败的连接请求
3. **缓存 TTL 增加**: 服务状态缓存从 10 秒增加到 30 秒，减少检查频率
4. **Chroma 客户端日志降级**: `chroma_client.py` 中 "Chroma不可用" 相关日志从 `warning` 降为 `info`/`debug`

**文件**:
- `backend/config/urls.py` — `system_services_status` 函数
- `backend/services/vector/chroma_client.py` — `get_collection` 和 `_initialize` 方法

**预防措施**:
1. 非关键服务的健康检查失败不应使用 WARNING 级别
2. 可选服务应有"已知不可用"跳过机制，避免反复发起无效连接
3. 健康检查缓存 TTL 不应低于 30 秒

**状态**: **已修复** | 2026-04-15

---

## E317: 架构整合——统一HTTP客户端 + 事件驱动激活 + Repository模式激活

**错误类型**: 代码重复/架构断裂

**修复内容**:

1. **E317-1: 统一HTTP客户端**
   - 问题: 4处HTTP请求工具重复定义（base_agent/pi/skill_market/embedded），返回格式不统一（data/content/body），仅base_agent有URL安全验证，仅embedded有超时异常区分
   - 修复: 创建 `common/utils/http_client.py` 统一HTTP客户端，内置重试(urllib3 Retry)、超时、熔断器(CircuitBreaker)、URL安全验证、JSON自动解析；4处重复定义全部委托到统一客户端
   - 文件: `backend/common/utils/http_client.py`（新增），`backend/openclaw/base_agent.py`，`backend/openclaw/architecture/pi.py`，`backend/openclaw/skill_market.py`，`backend/openclaw/architecture/embedded.py`

2. **E317-2: 事件驱动激活**
   - 问题: EventBus（core/events.py，445行）完整实现但0个外部引用，_persist_event()使用动态模型创建反模式
   - 修复: 将_persist_event()改为使用正式ORM模型EventStore（core/models.py + 迁移）；创建core/event_handlers.py事件处理器模块（企业CRUD→向量同步、招标/投标事件）；在enterprise/views.py、tenders/views.py、bids/views.py的关键业务操作中通过transaction.on_commit()发布事件
   - 文件: `backend/core/events.py`，`backend/core/models.py`，`backend/core/event_handlers.py`（新增），`backend/core/migrations/0002_eventstore.py`（新增），`backend/apps/enterprise/views.py`，`backend/apps/tenders/views.py`，`backend/apps/bids/views.py`

3. **E317-3: Repository模式激活**
   - 问题: services/data/定义了4个Repository类（748行）但0个外部引用，且3个Repository有Bug（models.Q在import之前使用、TenderRepository引用不存在的Tender模型）
   - 修复: 修复3个Repository的import顺序Bug和模型名错误；在bids/views.py的BidStatisticsView和BidDashboardView中激活BidRepository；在enterprise/views.py的my_enterprise中激活EnterpriseRepository
   - 文件: `backend/services/data/bid_repository.py`，`backend/services/data/enterprise_repository.py`，`backend/services/data/tender_repository.py`，`backend/services/data/__init__.py`，`backend/apps/bids/views.py`，`backend/apps/enterprise/views.py`

**预防措施**:
1. 新的HTTP请求代码必须使用 `common/utils/http_client`，禁止直接 import requests
2. 新的业务CRUD操作应通过 `transaction.on_commit()` 发布事件
3. 新的查询逻辑应优先放在 Repository 层，Views 通过 Repository 访问数据
4. 禁止在函数内部动态创建 Django Model，必须使用正式的 models.py + migration

**状态**: **已完成** | 2026-04-15

---

## E316: UnifiedResponse.error() 忽略 status_code 参数 + exception_handler 使用未注册的 error_code

**错误类型**: 响应状态码错误/错误码映射

**修复内容**:

1. **E316-1: UnifiedResponse.error() 忽略 status_code 参数**
   - 问题: `UnifiedResponse.error()` 当传入 `error_code` 参数时，调用 `get_http_status(error_code)` 获取 HTTP 状态码，完全忽略调用者传入的 `status_code` 参数。当 `error_code` 不在 `_error_code_mapping` 中时，`get_http_status()` 返回默认值 500，导致所有使用自定义 `error_code` 字符串的错误响应都返回 HTTP 500
   - 修复: 在 `UnifiedResponse.error()` 中添加防御逻辑：当 `get_http_status()` 返回 500 但调用者明确传入了非 500 的 `status_code` 时，使用调用者的 `status_code`
   - 文件: `backend/utils/responses.py`（第 99-101 行新增）

2. **E316-2: exception_handler 使用未注册的 error_code 字符串**
   - 问题: `common/exceptions.py` 中的 `exception_handler` 使用自定义字符串作为 `error_code`（如 `'AUTHENTICATION_REQUIRED'`、`'AUTHENTICATION_FAILED'`、`'PERMISSION_DENIED'`、`'RATE_LIMITED'`），但 `get_http_status()` 的映射表 `_error_code_mapping` 使用数字码作为键（如 `"2003"`、`"1008"`），导致查找失败返回默认 500
   - 修复: 将 `exception_handler` 中的 `error_code` 改为使用 `ErrorCode` 枚举值的数字码：`ErrorCode.AUTH_TOKEN_MISSING.value[0]`、`ErrorCode.AUTH_TOKEN_INVALID.value[0]`、`ErrorCode.PERMISSION_DENIED.value[0]`、`ErrorCode.RATE_LIMITED.value[0]`
   - 文件: `backend/common/exceptions.py`（exception_handler 函数）

**影响范围**: 所有 DRF 异常响应的 HTTP 状态码。修复前，未认证请求返回 500 而非 401，权限不足返回 500 而非 403，限流返回 500 而非 429

**预防措施**:
1. `UnifiedResponse.error()` 使用 `error_code` 参数时，必须确保该 code 在 `ErrorCode` 枚举中已注册
2. 新增 `ErrorCode` 枚举值时，`_error_code_mapping` 会自动更新（基于枚举遍历），无需手动维护
3. 测试 API 时应验证 HTTP 状态码是否正确，而不仅仅是响应体内容

**状态**: **已完成** | 2026-04-15

---

## E315: E313删除core.exceptions后遗漏的EXCEPTION_HANDLER配置 + 数据库迁移缺失

**错误类型**: 配置遗漏/数据库迁移

**修复内容**:

1. **E315-1: DRF EXCEPTION_HANDLER 引用已删除的 core.exceptions**
   - 问题: E313-2 删除了 `core/exceptions.py`，但 `config/settings/base.py` 第171行仍配置 `'EXCEPTION_HANDLER': 'core.exceptions.exception_handler'`，导致所有 DRF 视图在异常时触发 `ModuleNotFoundError: No module named 'core.exceptions'`，返回 500 而非正常错误响应
   - 修复: 在 `common/exceptions.py` 中新增 DRF 兼容的 `exception_handler(exc, context)` 函数，将所有异常统一转换为 `UnifiedResponse` 格式；更新 settings 引用为 `'common.exceptions.exception_handler'`
   - 文件: `backend/common/exceptions.py`（新增 exception_handler 函数），`backend/config/settings/base.py`（更新引用路径）

2. **E315-2: 数据库迁移未执行**
   - 问题: `tenders.0004`（添加 `is_deleted` 字段）、`bids.0003`、`core.0001`（AuditLog 模型）迁移未应用，导致 `ProgrammingError: 字段 is_deleted 不存在`
   - 修复: 执行 `python manage.py makemigrations core && python manage.py migrate`
   - 文件: 数据库迁移

**预防措施**:
1. 删除模块前必须全局搜索所有引用（包括 settings 配置），确保无遗漏
2. 代码变更后必须执行 `python manage.py showmigrations` 检查是否有未应用的迁移
3. 启动服务后应验证核心 API 端点是否正常返回

**状态**: **已完成** | 2026-04-15

---

## E314: 服务启动问题修复（Redis缺失 + FastAPI配置错误）

**错误类型**: 环境配置/依赖缺失

**修复内容**:

1. **E314-1: Redis 未安装**
   - 问题: 本机未安装 Redis 服务器，Celery 和缓存功能无法使用
   - 修复: 下载 Redis-x64-5.0.14.1.zip 到 `D:\共享文件\AUTO\redis\`，解压后启动 `redis-server.exe`
   - 文件: `D:\共享文件\AUTO\redis\redis-server.exe`（新增）

2. **E314-2: FastAPI main.py 硬编码 production 配置**
   - 问题: `fastapi_app/main.py` 第22行 `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')`，本地开发应使用 development
   - 修复: 改为 `'config.settings.development'`
   - 文件: `backend/fastapi_app/main.py`（已修改）

3. **E314-3: python-json-logger v4 路径变更**
   - 问题: `production.py` 中 `'()': 'pythonjsonlogger.jsonlogger.JsonFormatter'` 是旧版路径，v4+ 改为 `pythonjsonlogger.json.JsonFormatter`
   - 修复: 更新为 `'()': 'pythonjsonlogger.json.JsonFormatter'`
   - 文件: `backend/config/settings/production.py`（已修改）

**预防措施**:
1. 本地开发启动前确认 Redis 已运行（`D:\共享文件\AUTO\redis\redis-server.exe`）
2. FastAPI 本地开发应使用 `config.settings.development`，生产环境通过环境变量覆盖
3. `python-json-logger` 升级到 v4+ 后需更新 `production.py` 中的 formatter 路径

**状态**: **已完成** | 2026-04-15

---

## E313: 重复代码合并（响应/异常/通知/缓存装饰器）

**错误类型**: 代码重复/可维护性

**修复内容**:

1. **E313-1: 删除 core/response.py（与 utils/responses.py 重复）**
   - 问题: `core/response.py` 提供 `APIResponse/PageResponse/APIErrorCode`，0外部引用；`utils/responses.py` 提供 `UnifiedResponse`，20+引用
   - 修复: 删除 `core/response.py`。项目统一使用 `UnifiedResponse`
   - 文件: `backend/core/response.py`（已删除）

2. **E313-2: 删除 core/exceptions.py（与 common/exceptions.py 重复，有Bug）**
   - 问题: `core/exceptions.py` 从 `common.exceptions` 重新导出并添加别名 `BusinessException/ParameterException/PermissionDeniedException`，但 `from_exception()` 方法引用不存在的 `BaseServiceException`（Bug）。仅 `core/response.py` 引用它（已删除）
   - 修复: 删除 `core/exceptions.py`。项目统一使用 `common/exceptions.py` 的 `BusinessError/ValidationError/PermissionDeniedError`
   - 文件: `backend/core/exceptions.py`（已删除）

3. **E313-3: 统一通知服务（notification_service → unified_notification_service）**
   - 问题: `notification_service.py` 仅支持钉钉+邮件，被1处引用；`unified_notification_service.py` 支持钉钉+飞书+企微+邮件+Webhook，被4处引用
   - 修复: 将 `apps/notifications/views.py` 中的 `NotificationService` 替换为 `unified_notification_service`，删除旧文件
   - 变更: `NotificationService().send_notification(notification, channels)` → `unified_notification_service.send(title, content, channels)`
   - 文件: `apps/notifications/views.py`（已修改），`services/notification_service.py`（已删除）

4. **E313-4: 统一缓存装饰器（cache_it/invalidate_it → cached/invalidate_cache）**
   - 问题: `core/cache.py` 中 `cache_it()/invalidate_it()` 是兼容旧API，0外部调用；`utils/cache_manager.py` 中 `cached()/invalidate_cache()` 是正式版本，支持标签式缓存
   - 修复: 删除 `core/cache.py` 中的 `cache_it()` 和 `invalidate_it()` 函数（~72行）
   - 文件: `backend/core/cache.py`（已修改）

**删除统计**:
- 文件: 3个（core/response.py, core/exceptions.py, services/notification_service.py）
- 代码: ~500行（response.py 409行 + exceptions.py 91行 + cache装饰器 72行）

**预防措施**:
1. 禁止创建功能重复的模块（如 core/response.py 与 utils/responses.py），新增前先检查是否已有实现
2. 异常类统一在 `common/exceptions.py` 定义，禁止在其他模块创建别名或重新导出
3. 通知服务统一使用 `UnifiedNotificationService`，禁止创建新的单渠道通知服务
4. 缓存装饰器统一使用 `cached()/invalidate_cache()`，通过 `common/utils/cache.py` 统一入口

**状态**: **已完成** | 2026-04-15

---

## E312: 最大量冗余代码清理（常量/端点/重复模块）

**错误类型**: 代码冗余/可维护性

**修复内容**:

1. **E312-1: 清理 core/constants.py 未使用常量（~270行）**
   - 问题: constants.py 1493行中约40%从未被后端代码直接使用，仅通过constants_views.py暴露给前端
   - 删除的常量组:
     - `BUILDER_MAJOR_*` 单独常量值（保留CHOICES供API使用）
     - `STRUCTURE_TYPE_*` / `STRUCTURE_TYPE_CHOICES`（~21行，bid_config用JSONField）
     - `CERTIFICATION_*` / `CERTIFICATION_CHOICES`（~13行，无对应模型）
     - `ENTERPRISE_QUAL_TYPE_*` / `ENTERPRISE_QUAL_TYPE_CHOICES`（~17行，无对应模型字段）
     - `SEARCH_RULE_TYPE_*` / `SEARCH_TASK_STATUS_*`（~26行，无对应模型）
     - `INDUSTRY_CATEGORY_*` / `INDUSTRY_SUBCATEGORY_CHOICES`（~200行，无对应模型）
     - `SEARCH_OPERATOR_*` / `PROJECT_TYPE_*`（~24行，无对应模型）
   - 保留: `BUILDER_MAJOR_CHOICES`（仅CHOICES列表，供constants_views.py API使用）
   - 文件: `backend/core/constants.py`

2. **E312-2: 清理 tenders/urls.py 前端未调用端点（14→7个端点）**
   - 删除: sources/, files/, crawler/tasks/, crawler/notice-types/, crawler/execute/, crawler/sync-execute/, sync/, proxy/, read/
   - 保留: project_list, project_detail, project_favorite, project_batch, keyword_list, keyword_detail, statistics
   - 文件: `backend/apps/tenders/urls.py`

3. **E312-3: 清理 crawler/urls.py 前端未调用端点（11→4个端点）**
   - 删除: results/, logs/, recognition-rules/, recognized/, qualification-match/, validate/, validations/, collection/, workflow/
   - 保留: templates/, sessions/, schedules/, schedule-logs/
   - 文件: `backend/apps/crawler/urls.py`

4. **E312-4: 清理其他模块前端未调用端点**
   - openclaw: 删除 scheduler/, one-click/enterprise/, websites/, error-knowledge/, optimizer/（与scheduler app重复或未使用）
   - users: 删除 token/refresh/body/（前端用CookieTokenRefreshView）、me/profile/（前端用/auth/me/）、change-password/（无前端功能）
   - bids: 删除 results/<pk>/（前端只有列表）、dashboard/（无前端页面）
   - documents: 删除 generated/<pk>/ai-suggestion/（前端未调用）
   - config: 删除 scheduler/ 注册（与crawler/schedules重复）、validation-rules/ 端点（前端未调用）
   - 文件: `apps/openclaw/urls.py`, `apps/users/urls.py`, `apps/bids/urls.py`, `apps/documents/urls.py`, `config/urls.py`

5. **E312-5: 删除 services/agent/ 目录（与openclaw/功能完全重复）**
   - 删除: `services/agent/__init__.py`, `dispatcher.py`, `message_bus.py`, `skill_registry.py`
   - 原因: 0外部引用，所有功能已被openclaw/模块替代（AgentRouter替代AgentDispatcher，SkillRegistry替代旧版，AgentMessage替代ProtocolMessage）
   - 同时删除: `services/sync/__init__.py`（0外部引用，SyncManager无消费者）
   - 更新: `services/__init__.py` 移除agent和sync的导入
   - 文件: `backend/services/agent/`, `backend/services/sync/`, `backend/services/__init__.py`

**删除统计**:
- 常量代码: ~270行
- API端点: 30+个 → 7个模块共减少约30个端点
- 重复模块: services/agent/(4文件) + services/sync/(1文件) = 5文件

**预防措施**:
1. 新增常量必须有对应模型字段或明确的使用场景，禁止"预留"常量
2. 新增API端点必须同步前端调用代码，避免"后端先行"导致的死端点
3. 功能模块统一到一个实现，禁止在services/和openclaw/中各维护一份

**状态**: **已完成** | 2026-04-15

---

## E311: 代码错误文件清理（路径错误/端口错误/引用不存在/导入Bug）

**错误类型**: 代码错误/运行时崩溃

**修复内容**:

1. **E311-1: 删除 run_backend.py**
   - 问题: 路径硬编码为 `d:\shared\AUTO\backend`，实际路径为 `d:\共享文件\AUTO\backend`，运行必失败；且与 `start_all_services.bat` 功能重复
   - 修复: 删除文件。本地开发使用 `start_all_services.bat`
   - 文件: `run_backend.py`（已删除）

2. **E311-2: 删除 run_fastapi.py**
   - 问题: 端口错误（8002，实际应为8001）；硬编码数据库密码 `123456`；与 `start_fastapi.bat` 功能重复
   - 修复: 删除文件。本地开发使用 `start_fastapi.bat`
   - 文件: `run_fastapi.py`（已删除）

3. **E311-3: 删除 _check.bat**
   - 问题: 引用不存在的 `check_all_services.py`，运行必失败
   - 修复: 删除文件。健康检查通过 `run_health_check.py` 或 `/health/` API 端点执行
   - 文件: `_check.bat`（已删除）

4. **E311-4: 删除 services/agent/protocol.py**
   - 问题: 第38行 `from core.exceptions import ExternalServiceException` 导入不存在的类，运行时 ImportError；且0引用，与 `openclaw/messaging/protocol.py`（3引用）功能重复
   - 修复: 删除文件。消息协议统一使用 `openclaw/messaging/protocol.py`（AgentRouter + AgentMessage）
   - 文件: `backend/services/agent/protocol.py`（已删除）

**预防措施**:
1. 启动脚本路径必须与实际项目路径一致，优先使用相对路径或环境变量
2. 服务端口必须与 settings/docker-compose.yml 中的配置一致
3. 脚本引用的文件必须存在，提交前应验证可执行
4. import 的类必须在目标模块中存在，IDE类型检查可提前发现
5. 重复功能模块应统一到一个实现，避免维护多份代码

**状态**: **已完成** | 2026-04-15

---

## E310: 安全隐患文件清理（硬编码密码/凭证泄露）

**错误类型**: 安全/凭证泄露

**修复内容**:

1. **E310-1: 删除 start_backend_remote_db.bat**
   - 问题: 硬编码远程数据库IP `8.132.127.16` 和密码 `123456`，提交到版本库会导致凭证泄露
   - 修复: 删除文件。如需连接远程数据库，应通过 `.env` 文件配置，不提交到版本库
   - 文件: `start_backend_remote_db.bat`（已删除）

2. **E310-2: 删除 start_django_local.bat**
   - 问题: 硬编码数据库密码 `set DB_PASSWORD=123456`
   - 修复: 删除文件。本地开发应使用 `start_all_services.bat`，密码通过 `.env` 文件配置
   - 文件: `start_django_local.bat`（已删除）

3. **E310-3: 删除 run_backend_db.py**
   - 问题: 硬编码数据库密码 `os.environ['DB_PASSWORD'] = '123456'`
   - 修复: 删除文件。与 `start_django_local.bat` 功能重复
   - 文件: `run_backend_db.py`（已删除）

4. **E310-4: 删除 backend/clear_output.txt**
   - 问题: 临时输出文件，包含 MinIO 凭证警告信息和数据库清空操作日志
   - 修复: 删除文件。临时输出不应提交到版本库
   - 文件: `backend/clear_output.txt`（已删除）

**预防措施**:
1. 禁止在脚本文件中硬编码密码、IP等敏感信息，统一使用 `.env` 文件
2. 临时输出文件（如 `*.txt` 日志）不应提交到版本库，应添加到 `.gitignore`
3. 数据库连接配置应通过环境变量传入，而非在脚本中 `set` 或 `os.environ` 硬编码
4. 本地开发统一使用 `start_all_services.bat`，避免维护多个启动脚本

**状态**: **已完成** | 2026-04-15

---

## E309: P3架构审查低优先级问题修复（5项）

**错误类型**: 代码质量/可维护性

**修复内容**:

1. **E309-1: 前端API错误处理标准化**
   - 问题: `request.js` 响应拦截器中 400/403/404/500 等状态码的错误处理逻辑重复冗长（约100行if-else），且不兼容 UnifiedResponse 格式
   - 修复: 提取 `extractErrorMessage()` 和 `formatFieldErrors()` 函数，使用 `HTTP_ERROR_MAP` 映射表替代 if-else 链，兼容 UnifiedResponse `{code, message, data}` 和 DRF 原生 `{detail, errors}` 格式
   - 文件: `frontend/src/utils/request.js`

2. **E309-2: 限流监控指标添加**
   - 问题: 限流触发时无事件记录和统计，无法监控异常流量
   - 修复: 添加 `_record_throttle_event()` 记录限流事件到 Redis，添加 `get_throttle_stats()` 查询限流统计，LoginRateThrottle 添加 `throttle_failure` 钩子
   - 文件: `backend/core/throttling.py`

3. **E309-3: 常量集中管理确认**
   - 问题: 架构审查建议提取 magic numbers/strings
   - 确认: `core/constants.py` 已包含 1493 行完整常量定义，覆盖所有业务枚举和状态码，无需额外提取
   - 文件: `backend/core/constants.py`（无需修改）

4. **E309-4: 数据库连接池监控完善**
   - 问题: `setup_connection_pool()` 中 `results[1][1]` 索引错误（应为 `results[1][0]`），且缺少连接健康检查函数
   - 修复: 改用 `NAME, SETTING` 双列查询 + 字典映射，新增 `check_connection_health()` 函数检查各数据库连接状态
   - 文件: `backend/utils/db_optimizer.py`

5. **E309-5: Docker日志驱动配置**
   - 问题: 容器日志无大小限制，长期运行会占满磁盘
   - 修复: 添加 `x-logging` YAML 锚点，配置 json-file 驱动（max-size=50m, max-file=5），应用到 backend/fastapi/celery-worker/celery-beat/gateway 服务
   - 文件: `docker-compose.yml`

**预防措施**:
1. 前端错误处理应使用映射表模式，避免冗长的 if-else 链
2. 限流组件必须记录触发事件，便于安全审计和流量分析
3. 数据库查询结果应使用字典映射而非位置索引
4. Docker 容器必须配置日志轮转，防止磁盘溢出

**相关文件**:
- `frontend/src/utils/request.js`
- `backend/core/throttling.py`
- `backend/utils/db_optimizer.py`
- `docker-compose.yml`

**状态**: **已完成** | 2026-04-15

---

## E308: P2架构审查中等问题修复（6项）

**错误类型**: 安全/逻辑缺陷

**修复内容**:

1. **E308-1: 前端404路由重定向到登录页**
   - 问题: 路由中 `/:pathMatch(.*)*` 重定向到 `/login`，用户访问不存在的页面会被强制跳转到登录页，体验差且掩盖了404错误
   - 修复: 创建 `NotFound.vue` 404页面组件，路由直接渲染该组件而非重定向
   - 文件: `frontend/src/views/NotFound.vue`（新建），`frontend/src/router/index.js`

2. **E308-2: isAdmin判断逻辑脆弱**
   - 问题: `user.js` 使用 `role === 'admin'` 判断管理员，但后端RBAC模型使用 `is_staff`/`is_superuser` 字段
   - 修复: 改为 `userInfo.value?.is_staff || userInfo.value?.is_superuser`
   - 文件: `frontend/src/store/user.js`

3. **E308-3: ConcurrentRequestThrottle竞态条件**
   - 问题: `acquire()` 中 `cache.incr()` 后又执行 `cache.set(key, cache.get(key, 1), 60)`，导致incr结果被覆盖；`__init__` 中的 `_current_requests` 在多进程下无效
   - 修复: 移除冗余的 `cache.set` 调用，移除无用的 `_current_requests` 实例变量，`release()` 中使用 `cache.decr` 原子操作
   - 文件: `backend/core/throttling.py`

4. **E308-4: AuditLog模型依赖不存在**
   - 问题: `utils/audit_logger.py` 导入 `from apps.core.models import AuditLog`，但 `apps/core/` 目录下没有 models.py，导致运行时 ImportError
   - 修复: 在 `core/models.py` 中创建 AuditLog 模型，修改 audit_logger.py 导入为 `from core.models import AuditLog`
   - 文件: `backend/core/models.py`（新建），`backend/utils/audit_logger.py`
   - 注意: 需要执行 `python manage.py makemigrations core` 和 `python manage.py migrate`

5. **E308-5: IsEnterpriseOwner权限过严**
   - 问题: `has_permission()` 对非管理员返回 `False`，导致普通企业用户无法访问 list/create 等视图
   - 修复: `has_permission()` 仅检查认证状态，对象级权限由 `has_object_permission()` 控制
   - 文件: `backend/utils/permissions/enterprise.py`

6. **E308-6: 健康检查SSL验证禁用**
   - 问题: 健康检查使用 `ssl.CERT_NONE` 禁用证书验证，Milvus/MinIO 健康检查使用 HTTP 协议，不需要 SSL context
   - 修复: 移除所有 `ssl.create_default_context()` 和 `context=ctx` 参数，移除 `import ssl`
   - 文件: `backend/config/urls.py`

**预防措施**:
1. 前端路由必须有正确的404处理，不应重定向到登录页
2. 管理员判断应基于 Django 的 `is_staff`/`is_superuser` 字段，而非自定义 role 字符串
3. 分布式限流必须使用 Redis 原子操作，避免 read-modify-write 竞态
4. 新增模型必须确保导入路径正确，且已执行迁移
5. 权限类的 `has_permission` 应做粗粒度检查，`has_object_permission` 做细粒度检查
6. HTTP 请求不需要 SSL context，仅在 HTTPS 时配置

**相关文件**:
- `frontend/src/views/NotFound.vue`
- `frontend/src/router/index.js`
- `frontend/src/store/user.js`
- `backend/core/throttling.py`
- `backend/core/models.py`
- `backend/utils/audit_logger.py`
- `backend/utils/permissions/enterprise.py`
- `backend/config/urls.py`

**状态**: **已完成** | 2026-04-15

---

## E307: P1架构审查重要问题修复（7项）

**错误类型**: 架构缺陷/配置问题

**修复内容**:

1. **E307-1: TraceIdFilter读取源Bug**
   - 问题: `TraceIdFilter.filter()` 从 `settings.TRACE_ID` 读取追踪ID，但 `TraceIdMiddleware` 将trace_id存储在 `_thread_local.request.trace_id`，导致日志中trace_id始终为'-'
   - 修复: 改为从 `core.middleware._thread_local.request.trace_id` 读取
   - 文件: `backend/core/logging_config.py`

2. **E307-2: DEFAULT_PASSWORD弱密码**
   - 问题: `DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD', 'tianqi123456')` 硬编码弱密码作为默认值
   - 修复: 默认值改为空字符串，仅开发环境使用临时密码 `Dev@2026changeme`，生产环境必须通过环境变量设置
   - 文件: `backend/config/settings/base.py`

3. **E307-3: 双Nginx配置冲突**
   - 问题: `frontend/nginx.conf` 自带 `/api/` 代理到backend，与 `docker/nginx/gateway.conf` 的API网关角色冲突
   - 修复: 移除 `frontend/nginx.conf` 中的 `upstream backend`、`/api/`、`/health/` 代理配置，仅保留前端静态文件服务
   - 文件: `frontend/nginx.conf`

4. **E307-4: 冗余docker-compose-milvus.yml**
   - 问题: `docker-compose-milvus.yml` 与统一 `docker-compose.yml` 中的etcd/minio/milvus服务重复，且容器名冲突
   - 修复: 删除 `docker-compose-milvus.yml`，统一使用 `docker-compose.yml`
   - 文件: `docker-compose-milvus.yml`（已删除）

5. **E307-5: FastAPI缺少专用Dockerfile**
   - 问题: fastapi服务与backend共用Dockerfile，导致不必要的 `collectstatic` 和OCR依赖安装
   - 修复: 新建 `backend/Dockerfile.fastapi`，精简依赖（移除OCR/Tesseract），移除collectstatic，CMD直接启动uvicorn
   - 文件: `backend/Dockerfile.fastapi`（新建），`docker-compose.yml`（更新dockerfile引用）

6. **E307-6: requirements.txt未分组**
   - 问题: 52个依赖包无分组注释，难以维护和审查
   - 修复: 按11个功能分组（Django核心、ASGI/WSGI、数据库、Celery、FastAPI、爬虫、向量/嵌入、文档处理、云服务SDK、安全/加密、可观测性、开发/调试）
   - 文件: `backend/requirements.txt`

7. **E307-7: Celery Worker队列配置不匹配**
   - 问题: docker-compose中celery-worker监听 `default,crawl,analyze,notify`，但celery.py定义了 `default,notification,workflow,crawler,vector` 5个队列，名称和数量都不匹配
   - 修复: 更新docker-compose中worker的-Q参数为 `default,notification,workflow,crawler,vector`
   - 文件: `docker-compose.yml`

**预防措施**:
1. 日志Filter必须与Middleware使用相同的上下文存储机制
2. 禁止在代码中硬编码密码，默认值应为空
3. Nginx配置应遵循单一职责：frontend仅服务静态文件，gateway负责API路由
4. docker-compose文件应保持唯一，避免多文件导致配置冲突
5. Celery队列名在celery.py和docker-compose中必须完全一致

**相关文件**:
- `backend/core/logging_config.py`
- `backend/config/settings/base.py`
- `frontend/nginx.conf`
- `backend/Dockerfile.fastapi`
- `backend/requirements.txt`
- `docker-compose.yml`

**状态**: **已完成** | 2026-04-15

---

## E306: P0架构审查严重问题修复（3项）

**错误类型**: 架构缺陷/严重问题

**修复内容**:

1. **E306-1: 统一API响应格式**
   - 问题: 项目存在4套响应格式系统（UnifiedResponse、APIResponse别名、response_helpers、raw DRF Response），前端无法统一处理
   - 修复:
     - `enterprise/views.py`: 废弃 `response_helpers` 模块（success_response/error_response/not_found_response/validation_error_response等），全部改用 `UnifiedResponse`
     - `enterprise/views.py`: 所有 raw `Response(serializer.data)` 改为 `UnifiedResponse.success(data=serializer.data)`
     - `enterprise/views.py`: 所有 raw `Response({...})` 改为对应的 `UnifiedResponse.success/error/not_found/validation_error/server_error`
     - `monitor/views.py`: 所有 raw `Response({...})` 改为 `UnifiedResponse` 系列方法
     - 移除两个文件中不再使用的 `from rest_framework.response import Response` 导入
   - 注意: `APIResponse = UnifiedResponse`（responses.py第272行），tenders/bids/users模块已通过别名使用UnifiedResponse，无需修改
   - 文件: `backend/apps/enterprise/views.py`, `backend/apps/monitor/views.py`

2. **E306-2: 修复wsgi.py默认配置**
   - 问题: `config/wsgi.py` 使用 `config.settings` 作为默认配置，而非 `config.settings.production`，导致生产环境WSGI可能加载开发配置
   - 修复: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')` → `'config.settings.production'`
   - 对比: `config/asgi.py` 已正确使用 `config.settings.production`
   - 文件: `backend/config/wsgi.py`

3. **E306-3: 补充tenders/urls.py缺失路由**
   - 问题: `apps/tenders/views.py` 定义了10+个View类，但 `urls.py` 只注册了9个，导致大量API端点不可访问
   - 修复: 新增以下路由注册:
     - `sources/` → TenderSourceListView (招标来源列表)
     - `sources/<int:pk>/` → TenderSourceDetailView (招标来源详情)
     - `files/` → TenderFileListView (招标文件列表)
     - `files/<int:pk>/` → TenderFileDetailView (招标文件详情)
     - `crawler/tasks/` → CrawlerTaskListView (爬虫任务列表)
     - `crawler/tasks/<int:pk>/` → CrawlerTaskDetailView (爬虫任务详情)
     - `crawler/tasks/<int:pk>/execute/` → CrawlerTaskExecuteView (执行爬虫任务)
     - `crawler/notice-types/` → CrawlerNoticeTypesView (公告类型)
     - `crawler/execute/` → CrawlerExecuteView (执行爬虫)
     - `crawler/sync-execute/` → CrawlerSyncExecuteView (同步执行爬虫)
     - `proxy/` → TenderProxyView (代理访问)
   - 文件: `backend/apps/tenders/urls.py`

**预防措施**:
1. 新增视图必须同步更新urls.py，CI中可添加检测脚本
2. 所有API视图必须使用UnifiedResponse，禁止直接使用DRF Response
3. wsgi.py/asgi.py配置必须指向production settings
4. response_helpers.py模块已废弃，可考虑后续删除

**相关文件**:
- `backend/apps/enterprise/views.py`
- `backend/apps/monitor/views.py`
- `backend/config/wsgi.py`
- `backend/apps/tenders/urls.py`

**状态**: **已完成** | 2026-04-15

---

## E305: OpenClaw四大增强功能（借鉴Hermes设计理念）

**错误类型**: 功能增强/架构优化

**修复内容**:

1. **E305-1: 标书质量反馈学习系统**
   - 问题: 标书审核不通过或投标被拒时，经验教训无法积累复用，同类错误反复出现
   - 修复: 实现Hermes式自学习闭环（执行→评估→提取经验→更新策略→复用）
     - 新增 `BidFeedbackLearner` 反馈学习器，自动从审核/投标结果中提取优化规则
     - 新增 `BidFeedbackRecord` 模型记录每次反馈数据
     - 新增 `GenerationStrategy` 模型存储自动提取的生成策略
     - 新增 `StrategyLearningLog` 模型记录学习过程
     - `BidDocumentGeneratorAgent` 生成标书时自动注入历史经验提示
     - `BidDocumentReviewerAgent` 审核后自动记录反馈
   - 文件: `backend/openclaw/feedback_learning.py`(新建), `backend/apps/openclaw/feedback_models.py`(新建), `backend/openclaw/agents/bid_document_agents.py`(修改)

2. **E305-2: Agent记忆跨会话持久化**
   - 问题: Agent记忆仅存于进程内存，进程重启即丢失，无法积累企业投标历史经验
   - 修复: 实现三层记忆架构（L1内存→L2 ORM持久化→L3企业经验库）
     - 新增 `PersistentMemoryService` 持久化记忆服务
     - 新增 `AgentMemoryStore` 模型支持按agent_type+scope+key维度持久化
     - 新增 `EnterpriseBidExperience` 模型积累企业投标经验
     - `BaseAgent.add_memory()` 自动持久化到数据库
     - `BaseAgent.get_memory()` 先查内存再查持久化
     - 支持记忆过期清理、企业经验上下文注入
   - 文件: `backend/openclaw/persistent_memory.py`(新建), `backend/apps/openclaw/memory_models.py`(新建), `backend/openclaw/base_agent.py`(修改)

3. **E305-3: 通知渠道扩展到飞书/企微**
   - 问题: 通知仅支持钉钉单渠道，无法满足多平台办公需求
   - 修复: 实现统一通知服务，支持钉钉/飞书/企微/邮件/短信/Webhook六渠道
     - 新增 `FeishuNotificationService` 飞书通知服务（支持签名验证、Markdown卡片）
     - 新增 `WeComNotificationService` 企业微信通知服务（支持文本/Markdown/图文/文件）
     - 新增 `UnifiedNotificationService` 统一通知服务（多渠道同步推送）
     - `NotificationSkill` 升级v2.0，支持 `channel=all` 多渠道同步
     - `BidWorkflowOrchestrator` 故障通知改用统一通知服务
     - `NotificationConfig` 新增 `FEISHU_ENABLED`/`WECOM_ENABLED`/`MULTI_CHANNEL_ENABLED` 字段
     - settings 新增 `FEISHU_WEBHOOK_URL`/`FEISHU_SECRET`/`WECOM_WEBHOOK_URL` 配置
   - 文件: `backend/services/unified_notification_service.py`(新建), `backend/openclaw/skills/uploader/file_uploader.py`(修改), `backend/openclaw/agents/bid_workflow_orchestrator.py`(修改), `backend/config/settings/base.py`(修改), `backend/apps/openclaw/models.py`(修改)

4. **E305-4: SupervisorAgent重构为Coordinator/Worker模式**
   - 问题: 原SupervisorAgent是简单的顺序调度器，缺乏角色分工、并行执行、进度追踪能力
   - 修复: 借鉴Hermes的Coordinator/Worker架构重构
     - 新增 `WorkerAgent` 基类：执行具体任务，通过 `report_to_coordinator()` 主动汇报
     - 新增 `CoordinatorAgent`：任务分解→Worker分配→并行/顺序执行→结果综合
     - 支持并行执行（同parallel_group的步骤并行）
     - 内置进度追踪 `get_progress()`
     - `SupervisorAgent` 继承 `CoordinatorAgent` 保持向后兼容
     - `agents/__init__.py` 导出新增类
   - 文件: `backend/openclaw/agents/professional_agents.py`(重构), `backend/openclaw/agents/__init__.py`(修改)

5. **附带修复: 两个预存Bug**
   - `common/views/base.py` 缺少 `from rest_framework.decorators import action` 导入
   - `apps/openclaw/views.py` 缺少 `LLMUsageLogSerializer` 导入

**预防措施**:
1. 反馈学习系统应在每次标书审核后自动触发，无需人工干预
2. 持久化记忆失败不应影响Agent正常执行（已做异常隔离）
3. 飞书/企微Webhook未配置时自动跳过，不影响其他渠道
4. Coordinator/Worker模式向后兼容，旧代码无需修改

**相关文件**:
- `backend/openclaw/feedback_learning.py`
- `backend/openclaw/persistent_memory.py`
- `backend/services/unified_notification_service.py`
- `backend/apps/openclaw/feedback_models.py`
- `backend/apps/openclaw/memory_models.py`
- `backend/openclaw/agents/professional_agents.py`
- `backend/openclaw/agents/bid_document_agents.py`
- `backend/openclaw/base_agent.py`
- `backend/openclaw/skills/uploader/file_uploader.py`
- `backend/openclaw/agents/bid_workflow_orchestrator.py`
- `backend/config/settings/base.py`

**状态**: **已完成** | 2026-04-10

---

## E304: 架构审查P4扩展性设计问题修复（7项）

**错误类型**: 扩展性/架构设计/基础设施

**修复内容**:

1. **E304-1: .env.example配置文件不统一**
   - 问题: 根目录`.env.example`有105行完整配置，`backend/.env.example`仅35行且缺少大量配置项（DB从库、Redis集群、Celery、Milvus、OpenClaw、OTEL等），部分默认值不一致（DB_USER=postgres vs bid_user，MINIO_BUCKET_NAME=bid-auto vs bid-documents）
   - 修复: 合并为根目录统一配置文件，删除`backend/.env.example`；`load_dotenv()`改为先加载项目根目录`.env`再加载`backend/.env`，override=False确保不覆盖已设值
   - 文件: `.env.example`(重写), `backend/.env.example`(删除), `backend/config/settings/base.py`

2. **E304-2: 缺少RBAC角色权限模型**
   - 问题: 用户模型仅有admin/user二元角色字段，无法实现细粒度权限控制（如投标经理可创建投标但不可删除、商务专员可导出企业但不可管理等）
   - 修复: 添加4个RBAC模型：Role（角色表，含code/is_system/sort_order）、Permission（权限表，resource+action组合唯一）、UserRole（用户-角色关联，含granted_by授权人）、RolePermission（角色-权限关联）；User模型添加`get_roles()`、`get_permissions()`、`has_resource_permission(resource, action)`方法；新增`RBACPermission` DRF权限类（通过view的`rbac_resource`属性匹配）；新增`init_rbac`管理命令初始化5个默认角色和34个默认权限
   - 文件: `backend/apps/users/models.py`, `backend/apps/users/serializers.py`, `backend/utils/permissions/base.py`, `backend/apps/users/management/commands/init_rbac.py`(新建)

3. **E304-3: 事件总线缺少同步发布和Celery集成**
   - 问题: `core/events.py`中EventBus所有处理器都是async，Django视图/ORM是同步的无法直接使用；缺少Celery集成导致长时间事件处理阻塞请求；缺少事件持久化导致进程重启后事件丢失；中间件链实现有bug（所有中间件并行执行而非链式调用）
   - 修复: 添加`SyncEventHandler`基类和`subscribe_sync`/`publish_sync`方法支持同步处理器；添加`domain_handler`装饰器注册同步处理器；添加`DomainEvent`事件基类；添加`dispatch_celery`方法将事件分发到Celery任务队列；添加`_persist_event`函数将事件写入`event_store`表；修复中间件链为正确的递归链式调用；添加`to_json`方法便于序列化
   - 文件: `backend/core/events.py`

4. **E304-4: CrawlResult与TenderProject缺少关联**
   - 问题: CrawlResult和TenderProject字段高度相似（title/source_url/publish_date/budget/purchaser/agency等），但无外键关联，无法追踪"采集结果→正式招标项目"的转化关系
   - 修复: CrawlResult添加`tender_project` FK指向TenderProject（SET_NULL，nullable）；添加`convert_to_tender(user)`方法实现一键转化：自动创建TenderProject并回填FK，状态改为converted
   - 文件: `backend/apps/crawler/models.py`

5. **E304-5: 自建可观测性缺少OpenTelemetry集成**
   - 问题: `utils/observability.py`是纯内存自建方案，无法与行业标准可观测性工具（Jaeger/Zipkin/Prometheus/Grafana）集成；注释中提到OpenTelemetry但实际未实现
   - 修复: 添加`setup_otel()`函数初始化OTEL SDK（TracerProvider+MeterProvider+OTLP gRPC导出器）；`trace`装饰器增强：OTEL可用时同时创建OTEL span，记录status/error/exception；添加`otel_span`上下文管理器供手动创建OTEL span；`setup_observability`在OTEL_ENABLED=True时自动调用`setup_otel`；OTEL不可用时优雅降级到自建方案；添加OTEL依赖到requirements.txt
   - 文件: `backend/utils/observability.py`, `backend/requirements.txt`

6. **E304-6: 缺少统一Docker Compose编排**
   - 问题: 项目仅有`docker-compose-milvus.yml`（3个Milvus服务），缺少主应用编排（PostgreSQL/Redis/Django/FastAPI/Celery/Frontend/Nginx Gateway），部署需手动启动各服务
   - 修复: 创建统一`docker-compose.yml`，包含11个服务：postgres、redis、etcd、minio、milvus、backend、fastapi、celery-worker、celery-beat、frontend、gateway；所有服务配置healthcheck和restart策略；环境变量统一从`.env`文件读取；服务间依赖通过condition: service_healthy确保启动顺序
   - 文件: `docker-compose.yml`(新建)

7. **E304-7: 缺少API版本管理机制**
   - 问题: 当前API路径为`/api/v1/`，但无版本管理中间件，未来升级v2时无法平滑过渡，客户端无法通过Header指定版本
   - 修复: 添加`ApiVersionMiddleware`，支持两种版本指定方式：URL路径`/api/v1/`和Accept Header `application/vnd.bid-auto.v1+json`；request对象注入`api_version`属性；响应头添加`X-API-Version`；定义`SUPPORTED_VERSIONS`和`CURRENT_API_VERSION`常量便于扩展
   - 文件: `backend/core/middleware.py`, `backend/config/settings/base.py`

**预防措施**:
1. 环境配置文件应统一管理，避免多处维护导致不一致
2. 权限系统应从项目初期就设计RBAC模型，避免后期改造困难
3. 事件总线应同时支持同步/异步处理器，Django ORM场景必须使用同步模式
4. 有转化关系的数据模型应建立FK关联，避免数据孤岛
5. 可观测性应优先集成行业标准（OpenTelemetry），自建方案仅作降级备选
6. Docker Compose应统一编排所有服务，避免手动逐个启动
7. API版本管理应在项目初期就建立机制，避免后期升级困难

**状态**: **已修复** | 2026-04-15

---

## E303: 架构审查P3低优先级问题修复（9项）

**错误类型**: 正确性/代码质量/安全加固

**修复内容**:

1. **E303-1: SingletonModel.save()单例检查逻辑有误**
   - 问题: `self.pk is None`时检查`filter(pk=self.pk)`永远为空，新对象无法被拦截
   - 修复: 改为先检查表中是否有记录，再判断当前对象是否是已有记录
   - 文件: `backend/common/models/base.py`

2. **E303-2: UserTrackMixin.save()无法获取request**
   - 问题: Django ORM的save()不接受request参数，created_by/updated_by基本不会自动设置
   - 修复: 添加_thread_local线程本地存储，TraceIdMiddleware在process_request中存储request，UserTrackMixin从_thread_local读取；同时简化逻辑：创建时设created_by，更新时总设updated_by
   - 文件: `backend/common/models/mixins.py`, `backend/core/middleware.py`

3. **E303-3: BidStatistics.year默认值模块加载时求值+缺unique_together**
   - 问题: `default=timezone.now().year`在模块加载时求值，非运行时；缺少unique_together约束可能产生重复统计
   - 修复: 移除default（调用方必须显式传入year）；添加`unique_together = [['user', 'year', 'month']]`
   - 文件: `backend/apps/bids/models.py`

4. **E303-4: urls.py中_services_cache重复定义+import缺失**
   - 问题: _services_cache在第20行和第137行定义两次；health_check中使用os.getenv但未导入os；函数内重复import ssl/socket
   - 修复: 移除重复定义；顶部添加import os/re/socket/ssl；移除函数内重复import
   - 文件: `backend/config/urls.py`

5. **E303-5: sensitive_config默认密码检查可绕过**
   - 问题: `minio_access_key == 'minioadmin' and not os.getenv('MINIO_ACCESS_KEY')`中，如果环境变量设置为minioadmin，os.getenv返回非空，检查被绕过
   - 修复: 引入WEAK_PASSWORDS集合，直接检查值是否在集合中；添加ACCESS_KEY与SECRET_KEY不能相同的检查；添加DJANGO_SECRET_KEY弱值检查
   - 文件: `backend/utils/sensitive_config.py`

6. **E303-6: address脱敏规则未实现**
   - 问题: SENSITIVE_FIELDS_CONFIG中有address配置(type='address')，但SensitiveFieldMasker无mask_address方法，走默认路径返回原值
   - 修复: 添加mask_address方法（保留前6后4字符）；在mask方法中添加address类型处理
   - 文件: `backend/core/sensitive_mask.py`

7. **E303-7: content_moderation误报率高**
   - 问题: 日期模式`\d{4}[-/]\d{2}[-/]\d{2}`和长数字序列`\d{6,}`在招标文档中大量误报；SQL检测`'select' in text.lower() and 'from' in text.lower()`几乎所有英文文本都匹配
   - 修复: 移除日期和长数字序列模式（招标场景正常）；身份证正则改为精确匹配18位`(?<!\d)\d{17}[\dXx](?!\d)`；手机号添加后向否定`(?!\d)`；SQL检测改为完整语句模式匹配
   - 文件: `backend/utils/content_moderation.py`

8. **E303-8: SoftDeleteViewSet.restore未实现**
   - 问题: restore方法返回"暂未实现"错误
   - 修复: 实现restore功能：检查is_deleted状态，恢复为False并清除deleted_at
   - 文件: `backend/common/views/base.py`

9. **E303-9: 演示页面路由已移除**
   - 问题: /system/multi-view-demo演示页面不应出现在生产路由中
   - 修复: 在P0-8重写路由时已移除
   - 文件: `frontend/src/router/index.js`

**预防措施**:
1. 单例模型save()必须正确检查已有记录
2. ORM自动填充用户字段应使用线程本地存储而非依赖save()参数
3. 模型字段默认值不能使用函数调用的结果（如timezone.now().year），应使用callable
4. 模块级变量和import不应重复定义
5. 密码检查应直接检查值，而非同时检查环境变量是否存在
6. 脱敏规则配置必须与实现方法一一对应
7. 正则模式应考虑业务场景，避免大量误报
8. 声明的功能必须实现，未实现的应标记为@action并抛出NotImplementedError

**状态**: **已修复** | 2026-04-10

---

## E302: 架构审查P2中优先级问题修复（9项）

**错误类型**: 安全/性能/代码质量/基础设施

**修复内容**:

1. **E302-1: IsOwnerOrAdmin缺has_permission权限漏洞**
   - 问题: 仅实现has_object_permission，列表视图（无对象上下文）时权限检查不完整
   - 修复: 添加has_permission方法，已认证用户通过后由has_object_permission做对象级校验
   - 文件: `backend/utils/permissions/base.py`

2. **E302-2: EncryptedFieldMixin解密失败静默吞没**
   - 问题: from_db_value和to_python中解密失败pass，可能返回加密密文而不报错
   - 修复: 解密失败时记录warning日志并返回原始值，而非静默吞没
   - 文件: `backend/utils/crypto.py`

3. **E302-3: AES-CBC升级AES-GCM**
   - 问题: AES-CBC不提供完整性校验，加密数据可被篡改而不被发现
   - 修复: 新数据使用AES-256-GCM加密（同时提供加密和认证）；保留decrypt_cbc兼容旧数据；添加decrypt_auto自动检测模式
   - 文件: `backend/utils/crypto.py`

4. **E302-4: 脱敏逻辑统一**
   - 问题: crypto.py/sensitive_mask.py/content_moderation.py三处脱敏逻辑重复且规则不一致
   - 修复: crypto.py的mask_sensitive_data委托给core/sensitive_mask.py；content_moderation.py的sanitize_text简化
   - 文件: `backend/utils/crypto.py`, `backend/utils/content_moderation.py`

5. **E302-5: N+1查询修复(enterprise)**
   - 问题: semantic_match中逐个Enterprise.objects.get查询企业信息
   - 修复: 改用filter(id__in=...)+字典映射，单次查询替代N次查询
   - 文件: `backend/apps/enterprise/views.py`

6. **E302-6: 验证器重复定义消除**
   - 问题: users/serializers.py和common/serializers/validators.py都有validate_phone
   - 修复: users/serializers.py的validate_phone委托给common/serializers/validators.py
   - 文件: `backend/apps/users/serializers.py`

7. **E302-7: 后端Dockerfile多阶段构建**
   - 问题: 单阶段构建，build-essential和libpq-dev留在最终镜像中，体积过大
   - 修复: 采用builder+runtime两阶段构建，运行时镜像仅含必要依赖
   - 文件: `backend/Dockerfile`

8. **E302-8: Docker Compose优化**
   - 问题: 所有服务无restart策略；MinIO使用latest标签；etcd advertise-client-urls使用127.0.0.1；MinIO端口未暴露
   - 修复: 添加restart: unless-stopped；MinIO固定版本RELEASE.2024-01-31；etcd广播地址改为etcd:2379；暴露MinIO控制台9001端口
   - 文件: `docker-compose-milvus.yml`

9. **E302-9: 前端代码质量优化**
   - 问题: App.vue和main.js重复设置ElementPlus locale；ResizeObserver错误处理分散在3处；Layout.vue缺少SwitchButton/Expand/Fold图标注册；API导出冗余注释
   - 修复: 移除App.vue的el-config-provider（main.js已设置）；统一isResizeObserverError函数；注册缺失图标；精简API导出注释
   - 文件: `frontend/src/App.vue`, `frontend/src/main.js`, `frontend/src/api/index.js`

**预防措施**:
1. 权限类必须同时实现has_permission和has_object_permission
2. 加密算法优先选择AEAD模式（GCM/CCM），避免使用无认证的CBC模式
3. 数据库查询避免在循环中使用get()，改用filter(id__in=...)+字典映射
4. 公共验证逻辑统一到common/serializers/validators.py，业务模块通过导入复用
5. Dockerfile生产环境必须使用多阶段构建减小镜像体积
6. Docker Compose服务必须配置restart策略保证高可用
7. 前端全局配置（locale/错误处理）只在入口文件设置一次

**状态**: **已修复** | 2026-04-10

---

## E301: 架构审查P1高优先级问题修复（12项）

**错误类型**: 架构/安全/可靠性

**修复内容**:

1. **E301-1: 异常处理器不覆盖原生Python异常**
   - 问题: DRF异常处理器对原生Python异常(ValueError/ConnectionError等)返回None，Django返回HTML 500
   - 修复: 在exception_handler中添加BusinessError/django ValidationError/PermissionError/ConnectionError/TimeoutError/通用Exception的处理
   - 文件: `backend/core/exceptions.py`

2. **E301-2: Celery队列定义冲突**
   - 问题: celery.py定义5个队列含vector，production.py定义4个队列无vector；redis_cluster_hosts死代码；CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS中master_name无效
   - 修复: 移除死代码和无效配置，统一5队列定义
   - 文件: `backend/config/celery.py`

3. **E301-3: TraceIdMiddleware未注册+限流器Bug**
   - 问题: TraceIdMiddleware未在MIDDLEWARE中注册导致日志trace_id始终为"-"；DynamicRateThrottle的system_load缓存键从未被设置；ConcurrentRequestThrottle使用Django缓存不支持的expire方法
   - 修复: 添加TraceIdMiddleware到MIDDLEWARE；添加update_system_load()函数供定时调用；ConcurrentRequestThrottle改用cache.incr/decr+TTL
   - 文件: `backend/config/settings/base.py`, `backend/core/throttling.py`

4. **E301-4: 自定义CorsMiddleware与django-cors-headers冲突**
   - 问题: base.py MIDDLEWARE中同时包含corsheaders和core.middleware.CorsMiddleware
   - 修复: 移除自定义CorsMiddleware，统一使用django-cors-headers
   - 文件: `backend/core/middleware.py`, `backend/config/settings/base.py`

5. **E301-5: 接口定义与实现不匹配**
   - 问题: LLMServiceInterface.chat签名与UnifiedLLMService.chat完全不同；VectorStoreInterface方法名与ChromaClient不匹配
   - 修复: 重写interfaces.py，LLMServiceInterface改为async+匹配签名；VectorStoreInterface改为文档级操作；OCRServiceInterface的默认实现改为@abstractmethod
   - 文件: `backend/services/interfaces.py`

6. **E301-6: 错误信息泄露**
   - 问题: tenders/enterprise/openclaw视图中str(e)直接返回客户端，可能泄露数据库结构/文件路径/内部服务地址
   - 修复: 替换为通用错误消息，详细信息仅记录到logger
   - 文件: `backend/apps/tenders/views.py`, `backend/apps/enterprise/views.py`, `backend/apps/openclaw/views.py`

7. **E301-7: LLMUsageLogViewSet serializer_class错误**
   - 问题: serializer_class设为LLMModelSerializer而非LLMUsageLogSerializer
   - 修复: 改为LLMUsageLogSerializer
   - 文件: `backend/apps/openclaw/views.py`

8. **E301-8: 审计日志缓冲区无定时刷新**
   - 问题: 进程崩溃时未刷新的日志丢失，无atexit注册
   - 修复: 添加atexit.register(_flush_buffer)和30秒定时刷新机制
   - 文件: `backend/utils/audit_logger.py`

9. **E301-9: WorkflowEngine内存泄漏**
   - 问题: _workflows Dict只增不减，长期运行OOM
   - 修复: 添加MAX_WORKFLOWS=1000上限、WORKFLOW_TTL_SECONDS=3600过期清理、_cleanup_expired_workflows方法
   - 文件: `backend/services/unified_workflow_engine.py`

10. **E301-10: DjangoFastAPIBridge单例__init__重置Redis连接**
    - 问题: 单例模式下__init__每次调用重置_redis_client为None
    - 修复: 添加_initialized标志，__init__仅在首次调用时初始化
    - 文件: `backend/core/django_fastapi_bridge.py`

11. **E301-11: 前端getCookie重复+Token刷新竞态+PWA无效**
    - 问题: getCookie在request.js和user.js中重复定义；401时多个请求同时触发logout；PWA配置缺少依赖
    - 修复: 提取@/utils/cookie.js公共模块；添加hasLoggedOut标志防止多次logout；移除无效PWA配置
    - 文件: `frontend/src/utils/cookie.js`(新建), `frontend/src/utils/request.js`, `frontend/src/store/user.js`, `frontend/vue.config.js`

12. **E301-12: 缺少依赖+CI/CD修复**
    - 问题: requirements.txt缺少python-json-logger；CI/CD安全扫描|| true忽略失败；deploy-production无实际部署逻辑；codecov使用v3
    - 修复: 添加python-json-logger==2.0.7；移除|| true；deploy-production添加SSH部署+健康检查；codecov升级v4
    - 文件: `backend/requirements.txt`, `.github/workflows/ci-cd.yml`

**预防措施**:
1. 异常处理器必须覆盖所有可能的异常类型
2. Celery队列定义应只在celery.py中，production.py通过namespace='CELERY'继承
3. 中间件注册后必须验证日志中trace_id是否正常
4. 接口定义变更时必须同步更新实现类
5. 异常信息不得直接返回客户端，仅记录到日志
6. 单例模式必须使用_initialized标志防止__init__重复执行
7. 内存缓存必须设置上限和TTL清理机制
8. CI/CD安全扫描失败必须阻断流水线

**状态**: **已修复** | 2026-04-10

---

## E300: 架构审查P0严重问题修复（15项）

**错误类型**: 安全/架构/基础设施

**修复内容**:

1. **E300-1: 生产环境日志敏感信息过滤失效**
   - 问题: production.py 的 `sensitive_data_filter` 指向 `django.utils.log.ServerFormatter` 而非 `core.logging_config.SensitiveFilter`
   - 修复: 改为 `'core.logging_config.SensitiveFilter'`
   - 文件: `backend/config/settings/production.py`

2. **E300-2: ASGI/FastAPI 环境变量硬编码为 development**
   - 问题: `asgi.py` 和 `fastapi_app/main.py` 默认使用 `config.settings.development`，生产部署风险极高
   - 修复: 改为 `config.settings.production`
   - 文件: `backend/config/asgi.py`, `backend/fastapi_app/main.py`

3. **E300-3: monitor 模块所有视图无权限控制**
   - 问题: MonitoredServiceViewSet/ServiceAlertViewSet/MonitorHealthCheckView/MonitorAutoRecoveryView 均无权限，任何人可重启服务
   - 修复: 添加 `IsAuthenticated` 默认权限，写操作和敏感操作添加 `IsAdminUser`
   - 文件: `backend/apps/monitor/views.py`

4. **E300-4: TenderProxyView XSS 风险**
   - 问题: `target_url` 未转义直接插入 HTML 的 `href` 和文本中
   - 修复: 使用 `django.utils.html.escape` 对 `target_url` 进行 HTML 转义，添加 `rel="noopener noreferrer"`
   - 文件: `backend/apps/tenders/views.py`

5. **E300-5: BaseViewSet 数据隔离逻辑失效**
   - 问题: `get_queryset` 仅检查 `user` 字段，但多数业务模型使用 `created_by`
   - 修复: 同时检查 `user` 和 `created_by` 字段
   - 文件: `backend/common/views/base.py`

6. **E300-6: TraceContextManager 线程不安全**
   - 问题: `_current_context` 是类变量，多线程下互相覆盖
   - 修复: 改用 `threading.local()` 存储每个线程的追踪上下文；同时修复 `create_span` 中 tags 遍历 `span.tags` 而非传入 `tags` 的 bug
   - 文件: `backend/utils/observability.py`

7. **E300-7: Layout.vue 定时器内存泄漏**
   - 问题: `onMounted` 返回清理函数在 Vue 3 中无效，`setInterval` 永不清除
   - 修复: 使用 `onUnmounted` 注册清理函数；修复 `/settings` 路由不存在改为 `/profile`
   - 文件: `frontend/src/views/Layout.vue`

8. **E300-8: 缺少 404 路由和路由权限守卫**
   - 问题: 无兜底路由，无管理员路由权限控制
   - 修复: 添加 `/:pathMatch(.*)*` 404 路由；添加 `requiresAdmin` meta + 守卫检查 `is_staff`
   - 文件: `frontend/src/router/index.js`

9. **E300-9: 前端 HttpOnly Cookie 设置无效**
   - 问题: JavaScript 无法设置 HttpOnly Cookie，`document.cookie` 设置的 Cookie 可被 XSS 窃取
   - 修复: 前端不再尝试设置 HttpOnly Cookie，改为由后端 `Set-Cookie` 响应头设置；前端仅读取 Cookie 判断登录状态
   - 文件: `frontend/src/store/user.js`

10. **E300-10: 后端 Dockerfile 健康检查使用 curl 但未安装**
    - 问题: `python:3.11-slim` 不含 curl，HEALTHCHECK 永远失败
    - 修复: 在 apt 安装列表中添加 `curl`
    - 文件: `backend/Dockerfile`

11. **E300-11: 前端 Dockerfile `npm ci --only=production` 导致构建失败**
    - 问题: `--only=production` 跳过 devDependencies，Vite 等构建工具无法安装
    - 修复: 改为 `npm ci`（不加 `--only=production`）
    - 文件: `frontend/Dockerfile`

12. **E300-12: Nginx 端口不一致和未定义 upstream**
    - 问题: 前端 nginx.conf 上游端口 8007 vs 后端实际 8000；网关引用未定义的 `frontend`/`backend-replica` upstream；`/ws/` 路由指向 Django 而非 FastAPI
    - 修复: 端口改为 8000；添加 `frontend-app` upstream；`/ws/` 改为指向 `fastapi-api`；移除 `backend-replica` backup
    - 文件: `frontend/nginx.conf`, `docker/nginx/gateway.conf`

13. **E300-13: 响应格式三重体系冲突**
    - 问题: `StandardPagination`、`APIResponse`、`UnifiedResponseMiddleware` 三套格式互相覆盖/嵌套
    - 修复: `StandardPagination` 返回 DRF 原始分页格式 `{results, count, page, page_size, total_pages}`，由 `UnifiedResponseMiddleware` 统一转换为 `{code, message, data, meta.pagination, timestamp}`；修复时间戳使用 `django.utils.timezone.now()` 而非 `datetime.now().isoformat() + 'Z'`
    - 文件: `backend/core/pagination.py`, `backend/common/middleware/unified_response.py`

14. **E300-14: LLMProvider.api_key 明文存储**
    - 问题: `api_key` 字段使用 `TextField` 明文存储，注释说"加密存储"但实际未加密
    - 修复: 改为 `_api_key` (db_column='api_key') + `@property api_key` getter/setter，setter 自动调用 `encrypt_sensitive_data` 加密，getter 自动调用 `decrypt_sensitive_data` 解密
    - 文件: `backend/apps/openclaw/models.py`

15. **E300-15: FastAPI main.py 多个问题**
    - 问题: `logger` 未定义、`import json` 在循环内、`StreamEventType` 未导入、`system_status` 暴露敏感信息且无权限控制、WebSocket 无认证、全局异常处理器暴露内部错误
    - 修复: 添加顶部 `import json/logging` 和 `logger`；导入 `StreamEventType`；`system_status` 添加 `is_staff` 权限检查并移除敏感信息；全局异常处理器返回通用错误消息
    - 文件: `backend/fastapi_app/main.py`

**预防措施**:
1. 环境变量默认值必须使用 `production` 配置，开发环境通过 `.env` 文件覆盖
2. 所有 API 视图必须显式声明 `permission_classes`
3. 用户输入插入 HTML 必须经过转义
4. 数据隔离必须同时检查 `user` 和 `created_by` 字段
5. 线程上下文必须使用 `threading.local()` 而非类变量
6. Vue 组件清理逻辑必须使用 `onUnmounted` 而非 `onMounted` 返回值
7. 前端不可设置 HttpOnly Cookie，必须由后端 Set-Cookie 设置
8. Dockerfile 健康检查依赖的工具必须在镜像中安装
9. 前端构建不可使用 `--only=production`（构建工具在 devDeps 中）
10. API 密钥等敏感字段必须加密存储

**状态**: **已修复** | 2026-04-10

---

## E299: 项目安全与性能优化（23项修复）

**错误类型**: 安全/性能/代码质量

**修复内容**:
1. DEBUG 默认值从 'True' 改为 'False'（base.py）
2. docker-compose-milvus.yml 中 MinIO 密码改为环境变量引用
3. docker-compose-milvus.yml 添加 healthcheck 配置
4. UserRegisterView 添加 throttle_classes=[LoginRateThrottle]
5. 前端 refresh_token 不再存 sessionStorage，仅依赖 HttpOnly Cookie
6. 批量操作 Serializer 已有 max_length=100 限制
7. TenderProjectListSerializer 的 get_files_count 改用 annotate 避免N+1
8. 统计查询已使用 aggregate + Case/When 单次查询
9. BidDocumentLibrary 查询添加 select_related
10. CrawlerTask.status 添加 db_index，添加复合索引
11. users/views.py 和 health_checker.py 的 except Exception 添加日志记录
12. services.py 中 4 处 .get() 改为 get_object_or_404
13. TenderStatisticsView 已有 permission_classes=[IsAuthenticated]
14. bids/models.py 添加 MinValueValidator/MaxValueValidator
15. TenderFile.tender 和 CrawlerTask.source 的 on_delete 从 CASCADE 改为 SET_NULL
16. TenderProject 添加 is_deleted 字段实现软删除
17. Celery 任务超时从 3600s 改为 900s
18. 添加 CELERY_RESULT_EXPIRES = 3600
19. production.py 日志已有 RotatingFileHandler 配置
20. docker-compose-milvus.yml 添加 healthcheck
21. 路由切换时调用 cancelAllPendingRequests()
22. celery.py 的 debug_task 改用 logging
23. 统一 API 响应格式，移除 {'list': [...]} 包装

**状态**: **已修复** | 2026-04-10

---

## E298: Milvus 容器启动失败

**错误类型**: Docker 容器崩溃

**错误现象**:
- Milvus 容器启动后立即退出，状态 `Exited (1)`
- 日志只显示 tini init 帮助信息，没有实际错误
- 尝试多个版本（latest、v2.3.4）均失败
- 依赖服务（etcd、minio）正常运行

**发生场景**:
- Windows Docker Desktop 环境
- 使用 docker-compose-milvus.yml 启动
- 系统内存 16GB，Docker 分配约 15.53GB

**错误日志**:
```
bid-milvus         Exited (1) 38 seconds ago
bid-milvus-minio   Up 38 seconds
bid-milvus-etcd    Up 38 seconds
```

**尝试的解决方案**:
1. ✅ 重启容器：`docker-compose up -d`
2. ✅ 强制重建：`docker-compose up -d --force-recreate`
3. ✅ 降级版本：从 latest 切换到 v2.3.4
4. ✅ 添加资源限制：memory limit 2G
5. ❌ 查看日志：`docker logs bid-milvus` 只显示 tini 帮助信息

**可能原因**:
1. Windows Docker 与 Milvus 镜像兼容性问题
2. 镜像缺少必要的依赖或库
3. Docker Desktop 配置问题（如 WSL2 后端）
4. 系统资源不足或分配不当

**临时解决方案**:
- **使用 Chroma 作为向量数据库**（已配置在 8000 端口）
- Milvus 作为可选服务，不影响核心功能
- 企业向量检索功能使用 Chroma 实现

**预防措施**:
1. 评估使用 Chroma 作为主要向量数据库
2. 如需 Milvus，考虑在 Linux 环境或 WSL2 中运行
3. 检查 Docker Desktop WSL2 配置
4. 考虑使用 Milvus 轻量版或单机版

**相关文件**:
- `docker-compose-milvus.yml`
- `backend/services/vector/milvus_service.py`

**状态**: **已修复** | 2026-04-16

**最终解决方案**: 使用 Milvus v2.4.17 standalone 模式替代 v2.3.4。v2.4.x 修复了 Windows Docker Desktop 兼容性问题。部署方式：etcd + minio + milvus 三个容器在同一 Docker 网络（app），Milvus 通过容器名访问依赖服务。

---
