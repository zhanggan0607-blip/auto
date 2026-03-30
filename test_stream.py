import requests
import json
import time

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

    # Test streaming chat - use the same format as frontend
    start_time = time.time()
    resp = requests.post(
        'http://localhost:8000/api/v1/openclaw/playground/stream_chat/',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        json={
            'provider_id': 1,
            'model_id': 'gemma3:1b',
            'message': '你好，请介绍一下你自己',
            'temperature': 0.7,
            'max_tokens': 500,
            'history': []
        },
        stream=True
    )

    print(f"\nStatus: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")

    if resp.status_code != 200:
        print(f"Error response: {resp.text}")
    else:
        print("\n--- Full streaming response (waiting for completion) ---")

        full_content = []
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    try:
                        data = json.loads(decoded[6:])
                        if 'content' in data:
                            full_content.append(data['content'])
                    except:
                        pass

        complete_content = ''.join(full_content)
        print(f"\nComplete content ({len(complete_content)} chars):")
        print(complete_content)

        end_time = time.time()
        print(f"\nTotal time: {end_time - start_time:.3f}s")
else:
    print(f"Login failed: {data}")
