# 爬虫模块迁移指南

## 概述

本文档指导将旧爬虫模块 (`backend/crawler/`) 迁移到新的公共爬虫架构 (`backend/common/crawler/`)。

## 背景

### 问题
- `backend/crawler/` 下有 **17个爬虫类**，大量重复代码
- `UserAgentManager`、`ProxyManager`、`AntiDetection` 等组件在多处重复实现
- 缺乏统一的策略模式，采集逻辑散落各处

### 解决方案
- 新增 `common/crawler/` 模块，提供统一的爬虫基础设施
- 采用策略模式，支持多种采集策略（API直连、requests、Selenium、Pyppeteer）
- 自动降级机制，提升采集成功率

---

## 新架构

```
backend/common/crawler/
├── __init__.py                 # 公共爬虫模块入口
├── managers/
│   ├── __init__.py
│   ├── user_agent_manager.py   # UA管理器
│   ├── proxy_manager.py        # 代理管理器
│   └── cookie_manager.py        # Cookie管理器
├── strategies/
│   ├── __init__.py
│   └── base_strategy.py         # 策略基类
└── common_crawler.py           # 统一爬虫基类
```

---

## 核心组件

### 1. UserAgentManager
```python
from common.crawler import UserAgentManager

ua_manager = UserAgentManager()
ua = ua_manager.get_random()      # 获取随机UA
ua = ua_manager.get_chrome()       # 获取Chrome UA
```

### 2. ProxyManager
```python
from common.crawler import ProxyManager

proxy_mgr = ProxyManager(proxy_list=['http://proxy1:8080', 'http://proxy2:8080'])
proxy = proxy_mgr.get_proxy(strategy='random')  # 随机策略
proxy = proxy_mgr.get_proxy(strategy='round_robin')  # 轮询策略
proxy_mgr.mark_success(proxy)  # 标记成功
proxy_mgr.mark_failed(proxy)   # 标记失败
```

### 3. CookieManager
```python
from common.crawler import CookieManager

cookie_mgr = CookieManager()
cookies = cookie_mgr.get_cookies('tianyancha')  # 获取Cookie
cookies_str = cookie_mgr.get_cookies_string('tianyancha')  # 获取Cookie字符串
pw_cookies = cookie_mgr.get_cookies_for_playwright('tianyancha')  # Playwright格式
```

### 4. CrawlStrategy (策略模式)
```python
from common.crawler import CrawlStrategy, RequestStrategy, SeleniumStrategy

# 请求策略（requests库）
strategy = RequestStrategy()

# Selenium策略（带反检测）
strategy = SeleniumStrategy()

# 执行采集
result = strategy.fetch(url, headers=headers, proxies=proxies)
```

### 5. CommonCrawler (统一爬虫基类)
```python
from common.crawler import CommonCrawler, CrawlerConfig, SeleniumStrategy

class MyCrawler(CommonCrawler):
    def parse_items(self, html: str) -> List[Dict]:
        # 实现解析逻辑
        pass

# 使用示例
crawler = MyCrawler(config=CrawlerConfig(headless=True))
result = crawler.crawl_with_retry(url)
```

---

## 迁移步骤

### 步骤1：替换导入

**Before:**
```python
from crawler.base_crawler import BaseCrawler, CrawlerConfig, UserAgentManager, ProxyManager, AntiDetection
from crawler.multi_strategy_crawler import MultiStrategyCrawler, CrawlStrategy
```

**After:**
```python
from common.crawler import CommonCrawler, CrawlerConfig
from common.crawler.managers import UserAgentManager, ProxyManager, CookieManager
from common.crawler.strategies import CrawlStrategy, RequestStrategy, SeleniumStrategy
```

### 步骤2：继承新基类

**Before:**
```python
class MyCrawler(BaseCrawler):
    def __init__(self, config=None):
        super().__init__(config)
        self.ua_manager = UserAgentManager()

    def crawl(self):
        ua = self.ua_manager.get_random()
        # ...
```

**After:**
```python
from common.crawler import CommonCrawler, CrawlerConfig, SeleniumStrategy

class MyCrawler(CommonCrawler):
    def __init__(self, config=None):
        config = config or CrawlerConfig(
            headless=True,
            request_delay_min=2.0,
            request_delay_max=4.0
        )
        super().__init__(config)
        self.set_strategy(SeleniumStrategy())

    def parse_items(self, html: str) -> List[Dict]:
        # 解析逻辑
        pass
```

### 步骤3：使用策略模式

**Before:**
```python
# 手动切换采集方式
if use_selenium:
    driver = webdriver.Chrome(options=options)
    content = driver.page_source
else:
    response = requests.get(url)
    content = response.text
```

**After:**
```python
from common.crawler import CommonCrawler, CrawlerConfig, RequestStrategy, SeleniumStrategy

class MyCrawler(CommonCrawler):
    def __init__(self):
        super().__init__(CrawlerConfig())
        # 默认使用Selenium策略
        self.set_strategy(SeleniumStrategy())

    def crawl_page(self, url: str):
        # 自动使用当前策略
        result = self.strategy.fetch(url)
        return result.content
```

