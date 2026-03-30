import os
import sys
import django

sys.path.insert(0, r'D:\共享文件\AUTO\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.openclaw.models import LLMProvider
from services.llm_adapters import get_adapter
import traceback

provider = LLMProvider.objects.filter(provider_type='ollama').first()
if provider:
    print(f"Provider: {provider.name}")
    adapter = get_adapter(provider)
    messages = [{'role': 'user', 'content': '你好'}]
    print("\nTesting streaming...")

    try:
        for i, chunk in enumerate(adapter.chat_stream('qwen3:8b', messages, 0.7, 50)):
            if isinstance(chunk, tuple):
                continue
            print(f"Chunk {i}: '{chunk}'")
            if i >= 5:
                break
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
else:
    print("No Ollama provider found")
