# 前端UI统一规范

## 概述

本文档定义了投标自动化系统前端UI的统一规范，确保所有页面保持一致的设计语言和用户体验。

## 1. 组件体系

### 1.1 基础组件

| 组件名 | 文件 | 说明 |
|--------|------|------|
| CrudTable | `components/CrudTable.vue` | 通用表格组件 |
| Pagination | `components/Pagination.vue` | 分页组件 |
| SearchBox | `components/SearchBox.vue` | 搜索框组件 |
| StatusBadge | `components/StatusBadge.vue` | 状态标签组件 |
| TableActions | `components/TableActions.vue` | 表格操作按钮组 |
| VirtualTable | `components/VirtualTable.vue` | 虚拟表格组件 |

### 1.2 统一页面组件

| 组件名 | 文件 | 说明 |
|--------|------|------|
| PageHeader | `components/PageHeader.vue` | 统一页面头部 |
| StatCard | `components/StatCard.vue` | 统一统计卡片 |
| StatCards | `components/StatCards.vue` | 统计卡片组 |
| SearchForm | `components/SearchForm.vue` | 统一搜索表单 |
| ConfirmDialog | `components/ConfirmDialog.vue` | 统一确认对话框 |
| PageTemplate | `components/PageTemplate.vue` | 统一页面模板 |
| SectionHeader | `components/SectionHeader.vue` | 统一卡片区块头部 |
| SidebarNav | `components/SidebarNav.vue` | 统一侧边栏导航 |
| BreadcrumbNav | `components/BreadcrumbNav.vue` | 统一面包屑导航 |

### 1.3 布局组件

| 组件名 | 文件 | 说明 |
|--------|------|------|
| Layout | `views/Layout.vue` | 主布局容器 |
| SidebarNav | `components/SidebarNav.vue` | 侧边栏导航菜单 |

## 2. 页面结构规范

### 2.1 标准页面布局

```
PageTemplate
├── PageHeader (页面标题区)
│   ├── 标题
│   └── 操作按钮
├── StatCards (统计卡片区，可选)
├── SearchForm (搜索表单区，可选)
├── 内容区 (el-table 等)
└── Pagination (分页区，可选)
```

### 2.2 PageHeader 组件规范

**使用示例：**

```vue
<PageHeader title="页面标题" subtitle="副标题说明">
  <template #actions>
    <el-button type="primary">新增</el-button>
  </template>
</PageHeader>
```

**Props：**
- `title`: 页面标题（必填）
- `subtitle`: 副标题说明
- `compact`: 紧凑模式

### 2.3 StatCards 组件规范

**使用示例：**

```vue
<StatCards :stats="[
  { value: 100, label: '总数', type: 'default', icon: 'Document' },
  { value: 50, label: '已完成', type: 'success', icon: 'Check' },
  { value: 30, label: '进行中', type: 'warning', icon: 'Clock' },
  { value: 20, label: '异常', type: 'danger', icon: 'Warning' }
]" />
```

**StatItem 类型定义：**
```ts
interface StatItem {
  value: number | string
  label: string
  type?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  icon?: string
  suffix?: string
  prefix?: string
  decimals?: number
}
```

### 2.4 SearchForm 组件规范

**使用示例：**

```vue
<SearchForm
  :default-values="{ keyword: '', status: '' }"
  @search="handleSearch"
  @reset="handleReset"
>
  <template #default="{ formData, handleChange }">
    <el-form-item label="关键词">
      <el-input v-model="formData.keyword" />
    </el-form-item>
    <el-form-item label="状态">
      <el-select v-model="formData.status">
        <el-option label="启用" value="active" />
        <el-option label="禁用" value="inactive" />
      </el-select>
    </el-form-item>
  </template>
</SearchForm>
```

### 2.5 ConfirmDialog 组件规范

**使用示例：**

```vue
<ConfirmDialog
  v-model="dialogVisible"
  title="确认删除"
  message="确定要删除该记录吗？"
  description="删除后无法恢复，请谨慎操作。"
  type="warning"
  @confirm="handleConfirm"
/>
```

**Props：**
- `modelValue`: 双向绑定显示状态
- `title`: 对话框标题
- `message`: 主要提示信息
- `description`: 详细说明
- `type`: 类型 ('warning' | 'success' | 'danger' | 'info')
- `confirmText`: 确认按钮文字
- `cancelText`: 取消按钮文字
- `loading`: 确认按钮加载状态

## 3. 样式规范

### 3.1 颜色变量

位置：`src/assets/styles/variables.scss`

```scss
$primary-color: #409EFF;
$success-color: #67C23A;
$warning-color: #E6A23C;
$danger-color: #F56C6C;
$info-color: #909399;
```

### 3.2 间距规范

```scss
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;
```

### 3.3 圆角规范

```scss
$border-radius-base: 4px;
$border-radius-small: 2px;
$border-radius-large: 8px;
```

## 4. API响应处理

### 4.1 统一响应格式

后端返回格式：
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

### 4.2 useListPage Composable

位置：`src/composables/useListPage.js`

```js
const listPage = useListPage({
  fetchApi: async (params) => {
    const res = await api.getList(params)
    return res.data
  },
  deleteApi: (id) => api.delete(id),
  defaultSearchParams: { keyword: '' },
  onDeleteSuccess: () => fetchData()
})

// 解构出的属性和方法
const {
  loading,      // 加载状态
  list,         // 列表数据
  pagination,   // 分页信息
  searchForm,   // 搜索表单
  fetchData,    // 获取数据
  handleSearch, // 搜索
  resetSearch,  // 重置搜索
  handleDelete  // 删除（带确认框）
} = listPage
```

