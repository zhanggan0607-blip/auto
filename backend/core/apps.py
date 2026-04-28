from django.apps import AppConfig
import os


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    path = os.path.dirname(os.path.abspath(__file__))
    verbose_name = '核心功能'

    def ready(self):
        pass
