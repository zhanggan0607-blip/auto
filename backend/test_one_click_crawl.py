"""
测试修改后的 one_click_automation 采集流程
"""
import os
import sys
import asyncio

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

import django
django.setup()

from apps.crawler.models import WebsiteTemplate


class MockWebsite:
    """模拟网站对象"""
    def __init__(self, code, name, website_type='government'):
        self.code = code
        self.name = name
        self.website_type = website_type


async def test_crawl_website():
    """测试 _crawl_website 方法"""
    from services.one_click_automation import OneClickAutomationService

    service = OneClickAutomationService()

    test_websites = [
        MockWebsite('china_gov', '中国政府采购网'),
        MockWebsite('shanghai_gov', '上海市政府采购网'),
    ]

    keywords = ['信息化', '软件']

    print("=" * 70)
    print("测试 one_click_automation 采集流程 (统一架构后)")
    print("=" * 70)

    for website in test_websites:
        print(f"\n--- 测试网站: {website.name} ({website.code}) ---")

        try:
            results = await service._crawl_website(website, keywords)

            if results:
                print(f"✅ 成功采集 {len(results)} 条数据")
                for i, item in enumerate(results[:3], 1):
                    print(f"   {i}. {item.get('title', 'N/A')[:50]}...")
            else:
                print(f"⚠️ 未采集到数据")

        except Exception as e:
            print(f"❌ 采集失败: {str(e)}")

    print("\n" + "=" * 70)


async def main():
    await test_crawl_website()


if __name__ == '__main__':
    asyncio.run(main())
