import requests
import json

# First login to get token
login_url = "http://localhost:8000/api/v1/auth/login/"
login_data = {"username": "admin", "password": "admin123"}

print("Step 1: Login...")
login_resp = requests.post(login_url, json=login_data)
print(f"Login status: {login_resp.status_code}")

if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.text[:200]}")
    exit(1)

# Check if token is in cookie
token_from_cookie = login_resp.cookies.get('access_token')
print(f"Token from cookie: {token_from_cookie}")

# Also check response body
try:
    login_json = login_resp.json()
    token_from_body = login_json.get('data', {}).get('access_token')
    print(f"Token from body: {token_from_body[:30] if token_from_body else 'None'}...")
except:
    token_from_body = None

token = token_from_body or token_from_cookie
if not token:
    print("No token found!")
    exit(1)

# Now test stream_chat
print("\nStep 2: Testing stream_chat...")
stream_url = "http://localhost:8000/api/v1/openclaw/playground/stream_chat/"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
data = {
    "provider_id": 1,
    "model_id": "qwen3:8b",
    "message": "测试",
    "temperature": 0.7,
    "max_tokens": 50,
    "history": []
}

try:
    resp = requests.post(stream_url, headers=headers, json=data, stream=True, timeout=30)
    print(f"Stream status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")

    if resp.status_code == 200:
        for i, line in enumerate(resp.iter_lines()):
            if line:
                print(line.decode('utf-8'))
                if i >= 10:
                    break
    else:
        print(f"Error: {resp.text[:300]}")
except Exception as e:
    print(f"Exception: {e}")
