# VectorTransaction 使用指南

## 概述

本文档指导在业务代码中采用 `VectorTransaction`，确保 PostgreSQL 数据与向量库（Chroma）的一致性。

## 背景

### 问题
- 业务代码中存在大量独立调用向量库的操作
- PG 数据保存后，向量库操作失败会导致数据不一致
- 缺乏统一的事务管理机制

### 解决方案
- 统一使用 `VectorTransaction` 管理向量操作
- 在 Django ORM 事务中联动执行向量操作
- 事务失败时自动回滚，确保数据一致性

---

## 核心组件

### VectorTransaction
```python
from services.vector import vector_transaction

with VectorTransaction() as vt:
    # 1. 先保存PG数据
    enterprise = Enterprise.objects.create(name='xxx', ...)

    # 2. 添加向量操作
    vt.add_vector(
        collection_name='enterprise_vectors',
        doc_id=str(enterprise.id),
        text=f"{enterprise.name} {enterprise.business_scope}",
        metadata={'province': enterprise.province}
    )

    # 3. 提交时会同时执行向量操作
    # 如果向量操作失败，整个事务会回滚
```

---

## 使用场景

### 场景1：企业创建时同步索引向量

**Before（不一致风险）:**
```python
def create_enterprise(data):
    # 1. 保存PG数据
    enterprise = Enterprise.objects.create(**data)

    # 2. 索引向量（可能失败）
    success = enterprise_vector_store.add_enterprise(
        enterprise_id=str(enterprise.id),
        text=f"{enterprise.name} {enterprise.business_scope}",
        metadata={'province': enterprise.province}
    )

    if not success:
        # 企业已创建，但向量未索引，数据不一致
        pass

    return enterprise
```

**After（数据一致）:**
```python
from services.vector import vector_transaction

def create_enterprise(data):
    with VectorTransaction() as vt:
        # 1. 保存PG数据
        enterprise = Enterprise.objects.create(**data)

        # 2. 添加向量操作（会在事务提交时执行）
        text = f"{enterprise.name} {enterprise.business_scope}"
        metadata = {'province': enterprise.province, 'city': enterprise.city}
        vt.add_vector(
            collection_name='enterprise_vectors',
            doc_id=str(enterprise.id),
            text=text,
            metadata=metadata
        )

        return enterprise
    # 事务提交：如果向量操作失败，PG数据也会回滚
```

### 场景2：企业更新时同步更新向量

**Before:**
```python
def update_enterprise(enterprise_id, data):
    enterprise = Enterprise.objects.get(id=enterprise_id)

    # 1. 更新PG数据
    for key, value in data.items():
        setattr(enterprise, key, value)
    enterprise.save()

    # 2. 更新向量（可能失败）
    text = f"{enterprise.name} {enterprise.business_scope}"
    enterprise_vector_store.update_enterprise(
        enterprise_id=str(enterprise.id),
        text=text,
        metadata={'province': enterprise.province}
    )
```

**After:**
```python
from services.vector import vector_transaction

def update_enterprise(enterprise_id, data):
    with VectorTransaction() as vt:
        enterprise = Enterprise.objects.get(id=enterprise_id)

        # 1. 更新PG数据
        for key, value in data.items():
            setattr(enterprise, key, value)
        enterprise.save()

        # 2. 更新向量（会在事务提交时执行）
        text = f"{enterprise.name} {enterprise.business_scope}"
        vt.add_vector(
            collection_name='enterprise_vectors',
            doc_id=str(enterprise.id),
            text=text,
            metadata={'province': enterprise.province}
        )

    return enterprise
```

### 场景3：企业删除时同步删除向量

**Before:**
```python
def delete_enterprise(enterprise_id):
    enterprise = Enterprise.objects.get(id=enterprise_id)

    # 1. 删除PG数据
    enterprise.delete()

    # 2. 删除向量（可能失败）
    enterprise_vector_store.delete_enterprise(str(enterprise_id))
```

**After:**
```python
from services.vector import vector_transaction

def delete_enterprise(enterprise_id):
    with VectorTransaction() as vt:
        enterprise = Enterprise.objects.get(id=enterprise_id)

        # 1. 标记删除（软删除）或直接删除
        enterprise.delete()

        # 2. 添加删除向量操作
        vt.delete_vector(
            collection_name='enterprise_vectors',
            doc_id=str(enterprise_id)
        )

    return True
```

### 场景4：批量导入企业

```python
from services.vector import vector_transaction

def batch_import_enterprises(enterprise_list):
    with VectorTransaction() as vt:
        for data in enterprise_list:
            enterprise = Enterprise.objects.create(**data)

            text = f"{enterprise.name} {enterprise.business_scope}"
            vt.add_vector(
                collection_name='enterprise_vectors',
                doc_id=str(enterprise.id),
                text=text,
                metadata={'province': enterprise.province}
            )

    # 所有企业创建和向量索引在一个事务中
```

---

## 迁移检查清单

- [ ] `Enterprise.objects.create()` 后添加 `vt.add_vector()`
- [ ] `enterprise.save()` 后添加 `vt.add_vector()` 更新向量
- [ ] `enterprise.delete()` 后添加 `vt.delete_vector()`
- [ ] 使用 `with VectorTransaction() as vt:` 包装
- [ ] 确保向量操作在事务提交时执行

---

## 常见问题

### Q: 向量库不可用时会怎样？
```python
# VectorTransaction 会自动检测
if not self._chroma_available:
    logger.warning(f"向量库不可用，跳过添加向量: {doc_id}")
    return
# 向量操作会被跳过，但PG数据正常保存
```

### Q: 如何处理向量操作失败？
```python
# 事务会自动回滚，PG数据不会提交
with VectorTransaction() as vt:
    enterprise = Enterprise.objects.create(**data)
    vt.add_vector(...)  # 如果这里失败

# 抛出异常，enterprise 不会创建
```

### Q: 如何记录向量操作的详细日志？
```python
# VectorTransaction 内部有详细日志
logger.info(f"事务提交: {len(self._operations)} 个向量操作")
logger.error(f"向量操作失败: {str(e)}")
```

---

## 附录：相关文件

| 文件 | 说明 |
|------|------|
| `services/vector/transaction.py` | VectorTransaction 实现 |
| `services/vector/enterprise_store.py` | EnterpriseVectorStore 实现 |
| `services/vector/base_store.py` | BaseVectorStore 基类 |
| `apps/enterprise/views.py` | 企业相关API（待迁移） |

---

## 附录：集合名称参考

| 集合名称 | 用途 |
|----------|------|
| `enterprise_vectors` | 企业信息向量 |
| `tender_vectors` | 招标公告向量 |
| `document_vectors` | 文档向量 |

---

**最后更新**: 2026-04-04
**维护者**: 架构组
**版本**: v1.0
