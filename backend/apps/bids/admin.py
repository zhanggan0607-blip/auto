from django.contrib import admin
from .models import BidRecord, BidResult, BidStatistics


@admin.register(BidRecord)
class BidRecordAdmin(admin.ModelAdmin):
    list_display = ['tender', 'bid_code', 'bid_price', 'status', 'bid_manager', 'created_at']
    list_filter = ['status', 'bid_manager']
    search_fields = ['tender__title', 'bid_code']
    date_hierarchy = 'created_at'


@admin.register(BidResult)
class BidResultAdmin(admin.ModelAdmin):
    list_display = ['bid_record', 'result_type', 'winner_name', 'winner_price', 'announce_date']
    list_filter = ['result_type']
    search_fields = ['bid_record__tender__title', 'winner_name']


@admin.register(BidStatistics)
class BidStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'total_bids', 'won_bids', 'win_rate']
    list_filter = ['year', 'month']
    search_fields = ['user__username']
