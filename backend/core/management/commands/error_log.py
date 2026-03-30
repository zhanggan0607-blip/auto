"""
Django管理命令：错误日志管理

用法:
    python manage.py error_log list                    # 列出最近的错误
    python manage.py error_log search <keyword>        # 搜索错误
    python manage.py error_log stats                   # 显示统计信息
    python manage.py error_log add                     # 交互式添加错误
    python manage.py error_log add --type="数据库迁移" --desc="字段不存在" --scenario="调用API时" --solution="执行迁移"
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from utils.error_logger_service import error_logger
import argparse


class Command(BaseCommand):
    help = '管理项目错误日志（ERROR_LOG.md）'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='subcommand', help='子命令')

        list_parser = subparsers.add_parser('list', help='列出最近的错误')
        list_parser.add_argument('--limit', type=int, default=10, help='显示数量')

        search_parser = subparsers.add_parser('search', help='搜索错误')
        search_parser.add_argument('keyword', type=str, help='搜索关键词')

        subparsers.add_parser('stats', help='显示统计信息')

        add_parser = subparsers.add_parser('add', help='添加错误记录')
        add_parser.add_argument('--type', type=str, required=True, help='错误类型')
        add_parser.add_argument('--desc', type=str, required=True, help='错误描述')
        add_parser.add_argument('--scenario', type=str, default='', help='发生场景')
        add_parser.add_argument('--message', type=str, default='', help='错误信息')
        add_parser.add_argument('--solution', type=str, default='', help='解决方案')
        add_parser.add_argument('--prevention', type=str, default='', help='预防措施')
        add_parser.add_argument('--files', type=str, default='', help='相关文件（逗号分隔）')
        add_parser.add_argument('--status', type=str, default='已解决', help='状态')
        add_parser.add_argument('--no-check-duplicate', action='store_true', help='跳过去重检查')

    def handle(self, *args, **options):
        subcommand = options.get('subcommand')

        if not subcommand:
            self.print_help('manage.py', 'error_log')
            return

        if subcommand == 'list':
            self.handle_list(options)
        elif subcommand == 'search':
            self.handle_search(options)
        elif subcommand == 'stats':
            self.handle_stats()
        elif subcommand == 'add':
            self.handle_add(options)

    def handle_list(self, options):
        """
        列出最近的错误
        """
        limit = options.get('limit', 10)
        errors = error_logger.get_recent_errors(limit)

        if not errors:
            self.stdout.write(self.style.WARNING('暂无错误记录'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n最近 {len(errors)} 条错误记录:\n'))
        self.stdout.write('-' * 80)

        for error in errors:
            self.stdout.write(f"  {error['error_number']}: [{error['error_type']}] {error['description']}")
            self.stdout.write(f"         日期: {error['date']}")
            self.stdout.write('-' * 80)

    def handle_search(self, options):
        """
        搜索错误
        """
        keyword = options.get('keyword')
        if not keyword:
            raise CommandError('请提供搜索关键词')

        results = error_logger.search_errors(keyword)

        if not results:
            self.stdout.write(self.style.WARNING(f'未找到包含 "{keyword}" 的错误记录'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n找到 {len(results)} 条匹配记录:\n'))
        self.stdout.write('-' * 80)

        for error in results:
            self.stdout.write(f"  {error['error_number']}: [{error['error_type']}] {error['description']}")
            self.stdout.write(f"         日期: {error['date']}")
            self.stdout.write('-' * 80)

    def handle_stats(self):
        """
        显示统计信息
        """
        stats = error_logger.get_error_stats()

        self.stdout.write(self.style.SUCCESS('\n错误统计信息:\n'))
        self.stdout.write(f"  总计: {stats['total']} 条错误记录\n")

        if stats['by_type']:
            self.stdout.write('\n  按类型分布:')
            for error_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"    - {error_type}: {count} 条")

    def handle_add(self, options):
        """
        添加错误记录
        """
        related_files = []
        if options.get('files'):
            related_files = [f.strip() for f in options['files'].split(',')]

        result = error_logger.log_error(
            error_type=options['type'],
            description=options['desc'],
            scenario=options.get('scenario', ''),
            error_message=options.get('message', ''),
            solution=options.get('solution', ''),
            prevention=options.get('prevention', ''),
            related_files=related_files,
            status=options.get('status', '已解决'),
            check_duplicate=not options.get('no_check_duplicate', False)
        )

        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(f"\n✓ {result['message']}"))
            self.stdout.write(f"  编号: E{result.get('error_number', 0):03d}")
            self.stdout.write(f"  类型: {result.get('error_type', '')}")
        elif result.get('duplicate'):
            self.stdout.write(self.style.WARNING(f"\n⚠ {result['message']}"))
        else:
            self.stdout.write(self.style.ERROR(f"\n✗ {result['message']}"))
