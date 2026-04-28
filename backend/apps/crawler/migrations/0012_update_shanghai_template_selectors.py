from django.db import migrations


def update_shanghai_template_selectors(apps, schema_editor):
    WebsiteTemplate = apps.get_model('crawler', 'WebsiteTemplate')
    try:
        template = WebsiteTemplate.objects.get(code='shanghai_gov_procurement')
        template.selectors = {
            'list_container': 'ul.list',
            'item_container': 'ul.list > li',
            'title': 'a, .list-title a',
            'link': 'a',
            'date': '.publish-time',
            'region': '.title-head',
            'project_code': '.code, .project-code',
            'budget': '.budget, .amount',
            'description': '.desc, .description',
            'detail_content': '.content, .detail-content',
            'pagination_next': '.next, a.next',
            'pagination_info': '.page-info, .total',
        }
        template.pagination_config = {
            'type': 'link',
            'next_button': '.next, a.next',
            'page_info': '.page-info',
            'max_pages': 50,
            'page_size': 20,
            'url_pattern': 'index_{page}.html',
        }
        template.requires_javascript = True
        template.base_url = 'https://www.zfcg.sh.gov.cn/site/category?parentId=137028&childrenCode=ZcyAnnouncement2&page=1'
        template.list_url_pattern = 'https://www.zfcg.sh.gov.cn/site/category?parentId=137028&childrenCode=ZcyAnnouncement2&page={page}'
        template.save()
    except WebsiteTemplate.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0011_crawlhealthcheck_crawloptimizationplan_and_more'),
    ]

    operations = [
        migrations.RunPython(update_shanghai_template_selectors, migrations.RunPython.noop),
    ]
