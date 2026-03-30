"""
导入测试企业数据脚本
将天眼查收集的企业信息导入系统
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from decimal import Decimal
from datetime import date
from apps.enterprise.models import (
    Enterprise,
    EnterpriseQualification,
    EnterprisePerformance,
    EnterpriseContact,
    EnterpriseBidConfig,
    EnterpriseDocument
)


def import_tianqi_enterprise():
    """
    导入上海天齐智能建筑股份有限公司测试数据
    """
    enterprise_data = {
        'name': '上海天齐智能建筑股份有限公司',
        'short_name': '天齐智能建筑',
        'enterprise_type': 'supplier',
        'credit_code': '913100007411910789',
        'registration_number': None,
        'legal_person': '李莉',
        'registered_capital': Decimal('5050.00'),
        'establishment_date': date(2002, 7, 19),
        'province': '上海市',
        'city': '上海市',
        'district': '普陀区',
        'address': '上海市普陀区武威路88弄21号4层08室',
        'contact_person': '张干',
        'contact_phone': '021-3366****',
        'contact_email': '22583405@qq.com',
        'website': 'https://www.sstcp.com',
        'fax': None,
        'business_scope': '''许可项目：建设工程施工；建设工程设计
（依法须经批准的项目，经相关部门批准后方可开展经营活动，具体经营项目以相关部门批准文件或许可证件为准）
一般项目：建筑工程的设计、施工、咨询，市政工程，园林工程的设计与施工，从事货物及技术的进出口业务，计算机软件的开发与销售，技术服务、技术开发、技术咨询、技术交流、技术转让、技术推广，智能化系统集成''',
        'industry': '建筑装饰、装修和其他建筑业',
        'bank_name': None,
        'bank_account': None,
        'is_active': True,
        'is_verified': True,
        'auto_bid_enabled': False,
        'auto_bid_threshold': 60,
        'auto_upload_enabled': False,
        'auto_bid_keywords': ['智能建筑', '建设工程', '智能化', '安防'],
        'notification_channels': ['dingtalk', 'email'],
        'tags': ['高新技术企业', '专精特新', '智能建筑', '安防工程'],
        'extra_info': {
            'actual_controller': '张干',
            'actual_controller_share': '93.76%',
            'paid_capital': '1050万人民币',
            'social_security_count': 122,
            'branch_count': 5,
            'investment_count': 2,
            'patent_count': 30,
            'tender_count': 640,
            'judicial_cases': 19,
            'tax_credit_level': 'A级',
            'high_tech_enterprise': True,
            'specialized_new': True,
            'data_source': '天眼查',
            'data_update_date': '2026-03-20'
        }
    }
    
    enterprise, created = Enterprise.objects.update_or_create(
        credit_code=enterprise_data['credit_code'],
        defaults=enterprise_data
    )
    
    if created:
        print(f"✅ 创建企业: {enterprise.name}")
    else:
        print(f"✅ 更新企业: {enterprise.name}")
    
    qualifications_data = [
        {
            'qualification_type': 'construction',
            'qualification_name': '建筑工程施工总承包',
            'certificate_number': None,
            'grade': '二级',
            'scope': '建筑工程施工',
            'issue_date': None,
            'expiry_date': None,
            'issuing_authority': '住房和城乡建设部',
            'is_valid': True,
            'is_primary': True,
            'remarks': '建筑业企业资质'
        },
        {
            'qualification_type': 'design',
            'qualification_name': '建筑工程设计资质',
            'certificate_number': None,
            'grade': '乙级',
            'scope': '建筑工程设计',
            'issue_date': None,
            'expiry_date': None,
            'issuing_authority': '住房和城乡建设部',
            'is_valid': True,
            'is_primary': False,
            'remarks': '设计资质'
        },
        {
            'qualification_type': 'professional',
            'qualification_name': '音视频工程业企业资质',
            'certificate_number': None,
            'grade': '一级',
            'scope': '音视频工程设计与施工',
            'issue_date': None,
            'expiry_date': None,
            'issuing_authority': '中国电子学会',
            'is_valid': True,
            'is_primary': False,
            'remarks': '音视频工程专业资质'
        },
        {
            'qualification_type': 'professional',
            'qualification_name': '系统集成资质',
            'certificate_number': None,
            'grade': '三级',
            'scope': '计算机信息系统集成',
            'issue_date': None,
            'expiry_date': None,
            'issuing_authority': '中国电子信息行业联合会',
            'is_valid': True,
            'is_primary': False,
            'remarks': '系统集成资质'
        },
        {
            'qualification_type': 'safety',
            'qualification_name': '安防工程企业资质',
            'certificate_number': None,
            'grade': '一级',
            'scope': '安防工程设计施工',
            'issue_date': None,
            'expiry_date': None,
            'issuing_authority': '中国安全防范产品行业协会',
            'is_valid': True,
            'is_primary': False,
            'remarks': '安防工程专业资质'
        },
        {
            'qualification_type': 'safety',
            'qualification_name': '安全生产许可证',
            'certificate_number': None,
            'grade': None,
            'scope': '建筑施工安全生产',
            'issue_date': None,
            'expiry_date': None,
            'issuing_authority': '住房和城乡建设部',
            'is_valid': True,
            'is_primary': False,
            'remarks': '安全生产许可证'
        },
    ]
    
    for qual_data in qualifications_data:
        qual, qual_created = EnterpriseQualification.objects.update_or_create(
            enterprise=enterprise,
            qualification_name=qual_data['qualification_name'],
            defaults=qual_data
        )
        if qual_created:
            print(f"  ✅ 创建资质: {qual.qualification_name}")
        else:
            print(f"  ✅ 更新资质: {qual.qualification_name}")
    
    performances_data = [
        {
            'project_name': '区政府总机配套服务项目',
            'project_code': None,
            'performance_type': 'project',
            'client_name': '上海市普陀区人民政府机关事务管理局',
            'client_contact': None,
            'client_phone': None,
            'contract_amount': Decimal('293.00'),
            'settlement_amount': None,
            'start_date': None,
            'end_date': date(2025, 12, 30),
            'completion_date': None,
            'project_location': '上海市普陀区',
            'project_scale': '信息通信配套服务',
            'project_manager': None,
            'technical_director': None,
            'description': '区政府总机配套服务项目',
            'is_verified': True
        },
        {
            'project_name': '2024年优化生活垃圾全程分类体系项目(半淞园路街道)',
            'project_code': '310101000241128152047-01176803',
            'performance_type': 'project',
            'client_name': '上海市黄浦区半淞园路街道办事处',
            'client_contact': None,
            'client_phone': None,
            'contract_amount': Decimal('258.99'),
            'settlement_amount': None,
            'start_date': None,
            'end_date': date(2024, 12, 31),
            'completion_date': None,
            'project_location': '上海市黄浦区',
            'project_scale': '垃圾分类设施更新',
            'project_manager': None,
            'technical_director': None,
            'description': '优化生活垃圾投放点专项更新',
            'is_verified': True
        },
        {
            'project_name': '普陀区消防救援支队支队部会议室改造项目',
            'project_code': None,
            'performance_type': 'project',
            'client_name': '普陀区消防救援支队',
            'client_contact': None,
            'client_phone': None,
            'contract_amount': Decimal('32.89'),
            'settlement_amount': None,
            'start_date': None,
            'end_date': date(2025, 4, 9),
            'completion_date': None,
            'project_location': '上海市普陀区',
            'project_scale': '会议室改造',
            'project_manager': None,
            'technical_director': None,
            'description': '支队部会议室改造项目',
            'is_verified': True
        },
        {
            'project_name': '郑州大剧院',
            'project_code': None,
            'performance_type': 'project',
            'client_name': '郑州市文化广电和旅游局',
            'client_contact': None,
            'client_phone': None,
            'contract_amount': None,
            'settlement_amount': None,
            'start_date': None,
            'end_date': None,
            'completion_date': None,
            'project_location': '河南省郑州市',
            'project_scale': '大型公共建筑',
            'project_manager': None,
            'technical_director': None,
            'description': '郑州大剧院智能化系统设计与施工',
            'is_verified': True
        },
        {
            'project_name': '江苏阿里巴巴云计算中心',
            'project_code': None,
            'performance_type': 'project',
            'client_name': '阿里巴巴集团',
            'client_contact': None,
            'client_phone': None,
            'contract_amount': None,
            'settlement_amount': None,
            'start_date': None,
            'end_date': None,
            'completion_date': None,
            'project_location': '江苏省',
            'project_scale': '数据中心',
            'project_manager': None,
            'technical_director': None,
            'description': '江苏阿里巴巴云计算中心智能化项目',
            'is_verified': True
        },
    ]
    
    for perf_data in performances_data:
        perf, perf_created = EnterprisePerformance.objects.update_or_create(
            enterprise=enterprise,
            project_name=perf_data['project_name'],
            defaults=perf_data
        )
        if perf_created:
            print(f"  ✅ 创建业绩: {perf.project_name}")
        else:
            print(f"  ✅ 更新业绩: {perf.project_name}")
    
    contacts_data = [
        {
            'contact_type': 'business',
            'name': '张干',
            'position': '董事兼总经理',
            'department': '管理层',
            'phone': '021-3366****',
            'mobile': None,
            'email': None,
            'wechat': None,
            'is_primary': True,
            'is_active': True,
            'remarks': '疑似实际控制人，持股93.76%'
        },
        {
            'contact_type': 'business',
            'name': '李莉',
            'position': '董事长',
            'department': '管理层',
            'phone': None,
            'mobile': None,
            'email': None,
            'wechat': None,
            'is_primary': False,
            'is_active': True,
            'remarks': '法定代表人，持股6.24%'
        },
    ]
    
    for contact_data in contacts_data:
        contact, contact_created = EnterpriseContact.objects.update_or_create(
            enterprise=enterprise,
            name=contact_data['name'],
            defaults=contact_data
        )
        if contact_created:
            print(f"  ✅ 创建联系人: {contact.name}")
        else:
            print(f"  ✅ 更新联系人: {contact.name}")
    
    bid_config_data = {
        'accept_consortium': True,
        'builder_level': 'first',
        'builder_majors': ['建筑工程', '机电工程'],
        'no_ongoing_project': False,
        'need_similar_performance': True,
        'similar_performance_desc': '近三年内类似规模智能建筑项目业绩',
        'need_safety_certificate_b': True,
        'other_personnel_requirements': '技术负责人具有中级及以上职称',
        'need_safety_license': True,
        'performance_years': 3,
        'min_contract_amount': Decimal('100.00'),
        'min_building_area': None,
        'structure_types': ['框架结构', '钢结构'],
        'other_performance_features': '具有智能化系统集成经验',
        'need_audit_report': True,
        'min_net_assets': Decimal('1000.00'),
        'max_debt_ratio': Decimal('70.00'),
        'min_credit_line': None,
        'min_working_capital': Decimal('500.00'),
        'no_bad_credit': True,
        'no_bribery_record': True,
        'not_in_blacklist': True,
        'other_reputation_requirements': '无重大质量安全事故',
        'min_registered_capital': Decimal('1000.00'),
        'need_general_taxpayer': True,
        'company_certifications': ['ISO9001质量管理体系认证', 'ISO14001环境管理体系认证', 'OHSAS18001职业健康安全管理体系认证'],
        'equipment_requirements': None,
        'notes': '高新技术企业，专精特新企业，智能建筑领域专业公司'
    }
    
    bid_config, bid_created = EnterpriseBidConfig.objects.update_or_create(
        enterprise=enterprise,
        defaults=bid_config_data
    )
    
    if bid_created:
        print(f"  ✅ 创建投标配置")
    else:
        print(f"  ✅ 更新投标配置")
    
    documents_data = [
        {
            'document_type': 'patent',
            'document_name': '一种基于机器视觉的安防监控系统及方法',
            'document_no': 'CN11809755',
            'issue_date': date(2024, 8, 20),
            'expiry_date': None,
            'issuing_authority': '国家知识产权局',
            'description': '发明专利，显著提高检测的准确性和效率',
            'tags': ['发明专利', '安防监控', '机器视觉'],
            'is_primary': True,
            'is_verified': True,
            'is_ai_reference': True,
            'is_bid_material': True
        },
        {
            'document_type': 'patent',
            'document_name': '一种基于多模态大模型的数字人交互方法及系统',
            'document_no': 'CN1197615',
            'issue_date': date(2025, 4, 7),
            'expiry_date': None,
            'issuing_authority': '国家知识产权局',
            'description': '发明专利，多模态大模型数字人交互技术',
            'tags': ['发明专利', '数字人', '多模态'],
            'is_primary': False,
            'is_verified': True,
            'is_ai_reference': True,
            'is_bid_material': True
        },
        {
            'document_type': 'patent',
            'document_name': '一种安全生产降尘器',
            'document_no': 'CN223056346U',
            'issue_date': date(2025, 7, 5),
            'expiry_date': None,
            'issuing_authority': '国家知识产权局',
            'description': '实用新型专利，形成大范围的吸尘降尘效果',
            'tags': ['实用新型', '安全生产', '环保设备'],
            'is_primary': False,
            'is_verified': True,
            'is_ai_reference': True,
            'is_bid_material': True
        },
        {
            'document_type': 'patent',
            'document_name': '一种道路坑洼检测方法及系统',
            'document_no': 'CN120219384B',
            'issue_date': date(2025, 8, 5),
            'expiry_date': None,
            'issuing_authority': '国家知识产权局',
            'description': '发明专利，道路坑洼智能检测技术',
            'tags': ['发明专利', '道路检测', '智能交通'],
            'is_primary': False,
            'is_verified': True,
            'is_ai_reference': True,
            'is_bid_material': True
        },
        {
            'document_type': 'honor',
            'document_name': '国家级高新技术企业证书',
            'document_no': None,
            'issue_date': date(2025, 1, 1),
            'expiry_date': date(2027, 12, 31),
            'issuing_authority': '科技部',
            'description': '国家级高新技术企业认定',
            'tags': ['高新技术企业', '国家级'],
            'is_primary': True,
            'is_verified': True,
            'is_ai_reference': True,
            'is_bid_material': True
        },
        {
            'document_type': 'honor',
            'document_name': '省级专精特新中小企业证书',
            'document_no': None,
            'issue_date': date(2025, 1, 1),
            'expiry_date': None,
            'issuing_authority': '上海市经济和信息化委员会',
            'description': '省级专精特新中小企业认定',
            'tags': ['专精特新', '省级'],
            'is_primary': False,
            'is_verified': True,
            'is_ai_reference': True,
            'is_bid_material': True
        },
    ]
    
    for doc_data in documents_data:
        doc, doc_created = EnterpriseDocument.objects.update_or_create(
            enterprise=enterprise,
            document_name=doc_data['document_name'],
            defaults=doc_data
        )
        if doc_created:
            print(f"  ✅ 创建证书: {doc.document_name}")
        else:
            print(f"  ✅ 更新证书: {doc.document_name}")
    
    print(f"\n{'='*50}")
    print(f"企业数据导入完成!")
    print(f"企业ID: {enterprise.id}")
    print(f"企业名称: {enterprise.name}")
    print(f"资质数量: {enterprise.qualifications.count()}")
    print(f"业绩数量: {enterprise.performances.count()}")
    print(f"联系人数量: {enterprise.contacts.count()}")
    print(f"证书数量: {enterprise.documents.count()}")
    print(f"{'='*50}")
    
    return enterprise


if __name__ == '__main__':
    import_tianqi_enterprise()
