from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('openclaw', '0008_alter_agentmemorystore_unique_together_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='llmprovider',
            old_name='_api_key',
            new_name='encrypted_api_key',
        ),
    ]
