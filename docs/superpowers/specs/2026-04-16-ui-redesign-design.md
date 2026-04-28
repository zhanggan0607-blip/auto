# 天齐AI投标平台 — UI 全面重新设计规范

**日期**: 2026-04-16  
**版本**: 1.0  
**状态**: 待审核

---

## 1. 设计决策摘要

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 设计方向 | A 专业商务风 | B端企业级产品定位，专业可信赖 |
| 色彩方案 | A2 靛青蓝 (#4F46E5) | 现代科技商务感，突出AI技术实力 |
| 布局结构 | L1 侧边栏布局（优化版） | 迁移成本低，与现有结构兼容 |
| 仪表盘 | D3 混合型 | 欢迎横幅+待办+统计+趋势+列表，信息最完整 |
| 实施范围 | 一次性全量改造 | 40个页面全部升级 |

---

## 2. 色彩系统

### 2.1 主色板

```
主色 (Primary):     #4F46E5 (靛青蓝)
主色浅 (Light):     #6366F1
主色深 (Dark):      #3730A3
主色极浅 (50):      #EEF2FF
主色极浅 (100):     #E0E7FF

成功色 (Success):   #10B981
成功色浅:           #34D399
成功色深:           #059669
成功色极浅:         #F0FDF4

警告色 (Warning):   #F59E0B
警告色浅:           #FBBF24
警告色深:           #D97706
警告色极浅:         #FFF7ED

危险色 (Danger):    #EF4444
危险色浅:           #F87171
危险色深:           #DC2626
危险色极浅:         #FEF2F2

信息色 (Info):      #6B7280 (Gray 500，中性信息，区别于主色)
信息色浅:           #9CA3AF
信息色深:           #4B5563
信息色极浅:         #F3F4F6
```

### 2.2 中性色板

```
文字主色:     #1E293B (Slate 800)
文字次色:     #475569 (Slate 600)
文字辅助:     #94A3B8 (Slate 400)
文字占位:     #CBD5E1 (Slate 300)

边框深:       #E2E8F0 (Slate 200)
边框浅:       #F1F5F9 (Slate 100)
分割线:       #F8FAFC (Slate 50)

背景页面:     #F8FAFC (Slate 50)
背景卡片:     #FFFFFF
背景悬浮:     #F1F5F9 (Slate 100)
背景深色:     #0F172A (Slate 900)
```

### 2.3 侧边栏色彩

```
侧边栏背景:       #1E1B4B (Indigo 950)
侧边栏文字:       #C7D2FE (Indigo 300)
侧边栏文字亮:     #FFFFFF
侧边栏激活文字:   #FFFFFF
侧边栏激活背景:   rgba(99, 102, 241, 0.15)
侧边栏悬浮背景:   rgba(99, 102, 241, 0.08)
侧边栏分割线:     rgba(255, 255, 255, 0.06)
侧边栏品牌渐变:   linear-gradient(135deg, #4F46E5, #6366F1)
```

### 2.4 CSS 变量映射

将现有 `variables.scss` 中的 `:root` 变量全部更新为新色值：

```scss
:root {
  --color-primary: #4F46E5;
  --color-primary-light: #6366F1;
  --color-primary-lighter: #818CF8;
  --color-primary-dark: #3730A3;
  --color-primary-50: #EEF2FF;
  --color-primary-100: #E0E7FF;

  --color-success: #10B981;
  --color-success-light: #34D399;
  --color-success-dark: #059669;
  --color-success-50: #F0FDF4;

  --color-warning: #F59E0B;
  --color-warning-light: #FBBF24;
  --color-warning-dark: #D97706;
  --color-warning-50: #FFF7ED;

  --color-danger: #EF4444;
  --color-danger-light: #F87171;
  --color-danger-dark: #DC2626;
  --color-danger-50: #FEF2F2;

  --color-info: #6B7280;
  --color-info-light: #9CA3AF;
  --color-info-dark: #4B5563;
  --color-info-50: #F3F4F6;

  --color-text-primary: #1E293B;
  --color-text-secondary: #475569;
  --color-text-tertiary: #94A3B8;
  --color-text-placeholder: #CBD5E1;

  --color-border: #E2E8F0;
  --color-border-light: #F1F5F9;
  --color-border-lighter: #F8FAFC;

  --color-bg-page: #F8FAFC;
  --color-bg-white: #FFFFFF;
  --color-bg-base: #F1F5F9;
  --color-bg-hover: #F1F5F9;

  --sidebar-bg: #1E1B4B;
  --sidebar-text: #C7D2FE;
  --sidebar-text-active: #FFFFFF;
  --sidebar-active-bg: rgba(99, 102, 241, 0.15);
  --sidebar-hover-bg: rgba(99, 102, 241, 0.08);
  --sidebar-divider: rgba(255, 255, 255, 0.06);

  --brand-gradient: linear-gradient(135deg, #4F46E5, #6366F1);
  --brand-hover-gradient: linear-gradient(135deg, #3730A3, #4F46E5);
}
```

---

## 3. 排版系统

### 3.1 字体栈

```scss
--font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-family-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### 3.2 字号层级

```
Display:   30px / 1.2  — 仅用于欢迎横幅大标题
H1:        24px / 1.3  — 页面主标题
H2:        20px / 1.4  — 区块标题
H3:        16px / 1.5  — 卡片标题
H4:        14px / 1.5  — 小节标题
Body:      14px / 1.6  — 正文
Small:     13px / 1.5  — 辅助文字
Caption:   12px / 1.5  — 标签、时间戳
Micro:     11px / 1.4  — 极小文字（badge等）
```

### 3.3 字重

```
Regular:   400  — 正文
Medium:    500  — 强调文字、按钮
Semibold:  600  — 标题
Bold:      700  — 数据数字、大标题
```

---

## 4. 间距与尺寸系统

### 4.1 间距（4px基准）

```
--spacing-3xs: 2px
--spacing-xxs: 4px
--spacing-xs:  8px
--spacing-sm:  12px
--spacing-md:  16px
--spacing-lg:  20px
--spacing-xl:  24px
--spacing-2xl: 32px
--spacing-3xl: 48px
```

### 4.2 圆角

```
--radius-xs: 4px    — 小元素（badge、tag）
--radius-sm: 6px    — 输入框、小按钮
--radius-md: 8px    — 卡片、对话框
--radius-lg: 12px   — 大卡片、面板
--radius-xl: 16px   — 特大容器
--radius-full: 9999px — 圆形/胶囊
```

### 4.3 阴影

```
--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04)
--shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.06)
--shadow-md: 0 4px 8px rgba(0, 0, 0, 0.08)
--shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 12px 24px rgba(0, 0, 0, 0.12)
--shadow-card: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)
--shadow-header: 0 1px 3px rgba(0, 0, 0, 0.04)
```

---

## 5. 布局系统

### 5.1 整体布局

```
┌─────────────────────────────────────────────────────┐
│ 侧边栏 (64px 折叠 / 220px 展开)                      │
│ ┌──────────┐                                        │
│ │ Logo区域  │  顶部栏 (56px, sticky)                  │
│ │ 投标精灵  │  ┌──────────────────────────────────┐  │
│ ├──────────┤  │ ☰ 面包屑导航    模型状态 🔔 用户  │  │
│ │          │  └──────────────────────────────────┘  │
│ │ 图标导航  │                                        │
│ │ (悬浮展开)│  主内容区 (padding: 20px)               │
│ │          │  ┌──────────────────────────────────┐  │
│ │          │  │   <router-view>                  │  │
│ │          │  │   带页面切换动画                    │  │
│ │          │  └──────────────────────────────────┘  │
│ │ 服务状态  │                                        │
│ └──────────┘                                        │
└─────────────────────────────────────────────────────┘
```

### 5.2 侧边栏优化

- **折叠态**: 64px 宽，仅显示图标
- **展开态**: 220px 宽，图标+文字
- **悬浮展开**: 折叠态下悬浮菜单项显示完整文字（popover方式）
- **Logo区域**: 品牌渐变背景，折叠时仅显示图标
- **菜单项**: 增大点击区域(40px高)，激活态用半透明背景+左侧3px指示条
- **底部**: 服务状态指示器保留

### 5.3 响应式断点

```
xs: < 640px   — 手机（侧边栏隐藏，底部导航）
sm: 640-767px — 大手机/小平板（侧边栏折叠）
md: 768-1023px — 平板（侧边栏折叠，内容区自适应）
lg: 1024-1279px — 小桌面（侧边栏展开/折叠可选）
xl: ≥ 1280px  — 标准桌面（侧边栏展开）
```

---

## 6. 组件设计规范

### 6.1 卡片 (Card)

```
背景: #FFFFFF
边框: 1px solid #E2E8F0
圆角: 12px (--radius-lg)
阴影: --shadow-card
悬浮: translateY(-2px) + --shadow-md
内边距: 20px (--spacing-lg)
```

### 6.2 按钮 (Button)

**主要按钮**:
```
背景: #4F46E5
文字: #FFFFFF
圆角: 8px
内边距: 8px 16px
悬浮: #3730A3 (darken)
点击: scale(0.98)
```

**次要按钮**:
```
背景: transparent
边框: 1px solid #E2E8F0
文字: #1E293B
悬浮: background #F1F5F9
```

**文字按钮**:
```
背景: transparent
文字: #4F46E5
悬浮: background #EEF2FF
```

### 6.3 输入框 (Input)

```
边框: 1px solid #E2E8F0
圆角: 8px
内边距: 8px 12px
聚焦边框: #4F46E5 + shadow 0 0 0 3px rgba(79, 70, 229, 0.1)
聚焦动画: border-color transition 0.15s
```

### 6.4 表格 (Table)

```
表头背景: #F8FAFC
表头文字: #475569, font-weight 600, font-size 13px
行高: 52px
斑马纹: 偶数行 #FFFFFF, 奇数行 #FAFBFC
悬浮行: #F1F5F9
边框: 无外边框, 行间 1px solid #F1F5F9
```

### 6.5 标签 (Tag/Badge)

```
圆角: 6px
内边距: 2px 8px
字号: 12px
字重: 500

