"""
SAAS企业资料库模块 - Admin配置
"""
from django.contrib import admin
from .models import (
    Enterprise, EnterpriseQualification, EnterprisePerformance,
    EnterpriseMatchRule, EnterpriseMatchResult, EnterpriseContact,
    EnterpriseBidConfig, EnterpriseKeyPersonnel
)


class EnterpriseQualificationInline(admin.TabularInline):
    """
    企业资质内联
    """
    model = EnterpriseQualification
    extra = 1
    fields = ['qualification_category', 'qualification_name', 'grade', 'is_valid',
              'expiry_date', 'is_primary']


class EnterprisePerformanceInline(admin.TabularInline):
    """
    企业业绩内联
    """
    model = EnterprisePerformance
    extra = 0
    fields = ['project_name', 'performance_type', 'client_name', 'contract_amount', 
              'start_date', 'end_date']


class EnterpriseContactInline(admin.TabularInline):
    """
    企业联系人内联
    """
    model = EnterpriseContact
    extra = 1
    fields = ['contact_type', 'name', 'position', 'phone', 'mobile', 'is_primary']


class EnterpriseKeyPersonnelInline(admin.TabularInline):
    """
    企业关键人员内联
    """
    model = EnterpriseKeyPersonnel
    extra = 0
    fields = ['personnel_type', 'name', 'certificate_number', 'certificate_major',
              'expiry_date', 'certificate_status', 'is_available']


@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    """
    企业管理
    """
    list_display = ['name', 'enterprise_type', 'credit_code', 
                    'province', 'city', 'contact_person', 'contact_phone', 
                    'is_active', 'is_verified', 'created_at']
    list_filter = ['enterprise_type', 'province', 'is_active', 'is_verified']
    search_fields = ['name', 'credit_code']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [EnterpriseQualificationInline, EnterpriseContactInline, EnterpriseKeyPersonnelInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'enterprise_type', 'credit_code', 
                      'legal_person', 'registered_capital', 
                      'establishment_date')
        }),
        ('联系信息', {
            'fields': ('province', 'city', 'district', 'address', 'contact_person', 
                      'contact_phone', 'contact_email')
        }),
        ('经营信息', {
            'fields': ('business_scope', 'bank_name', 'bank_account')
        }),
        ('状态与标签', {
            'fields': ('is_active', 'is_verified', 'tags', 'extra_info')
        }),
        ('时间信息', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EnterpriseQualification)
class EnterpriseQualificationAdmin(admin.ModelAdmin):
    """
    企业资质管理
    """
    list_display = ['enterprise', 'qualification_category', 'qualification_name',
                    'grade', 'certificate_no', 'is_valid', 'expiry_date',
                    'is_primary']
    list_filter = ['qualification_category', 'is_valid', 'is_primary', 'enterprise']
    search_fields = ['enterprise__name', 'qualification_name', 'certificate_no']
    date_hierarchy = 'expiry_date'
    raw_id_fields = ['enterprise']


@admin.register(EnterprisePerformance)
class EnterprisePerformanceAdmin(admin.ModelAdmin):
    """
    企业业绩管理
    """
    list_display = ['enterprise', 'project_name', 'performance_type', 'client_name',
                    'contract_amount', 'start_date', 'end_date', 'is_verified']
    list_filter = ['performance_type', 'is_verified', 'enterprise']
    search_fields = ['project_name', 'client_name', 'project_code']
    date_hierarchy = 'start_date'
    raw_id_fields = ['enterprise']


@admin.register(EnterpriseMatchRule)
class EnterpriseMatchRuleAdmin(admin.ModelAdmin):
    """
    企业匹配规则管理
    """
    list_display = ['name', 'enterprise', 'rule_type', 'weight', 'priority', 'is_active']
    list_filter = ['rule_type', 'is_active', 'enterprise']
    search_fields = ['name', 'enterprise__name']
    raw_id_fields = ['enterprise']


