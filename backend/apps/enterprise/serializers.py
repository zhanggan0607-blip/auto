"""
SAAS企业资料库模块 - 序列化器
"""
from rest_framework import serializers
from utils.crypto import AESCrypto, mask_sensitive_data
from .models import (
    Enterprise, EnterpriseQualification, EnterprisePerformance,
    EnterpriseMatchRule, EnterpriseMatchResult, EnterpriseContact,
    EnterpriseBidConfig, EnterpriseDocument, DocumentAuditLog,
    EnterpriseKeyPersonnel
)


class EnterpriseQualificationSerializer(serializers.ModelSerializer):
    """
    企业资质序列化器
    """
    qualification_category_display = serializers.CharField(source='get_qualification_category_display', read_only=True)
    qualification_name_display = serializers.CharField(source='get_qualification_name_display', read_only=True)
    grade_display = serializers.SerializerMethodField()
    days_to_expiry = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseQualification
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_grade_display(self, obj):
        """
        获取资质等级的显示文本
        """
        if not obj.grade:
            return ''

        grade_map = {
            'survey_first': '甲级',
            'survey_second': '乙级',
            'survey_third': '丙级',
            'survey_labor': '不分等级',
            'design_first': '甲级',
            'design_second': '乙级',
            'design_third': '丙级',
            'design_fourth': '丁级',
            'special': '特级',
            'first': '一级',
            'second': '二级',
            'third': '三级',
            'no_level': '不分等级',
            'supervision_no_level': '不分等级',
            'supervision_first': '甲级',
            'supervision_second': '乙级',
            'supervision_third': '丙级（部分专业）',
        }
        return grade_map.get(obj.grade, obj.grade)

    def get_days_to_expiry(self, obj):
        """
        获取距离过期的天数
        """
        if not obj.expiry_date:
            return None

        from datetime import date
        delta = obj.expiry_date - date.today()
        return delta.days


class EnterprisePerformanceSerializer(serializers.ModelSerializer):
    """
    企业业绩序列化器
    """
    performance_type_display = serializers.CharField(source='get_performance_type_display', read_only=True)
    
    class Meta:
        model = EnterprisePerformance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EnterpriseContactSerializer(serializers.ModelSerializer):
    """
    企业联系人序列化器
    """
    contact_type_display = serializers.CharField(source='get_contact_type_display', read_only=True)
    
    class Meta:
        model = EnterpriseContact
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EnterpriseBidConfigSerializer(serializers.ModelSerializer):
    """
    企业投标配置序列化器
    """
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    builder_level_display = serializers.CharField(source='get_builder_level_display', read_only=True)
    
    class Meta:
        model = EnterpriseBidConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EnterpriseBidConfigCreateSerializer(serializers.ModelSerializer):
    """
    企业投标配置创建序列化器
    """
    class Meta:
        model = EnterpriseBidConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_enterprise(self, value):
        """
        验证企业是否存在
        """
        if not value:
            raise serializers.ValidationError('企业不能为空')
        return value


class EnterpriseWithBidConfigSerializer(serializers.ModelSerializer):
    """
    企业完整信息序列化器（包含投标配置）
    """
    enterprise_type_display = serializers.CharField(source='get_enterprise_type_display', read_only=True)
    qualifications = EnterpriseQualificationSerializer(many=True, read_only=True)
    performances = EnterprisePerformanceSerializer(many=True, read_only=True)
    contacts = EnterpriseContactSerializer(many=True, read_only=True)
    bid_config = EnterpriseBidConfigSerializer(read_only=True)
    
    class Meta:
        model = Enterprise
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class EnterpriseSerializer(serializers.ModelSerializer):
    """
    企业序列化器
    """
    enterprise_type_display = serializers.CharField(source='get_enterprise_type_display', read_only=True)
    qualifications = EnterpriseQualificationSerializer(many=True, read_only=True)
    performances = EnterprisePerformanceSerializer(many=True, read_only=True)
    contacts = EnterpriseContactSerializer(many=True, read_only=True)
    bank_account_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = Enterprise
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_bank_account_masked(self, obj):
        """
        获取脱敏后的银行账号
        """
        if obj.bank_account:
            decrypted = AESCrypto.decrypt(obj.bank_account) if obj.bank_account else ''
            return mask_sensitive_data(decrypted, 'bank_account')
        return ''
    
    def to_internal_value(self, data):
        """
        预处理输入数据，将空字符串转为None，加密敏感字段
        """
        date_fields = ['establishment_date']
        decimal_fields = ['registered_capital', 'min_net_assets', 'max_debt_ratio',
                          'min_credit_line', 'min_working_capital', 'min_registered_capital']
        string_fields = ['address', 'credit_code', 'legal_person', 'province', 'city',
                         'district', 'contact_person', 'contact_phone', 'contact_email',
                         'bank_name', 'bank_account', 'enterprise_type', 'enterprise_scale',
                         'business_scope']

        data = data.copy() if hasattr(data, 'copy') else dict(data)

        for field in date_fields:
            if field in data and data[field] == '':
                data[field] = None

        for field in decimal_fields:
            if field in data and data[field] == '':
                data[field] = None

        for field in string_fields:
            if field in data and data[field] == '':
                data[field] = None

        if data.get('bank_account'):
            bank_account = data['bank_account']
            if bank_account and isinstance(bank_account, str):
                try:
                    decrypted = AESCrypto.decrypt(bank_account)
                    if decrypted and decrypted != bank_account:
                        data['bank_account'] = bank_account
                    else:
                        data['bank_account'] = AESCrypto.encrypt(bank_account)
                except Exception:
                    data['bank_account'] = AESCrypto.encrypt(bank_account)

        return super().to_internal_value(data)
    
    def to_representation(self, instance):
        """
        输出时解密敏感字段
        """
        data = super().to_representation(instance)
        if data.get('bank_account'):
            decrypted = AESCrypto.decrypt(data['bank_account'])
            data['bank_account'] = decrypted
        return data