类型色彩:
  primary: bg #EEF2FF, text #4F46E5
  success: bg #F0FDF4, text #059669
  warning: bg #FFF7ED, text #D97706
  danger:  bg #FEF2F2, text #DC2626
  info:    bg #F1F5F9, text #475569
```

### 6.6 统计卡片 (StatCard)

```
背景: #FFFFFF
边框: 1px solid #E2E8F0
圆角: 12px
内边距: 20px
阴影: --shadow-card
悬浮: translateY(-3px) + --shadow-md

图标区域: 48x48px, 圆角 10px, 渐变背景
数值: 24px, font-weight 700
标签: 13px, color #475569
趋势: 右上角, 12px, 绿色↑/红色↓
装饰: 右上角半透明圆形背景
```

### 6.7 对话框 (Dialog)

```
圆角: 16px (--radius-xl)
阴影: --shadow-xl
遮罩: rgba(15, 23, 42, 0.5)
头部: 20px内边距, 底部分割线
内容: 20px内边距
底部: 20px内边距, 按钮右对齐
```

---

## 7. 仪表盘设计 (D3 混合型)

### 7.1 页面结构（从上到下）

```
1. 欢迎横幅 (WelcomeBanner)
   - 渐变背景: linear-gradient(135deg, #4F46E5, #6366F1)
   - 问候语: "欢迎回来，{username} 👋"
   - 待办摘要: "你有 X 个待处理招标，Y 个投标即将截止"
   - 快捷按钮: "查看待办 →" "开始投标 →"
   - 右侧装饰: 半透明圆形

2. 统计卡片行 (StatCards)
   - 4列网格: 招标项目 / 已中标 / 待处理 / 收藏
   - 每张卡片: 图标 + 数值 + 标签 + 趋势变化
   - 右上角装饰: 半透明主题色圆形

3. 双列区域
   - 左列 (2/3宽): 投标趋势图
     - 柱状图/折线图，最近7天/30天
     - 需引入 ECharts 或 Chart.js
   - 右列 (1/3宽): 快捷操作网格
     - 2x2 网格: 搜索招标 / 新建投标 / 自动投标 / 导出报告
     - 每个操作: 图标 + 文字，主题色浅背景

4. 双列区域
   - 左列 (1/2宽): 即将截止提醒
     - 列表形式，按截止时间排序
     - 红色/橙色/灰色 时间指示
   - 右列 (1/2宽): 自动化状态
     - 服务运行状态列表
     - 绿色/黄色/灰色 状态点

5. 最近招标项目表格
   - 紧凑表格，5-8行
   - 列: 项目名称 / 地区 / 状态 / 操作
   - 状态用彩色标签
   - "查看全部 →" 链接
```

---

## 8. 登录/注册页面

### 8.1 设计

```
左右分栏布局:
  左侧 (55%): 品牌展示区
    - 深色背景 (#1E1B4B)
    - 品牌Logo + 标语
    - 装饰性几何图形/渐变
    - 产品特性列表 (3-4个图标+文字)
  
  右侧 (45%): 表单区
    - 白色背景
    - 居中的登录/注册表单
    - 最大宽度 400px
    - 输入框使用新设计规范
    - 主按钮使用品牌渐变

移动端: 全屏表单，品牌区隐藏或缩小为顶部横幅
```

---

## 9. 交互与动画

### 9.1 页面切换

```scss
.page-enter-active { transition: all 0.25s ease-out; }
.page-leave-active { transition: all 0.15s ease-in; }
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }
```

### 9.2 卡片悬浮

```scss
.card {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
}
```

### 9.3 按钮点击

```scss
.button:active {
  transform: scale(0.98);
}
```

### 9.4 列表项入场

```scss
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
// 逐项延迟: animation-delay: calc(var(--index) * 0.05s)
```

### 9.5 骨架屏

```
背景: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%)
动画: shimmer 1.5s infinite
圆角: 与实际内容一致
```

---

## 10. Element Plus 主题定制

### 10.1 关键修复

**移除 `main.js` 中的预编译CSS引入**:
```javascript
// 删除这行:
import 'element-plus/dist/index.css'
```

**改为通过 SCSS 编译引入** (在 `element-variables.scss` 末尾):
```scss
@use "element-plus/theme-chalk/src/index.scss" as *;
```

### 10.2 变量覆盖更新

```scss
// element-variables.scss 关键覆盖
$--colors: (
  'primary': (
    'base': #4F46E5,
  ),
  'success': (
    'base': #10B981,
  ),
  'warning': (
    'base': #F59E0B,
  ),
  'danger': (
    'base': #EF4444,
  ),
  'info': (
    'base': #6B7280,
  ),
);

