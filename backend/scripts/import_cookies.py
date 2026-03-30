"""
Cookie 导入和测试脚本

使用方法:
1. 在浏览器中登录天眼查/企查查等平台
2. 打开浏览器开发者工具 (F12)
3. 切换到 Network 标签页
4. 刷新页面，找到任意请求
5. 在请求头中找到 Cookie 字段，复制完整值
6. 运行此脚本导入Cookie

示例:
    python scripts/import_cookies.py tianyancha "auth_token=xxx; TYCID=xxx; ssuid=xxx"
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from crawler.cookie_manager import cookie_manager
from crawler.cookie_based_collector import collect_with_cookies


def import_cookies(platform: str, cookie_string: str, expire_hours: int = 24):
    """
    导入Cookie
    
    Args:
        platform: 平台名称
        cookie_string: Cookie字符串
        expire_hours: 过期时间（小时）
    """
    print(f"\n{'='*60}")
    print(f"导入 {platform} Cookie")
    print('='*60)
    
    success = cookie_manager.import_from_browser(
        platform=platform,
        cookie_string=cookie_string
    )
    
    if success:
        cookie_manager.save_cookies(
            platform=platform,
            cookies=cookie_manager.get_cookies(platform),
            expire_hours=expire_hours
        )
        print(f"✅ Cookie导入成功!")
        print(f"   过期时间: {expire_hours}小时后")
        print(f"   Cookie数量: {len(cookie_manager.get_cookies(platform))}")
        return True
    else:
        print("❌ Cookie导入失败，请检查格式")
        return False


def show_cookie_status():
    """显示所有平台的Cookie状态"""
    print(f"\n{'='*60}")
    print("Cookie 状态")
    print('='*60)
    
    status_data = cookie_manager.get_status()
    
    for platform, info in status_data.items():
        status_icon = "✅" if info['valid'] else "❌"
        print(f"\n{status_icon} {platform}")
        print(f"   有效: {'是' if info['valid'] else '否'}")
        print(f"   Cookie数量: {info['cookie_count']}")
        if info.get('expire_at'):
            print(f"   过期时间: {info['expire_at']}")


async def test_collect(company_name: str, source: str = 'auto'):
    """测试采集"""
    print(f"\n{'='*60}")
    print(f"测试采集: {company_name}")
    print('='*60)
    
    result = await collect_with_cookies(company_name, source)
    
    if result.get('success'):
        print("\n✅ 采集成功!")
        print(f"数据源: {result.get('source')}")
        print(f"尝试的平台: {result.get('sources_tried')}")
        print("\n采集到的数据:")
        for key, value in result.get('data', {}).items():
            if value:
                print(f"  {key}: {value}")
    else:
        print(f"\n❌ 采集失败: {result.get('error')}")
        print(f"尝试的平台: {result.get('sources_tried')}")


def interactive_import():
    """交互式导入"""
    print("\n" + "="*60)
    print("企业信息采集 - Cookie导入工具")
    print("="*60)
    
    print("\n支持的平台:")
    print("  1. tianyancha - 天眼查")
    print("  2. qichacha - 企查查")
    print("  3. aiqicha - 爱企查")
    print("  4. qixin - 启信宝")
    
    print("\n如何获取Cookie:")
    print("  1. 在浏览器中登录对应平台")
    print("  2. 按F12打开开发者工具")
    print("  3. 切换到Network标签页")
    print("  4. 刷新页面")
    print("  5. 点击任意请求，找到Request Headers中的Cookie")
    print("  6. 复制完整的Cookie值")
    
    platform = input("\n请输入平台名称 (如 tianyancha): ").strip()
    
    if platform not in cookie_manager.PLATFORMS:
        print(f"❌ 不支持的平台: {platform}")
        return
    
    print(f"\n请粘贴 {platform} 的Cookie (粘贴后按回车):")
    cookie_string = input().strip()
    
    if not cookie_string:
        print("❌ Cookie不能为空")
        return
    
    expire_hours = input("过期时间(小时，默认24): ").strip()
    expire_hours = int(expire_hours) if expire_hours else 24
    
    if import_cookies(platform, cookie_string, expire_hours):
        test = input("\n是否测试采集? (y/n): ").strip().lower()
        if test == 'y':
            company_name = input("请输入企业名称: ").strip()
            if company_name:
                asyncio.run(test_collect(company_name, platform))


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'status':
            show_cookie_status()
        
        elif command == 'import' and len(sys.argv) >= 4:
            platform = sys.argv[2]
            cookie_string = sys.argv[3]
            expire_hours = int(sys.argv[4]) if len(sys.argv) > 4 else 24
            import_cookies(platform, cookie_string, expire_hours)
        
        elif command == 'test' and len(sys.argv) >= 3:
            company_name = sys.argv[2]
            source = sys.argv[3] if len(sys.argv) > 3 else 'auto'
            asyncio.run(test_collect(company_name, source))
        
        elif command == 'clear':
            platform = sys.argv[2] if len(sys.argv) > 2 else None
            cookie_manager.clear_cookies(platform)
            print(f"✅ 已清除 {platform or '所有平台'} 的Cookie")
        
        else:
            print("用法:")
            print("  python scripts/import_cookies.py status                    # 查看Cookie状态")
            print("  python scripts/import_cookies.py import <平台> <Cookie>    # 导入Cookie")
            print("  python scripts/import_cookies.py test <企业名> [平台]      # 测试采集")
            print("  python scripts/import_cookies.py clear [平台]              # 清除Cookie")
            print("  python scripts/import_cookies.py                           # 交互式导入")
    else:
        interactive_import()


if __name__ == '__main__':
    main()
