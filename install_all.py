import subprocess
import sys
import time

packages = [
    'Django==4.2.7',
    'djangorestframework==3.14.0',
    'djangorestframework-simplejwt==5.3.0',
    'django-cors-headers==4.3.1',
    'django-filter==23.5',
    'python-dotenv==1.0.0',
    'psycopg2-binary==2.9.9',
    'channels==4.0.0',
    'daphne==4.0.0',
    'gunicorn==21.2.0',
    'django-redis==5.4.0',
    'django-celery-beat==2.5.0',
    'celery==5.3.4',
    'redis==5.0.1',
    'kombu==5.3.4',
    'websockets>=10.0,<11.0',
    'selenium==4.15.2',
    'pyppeteer==1.0.2',
    'beautifulsoup4==4.12.2',
    'requests==2.31.0',
    'aiohttp==3.9.1',
    'chromadb==0.4.22',
    'openai==1.7.2',
    'sentence-transformers==2.2.2',
    'numpy>=1.24.0',
    'pymilvus==2.3.4',
    'minio==7.2.3',
    'python-docx==1.1.0',
    'PyPDF2==3.0.1',
    'alibabacloud-ocr-api20210707==3.1.3',
    'alibabacloud-tea-openapi>=0.3.14',
    'alibabacloud-darabonba-env==0.0.1',
    'DingtalkChatbot==1.5.7',
    'fastapi==0.109.0',
    'uvicorn[standard]==0.27.0',
    'pydantic==2.5.3',
    'pydantic-settings==2.1.0',
    'python-multipart==0.0.6',
    'sse-starlette==1.8.2',
    'starlette==0.32.0',
    'cryptography==41.0.7',
    'django-debug-toolbar==4.2.0',
    'pytest==7.4.3',
    'pytest-django==4.7.0',
    'pytest-cov==4.1.0',
    'pytest-asyncio==0.21.1',
    'redis[hiredis]==5.0.1',
    'drf-spectacular==0.27.0',
]

pip = r'D:\共享文件\AUTO\.venv\Scripts\pip.exe'
failed = []

for pkg in packages:
    print(f"Installing {pkg}...", end=" ")
    for attempt in range(3):
        result = subprocess.run(
            [pip, 'install', pkg, '--quiet'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("OK")
            break
        else:
            if attempt < 2:
                time.sleep(3)
    else:
        print("FAILED")
        failed.append(pkg)

print(f"\n=== Summary ===")
if failed:
    print(f"Failed packages ({len(failed)}):")
    for p in failed:
        print(f"  - {p}")
else:
    print("All packages installed successfully!")

print("\nVerifying core packages...")
core = ['Django', 'rest_framework', 'celery', 'fastapi', 'chromadb']
for pkg in core:
    result = subprocess.run(
        [r'D:\共享文件\AUTO\.venv\Scripts\python.exe', '-c', f'import {pkg}; print("{pkg}: OK")'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(f"{pkg}: NOT INSTALLED")
