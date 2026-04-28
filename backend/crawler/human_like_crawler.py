# -*- coding: utf-8 -*-
"""
真人行为模拟爬虫引擎
===================
设计原则：引擎与站点配置分离
- 引擎负责：请求调度、延时策略、Referer链路、会话管理、去重、断点续爬
- 站点配置负责：URL模板、XPath解析规则、站点特征参数

新增网站只需继承 SiteConfig 并实现解析方法即可
"""
import hashlib
import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

BROWSER_HEADERS_TEMPLATE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "DNT": "1",
}


@dataclass
class SiteConfig(ABC):
    """
    站点配置基类 —— 新增网站只需继承此类并实现抽象方法
    """
    site_name: str = "default"
    base_url: str = ""
    list_url_template: str = ""
    total_pages: int = 3
    max_detail_per_page: int = 3
    daily_limit: int = 100
    use_proxy: bool = False
    proxy_str: str = ""
    save_dir: str = "./crawl_results"
    explore_pages: List[str] = field(default_factory=list)

    @abstractmethod
    def parse_list_page(self, html: str) -> List[str]:
        """从列表页HTML中提取详情页链接列表"""

    @abstractmethod
    def parse_detail_page(self, html: str, url: str) -> Dict:
        """从详情页HTML中提取结构化数据，返回字典"""

    def normalize_url(self, link: str) -> str:
        """将相对URL补全为绝对URL"""
        if link.startswith("/"):
            return self.base_url + link
        if "http" not in link:
            return f"{self.base_url}/{link}"
        return link

    def get_list_url(self, page: int) -> str:
        """生成第page页的列表页URL"""
        return self.list_url_template.format(page=page)


