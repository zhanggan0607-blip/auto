# 天齐SSTCP — 产品UI标准文档

> 版本：1.0 | 更新日期：2026-04-23 | 适用范围：天齐SSTCP前端及所有衍生项目

***

## 目录

1. [设计原则](#1-设计原则)
2. [色彩系统](#2-色彩系统)
3. [字体规范](#3-字体规范)
4. [图标规范](#4-图标规范)
5. [间距与布局](#5-间距与布局)
6. [圆角与阴影](#6-圆角与阴影)
7. [组件规范](#7-组件规范)
8. [导航规范](#8-导航规范)
9. [页面模板](#9-页面模板)
10. [动效规范](#10-动效规范)
11. [暗色侧边栏](#11-暗色侧边栏)
12. [工具类速查](#12-工具类速查)
13. [实施指南](#13-实施指南)

***

## 1. 设计原则

### 1.1 品牌调性

**专业、高效、可信赖** — 天齐AI投标平台面向企业级用户，视觉风格需传达专业商务感，同时通过品牌渐变和微动效体现科技感与活力。

### 1.2 设计哲学

| 原则        | 说明                                                                    |
| --------- | --------------------------------------------------------------------- |
| **一致性优先** | 相同交互场景使用相同的视觉表现，减少用户认知负担                                              |
| **内容驱动**  | 界面服务于内容，避免过度装饰，保持信息密度与留白的平衡                                           |
| **渐进反馈**  | 操作反馈分层级：微交互（hover）→ 状态变更（active/selected）→ 结果通知（message/notification） |
| **可复用性**  | 所有设计决策以 CSS 变量形式定义，确保跨项目一键复用                                          |

### 1.3 视觉风格关键词

- **色系**：Slate 中性色 + 蓝色主色 = 现代商务
- **圆角**：中等圆角（8px 为主），温和但不失严谨
- **阴影**：极轻阴影，悬停时加深，营造层次但不喧宾夺主
- **渐变**：品牌渐变 `135deg, #1A56DB → #3B82F6` 贯穿核心元素

***

## 2. 色彩系统

### 2.1 主色（Primary）

主色 `#1A56DB` 是品牌的核心识别色，用于主要操作、链接、选中态等。

| 层级      | 色值            | CSS 变量                    | 用途                |
| ------- | ------------- | ------------------------- | ----------------- |
| Dark    | `#1E40AF`     | `--color-primary-dark`    | 深色强调、渐变终点         |
| Base    | `#1A56DB`     | `--color-primary`         | 主按钮、链接、选中态        |
| Light   | `#3B82F6`     | `--color-primary-light`   | 悬停态、渐变终点          |
| Lighter | `#60A5FA`     | `--color-primary-lighter` | 次级强调              |
| 100     | `#DBEAFE`     | `--color-primary-100`     | 浅色背景              |
| 50      | `#EFF6FF`     | `--color-primary-50`      | 极浅背景、标签底色         |
| RGB     | `26, 86, 219` | `--color-primary-rgb`     | 用于 `rgba()` 透明度组合 |

**品牌渐变**：

```css
background: var(--brand-gradient);
/* 等价于 */
background: linear-gradient(135deg, #1A56DB, #3B82F6);
```

**品牌悬停渐变**：

```css
background: var(--brand-hover-gradient);
/* 等价于 */
background: linear-gradient(135deg, #1E40AF, #1A56DB);
```

### 2.2 功能色

#### 成功色（Success）

| 层级    | 色值            | CSS 变量                  | 用途      |
| ----- | ------------- | ----------------------- | ------- |
| Dark  | `#15803D`     | `--color-success-dark`  | 成功文字    |
| Base  | `#16A34A`     | `--color-success`       | 成功状态    |
| Light | `#22C55E`     | `--color-success-light` | 成功悬停    |
| 50    | `#DCFCE7`     | `--color-success-50`    | 成功背景    |
| RGB   | `22, 163, 74` | `--color-success-rgb`   | rgba 组合 |

#### 警告色（Warning）

| 层级    | 色值        | CSS 变量                  | 用途   |
| ----- | --------- | ----------------------- | ---- |
| Dark  | `#C2410C` | `--color-warning-dark`  | 警告文字 |
| Base  | `#EA580C` | `--color-warning`       | 警告状态 |
| Light | `#F97316` | `--color-warning-light` | 警告悬停 |
| 50    | `#FFF7ED` | `--color-warning-50`    | 警告背景 |

#### 危险色（Danger）

| 层级    | 色值        | CSS 变量                 | 用途        |
| ----- | --------- | ---------------------- | --------- |
| Dark  | `#B91C1C` | `--color-danger-dark`  | 危险文字      |
| Base  | `#DC2626` | `--color-danger`       | 危险状态、删除操作 |
| Light | `#DC2626` | `--color-danger-light` | 危险悬停      |
| 50    | `#FEE2E2` | `--color-danger-50`    | 危险背景      |

#### 信息色（Info）

| 层级    | 色值        | CSS 变量               | 用途   |
| ----- | --------- | -------------------- | ---- |
| Dark  | `#1D4ED8` | `--color-info-dark`  | 信息文字 |
| Base  | `#2563EB` | `--color-info`       | 信息状态 |
| Light | `#3B82F6` | `--color-info-light` | 信息悬停 |
| 50    | `#DBEAFE` | `--color-info-50`    | 信息背景 |

### 2.3 中性色（文字）

| 层级  | 色值        | CSS 变量                     | 用途         |
| --- | --------- | -------------------------- | ---------- |
| 主要  | `#1E293B` | `--color-text-primary`     | 标题、重要文字    |
| 常规  | `#334155` | `--color-text-regular`     | 正文内容       |
| 次要  | `#64748B` | `--color-text-secondary`   | 辅助说明、时间戳   |
| 三级  | `#94A3B8` | `--color-text-tertiary`    | 禁用态文字、占位图标 |
| 占位符 | `#CBD5E1` | `--color-text-placeholder` | 输入框占位文字    |
| 禁用  | `#E2E8F0` | `--color-text-disabled`    | 禁用态文字      |

### 2.4 边框色

| 层级 | 色值                     | CSS 变量                   | 用途         |
| -- | ---------------------- | ------------------------ | ---------- |
| 基础 | `#E2E8F0`              | `--color-border`         | 输入框边框、分割线  |
| 浅  | `#F1F5F9`              | `--color-border-light`   | 卡片内分割、表格行线 |
| 更浅 | `#F8FAFC`              | `--color-border-lighter` | 卡片外边框、表格底边 |
| 聚焦 | `var(--color-primary)` | `--color-border-focus`   | 输入框聚焦边框    |

### 2.5 背景色

| 层级 | 色值                        | CSS 变量               | 用途       |
| -- | ------------------------- | -------------------- | -------- |
| 页面 | `#F1F5F9`                 | `--color-bg-page`    | 页面底色     |
| 基础 | `#F1F5F9`                 | `--color-bg-base`    | 表格头背景    |
| 白色 | `#FFFFFF`                 | `--color-bg-white`   | 卡片、对话框背景 |
| 遮罩 | `rgba(15, 23, 42, 0.5)`   | `--color-bg-overlay` | 弹窗遮罩层    |
| 悬停 | `#F1F5F9`                 | `--color-bg-hover`   | 表格行悬停    |
| 激活 | `rgba(26, 86, 219, 0.08)` | `--color-bg-active`  | 选中行、激活项  |

### 2.6 色彩使用规则

**✅ 正确做法**：

```css
/* 使用 CSS 变量 */
color: var(--color-text-primary);
background: var(--color-primary-50);
border: 1px solid var(--color-border);

/* 使用 RGB 变量组合透明度 */
background: rgba(var(--color-primary-rgb), 0.08);
```

**❌ 错误做法**：

```css
/* 硬编码色值 */
color: #1E293B;
background: #EFF6FF;
border: 1px solid #E2E8F0;

/* 自行计算透明度 */
background: rgba(26, 86, 219, 0.08);
```

***

## 3. 字体规范

### 3.1 字体栈

```css
font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

**优先级说明**：

1. `Inter` — 西文主字体（需加载）
2. `PingFang SC` — macOS 中文回退
3. `Microsoft YaHei` — Windows 中文回退
4. 系统字体 — 最终回退

**等宽字体**（代码块、日志输出）：

```css
font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
```

### 3.2 字号阶梯

| 级别   | 大小   | CSS 变量             | 用途        |
| ---- | ---- | ------------------ | --------- |
| xs   | 11px | `--font-size-xs`   | 极小标注、角标   |
| sm   | 12px | `--font-size-sm`   | 表格内容、辅助文字 |
| base | 13px | `--font-size-base` | 正文基础字号    |
| md   | 14px | `--font-size-md`   | 常规内容、菜单项  |
| lg   | 15px | `--font-size-lg`   | 小标题       |
| xl   | 16px | `--font-size-xl`   | 页面标题      |
| 2xl  | 20px | `--font-size-2xl`  | 区块标题      |
| 3xl  | 24px | `--font-size-3xl`  | 大标题       |
| 4xl  | 30px | `--font-size-4xl`  | 数据展示、统计数字 |

### 3.3 字重

| 级别 | 值   | CSS 变量                   | 用途        |
| -- | --- | ------------------------ | --------- |
| 常规 | 400 | `--font-weight-normal`   | 正文内容      |
| 中等 | 500 | `--font-weight-medium`   | 表格头、标签    |
| 半粗 | 600 | `--font-weight-semibold` | 页面标题、卡片标题 |
| 粗体 | 700 | `--font-weight-bold`     | 数据数字、强调   |

### 3.4 行高

```css
line-height: 1.6; /* 全局默认 */
```

### 3.5 字体渲染优化

```css
html {
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
```

***

## 4. 图标规范

### 4.1 图标库

项目使用 **@element-plus/icons-vue** 作为唯一图标库，不引入其他第三方图标库。

### 4.2 图标注册

在 `main.js` 中全局注册常用图标（37个）：

```javascript
import { Upload, Delete, View, Download, Star, CircleCheck, CircleClose,
  ArrowDown, Document, Camera, Connection, Refresh, Edit, Plus,
  OfficeBuilding, Location, Select, Clock, Loading, Timer, Trophy,
  Warning, Check, DataBoard, Key, Collection, Folder, TrendCharts,
  Monitor, VideoPlay, Setting, Bell, User, CirclePlus, SwitchButton,
  Expand, Fold } from '@element-plus/icons-vue'
```

### 4.3 使用方式

**方式一：全局注册图标（推荐）**

```vue
<el-icon><Plus /></el-icon>
<el-icon><Refresh /></el-icon>
```

**方式二：动态组件（菜单图标）**

```vue
<el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
```

**方式三：按需导入（非全局注册的图标）**

```vue
<script setup>
import { ArrowLeft, WarningFilled } from '@element-plus/icons-vue'
</script>
<template>
  <el-icon><ArrowLeft /></el-icon>
</template>
```

### 4.4 图标尺寸规范

| 场景     | 尺寸   | 方式                                                      |
| ------ | ---- | ------------------------------------------------------- |
| 按钮内图标  | 继承字号 | `<el-button><el-icon><Plus /></el-icon> 新增</el-button>` |
| 导航菜单图标 | 18px | `.nav-icon { font-size: 18px; }`                        |
| 独立操作图标 | 16px | `<el-icon :size="16"><Refresh /></el-icon>`             |
| 空状态图标  | 56px | `.empty-icon { font-size: 56px; }`                      |

### 4.5 常用图标映射表

| 用途 | 图标名                         | 用途 | 图标名                         |
| -- | --------------------------- | -- | --------------------------- |
| 新增 | `Plus` / `CirclePlus`       | 刷新 | `Refresh`                   |
| 搜索 | `Search`                    | 删除 | `Delete`                    |
| 编辑 | `Edit`                      | 查看 | `View`                      |
| 下载 | `Download`                  | 上传 | `Upload`                    |
| 通知 | `Bell`                      | 用户 | `User`                      |
| 设置 | `Setting`                   | 成功 | `CircleCheck` / `Check`     |
| 失败 | `CircleClose`               | 警告 | `Warning` / `WarningFilled` |
| 加载 | `Loading`                   | 时间 | `Clock` / `Timer`           |
| 数据 | `DataBoard` / `TrendCharts` | 监控 | `Monitor`                   |
| 播放 | `VideoPlay`                 | 文档 | `Document` / `Folder`       |
| 折叠 | `Expand` / `Fold`           | 位置 | `Location`                  |
| 建筑 | `OfficeBuilding`            | 密钥 | `Key`                       |

***

## 5. 间距与布局

### 5.1 间距体系

项目采用 **2px 基数** 的 9 级间距系统：

```
2px → 4px → 8px → 12px → 16px → 20px → 24px → 32px → 48px
3xs   xxs   xs    sm     md     lg     xl     2xl    3xl
```

| 级别  | 大小   | CSS 变量          | 典型用途        |
| --- | ---- | --------------- | ----------- |
| 3xs | 2px  | `--spacing-3xs` | 微调间距        |
| xxs | 4px  | `--spacing-xxs` | 图标与文字间距     |
| xs  | 8px  | `--spacing-xs`  | 紧凑元素间距      |
| sm  | 12px | `--spacing-sm`  | 按钮组间距、表单项间距 |
| md  | 16px | `--spacing-md`  | 卡片内间距、列表项间距 |
| lg  | 20px | `--spacing-lg`  | 页面内边距、卡片间距  |
| xl  | 24px | `--spacing-xl`  | 区块间距        |
| 2xl | 32px | `--spacing-2xl` | 大区块间距       |
| 3xl | 48px | `--spacing-3xl` | 空状态内边距      |

### 5.2 布局尺寸

| 元素      | 尺寸    | CSS 变量                      |
| ------- | ----- | --------------------------- |
| 侧边栏展开宽度 | 240px | `--sidebar-width`           |
| 侧边栏折叠宽度 | 64px  | `--sidebar-collapsed-width` |
| 顶部导航高度  | 56px  | `--header-height`           |

### 5.3 响应式断点

| 断点名 | 宽度     | SCSS 变量          | 典型设备      |
| --- | ------ | ---------------- | --------- |
| xs  | 480px  | `$breakpoint-xs` | 小屏手机      |
| sm  | 640px  | `$breakpoint-sm` | 大屏手机      |
| md  | 768px  | `$breakpoint-md` | 平板竖屏      |
| lg  | 1024px | `$breakpoint-lg` | 平板横屏/小笔记本 |
| xl  | 1280px | `$breakpoint-xl` | 桌面显示器     |

**使用方式**：

```scss
@media (max-width: $breakpoint-md) {
  .sidebar { display: none; }
}
```

### 5.4 Z-Index 层级

| 层级   | 值   | CSS 变量               | 用途            |
| ---- | --- | -------------------- | ------------- |
| 下拉菜单 | 100 | `--z-dropdown`       | el-dropdown   |
| 粘性定位 | 200 | `--z-sticky`         | sticky header |
| 固定定位 | 300 | `--z-fixed`          | fixed 面板      |
| 遮罩层  | 400 | `--z-modal-backdrop` | dialog 遮罩     |
| 模态框  | 500 | `--z-modal`          | dialog        |
| 弹出层  | 600 | `--z-popover`        | popover       |
| 提示框  | 700 | `--z-tooltip`        | tooltip       |
| 通知   | 800 | `--z-notification`   | notification  |

***

## 6. 圆角与阴影

### 6.1 圆角体系

| 级别   | 大小     | CSS 变量          | 用途         |
| ---- | ------ | --------------- | ---------- |
| xs   | 4px    | `--radius-xs`   | 小标签、徽章     |
| sm   | 6px    | `--radius-sm`   | 小按钮、标签、输入框 |
| md   | 8px    | `--radius-md`   | 按钮、输入框、菜单项 |
| lg   | 12px   | `--radius-lg`   | 卡片、搜索框     |
| xl   | 16px   | `--radius-xl`   | 对话框        |
| 2xl  | 20px   | `--radius-2xl`  | 大对话框、胶囊按钮  |
| full | 9999px | `--radius-full` | 头像、圆形按钮    |

### 6.2 阴影体系

| 级别     | 值                                                        | CSS 变量            | 用途       |
| ------ | -------------------------------------------------------- | ----------------- | -------- |
| xs     | `0 1px 2px rgba(0,0,0,0.04)`                             | `--shadow-xs`     | 搜索框、轻量卡片 |
| sm     | `0 2px 4px rgba(0,0,0,0.06)`                             | `--shadow-sm`     | 常规卡片     |
| md     | `0 4px 8px rgba(0,0,0,0.08)`                             | `--shadow-md`     | 悬停态卡片    |
| lg     | `0 8px 16px rgba(0,0,0,0.1)`                             | `--shadow-lg`     | 弹出层      |
| xl     | `0 12px 24px rgba(0,0,0,0.12)`                           | `--shadow-xl`     | 对话框      |
| card   | `0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)` | `--shadow-card`   | 卡片默认态    |
| header | `0 1px 3px rgba(0,0,0,0.04)`                             | `--shadow-header` | 顶部导航     |

### 6.3 阴影使用规则

- **默认态**：使用 `--shadow-card` 或 `--shadow-xs`，极轻阴影
- **悬停态**：升级到 `--shadow-md`，同时配合 `transform: translateY(-2px)`
- **弹出层**：使用 `--shadow-lg` 或 `--shadow-xl`

```css
.card {
  box-shadow: var(--shadow-card);
  transition: box-shadow var(--transition-base), transform var(--transition-base);
}
.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

***

## 7. 组件规范

### 7.1 按钮（Button）

#### 尺寸与间距

| 尺寸 | 圆角  | 垂直内边距 | 水平内边距 | 字号   |
| -- | --- | ----- | ----- | ---- |
| 默认 | 8px | 10px  | 20px  | 14px |
| 中号 | 8px | —     | —     | 14px |
| 小号 | 6px | —     | —     | 12px |

#### 按钮类型与使用场景

| 类型   | Element Plus type     | 用途           |
| ---- | --------------------- | ------------ |
| 主要操作 | `type="primary"`      | 表单提交、新建、保存   |
| 次要操作 | 默认（无 type）            | 取消、返回        |
| 文字链接 | `type="primary" link` | 表格操作列（查看、编辑） |
| 危险操作 | `type="danger" link`  | 表格操作列（删除）    |

#### 品牌渐变按钮

用于页面级主要操作（如"新增"按钮），比普通 primary 按钮更醒目：

```vue
<el-button type="primary" class="primary-action-btn">
  <el-icon><Plus /></el-icon> 新增
</el-button>
```

```css
.primary-action-btn {
  background: var(--brand-gradient);
  border: none;
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}
.primary-action-btn:hover {
  background: var(--brand-hover-gradient);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(26, 86, 219, 0.3);
}
```

#### 按钮组规范

```vue
<!-- 操作区按钮组 -->
<div style="display: flex; gap: var(--spacing-sm);">
  <el-button type="primary" class="primary-action-btn">
    <el-icon><Plus /></el-icon> 新增
  </el-button>
  <el-button @click="handleExport">
    <el-icon><Download /></el-icon> 导出
  </el-button>
</div>
```

#### 表格操作列按钮

```vue
<el-table-column label="操作" width="150" fixed="right">
  <template #default="{ row }">
    <el-button type="primary" link @click="viewDetail(row)">查看</el-button>
    <el-button type="primary" link @click="editRow(row)">编辑</el-button>
    <el-button type="danger" link @click="deleteRow(row)">删除</el-button>
  </template>
</el-table-column>
```

### 7.2 表单（Form）

#### 基础结构

```vue
<el-form ref="formRef" :model="formData" :rules="formRules" label-width="140px">
  <el-form-item label="项目名称" prop="name">
    <el-input v-model="formData.name" placeholder="请输入项目名称" />
  </el-form-item>
  <el-form-item label="类型" prop="type">
    <el-select v-model="formData.type" filterable style="width: 100%">
      <el-option v-for="item in options" :key="item.value"
        :label="item.label" :value="item.value" />
    </el-select>
  </el-form-item>
</el-form>
```

#### 表单规范

| 规范项      | 要求                                                     |
| -------- | ------------------------------------------------------ |
| label 宽度 | `label-width="140px"`（默认）                              |
| 下拉框      | 必须加 `filterable`，宽度 `width: 100%`                      |
| 日期选择器    | 宽度 `width: 100%`                                       |
| 验证规则     | 必须通过 `:rules` 绑定                                       |
| 搜索表单     | `margin-bottom: 0`（通过 `.search-form .el-form-item` 覆盖） |

#### 输入框样式

```css
/* Element Plus 已通过 element-variables.scss 覆盖 */
$--input-border-radius-base: 8px;
$--input-border-color: #E2E8F0;
$--input-border-color-hover: #1A56DB;
$--input-focus-border-color: #1A56DB;
```

### 7.3 卡片（Card）

#### 使用场景

| 场景     | shadow 属性        | 说明        |
| ------ | ---------------- | --------- |
| 搜索区域   | `shadow="never"` | 无阴影，用边框代替 |
| 数据表格区域 | `shadow="never"` | 无阴影，用边框代替 |
| 统计卡片   | `shadow="hover"` | 悬停时显示阴影   |
| 独立内容块  | 默认               | 始终显示阴影    |

#### 卡片样式

```css
/* 搜索/表格区域 */
.search-card, .table-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  border: 1px solid var(--color-border-lighter);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

/* 统计卡片 */
.stat-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border-lighter);
  transition: all var(--transition-base);
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

#### 卡片圆角

```css
$--card-border-radius-base: 12px;
$--card-border-color: #E2E8F0;
```

### 7.4 表格（Table）

#### 基础结构

```vue
<el-table :data="list" v-loading="loading" stripe size="small">
  <el-table-column type="selection" width="55" />
  <el-table-column prop="title" label="项目名称" min-width="250" show-overflow-tooltip />
  <el-table-column label="操作" width="150" fixed="right">
    <template #default="{ row }">
      <el-button type="primary" link @click="edit(row)">编辑</el-button>
      <el-button type="danger" link @click="del(row)">删除</el-button>
    </template>
  </el-table-column>
</el-table>
```

#### 表格规范

| 规范项 | 要求                            |
| --- | ----------------------------- |
| 尺寸  | `size="small"`                |
| 斑马纹 | `stripe`                      |
| 加载态 | `v-loading="loading"`         |
| 长文本 | `show-overflow-tooltip`       |
| 操作列 | `fixed="right"`               |
| 列宽  | 内容列用 `min-width`，操作列用 `width` |
| 容器  | 包裹在 `.data-table` 类中          |

#### 表格样式覆盖

```css
.data-table .el-table th {
  background-color: var(--color-bg-base) !important;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.data-table .el-table td {
  border-bottom-color: var(--color-border-lighter);
  font-size: var(--font-size-sm);
}
.data-table .el-table tr:hover > td {
  background-color: var(--color-bg-hover);
}
```

#### 表格 Element Plus 变量

```scss
$--table-border-color: #F1F5F9;
$--table-header-background: #F8FAFC;
$--table-row-hover-background: #F1F5F9;
$--table-current-row-background: rgba(26, 86, 219, 0.04);
```

### 7.5 对话框（Dialog）

#### 基础结构

```vue
<el-dialog v-model="dialogVisible" :title="title" width="600px"
  :close-on-click-modal="false">
  <el-form>...</el-form>
  <template #footer>
    <el-button @click="dialogVisible = false">取消</el-button>
    <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
  </template>
</el-dialog>
```

#### 对话框规范

| 规范项  | 要求                                      |
| ---- | --------------------------------------- |
| 圆角   | 16px（通过 `$--dialog-border-radius-base`） |
| 内边距  | 24px（通过 `$--dialog-padding-primary`）    |
| 阻止误关 | `:close-on-click-modal="false"`         |
| 宽度   | 表单类 600px，详情类 800px，全屏类 90%             |
| 底部按钮 | 取消（左）+ 确定（右），确定按钮 loading 态             |

### 7.6 分页（Pagination）

```vue
<el-pagination
  v-model:current-page="page"
  v-model:page-size="pageSize"
  :total="total"
  :page-sizes="[10, 20, 50, 100]"
  layout="total, sizes, prev, pager, next, jumper"
  :background="true"
  size="small"
/>
```

分页容器：

```css
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border-lighter);
}
```

### 7.7 标签（Tag）

#### 状态标签

```css
.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-sm);
}
.status-tag.status-pending {
  background-color: var(--color-warning-50);
  color: var(--color-warning-dark);
  border: 1px solid rgba(234, 88, 12, 0.2);
}
.status-tag.status-submitted {
  background-color: var(--color-primary-50);
  color: var(--color-primary);
  border: 1px solid rgba(26, 86, 219, 0.2);
}
.status-tag.status-won {
  background-color: var(--color-success-50);
  color: var(--color-success-dark);
  border: 1px solid rgba(22, 163, 74, 0.2);
}
.status-tag.status-lost {
  background-color: var(--color-danger-50);
  color: var(--color-danger-dark);
  border: 1px solid rgba(220, 38, 38, 0.2);
}
```

#### Element Plus Tag 变量

```scss
$--tag-border-radius: 6px;
$--tag-padding-vertical: 0;
$--tag-padding-horizontal: 10px;
```

### 7.8 下拉菜单（Dropdown）

```scss
$--dropdown-menu-box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
$--dropdown-menuItem-hover-fill: rgba(26, 86, 219, 0.04);
$--dropdown-menuItem-hover-color: #1A56DB;
```

***

## 8. 导航规范

### 8.1 侧边栏导航

#### 布局结构

```
┌──────────────────────┐
│  Logo区 (品牌渐变背景) │  高度: 56px
├──────────────────────┤
│                      │
│  导航菜单区           │  可滚动
│  ├── 首页            │
│  ├── 招标采集 ▾       │
│  │   ├── 定时采集     │
│  │   ├── 关键词管理   │
│  │   └── 采集统计     │
│  ├── 投标管理 ▾       │
│  │   ├── 招标项目     │
│  │   └── 投标记录     │
│  └── ...             │
│                      │
├──────────────────────┤
│  服务状态指示器        │  底部固定
│  消息通知入口          │
└──────────────────────┘
```

#### 交互规范

| 交互     | 行为                                              |
| ------ | ----------------------------------------------- |
| 展开/折叠  | 240px ↔ 64px，过渡 `0.25s cubic-bezier`            |
| 菜单悬停   | 背景 `--sidebar-hover-bg`，文字变亮                    |
| 菜单激活   | 左侧蓝色指示条 `::before`，背景 `--sidebar-active-bg`     |
| 子菜单展开  | `<transition name="submenu-expand">`，Y轴位移 + 透明度 |
| 折叠态子菜单 | `el-tooltip` 显示菜单名                              |

### 8.2 面包屑导航

```vue
<el-breadcrumb separator="/">
  <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
  <el-breadcrumb-item>当前页面</el-breadcrumb-item>
</el-breadcrumb>
```

### 8.3 顶部导航

```
┌─────────────────────────────────────────────────┐
│  ☰ 折叠按钮 │ 面包屑 │          🔔 通知 │ 👤 用户 ▾ │
└─────────────────────────────────────────────────┘
```

- 高度：56px（`--header-height`）
- 定位：`position: sticky; top: 0`
- 阴影：`--shadow-header`
- 右侧：通知图标（带 `el-badge`）+ 用户下拉菜单

***

## 9. 页面模板

### 9.1 列表页模板

最常用的页面模式，适用于招标列表、投标列表、用户管理等。

```
┌──────────────────────────────────────────────┐
│  PageHeader (标题 + 操作按钮)                  │
├──────────────────────────────────────────────┤
│  SearchForm (搜索/筛选条件)                    │
├──────────────────────────────────────────────┤
│  CrudTable (数据表格)                         │
│  ├── 批量操作栏                               │
│  ├── el-table (stripe, small, v-loading)      │
│  └── PaginationWrapper (分页)                 │
└──────────────────────────────────────────────┘
```

**代码骨架**：

```vue
<template>
  <div class="page-container">
    <PageHeader title="页面标题">
      <template #actions>
        <el-button type="primary" class="primary-action-btn">
          <el-icon><Plus /></el-icon> 新增
        </el-button>
      </template>
    </PageHeader>

    <div class="search-form">
      <SearchForm :fields="searchFields" @search="handleSearch" @reset="handleReset" />
    </div>

    <div class="data-table">
      <CrudTable :data="list" :columns="columns" :loading="loading"
        @selection-change="handleSelectionChange">
        <template #toolbar>
          <el-button type="danger" :disabled="!selectedIds.length"
            @click="handleBatchDelete">批量删除</el-button>
        </template>
      </CrudTable>
      <div class="pagination-wrapper">
        <el-pagination ... />
      </div>
    </div>
  </div>
</template>
```

### 9.2 仪表盘模板

适用于首页、自动化工作台等。

```
┌──────────────────────────────────────────────┐
│  PageHeader (标题)                            │
├──────────┬──────────┬──────────┬─────────────┤
│ StatCard │ StatCard │ StatCard │ StatCard    │
├──────────┴──────────┴──────────┴─────────────┤
│  el-row                                       │
│  ├── el-col :span="12" │ 图表/列表卡片        │
│  └── el-col :span="12" │ 图表/列表卡片        │
└──────────────────────────────────────────────┘
```

**统计卡片交错动画**：

```vue
<el-col :span="6" v-for="(stat, index) in stats" :key="stat.key"
  :style="{ animationDelay: `${index * 0.1}s` }">
  <StatCard v-bind="stat" />
</el-col>
```

### 9.3 详情页模板

适用于招标详情、投标详情等。

```
┌──────────────────────────────────────────────┐
│  ← 返回列表  │  页面标题  │  操作按钮         │
├──────────────────────────────────────────────┤
│  基本信息卡片 (el-descriptions)               │
├──────────────────────────────────────────────┤
│  详细内容卡片 (多个)                          │
└──────────────────────────────────────────────┘
```

### 9.4 表单页模板

适用于创建采集计划、编辑配置等。

```
┌──────────────────────────────────────────────┐
│  ← 返回  │  页面标题                          │
├──────────────────────────────────────────────┤
│  el-form (label-width="140px")               │
│  ├── 基本信息区块                             │
│  ├── 详细配置区块                             │
│  └── 底部操作栏 (取消 + 保存)                  │
└──────────────────────────────────────────────┘
```

### 9.5 全屏页模板

适用于登录、注册、404等。

```vue
<template>
  <div class="fullscreen-page">
    <!-- 不使用 Layout 包裹 -->
  </div>
</template>
```

路由配置中不使用 `Layout` 组件作为父级。

***

## 10. 动效规范

### 10.1 过渡时间

| 级别 | 时长                                       | CSS 变量                | 用途        |
| -- | ---------------------------------------- | --------------------- | --------- |
| 快速 | 0.15s ease                               | `--transition-fast`   | 颜色变化、小元素  |
| 基础 | 0.2s ease                                | `--transition-base`   | 大多数交互过渡   |
| 慢速 | 0.3s ease                                | `--transition-slow`   | 页面切换、复杂动画 |
| 弹跳 | 0.3s cubic-bezier(0.68, -0.2, 0.32, 1.2) | `--transition-bounce` | 特殊强调动效    |

### 10.2 Vue Transition 组件

| 过渡名              | 效果          | 使用场景              |
| ---------------- | ----------- | ----------------- |
| `fade`           | 透明度淡入淡出     | Logo 文字显隐         |
| `page`           | 向上滑出 + 向下滑入 | 页面切换（router-view） |
| `submenu-expand` | Y轴位移 + 透明度  | 侧边栏子菜单展开          |
| `viewer-fade`    | 透明度         | 图片查看器开关           |
| `viewer-slide`   | 缩放 + 透明度    | 图片切换              |

**page 过渡定义**：

```css
.page-enter-active, .page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-8px); }
```

### 10.3 CSS @keyframes 动画

| 动画名            | 效果        | 用途     |
| -------------- | --------- | ------ |
| `fadeInUp`     | 从下方8px淡入  | 页面容器入场 |
| `fadeIn`       | 透明度淡入     | 通用     |
| `slideInLeft`  | 从左16px滑入  | 侧边栏    |
| `slideInRight` | 从右16px滑入  | 侧边栏    |
| `scaleIn`      | 从0.98缩放淡入 | 弹窗     |
| `shimmer`      | 骨架屏闪光     | 加载态    |
| `float`        | 上下8px浮动   | 空状态图标  |
| `pulse`        | 脉冲闪烁      | 状态指示灯  |
| `rotate`       | 360°旋转    | 加载图标   |
| `typing`       | 打字机效果     | AI回复   |

### 10.4 交互动画规范

**悬停效果**：

```css
/* 卡片悬停 */
&:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 按钮悬停 */
&:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(26, 86, 219, 0.3);
}

/* 图标悬停 */
&:hover {
  transform: scale(1.05);
}
```

**列表交错动画**：

```vue
<el-col :style="{ animationDelay: `${index * 0.05}s` }">
<!-- 或 -->
<el-col :style="{ animationDelay: `${index * 0.1}s` }">
```

**加载旋转**：

```vue
<el-icon class="is-loading"><Loading /></el-icon>
```

### 10.5 动效使用规则

- **✅ 使用 CSS 变量**：`transition: all var(--transition-base)`
- **❌ 硬编码时长**：`transition: all 0.2s ease`
- **✅ 悬停配合阴影加深**：`box-shadow` 升级 + `translateY`
- **❌ 仅改变颜色**：悬停反馈应包含位移或阴影变化
- **✅ 列表项交错入场**：`animationDelay` 递增
- **❌ 所有元素同时入场**：缺乏节奏感

***

## 11. 暗色侧边栏

侧边栏采用独立的深色主题，与浅色内容区形成对比。

### 11.1 侧边栏色板

| 元素   | 色值                          | CSS 变量                    |
| ---- | --------------------------- | ------------------------- |
| 背景   | `#0F172A`                   | `--sidebar-bg`            |
| 浅背景  | `#1E293B`                   | `--sidebar-bg-light`      |
| 文字   | `#94A3B8`                   | `--sidebar-text`          |
| 激活文字 | `#FFFFFF`                   | `--sidebar-text-active`   |
| 悬停背景 | `#1E293B`                   | `--sidebar-hover-bg`      |
| 激活背景 | `rgba(59, 130, 246, 0.15)`  | `--sidebar-active-bg`     |
| 激活边框 | `#3B82F6`                   | `--sidebar-active-border` |
| 分隔线  | `rgba(255, 255, 255, 0.06)` | `--sidebar-divider`       |

### 11.2 Logo 区

```css
.logo-area {
  background: var(--brand-gradient);
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-lg);
}
```

### 11.3 深色渐变

```css
.gradient-dark {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
}
```

***

## 12. 工具类速查

### 12.1 文字颜色

| 类名              | 等价 CSS                               |
| --------------- | ------------------------------------ |
| `.text-primary` | `color: var(--color-primary)`        |
| `.text-success` | `color: var(--color-success)`        |
| `.text-warning` | `color: var(--color-warning)`        |
| `.text-danger`  | `color: var(--color-danger)`         |
| `.text-info`    | `color: var(--color-info)`           |
| `.text-muted`   | `color: var(--color-text-secondary)` |

### 12.2 文字对齐

| 类名             | 等价 CSS               |
| -------------- | -------------------- |
| `.text-center` | `text-align: center` |
| `.text-left`   | `text-align: left`   |
| `.text-right`  | `text-align: right`  |

### 12.3 间距

| 类名       | 等价 CSS                |
| -------- | --------------------- |
| `.mt-sm` | `margin-top: 12px`    |
| `.mt-md` | `margin-top: 16px`    |
| `.mt-lg` | `margin-top: 24px`    |
| `.mb-sm` | `margin-bottom: 12px` |
| `.mb-md` | `margin-bottom: 16px` |
| `.mb-lg` | `margin-bottom: 24px` |

### 12.4 Flex 布局

| 类名              | 等价 CSS                                                               |
| --------------- | -------------------------------------------------------------------- |
| `.flex`         | `display: flex`                                                      |
| `.flex-center`  | `display: flex; align-items: center; justify-content: center`        |
| `.flex-between` | `display: flex; align-items: center; justify-content: space-between` |
| `.flex-1`       | `flex: 1`                                                            |

### 12.5 文字截断

| 类名            | 等价 CSS |
| ------------- | ------ |
| `.ellipsis`   | 单行截断   |
| `.ellipsis-2` | 2行截断   |
| `.ellipsis-3` | 3行截断   |

### 12.6 特效类

| 类名                  | 效果     |
| ------------------- | ------ |
| `.skeleton`         | 骨架屏闪光  |
| `.glass`            | 毛玻璃效果  |
| `.gradient-primary` | 品牌渐变背景 |
| `.gradient-dark`    | 深色渐变背景 |
| `.btn-primary`      | 品牌渐变按钮 |

### 12.7 容器类

| 类名                    | 用途                       |
| --------------------- | ------------------------ |
| `.page-container`     | 页面容器（padding + fadeInUp） |
| `.page-header`        | 页面标题栏                    |
| `.card`               | 通用卡片                     |
| `.search-form`        | 搜索表单容器                   |
| `.data-table`         | 数据表格容器                   |
| `.pagination-wrapper` | 分页容器                     |
| `.status-tag`         | 状态标签                     |
| `.empty-state`        | 空状态                      |
| `.loading-wrapper`    | 加载中                      |
| `.stat-card`          | 统计卡片                     |
| `.main-content`       | 主内容区                     |
| `.toolbar`            | 工具栏                      |

***

## 13. 实施指南

### 13.1 新项目复用步骤

1. **复制核心样式文件**：
   - `src/assets/styles/variables.scss` — CSS 变量 + SCSS 映射
   - `src/assets/styles/element-variables.scss` — Element Plus 主题覆盖
   - `src/assets/styles/main.scss` — 全局样式 + 工具类 + 动画
2. **配置 Vite 全局注入**：

```typescript
// vite.config.ts
css: {
  preprocessorOptions: {
    scss: {
      additionalData: `@use "@/assets/styles/variables.scss" as *;`,
      api: 'modern-compiler'
    }
  }
}
```

1. **注册 Element Plus**：

```javascript
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

app.use(ElementPlus, { locale: zhCn })
```

1. **安装图标库**：

```bash
npm install @element-plus/icons-vue
```

### 13.2 开发规范

#### 必须遵守

- **使用 CSS 变量**而非硬编码色值、字号、间距
- **使用全局工具类**（`.flex-between`, `.text-muted` 等）而非内联样式
- **表格统一** `stripe` + `size="small"` + `v-loading`
- **对话框统一** `:close-on-click-modal="false"`
- **下拉框统一** `filterable`

#### 禁止事项

- ❌ 硬编码颜色值（如 `color: #1E293B`）
- ❌ 硬编码字号（如 `font-size: 14px`）
- ❌ 硬编码间距（如 `margin-top: 16px`，应使用 `var(--spacing-md)`）
- ❌ 引入其他图标库（仅使用 @element-plus/icons-vue）
- ❌ 使用 `!important` 覆盖 Element Plus 样式（应通过 `element-variables.scss` 或 `:deep` 穿透）

#### Element Plus 样式覆盖优先级

1. **首选**：`element-variables.scss` 中的 SCSS 变量覆盖
2. **次选**：`main.scss` 中的全局样式覆盖
3. **最后**：组件内 `:deep()` 穿透（仅限组件特有样式）

### 13.3 设计评审流程

```
需求提出 → UI设计/修改 → 对照本规范检查 → 代码实现 → 代码审查
                                    ↓
                          是否符合色彩/间距/圆角/阴影规范？
                          是否使用了CSS变量？
                          是否复用了工具类？
                          是否遵循了组件规范？
```

### 13.4 规范更新流程

当需要新增或修改设计规范时：

1. **修改变量**：在 `variables.scss` 中新增/修改 CSS 变量
2. **同步 SCSS 映射**：在 `variables.scss` 下半部分添加对应的 SCSS 变量
3. **更新 Element Plus 覆盖**：如涉及组件样式，同步修改 `element-variables.scss`
4. **更新本文档**：在对应章节记录变更
5. **通知团队**：变更内容与影响范围

***

## 附录A：Element Plus 完整主题变量覆盖参考

```scss
/* element-variables.scss 完整内容 */

$--colors-primary: (
  "primary": (
    "base": #1A56DB,
    "light-3": #3B82F6,
    "light-5": #60A5FA,
    "light-7": #93C5FD,
    "light-8": #BFDBFE,
    "light-9": #EFF6FF,
    "dark-2": #1E40AF,
  ),
  "success": (
    "base": #16A34A,
    "light-3": #22C55E,
    "light-5": #4ADE80,
    "light-7": #86EFAC,
    "light-8": #BBF7D0,
    "light-9": #DCFCE7,
    "dark-2": #15803D,
  ),
  "warning": (
    "base": #EA580C,
    "light-3": #F97316,
    "light-5": #FB923C,
    "light-7": #FDBA74,
    "light-8": #FED7AA,
    "light-9": #FFF7ED,
    "dark-2": #C2410C,
  ),
  "danger": (
    "base": #DC2626,
    "light-3": #DC2626,
    "light-5": #F87171,
    "light-7": #FCA5A5,
    "light-8": #FECACA,
    "light-9": #FEE2E2,
    "dark-2": #B91C1C,
  ),
  "info": (
    "base": #2563EB,
    "light-3": #3B82F6,
    "light-5": #60A5FA,
    "light-7": #93C5FD,
    "light-8": #BFDBFE,
    "light-9": #DBEAFE,
    "dark-2": #1D4ED8,
  ),
);

$--border-radius-base: 8px;
$--border-radius-small: 6px;
$--border-radius-round: 20px;
$--font-size-base: 14px;
$--font-size-primary: 14px;
$--box-shadow-base: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
$--box-shadow-light: 0 4px 8px rgba(0, 0, 0, 0.08);
$--box-shadow-lighter: 0 8px 16px rgba(0, 0, 0, 0.1);
$--transition-duration: 0.2s;
$--input-border-radius-base: 8px;
$--input-border-color: #E2E8F0;
$--input-border-color-hover: #1A56DB;
$--input-focus-border-color: #1A56DB;
$--input-fill-background: #FFFFFF;
$--input-fill-focus-background: #FFFFFF;
$--button-border-radius-base: 8px;
$--button-padding-vertical: 10px;
$--button-padding-horizontal: 20px;
$--button-medium-border-radius: 8px;
$--button-small-border-radius: 6px;
$--card-border-radius-base: 12px;
$--card-border-color: #E2E8F0;
$--dialog-border-radius-base: 16px;
$--dialog-padding-primary: 24px;
$--menu-item-border-radius-base: 8px;
$--menu-item-hover-fill-color: rgba(26, 86, 219, 0.04);
$--menu-item-hover-text-color: #1A56DB;
$--menu-active-color: #1A56DB;
$--menu-item-font-size: 14px;
$--table-border-color: #F1F5F9;
$--table-header-background: #F8FAFC;
$--table-row-hover-background: #F1F5F9;
$--table-current-row-background: rgba(26, 86, 219, 0.04);
$--tag-border-radius: 6px;
$--tag-padding-vertical: 0;
$--tag-padding-horizontal: 10px;
$--dropdown-menu-box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
$--dropdown-menuItem-hover-fill: rgba(26, 86, 219, 0.04);
$--dropdown-menuItem-hover-color: #1A56DB;
$--pagination-button-bg: #FFFFFF;
$--pagination-hover-color: #1A56DB;

@use "element-plus/theme-chalk/src/index.scss" as *;
```

## 附录B：CSS 变量完整定义参考

```css
:root {
  /* 主色 */
  --color-primary: #1A56DB;
  --color-primary-light: #3B82F6;
  --color-primary-lighter: #60A5FA;
  --color-primary-dark: #1E40AF;
  --color-primary-50: #EFF6FF;
  --color-primary-100: #DBEAFE;
  --color-primary-rgb: 26, 86, 219;

  /* 成功色 */
  --color-success: #16A34A;
  --color-success-light: #22C55E;
  --color-success-dark: #15803D;
  --color-success-50: #DCFCE7;
  --color-success-rgb: 22, 163, 74;

  /* 警告色 */
  --color-warning: #EA580C;
  --color-warning-light: #F97316;
  --color-warning-dark: #C2410C;
  --color-warning-50: #FFF7ED;

  /* 危险色 */
  --color-danger: #DC2626;
  --color-danger-light: #DC2626;
  --color-danger-dark: #B91C1C;
  --color-danger-50: #FEE2E2;

  /* 信息色 */
  --color-info: #2563EB;
  --color-info-light: #3B82F6;
  --color-info-dark: #1D4ED8;
  --color-info-50: #DBEAFE;

  /* 文字色 */
  --color-text-primary: #1E293B;
  --color-text-regular: #334155;
  --color-text-secondary: #64748B;
  --color-text-tertiary: #94A3B8;
  --color-text-placeholder: #CBD5E1;
  --color-text-disabled: #E2E8F0;

  /* 边框色 */
  --color-border: #E2E8F0;
  --color-border-light: #F1F5F9;
  --color-border-lighter: #F8FAFC;
  --color-border-focus: var(--color-primary);

  /* 背景色 */
  --color-bg-page: #F1F5F9;
  --color-bg-base: #F1F5F9;
  --color-bg-white: #FFFFFF;
  --color-bg-overlay: rgba(15, 23, 42, 0.5);
  --color-bg-hover: #F1F5F9;
  --color-bg-active: rgba(26, 86, 219, 0.08);

  /* 侧边栏 */
  --sidebar-bg: #0F172A;
  --sidebar-bg-light: #1E293B;
  --sidebar-text: #94A3B8;
  --sidebar-text-active: #FFFFFF;
  --sidebar-hover-bg: #1E293B;
  --sidebar-active-bg: rgba(59, 130, 246, 0.15);
  --sidebar-active-border: #3B82F6;
  --sidebar-divider: rgba(255, 255, 255, 0.06);

  /* 阴影 */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 12px 24px rgba(0, 0, 0, 0.12);
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  --shadow-header: 0 1px 3px rgba(0, 0, 0, 0.04);

  /* 圆角 */
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-full: 9999px;

  /* 字号 */
  --font-size-xs: 11px;
  --font-size-sm: 12px;
  --font-size-base: 13px;
  --font-size-md: 14px;
  --font-size-lg: 15px;
  --font-size-xl: 16px;
  --font-size-2xl: 20px;
  --font-size-3xl: 24px;
  --font-size-4xl: 30px;

  /* 字重 */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* 间距 */
  --spacing-3xs: 2px;
  --spacing-xxs: 4px;
  --spacing-xs: 8px;
  --spacing-sm: 12px;
  --spacing-md: 16px;
  --spacing-lg: 20px;
  --spacing-xl: 24px;
  --spacing-2xl: 32px;
  --spacing-3xl: 48px;

  /* 过渡 */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
  --transition-slow: 0.3s ease;
  --transition-bounce: 0.3s cubic-bezier(0.68, -0.2, 0.32, 1.2);

  /* 布局 */
  --sidebar-width: 240px;
  --sidebar-collapsed-width: 64px;
  --header-height: 56px;

  /* Z-Index */
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-popover: 600;
  --z-tooltip: 700;
  --z-notification: 800;

  /* 渐变 */
  --brand-gradient: linear-gradient(135deg, #1A56DB, #3B82F6);
  --brand-hover-gradient: linear-gradient(135deg, #1E40AF, #1A56DB);
}
```

