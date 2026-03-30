# Generated migration for adding qualifications_list field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_remove_companycontract_company_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyinfo',
            name='qualifications_list',
            field=models.JSONField(blank=True, default=list, help_text='企业资质列表，每项包含：type(类型)、level(等级)、certificate_no(证书编号)、expiry_date(有效期)', verbose_name='资质列表'),
        ),
    ]
