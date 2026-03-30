import os
import re
from pathlib import Path
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from utils.responses import UnifiedResponse


class ProjectKnowledgeView(APIView):
    """
    项目知识库 API
    提供项目结构、模块、路由等信息，用于AI了解项目
    """
    permission_classes = [AllowAny]

    def get(self, request):
        knowledge = {
            'project_overview': self.get_project_overview(),
            'modules': self.get_modules(),
            'database_models': self.get_database_models(),
            'api_routes': self.get_api_routes(),
            'error_summary': self.get_error_summary(),
        }
        return UnifiedResponse.success(data=knowledge)

    def get_project_overview(self):
        """获取项目概述"""
        return {
            'name': '天齐AI大模型投标平台',
            'version': '2.0',
            'description': '基于AI的投标自动化系统，支持招标采集、企业匹配、投标管理',
            'tech_stack': {
                'frontend': 'Vue 3 + TypeScript + Element Plus',
                'backend': 'Django + DRF + Celery',
                'database': 'PostgreSQL + Redis',
                'ai': 'Ollama/vLLM + Qwen2.5系列',
                'deployment': 'Docker/K8s'
            },
            'main_features': [
                '招标信息智能采集（中国政府采购网等）',
                '企业资质与招标公告语义匹配',
                '投标流程自动化管理',
                'AI辅助标书生成',
                '钉钉通知集成'
            ]
        }

    def get_modules(self):
        """获取项目模块结构"""
        apps_dir = Path(settings.BASE_DIR) / 'apps'
        modules = []

        app_dirs = [d for d in apps_dir.iterdir() if d.is_dir() and not d.name.startswith('_') and not d.name.startswith('core')]
        for app_dir in sorted(app_dirs):
            app_py = app_dir / '__init__.py'
            if app_py.exists():
                app_name = app_dir.name
                verbose_name = self._get_app_verbose_name(app_dir)

                views_file = app_dir / 'views.py'
                models_file = app_dir / 'models.py'
                urls_file = app_dir / 'urls.py'

                module_info = {
                    'name': app_name,
                    'verbose_name': verbose_name,
                    'has_views': views_file.exists(),
                    'has_models': models_file.exists(),
                    'has_urls': urls_file.exists(),
                    'files': []
                }

                for py_file in app_dir.glob('*.py'):
                    if not py_file.name.startswith('_'):
                        module_info['files'].append(py_file.name)

                modules.append(module_info)

        return modules

    def _get_app_verbose_name(self, app_dir):
        """获取app的中文名称"""
        apps_file = app_dir / 'apps.py'
        if apps_file.exists():
            content = apps_file.read_text(encoding='utf-8')
            match = re.search(r"verbose_name\s*=\s*['\"](.+?)['\"]", content)
            if match:
                return match.group(1)
        return app_dir.name

    def get_database_models(self):
        """获取数据库模型信息"""
        apps_dir = Path(settings.BASE_DIR) / 'apps'
        models_info = []

        for app_dir in apps_dir.iterdir():
            if not app_dir.is_dir() or app_dir.name.startswith('_'):
                continue

            models_file = app_dir / 'models.py'
            if models_file.exists():
                content = models_file.read_text(encoding='utf-8')
                classes = re.findall(r'class (\w+)\(.*?Model.*?\)', content, re.DOTALL)
                if classes:
                    models_info.append({
                        'app': app_dir.name,
                        'models': classes
                    })

        return models_info

    def get_api_routes(self):
        """获取API路由信息"""
        apps_dir = Path(settings.BASE_DIR) / 'apps'
        routes = []

        for app_dir in apps_dir.iterdir():
            if not app_dir.is_dir() or app_dir.name.startswith('_'):
                continue

            urls_file = app_dir / 'urls.py'
            if urls_file.exists():
                content = urls_file.read_text(encoding='utf-8')

                path_patterns = re.findall(r"path\(['\"]([^'\"]+)['\"],\s*([^,]+)", content)
                for path, view in path_patterns:
                    if 'api' in path.lower() or 'v1' in path:
                        routes.append({
                            'app': app_dir.name,
                            'path': f'/api/v1/{app_dir.name}/{path}',
                            'view': view.strip()
                        })

                url_patterns = re.findall(r"re_path\(['\"]([^'\"]+)['\"],\s*([^,]+)", content)
                for path, view in url_patterns:
                    routes.append({
                        'app': app_dir.name,
                        'path': f'/api/v1/{app_dir.name}/{path}',
                        'view': view.strip()
                    })

        return routes

    def get_error_summary(self):
        """获取错误日志摘要"""
        error_log_path = Path(settings.BASE_DIR).parent / 'ERROR_LOG.md'

        if not error_log_path.exists():
            return {'total_errors': 0, 'summary': '错误日志文件不存在'}

        try:
            content = error_log_path.read_text(encoding='utf-8')

            error_entries = re.findall(r'\|\s*E(\d+)\s*\|\s*(.+?)\s*\|', content)
            feature_entries = re.findall(r'\|\s*F(\d+)\s*\|\s*(.+?)\s*\|', content)

            recent_errors = []
            for num, desc in error_entries[-20:]:
                recent_errors.append({
                    'code': f'E{num}',
                    'description': desc.strip()
                })

            return {
                'total_errors': len(error_entries),
                'total_features': len(feature_entries),
                'recent_errors': recent_errors,
                'file_exists': True
            }
        except Exception as e:
            return {'total_errors': 0, 'summary': f'读取错误日志失败: {str(e)}', 'file_exists': False}


class ProjectContextView(APIView):
    """
    项目上下文 API
    生成供AI使用的项目上下文信息
    """
    permission_classes = [AllowAny]

    def get(self, request):
        context = self.generate_context()
        return UnifiedResponse.success(data={'context': context})

    def generate_context(self):
        """生成项目上下文"""
        overview = ProjectKnowledgeView().get_project_overview()
        modules = ProjectKnowledgeView().get_modules()

        module_descriptions = []
        for m in modules:
            desc = f"- {m['verbose_name']} ({m['name']})"
            if m.get('has_models'):
                desc += f": 包含数据模型"
            if m.get('has_views'):
                desc += f", 提供API接口"
            module_descriptions.append(desc)

        context = f"""# 项目概述
{overview['name']} v{overview['version']}
{overview['description']}

## 技术栈
- 前端: {overview['tech_stack']['frontend']}
- 后端: {overview['tech_stack']['backend']}
- 数据库: {overview['tech_stack']['database']}
- AI: {overview['tech_stack']['ai']}

## 主要功能
{chr(10).join(['- ' + f for f in overview['main_features']])}

## 项目模块
{chr(10).join(module_descriptions)}

## 数据库模型（按模块）
"""
        models_info = ProjectKnowledgeView().get_database_models()
        for app_models in models_info:
            context += f"\n### {app_models['app']}\n"
            for model in app_models['models']:
                context += f"- {model}\n"

        return context