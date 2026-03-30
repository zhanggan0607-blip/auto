import subprocess
import sys

with open(r'D:\共享文件\AUTO\backend\requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read()

# Parse requirements
pkgs = []
for line in requirements.split('\n'):
    line = line.strip()
    if line and not line.startswith('#'):
        # Handle inline comments
        if '#' in line:
            line = line.split('#')[0].strip()
        pkgs.append(line)

# Install each package
for pkg in pkgs:
    if pkg:
        print(f"Installing {pkg}...")
        result = subprocess.run(
            [r'D:\共享文件\AUTO\.venv\Scripts\pip.exe', 'install', pkg],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"  OK")
        else:
            print(f"  FAILED: {result.stderr[:200]}")
