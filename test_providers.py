import requests
import json

# Login to get token
login_resp = requests.post(
    'http://localhost:8000/api/v1/auth/login/',
    json={'username': 'admin', 'password': 'admin123'}
)
print(f"Login status: {login_resp.status_code}")

data = login_resp.json()
if data.get('success'):
    token = data['data']['token']['access']
    print(f"Token obtained")

    # Test all providers
    resp = requests.post(
        'http://localhost:8000/api/v1/openclaw/llm-providers/test_all_providers/',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        json={
            'message': '你好，请回复"测试成功"'
        }
    )

    print(f"\nStatus: {resp.status_code}")
    print(f"Response: {resp.text}")
else:
    print(f"Login failed: {data}")
