# 字段命名规范

## 目的

统一前后端字段命名，避免字段不一致导致的 API 调用错误。

---

## 核心规则

### 1. 外键字段命名规则

**DRF 的 PrimaryKeyRelatedField 期望的是关联对象本身（ID），字段名是关联名，不是 `xxx_id`**

| 后端 Serializer 字段 | 前端提交时的 JSON Key | 说明 |
|---------------------|---------------------|------|
| `tender = serializers.PrimaryKeyRelatedField(...)` | `"tender": 123` | 直接用关联名，不是 `tender_id` |
| `bid_manager = serializers.PrimaryKeyRelatedField(...)` | `"bid_manager": 456` | 直接用关联名，不是 `bid_manager_id` |
| `source = serializers.PrimaryKeyRelatedField(...)` | `"source": 1` | 直接用关联名 |

**❌ 错误示例**：
```javascript
// 错误！后端无法识别 tender_id
const data = {
  tender_id: bidForm.tender_id,       // ❌
  bid_manager_id: bidForm.bid_manager_id  // ❌
}
```

**✅ 正确示例**：
```javascript
// 正确！字段名与后端 Serializer 期望一致
const data = {
  tender: bidForm.tender_id,           // ✅ 关联名
  bid_manager: bidForm.bid_manager_id, // ✅ 关联名
}
```

---

### 2. 外键字段读取规则（列表/详情）

**后端 Serializer 的 source 字段展开会返回完整对象或特定字段**

| 后端 Serializer 定义 | 前端收到的数据结构 |
|---------------------|------------------|
| `tender_id = serializers.IntegerField(source='tender.id', read_only=True)` | `"tender_id": 123` (纯ID) |
| `tender_title = serializers.CharField(source='tender.title', read_only=True)` | `"tender_title": "项目名称"` (展开字段) |
| `tender = TenderSourceSerializer(read_only=True)` | `"tender": {id, name, ...}` (完整对象) |

**前端模板中使用**：
```vue
<!-- tender_id 是纯ID -->
<el-table-column prop="tender_id" label="招标ID" />

<!-- tender_title 是展开的字符串 -->
<el-table-column prop="tender_title" label="项目名称" />

<!-- tender 是完整对象（需要小心处理） -->
<template #default="{ row }">
  <span>{{ row.tender?.title }}</span>
</template>
```

---

## 已知的字段映射对照表

### 投标记录 (BidRecord)

| 操作 | 前端变量 (form.tender_id) | 提交到后端的 JSON Key | 后端 Serializer 期望 |
|-----|------------------------|---------------------|---------------------|
| 创建 | `bidForm.tender_id` | `tender: 123` | `tender` |
| 创建 | `bidForm.bid_manager_id` | `bid_manager: 456` | `bid_manager` |
| 创建 | `bidForm.team_member_ids[]` | `team_members: [1,2,3]` | `team_members` |
| 读取 | API 返回 | `tender_id`, `tender_title`, `bid_manager_id`, `bid_manager_name` | `source='tender.id'` 等 |

### 招标项目 (TenderProject)

| 操作 | 提交到后端的 JSON Key | 后端 Serializer 期望 |
|-----|---------------------|---------------------|
| 创建 | `source: 1` | `source` (PrimaryKeyRelatedField) |
| 创建 | `publish_date: "2026-01-01"` | `publish_date` |
| 批量更新 | `ids: [1,2,3]`, `status: "archived"` | `ids`, `status` |

### 企业资质 (EnterpriseQualification)

| 操作 | 提交到后端的 JSON Key | 后端 Serializer 期望 |
|-----|---------------------|---------------------|
| 创建 | `enterprise: 1` | `enterprise` |
| 创建 | `qualification_type: "construction"` | `qualification_type` |

---

## 开发检查清单

在提交 API 调用前，确认以下内容：

- [ ] 确认后端 Serializer 的 `fields` 定义
- [ ] 确认外键字段名是关联名（如 `tender`）还是 `xxx_id`
- [ ] 确认 `read_only=True` 的字段不需要提交
- [ ] 确认日期格式为 `YYYY-MM-DD`
- [ ] 确认数字字段不是字符串

---

## DRF Serializer 字段类型速查

| 字段类型 | 提交时 Key | 示例值 |
|---------|-----------|--------|
| PrimaryKeyRelatedField | 关联名 | `tender: 123` |
| CharField | 字段名 | `title: "标题"` |
| IntegerField | 字段名 | `budget: 100000` |
| DateField | 字段名 | `deadline_date: "2026-01-01"` |
| SerializerMethodField | 只读 | 不需要提交 |
| 嵌套 Serializer | 对象 | `source: {name: "xx"}` (只读) |

---

## 常见错误排查

### 错误：`'tender_id' is not a valid field`

**原因**：后端 Serializer 期望的是 `tender`，不是 `tender_id`

**解决**：
```javascript
// 改
{ tender_id: value }
// 为
{ tender: value }
```

### 错误：`Invalid pk "xxx" - object does not exist.`

**原因**：提交的外键 ID 不存在

**解决**：检查关联数据是否存在

### 错误：`Expected a dictionary but got value`

**原因**：提交了 ID 而非对象，但 Serializer 期望嵌套对象

**解决**：确认 Serializer 定义，是 PrimaryKeyRelatedField 还是嵌套 Serializer
