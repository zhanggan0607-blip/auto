# TypeScript 类型生成工具

## 概述

本工具从 Django REST Framework Serializer 自动生成 TypeScript 类型定义，保持前后端类型同步。

## 使用方法

### 1. 运行生成器

```bash
cd backend
python -m scripts.generate_ts_types --apps tenders,enterprise,crawler
```

### 2. 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--apps` | 要处理的 Django 应用列表（逗号分隔） | `tenders,enterprise,crawler,vectorlib,openclaw` |
| `--output` | 输出目录 | `frontend/src/types/generated` |
| `--print` | 打印到标准输出而非写入文件 | `false` |

### 3. 示例

```bash
# 生成所有应用的类型
python -m scripts.generate_ts_types

# 只生成特定应用的类型
python -m scripts.generate_ts_types --apps tenders,enterprise

# 输出到自定义目录
python -m scripts.generate_ts_types --output ./my-types

# 打印到控制台查看
python -m scripts.generate_ts_types --print
```

## 生成的文件结构

```
frontend/src/types/generated/
├── index.ts          # 包含所有类型的索引文件
├── tenders.ts        # 招标相关类型
├── enterprise.ts     # 企业相关类型
├── crawler.ts        # 爬虫相关类型
├── vectorlib.ts      # 向量库相关类型
└── openclaw.ts       # OpenClaw相关类型
```

## 在前端使用

```typescript
// 方式1: 从生成的类型导入
import { TenderProjectSerializer, TenderFileSerializer } from '@/types/generated/tenders'

// 方式2: 从索引文件导入所有类型
import * as GeneratedTypes from '@/types/generated'

// 使用类型
const project: TenderProjectSerializer = {
  id: 1,
  title: '招标项目',
  // ...
}
```

## 集成到开发流程

### 方式1: 手动运行

每次修改后端 Serializer 后运行：

```bash
python -m scripts.generate_ts_types --apps your_modified_app
```

### 方式2: Git Hook (推荐)

创建 pre-commit hook：

```bash
# 在 backend 目录下创建 .git/hooks/pre-commit
#!/bin/sh
cd "$(dirname "$0")/.."
python -m scripts.generate_ts_types --apps tenders,enterprise,crawler
git add frontend/src/types/generated/
```

### 方式3: Makefile 任务

```makefile
# 在项目根目录的 Makefile 中添加
generate-types:
	cd backend && python -m scripts.generate_ts_types

.PHONY: generate-types
```

## 类型映射规则

| Django/DRF 类型 | TypeScript 类型 |
|----------------|-----------------|
| CharField, TextField | `string` |
| IntegerField, FloatField | `number` |
| BooleanField | `boolean` |
| DateField, DateTimeField | `string` |
| ChoiceField | `'option1' \| 'option2'` |
| ForeignKey (read_only) | 不生成 |
| Nested Serializer | 嵌套接口 |
| PrimaryKeyRelatedField | `number` (关联ID) |

## 注意事项

1. **只读字段被忽略**: `read_only=True` 的字段不会生成到 TypeScript 类型中
2. **手动补充类型**: 复杂的嵌套结构可能需要手动调整
3. **Choice 字段**: 会自动转换为联合类型
4. **关联字段**: 外键字段默认生成 `number` 类型

## 故障排除

### ImportError: cannot import name 'serializers'

确保 Django 设置正确：

```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
cd backend
python -m scripts.generate_ts_types
```

### 生成的类型不完整

检查 Serializer 是否正确继承了 `serializers.Serializer` 或 `serializers.ModelSerializer`。
