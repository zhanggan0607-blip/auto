# -*- coding: utf-8 -*-
"""
中国政府采购网站点配置 (ccgp.gov.cn)
====================================
适合 requests + lxml 静态HTML采集
"""
from datetime import datetime
from typing import Dict, List
from urllib.parse import urljoin

from lxml import etree

from ..human_like_crawler import SiteConfig


class CcgpGovConfig(SiteConfig):
    """中国政府采购网配置"""

    NOTICE_TYPE_MAP = {
        "gkzb": {"name": "公开招标公告", "path": "/cggg/dfgg/gkzb/"},
        "jzxcs": {"name": "竞争性磋商公告", "path": "/cggg/dfgg/jzxcs/"},
        "jzxtp": {"name": "竞争性谈判公告", "path": "/cggg/dfgg/jzxtp/"},
        "xjcg": {"name": "询价公告", "path": "/cggg/dfgg/xjgg/"},
        "zbjg": {"name": "中标公告", "path": "/cggg/dfgg/zbgg/"},
        "gzgg": {"name": "更正公告", "path": "/cggg/dfgg/gzgg/"},
    }

    def __init__(
        self,
        notice_type: str = "gkzb",
        total_pages: int = 5,
        max_detail_per_page: int = 5,
        daily_limit: int = 100,
    ):
        notice_info = self.NOTICE_TYPE_MAP.get(notice_type, self.NOTICE_TYPE_MAP["gkzb"])
        self.notice_type = notice_type
        self.notice_name = notice_info["name"]
        self.notice_path = notice_info["path"]

        super().__init__(
            site_name=f"ccgp_{notice_type}",
            base_url="http://www.ccgp.gov.cn",
            list_url_template=f"http://www.ccgp.gov.cn{self.notice_path}index.htm",
            total_pages=total_pages,
            max_detail_per_page=max_detail_per_page,
            daily_limit=daily_limit,
            explore_pages=[
                "http://www.ccgp.gov.cn/about/",
            ],
        )

    def get_list_url(self, page: int) -> str:
        if page == 1:
            return self.list_url_template
        base = self.list_url_template.replace("index.htm", "")
        return f"{base}index_{page}.htm"

    def normalize_url(self, link: str) -> str:
        if link.startswith("http"):
            return link
        return urljoin(self.base_url, link)

    def parse_list_page(self, html: str) -> List[str]:
        tree = etree.HTML(html)
        links = tree.xpath('//ul[@class="c_list_bid"]//li/a/@href')
        if not links:
            links = tree.xpath('//ul[@class="list_con"]//li/a/@href')
        if not links:
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
            "notice_type": self.notice_name,
        }
        try:
            title = tree.xpath('//h2[@class="tc"]//text()')
            if not title:
                title = tree.xpath('//h2[@class="detail_title"]//text()')
            if not title:
                title = tree.xpath("//h2//text()")
            data["title"] = title[0].strip() if title else ""

            content = tree.xpath('//div[@class="vF_detail_content"]//text()')
            if not content:
                content = tree.xpath('//div[contains(@class,"content")]//text()')
            data["content"] = "\n".join([p.strip() for p in content if p.strip()])

            pub_time = tree.xpath('//div[@class="vF_detail_header"]//p[@class="tc"]//text()')
            if not pub_time:
                pub_time = tree.xpath('//span[contains(@class,"time")]//text()')
            if not pub_time:
                pub_time = tree.xpath('//td[contains(text(),"发布时间")]//following-sibling::td//text()')
            data["publish_time"] = pub_time[0].strip() if pub_time else ""
        except Exception:
            pass
        return data
