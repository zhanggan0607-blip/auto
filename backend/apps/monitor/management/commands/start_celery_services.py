"""
Celery服务自动启动管理命令
当检测到Celery服务未运行时，自动启动Worker和Beat
"""
import logging
import platform
import subprocess
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '自动检测并启动Celery服务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='仅检查服务状态，不启动',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重启服务',
        )

    def handle(self, *args, **options):
        check_only = options.get('check_only', False)
        force = options.get('force', False)

        if platform.system() != 'Windows':
            self.stdout.write(self.style.ERROR('此命令仅支持Windows系统'))
            return

        worker_running = self._is_celery_worker_running()
        beat_running = self._is_celery_beat_running()

        self.stdout.write(f'Celery Worker状态: {"运行中" if worker_running else "未运行"}')
        self.stdout.write(f'Celery Beat状态: {"运行中" if beat_running else "未运行"}')

        if check_only:
            return

        if not worker_running or force:
            self._start_celery_worker(force=force)

        if not beat_running or force:
            self._start_celery_beat(force=force)

        time.sleep(2)

        worker_ok = self._is_celery_worker_running()
        beat_ok = self._is_celery_beat_running()

        if worker_ok and beat_ok:
            self.stdout.write(self.style.SUCCESS('所有Celery服务已启动'))
        else:
            self.stdout.write(self.style.WARNING(f'Celery Worker: {"✓" if worker_ok else "✗"}, Celery Beat: {"✓" if beat_ok else "✗"}'))

    def _is_celery_worker_running(self):
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    name = proc.info['name'] or ''
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)
                    else:
                        cmdline_str = ''
                    if 'celery' in name.lower() and 'worker' in cmdline_str.lower():
                        return True
                    if 'celery.exe' in name.lower() and 'worker' in cmdline_str.lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        except Exception as e:
            logger.error(f'检查Celery Worker状态失败: {e}')
            return False

    def _is_celery_beat_running(self):
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    name = proc.info['name'] or ''
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)
                    else:
                        cmdline_str = ''
                    if 'celery' in name.lower() and 'beat' in cmdline_str.lower():
                        return True
                    if 'celery.exe' in name.lower() and 'beat' in cmdline_str.lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        except Exception as e:
            logger.error(f'检查Celery Beat状态失败: {e}')
            return False

    def _start_celery_worker(self, force=False):
        try:
            self.stdout.write('正在启动Celery Worker...')

            cmd = ['d:\\共享文件\\AUTO\\venv\\Scripts\\celery.exe', '-A', 'config', 'worker', '--loglevel=info', '-P', 'solo', '-Q', 'celery,crawler,default']

            env = {
                'DJANGO_SETTINGS_MODULE': 'config.settings.development',
                'CELERY_BROKER_URL': settings.CELERY_BROKER_URL,
                'CELERY_RESULT_BACKEND': getattr(settings, 'CELERY_RESULT_BACKEND', settings.CELERY_BROKER_URL),
                'PYTHONPATH': 'C:/Users/ZhangGan/AppData/Local/Programs/Python/Python312/Lib/site-packages;d:/共享文件/AUTO/backend'
            }

            process_env = subprocess.os.environ.copy()
            process_env.update(env)

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            if force:
                self._kill_celery_worker()

            subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                cwd='d:/共享文件/AUTO/backend',
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.stdout.write(self.style.SUCCESS('Celery Worker启动命令已执行'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'启动Celery Worker失败: {e}'))

    def _start_celery_beat(self, force=False):
        try:
            self.stdout.write('正在启动Celery Beat...')

            cmd = ['d:\\共享文件\\AUTO\\venv\\Scripts\\celery.exe', '-A', 'config', 'beat', '--loglevel=info']

            env = {
                'DJANGO_SETTINGS_MODULE': 'config.settings.development',
                'CELERY_BROKER_URL': settings.CELERY_BROKER_URL,
                'CELERY_RESULT_BACKEND': getattr(settings, 'CELERY_RESULT_BACKEND', settings.CELERY_BROKER_URL),
                'PYTHONPATH': 'C:/Users/ZhangGan/AppData/Local/Programs/Python/Python312/Lib/site-packages;d:/共享文件/AUTO/backend'
            }

            process_env = subprocess.os.environ.copy()
            process_env.update(env)

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            if force:
                self._kill_celery_beat()

            subprocess.Popen(
                cmd,
                startupinfo=startupinfo,
                cwd='d:/共享文件/AUTO/backend',
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.stdout.write(self.style.SUCCESS('Celery Beat启动命令已执行'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'启动Celery Beat失败: {e}'))

    def _kill_celery_worker(self):
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)
                    else:
                        continue
                    if 'celery' in cmdline_str.lower() and 'worker' in cmdline_str.lower():
                        proc.kill()
                        logger.info(f'已终止Celery Worker: PID {proc.info["pid"]}')
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.error(f'终止Celery Worker失败: {e}')

    def _kill_celery_beat(self):
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline) if isinstance(cmdline, list) else str(cmdline)
                    else:
                        continue
                    if 'celery' in cmdline_str.lower() and 'beat' in cmdline_str.lower():
                        proc.kill()
                        logger.info(f'已终止Celery Beat: PID {proc.info["pid"]}')
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.error(f'终止Celery Beat失败: {e}')
