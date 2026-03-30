"""
初始化默认LLM提供商配置
"""
from django.db import migrations


def create_default_providers(apps, schema_editor):
    """
    创建默认的LLM提供商配置
    """
    LLMProvider = apps.get_model('openclaw', 'LLMProvider')
    
    providers_data = [
        {
            'name': '投标精灵',
            'provider_type': 'ollama',
            'code': 'ollama_local',
            'base_url': 'http://localhost:11434',
            'api_key': None,
            'default_model': 'qwen2.5:14b',
            'available_models': ['qwen2.5:14b', 'qwen2.5:72b', 'llama3.1:70b', 'deepseek-r1:14b'],
            'max_tokens': 4096,
            'temperature': 0.7,
            'timeout': 120,
            'is_active': True,
            'is_default': True,
        },
        {
            'name': '智谱AI',
            'provider_type': 'zhipu',
            'code': 'zhipu',
            'base_url': 'https://open.bigmodel.cn',
            'api_key': None,
            'default_model': 'glm-4-flash',
            'available_models': ['glm-4', 'glm-4-flash', 'glm-4-plus', 'glm-4-air'],
            'max_tokens': 4096,
            'temperature': 0.7,
            'timeout': 60,
            'is_active': True,
            'is_default': False,
        },
        {
            'name': '通义千问',
            'provider_type': 'qwen',
            'code': 'qwen',
            'base_url': 'https://dashscope.aliyuncs.com',
            'api_key': None,
            'default_model': 'qwen-turbo',
            'available_models': ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-max-longcontext'],
            'max_tokens': 4096,
            'temperature': 0.7,
            'timeout': 60,
            'is_active': True,
            'is_default': False,
        },
        {
            'name': 'DeepSeek',
            'provider_type': 'deepseek',
            'code': 'deepseek',
            'base_url': 'https://api.deepseek.com',
            'api_key': None,
            'default_model': 'deepseek-chat',
            'available_models': ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
            'max_tokens': 4096,
            'temperature': 0.7,
            'timeout': 60,
            'is_active': True,
            'is_default': False,
        },
        {
            'name': 'OpenAI',
            'provider_type': 'openai',
            'code': 'openai',
            'base_url': 'https://api.openai.com',
            'api_key': None,
            'default_model': 'gpt-4o-mini',
            'available_models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'max_tokens': 4096,
            'temperature': 0.7,
            'timeout': 60,
            'is_active': False,
            'is_default': False,
        },
    ]
    
    for data in providers_data:
        LLMProvider.objects.update_or_create(
            code=data['code'],
            defaults=data
        )
    
    print(f'成功创建 {len(providers_data)} 个LLM提供商配置')


def reverse_func(apps, schema_editor):
    """
    回滚迁移
    """
    LLMProvider = apps.get_model('openclaw', 'LLMProvider')
    LLMProvider.objects.filter(code__in=['ollama_local', 'zhipu', 'qwen', 'deepseek', 'openai']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('openclaw', '0002_llmmodel_remove_agentinstance_parent_agent_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_providers, reverse_func),
    ]
