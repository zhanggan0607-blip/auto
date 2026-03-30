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
]

pip = r'D:\共享文件\AUTO\.venv\Scripts\pip.exe'

for pkg in packages:
    print(f"Installing {pkg}...")
    for attempt in range(3):
        result = subprocess.run(
            [pip, 'install', pkg],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  OK")
            break
        else:
            print(f"  Attempt {attempt+1} failed, retrying...")
            time.sleep(2)
    else:
        print(f"  FAILED after 3 attempts")

# Verify
print("\nVerifying installation...")
for pkg in ['Django', 'rest_framework', 'corsheaders']:
    result = subprocess.run(
        [r'D:\共享文件\AUTO\.venv\Scripts\python.exe', '-c', f'import {pkg}; print(f"{pkg}: OK")'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(f"{pkg}: FAILED")
