"""
招标文件下载适配器
提供统一的下载接口，支持多网站适配器模式
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DownloadedFile:
    """下载文件信息"""
    name: str
    path: str
    type: str
    size: int
    url: str


class BaseDownloadAdapter(ABC):
    """
    下载适配器基类
    各网站具体下载逻辑在此实现
    """

    @property
    @abstractmethod
    def website_type(self) -> str:
        """网站类型标识"""
        pass

    @abstractmethod
    async def download_tender_files(self, url: str, tender_id: int, **kwargs) -> Dict[str, Any]:
        """
        下载招标文件

        Args:
            url: 招标文件URL
            tender_id: 招标项目ID
            **kwargs: 其他参数

        Returns:
            dict: 包含files列表的字典
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        判断是否支持该URL

        Args:
            url: 文件URL

        Returns:
            bool: 是否支持
        """
        pass


class ShanghaiGovDownloadAdapter(BaseDownloadAdapter):
    """
    上海政府采购网下载适配器
    """

    @property
    def website_type(self) -> str:
        return 'shanghai'

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        url_lower = url.lower()
        return 'zfcg.sh.gov.cn' in url_lower or 'sh.gov.cn' in url_lower

    async def download_tender_files(self, url: str, tender_id: int, **kwargs) -> Dict[str, Any]:
        try:
            from crawler.shanghai_gov_crawler_v2 import ShanghaiGovCrawler
            crawler = ShanghaiGovCrawler()
            result = await crawler.download_tender_files(url=url, tender_id=tender_id)
            return result
        except Exception as e:
            logger.error(f"上海政府采购网下载失败: {str(e)}")
            return {'files': [], 'error': str(e)}


class ChinaGovDownloadAdapter(BaseDownloadAdapter):
    """
    中国政府采购网下载适配器
    """

    @property
    def website_type(self) -> str:
        return 'china_gov'

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        url_lower = url.lower()
        return 'ccgp.gov.cn' in url_lower or 'ccgp' in url_lower

    async def download_tender_files(self, url: str, tender_id: int, **kwargs) -> Dict[str, Any]:
        try:
            from crawler.china_gov_crawler import ChinaGovCrawler
            crawler = ChinaGovCrawler()
            result = await crawler.download_tender_files(url=url, tender_id=tender_id)
            return result
        except Exception as e:
            logger.error(f"中国政府采购网下载失败: {str(e)}")
            return {'files': [], 'error': str(e)}


class GenericDownloadAdapter(BaseDownloadAdapter):
    """
    通用下载适配器
    处理未知网站的下载请求
    """

    @property
    def website_type(self) -> str:
        return 'generic'

    def can_handle(self, url: str) -> bool:
        return True

    async def download_tender_files(self, url: str, tender_id: int, **kwargs) -> Dict[str, Any]:
        logger.warning(f"通用下载适配器处理: {url}")
        return {
            'files': [],
            'error': '该网站暂不支持自动下载，请手动下载',
            'suggestion': '请前往原始链接手动下载招标文件'
        }


class DownloadAdapterManager:
    """
    下载适配器管理器
    实现适配器模式，提供统一的下载接口
    """

    _instance = None
    _adapters: List[BaseDownloadAdapter] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_adapters()
        return cls._instance

    def _initialize_adapters(self):
        """初始化所有适配器"""
        self._adapters = [
            ShanghaiGovDownloadAdapter(),
            ChinaGovDownloadAdapter(),
            GenericDownloadAdapter(),
        ]
        logger.info(f"下载适配器初始化完成: {[a.website_type for a in self._adapters]}")

    def get_adapter(self, url: str) -> BaseDownloadAdapter:
        """
        获取适合该URL的适配器

        Args:
            url: 文件URL

        Returns:
            BaseDownloadAdapter: 适配器实例
        """
        for adapter in self._adapters:
            if adapter.can_handle(url):
                logger.debug(f"匹配到下载适配器: {adapter.website_type} for {url}")
                return adapter
        return self._adapters[-1]

    async def download_tender_files(self, url: str, tender_id: int, **kwargs) -> Dict[str, Any]:
        """
        统一的下载接口

        Args:
            url: 招标文件URL
            tender_id: 招标项目ID
            **kwargs: 其他参数

        Returns:
            dict: 包含files列表的字典
        """
        if not url:
            logger.warning(f"下载URL为空: tender_id={tender_id}")
            return {'files': [], 'error': 'URL为空'}

        adapter = self.get_adapter(url)
        logger.info(f"使用下载适配器: {adapter.website_type} for tender_id={tender_id}")

        try:
            return await adapter.download_tender_files(url, tender_id, **kwargs)
        except Exception as e:
            logger.error(f"下载失败: {str(e)}")
            return {'files': [], 'error': str(e)}


download_adapter_manager = DownloadAdapterManager()
