"""
采集源注册中心 - 统一管理所有采集源的注册信息

新增采集源只需在此文件中添加一条 CRAWL_SOURCE_CONFIG 记录即可，
无需修改 tasks.py、tender_collector.py、one_click_automation.py 等多个文件。

使用方式:
    from crawler.crawl_source_registry import crawl_source_registry

    # 获取爬虫类
    crawler_class = crawl_source_registry.get_crawler_class('sh_construction')

    # 获取所有已注册的源代码
    source_codes = crawl_source_registry.get_source_codes()

    # 判断源是否已注册
    if crawl_source_registry.is_registered('sh_construction'):
        ...
"""
import logging
from typing import Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class CrawlSourceConfig:
    """
    单个采集源的配置

    Attributes:
        source_code: 数据源代码（唯一标识）
        crawler_class: 爬虫类
        aliases: 数据源别名列表（如 sh_gov 是 shanghai_gov 的别名）
        description: 数据源描述
        supports_max_pages: 爬虫是否支持 max_pages 参数
    """

    def __init__(self, source_code, crawler_class, aliases=None, description='', supports_max_pages=True):
        self.source_code = source_code
        self.crawler_class = crawler_class
        self.aliases = aliases or []
        self.description = description
        self.supports_max_pages = supports_max_pages


class CrawlSourceRegistry:
    """
    采集源注册中心

    统一管理所有采集源的注册、查询和调度。
    新增采集源只需调用 register() 方法。
    """

    def __init__(self):
        self._sources: Dict[str, CrawlSourceConfig] = {}
        self._alias_map: Dict[str, str] = {}

    def register(self, source_code: str, crawler_class: Type, aliases: List[str] = None,
                 description: str = '', supports_max_pages: bool = True):
        """
        注册采集源

        Args:
            source_code: 数据源代码（唯一标识）
            crawler_class: 爬虫类（必须有 crawl 方法）
            aliases: 数据源别名列表
            description: 数据源描述
            supports_max_pages: 爬虫是否支持 max_pages 参数
        """
        config = CrawlSourceConfig(
            source_code=source_code,
            crawler_class=crawler_class,
            aliases=aliases,
            description=description,
            supports_max_pages=supports_max_pages,
        )
        self._sources[source_code] = config

        if aliases:
            for alias in aliases:
                self._alias_map[alias] = source_code

        logger.debug(f"注册采集源: {source_code} -> {crawler_class.__name__} (别名: {aliases})")

    def is_registered(self, source_code: str) -> bool:
        """判断源是否已注册（包括别名）"""
        resolved = self._alias_map.get(source_code, source_code)
        return resolved in self._sources

    def get_crawler_class(self, source_code: str) -> Optional[Type]:
        """获取爬虫类"""
        resolved = self._alias_map.get(source_code, source_code)
        config = self._sources.get(resolved)
        return config.crawler_class if config else None

    def get_source_codes(self) -> List[str]:
        """获取所有已注册的主源代码（不含别名）"""
        return list(self._sources.keys())

    def get_all_codes_and_aliases(self) -> List[str]:
        """获取所有已注册的源代码（含别名）"""
        codes = list(self._sources.keys())
        codes.extend(self._alias_map.keys())
        return codes

    def resolve_source(self, source_code: str) -> str:
        """
        解析源代码（别名转主代码）

        Args:
            source_code: 可能是别名的源代码

        Returns:
            str: 主源代码
        """
        return self._alias_map.get(source_code, source_code)

    def supports_max_pages(self, source_code: str) -> bool:
        """判断源是否支持 max_pages 参数"""
        resolved = self._alias_map.get(source_code, source_code)
        config = self._sources.get(resolved)
        return config.supports_max_pages if config else False

    def get_config(self, source_code: str) -> Optional[CrawlSourceConfig]:
        """获取采集源配置"""
        resolved = self._alias_map.get(source_code, source_code)
        return self._sources.get(resolved)


crawl_source_registry = CrawlSourceRegistry()


def _auto_register_sources():
    """
    自动注册所有已知采集源

    新增采集源只需在此函数中添加一条 register 调用即可。
    """
    try:
        from crawler.china_gov_crawler import ChinaGovCrawler
        crawl_source_registry.register(
            source_code='china_gov',
            crawler_class=ChinaGovCrawler,
            aliases=['ccgp', 'zbtb'],
            description='中国政府采购网',
            supports_max_pages=True,
        )
    except ImportError:
        pass

    try:
        from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
        crawl_source_registry.register(
            source_code='shanghai_gov',
            crawler_class=ShanghaiGovCrawler,
            aliases=['sh_gov'],
            description='上海市政府采购网',
            supports_max_pages=True,
        )
    except ImportError:
        pass

    try:
        from crawler.shanghai_gov_procurement_crawler import ShanghaiGovProcurementCrawler
        crawl_source_registry.register(
            source_code='sh_procurement',
            crawler_class=ShanghaiGovProcurementCrawler,
            description='上海市政府采购网（采购）',
            supports_max_pages=True,
        )
    except ImportError:
        pass

    try:
        from crawler.shanghai_construction_crawler import ShanghaiConstructionCrawler
        crawl_source_registry.register(
            source_code='sh_construction',
            crawler_class=ShanghaiConstructionCrawler,
            description='上海建筑建材业',
            supports_max_pages=True,
        )
    except ImportError:
        pass


_auto_register_sources()
