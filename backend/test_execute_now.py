"""
测试 execute_now API
"""
import requests
import json

BASE_URL = "http://localhost:8081/api/v1"
TOKEN = "your-token-here"

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

print("=== 测试 execute_now API ===")
print(f"计划ID: 6 (上海政府采购)")

try:
    response = requests.post(
        f"{BASE_URL}/crawler/schedules/6/execute_now/",
        headers=headers,
        timeout=30
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
except Exception as e:
    print(f"错误: {e}")