## 5. 页面模板示例

### 5.1 标准列表页

```vue
<template>
  <div class="page-container">
    <PageHeader title="招标项目管理" subtitle="管理所有招标项目信息">
      <template #actions>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增项目
        </el-button>
      </template>
    </PageHeader>

    <StatCards :stats="statistics" />

    <SearchForm
      :default-values="searchDefaults"
      @search="handleSearch"
      @reset="handleReset"
    >
      <template #default="{ formData }">
        <el-form-item label="关键词">
          <el-input v-model="formData.keyword" placeholder="项目名称/编号" />
        </el-form-item>
      </template>
    </SearchForm>

    <div class="content-card">
      <el-table :data="list" v-loading="loading">
        <el-table-column prop="title" label="项目名称" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row.id, row.title)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
        />
      </div>
    </div>
  </div>
</template>
```

### 5.2 带弹窗的列表页

```vue
<template>
  <!-- 列表内容 -->

  <ConfirmDialog
    v-model="deleteDialogVisible"
    title="确认删除"
    :message="`确定要删除项目「${deleteTarget?.title}」吗？`"
    type="danger"
    :loading="deleteLoading"
    @confirm="confirmDelete"
  />
</template>

<script setup>
import { ref } from 'vue'
import { ConfirmDialog } from '@/components'
import { useMessage } from '@/composables'

const message = useMessage()
const deleteDialogVisible = ref(false)
const deleteLoading = ref(false)

const handleDelete = async (id, title) => {
  deleteDialogVisible.value = true
  deleteTarget.value = { id, title }
}

const confirmDelete = async () => {
  deleteLoading.value = true
  try {
    await api.delete(deleteTarget.value.id)
    message.success('删除成功')
    deleteDialogVisible.value = false
    fetchData()
  } catch (error) {
    message.error('删除失败')
  } finally {
    deleteLoading.value = false
  }
}
</script>
```

## 6. 命名规范

### 6.1 组件命名
- PascalCase：`PageHeader.vue`
- 简写避免过长：`CrudTable` 而非 `CurdTableComponent`

### 6.2 样式命名
- BEM风格：`.block__element--modifier`
- 或使用有意义的类名：`.page-header`, `.content-card`

### 6.3 变量命名
- 布尔值使用 `is`/`has`/`can` 前缀： `isLoading`, `hasPermission`
- 列表使用复数形式：`items`, `users`
- Composable返回值使用驼峰：`listPage`, `searchForm`

## 7. 状态管理

### 7.1 组件内状态
- 简单状态：`ref()`
- 响应式对象：`reactive()`
- 计算属性：`computed()`

### 7.2 Pinia Store
用于全局状态管理：
- `src/store/user.js` - 用户信息
- `src/store/constants.js` - 常量配置

### 7.3 Composable
用于跨组件逻辑复用：
- `src/composables/useListPage.js` - 列表页通用逻辑
- `src/composables/usePagination.js` - 分页逻辑
- `src/composables/useApi.js` - API调用封装

## 8. 错误处理

### 8.1 API错误处理

```js
import { useMessage } from '@/composables'

const message = useMessage()

try {
  await api.delete(id)
  message.success('删除成功')
} catch (error) {
  message.error(error.response?.data?.message || '操作失败')
}
```

### 8.2 删除确认

必须使用 `ElMessageBox.confirm` 或 `ConfirmDialog` 组件进行二次确认：

```js
await ElMessageBox.confirm(
  '确定要删除该记录吗？',
  '确认删除',
  {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }
)
```

## 9. 响应式设计

### 9.1 断点

```scss
$breakpoint-xs: 480px;
$breakpoint-sm: 768px;
$breakpoint-md: 992px;
$breakpoint-lg: 1200px;
$breakpoint-xl: 1920px;
```

### 9.2 栅格系统

使用 Element Plus 的 `el-row` 和 `el-col`：
- `<el-col :xs="24" :sm="12" :md="8" :lg="6">`

## 10. 可访问性

### 10.1 必填字段
- 使用 `aria-required` 标记

### 10.2 键盘导航
- Tab 键顺序合理
- 支持 Enter 确认

### 10.3 屏幕阅读
- 使用语义化标签
- 补充 aria-label

## 11. 导航规范

### 11.1 SidebarNav 侧边栏导航

使用统一的 `SidebarNav` 组件：

```vue
<SidebarNav :is-collapse="isCollapse" :unread-count="unreadCount" />
```

**功能特性：**
- 自动高亮当前激活菜单
- 支持折叠/展开
- 未读消息数量徽章
- 统一的图标和样式

### 11.2 SectionHeader 卡片区块头部

用于 el-card 等容器的内部区块头部：

```vue
<SectionHeader title="企业列表" icon="OfficeBuilding">
  <template #actions>
    <el-button size="small">操作按钮</el-button>
  </template>
</SectionHeader>
```

**Props：**
- `title`: 区块标题（必填）
- `icon`: Element Plus 图标名称
- `compact`: 紧凑模式

### 11.3 BreadcrumbNav 面包屑导航

用于页面内的路径导航：

```vue
<BreadcrumbNav :items="[
  { title: '首页', path: '/' },
  { title: '企业信息', path: '/company' },
  { title: '企业详情' }
]" />
```

### 11.4 页面头部样式规范

所有页面头部应使用统一的渐变背景样式：

```scss
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.header-title {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.page-subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
```
