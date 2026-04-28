"""
服务自动重启与告警模块
"""
import logging
import os
import platform
import shutil
import subprocess
from datetime import timedelta
from typing import Dict, Any, List, Optional

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class PostgresGuardian:
    """
    PostgreSQL 数据库守护器
    检测并自动重启停止的 PostgreSQL 服务
    """
    _last_check = None
    _last_status = None

    @staticmethod
    def check_postgres_status() -> Dict[str, Any]:
        """
        检查 PostgreSQL 服务状态
        返回: {'is_running': bool, 'message': str, 'can_restart': bool}
        """
        import subprocess
        import platform

        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ['sc', 'query', 'postgresql-x64-18'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    PostgresGuardian._last_status = False
                    return {
                        'is_running': False,
                        'message': 'PostgreSQL 服务不存在',
                        'can_restart': True,
                        'service_name': None
                    }

                output = result.stdout.upper()
                if 'STOPPED' in output:
                    PostgresGuardian._last_status = False
                    return {
                        'is_running': False,
                        'message': 'PostgreSQL 服务已停止',
                        'can_restart': True,
                        'service_name': 'postgresql-x64-18'
                    }
                elif 'RUNNING' in output or 'STARTED' in output:
                    PostgresGuardian._last_status = True
                    return {
                        'is_running': True,
                        'message': 'PostgreSQL 服务运行正常',
                        'can_restart': False,
                        'service_name': 'postgresql-x64-18'
                    }
                else:
                    PostgresGuardian._last_status = None
                    return {
                        'is_running': None,
                        'message': f'未知状态: {result.stdout[:100]}',
                        'can_restart': True,
                        'service_name': 'postgresql-x64-18'
                    }

            except subprocess.TimeoutExpired:
                return {'is_running': False, 'message': '检查超时', 'can_restart': False, 'service_name': None}
            except Exception as e:
                return {'is_running': False, 'message': str(e), 'can_restart': False, 'service_name': None}

        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            PostgresGuardian._last_status = True
            return {
                'is_running': True,
                'message': 'PostgreSQL 数据库连接正常',
                'can_restart': True,
                'service_name': 'docker:bid-postgres'
            }
        except Exception as e:
            PostgresGuardian._last_status = False
            return {
                'is_running': False,
                'message': f'PostgreSQL 连接失败: {str(e)}',
                'can_restart': True,
                'service_name': 'docker:bid-postgres'
            }

    @staticmethod
    def ensure_postgres_running() -> tuple[bool, str]:
        """
        确保 PostgreSQL 运行，如果停止则尝试启动
        返回: (success, message)
        """
        status = PostgresGuardian.check_postgres_status()

        if status['is_running'] is True:
            return True, 'PostgreSQL 已在运行'

        if not status['can_restart']:
            return False, f'无法重启: {status["message"]}'

        service_name = status['service_name'] or 'postgresql-x64-18'
        logger.info(f'尝试启动 PostgreSQL 服务: {service_name}')

        try:
            result = subprocess.run(
                ['sc', 'start', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            logger.info(f'sc start result: returncode={result.returncode}, stdout={result.stdout}, stderr={result.stderr}')

            if result.returncode in [0, 1056, 1057]:
                import time
                time.sleep(3)

                verify = PostgresGuardian.check_postgres_status()
                if verify['is_running']:
                    return True, 'PostgreSQL 启动成功'

            if result.returncode == 5:
                return False, '需要管理员权限启动 PostgreSQL'

            return False, f'启动失败: {result.stderr or result.stdout}'

        except subprocess.TimeoutExpired:
            return False, '启动超时'
        except Exception as e:
            return False, f'启动异常: {str(e)}'

    @staticmethod
    def get_postgres_process_info() -> Optional[Dict[str, Any]]:
        """
        获取 PostgreSQL 进程详细信息
        """
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    name = proc.info['name'] or ''
                    if 'postgres' in name.lower():
                        return {
                            'pid': proc.info['pid'],
                            'name': name,
                            'cpu_percent': proc.cpu_percent(),
                            'memory_mb': proc.memory_info().rss / 1024 / 1024,
                            'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return None
        except Exception:
            return None


class ServiceRestartManager:
    """
    服务自动重启管理器
    实现冷却策略和多级降级重启

    重启优先级:
    1. 嵌入式服务 (Chroma) — 不可独立重启
    2. Docker 容器 — 主要重启方式 (docker-compose.yml)
    3. 本地进程回退 — 开发环境备用
    """

    DOCKER_CONTAINER_MAP = {
        'postgresql': {'container': 'bid-postgres', 'display_name': 'PostgreSQL Database'},
        'redis': {'container': 'bid-redis', 'display_name': 'Redis Cache'},
        'celery_worker': {'container': 'bid-celery-worker', 'display_name': 'Celery Worker'},
        'celery_beat': {'container': 'bid-celery-beat', 'display_name': 'Celery Beat'},
        'django': {'container': 'bid-backend', 'display_name': 'Django Server'},
        'fastapi': {'container': 'bid-fastapi', 'display_name': 'FastAPI Server'},
        'milvus': {'container': 'bid-milvus', 'display_name': 'Milvus VectorDB'},
        'minio': {'container': 'bid-minio', 'display_name': 'MinIO Storage'},
        'frontend': {'container': 'bid-frontend', 'display_name': 'Frontend'},
        'gateway': {'container': 'bid-gateway', 'display_name': 'API Gateway'},
        'etcd': {'container': 'bid-milvus-etcd', 'display_name': 'Milvus Etcd'},
    }

    EMBEDDED_SERVICES = {
        'chroma': {
            'display_name': 'Chroma VectorDB',
            'message': 'Chroma 以嵌入式模式运行，随 Django 服务自动重启，无需独立重启',
        },
    }

    LOCAL_PROCESS_FALLBACK = {
        'ollama': {
            'process_patterns': ['ollama'],
            'start_command': ['C:\\Users\\ZhangGan\\AppData\\Local\\Programs\\Ollama\\ollama.exe', 'serve'],
            'display_name': 'Ollama AI',
            'env': None,
            'cwd': None,
        },
        'celery_worker': {
            'process_patterns': ['celery.*worker', 'celery_worker'],
            'start_command': ['d:\\共享文件\\AUTO\\venv\\Scripts\\celery.exe', '-A', 'config', 'worker', '--loglevel=info', '--pool=solo', '-Q', 'celery,crawler,default', '--hostname=worker1@%h'],
            'display_name': 'Celery Worker',
            'env': {
                'DJANGO_SETTINGS_MODULE': 'config.settings.development',
                'PYTHONPATH': 'C:/Users/ZhangGan/AppData/Local/Programs/Python/Python312/Lib/site-packages;d:/共享文件/AUTO/backend'
            },
            'cwd': 'd:/共享文件/AUTO/backend',
        },
        'celery_beat': {
            'process_patterns': ['celery.*beat', 'celery_beat'],
            'start_command': ['d:\\共享文件\\AUTO\\venv\\Scripts\\celery.exe', '-A', 'config', 'beat', '--loglevel=info'],
            'display_name': 'Celery Beat',
            'env': {
                'DJANGO_SETTINGS_MODULE': 'config.settings.development',
                'PYTHONPATH': 'C:/Users/ZhangGan/AppData/Local/Programs/Python/Python312/Lib/site-packages;d:/共享文件/AUTO/backend'
            },
            'cwd': 'd:/共享文件/AUTO/backend',
        },
        'minio': {
            'process_patterns': ['minio'],
            'start_command': ['minio', 'server', 'D:\\共享文件\\AUTO\\minio_data', '--console-address', ':9001'],
            'display_name': 'MinIO Storage',
            'env': {
                'MINIO_ROOT_USER': 'minioadmin',
                'MINIO_ROOT_PASSWORD': 'minioadmin',
            },
            'cwd': None,
        },
        'postgresql': {
            'process_patterns': ['postgres'],
            'display_name': 'PostgreSQL Database',
            'is_windows_service': True,
            'service_pattern': 'postgresql',
        },
        'redis': {
            'process_patterns': ['redis'],
            'display_name': 'Redis Cache',
            'is_windows_service': True,
            'service_pattern': 'Redis',
        },
        'django': {
            'process_patterns': ['runserver'],
            'start_command': ['d:\\共享文件\\AUTO\\venv\\Scripts\\python.exe', 'manage.py', 'runserver', '0.0.0.0:8100'],
            'display_name': 'Django Server',
            'env': {
                'DJANGO_SETTINGS_MODULE': 'config.settings.development',
                'PYTHONPATH': 'd:/共享文件/AUTO/backend',
            },
            'cwd': 'd:/共享文件/AUTO/backend',
        },
    }

    RESTART_COMMANDS = DOCKER_CONTAINER_MAP

    @staticmethod
    def can_restart(service, restart_type: str = 'auto') -> tuple[bool, str]:
        """
        检查服务是否可以重启
        restart_type: 'auto' 自动重启, 'manual' 手动重启
        返回 (是否可以重启, 原因)
        """
        if restart_type == 'manual':
            if service.last_restart_time:
                cooldown_seconds = 30
                elapsed = (timezone.now() - service.last_restart_time).total_seconds()
                if elapsed < cooldown_seconds:
                    remaining = int(cooldown_seconds - elapsed)
                    return False, f"操作过快，请等待 {remaining} 秒"
            return True, "可以重启"

        if not service.auto_restart_enabled:
            return False, "自动重启已禁用"

        if service.restart_attempts_today >= service.max_restart_attempts:
            return False, f"今日重启次数已达上限({service.max_restart_attempts})"

        if service.last_restart_time:
            cooldown_seconds = service.restart_cooldown_minutes * 60
            elapsed = (timezone.now() - service.last_restart_time).total_seconds()
            if elapsed < cooldown_seconds:
                remaining = int(cooldown_seconds - elapsed)
                return False, f"冷却中，还需等待 {remaining} 秒"

        return True, "可以重启"

    @staticmethod
    def execute_restart(service, action_type: str = 'auto_restart', trigger_condition: str = None) -> Dict[str, Any]:
        """
        执行服务重启
        """
        from apps.monitor.models import ServiceActionLog, ServiceAlert, AlertLevel, AlertStatus

        restart_type = 'manual' if action_type == 'manual_restart' else 'auto'
        can_restart, reason = ServiceRestartManager.can_restart(service, restart_type=restart_type)
        if not can_restart:
            return {'success': False, 'message': reason}

        if trigger_condition is None:
            trigger_condition = f'连续失败{service.consecutive_failures}次'

        action_log = ServiceActionLog.objects.create(
            service=service,
            action_type=action_type,
            status='started',
            trigger_condition=trigger_condition
        )

        try:
            restart_success, error_msg = ServiceRestartManager._do_restart(service)

            if restart_success:
                service.consecutive_failures = 0
                service.last_restart_time = timezone.now()
                service.restart_attempts_today += 1
                service.save(update_fields=[
                    'consecutive_failures', 'last_restart_time',
                    'restart_attempts_today', 'updated_at'
                ])

                action_log.status = 'success'
                action_log.result_message = f"重启成功"
                action_log.completed_at = timezone.now()
                action_log.save()

                ServiceRestartManager._resolve_existing_alerts(service)

                return {'success': True, 'message': '重启成功'}
            else:
                action_log.status = 'failed'
                action_log.result_message = error_msg or '重启执行返回失败'
                action_log.completed_at = timezone.now()
                action_log.save()

                return {'success': False, 'message': error_msg or '不支持此服务的重启'}

        except Exception as e:
            logger.error(f"重启服务失败 {service.name}: {str(e)}")
            action_log.status = 'failed'
            action_log.error_details = str(e)
            action_log.completed_at = timezone.now()
            action_log.save()

            return {'success': False, 'message': str(e)}

    @staticmethod
    def _do_restart(service) -> tuple[bool, str]:
        """
        执行实际的重启操作
        统一优先级: 嵌入式检查 → Docker容器 → 本地进程回退
        返回 (success, error_message)
        """
        service_name = service.name.lower()

        for key, embedded_info in ServiceRestartManager.EMBEDDED_SERVICES.items():
            if key in service_name:
                logger.info(f"嵌入式服务 {embedded_info['display_name']} 无需独立重启")
                return False, embedded_info['message']

        docker_result = ServiceRestartManager._try_docker_restart_by_name(service_name)
        if docker_result is not None:
            if docker_result[0]:
                return docker_result
            if docker_result[1].startswith('Docker重启失败') or '未部署' in docker_result[1]:
                return docker_result

        local_result = ServiceRestartManager._try_local_process_restart(service_name)
        if local_result is not None:
            if local_result[0]:
                return local_result
            if docker_result is not None and docker_result[1]:
                return False, f"{docker_result[1]}；本地回退也失败: {local_result[1]}"
            return local_result

        docker_info = ServiceRestartManager.DOCKER_CONTAINER_MAP.get(service_name.replace('_', ' ').split()[0])
        if docker_info:
            return False, f"{docker_info['display_name']} 当前环境未部署（Docker容器和本地进程均不可用），请先部署该服务"

        logger.warning(f"未找到服务 {service.name} 的重启方式")
        return False, f"不支持的服务: {service.name}"

    @staticmethod
    def _try_docker_restart_by_name(service_name: str) -> Optional[tuple[bool, str]]:
        """
        通过Docker容器重启服务
        优先使用 Docker Engine API (unix socket + curl)，回退到 Docker CLI
        返回 None 表示该服务没有Docker容器配置
        """
        container_name = None
        display_name = None

        for key, info in ServiceRestartManager.DOCKER_CONTAINER_MAP.items():
            if key in service_name:
                container_name = info['container']
                display_name = info['display_name']
                break

        if not container_name:
            return None

        if not ServiceRestartManager._is_docker_available():
            logger.info(f"Docker不可用，尝试本地进程回退: {display_name}")
            return None

        if os.path.exists(ServiceRestartManager.DOCKER_SOCKET_PATH):
            logger.info(f"通过Docker Engine API重启: {display_name} ({container_name})")
            inspect_ok, inspect_err = ServiceRestartManager._docker_api_request(
                'GET', f'/containers/{container_name}/json', timeout=10
            )
            if not inspect_ok:
                if '404' in inspect_err or '不存在' in inspect_err:
                    return False, f"{display_name} 当前环境未部署（容器 {container_name} 不存在）"
                return False, f"{display_name} 检查失败: {inspect_err}"

            restart_ok, restart_err = ServiceRestartManager._docker_api_request(
                'POST', f'/containers/{container_name}/restart', timeout=60
            )
            if restart_ok:
                return True, ""
            return False, f"Docker重启失败: {restart_err}"

        logger.info(f"尝试Docker CLI容器重启: {display_name} ({container_name})")

        try:
            inspect_result = subprocess.run(
                ['docker', 'inspect', container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if inspect_result.returncode != 0:
                return False, f"{display_name} 当前环境未部署（容器 {container_name} 不存在）"

            result = subprocess.run(
                ['docker', 'restart', container_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            logger.info(f"docker restart result: returncode={result.returncode}, stdout={result.stdout}, stderr={result.stderr}")
            if result.returncode == 0:
                return True, ""
            return False, f"Docker重启失败: {result.stderr or result.stdout}"
        except subprocess.TimeoutExpired:
            logger.error(f"Docker容器重启超时: {container_name}")
            return False, f"Docker重启超时: {container_name}"
        except Exception as e:
            logger.error(f"Docker容器重启失败: {str(e)}")
            return False, f"Docker重启失败: {str(e)}"

    DOCKER_SOCKET_PATH = '/var/run/docker.sock'

    @staticmethod
    def _is_docker_available() -> bool:
        if os.path.exists(ServiceRestartManager.DOCKER_SOCKET_PATH):
            return True
        try:
            result = subprocess.run(
                ['docker', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return 'Version' in result.stdout or 'version' in result.stdout.lower()
        except (FileNotFoundError, Exception):
            return False

    @staticmethod
    def _docker_api_request(method: str, path: str, timeout: int = 60) -> tuple[bool, str]:
        """
        通过 Docker Engine API (unix socket + curl) 发送请求
        返回 (success, error_message)
        """
        socket_path = ServiceRestartManager.DOCKER_SOCKET_PATH
        if not os.path.exists(socket_path):
            return False, f"Docker socket 不存在: {socket_path}"

        try:
            cmd = [
                'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                '--unix-socket', socket_path,
                '-X', method,
                f'http://localhost{path}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            http_code = result.stdout.strip()

            if http_code in ('200', '204', '304'):
                return True, ""
            if http_code == '404':
                return False, f"容器不存在 (HTTP {http_code})"
            if http_code == '500':
                return False, f"Docker Engine 内部错误 (HTTP {http_code})"
            return False, f"Docker API 请求失败 (HTTP {http_code})"
        except subprocess.TimeoutExpired:
            return False, "Docker API 请求超时"
        except FileNotFoundError:
            return False, "curl 命令不可用"
        except Exception as e:
            return False, f"Docker API 请求异常: {str(e)}"

    @staticmethod
    def _try_local_process_restart(service_name: str) -> Optional[tuple[bool, str]]:
        """
        本地进程重启回退
        返回 None 表示该服务没有本地进程配置
        """
        for key, process_info in ServiceRestartManager.LOCAL_PROCESS_FALLBACK.items():
            if key in service_name:
                display_name = process_info['display_name']

                if process_info.get('is_windows_service') and platform.system() == 'Windows':
                    return ServiceRestartManager._restart_windows_service(
                        process_info['service_pattern'], display_name
                    )

                start_command = process_info.get('start_command')
                if not start_command:
                    return False, f"{display_name} 无本地启动命令配置"

                exe_path = start_command[0]
                exe_exists = os.path.isfile(exe_path) or ServiceRestartManager._find_executable(exe_path) is not None
                is_running = ServiceRestartManager._is_process_running(process_info['process_patterns'])

                if not exe_exists and not is_running:
                    return False, f"{display_name} 未运行且本地未找到可执行文件 ({exe_path})"

                if not exe_exists and is_running:
                    return False, f"{display_name} 进程运行中但无法重启（未找到可执行文件: {exe_path}）"

                try:
                    logger.info(f"本地进程重启: {display_name}")

                    killed = ServiceRestartManager._kill_process_by_pattern(process_info['process_patterns'])
                    logger.info(f"进程终止结果: {killed}")

                    import time
                    time.sleep(2)

                    started, start_msg = ServiceRestartManager._start_process(
                        start_command,
                        env=ServiceRestartManager._build_celery_env(process_info.get('env'), key),
                        cwd=process_info.get('cwd')
                    )
                    logger.info(f"进程启动结果: {started}, {start_msg}")

                    return started, start_msg
                except Exception as e:
                    logger.error(f"本地进程重启失败: {str(e)}")
                    return False, f"重启失败: {str(e)}"

        return None

    @staticmethod
    def _build_celery_env(base_env: Optional[Dict], service_key: str) -> Optional[Dict]:
        if not base_env or 'celery' not in service_key:
            return base_env
        env = dict(base_env)
        try:
            from django.conf import settings
            env['CELERY_BROKER_URL'] = settings.CELERY_BROKER_URL
            env['CELERY_RESULT_BACKEND'] = getattr(settings, 'CELERY_RESULT_BACKEND', settings.CELERY_BROKER_URL)
        except Exception:
            env.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            env.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        return env

    @staticmethod
    def _restart_windows_service(service_pattern: str, display_name: str) -> tuple[bool, str]:
        windows_service_name = ServiceRestartManager._find_windows_service_name(service_pattern)
        if not windows_service_name:
            logger.warning(f"未找到包含 '{service_pattern}' 的Windows服务")
            return False, f"未找到Windows服务: {display_name}"

        try:
            logger.info(f"Windows服务重启: {display_name} ({windows_service_name})")

            stop_result = subprocess.run(
                ['sc', 'stop', windows_service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            logger.info(f"sc stop result: returncode={stop_result.returncode}, stdout={stop_result.stdout}, stderr={stop_result.stderr}")

            import time
            time.sleep(2)

            start_result = subprocess.run(
                ['sc', 'start', windows_service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            logger.info(f"sc start result: returncode={start_result.returncode}, stdout={start_result.stdout}, stderr={start_result.stderr}")

            if start_result.returncode in [0, 1056]:
                return True, ""
            elif start_result.returncode == 5:
                logger.error("拒绝访问，需要管理员权限")
                return False, "需要管理员权限"
            else:
                if start_result.stdout and ('state' in start_result.stdout.lower() or 'running' in start_result.stdout.lower()):
                    return True, ""
                return False, f"重启失败: {start_result.stderr or start_result.stdout}"
        except subprocess.TimeoutExpired:
            logger.error(f"Windows服务重启命令超时: {display_name}")
            return False, f"重启超时: {display_name}"
        except Exception as e:
            logger.error(f"Windows服务重启失败: {str(e)}")
            return False, f"重启失败: {str(e)}"

    @staticmethod
    def _find_executable(name: str) -> Optional[str]:
        """
        在系统PATH中查找可执行文件
        """
        return shutil.which(name)

    @staticmethod
    def _is_process_running(patterns: list) -> bool:
        """
        检查是否有匹配模式的进程正在运行
        """
        try:
            import psutil
            import re
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'] or ''
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    for pattern in patterns:
                        if re.search(pattern, proc_name, re.IGNORECASE) or re.search(pattern, cmdline, re.IGNORECASE):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass
        return False

    @staticmethod
    def _find_windows_service_name(pattern: str) -> Optional[str]:
        """
        通过服务显示名称查找实际的服务名
        使用 sc query 命令枚举服务
        """
        try:
            result = subprocess.run(
                ['sc', 'query', 'state=', 'all'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                return None

            lines = result.stdout.split('\n')
            current_service_name = None
            current_display_name = None

            for line in lines:
                line = line.strip()
                if line.startswith('SERVICE_NAME:'):
                    current_service_name = line.split(':', 1)[1].strip()
                elif line.startswith('DISPLAY_NAME:'):
                    current_display_name = line.split(':', 1)[1].strip()
                    if pattern.lower() in current_display_name.lower():
                        logger.info(f"找到匹配服务: {current_display_name} -> {current_service_name}")
                        return current_service_name

            return None
        except Exception as e:
            logger.error(f"查找Windows服务名失败: {str(e)}")
            return None

    @staticmethod
    def _kill_process_by_pattern(patterns: list) -> bool:
        """
        通过进程名模式终止进程
        使用 taskkill /F /IM 或 wmic 命令
        """
        try:
            import psutil
            killed_any = False

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'] or ''
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                    for pattern in patterns:
                        import re
                        if re.search(pattern, proc_name, re.IGNORECASE) or re.search(pattern, cmdline, re.IGNORECASE):
                            logger.info(f"终止进程: {proc_name} (PID: {proc.info['pid']})")
                            proc.kill()
                            killed_any = True
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            return killed_any
        except Exception as e:
            logger.error(f"终止进程失败: {str(e)}")
            return False

    @staticmethod
    def _start_process(command: list, env: dict = None, cwd: str = None) -> tuple[bool, str]:
        """
        启动一个新进程
        返回 (success, error_message)
        """
        try:
            import subprocess
            import os

            logger.info(f"启动进程: {' '.join(command)}")

            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            startup_dir = cwd if cwd else os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

            popen_kwargs = {
                'cwd': startup_dir,
                'env': process_env,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True
            }

            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                popen_kwargs['startupinfo'] = startupinfo

            process = subprocess.Popen(command, **popen_kwargs)

            logger.info(f"进程已启动，PID: {process.pid}")
            return True, ""
        except Exception as e:
            logger.error(f"启动进程失败: {str(e)}")
            return False, f"启动进程失败: {str(e)}"

    @staticmethod
    def _resolve_existing_alerts(service):
        """解决服务已有的告警"""
        from apps.monitor.models import ServiceAlert, AlertStatus

        ServiceAlert.objects.filter(
            service=service,
            status__in=[AlertStatus.PENDING, AlertStatus.NOTIFIED]
        ).update(
            status=AlertStatus.RESOLVED,
            resolved_at=timezone.now()
        )


class AlertManager:
    """
    告警管理器
    负责告警的创建、通知和升级
    """

    @staticmethod
    def check_and_create_alert(service) -> Optional[Any]:
        """
        检查是否需要创建告警
        """
        from apps.monitor.models import ServiceAlert, AlertLevel, AlertStatus

        if service.consecutive_failures < service.consecutive_failures_to_alert:
            return None

        existing_alert = ServiceAlert.objects.filter(
            service=service,
            status__in=[AlertStatus.PENDING, AlertStatus.NOTIFIED]
        ).first()

        if existing_alert:
            return existing_alert

        level = AlertLevel.CRITICAL if service.is_critical else AlertLevel.ERROR

        alert = ServiceAlert.objects.create(
            service=service,
            level=level,
            status=AlertStatus.PENDING,
            title=f"服务异常: {service.display_name}",
            message=f"服务 {service.display_name} 连续{service.consecutive_failures}次检查失败",
            triggered_by='consecutive_failures',
            consecutive_failures=service.consecutive_failures
        )

        return alert

    @staticmethod
    def send_alert_notification(alert) -> bool:
        """
        发送告警通知
        """
        from apps.monitor.models import ServiceActionLog

        action_log = ServiceActionLog.objects.create(
            service=alert.service,
            action_type='alert_sent',
            status='started',
            trigger_condition=f'告警 #{alert.id}'
        )

        try:
            notification_sent = AlertManager._do_send_notification(alert)

            if notification_sent:
                alert.status = 'NOTIFIED'
                alert.notified_at = timezone.now()
                alert.save(update_fields=['status', 'notified_at', 'updated_at'])

                action_log.status = 'success'
                action_log.result_message = "告警通知已发送"
            else:
                action_log.status = 'failed'
                action_log.result_message = "告警通知发送失败"

            action_log.completed_at = timezone.now()
            action_log.save()

            return notification_sent

        except Exception as e:
            logger.error(f"发送告警通知失败: {str(e)}")
            action_log.status = 'failed'
            action_log.error_details = str(e)
            action_log.completed_at = timezone.now()
            action_log.save()
            return False

    @staticmethod
    def _do_send_notification(alert) -> bool:
        """
        执行实际的通知发送
        支持钉钉、邮件等多种渠道
        """
        try:
            webhook_url = getattr(settings, 'DINGTALK_WEBHOOK_URL', None)

            if webhook_url:
                return AlertManager._send_dingtalk(webhook_url, alert)

            logger.warning("未配置告警通知渠道")
            return True

        except Exception as e:
            logger.error(f"通知发送异常: {str(e)}")
            return False

    @staticmethod
    def _send_dingtalk(webhook_url: str, alert) -> bool:
        """
        发送钉钉通知
        """
        try:
            import json
            import urllib.request
            import urllib.error

            message = {
                'msgtype': 'markdown',
                'markdown': {
                    'title': f"【{alert.get_level_display()}】{alert.title}",
                    'text': f"### 【{alert.get_level_display()}】{alert.title}\n\n"
                           f"**服务**: {alert.service.display_name}\n\n"
                           f"**级别**: {alert.get_level_display()}\n\n"
                           f"**消息**: {alert.message}\n\n"
                           f"**连续失败**: {alert.consecutive_failures}次\n\n"
                           f"**时间**: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                           f"**状态**: {alert.get_status_display()}\n\n"
                           f"> 请及时处理！"
                }
            }

            data = json.dumps(message).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('errcode', 1) == 0

        except Exception as e:
            logger.error(f"钉钉通知发送失败: {str(e)}")
            return False

    @staticmethod
    def get_pending_alerts() -> List[Any]:
        """
        获取所有待处理的告警
        """
        from apps.monitor.models import ServiceAlert, AlertStatus
        return list(ServiceAlert.objects.filter(
            status__in=[AlertStatus.PENDING, AlertStatus.NOTIFIED]
        ).select_related('service').order_by('-created_at'))

    @staticmethod
    def resolve_alert(alert_id: int, resolved_by: str = 'system') -> bool:
        """
        解决告警
        """
        from apps.monitor.models import ServiceAlert, AlertStatus

        try:
            alert = ServiceAlert.objects.get(id=alert_id)
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = timezone.now()
            alert.save(update_fields=['status', 'resolved_at', 'updated_at'])
            return True
        except ServiceAlert.DoesNotExist:
            return False