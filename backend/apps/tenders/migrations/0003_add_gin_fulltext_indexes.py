from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('tenders', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
                ),
                (
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS tender_projects_title_gin_idx "
                    "ON tender_projects USING gin (title gin_trgm_ops);"
                ),
                (
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS tender_projects_description_gin_idx "
                    "ON tender_projects USING gin (description gin_trgm_ops);"
                ),
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS tender_projects_title_gin_idx;",
                "DROP INDEX IF EXISTS tender_projects_description_gin_idx;",
            ],
        ),
    ]
