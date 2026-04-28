# 故障排除记录

## 2026-04-23 修复记录

### E371: 上海建筑建材业采集任务完成但无数据

**触发场景**: 执行上海建筑建材业采集任务

**错误原因**（3个叠加问题）:
1. `tasks.py` 默认 `notice_types=['gkzb','jzxcs','jzxtp','xjcg']`（政府采购网代码），但上海建筑建材业使用 `['zbgg','zbjg','gzgg','fbgg','htgg']`，导致所有公告类型被跳过
2. `ShanghaiConstructionCrawler` 的API策略对SPA页面返回HTTP 200但内容为空壳HTML，被误判为成功，不降级到headless浏览器
3. 旧平台公开API `/jygg/list` 已无数据（数据迁移到新平台，需要SSO认证）

**修复方案**:
1. `tasks.py`: 添加 `source_default_notice_types` 映射，不同采集源使用不同的默认公告类型
2. `shanghai_construction_crawler.py`: 重写为直接使用公开API，不再依赖Pyppeteer渲染SPA

**当前状态**: 代码已修复，但旧平台API返回空数据。上海建筑建材业网站数据已迁移到新平台（需要SSO认证），需要提供SSO认证凭据才能采集数据。

**API发现**:
- 旧平台公开API: `POST /JGBAppZtbInterWeb/interWeb/jygg/list` (不需要认证，但已无数据)
- 新平台API: `POST /JGBXMJYPTInterWeb/xxx/api/xxx` (需要SSO认证，cookie: `xc_ciacsso`)
- 新平台登录页: `https://ciac.zjw.sh.gov.cn/JGBCiacUserPortalInterWeb/pc/#/login`

### E370: "cannot access local variable 'asyncio' where it is not associated with a value"

**触发场景**: 执行上海建筑建材业采集任务

**错误原因**: `tasks.py` 的 `scheduled_crawl_with_match` 函数内部有局部 `import asyncio`（第1239行），Python 将 `asyncio` 视为整个函数的局部变量，但在第1077行就引用了 `asyncio.new_event_loop()`，此时局部变量尚未赋值，触发 `UnboundLocalError`。

**修复方案**:
1. 删除 `tasks.py` 第1239行的局部 `import asyncio`（文件顶部已有导入）
2. 全项目排查并清理所有14处局部 `import asyncio`，统一移到文件顶部

**修改文件**（9个）:
- `crawler/tasks.py` — 删除局部 import
- `apps/enterprise/views.py` — 删除3处局部 import
- `openclaw/agents/professional_agents.py` — 删除局部 import
- `apps/openclaw/automation_tasks.py` — 添加顶层 import + 删除2处局部 import
- `crawler/multi_strategy_crawler.py` — 添加顶层 import + 删除局部 import
- `apps/vectorlib/views.py` — 添加顶层 import + 删除局部 import
- `common/utils/http_client.py` — 添加顶层 import + 删除局部 import
- `services/bid_automation_workflow.py` — 添加顶层 import + 删除3处局部 import
- `openclaw/ai_extractors/enterprise_extractor.py` — 添加顶层 import + 删除局部 import

**预防措施**: 禁止在函数内部使用 `import asyncio`，所有 `import asyncio` 必须放在文件顶部

---

### E369: "cannot schedule new futures after interpreter shutdown"

**触发场景**: Celery worker 执行采集任务、AI Playground 对话

**错误原因**: 5个问题叠加：
1. `tasks.py` 使用 `ThreadPoolExecutor` 运行异步代码
2. 多个文件使用已弃用的 `asyncio.get_event_loop()`
3. `workflow_views.py` 和 `vectorlib/views.py` 用 `ThreadPoolExecutor` 嵌套 `asyncio.run()`
4. `views.py` AI Playground 使用 `asyncio.run()`
5. `automation_tasks.py` 和 `enterprise/views.py` 使用 `asyncio.run()`

**修复方案**: 14个文件，统一替换为 `asyncio.new_event_loop()` + `loop.run_until_complete()` + `try/finally: loop.close()`

**核心原则**:
- 同步上下文运行异步代码：`asyncio.new_event_loop()` + `loop.run_until_complete()` + `try/finally: loop.close()`
- 异步上下文运行同步代码：`asyncio.get_running_loop().run_in_executor()`
- **禁止** `asyncio.run()`、`asyncio.get_event_loop()`、`ThreadPoolExecutor` 运行异步代码

---

### E368: 采集计划 max_pages 设置不生效

**触发场景**: 上海建筑建材业采集200+页超出设定89页

**修复方案**: 修复7个重叠问题，创建 `CrawlSourceRegistry` 统一注册

---

### E367: 登录500错误

**触发场景**: Vite 代理端口不匹配（8100 vs 8000）

**修复方案**: 统一代理端口为8000
