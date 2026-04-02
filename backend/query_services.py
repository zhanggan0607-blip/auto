import requests

login = requests.post('http://localhost:8000/api/v1/auth/login/', json={'username': 'admin', 'password': 'admin123'})
token = login.json()['data']['token']['access']
headers = {'Authorization': f'Bearer {token}'}
resp = requests.get('http://localhost:8000/api/v1/monitor/services/', headers=headers)
data = resp.json()['data']['list']
print(f'共 {len(data)} 个服务:\n')
for s in data:
    print(f"ID:{s['id']} | {s['display_name']:20} | {s['category_display']:8} | {s['description']}")