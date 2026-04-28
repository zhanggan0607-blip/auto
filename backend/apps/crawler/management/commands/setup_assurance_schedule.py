from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '注册采集保障定时检查任务到Celery Beat'

    def handle(self, *args, **options):
        from django_celery_beat.models import CrontabSchedule, PeriodicTask

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='*/2',
            day_of_month='*',
            month_of_year='*',
            day_of_week='*',
            timezone='Asia/Shanghai',
        )

        task, created = PeriodicTask.objects.update_or_create(
            name='crawl_assurance_health_check',
            defaults={
                'crontab': schedule,
                'task': 'crawler.tasks.check_all_template_health',
                'enabled': True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS('✅ 采集保障定时检查任务已创建（每2小时执行一次）'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ 采集保障定时检查任务已更新（每2小时执行一次）'))

        self.stdout.write(f'  任务名: {task.name}')
        self.stdout.write(f'  执行频率: 每2小时')
        self.stdout.write(f'  状态: {"启用" if task.enabled else "禁用"}')