$--border-radius-base: 8px;
$--border-radius-small: 6px;
$--font-size-base: 14px;
$--box-shadow-base: 0 1px 3px rgba(0, 0, 0, 0.04);
```

---

## 11. 需要新增的依赖

| 依赖 | 用途 | 版本建议 |
|------|------|----------|
| `echarts` | 仪表盘趋势图表 | ^5.5.0 |
| `vue-echarts` | ECharts Vue 封装 | ^7.0.0 |
| `inter-ui` | Inter 字体 (Web Font) | ^4.0.0 |

---

## 12. 实施文件清单

### 12.1 设计系统文件（必须先改）

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/assets/styles/variables.scss` | 重写 | 全部CSS变量更新为靛青蓝色系 |
| `src/assets/styles/element-variables.scss` | 重写 | Element Plus主题变量覆盖 |
| `src/assets/styles/main.scss` | 修改 | 更新全局样式类、新增组件样式 |
| `src/assets/styles/mixins.scss` | 修改 | 新增响应式mixin、动画mixin |
| `src/main.js` | 修改 | 移除预编译CSS引入 |

### 12.2 布局组件（第二优先级）

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/views/Layout.vue` | 重写 | 新布局结构、侧边栏优化 |
| `src/components/SidebarNav.vue` | 重写 | 图标列+悬浮展开、新配色 |
| `src/components/BreadcrumbNav.vue` | 修改 | 新配色 |
| `src/views/Login.vue` | 重写 | 左右分栏布局 |
| `src/views/Register.vue` | 重写 | 同登录页风格 |

### 12.3 核心页面组件（第三优先级）

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/views/Dashboard.vue` | 重写 | D3混合型仪表盘 |
| `src/components/StatCard.vue` | 重写 | 新设计规范 |
| `src/components/StatCards.vue` | 修改 | 新布局 |
| `src/components/PageHeader.vue` | 修改 | 新配色 |
| `src/components/SearchForm.vue` | 修改 | 新输入框样式 |
| `src/components/CrudTable.vue` | 修改 | 新表格样式 |
| `src/components/Pagination.vue` | 修改 | 新配色 |
| `src/components/ConfirmDialog.vue` | 修改 | 新对话框样式 |
| `src/components/StatusBadge.vue` | 修改 | 新标签样式 |

