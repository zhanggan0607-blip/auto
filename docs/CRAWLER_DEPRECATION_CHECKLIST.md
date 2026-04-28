# 爬虫模块废弃清单（保守渐进策略）

## 废弃策略说明

本项目采用**保守渐进策略**清理爬虫冗余：
- 不进行大规模重构，避免破坏现有功能
- 通过标记废弃 + 新功能引导的方式逐步迁移
- 等依赖方自然迁移或业务淡出后逐步删除

---

## 废弃状态总览

| 文件 | 状态 | 说明 |
|------|------|------|
| `anti_detection.py` | ⚠️ 已废弃 | 仅被 `multi_strategy_crawler.py` 内部引用，建议删除 |
| `cookie_manager.py` | ⚠️ 已废弃 | 已被 `common.crawler.managers.cookie_manager` 替代，建议删除 |
| `cookie_based_collector.py` | ⚠️ 已废弃 | 被 `enterprise/views.py` 引用，建议迁移后删除 |
| `base_crawler.py` | 🔴 保留 | 被 `UniversalCrawlerEngine`、`tasks.py` 复杂依赖 |
| `multi_strategy_crawler.py` | 🔴 保留 | 被 `UniversalCrawlerEngine` 依赖 |
| `configurable_crawler.py` | 🔴 保留 | 被 `services/one_click_automation.py` 引用 |

---

## 可安全删除的文件（无外部依赖）

### 1. anti_detection.py
- **路径**: `crawler/anti_detection.py`
- **功能**: 反检测 JavaScript 注入
- **替代**: `common.crawler.strategies.SeleniumStrategy`
- **引用**: 仅被 `multi_strategy_crawler.py` 内部使用
- **删除条件**: 确认无其他外部引用后可删除

### 2. cookie_manager.py
- **路径**: `crawler/cookie_manager.py`
- **功能**: Cookie 存储、验证、格式化
- **替代**: `common.crawler.managers.cookie_manager.CookieManager`
- **引用**: 无外部直接引用
- **删除条件**: 确认 `cookie_based_collector.py` 被废弃后即可删除

---

## 已废弃文件（标记 @deprecated，待删除）

### 1. cookie_based_collector.py
- **路径**: `crawler/cookie_based_collector.py`
- **功能**: 基于Cookie的企业信息采集器
- **替代**: `common.crawler.common_crawler.CommonCrawler`
- **引用**: `enterprise/views.py` - `collect_with_cookies`
- **废弃策略**: 标记 @deprecated，引导使用 `common.crawler`

---

## 需要保留的文件（依赖复杂，渐进处理）

### 1. base_crawler.py 🔴
- **路径**: `crawler/base_crawler.py`
- **功能**: 爬虫基类，包含 Selenium/WebDriver 初始化
- **引用**:
  - `apps/crawler/services.py` - `UniversalCrawlerEngine`
  - `crawler/tasks.py` - 任务中创建 BaseCrawler
  - `crawler/configurable_crawler.py` - 继承 BaseCrawler
  - `crawler/china_gov_crawler.py` - 继承 BaseCrawler
- **废弃策略**: 标记 @deprecated，新功能使用 `common.crawler`

### 2. multi_strategy_crawler.py 🔴
- **路径**: `crawler/multi_strategy_crawler.py`
- **功能**: 多级降级策略、自适应频率控制、爬取监控
- **引用**: `apps/crawler/services.py` - `UniversalCrawlerEngine`
- **废弃策略**: 标记 @deprecated

### 3. configurable_crawler.py 🔴
- **路径**: `crawler/configurable_crawler.py`
- **功能**: 可配置爬虫（Selenium 配置）
- **引用**: `services/one_click_automation.py`
- **废弃策略**: 标记 @deprecated，新功能使用 `common.crawler`

---

## 业务专用爬虫（保留，不应废弃）

以下文件是业务专用爬虫，**不应标记废弃**：

| 文件 | 用途 |
|------|------|
| `china_gov_crawler.py` | 中国政府采购网站爬虫 |
| `enterprise_browser_crawler.py` | 企业浏览器采集 |
| `shanghai_construction_crawler.py` | 上海建设招标爬虫 |
| `shanghai_gov_crawler_v2.py` | 上海政府爬虫 v2 |
| `shanghai_gov_procurement_crawler.py` | 上海政府采购爬虫 |
| `staged_collection_workflow.py` | 分阶段采集工作流 |
| `stealth_crawler.py` | 隐身爬虫 |
| `pyppeteer_crawler.py` | Pyppeteer 爬虫 |
| `scrapling_enterprise_collector.py` | Scrapling 企业采集 |
| `data_source_validator.py` | 数据源验证器 |
| `self_healing.py` | 故障自愈机制 |
| `tasks.py` | Celery异步任务 |
| `common_types.py` | 公共类型定义 |

---

## 废弃步骤（保守渐进）

### Phase 1: 清理无依赖文件 ✅
1. ✅ 已完成：迁移 `enterprise/views.py` 到 `common.crawler`
2. ✅ 已完成：迁移 `scripts/import_cookies.py` 到 `common.crawler`
3. ⚠️ 待执行：标记 `cookie_based_collector.py` 为 @deprecated
4. ⚠️ 待执行：删除 `crawler/anti_detection.py`（无外部引用）
5. ⚠️ 待执行：删除 `crawler/cookie_manager.py`（无外部引用）

### Phase 2: 标记废弃（不删除）
1. ⚠️ 标记 `base_crawler.py` 为 @deprecated
2. ⚠️ 标记 `multi_strategy_crawler.py` 为 @deprecated
3. ⚠️ 标记 `configurable_crawler.py` 为 @deprecated

### Phase 3: 引导新功能迁移
1. 新爬虫开发统一使用 `common.crawler.CommonCrawler`
2. 文档化迁移指南
3. 监控依赖变化，逐步删除无引用文件

---

## 废弃检查清单

### 可立即删除
- [ ] `crawler/anti_detection.py` - 无外部引用
- [ ] `crawler/cookie_manager.py` - 无外部引用

### 标记废弃
- [ ] `crawler/cookie_based_collector.py` - 添加 @deprecated 注释

### 标记 @deprecated（保留使用）
- [ ] `crawler/base_crawler.py` - 添加 @deprecated 注释
- [ ] `crawler/multi_strategy_crawler.py` - 添加 @deprecated 注释
- [ ] `crawler/configurable_crawler.py` - 添加 @deprecated 注释

---

## 新爬虫开发规范

**新增爬虫必须使用 `common.crawler`**：

```python
from common.crawler import CommonCrawler, CrawlerConfig

class MyCrawler(CommonCrawler):
    def parse_items(self, html: str):
        # 实现解析逻辑
        pass

config = CrawlerConfig(
    headless=True,
    proxy_enabled=True,
    proxy_list=['http://proxy:8080']
)
crawler = MyCrawler(config=config)
```

---

**最后更新**: 2026-04-04
**维护者**: 架构组
**版本**: v2.0（保守渐进策略）
