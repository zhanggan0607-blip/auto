"""
采集引擎模块

职责：
- 爬虫基类和实现（BaseCrawler, ShanghaiGovCrawler等）
- 反检测机制（anti_detection.py）
- 故障自愈机制（self_healing.py）
- Celery异步任务（tasks.py）

目录结构：
crawler/
├── base_crawler.py         # 爬虫基类
├── configurable_crawler.py # 可配置爬虫
├── shanghai_gov_crawler_v2.py # 上海政府采购爬虫
├── shanghai_construction_crawler.py # 上海建设工程爬虫
├── china_gov_crawler.py    # 中国政府采购爬虫
├── pyppeteer_crawler.py    # Pyppeteer动态爬虫
├── anti_detection.py       # 反检测机制
├── self_healing.py         # 故障自愈
├── cookie_manager.py       # Cookie管理
├── common_types.py         # 公共类型定义
└── tasks.py                # Celery异步任务

注意：
- Django模型在 apps/crawler/ 目录
- 此目录只包含爬虫实现代码
"""
