"""
微服务架构设计文档

## 架构概览

### 当前架构 (单体应用)
```
┌─────────────────────────────────────────────────────────┐
│                      Django API                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Users   │ │ Tenders │ │  Bids   │ │Crawler │       │
│  │ Module  │ │ Module  │ │ Module  │ │ Module  │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │Documents│ │Enterprise│ │Notifs  │ │ Vector  │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
    PostgreSQL         Redis           Milvus
```

### 目标架构 (微服务)
```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                    (Kong/Nginx + JWT Auth)                       │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   User Service  │ │  Core API       │ │ Crawler Service │
│   (Django)      │ │  (Django+DRF)   │ │ (FastAPI+Pypp)  │
│   Port: 8001    │ │  Port: 8000     │ │  Port: 8002      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   AI Service    │ │ Notification    │ │  Task Service   │
│  (FastAPI+LLM)  │ │   Service       │ │  (Celery)       │
│   Port: 8003    │ │   (Channels)    │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    PostgreSQL            Redis              Milvus
```

## 服务划分

### 1. User Service (用户服务)
**职责**: 用户认证、权限管理、角色管理
**技术栈**: Django + DRF + SimpleJWT
**数据存储**: PostgreSQL (users库)
**API端点**:
- POST /api/v1/auth/login
- POST /api/v1/auth/register
- GET /api/v1/users/me
- PUT /api/v1/users/me

### 2. Core API Service (核心业务服务)
**职责**: 招标信息管理、投标管理、企业库管理
**技术栈**: Django + DRF
**数据存储**: PostgreSQL (bid_core库)
**API端点**:
- GET /api/v1/tenders/
- POST /api/v1/bids/
- GET /api/v1/enterprises/

### 3. Crawler Service (爬虫服务)
**职责**: 招标信息采集、网站数据抓取、代理池管理
**技术栈**: FastAPI + Pyppeteer + Playwright
**数据存储**: PostgreSQL (crawler库) + Redis (代理池)
**API端点**:
- POST /api/v1/crawler/tasks
- GET /api/v1/crawler/tasks/{id}
- POST /api/v1/crawler/proxy/rotate

### 4. AI Service (AI推理服务)
**职责**: Embedding生成、文本向量化、语义匹配
**技术栈**: FastAPI + sentence-transformers + vLLM
**数据存储**: Milvus (向量库)
**API端点**:
- POST /api/v1/ai/embed
- POST /api/v1/ai/similarity
- POST /api/v1/ai/match

### 5. Notification Service (通知服务)
**职责**: 实时通知、中标结果推送
**技术栈**: Django Channels + WebSocket
**数据存储**: PostgreSQL + Redis Pub/Sub

## 服务间通信

### 同步通信 (REST)
```python
# 服务间调用示例
import httpx

async def call_crawler_service(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://crawler-service:8002/api/v1/crawler/tasks",
            json={"url": url},
            timeout=30.0
        )
        return response.json()
```

### 异步通信 (Celery/RabbitMQ)
```python
# 异步任务示例
from celery import shared_task

@shared_task(name='crawler.fetch_tender')
def fetch_tender_task(tender_id: int):
    # 爬虫任务
    pass

@shared_task(name='ai.match_enterprise')
def match_enterprise_task(tender_id: int):
    # AI匹配任务
    pass
```

## 数据隔离策略

### 方案一: 数据库分离 (高隔离)
每个租户独立数据库
- 优点: 完全隔离、性能好
- 缺点: 资源成本高、管理复杂

### 方案二: Schema分离 (中等隔离)
PostgreSQL Schema隔离
- 优点: 成本低、易于备份
- 缺点: 需要schema切换

### 方案三: 行级隔离 (推荐)
所有表添加tenant_id
- 优点: 成本低、实现简单
- 缺点: 需要所有查询携带tenant_id

## 配置管理

### 环境变量
```bash
# docker-compose.yml
SERVICE_NAME=crawler-service
SERVICE_PORT=8002
DATABASE_URL=postgres://user:pass@postgres:5432/crawler
REDIS_URL=redis://redis:6379/1
```

### 服务注册
使用Consul或etcd进行服务发现
```yaml
# consul服务注册
{
  "service": {
    "name": "crawler-service",
    "port": 8002,
    "check": {
      "http": "http://crawler-service:8002/health",
      "interval": "10s"
    }
  }
}
```

## 部署策略

### 蓝绿部署
```bash
# 部署新版本
docker-compose -f docker-compose.blue.yml up -d

# 切换流量
nginx -s reload

# 回滚
docker-compose -f docker-compose.green.yml up -d
```

### 滚动更新
```bash
# Kubernetes滚动更新
kubectl rollout restart deployment/crawler-service
```

## 监控与告警

### 指标采集
- Prometheus + Grafana
- 各服务暴露 /metrics 端点

### 日志收集
- ELK Stack (Elasticsearch + Logstash + Kibana)
- 结构化日志 JSON格式

### 链路追踪
- Jaeger
- OpenTelemetry

## 迁移步骤

### 阶段1: 代码拆分 (1-2周)
1. 创建 crawler-service 独立仓库
2. 创建 ai-service 独立仓库
3. 提取公共模块到 shared/ 目录

### 阶段2: 数据拆分 (2-4周)
1. 迁移爬虫相关表到独立数据库
2. 迁移向量数据到独立Milvus实例
3. 实现服务间API调用

### 阶段3: 流量切换 (1-2周)
1. 配置API网关路由
2. 逐步切换流量
3. 监控异常

### 阶段4: 独立部署 (持续)
1. Kubernetes化
2. 自动扩缩容
3. 服务网格

## 预期收益

| 指标 | 当前 | 目标 |
|-----|-----|-----|
| 部署时间 | 30分钟 | 5分钟 |
| 故障影响范围 | 整个系统 | 单个服务 |
| 扩展性 | 整体扩展 | 服务独立扩展 |
| 开发效率 | 团队协作困难 | 服务独立迭代 |
"""