### 12.4 业务页面（第四优先级 — 逐页更新样式）

所有 40 个页面组件均需更新：
- 替换硬编码颜色为新CSS变量
- 统一使用新的间距、圆角、阴影变量
- 统一标签/按钮/输入框样式
- 添加响应式适配

完整页面列表：
- Dashboard, Login, Register, NotFound, Profile
- CompanyInfo + 7个company子组件
- TenderList, TenderDetail
- BidList, BidDetail
- DocumentList, DocumentGenerate
- KeywordList, ScheduleList
- CreateSchedule, EditSchedule
- AutomationDashboard, AutomationMonitor, OneClickLaunch, AutomationConfig
- NotificationList, VectorLibrary
- UserManagement, ModelConfig, AIPlayground, ProjectKnowledge
- WebsiteTemplateList, ServiceMonitor + 3个监控子组件

---

## 13. 验收标准

1. **色彩一致性**: 所有页面使用统一的靛青蓝色系，无残留旧色值
2. **Element Plus主题生效**: 按钮、输入框、表格等组件使用新主题
3. **侧边栏优化**: 折叠/展开/悬浮展开三种状态正常工作
4. **仪表盘完整**: 欢迎横幅+统计+趋势图+快捷操作+待办+列表
5. **响应式**: 在 1280px/768px/640px 三个断点下布局正常
6. **动画流畅**: 页面切换、卡片悬浮、列表入场动画自然
7. **登录页**: 左右分栏布局，品牌展示+表单
8. **无控制台错误**: 无CSS变量未定义、无样式覆盖冲突
