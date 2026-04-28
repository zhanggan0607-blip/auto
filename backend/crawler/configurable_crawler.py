"""
爬虫模块 - 配置化爬虫

.. deprecated::
    请使用 `common.crawler.common_crawler.CommonCrawler` 替代
    此模块将在未来版本中移除
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from .base_crawler import BaseCrawler, CrawlerConfig, SelectorConfig

logger = logging.getLogger(__name__)


class ConfigurableCrawler(BaseCrawler):
    """
    配置化爬虫 - 通过配置驱动爬取逻辑
    """
    
    def __init__(self, config: CrawlerConfig = None, selector: SelectorConfig = None, 
                 base_url: str = '', source_code: str = ''):
        """
        初始化配置化爬虫
        
        Args:
            config: 爬虫配置
            selector: 选择器配置
            base_url: 基础URL
            source_code: 来源代码
        """
        super().__init__(config)
        self.selector = selector or SelectorConfig()
        self.base_url = base_url
        self.source_code = source_code
    
    def crawl(self, keywords: List[str] = None, page: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        爬取招标信息
        
        Args:
            keywords: 关键词列表
            page: 页码
            page_size: 每页数量
            
        Returns:
            list: 招标数据列表
        """
        results = []
        
        try:
            self.init_driver()
            
            list_url = self._build_list_url(page, page_size)
            html = self.get_page(list_url, wait_selector=self.selector.list_container)
            
            if not html:
                logger.error("获取列表页面失败")
                return results
            
            soup = self.parse_html(html)
            items = self._extract_items(soup)
            
            for item in items:
                try:
                    tender_data = self._parse_tender_item(item)
                    if tender_data:
                        if keywords:
                            if self._match_keywords(tender_data, keywords):
                                results.append(tender_data)
                        else:
                            results.append(tender_data)
                except Exception as e:
                    logger.error(f"解析招标项目失败: {str(e)}")
                    continue
            
            logger.info(f"爬取完成，共获取 {len(results)} 条数据")
            
        except Exception as e:
            logger.error(f"爬取招标信息失败: {str(e)}")
        finally:
            self.close_driver()
        
        return results
    
    def _build_list_url(self, page: int, page_size: int) -> str:
        """
        构建列表URL
        """
        return self.base_url
    
    def _extract_items(self, soup: BeautifulSoup) -> List:
        """
        提取项目列表
        """
        if self.selector.item_container:
            items = soup.select(self.selector.item_container)
        else:
            items = soup.select('.list-item, .project-item, .item, tr[data-id], li[data-id]')
        
        return items
    
    def _parse_tender_item(self, item) -> Dict[str, Any]:
        """
        解析单个招标项目
        """
        try:
            title = self._extract_text(item, self.selector.title or 'a, .title, .project-title')
            if not title:
                return None
            
            link = self._extract_link(item, self.selector.link or 'a')
            if link and not link.startswith('http'):
                link = f"{self.base_url}{link}"
            
            publish_date = self._extract_text(item, self.selector.date or '.date, .time, .publish-date')
            publish_date = self._parse_date(publish_date) if publish_date else None
            
            region = self._extract_text(item, self.selector.region or '.region, .area')
            project_code = self._extract_text(item, self.selector.project_code or '.code, .project-code')
            budget = self._extract_text(item, self.selector.budget or '.budget, .amount')
            
            return {
                'title': title,
                'source_url': link,
                'publish_date': publish_date,
                'region': region,
                'project_code': project_code,
                'budget': self._parse_budget(budget) if budget else None,
                'source_type': self.source_code,
            }
        except Exception as e:
            logger.error(f"解析招标项目详情失败: {str(e)}")
            return None
    
    def _extract_text(self, item, selector: str) -> Optional[str]:
        """
        提取文本
        """
        try:
            selectors = selector.split(', ')
            for sel in selectors:
                elem = item.select_one(sel.strip())
                if elem:
                    return elem.get_text(strip=True)
        except Exception:
            pass
        return None
    
    def _extract_link(self, item, selector: str) -> Optional[str]:
        """
        提取链接
        """
        try:
            elem = item.select_one(selector)
            if elem:
                return elem.get('href', '')
        except Exception:
            pass
        return None
    
    def _match_keywords(self, tender_data: Dict, keywords: List[str]) -> bool:
        """
        匹配关键词
        """
        title = tender_data.get('title', '').lower()
        description = tender_data.get('description', '').lower()
        text = f"{title} {description}"
        
        return any(kw.lower() in text for kw in keywords)
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        解析日期字符串
        """
        if not date_str:
            return None
        
        patterns = [
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
            (r'(\d{4}/\d{2}/\d{2})', '%Y/%m/%d'),
            (r'(\d{4}年\d{1,2}月\d{1,2}日)', '%Y年%m月%d日'),
            (r'(\d{2}-\d{2}-\d{4})', '%m-%d-%Y'),
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    dt = datetime.strptime(match.group(1), date_format)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _parse_budget(self, budget_str: str) -> Optional[float]:
        """
        解析预算金额
        """
        if not budget_str:
            return None
        
        budget_str = budget_str.replace(',', '').replace('，', '')
        
        patterns = [
            (r'(\d+\.?\d*)\s*万', 10000),
            (r'(\d+\.?\d*)\s*亿', 100000000),
            (r'(\d+\.?\d*)\s*元', 1),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, budget_str)
            if match:
                try:
                    return float(match.group(1)) * multiplier
                except ValueError:
                    continue
        
        numbers = re.findall(r'\d+\.?\d*', budget_str)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    def get_tender_detail(self, url: str) -> Dict[str, Any]:
        """
        获取招标详情
        """
        try:
            html = self.get_page(url, wait_selector=self.selector.detail_content)
            if not html:
                return {}
            
            soup = self.parse_html(html)
            
            content = ''
            if self.selector.detail_content:
                content_elem = soup.select_one(self.selector.detail_content)
                if content_elem:
                    content = content_elem.get_text(strip=True)
            
            info = {}
            info_items = soup.select('.info-item, .detail-item, tr')
            for item in info_items:
                label_elem = item.select_one('th, .label, .name')
                value_elem = item.select_one('td, .value')
                if label_elem and value_elem:
                    label = label_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    info[label] = value
            
            return {
                'description': content,
                'raw_data': info
            }
        except Exception as e:
            logger.error(f"获取招标详情失败: {url}, 错误: {str(e)}")
            return {}


class CrawlerFactory:
    """
    爬虫工厂类
    """
    
    _crawlers = {}
    
    @classmethod
    def register(cls, source_code: str, crawler_class, config: CrawlerConfig = None, 
                 selector: SelectorConfig = None, base_url: str = ''):
        """
        注册爬虫
        """
        cls._crawlers[source_code] = {
            'class': crawler_class,
            'config': config,
            'selector': selector,
            'base_url': base_url
        }
    
    @classmethod
    def create(cls, source_code: str) -> Optional[BaseCrawler]:
        """
        创建爬虫实例
        """
        if source_code not in cls._crawlers:
            logger.error(f"未注册的爬虫来源: {source_code}")
            return None
        
        crawler_info = cls._crawlers[source_code]
        crawler_class = crawler_info['class']
        
        return crawler_class(
            config=crawler_info.get('config'),
            selector=crawler_info.get('selector'),
            base_url=crawler_info.get('base_url', ''),
            source_code=source_code
        )
    
    @classmethod
    def get_registered_sources(cls) -> List[str]:
        """
        获取已注册的来源列表
        """
        return list(cls._crawlers.keys())


def _get_website_base_url(code: str, default_url: str = None) -> str:
    """
    从PILOT_WEBSITES配置获取网站base_url

    Args:
        code: 网站代码
        default_url: 默认URL（当配置中不存在时使用）
    """
    try:
        from django.conf import settings
        for website in settings.PILOT_WEBSITES:
            if website['code'] == code:
                return website['base_url']
    except Exception:
        pass
    return default_url or ''


def register_default_crawlers():
    """
    注册默认爬虫
    """
    from .shanghai_construction_crawler import ShanghaiConstructionCrawler
    from .shanghai_gov_procurement_crawler import ShanghaiGovProcurementCrawler

    shanghai_selector = SelectorConfig(
        list_container='.list-container, .project-list',
        item_container='.list-item, .project-item',
        title='.title a, .project-title a',
        link='.title a, .project-title a',
        date='.date, .publish-date',
        region='.region, .area',
        project_code='.code, .project-code',
        budget='.budget, .amount',
        detail_content='.content, .detail-content'
    )

    shanghai_config = CrawlerConfig(
        headless=True,
        request_delay_min=2.0,
        request_delay_max=4.0,
        max_retries=3
    )

    shanghai_gov_base_url = _get_website_base_url('shanghai_gov', 'https://www.zfcg.sh.gov.cn')

    CrawlerFactory.register(
        source_code='shanghai_gov',
        crawler_class=ConfigurableCrawler,
        config=shanghai_config,
        selector=shanghai_selector,
        base_url=shanghai_gov_base_url
    )

    CrawlerFactory.register(
        source_code='shanghai_gov_procurement',
        crawler_class=ShanghaiGovProcurementCrawler,
        config=shanghai_config,
        selector=shanghai_selector,
        base_url=shanghai_gov_base_url
    )


register_default_crawlers()
