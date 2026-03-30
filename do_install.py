import subprocess
import sys

print("Installing requirements...")

result = subprocess.run(
    [r'D:\共享文件\AUTO\.venv\Scripts\pip.exe', 'install', '-r', r'D:\共享文件\AUTO\backend\requirements_clean.txt'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])

print(f"\nReturn code: {result.returncode}")
