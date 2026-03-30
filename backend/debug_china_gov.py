"""
诊断 china_gov 采集问题 - 关键词过滤
"""
import os
import sys

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from crawler.china_gov_crawler import ChinaGovCrawler

crawler = ChinaGovCrawler()
url = "http://www.ccgp.gov.cn/cggg/dfgg/gkzb/"
html = crawler._fetch_page(url)

if html:
    soup = crawler.parse_html(html)
    items = crawler._extract_items(soup)

    print(f"找到 {len(items)} 个 items\n")

    keywords = ['信息化', '软件']
    print(f"关键词过滤测试: {keywords}")
    print("=" * 60)

    matched = 0
    for i, item in enumerate(items):
        tender_data = crawler._parse_item(item, 'gkzb')
        if not tender_data:
            print(f"  Item {i+1}: 解析失败")
            continue

        title = tender_data.get('title', '')
        title_lower = title.lower()
        keywords_lower = [kw.lower() for kw in keywords]

        kw_match = any(kw in title_lower for kw in keywords_lower)
        print(f"\n  Item {i+1}:")
        print(f"    标题: {title[:50]}...")
        print(f"    关键词匹配: {kw_match}")
        if kw_match:
            matched += 1
            print(f"    ✓ 匹配成功")
        else:
            print(f"    ✗ 匹配失败")

    print("\n" + "=" * 60)
    print(f"总匹配数: {matched}/{len(items)}")
