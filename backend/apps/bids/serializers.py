"""
投标管理模块 - 序列化器
"""
from rest_framework import serializers
from .models import BidRecord, BidResult, BidStatistics


class BidRecordListSerializer(serializers.ModelSerializer):
    """
    投标记录列表序列化器
    """
    tender_title = serializers.CharField(source='tender.title', read_only=True)
    tender_project_code = serializers.CharField(source='tender.project_code', read_only=True)
    tender_region = serializers.CharField(source='tender.region', read_only=True)
    tender_deadline = serializers.DateField(source='tender.deadline_date', read_only=True)
    tender_id = serializers.IntegerField(source='tender.id', read_only=True)
    bid_manager_name = serializers.CharField(source='bid_manager.username', read_only=True)
    bid_manager_id = serializers.IntegerField(source='bid_manager.id', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    team_member_ids = serializers.SerializerMethodField()
    result_type = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = BidRecord
        fields = [
            'id', 'tender_id', 'tender_title', 'tender_project_code', 'tender_region',
            'tender_deadline', 'bid_code', 'bid_price', 'bid_date', 'status',
            'bid_manager_id', 'bid_manager_name', 'team_member_ids',
            'win_probability', 'competitor_count',
            'notes', 'result_type', 'result', 'created_by_name', 'created_at'
        ]

    def get_team_member_ids(self, obj):
        return list(obj.team_members.values_list('id', flat=True))

    def get_result_type(self, obj):
        if hasattr(obj, 'result') and obj.result:
            return obj.result.result_type
        return None

    def get_result(self, obj):
        if hasattr(obj, 'result') and obj.result:
            return BidResultSerializer(obj.result).data
        return None


class BidRecordDetailSerializer(serializers.ModelSerializer):
    """
    投标记录详情序列化器
    """
    tender_title = serializers.CharField(source='tender.title', read_only=True)
    bid_manager_name = serializers.CharField(source='bid_manager.username', read_only=True)
    team_member_names = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = BidRecord
        fields = [
            'id', 'tender', 'tender_title', 'bid_code', 'bid_price', 'bid_date',
            'status', 'bid_documents', 'documents', 'bid_manager', 'bid_manager_name',
            'team_members', 'team_member_names', 'notes', 'win_probability',
            'competitor_count', 'result', 'created_at', 'updated_at'
        ]

    def get_team_member_names(self, obj):
        return [member.username for member in obj.team_members.all()]

    def get_documents(self, obj):
        from apps.documents.serializers import GeneratedDocumentSerializer
        return GeneratedDocumentSerializer(
            obj.bid_documents.all(), many=True, context=self.context
        ).data

    def get_result(self, obj):
        if hasattr(obj, 'result'):
            return BidResultSerializer(obj.result).data
        return None


class BidRecordCreateSerializer(serializers.ModelSerializer):
    """
    投标记录创建序列化器
    """
    class Meta:
        model = BidRecord
        fields = [
            'tender', 'bid_code', 'bid_price', 'bid_date', 'status',
            'bid_documents', 'bid_manager', 'team_members', 'notes',
            'win_probability', 'competitor_count'
        ]


class BidRecordUpdateSerializer(serializers.ModelSerializer):
    """
    投标记录更新序列化器
    """
    class Meta:
        model = BidRecord
        fields = [
            'bid_code', 'bid_price', 'bid_date', 'status',
            'bid_documents', 'bid_manager', 'team_members', 'notes',
            'win_probability', 'competitor_count'
        ]


class BidResultSerializer(serializers.ModelSerializer):
    """
    中标结果序列化器
    """
    bid_record_title = serializers.CharField(source='bid_record.tender.title', read_only=True)

    class Meta:
        model = BidResult
        fields = [
            'id', 'bid_record', 'bid_record_title', 'result_type',
            'winner_name', 'winner_price', 'our_rank', 'total_bidders',
            'announce_date', 'announce_url', 'win_reason', 'lose_reason',
            'lessons_learned', 'created_at', 'updated_at'
        ]


class BidResultCreateSerializer(serializers.ModelSerializer):
    """
    中标结果创建序列化器
    """
    class Meta:
        model = BidResult
        fields = [
            'bid_record', 'result_type', 'winner_name', 'winner_price',
            'our_rank', 'total_bidders', 'announce_date', 'announce_url',
            'win_reason', 'lose_reason', 'lessons_learned'
        ]


class BidStatisticsSerializer(serializers.ModelSerializer):
    """
    投标统计序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BidStatistics
        fields = [
            'id', 'username', 'total_bids', 'won_bids', 'lost_bids',
            'pending_bids', 'total_bid_amount', 'total_win_amount',
            'win_rate', 'year', 'month', 'created_at', 'updated_at'
        ]
