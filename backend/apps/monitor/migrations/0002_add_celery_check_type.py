"""
添加Celery健康检查类型
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monitoredservice',
            name='health_check_type',
            field=models.CharField(
                choices=[
                    ('http', 'HTTP请求'),
                    ('tcp', 'TCP端口'),
                    ('process', '进程检测'),
                    ('celery', 'Celery服务'),
                    ('custom', '自定义')
                ],
                default='http',
                max_length=20,
                verbose_name='检查类型'
            ),
        ),
    ]