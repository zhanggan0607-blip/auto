"""
Monitor模块初始迁移
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MonitoredService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='服务名称')),
                ('display_name', models.CharField(max_length=200, verbose_name='显示名称')),
                ('category', models.CharField(choices=[('database', '数据库'), ('cache', '缓存'), ('queue', '消息队列'), ('ai', 'AI服务'), ('storage', '存储'), ('crawler', '采集服务'), ('web', 'Web服务'), ('other', '其他')], default='other', max_length=20, verbose_name='服务类别')),
                ('description', models.TextField(blank=True, default='', verbose_name='服务描述')),
                ('health_check_url', models.URLField(blank=True, null=True, verbose_name='健康检查URL')),
                ('health_check_port', models.IntegerField(blank=True, null=True, verbose_name='健康检查端口')),
                ('health_check_type', models.CharField(choices=[('http', 'HTTP请求'), ('tcp', 'TCP端口'), ('process', '进程检测'), ('custom', '自定义')], default='http', max_length=20, verbose_name='检查类型')),
                ('health_check_interval', models.IntegerField(default=30, verbose_name='检查间隔(秒)')),
                ('health_check_timeout', models.IntegerField(default=10, verbose_name='检查超时(秒)')),
                ('consecutive_failures_to_restart', models.IntegerField(default=3, verbose_name='连续失败次数触发重启')),
                ('consecutive_failures_to_alert', models.IntegerField(default=3, verbose_name='连续失败次数触发告警')),
                ('restart_cooldown_minutes', models.IntegerField(default=5, verbose_name='重启冷却时间(分钟)')),
                ('max_restart_attempts', models.IntegerField(default=3, verbose_name='最大重启尝试次数')),
                ('is_enabled', models.BooleanField(default=True, verbose_name='是否启用监控')),
                ('is_critical', models.BooleanField(default=False, verbose_name='是否关键服务')),
                ('auto_restart_enabled', models.BooleanField(default=True, verbose_name='是否启用自动重启')),
                ('last_health_check', models.DateTimeField(blank=True, null=True, verbose_name='上次健康检查')),
                ('last_restart_time', models.DateTimeField(blank=True, null=True, verbose_name='上次重启时间')),
                ('consecutive_failures', models.IntegerField(default=0, verbose_name='连续失败次数')),
                ('restart_attempts_today', models.IntegerField(default=0, verbose_name='今日重启次数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '被监控服务',
                'verbose_name_plural': '被监控服务',
                'db_table': 'monitored_services',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ServiceActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('health_check', '健康检查'), ('auto_restart', '自动重启'), ('manual_restart', '手动重启'), ('manual_check', '手动检查'), ('alert_sent', '发送告警'), ('cooling_wait', '冷却等待')], max_length=50, verbose_name='操作类型')),
                ('status', models.CharField(choices=[('started', '开始'), ('success', '成功'), ('failed', '失败'), ('skipped', '跳过')], max_length=20, verbose_name='操作状态')),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='开始时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('duration_ms', models.IntegerField(blank=True, null=True, verbose_name='耗时(毫秒)')),
                ('trigger_condition', models.CharField(blank=True, default='', max_length=200, verbose_name='触发条件')),
                ('result_message', models.TextField(blank=True, default='', verbose_name='结果消息')),
                ('error_details', models.TextField(blank=True, default='', verbose_name='错误详情')),
                ('performed_by', models.CharField(default='system', max_length=100, verbose_name='执行者')),
                ('details', models.JSONField(blank=True, default=dict, verbose_name='详细信息')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_logs', to='monitor.monitoredservice', verbose_name='服务')),
            ],
            options={
                'verbose_name': '服务操作日志',
                'verbose_name_plural': '服务操作日志',
                'db_table': 'service_action_logs',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='ServiceAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('info', '通知'), ('warning', '警告'), ('error', '错误'), ('critical', '严重')], default='error', max_length=20, verbose_name='告警级别')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('notified', '已通知'), ('resolved', '已解决'), ('ignored', '已忽略')], default='pending', max_length=20, verbose_name='告警状态')),
                ('title', models.CharField(max_length=200, verbose_name='告警标题')),
                ('message', models.TextField(verbose_name='告警消息')),
                ('triggered_by', models.CharField(blank=True, default='', max_length=100, verbose_name='触发原因')),
                ('consecutive_failures', models.IntegerField(default=0, verbose_name='连续失败次数')),
                ('notified_at', models.DateTimeField(blank=True, null=True, verbose_name='通知时间')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='解决时间')),
                ('actions_taken', models.JSONField(blank=True, default=list, verbose_name='已执行操作')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='monitor.monitoredservice', verbose_name='服务')),
            ],
            options={
                'verbose_name': '服务告警',
                'verbose_name_plural': '服务告警',
                'db_table': 'service_alerts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ServiceHealthRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, verbose_name='检查时间')),
                ('is_healthy', models.BooleanField(verbose_name='是否健康')),
                ('response_time_ms', models.IntegerField(blank=True, null=True, verbose_name='响应时间(毫秒)')),
                ('cpu_usage', models.FloatField(blank=True, null=True, verbose_name='CPU使用率(%)')),
                ('memory_usage', models.FloatField(blank=True, null=True, verbose_name='内存使用率(%)')),
                ('error_message', models.TextField(blank=True, default='', verbose_name='错误信息')),
                ('details', models.JSONField(blank=True, default=dict, verbose_name='详细信息')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_records', to='monitor.monitoredservice', verbose_name='服务')),
            ],
            options={
                'verbose_name': '健康检查记录',
                'verbose_name_plural': '健康检查记录',
                'db_table': 'service_health_records',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='servicehealthrecord',
            index=models.Index(fields=['service', '-timestamp'], name='service_hea_service_idx'),
        ),
        migrations.AddIndex(
            model_name='servicehealthrecord',
            index=models.Index(fields=['-timestamp'], name='service_hea_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='servicealert',
            index=models.Index(fields=['service', '-created_at'], name='service_al_service_idx'),
        ),
        migrations.AddIndex(
            model_name='servicealert',
            index=models.Index(fields=['status', '-created_at'], name='service_al_status_idx'),
        ),
        migrations.AddIndex(
            model_name='servicealert',
            index=models.Index(fields=['level', '-created_at'], name='service_al_level_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceactionlog',
            index=models.Index(fields=['service', '-started_at'], name='service_ac_service_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceactionlog',
            index=models.Index(fields=['action_type', '-started_at'], name='service_ac_action__idx'),
        ),
        migrations.AddIndex(
            model_name='serviceactionlog',
            index=models.Index(fields=['-started_at'], name='service_ac_timesta_idx'),
        ),
    ]