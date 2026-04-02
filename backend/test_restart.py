import requests

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc0OTMzNzEwLCJpYXQiOjE3NzQ5MjY1MTAsImp0aSI6IjlhOTdmZGVjMGUwMDQxYzJhMWU2ZjdlMGQxNTYyMDRhIiwidXNlcl9pZCI6IjEifQ.eu9NJLtL389VzqKV6gyvoTFmTT6u1yb04fnLxKKsUU0'
headers = {'Authorization': f'Bearer {token}'}

# 测试重启服务9 (milvus_vector_db)
restart_resp = requests.post('http://localhost:8000/api/v1/monitor/services/9/restart/', headers=headers)
print(f'Restart status: {restart_resp.status_code}')
print(f'Restart response: {restart_resp.text[:500]}')