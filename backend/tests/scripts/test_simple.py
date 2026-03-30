"""
简单测试脚本
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from openclaw.skills.collector.enterprise_collector import EnterpriseInfoCollectorSkill

async def test():
    skill = EnterpriseInfoCollectorSkill()
    result = await skill.execute(
        company_name='上海天齐智能建筑股份有限公司',
        mode='http',
        source='auto'
    )
    if result.success:
        print('成功!')
        for k, v in result.data.items():
            if v:
                print(f'  {k}: {v}')
    else:
        print(f'失败: {result.error}')
        sources = result.metadata.get('sources_tried', [])
        print(f'尝试的数据源: {sources}')

if __name__ == '__main__':
    asyncio.run(test())
