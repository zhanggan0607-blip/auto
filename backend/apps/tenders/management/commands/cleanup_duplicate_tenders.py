"""
清理重复的招标项目
保留最早创建的记录，删除其他重复记录
"""
from django.core.management.base import BaseCommand
from django.db.models import Min
from apps.tenders.models import TenderProject


class Command(BaseCommand):
    help = '清理重复的招标项目，按项目名称(title)去重，保留最早创建的'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅预览，不实际删除',
        )
        parser.add_argument(
            '--keep-newest',
            action='store_true',
            help='保留最新创建的，而不是最早创建的',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        keep_newest = options.get('keep_newest', False)

        self.stdout.write(self.style.NOTICE('开始查找重复项目...'))

        title_groups = {}
        for tender in TenderProject.objects.all().order_by('created_at'):
            title = tender.title.strip()
            if title not in title_groups:
                title_groups[title] = []
            title_groups[title].append(tender)

        duplicate_titles = {k: v for k, v in title_groups.items() if len(v) > 1}

        if not duplicate_titles:
            self.stdout.write(self.style.SUCCESS('没有发现重复项目'))
            return

        total_duplicates = sum(len(v) - 1 for v in duplicate_titles.values())
        self.stdout.write(self.style.WARNING(f'发现 {len(duplicate_titles)} 个重复标题，共 {total_duplicates} 条重复记录'))

        to_delete = []
        for title, tenders in duplicate_titles.items():
            if keep_newest:
                keep = max(tenders, key=lambda t: t.created_at)
            else:
                keep = min(tenders, key=lambda t: t.created_at)

            for t in tenders:
                if t.id != keep.id:
                    to_delete.append(t)

        self.stdout.write(f'\n将删除 {len(to_delete)} 条记录:')
        for t in to_delete[:20]:
            self.stdout.write(f'  - ID:{t.id}, 标题:{t.title[:50]}, 创建时间:{t.created_at}')

        if len(to_delete) > 20:
            self.stdout.write(f'  ... 还有 {len(to_delete) - 20} 条记录')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] 预览模式，未实际删除'))
            return

        confirm = input('\n确认删除? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('已取消'))
            return

        ids_to_delete = [t.id for t in to_delete]
        deleted_count, _ = TenderProject.objects.filter(id__in=ids_to_delete).delete()

        self.stdout.write(self.style.SUCCESS(f'\n已删除 {deleted_count} 条重复记录'))
