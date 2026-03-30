# TypeScript 迁移计划

## 当前状态
- Vue 3.3.11 + JavaScript
- 无 TypeScript 支持

## 迁移目标
1. 添加 TypeScript 支持
2. 类型安全的 API 调用
3. 组件 Props 类型定义
4. Store 类型定义

## 迁移步骤

### 第一阶段：基础配置
1. 安装 TypeScript 依赖
```bash
npm install -D typescript @types/node @vue/tsconfig
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

2. 创建 tsconfig.json
3. 添加类型声明文件

### 第二阶段：核心文件迁移
1. src/types/ - 类型定义
2. src/api/ - API 类型
3. src/store/ - Store 类型
4. src/utils/ - 工具函数类型

### 第三阶段：组件迁移
1. 通用组件
2. 业务组件
3. 页面组件

## 文件结构
```
frontend/
├── src/
│   ├── types/              # 类型定义
│   │   ├── api.d.ts        # API响应类型
│   │   ├── models.d.ts     # 数据模型类型
│   │   ├── store.d.ts      # Store类型
│   │   └── components.d.ts # 组件Props类型
│   ├── api/
│   │   ├── user.ts         # 用户API
│   │   ├── tender.ts       # 招标API
│   │   └── index.ts
│   ├── store/
│   │   ├── index.ts
│   │   └── modules/
│   └── ...
├── tsconfig.json
└── package.json
```

## 类型定义示例

### API 响应类型
```typescript
interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

interface PaginatedResponse<T> {
  list: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}
```

### 数据模型类型
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

interface TenderProject {
  id: number;
  title: string;
  status: string;
  budget: number;
  deadline: string;
  source_url: string;
}

interface Enterprise {
  id: number;
  name: string;
  credit_code: string;
  legal_person: string;
  contact_phone: string;
}
```

## 注意事项
1. 渐进式迁移，不影响现有功能
2. 优先迁移核心模块
3. 使用 JSDoc 作为过渡方案