class EnterpriseListSerializer(serializers.ModelSerializer):
    """
    企业列表序列化器
    """
    enterprise_type_display = serializers.CharField(source='get_enterprise_type_display', read_only=True)
    qualification_count = serializers.SerializerMethodField()
    performance_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Enterprise
        fields = ['id', 'name', 'enterprise_type', 'enterprise_type_display',
                  'credit_code', 'province', 'city', 'district', 'address',
                  'legal_person', 'registered_capital', 'establishment_date',
                  'contact_person', 'contact_phone', 'contact_email',
                  'bank_name', 'bank_account', 'enterprise_scale',
                  'staff_count', 'insured_count', 'business_scope',
                  'is_active', 'is_verified', 'qualification_count', 
                  'performance_count', 'created_at']
    
    def get_qualification_count(self, obj):
        """
        获取资质数量
        """
        return obj.qualifications.count()
    
    def get_performance_count(self, obj):
        """
        获取业绩数量
        """
        return obj.performances.count()


class EnterpriseMatchRuleSerializer(serializers.ModelSerializer):
    """
    企业匹配规则序列化器
    """
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    
    class Meta:
        model = EnterpriseMatchRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EnterpriseMatchResultSerializer(serializers.ModelSerializer):
    """
    企业匹配结果序列化器
    """
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    match_level_display = serializers.CharField(help_text='high: 高度匹配, medium: 中度匹配, low: 低度匹配')
    
    class Meta:
        model = EnterpriseMatchResult
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EnterpriseMatchResultListSerializer(serializers.ModelSerializer):
    """
    企业匹配结果列表序列化器
    """
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    
    class Meta:
        model = EnterpriseMatchResult
        fields = ['id', 'enterprise_name', 'tender_title', 'tender_url', 'tender_source',
                  'publish_date', 'deadline_date', 'match_score', 'match_level',
                  'is_read', 'is_favorite', 'is_applied', 'created_at']


class MatchTenderSerializer(serializers.Serializer):
    """
    匹配招标信息序列化器
    """
    title = serializers.CharField(max_length=500, help_text='招标标题')
    url = serializers.URLField(max_length=1000, help_text='招标链接')
    source = serializers.CharField(max_length=100, required=False, help_text='招标来源')
    
    publish_date = serializers.DateField(required=False, help_text='发布日期')
    deadline_date = serializers.DateField(required=False, help_text='截止日期')
    
    region = serializers.CharField(max_length=100, required=False, help_text='地区')
    industry = serializers.CharField(max_length=100, required=False, help_text='行业')
    category = serializers.CharField(max_length=100, required=False, help_text='类别')
    
    budget = serializers.FloatField(required=False, help_text='预算金额')
    
    description = serializers.CharField(required=False, help_text='项目描述')
    requirements = serializers.CharField(required=False, help_text='技术要求')
    
    enterprise_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='指定企业ID列表（为空则匹配所有企业）'
    )


class EnterpriseStatisticsSerializer(serializers.Serializer):
    """
    企业统计信息序列化器
    """
    qualification_count = serializers.IntegerField()
    valid_qualification_count = serializers.IntegerField()
    performance_count = serializers.IntegerField()
    match_result_count = serializers.IntegerField()
    high_match_count = serializers.IntegerField()
    medium_match_count = serializers.IntegerField()
    low_match_count = serializers.IntegerField()


