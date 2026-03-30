@echo off
REM Celery Worker 启动脚本
cd /d %~dp0backend
set DJANGO_SETTINGS_MODULE=config.settings.development
echo Starting Celery Worker...
celery -A config.celery worker -l info -Q default,crawler
pause
