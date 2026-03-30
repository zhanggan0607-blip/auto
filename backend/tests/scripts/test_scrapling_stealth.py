"""
测试 Scrapling 隐身模式采集
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from scrapling.fetchers import StealthyFetcher

def test_scrapling():
    company_name = "上海天齐智能建筑股份有限公司"
    url = f"https://www.tianyancha.com/search?key={company_name}"
    
    print(f"测试 Scrapling 隐身模式采集")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            solve_cloudflare=True
        )
        
        if page:
            print("页面获取成功!")
            print(f"页面标题: {page.css('title::text').get()}")
            
            text = page.text[:2000] if page.text else "无文本内容"
            print(f"\n页面内容预览:\n{text}")
            
            import re
            import json
            
            html = page.html
            
            data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    print("\n找到 JSON 数据!")
                    print(f"数据键: {list(data.keys())[:10]}")
                except (json.JSONDecodeError, KeyError):
                    pass
            
            company_selectors = [
                '.search-result-item',
                '.company-item',
                '.index_search-result__item',
                '[class*="search"]',
            ]
            
            for selector in company_selectors:
                elements = page.css(selector)
                if elements:
                    print(f"\n找到 {len(elements)} 个元素: {selector}")
                    break
        else:
            print("页面获取失败")
            
    except Exception as e:
        print(f"采集失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_scrapling()
