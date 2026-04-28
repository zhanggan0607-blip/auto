# -*- coding: utf-8 -*-
"""
站点配置模板
===========
复制此文件，改名为你的站点（如 ccgp_gov.py），然后修改三处：
1. __init__ 中的 URL 和参数
2. parse_list_page 的 XPath
3. parse_detail_page 的 XPath
"""
from datetime import datetime
from typing import Dict, List

from lxml import etree

from ..human_like_crawler import SiteConfig


class TemplateSiteConfig(SiteConfig):
    """模板站点配置 —— 复制后修改"""

    def __init__(self):
        super().__init__(
            site_name="template",
            base_url="https://www.example.com",
            list_url_template="https://www.example.com/list?page={page}",
            total_pages=3,
            max_detail_per_page=3,
            daily_limit=100,
            use_proxy=False,
            proxy_str="",
            save_dir="./crawl_results",
            explore_pages=[
                "https://www.example.com/about",
            ],
        )

    def parse_list_page(self, html: str) -> List[str]:
        """
        从列表页HTML提取详情页链接
        修改 XPath 匹配目标网站的列表结构
        """
        tree = etree.HTML(html)
        links = tree.xpath('//div[contains(@class,"list")]//a/@href')
        return links

    def parse_detail_page(self, html: str, url: str) -> Dict:
        """
        从详情页HTML提取结构化数据
        修改 XPath 匹配目标网站的详情页结构
        """
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
        except Exception:
            pass
        return data