class EnterpriseDocumentSerializer(serializers.ModelSerializer):
    """
    企业证书序列化器
    """
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recognition_status_display = serializers.CharField(source='get_recognition_status_display', read_only=True) if hasattr(EnterpriseDocument, 'get_recognition_status_display') else serializers.CharField(read_only=True)
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    days_to_expiry = serializers.ReadOnlyField()
    file_url = serializers.ReadOnlyField()
    file_size_display = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = EnterpriseDocument
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'status', 'file_size', 'file_type', 
                           'extracted_content', 'extracted_data', 'recognition_status', 'recognition_error',
                           'recognition_at', 'comparison_result', 'comparison_at']


class EnterpriseDocumentListSerializer(serializers.ModelSerializer):
    """
    企业证书列表序列化器
    """
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    days_to_expiry = serializers.ReadOnlyField()
    file_size_display = serializers.ReadOnlyField()
    recognition_status = serializers.CharField(read_only=True)
    is_ai_reference = serializers.BooleanField(read_only=True)
    is_bid_material = serializers.BooleanField(read_only=True)

    class Meta:
        model = EnterpriseDocument
        fields = [
            'id', 'enterprise', 'enterprise_name', 'document_type', 'document_type_display',
            'document_name', 'document_no', 'issue_date', 'expiry_date', 'days_to_expiry',
            'status', 'status_display', 'file_path', 'file_url', 'file_size', 'file_size_display',
            'is_primary', 'is_verified', 'recognition_status', 'is_ai_reference', 'is_bid_material',
            'created_at'
        ]


class EnterpriseDocumentUploadSerializer(serializers.ModelSerializer):
    """
    企业证书上传序列化器
    """
    is_ai_reference = serializers.BooleanField(default=True, help_text='是否用于AI招标公告比对')
    is_bid_material = serializers.BooleanField(default=True, help_text='是否用于标书生成素材')
    auto_recognize = serializers.BooleanField(default=False, write_only=True, help_text='上传后自动识别')
    
    class Meta:
        model = EnterpriseDocument
        fields = [
            'enterprise', 'document_type', 'document_name', 'document_no',
            'issue_date', 'expiry_date', 'issuing_authority', 'file_path',
            'description', 'tags', 'is_primary', 'remind_days',
            'is_ai_reference', 'is_bid_material', 'auto_recognize'
        ]
    
    def validate_file_path(self, value):
        """
        验证文件
        """
        if value:
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'doc', 'docx', 'xls', 'xlsx']
            ext = value.name.split('.')[-1].lower() if '.' in value.name else ''
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f'不支持的文件类型: {ext}。支持格式: {", ".join(allowed_extensions)}')
            
            max_size = 10 * 1024 * 1024
            if value.size > max_size:
                raise serializers.ValidationError('文件大小不能超过10MB')
        
        return value


class EnterpriseDocumentStatisticsSerializer(serializers.Serializer):
    """
    企业证书统计序列化器
    """
    total_count = serializers.IntegerField()
    valid_count = serializers.IntegerField()
    expiring_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    by_type = serializers.DictField()


class DocumentAuditLogSerializer(serializers.ModelSerializer):
    """
    证书审计日志序列化器
    """
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    document_name = serializers.CharField(source='document.document_name', read_only=True)
    operated_by_name = serializers.CharField(source='operated_by.username', read_only=True)

    class Meta:
        model = DocumentAuditLog
        fields = [
            'id', 'document', 'document_name', 'action_type', 'action_type_display',
            'action_detail', 'is_success', 'error_message', 'recognition_result',
            'comparison_result', 'update_result', 'ip_address', 'operated_by',
            'operated_by_name', 'operated_at'
        ]
        read_only_fields = ['operated_at']


