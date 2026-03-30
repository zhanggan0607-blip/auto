# ViewSet迁移指南

## 迁移目标

将所有 `APIResponseMixin, viewsets.ModelViewSet` 模式的ViewSet迁移到 `AuthenticatedModelViewSet`。

## 迁移步骤

### 1. 更新import语句

**旧写法：**
```python
from core.viewsets import APIResponseMixin
from rest_framework import viewsets
```

**新写法：**
```python
from core.viewsets import AuthenticatedModelViewSet
```

### 2. 更新类继承

**旧写法：**
```python
class MyViewSet(APIResponseMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    # ...
```

**新写法：**
```python
class MyViewSet(AuthenticatedModelViewSet):
    # permission_classes已自动包含IsAuthenticated
    # filter_backends已自动配置
    # ...
```

## 迁移清单

### 高优先级（必须迁移）

| 文件 | ViewSet | 状态 | 说明 |
|------|---------|------|------|
| enterprise/views.py | EnterpriseViewSet | ✅ 已用APIResponseMixin | 改为AuthenticatedModelViewSet |
| enterprise/views.py | EnterpriseBidConfigViewSet | ⚠️ 未用APIResponseMixin | 需要添加权限 |
| openclaw/views.py | LLMModelViewSet | ⚠️ 未用APIResponseMixin | 需要完整迁移 |
| crawler/views.py | WebsiteTemplateViewSet | ⚠️ 未用APIResponseMixin | 需要完整迁移 |
| crawler/views.py | CrawlResultViewSet | ⚠️ 未用APIResponseMixin | 需要完整迁移 |

### 中优先级（建议迁移）

| 文件 | ViewSet | 状态 |
|------|---------|------|
| enterprise/views.py | EnterpriseQualificationViewSet | 使用APIResponseMixin |
| enterprise/views.py | EnterprisePerformanceViewSet | 使用APIResponseMixin |
| enterprise/views.py | EnterpriseContactViewSet | 使用APIResponseMixin |
| enterprise/views.py | EnterpriseMatchRuleViewSet | 使用APIResponseMixin |
| enterprise/views.py | EnterpriseDocumentViewSet | 使用APIResponseMixin |
| enterprise/views.py | EnterpriseKeyPersonnelViewSet | 使用APIResponseMixin |
| vectorlib/views.py | BidDocumentLibraryViewSet | 使用APIResponseMixin |
| vectorlib/views.py | AISearchTaskViewSet | 使用APIResponseMixin |
| scheduler/views.py | UnifiedScheduleViewSet | 使用APIResponseMixin |
| crawler/scheduler_views.py | CrawlScheduleViewSet | 使用APIResponseMixin |
| crawler/scheduler_views.py | CrawlScheduleLogViewSet | 使用APIResponseMixin |
| crawler/views.py | CrawlSessionViewSet | 使用APIResponseMixin |

### 低优先级（可选迁移）

| 文件 | ViewSet | 状态 |
|------|---------|------|
| openclaw/views.py | LLMProviderViewSet | 使用APIResponseMixin |
| openclaw/views.py | AgentModelConfigViewSet | 使用APIResponseMixin |
| openclaw/views.py | BidWorkflowViewSet | 使用APIResponseMixin |
| openclaw/views.py | WorkflowStageViewSet | 使用APIResponseMixin |
| openclaw/views.py | LLMUsageLogViewSet | ReadOnlyModelViewSet |
| openclaw/one_click_views.py | OneClickAutomationViewSet | ViewSet |
| openclaw/one_click_views.py | EnterpriseQuickSetupViewSet | ViewSet |
| openclaw/one_click_views.py | WebsiteQuickSelectViewSet | ViewSet |
| openclaw/workflow_views.py | BidWorkflowViewSet | ViewSet |
| openclaw/workflow_views.py | TaskSchedulerViewSet | ViewSet |
| enterprise/views.py | EnterpriseMatchViewSet | ViewSet |
| enterprise/views.py | EnterpriseMatchResultViewSet | ReadOnlyModelViewSet |
| crawler/scheduler_views.py | QualificationMatchViewSet | ViewSet |

## 迁移示例

### EnterpriseViewSet迁移

**迁移前 (enterprise/views.py):**
```python
from core.viewsets import APIResponseMixin
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

class EnterpriseViewSet(APIResponseMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EnterpriseSerializer
    queryset = Enterprise.objects.all()
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
```

**迁移后:**
```python
from core.viewsets import AuthenticatedModelViewSet

class EnterpriseViewSet(AuthenticatedModelViewSet):
    serializer_class = EnterpriseSerializer
    queryset = Enterprise.objects.all()
    # filter_backends已自动配置
    # permission_classes已自动配置
```

### EnterpriseBidConfigViewSet迁移

**迁移前:**
```python
class EnterpriseBidConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EnterpriseBidConfigSerializer
    queryset = EnterpriseBidConfig.objects.all()
```

**迁移后:**
```python
class EnterpriseBidConfigViewSet(AuthenticatedModelViewSet):
    serializer_class = EnterpriseBidConfigSerializer
    queryset = EnterpriseBidConfig.objects.all()
```

## 注意事项

1. **保持向后兼容**: 迁移应逐步进行，确保每次迁移后系统仍能正常运行
2. **测试覆盖**: 每次迁移后应运行相关测试用例
3. **权限验证**: 确保迁移后的权限设置与原来一致
4. **过滤配置**: AuthenticatedModelViewSet自动配置了filter_backends，如需自定义需显式覆盖

## 自动化工具（规划中）

未来可以开发自动化迁移脚本：

```python
# migrate_viewsets.py
import re

def migrate_viewset(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # 替换import
    content = content.replace(
        'from core.viewsets import APIResponseMixin',
        'from core.viewsets import AuthenticatedModelViewSet'
    )

    # 替换继承
    content = content.replace(
        'APIResponseMixin, viewsets.ModelViewSet',
        'AuthenticatedModelViewSet'
    )

    with open(file_path, 'w') as f:
        f.write(content)
```
