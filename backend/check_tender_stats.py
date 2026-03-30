from apps.tenders.models import TenderProject, TenderSource

print('=== 招标项目统计 ===')
total_tenders = TenderProject.objects.count()
pending = TenderProject.objects.filter(status='pending').count()
matched = TenderProject.objects.filter(status='matched').count()
processing = TenderProject.objects.filter(status='processing').count()
won = TenderProject.objects.filter(status='won').count()
lost = TenderProject.objects.filter(status='lost').count()

print(f'总招标项目数: {total_tenders}')
print(f'待处理: {pending}')
print(f'已匹配: {matched}')
print(f'处理中: {processing}')
print(f'已中标: {won}')
print(f'未中标: {lost}')

print()
print('=== 数据来源统计 ===')
for source in TenderSource.objects.all():
    count = TenderProject.objects.filter(source=source).count()
    print(f'  {source.name}: {count}条')

print()
print('=== 最新招标项目 ===')
recent = TenderProject.objects.order_by('-created_at')[:10]
for t in recent:
    source_name = t.source.name if t.source else '无'
    print(f'  [{t.status}] {t.title[:40]} | 来源:{source_name} | 发布:{t.publish_date}')