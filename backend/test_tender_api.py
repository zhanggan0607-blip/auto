"""
测试招标项目 API
"""
import os
import sys
import django

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

django.setup()

from apps.tenders.models import TenderProject

print("=" * 70)
print("检查 TenderProject 数据")
print("=" * 70)

print(f"\n总记录数: {TenderProject.objects.count()}")

projects = TenderProject.objects.all()[:5]
print(f"前5条数据:")

for p in projects:
    print(f"\n  ID: {p.id}")
    print(f"  标题: {p.title}")
    print(f"  状态: {p.status}")
    print(f"  发布日期: {p.publish_date}")
    print(f"  地区: {p.region}")
    print(f"  原始链接: {p.source_url}")

print("\n" + "=" * 70)
