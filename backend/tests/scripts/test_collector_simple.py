"""
企业信息采集测试脚本 - 简化版
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_http_collector():
    """
    测试 HTTP 模式采集
    """
    from openclaw.skills.collector.enterprise_collector import EnterpriseInfoCollectorSkill
    
    skill = EnterpriseInfoCollectorSkill()
    
    test_companies = [
        "上海天齐智能建筑股份有限公司",
        "腾讯科技（深圳）有限公司",
    ]
    
    for company_name in test_companies:
        print(f"\n{'='*60}")
        print(f"测试 HTTP 模式采集: {company_name}")
        print('='*60)
        
        result = await skill.execute(
            company_name=company_name,
            mode='http',
            source='auto'
        )
        
        if result.success:
            print(f"\n✅ 采集成功!")
            print(f"数据源: {result.metadata.get('source')}")
            print(f"采集模式: {result.metadata.get('mode')}")
            print("\n采集到的数据:")
            for key, value in result.data.items():
                if value:
                    print(f"  {key}: {value}")
        else:
            print(f"\n❌ 采集失败: {result.error}")
            print(f"尝试的数据源: {result.metadata.get('sources_tried', [])}")
        
        await asyncio.sleep(2)


async def test_scrapling_simple():
    """
    测试 Scrapling 简单模式
    """
    print(f"\n{'='*60}")
    print("测试 Scrapling 简单模式")
    print('='*60)
    
    try:
        from scrapling.fetchers import Fetcher
        
        print("Scrapling Fetcher 已安装，尝试获取页面...")
        
        page = Fetcher.get('https://www.baidu.com', impersonate='chrome')
        
        if page:
            print(f"✅ 页面获取成功")
            print(f"页面标题: {page.css('title::text').get()}")
        else:
            print("❌ 页面获取失败")
            
    except ImportError as e:
        print(f"❌ Scrapling 未正确安装: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def test_skill_with_fallback():
    """
    测试 Skill 采集器（自动降级）
    """
    from openclaw.skills.collector.enterprise_collector import EnterpriseInfoCollectorSkill
    
    skill = EnterpriseInfoCollectorSkill()
    
    print(f"\n{'='*60}")
    print("测试 Skill 采集器（自动降级模式）")
    print('='*60)
    
    result = await skill.execute(
        company_name="上海天齐智能建筑股份有限公司",
        mode='auto',
        source='auto'
    )
    
    if result.success:
        print(f"\n✅ 采集成功!")
        print(f"数据源: {result.metadata.get('source')}")
        print(f"采集模式: {result.metadata.get('mode')}")
        print(f"字段数量: {result.metadata.get('fields_count')}")
        print("\n采集到的数据:")
        for key, value in result.data.items():
            if value:
                print(f"  {key}: {value}")
    else:
        print(f"\n❌ 采集失败: {result.error}")


async def main():
    """
    主函数
    """
    print("\n" + "="*60)
    print("企业信息采集测试")
    print("="*60)
    
    print("\n选择测试模式:")
    print("1. 测试 HTTP 模式采集")
    print("2. 测试 Scrapling 简单模式")
    print("3. 测试 Skill 自动降级模式")
    print("4. 运行所有测试")
    print("0. 退出")
    
    choice = input("\n请输入选择 (0-4): ").strip()
    
    if choice == '1':
        await test_http_collector()
    elif choice == '2':
        await test_scrapling_simple()
    elif choice == '3':
        await test_skill_with_fallback()
    elif choice == '4':
        await test_scrapling_simple()
        await test_http_collector()
        await test_skill_with_fallback()
    else:
        print("退出测试")


if __name__ == '__main__':
    asyncio.run(main())
