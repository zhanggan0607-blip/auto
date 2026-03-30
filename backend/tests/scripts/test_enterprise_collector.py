"""
企业信息采集测试脚本
测试 Scrapling + AI 语义提取
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scrapling_collector():
    """
    测试 Scrapling 采集器
    """
    from crawler.scrapling_enterprise_collector import ScraplingEnterpriseCollector
    
    test_companies = [
        "上海天齐智能建筑股份有限公司",
        "腾讯科技（深圳）有限公司",
        "阿里巴巴（中国）有限公司",
    ]
    
    collector = ScraplingEnterpriseCollector(use_ai=True)
    
    for company_name in test_companies:
        print(f"\n{'='*60}")
        print(f"测试采集: {company_name}")
        print('='*60)
        
        try:
            result = await collector.collect(company_name)
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"\n✅ 采集成功!")
                print(f"数据源: {result.get('source')}")
                print(f"尝试的数据源: {result.get('sources_tried')}")
                print("\n采集到的数据:")
                for key, value in data.items():
                    if value:
                        print(f"  {key}: {value}")
            else:
                print(f"\n❌ 采集失败: {result.get('error')}")
                print(f"尝试的数据源: {result.get('sources_tried')}")
                
        except Exception as e:
            print(f"\n❌ 采集异常: {str(e)}")
        
        await asyncio.sleep(2)


async def test_browser_collector():
    """
    测试浏览器采集器
    """
    from crawler.enterprise_browser_crawler import EnterpriseBrowserCollector
    from crawler.stealth_crawler import ProxyConfig
    
    test_companies = [
        "上海天齐智能建筑股份有限公司",
    ]
    
    proxy_config = ProxyConfig(enabled=False)
    collector = EnterpriseBrowserCollector(
        proxy_config=proxy_config,
        ocr_service=None
    )
    
    for company_name in test_companies:
        print(f"\n{'='*60}")
        print(f"测试浏览器采集: {company_name}")
        print('='*60)
        
        try:
            result = await collector.collect(company_name)
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"\n✅ 采集成功!")
                print(f"数据源: {result.get('source')}")
                print("\n采集到的数据:")
                for key, value in data.items():
                    if value:
                        print(f"  {key}: {value}")
            else:
                print(f"\n❌ 采集失败: {result.get('error')}")
                
        except Exception as e:
            print(f"\n❌ 采集异常: {str(e)}")


async def test_skill_collector():
    """
    测试 Skill 采集器
    """
    from openclaw.skills.collector.enterprise_collector import EnterpriseInfoCollectorSkill
    
    skill = EnterpriseInfoCollectorSkill()
    
    print(f"\n{'='*60}")
    print("测试 Skill 采集器")
    print('='*60)
    
    result = await skill.execute(
        company_name="上海天齐智能建筑股份有限公司",
        mode="browser",
        source="auto"
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


def check_dependencies():
    """
    检查依赖
    """
    print("\n检查依赖...")
    
    dependencies = [
        ('scrapling', 'Scrapling 库'),
        ('pyppeteer', 'Pyppeteer 库'),
        ('aiohttp', 'Aiohttp 库'),
    ]
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name} 已安装")
        except ImportError:
            print(f"  ❌ {display_name} 未安装")
    
    print("\n可选依赖:")
    
    optional_deps = [
        ('scrapling.fetchers', 'Scrapling Fetchers (pip install scrapling[fetchers])'),
        ('scrapling.ai', 'Scrapling AI (pip install scrapling[ai])'),
    ]
    
    for module_name, display_name in optional_deps:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name} 已安装")
        except ImportError:
            print(f"  ⚠️ {display_name} 未安装")


async def main():
    """
    主函数
    """
    print("\n" + "="*60)
    print("企业信息采集测试")
    print("="*60)
    
    check_dependencies()
    
    print("\n选择测试模式:")
    print("1. 测试 Scrapling 采集器")
    print("2. 测试浏览器采集器")
    print("3. 测试 Skill 采集器")
    print("4. 运行所有测试")
    print("0. 退出")
    
    choice = input("\n请输入选择 (0-4): ").strip()
    
    if choice == '1':
        await test_scrapling_collector()
    elif choice == '2':
        await test_browser_collector()
    elif choice == '3':
        await test_skill_collector()
    elif choice == '4':
        await test_scrapling_collector()
        await test_browser_collector()
        await test_skill_collector()
    else:
        print("退出测试")


if __name__ == '__main__':
    asyncio.run(main())
