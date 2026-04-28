"""
独立脚本：清理重复的招标项目
直接使用Django db cursor执行，避免导入问题
"""
import os
import sys
import django

sys.path.insert(0, 'd:/共享文件/AUTO/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'

django.setup()

from django.db import connection
from apps.tenders.models import TenderProject

def cleanup_duplicate_tenders():
    """清理重复的招标项目"""
    print('开始查找重复项目...')

    title_groups = {}
    for tender in TenderProject.objects.all().order_by('created_at'):
        title = tender.title.strip()
        if title not in title_groups:
            title_groups[title] = []
        title_groups[title].append(tender)

    duplicate_titles = {k: v for k, v in title_groups.items() if len(v) > 1}

    if not duplicate_titles:
        print('没有发现重复项目')
        return

    total_duplicates = sum(len(v) - 1 for v in duplicate_titles.values())
    print(f'发现 {len(duplicate_titles)} 个重复标题，共 {total_duplicates} 条重复记录')

    to_delete = []
    for title, tenders in duplicate_titles.items():
        keep = min(tenders, key=lambda t: t.created_at)
        for t in tenders:
            if t.id != keep.id:
                to_delete.append(t)

    print(f'\n将删除 {len(to_delete)} 条记录:')
    for t in to_delete[:20]:
        print(f'  - ID:{t.id}, 标题:{t.title[:50]}, 创建时间:{t.created_at}')

    if len(to_delete) > 20:
        print(f'  ... 还有 {len(to_delete) - 20} 条记录')

    print('\n开始删除重复记录...')

    ids_to_delete = [t.id for t in to_delete]
    deleted_count, _ = TenderProject.objects.filter(id__in=ids_to_delete).delete()

    print(f'已删除 {deleted_count} 条重复记录')
    return to_delete

if __name__ == '__main__':
    cleanup_duplicate_tenders()
