"""
测试 Scrapling 隐身模式采集 - 多数据源
"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from scrapling.fetchers import StealthyFetcher, Fetcher
from urllib.parse import quote

def test_source(name, url, use_stealth=True):
    print(f"\n{'='*60}")
    print(f"测试数据源: {name}")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        if use_stealth:
            page = StealthyFetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                solve_cloudflare=True
            )
        else:
            page = Fetcher.get(url, impersonate='chrome')
        
        if page:
            print(f"页面获取成功! 状态码: {page.status if hasattr(page, 'status') else 'N/A'}")
            
            if hasattr(page, 'css'):
                title = page.css('title::text').get()
                print(f"页面标题: {title}")
            
            html_content = None
            if hasattr(page, 'html'):
                html_content = page.html
            elif hasattr(page, 'text'):
                html_content = page.text
            elif hasattr(page, 'content'):
                html_content = page.content
            
            if html_content:
                print(f"内容长度: {len(html_content)} 字符")
                
                data_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
                if data_match:
                    try:
                        data = json.loads(data_match.group(1))
                        print(f"找到 JSON 数据! 键: {list(data.keys())[:5]}")
                        return True, data
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                credit_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', html_content)
                if credit_match:
                    print(f"找到信用代码: {credit_match.group(1)}")
                    return True, {'credit_code': credit_match.group(1)}
                
                legal_match = re.search(r'法定代表人[：:]\s*([^\s<]+)', html_content)
                if legal_match:
                    print(f"找到法人: {legal_match.group(1)}")
                
                if '登录' in html_content or 'login' in html_content.lower():
                    print("页面需要登录!")
                
                return True, None
            else:
                print("无法获取页面内容")
        else:
            print("页面获取失败")
            
    except Exception as e:
        print(f"采集失败: {e}")
    
    return False, None

def main():
    company_name = "腾讯科技（深圳）有限公司"
    
    sources = [
        ('企查查', f'https://www.qcc.com/web/search?key={quote(company_name)}', True),
        ('爱企查', f'https://aiqicha.baidu.com/s?q={quote(company_name)}', True),
        ('启信宝', f'https://www.qixin.com/search?key={quote(company_name)}', True),
        ('百度企业信用', f'https://xin.baidu.com/s?q={quote(company_name)}', False),
    ]
    
    print(f"测试企业: {company_name}")
    
    for name, url, use_stealth in sources:
        success, data = test_source(name, url, use_stealth)
        if success and data:
            print(f"\n成功从 {name} 获取数据!")
            break

if __name__ == '__main__':
    main()