### 步骤4：使用统一配置

**Before:**
```python
class MyCrawler:
    def __init__(self):
        self.headless = True
        self.timeout = 30
        self.request_delay = 2.0
        self.max_retries = 3
```

**After:**
```python
from common.crawler import CrawlerConfig

config = CrawlerConfig(
    headless=True,
    timeout=30,
    page_load_timeout=60,
    implicit_wait=10,
    request_delay_min=2.0,
    request_delay_max=4.0,
    max_retries=3,
    proxy_enabled=False,
    proxy_list=[],
    user_agent_rotation=True,
    cookies_enabled=True,
    javascript_enabled=True
)
```

---

## 废弃组件清单

以下文件将被废弃，不再推荐使用：

| 文件 | 建议替代 |
|------|----------|
| `crawler/base_crawler.py` | `common.crawler.CommonCrawler` |
| `crawler/anti_detection.py` | `common.crawler.strategies.SeleniumStrategy` |
| `crawler/cookie_manager.py` | `common.crawler.managers.CookieManager` |
| `crawler/multi_strategy_crawler.py` | `common.crawler.CommonCrawler` + 策略模式 |

---

## 新爬虫开发规范

```python
"""
示例：使用新架构开发爬虫
"""
from typing import List, Dict, Any
from common.crawler import CommonCrawler, CrawlerConfig, SeleniumStrategy

class ShanghaiGovCrawler(CommonCrawler):
    """上海政府采购网爬虫（使用新架构）"""

    def __init__(self):
        config = CrawlerConfig(
            headless=True,
            timeout=30,
            request_delay_min=2.0,
            request_delay_max=4.0,
            max_retries=3
        )
        super().__init__(config)
        self.set_strategy(SeleniumStrategy())

    def parse_items(self, html: str) -> List[Dict[str, Any]]:
        """解析页面获取招标列表"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        items = []
        for item in soup.select('.list-item'):
            title_elem = item.select_one('.title a')
            if title_elem:
                items.append({
                    'title': title_elem.get_text(strip=True),
                    'url': title_elem.get('href', ''),
                    'publish_date': item.select_one('.date').get_text(strip=True) if item.select_one('.date') else None
                })
        return items

    def crawl_notices(self, notice_type: str = None, page: int = 1) -> List[Dict]:
        """爬取公告"""
        url = f"https://www.zfcg.sh.gov.cn/search/?noticeType={notice_type}&page={page}"
        result = self.crawl_with_retry(url)
        return self.parse_items(result)
```

---

## 常见问题

### Q: 如何处理Cookie？
```python
from common.crawler import CookieManager

cookie_mgr = CookieManager()
# 获取Cookie
cookies = cookie_mgr.get_cookies('tianyancha')
# Playwright格式
pw_cookies = cookie_mgr.get_cookies_for_playwright('tianyancha')
```

### Q: 如何使用代理？
```python
from common.crawler import ProxyManager

proxy_mgr = ProxyManager(['http://proxy1:8080', 'http://proxy2:8080'])
proxy = proxy_mgr.get_proxy()  # 自动选择可用代理
```

### Q: 如何处理反检测？
```python
from common.crawler import SeleniumStrategy

strategy = SeleniumStrategy()
# 策略内部自动处理:
# - Chrome选项配置
# - 反检测JS注入
# - 浏览器指纹随机化
```

---

## 迁移检查清单

- [ ] 导入语句已更新为 common.crawler
- [ ] 继承关系已更新为 CommonCrawler
- [ ] 配置已迁移到 CrawlerConfig
- [ ] 策略模式已正确使用
- [ ] UserAgent管理已使用 UserAgentManager
- [ ] Proxy管理已使用 ProxyManager
- [ ] Cookie管理已使用 CookieManager
- [ ] 测试用例已更新

---

## 附录：完整导入对照表

| 旧导入 | 新导入 |
|--------|--------|
| `from crawler.base_crawler import BaseCrawler` | `from common.crawler import CommonCrawler` |
| `from crawler.base_crawler import CrawlerConfig` | `from common.crawler import CrawlerConfig` |
| `from crawler.base_crawler import UserAgentManager` | `from common.crawler.managers import UserAgentManager` |
| `from crawler.base_crawler import ProxyManager` | `from common.crawler.managers import ProxyManager` |
| `from crawler.cookie_manager import CookieManager` | `from common.crawler.managers import CookieManager` |
| `from crawler.anti_detection import AntiDetection` | `from common.crawler.strategies import SeleniumStrategy` |
| `from crawler.multi_strategy_crawler import MultiStrategyCrawler` | `from common.crawler import CommonCrawler` |

---

## 附录：废弃文件清单

详见: [CRAWLER_DEPRECATION_CHECKLIST.md](./CRAWLER_DEPRECATION_CHECKLIST.md)

**最后更新**: 2026-04-04
**维护者**: 架构组
**版本**: v1.0
