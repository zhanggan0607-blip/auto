"""
直接测试 tenders API 返回格式
"""
import os
import sys

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

import django
django.setup()

from apps.tenders.models import TenderProject

print("=" * 70)
print("直接检查 TenderProject 数据和序列化格式")
print("=" * 70)

# 检查数据
count = TenderProject.objects.count()
print(f"\n数据库 TenderProject 数量: {count}")

# 检查第一条数据
first = TenderProject.objects.first()
if first:
    print(f"\n第一条数据:")
    print(f"  id: {first.id}")
    print(f"  title: {first.title}")
    print(f"  status: {first.status}")
    print(f"  region: {first.region}")
    print(f"  source_url: {first.source_url}")

# 测试序列化
from apps.tenders.serializers import TenderProjectListSerializer
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User
from rest_framework.request import Request

factory = APIRequestFactory()
request = factory.get('/v1/tenders/')
request.user = User.objects.first() if User.objects.exists() else None

# 获取 queryset
queryset = TenderProject.objects.all()[:5]
serializer = TenderProjectListSerializer(queryset, many=True)

print(f"\n序列化后的数据 (前2条):")
for i, item in enumerate(serializer.data[:2]):
    print(f"  {i+1}. keys: {list(item.keys())}")
    print(f"     title: {item.get('title', 'N/A')}")
    print(f"     status: {item.get('status', 'N/A')}")

print("\n" + "=" * 70)
