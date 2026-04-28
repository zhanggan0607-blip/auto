#!/bin/bash
set -e

echo "=== 天齐AI投标平台 启动中 ==="

echo "--- 收集静态文件 ---"
python manage.py collectstatic --noinput 2>/dev/null || echo "collectstatic skipped (non-critical)"

echo "--- 检查数据库迁移 ---"
python manage.py migrate --noinput 2>/dev/null || echo "migrate skipped (will retry)"

echo "--- 启动服务 ---"
exec "$@"
