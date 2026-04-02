"""
Celery Worker 状态检查脚本
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from celery import Celery
from config.celery import app

if __name__ == '__main__':
    try:
        inspect = app.control.inspect(timeout=5)
        stats = inspect.stats()

        if stats:
            print("=" * 50)
            print("Celery Worker 状态: RUNNING")
            print("=" * 50)
            for worker, info in stats.items():
                print(f"\nWorker: {worker}")
                print(f"  Pool: {info.get('pool', 'N/A')}")
                print(f"  并发数: {info.get('concurrency', 'N/A')}")
                print(f"  队列: {info.get('queues', 'N/A')}")
            print("=" * 50)
        else:
            print("Celery Worker 未响应（可能未运行）")

    except Exception as e:
        print(f"检查失败: {e}")
        sys.exit(1)