@admin.register(EnterpriseMatchResult)
class EnterpriseMatchResultAdmin(admin.ModelAdmin):
    """
    企业匹配结果管理
    """
    list_display = ['enterprise', 'tender_title', 'tender_source', 'match_score',
                    'match_level', 'is_read', 'is_favorite', 'is_applied', 'created_at']
    list_filter = ['match_level', 'is_read', 'is_favorite', 'is_applied', 'enterprise']
    search_fields = ['tender_title', 'enterprise__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['enterprise']


@admin.register(EnterpriseContact)
class EnterpriseContactAdmin(admin.ModelAdmin):
    """
    企业联系人管理
    """
    list_display = ['enterprise', 'name', 'contact_type', 'position', 'phone', 
                    'mobile', 'is_primary', 'is_active']
    list_filter = ['contact_type', 'is_primary', 'is_active', 'enterprise']
    search_fields = ['enterprise__name', 'name', 'phone', 'mobile']
    raw_id_fields = ['enterprise']


@admin.register(EnterpriseBidConfig)
class EnterpriseBidConfigAdmin(admin.ModelAdmin):
    """
    企业投标配置管理
    """
    list_display = ['enterprise', 'builder_level', 'accept_consortium', 
                    'need_safety_license', 'performance_years', 'created_at']
    list_filter = ['builder_level', 'accept_consortium', 'need_safety_license']
    search_fields = ['enterprise__name']
    raw_id_fields = ['enterprise']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('企业信息', {
            'fields': ('enterprise',)
        }),
        ('人员要求', {
            'fields': ('builder_level', 'builder_majors', 'no_ongoing_project',
                      'need_similar_performance', 'similar_performance_desc',
                      'need_safety_certificate_b', 'other_personnel_requirements')
        }),
        ('业绩要求', {
            'fields': ('performance_years', 'min_contract_amount', 'min_building_area',
                      'structure_types', 'other_performance_features')
        }),
        ('财务要求', {
            'fields': ('need_audit_report', 'min_net_assets', 'max_debt_ratio',
                      'min_credit_line', 'min_working_capital')
        }),
        ('信誉要求', {
            'fields': ('no_bad_credit', 'no_bribery_record', 'not_in_blacklist',
                      'other_reputation_requirements')
        }),
        ('其他配置', {
            'fields': ('accept_consortium', 'need_safety_license', 'min_registered_capital',
                      'need_general_taxpayer', 'company_certifications', 
                      'equipment_requirements', 'notes')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EnterpriseKeyPersonnel)
class EnterpriseKeyPersonnelAdmin(admin.ModelAdmin):
    """
    企业关键人员管理
    """
    list_display = ['enterprise', 'personnel_type', 'name', 'personnel_id',
                    'certificate_number', 'certificate_major', 'expiry_date', 
                    'certificate_status', 'is_available']
    list_filter = ['personnel_type', 'certificate_status', 'is_available', 'enterprise']
    search_fields = ['enterprise__name', 'name', 'certificate_number', 'personnel_id', 'id_number']
    date_hierarchy = 'expiry_date'
    raw_id_fields = ['enterprise']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('enterprise', 'personnel_type', 'officer_type', 'personnel_id', 
                      'name', 'id_number', 'birth_date')
        }),
        ('证书信息', {
            'fields': ('builder_certificate', 'safety_certificate_b', 'engineer_title_certificate',
                      'certificate_number', 'certificate_major', 'expiry_date', 
                      'issuing_authority', 'issuing_authority_full', 'title_level')
        }),
        ('证明文件', {
            'fields': ('social_security_proof', 'no_ongoing_commitment', 
                      'labor_contract', 'similar_performance_proof')
        }),
        ('其他信息', {
            'fields': ('is_registered_locally', 'social_security_code', 'professional_years',
                      'phone', 'email')
        }),
        ('状态', {
            'fields': ('certificate_status', 'is_available', 'remarks')
        }),
    )