class EnterpriseKeyPersonnelSerializer(serializers.ModelSerializer):
    """
    企业关键人员序列化器
    """
    personnel_type_display = serializers.CharField(source='get_personnel_type_display', read_only=True)
    officer_type_display = serializers.CharField(source='get_officer_type_display', read_only=True)
    certificate_status_display = serializers.CharField(source='get_certificate_status_display', read_only=True)
    title_level_display = serializers.CharField(source='get_title_level_display', read_only=True)
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)
    days_to_expiry = serializers.SerializerMethodField()
    builder_certificate_file_url = serializers.SerializerMethodField()
    safety_certificate_b_file_url = serializers.SerializerMethodField()
    engineer_certificate_file_url = serializers.SerializerMethodField()
    social_security_proof_url = serializers.SerializerMethodField()
    no_ongoing_commitment_url = serializers.SerializerMethodField()
    labor_contract_url = serializers.SerializerMethodField()
    similar_performance_proof_url = serializers.SerializerMethodField()
    id_number_masked = serializers.SerializerMethodField()

    FILE_FIELDS = [
        'builder_certificate_file', 'safety_certificate_b_file',
        'engineer_certificate_file', 'social_security_proof',
        'no_ongoing_commitment', 'labor_contract', 'similar_performance_proof'
    ]

    class Meta:
        model = EnterpriseKeyPersonnel
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'certificate_status', 'personnel_id']

    def validate(self, attrs):
        """
        对于文件字段，如果传入的是字符串（URL）而不是文件对象，则移除该字段（保留原有值）
        """
        for field in self.FILE_FIELDS:
            if field in attrs and isinstance(attrs[field], str):
                attrs.pop(field)
        return attrs

    def get_id_number_masked(self, obj):
        """
        获取脱敏后的身份证号
        """
        if obj.id_number:
            return mask_sensitive_data(obj.id_number, 'id_number')
        return ''

    def get_days_to_expiry(self, obj):
        """获取证书到期天数"""
        if obj.expiry_date:
            from datetime import date
            delta = obj.expiry_date - date.today()
            return delta.days
        return None
    
    def get_builder_certificate_file_url(self, obj):
        if obj.builder_certificate_file:
            return obj.builder_certificate_file.url
        return None
    
    def get_safety_certificate_b_file_url(self, obj):
        if obj.safety_certificate_b_file:
            return obj.safety_certificate_b_file.url
        return None
    
    def get_engineer_certificate_file_url(self, obj):
        if obj.engineer_certificate_file:
            return obj.engineer_certificate_file.url
        return None
    
    def get_social_security_proof_url(self, obj):
        if obj.social_security_proof:
            return obj.social_security_proof.url
        return None
    
    def get_no_ongoing_commitment_url(self, obj):
        if obj.no_ongoing_commitment:
            return obj.no_ongoing_commitment.url
        return None
    
    def get_labor_contract_url(self, obj):
        if obj.labor_contract:
            return obj.labor_contract.url
        return None
    
    def get_similar_performance_proof_url(self, obj):
        if obj.similar_performance_proof:
            return obj.similar_performance_proof.url
        return None


class EnterpriseKeyPersonnelListSerializer(serializers.ModelSerializer):
    """
    企业关键人员列表序列化器
    """
    personnel_type_display = serializers.CharField(source='get_personnel_type_display', read_only=True)
    officer_type_display = serializers.CharField(source='get_officer_type_display', read_only=True)
    certificate_status_display = serializers.CharField(source='get_certificate_status_display', read_only=True)
    title_level_display = serializers.CharField(source='get_title_level_display', read_only=True)
    days_to_expiry = serializers.SerializerMethodField()
    builder_certificate_file_url = serializers.SerializerMethodField()
    safety_certificate_b_file_url = serializers.SerializerMethodField()
    engineer_certificate_file_url = serializers.SerializerMethodField()
    social_security_proof_url = serializers.SerializerMethodField()
    no_ongoing_commitment_url = serializers.SerializerMethodField()
    labor_contract_url = serializers.SerializerMethodField()
    similar_performance_proof_url = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseKeyPersonnel
        fields = [
            'id', 'enterprise', 'personnel_type', 'personnel_type_display', 'personnel_id',
            'name', 'id_number', 'birth_date', 'builder_certificate', 'safety_certificate_b',
            'engineer_title_certificate', 'certificate_number', 'certificate_major',
            'expiry_date', 'days_to_expiry', 'issuing_authority', 'issuing_authority_full',
            'title_level', 'title_level_display', 'officer_type', 'officer_type_display',
            'is_registered_locally', 'social_security_code', 'professional_years',
            'certificate_status', 'certificate_status_display', 'is_available', 'phone',
            'builder_certificate_file_url', 'safety_certificate_b_file_url',
            'engineer_certificate_file_url', 'social_security_proof_url',
            'no_ongoing_commitment_url', 'labor_contract_url', 'similar_performance_proof_url'
        ]

    def get_days_to_expiry(self, obj):
        """获取证书到期天数"""
        if obj.expiry_date:
            from datetime import date
            delta = obj.expiry_date - date.today()
            return delta.days
        return None

    def get_builder_certificate_file_url(self, obj):
        if obj.builder_certificate_file:
            return obj.builder_certificate_file.url
        return None

    def get_safety_certificate_b_file_url(self, obj):
        if obj.safety_certificate_b_file:
            return obj.safety_certificate_b_file.url
        return None

    def get_engineer_certificate_file_url(self, obj):
        if obj.engineer_certificate_file:
            return obj.engineer_certificate_file.url
        return None

    def get_social_security_proof_url(self, obj):
        if obj.social_security_proof:
            return obj.social_security_proof.url
        return None

    def get_no_ongoing_commitment_url(self, obj):
        if obj.no_ongoing_commitment:
            return obj.no_ongoing_commitment.url
        return None

    def get_labor_contract_url(self, obj):
        if obj.labor_contract:
            return obj.labor_contract.url
        return None

    def get_similar_performance_proof_url(self, obj):
        if obj.similar_performance_proof:
            return obj.similar_performance_proof.url
        return None



