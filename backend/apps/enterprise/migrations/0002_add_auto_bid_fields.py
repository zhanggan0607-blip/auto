"""
添加企业自动投标配置字段
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterprise',
            name='auto_bid_enabled',
            field=models.BooleanField(default=False, verbose_name='是否启用自动投标'),
        ),
        migrations.AddField(
            model_name='enterprise',
            name='auto_bid_threshold',
            field=models.IntegerField(default=60, verbose_name='自动投标阈值'),
        ),
        migrations.AddField(
            model_name='enterprise',
            name='auto_upload_enabled',
            field=models.BooleanField(default=False, verbose_name='是否启用自动上传'),
        ),
        migrations.AddField(
            model_name='enterprise',
            name='auto_bid_keywords',
            field=models.JSONField(default=list, blank=True, verbose_name='自动投标关键词'),
        ),
        migrations.AddField(
            model_name='enterprise',
            name='notification_channels',
            field=models.JSONField(default=list, blank=True, verbose_name='通知渠道'),
        ),
    ]
