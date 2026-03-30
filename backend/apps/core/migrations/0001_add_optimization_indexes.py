# Generated database index optimization migration

from django.db import migrations


class Migration(migrations.Migration):
    """
    数据库索引优化迁移
    添加高频查询字段的复合索引
    """

    dependencies = [
        ('enterprise', '0001_initial'),
        ('crawler', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # EnterpriseDocument 复合索引
                "CREATE INDEX IF NOT EXISTS enterprise_document_enterprise_type_idx ON enterprise_enterprisedocument (enterprise_id, document_type);",
                
                # CrawlResult 复合索引
                "CREATE INDEX IF NOT EXISTS crawl_result_session_status_idx ON crawler_crawlresult (session_id, status);",
                
                # EnterpriseMatchResult 复合索引
                "CREATE INDEX IF NOT EXISTS enterprise_match_enterprise_read_idx ON crawler_enterprisematchresult (enterprise_id, is_read);",
                
                # Tender 复合索引
                "CREATE INDEX IF NOT EXISTS tender_status_deadline_idx ON tenders_tender (status, deadline_date);",
                
                # BidRecord 复合索引
                "CREATE INDEX IF NOT EXISTS bid_record_status_created_idx ON bids_bidrecord (status, created_at);",
                
                # Notification 复合索引
                "CREATE INDEX IF NOT EXISTS notification_user_read_idx ON notifications_notification (user_id, is_read);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS enterprise_document_enterprise_type_idx;",
                "DROP INDEX IF EXISTS crawl_result_session_status_idx;",
                "DROP INDEX IF EXISTS enterprise_match_enterprise_read_idx;",
                "DROP INDEX IF EXISTS tender_status_deadline_idx;",
                "DROP INDEX IF EXISTS bid_record_status_created_idx;",
                "DROP INDEX IF EXISTS notification_user_read_idx;",
            ]
        ),
    ]
