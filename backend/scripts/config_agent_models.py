import os
import sys
import django
import requests
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.openclaw.models import LLMProvider, LLMModel, AgentModelConfig

# 获取Ollama模型列表
print("=" * 60)
print("1. 检查Ollama模型列表")
print("=" * 60)

try:
    response = requests.get('http://localhost:11434/api/tags', timeout=10)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"Ollama共有 {len(models)} 个模型:")
        for m in models:
            size_gb = m['size'] / 1024 / 1024 / 1024
            print(f"  - {m['name']} ({size_gb:.2f} GB)")
    else:
        print(f"获取模型失败: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"连接Ollama失败: {e}")
    sys.exit(1)

# 方案1配置
agent_model_config = {
    'collector': 'qwen3:8b',      # 信息收集Agent - 中文理解好
    'matcher': 'gemma3:12b',     # 企业比对Agent - 12B大模型，匹配准确
    'analyst': 'deepseek-r1:8b',  # 投标论证Agent - R1推理强
    'generator': 'qwen3:8b',     # 标书制作Agent - 中文生成流畅
    'reviewer': 'gemma3:12b',    # 标书审核Agent - 全面检查
    'tracker': 'qwen3:4b',       # 结果查询Agent - 轻量快速
    'optimizer': 'deepseek-r1:8b', # 质量提升Agent - 推理优化强
    'orchestrator': 'gemma3:12b', # 协调器Agent - 统筹调度
}

print("\n" + "=" * 60)
print("2. 同步Ollama模型到数据库")
print("=" * 60)

ollama_provider = LLMProvider.objects.filter(provider_type='ollama', is_active=True).first()
if not ollama_provider:
    print("未找到Ollama提供商，正在创建...")
    ollama_provider = LLMProvider.objects.create(
        name='Ollama本地模型',
        provider_type='ollama',
        code='ollama',
        base_url='http://localhost:11434',
        default_model='qwen3:8b',
        available_models=[m['name'] for m in models],
        is_active=True,
        is_default=True
    )
    print(f"创建Ollama提供商成功: {ollama_provider.name}")
else:
    print(f"找到Ollama提供商: {ollama_provider.name}")

# 更新available_models
ollama_provider.available_models = [m['name'] for m in models]
ollama_provider.save()

# 创建或更新LLMModel记录
model_map = {}
for m in models:
    model_id = m['name']
    obj, created = LLMModel.objects.update_or_create(
        provider=ollama_provider,
        model_id=model_id,
        defaults={
            'name': model_id,
            'model_type': 'chat',
            'context_window': 128000,
            'is_active': True
        }
    )
    model_map[model_id] = obj
    action = "创建" if created else "更新"
    print(f"  {action}: {model_id}")

print("\n" + "=" * 60)
print("3. 配置8个Agent的模型")
print("=" * 60)

for agent_type, model_name in agent_model_config.items():
    if model_name not in model_map:
        print(f"  [跳过] {agent_type}: {model_name} (模型不存在)")
        continue

    model_obj = model_map[model_name]

    config, created = AgentModelConfig.objects.update_or_create(
        agent_type=agent_type,
        defaults={
            'chat_model': model_obj,
            'temperature': 0.7,
            'max_tokens': 4096,
            'is_active': True
        }
    )
    action = "创建" if created else "更新"
    print(f"  [{action}] {agent_type}: {model_name}")

print("\n" + "=" * 60)
print("4. 验证配置结果")
print("=" * 60)

all_configs = AgentModelConfig.objects.filter(is_active=True)
for config in all_configs:
    model_name = config.chat_model.model_id if config.chat_model else "未设置"
    print(f"  {config.agent_type}: {model_name} (温度={config.temperature}, 最大Token={config.max_tokens})")

print("\n" + "=" * 60)
print("配置完成！")
print("=" * 60)