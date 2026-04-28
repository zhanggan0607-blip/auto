from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventStore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(db_index=True, max_length=36, unique=True)),
                ('event_type', models.CharField(db_index=True, max_length=200)),
                ('source', models.CharField(max_length=50)),
                ('data', models.JSONField(default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('priority', models.IntegerField(default=1)),
                ('correlation_id', models.CharField(blank=True, db_index=True, max_length=36, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'event_store',
                'ordering': ['-created_at'],
            },
        ),
    ]