class HumanBehaviorEngine:
    """
    真人行为模拟引擎
    ================
    核心策略：
    1. Referer 链路 —— 列表→详情带来源页
    2. 阅读时间挂钩内容长度
    3. 批次爬取 + 长休息
    4. 穿插探索行为（访问无关页面）
    5. UA 每会话随机
    6. 去重 + 断点续爬
    """

    def __init__(self, site_config: SiteConfig):
        self.config = site_config
        self.session: Optional[requests.Session] = None
        self.current_ua: str = ""
        self.crawled_count: int = 0
        self.crawled_urls: set = set()
        self._progress_file = os.path.join(
            site_config.save_dir, f".progress_{site_config.site_name}.json"
        )
        os.makedirs(site_config.save_dir, exist_ok=True)

    def _load_progress(self):
        """加载断点续爬记录"""
        if os.path.exists(self._progress_file):
            try:
                with open(self._progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.crawled_urls = set(data.get("crawled_urls", []))
                    self.crawled_count = data.get("crawled_count", 0)
                    logger.info(
                        f"[断点续爬] 已加载 {len(self.crawled_urls)} 条历史记录"
                    )
            except Exception:
                self.crawled_urls = set()
                self.crawled_count = 0

    def _save_progress(self):
        """保存爬取进度"""
        try:
            with open(self._progress_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "crawled_urls": list(self.crawled_urls),
                        "crawled_count": self.crawled_count,
                        "last_update": datetime.now().isoformat(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"[进度保存失败] {e}")

    def _is_crawled(self, url: str) -> bool:
        """URL去重检查"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return url_hash in self.crawled_urls

    def _mark_crawled(self, url: str):
        """标记URL已爬取"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self.crawled_urls.add(url_hash)

    def _create_session(self) -> requests.Session:
        """创建带重试和浏览器指纹的HTTP会话"""
        self.current_ua = random.choice(UA_POOL)
        headers = {**BROWSER_HEADERS_TEMPLATE, "User-Agent": self.current_ua}

        session = requests.Session()
        session.headers.update(headers)

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        if self.config.use_proxy and self.config.proxy_str:
            session.proxies = {
                "http": self.config.proxy_str,
                "https": self.config.proxy_str,
            }

        return session

    @staticmethod
    def _random_sleep(min_sec: float, max_sec: float, label: str = ""):
        """随机延时，模拟人阅读/等待"""
        sleep_time = random.uniform(min_sec, max_sec)
        if label:
            logger.debug(f"[延时] {label} {sleep_time:.2f}s")
        time.sleep(sleep_time)

    def _reading_sleep(self, content_length: int):
        """根据内容长度计算阅读停留时间"""
        chars_per_second = random.uniform(5, 8)
        base_time = content_length / chars_per_second if content_length > 0 else 0
        overhead = random.uniform(2, 5)
        total = min(base_time + overhead, 60)
        logger.debug(f"[阅读] 内容{content_length}字，停留{total:.1f}s")
        time.sleep(total)

    def _batch_break(self, batch_index: int):
        """批次间长休息"""
        break_time = random.uniform(30, 120)
        logger.info(f"[批次休息] 第{batch_index}批完成，休息{break_time:.0f}s")
        time.sleep(break_time)

    def _explore_page(self, url: str, referer: str):
        """模拟探索行为：访问无关页面"""
        try:
            self.session.get(
                url,
                timeout=15,
                headers={
                    "Referer": referer,
                    "Sec-Fetch-Site": "same-origin",
                },
            )
            self._random_sleep(2, 5, "探索")
        except Exception as e:
            logger.debug(f"[探索跳过] {url}: {e}")

    def _visit_homepage(self):
        """访问首页建立会话和Cookie"""
        logger.info("[行为] 访问首页建立会话...")
        try:
            self.session.get(self.config.base_url, timeout=15)
        except Exception as e:
            logger.warning(f"[首页访问失败] {e}")
        self._random_sleep(3, 6, "首页停留")

        if "cookie_consent" not in self.session.cookies.get_dict():
            domain = self.config.base_url.replace("https://", "").replace(
                "http://", ""
            )
            self.session.cookies.set("cookie_consent", "true", domain=domain)

    def _crawl_detail(self, url: str, referer: str) -> Optional[Dict]:
        """爬取单条详情页"""
        if self._is_crawled(url):
            logger.debug(f"[跳过] 已爬取: {url}")
            return None

        if self.crawled_count >= self.config.daily_limit:
            logger.info(f"[限额] 已达每日上限 {self.config.daily_limit} 条")
            return None

        try:
            resp = self.session.get(
                url,
                timeout=15,
                headers={
                    "Referer": referer,
                    "Sec-Fetch-Site": "same-origin",
                },
            )
            if resp.status_code != 200:
                logger.warning(f"[状态码异常] {resp.status_code} {url}")
                return None

            data = self.config.parse_detail_page(resp.text, url)
            self._mark_crawled(url)
            self.crawled_count += 1
            return data

        except requests.RequestException as e:
            logger.warning(f"[请求失败] {url}: {e}")
            return None

    def _save_item(self, item: Dict):
        """保存单条结果"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.config.site_name}_{date_str}.txt"
        filepath = os.path.join(self.config.save_dir, filename)

        line = (
            f"========== {item.get('crawl_time', '')} ==========\n"
            f"链接：{item.get('url', '')}\n"
            f"标题：{item.get('title', '')}\n"
            f"时间：{item.get('publish_time', '')}\n"
            f"内容：\n{item.get('content', '')}\n\n"
        )
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(line)

    def run(self):
        """执行爬取主流程"""
        logger.info("=" * 60)
        logger.info(f"开始【{self.config.site_name}】真人模拟爬取")
        logger.info(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"每日限额：{self.config.daily_limit} 条")
        logger.info("=" * 60)

        self._load_progress()
        self.session = self._create_session()

        self._visit_homepage()

        if self.config.explore_pages and random.random() < 0.3:
            page_url = random.choice(self.config.explore_pages)
            self._explore_page(page_url, self.config.base_url + "/")

            self.session.get(
                self.config.base_url,
                timeout=15,
                headers={"Referer": page_url},
            )
            self._random_sleep(1, 3, "返回首页")

        batch_size = random.randint(3, 7)
        items_in_batch = 0

        for page in range(1, self.config.total_pages + 1):
            if self.crawled_count >= self.config.daily_limit:
                break

            list_url = self.config.get_list_url(page)
            logger.info(f"\n{'='*20} 列表第 {page} 页：{list_url} {'='*20}")

            try:
                resp = self.session.get(
                    list_url,
                    timeout=15,
                    headers={
                        "Referer": self.config.base_url + "/",
                        "Sec-Fetch-Site": "same-origin",
                    },
                )
                if resp.status_code != 200:
                    logger.warning(f"列表页状态码异常：{resp.status_code}")
                    continue

                detail_links = self.config.parse_list_page(resp.text)
                detail_links = [self.config.normalize_url(l) for l in detail_links]
                logger.info(f"本页找到 {len(detail_links)} 条链接")

                random.shuffle(detail_links)
                target_links = detail_links[: self.config.max_detail_per_page]
                logger.info(f"随机选取 {len(target_links)} 条爬取")

                for idx, url in enumerate(target_links, 1):
                    if self.crawled_count >= self.config.daily_limit:
                        break

                    self._random_sleep(2, 5, "列表→详情")
                    logger.info(f"[{page}-{idx}] 详情：{url}")

                    data = self._crawl_detail(url, referer=list_url)
                    if data:
                        self._save_item(data)
                        content_len = len(data.get("content", ""))
                        self._reading_sleep(content_len)

                        items_in_batch += 1
                        if items_in_batch >= batch_size:
                            self._batch_break(page)
                            batch_size = random.randint(3, 7)
                            items_in_batch = 0

            except requests.RequestException as e:
                logger.warning(f"[列表页请求失败] {list_url}: {e}")
                self._random_sleep(10, 30, "错误后退避")

            if page % 3 == 0 and random.random() < 0.4:
                logger.info("[休息] 回首页看看")
                self.session.get(self.config.base_url, timeout=15)
                self._random_sleep(5, 15, "首页休息")

        self._save_progress()
        logger.info(f"\n爬取完成！本会话共 {self.crawled_count} 条")
        logger.info(f"结果保存在：{self.config.save_dir}")


class ExampleSiteConfig(SiteConfig):
    """
    示例站点配置
    ===========
    复制此类并修改即可适配新网站，只需改三个地方：
    1. 构造函数中的 URL 和参数
    2. parse_list_page 的 XPath
    3. parse_detail_page 的 XPath
    """

    def __init__(self):
        super().__init__(
            site_name="example",
            base_url="https://www.example.com",
            list_url_template="https://www.example.com/list?page={page}",
            total_pages=3,
            max_detail_per_page=3,
            daily_limit=100,
            explore_pages=[
                "https://www.example.com/about",
                "https://www.example.com/contact",
            ],
        )

    def parse_list_page(self, html: str) -> List[str]:
        tree = etree.HTML(html)
        links = tree.xpath('//div[contains(@class,"list")]//a/@href')
        return links

    def parse_detail_page(self, html: str, url: str) -> Dict:
        tree = etree.HTML(html)
        data = {
            "url": url,
            "title": "",
            "content": "",
            "publish_time": "",
            "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            title = tree.xpath("//h1/text()")
            data["title"] = title[0].strip() if title else ""

            content = tree.xpath('//div[@class="content"]//text()')
            data["content"] = "\n".join([p.strip() for p in content if p.strip()])

            pub_time = tree.xpath('//span[@class="time"]/text()')
            data["publish_time"] = pub_time[0].strip() if pub_time else ""
        except Exception as e:
            logger.warning(f"[解析出错] {url}: {e}")
        return data


SITE_REGISTRY: Dict[str, type] = {}


def register_site(name: str):
    """站点注册装饰器，新增网站用 @register_site('site_name') 注册"""
    def decorator(cls):
        SITE_REGISTRY[name] = cls
        return cls
    return decorator


def get_site_config(name: str, **kwargs) -> SiteConfig:
    """通过名称获取站点配置实例"""
    if name not in SITE_REGISTRY:
        available = ", ".join(SITE_REGISTRY.keys()) or "无"
        raise ValueError(f"未知站点 '{name}'，可用站点：{available}")
    return SITE_REGISTRY[name](**kwargs)


def list_sites() -> List[str]:
    """列出所有已注册的站点"""
    return list(SITE_REGISTRY.keys())


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        from .sites.ccgp_gov import CcgpGovConfig
        register_site("ccgp_gkzb")(CcgpGovConfig)
        register_site("ccgp_jzxcs")(lambda: CcgpGovConfig(notice_type="jzxcs"))
        register_site("ccgp_zbjg")(lambda: CcgpGovConfig(notice_type="zbjg"))
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="真人行为模拟爬虫")
    parser.add_argument("--site", "-s", default="example", help="站点名称")
    parser.add_argument("--list", "-l", action="store_true", help="列出可用站点")
    parser.add_argument("--pages", "-p", type=int, default=None, help="列表页数")
    parser.add_argument("--limit", type=int, default=None, help="每日限额")
    args = parser.parse_args()

    if args.list:
        sites = list_sites()
        print(f"可用站点：{', '.join(sites) if sites else '无（请先注册站点配置）'}")
        exit(0)

    config = ExampleSiteConfig()
    if args.pages:
        config.total_pages = args.pages
    if args.limit:
        config.daily_limit = args.limit

    engine = HumanBehaviorEngine(config)
    engine.run()
