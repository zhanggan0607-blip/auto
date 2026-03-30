# 数据库迁移计划

## 概述

本文档描述了数据库清理和迁移的详细计划，包括废弃表的删除、数据迁移和验证步骤。

## 当前数据库状态

### 所有数据库表

| 应用 | 表名 | 模型 | 状态 |
|------|------|------|------|
| documents | document_templates | DocumentTemplate | ✅ 保留 |
| documents | generated_documents | GeneratedDocument | ✅ 保留 |
| documents | company_infos | CompanyInfo | ❌ 废弃 - 待删除 |
| tenders | tender_sources | TenderSource | ✅ 保留 |
| tenders | tender_projects | TenderProject | ✅ 保留 |
| tenders | tender_files | TenderFile | ✅ 保留 |
| tenders | tender_keywords | TenderKeyword | ✅ 保留 |
| tenders | crawler_tasks | CrawlerTask | ✅ 保留 |
| search_config | search_engines | SearchEngine | ⚠️ 未使用 - 可选删除 |
| search_config | search_categories | SearchCategory | ⚠️ 未使用 - 可选删除 |
| search_config | search_templates | SearchTemplate | ⚠️ 未使用 - 可选删除 |
| search_config | search_histories | SearchHistory | ⚠️ 未使用 - 可选删除 |
| search_config | search_rules | SearchRule | ⚠️ 未使用 - 可选删除 |
| search_config | search_tasks | SearchTask | ⚠️ 未使用 - 可选删除 |
| enterprise | enterprises | Enterprise | ✅ 保留 |
| enterprise | enterprise_qualifications | EnterpriseQualification | ✅ 保留 |
| enterprise | enterprise_performances | EnterprisePerformance | ✅ 保留 |
| enterprise | enterprise_match_rules | EnterpriseMatchRule | ✅ 保留 |
| enterprise | enterprise_match_results | EnterpriseMatchResult | ✅ 保留 |
| enterprise | enterprise_contacts | EnterpriseContact | ✅ 保留 |
| enterprise | enterprise_bid_configs | EnterpriseBidConfig | ✅ 保留 |
| enterprise | enterprise_documents | EnterpriseDocument | ✅ 保留 |
| enterprise | document_audit_logs | DocumentAuditLog | ✅ 保留 |
| vectorlib | bid_document_library | BidDocumentLibrary | ✅ 保留 |
| vectorlib | document_search_logs | DocumentSearchLog | ✅ 保留 |
| vectorlib | ai_search_tasks | AISearchTask | ✅ 保留 |
| notifications | notification_channels | NotificationChannel | ⚠️ 部分使用 |
| notifications | notifications | Notification | ✅ 保留 |
| notifications | notification_templates | NotificationTemplate | ⚠️ 未使用 |
| notifications | notification_logs | NotificationLog | ⚠️ 未使用 |
| crawler | website_templates | WebsiteTemplate | ✅ 保留 |
| crawler | crawl_sessions | CrawlSession | ✅ 保留 |
| crawler | crawl_results | CrawlResult | ✅ 保留 |
| crawler | crawl_logs | CrawlLog | ✅ 保留 |
| crawler | failure_knowledge | FailureKnowledge | ✅ 保留 |
| crawler | enterprise_vector_indices | EnterpriseVectorIndex | ✅ 保留 |
| crawler | bid_project_trackings | BidProjectTracking | ✅ 保留 |
| bids | bid_records | BidRecord | ✅ 保留 |
| bids | bid_results | BidResult | ✅ 保留 |
| bids | bid_statistics | BidStatistics | ✅ 保留 |
| openclaw | llm_providers | LLMProvider | ✅ 保留 |
| openclaw | llm_models | LLMModel | ✅ 保留 |
| openclaw | agent_model_configs | AgentModelConfig | ✅ 保留 |
| openclaw | llm_usage_logs | LLMUsageLog | ✅ 保留 |

## 迁移计划

### 阶段1: 废弃表删除 (必须执行)

#### 1.1 删除 CompanyInfo 表

**原因**: 该模型已废弃，数据已迁移到 Enterprise 模块

**迁移步骤**:
1. 确认数据已迁移完成
2. 创建删除迁移
3. 执行迁移

```bash
# 检查是否有数据需要迁移
python manage.py shell -c "
from apps.documents.models import CompanyInfo
count = CompanyInfo.objects.count()
print(f'CompanyInfo 记录数: {count}')
"

# 创建迁移
python manage.py makemigrations documents --name remove_company_info

# 执行迁移
python manage.py migrate documents
```

### 阶段2: 未使用表清理 (可选执行)

#### 2.1 search_config 模块表

**状态**: 前端未调用，但可能用于未来功能

**建议**: 
- 如果确认不使用，可以删除整个模块
- 如果可能用于未来功能，保留但标记为待定

```bash
# 删除整个 search_config 模块
python manage.py makemigrations search_config --name drop_all_tables
python manage.py migrate search_config
```

#### 2.2 notifications 模块部分表

**未使用表**:
- notification_channels
- notification_templates
- notification_logs

**建议**: 保留 notifications 表，删除其他未使用表

### 阶段3: 数据清理 (推荐执行)

#### 3.1 清理孤立记录

```sql
-- 清理没有企业关联的文档
DELETE FROM enterprise_documents WHERE enterprise_id IS NULL;

-- 清理没有企业关联的匹配结果
DELETE FROM enterprise_match_results WHERE enterprise_id IS NULL;

-- 清理过期的会话记录
DELETE FROM crawl_sessions WHERE status = 'completed' AND created_at < NOW() - INTERVAL '30 days';
```

#### 3.2 清理过期日志

```sql
-- 清理30天前的爬虫日志
DELETE FROM crawl_logs WHERE created_at < NOW() - INTERVAL '30 days';

-- 清理30天前的通知日志
DELETE FROM notification_logs WHERE created_at < NOW() - INTERVAL '30 days';
```

## 迁移脚本

### 执行顺序

```
1. 备份数据库
2. 执行阶段1迁移 (废弃表删除)
3. 执行阶段3清理 (数据清理)
4. 验证迁移结果
5. (可选) 执行阶段2迁移 (未使用表清理)
```

### 备份命令

```bash
# PostgreSQL 备份
pg_dump -h localhost -U postgres -d auto_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复命令 (如需回滚)
# psql -h localhost -U postgres -d auto_db < backup_20260320.sql
```

### 迁移命令

```bash
cd d:\共享文件\AUTO\backend

# 1. 检查迁移状态
python manage.py showmigrations

# 2. 创建迁移
python manage.py makemigrations

# 3. 执行迁移
python manage.py migrate

# 4. 验证
python manage.py check
```

## 验证清单

- [ ] 后端服务启动正常
- [ ] API接口响应正常
- [ ] 前端页面加载正常
- [ ] 企业模块功能正常
- [ ] 爬虫模块功能正常
- [ ] 通知模块功能正常

## 回滚计划

如果迁移失败，执行以下步骤回滚：

```bash
# 1. 停止服务
# 2. 恢复数据库
psql -h localhost -U postgres -d auto_db < backup_20260320.sql

# 3. 恢复代码
git checkout -- .

# 4. 重启服务
```

## 注意事项

1. **生产环境迁移前必须备份**
2. **建议在测试环境先验证**
3. **迁移期间需要停机维护**
4. **保留回滚脚本和备份文件**
5. **迁移后验证所有功能正常**

## 联系人

如有问题，请联系开发团队。

---

**文档版本**: 1.0  
**创建日期**: 2026-03-20  
**最后更新**: 2026-03-20
