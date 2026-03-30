"""
添加上海政府采购网站模板
"""
from django.db import migrations


def add_shanghai_gov_procurement_template(apps, schema_editor):
    """
    添加上海政府采购网站模板配置
    """
    WebsiteTemplate = apps.get_model('crawler', 'WebsiteTemplate')

    WebsiteTemplate.objects.create(
        name='上海政府采购',
        code='shanghai_gov_procurement',
        website_type='government',
        base_url='https://www.zfcg.sh.gov.cn/cgxx/cggg/index.html',
        list_url_pattern='https://www.zfcg.sh.gov.cn/cgxx/cggg/index_{page}.html',
        search_url_pattern='https://www.zfcg.sh.gov.cn/cgxx/cggg/search.html?keyword={keyword}',
        selectors={
            'list_container': '.list-box, .news-list, .procurement-list',
            'item_container': 'li, .item, .news-item',
            'title': 'a, .title, .item-title',
            'link': 'a',
            'date': '.date, .time, .publish-date, span:nth-child(n)',
            'region': '.region, .area, .district',
            'project_code': '.code, .project-code',
            'budget': '.budget, .amount, .money',
            'description': '.desc, .description, .summary',
            'detail_content': '.content, .detail-content, .article-content',
            'pagination_next': '.next, a.next, .page-next',
            'pagination_info': '.page-info, .total',
        },
        pagination_config={
            'type': 'link',
            'next_button': '.next, a.next',
            'page_info': '.page-info',
            'max_pages': 50,
            'page_size': 20,
            'url_pattern': 'index_{page}.html',
        },
        request_config={
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.zfcg.sh.gov.cn/',
            },
            'timeout': 30,
            'retry_times': 3,
            'retry_delay': 2,
        },
        requires_javascript=False,
        requires_login=False,
        login_config={},
        is_active=True,
        priority=90,
    )


def remove_shanghai_gov_procurement_template(apps, schema_editor):
    """
    删除上海政府采购网站模板配置
    """
    WebsiteTemplate = apps.get_model('crawler', 'WebsiteTemplate')
    WebsiteTemplate.objects.filter(code='shanghai_gov_procurement').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0004_add_shanghai_construction_template'),
    ]

    operations = [
        migrations.RunPython(
            add_shanghai_gov_procurement_template,
            remove_shanghai_gov_procurement_template
        ),
    ]