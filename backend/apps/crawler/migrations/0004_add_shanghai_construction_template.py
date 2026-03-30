"""
添加上海建筑建材业网站模板
"""
from django.db import migrations


def add_shanghai_construction_template(apps, schema_editor):
    """
    添加上海建筑建材业网站模板配置
    """
    WebsiteTemplate = apps.get_model('crawler', 'WebsiteTemplate')
    
    WebsiteTemplate.objects.create(
        name='上海建筑建材业',
        code='shanghai_construction',
        website_type='construction',
        base_url='https://ciac.zjw.sh.gov.cn/JGBAppZtbInterWeb/pc/#/jyggList',
        list_url_pattern='https://ciac.zjw.sh.gov.cn/JGBAppZtbInterWeb/pc/#/jyggList?gglx={notice_type}',
        search_url_pattern='https://ciac.zjw.sh.gov.cn/JGBAppZtbInterWeb/pc/#/jyggList?gglx={notice_type}&keyword={keyword}',
        selectors={
            'list_container': '.el-table__body',
            'item_container': '.el-table__row',
            'title': '.ggmc, .title, a',
            'link': 'a',
            'date': '.fbsj, .date, td:nth-child(3)',
            'region': '.jsdd, .region, td:nth-child(4)',
            'project_code': '.ggbh, .code, td:nth-child(1)',
            'project_type': '.xmlx, td:nth-child(5)',
            'budget': '.ysje, .budget',
            'description': '.gg-content, .content',
            'detail_content': '.gg-content, .detail-content',
            'pagination_next': '.btn-next',
            'pagination_info': '.el-pagination__total',
        },
        pagination_config={
            'type': 'click',
            'next_button': '.btn-next',
            'page_info': '.el-pagination__total',
            'max_pages': 100,
            'page_size': 20,
        },
        request_config={
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            },
            'timeout': 30,
            'retry_times': 3,
            'retry_delay': 2,
        },
        requires_javascript=True,
        requires_login=False,
        login_config={},
        is_active=True,
        priority=100,
    )


def remove_shanghai_construction_template(apps, schema_editor):
    """
    删除上海建筑建材业网站模板配置
    """
    WebsiteTemplate = apps.get_model('crawler', 'WebsiteTemplate')
    WebsiteTemplate.objects.filter(code='shanghai_construction').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0003_crawlschedule_crawl_mode'),
    ]

    operations = [
        migrations.RunPython(
            add_shanghai_construction_template,
            remove_shanghai_construction_template
        ),
    ]
