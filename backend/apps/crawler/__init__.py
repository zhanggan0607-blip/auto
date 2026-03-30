"""
Django应用模块 - 采集配置

职责：
- 采集配置的模型定义（CrawlSource, CrawlSchedule等）
- 采集配置的API视图
- 采集配置的序列化器

注意：
- 爬虫实现在 backend/crawler/ 目录
- Celery任务在 backend/crawler/tasks.py
- 此目录只包含Django应用相关代码
"""
