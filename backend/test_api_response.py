"""
直接测试 API 响应格式
"""
import os
import sys
import django
import json

sys.path.insert(0, r'd:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ.setdefault('DB_PASSWORD', '123456')

django.setup()

from apps.tenders.views import TenderProjectListView
from django.test import RequestFactory

print("=" * 70)
print("测试 TenderProjectListView API 响应")
print("=" * 70)

factory = RequestFactory()
request = factory.get('/v1/tenders/?page=1&page_size=5')

from django.contrib.auth.models import User
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.get('/v1/tenders/?page=1&page_size=5')

from apps.tenders.views import TenderProjectListView

view = TenderProjectListView.as_view()
response = view(request)

print(f"\n状态码: {response.status_code}")
print(f"\n响应数据 (前500字符):")
data = response.data
print(f"  data type: {type(data)}")
if isinstance(data, dict):
    print(f"  keys: {list(data.keys())}")
    if 'results' in data:
        print(f"  results count: {len(data['results'])}")
        if data['results']:
            print(f"  first result keys: {list(data['results'][0].keys())}")
    if 'count' in data:
        print(f"  count: {data['count']}")

print("\n" + "=" * 70)
