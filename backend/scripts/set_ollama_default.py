import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.openclaw.models import LLMProvider

current_default = LLMProvider.objects.filter(is_default=True).first()
if current_default:
    print(f'当前默认提供商: {current_default.name} ({current_default.provider_type})')
else:
    print('没有设置默认提供商')

ollama = LLMProvider.objects.filter(provider_type='ollama').first()
if ollama:
    print(f'Ollama提供商: {ollama.name}, is_default={ollama.is_default}, is_active={ollama.is_active}')
    if not ollama.is_default:
        print('正在将Ollama设为默认...')
        LLMProvider.objects.filter(is_default=True).update(is_default=False)
        ollama.is_default = True
        ollama.save()
        print('已将Ollama设为默认提供商')
    else:
        print('Ollama已经是默认提供商')
else:
    print('没有找到Ollama提供商')
