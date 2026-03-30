"""
智能企业资质匹配服务

业务逻辑说明：
1. 企业信息 = 用户自己企业能够满足的条件（资质、建造师、业绩能力等）
2. 招标公告 = 项目的要求
3. 匹配逻辑 = 用企业条件对比招标公告要求
4. 结果处理：
   - 满足企业条件 → 进入投标报名（status='processing'）
   - 不满足企业条件 → 自动删除（如果开启自动删除）

匹配规则：
- 资质类型：企业拥有的资质类型必须包含项目要求的资质类型
- 资质等级：企业拥有的资质等级必须满足项目要求的等级
- 建造师：企业拥有的建造师等级和专业必须满足项目要求
- 联合体：企业是否接受联合体投标
- 预算：项目预算必须满足企业可承担的最低合同金额
- 结构类型：企业可施工的结构类型必须包含项目要求的结构类型
"""
import logging
import re
import warnings
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from django.db import transaction

from apps.tenders.models import TenderProject
from apps.enterprise.models import Enterprise, EnterpriseBidConfig, EnterpriseQualification

logger = logging.getLogger(__name__)


@dataclass
class QualificationMatchResult:
    """
    资质匹配结果
    """
    tender_id: int
    tender_title: str
    is_matched: bool = False
    match_score: float = 0.0
    match_details: Dict = field(default_factory=dict)
    reject_reasons: List = field(default_factory=list)


class QualificationMatcher:
    """
    企业资质匹配器
    支持使用Enterprise和EnterpriseBidConfig进行匹配
    """
    
    QUALIFICATION_KEYWORDS = {
        'building_construction': ['建筑工程', '房屋建筑', '建筑施工', '住宅', '商业建筑', '办公楼'],
        'municipal_engineering': ['市政工程', '市政公用', '道路工程', '桥梁工程', '给排水', '污水处理'],
        'mechanical_electrical': ['机电工程', '机电安装', '电气工程', '暖通空调', '消防工程'],
        'steel_structure': ['钢结构', '金属结构', '网架结构'],
        'foundation': ['地基基础', '基坑支护', '桩基工程', '土方工程'],
        'decoration': ['装修装饰', '室内装修', '幕墙工程', '装饰工程'],
        'curtain_wall': ['幕墙', '玻璃幕墙', '石材幕墙', '金属幕墙'],
        'fire_protection': ['消防设施', '消防工程', '消防系统'],
        'waterproof_anticorrosion': ['防水', '防腐', '保温工程', '屋面防水'],
        'environmental': ['环保工程', '环境工程', '污染治理', '废气处理', '废水处理'],
        'lighting': ['照明工程', '路灯', '景观照明', '城市照明'],
        'special': ['特种工程', '结构补强', '纠偏平移'],
    }

    STRUCTURE_KEYWORDS = {
        'frame': ['框架结构', '框架'],
        'shear_wall': ['剪力墙', '剪力墙结构'],
        'frame_shear': ['框架剪力墙', '框剪结构', '框架-剪力墙'],
        'steel': ['钢结构', '钢框架'],
        'tube': ['筒体结构', '筒中筒'],
        'brick_concrete': ['砖混结构', '砌体结构'],
        'wood': ['木结构'],
        'other': ['其他结构'],
    }

    def __init__(self, enterprise: Enterprise = None, bid_config: EnterpriseBidConfig = None):
        """
        初始化匹配器
        
        Args:
            enterprise: 企业信息模型
            bid_config: 企业投标配置模型
        """
        self.enterprise = enterprise
        self.bid_config = bid_config
        self.rules = self._build_rules()

    def _build_rules(self) -> Dict[str, Any]:
        """
        构建匹配规则
        """
        rules = {
            'qualification_types': [],
            'qualification_levels': [],
            'builder_level': None,
            'builder_majors': [],
            'accept_consortium': True,
            'min_contract_amount': None,
            'structure_types': [],
            'performance_years': None,
            'need_safety_license': True,
            'need_safety_certificate_b': True,
        }
        
        if self.enterprise:
            qualifications = EnterpriseQualification.objects.filter(
                enterprise=self.enterprise,
                is_valid=True
            )
            
            qual_types = set()
            qual_levels = set()
            for qual in qualifications:
                if qual.qualification_category:
                    qual_types.add(qual.qualification_category)
                if qual.grade:
                    qual_levels.add(qual.grade)
            
            rules['qualification_types'] = list(qual_types)
            rules['qualification_levels'] = list(qual_levels)
        
        if self.bid_config:
            rules['builder_level'] = self.bid_config.builder_level
            rules['builder_majors'] = self.bid_config.builder_majors or []
            rules['accept_consortium'] = self.bid_config.accept_consortium
            rules['min_contract_amount'] = self.bid_config.min_contract_amount
            rules['structure_types'] = self.bid_config.structure_types or []
            rules['performance_years'] = self.bid_config.performance_years
            rules['need_safety_license'] = self.bid_config.need_safety_license
            rules['need_safety_certificate_b'] = self.bid_config.need_safety_certificate_b
        
        return rules

    def match_tender(
        self,
        tender: TenderProject,
        threshold: float = 0.6
    ) -> QualificationMatchResult:
        """
        匹配单个招标项目
        
        Args:
            tender: 招标项目
            threshold: 匹配阈值
            
        Returns:
            QualificationMatchResult: 匹配结果
        """
        full_text = f"{tender.title} {tender.description or ''}"
        
        scores = []
        reject_reasons = []
        match_details = {}
        
        qual_score, qual_reasons = self._check_qualification_match(full_text)
        if qual_reasons:
            reject_reasons.extend(qual_reasons)
        scores.append(qual_score)
        match_details['qualification_match'] = {
            'score': qual_score,
            'reasons': qual_reasons
        }
        
        builder_score, builder_reasons = self._check_builder_requirement(full_text)
        if builder_reasons:
            reject_reasons.extend(builder_reasons)
        scores.append(builder_score)
        match_details['builder_match'] = {
            'score': builder_score,
            'reasons': builder_reasons
        }

        consortium_score, consortium_reasons = self._check_consortium_requirement(full_text)
        if consortium_reasons:
            reject_reasons.extend(consortium_reasons)
        scores.append(consortium_score)
        match_details['consortium_match'] = {
            'score': consortium_score,
            'reasons': consortium_reasons
        }

        budget_score, budget_reasons = self._check_budget_requirement(tender.budget)
        if budget_reasons:
            reject_reasons.extend(budget_reasons)
        scores.append(budget_score)
        match_details['budget_match'] = {
            'score': budget_score,
            'reasons': budget_reasons
        }

        structure_score, structure_reasons = self._check_structure_requirement(full_text)
        if structure_reasons:
            reject_reasons.extend(structure_reasons)
        scores.append(structure_score)
        match_details['structure_match'] = {
            'score': structure_score,
            'reasons': structure_reasons
        }

        final_score = sum(scores) / len(scores) if scores else 0.5
        is_matched = final_score >= threshold and len(reject_reasons) == 0

        return QualificationMatchResult(
            tender_id=tender.id,
            tender_title=tender.title,
            is_matched=is_matched,
            match_score=final_score,
            match_details=match_details,
            reject_reasons=reject_reasons
        )

    def _check_qualification_match(self, text: str) -> Tuple[float, List[str]]:
        """
        检查资质匹配
        """
        reasons = []
        score = 1.0

        enterprise_qual_types = self.rules.get('qualification_types', [])
        if not enterprise_qual_types:
            return score, reasons

        required_qual_types = set()
        for qual_type, keywords in self.QUALIFICATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    required_qual_types.add(qual_type)
                    break

        if required_qual_types:
            matched = required_qual_types & set(enterprise_qual_types)
            if not matched:
                reasons.append(f'项目要求资质类型({", ".join(required_qual_types)})与企业资质不匹配')
                score = 0.0
            else:
                match_ratio = len(matched) / len(required_qual_types)
                score = match_ratio

        return score, reasons

    def _check_builder_requirement(self, text: str) -> Tuple[float, List[str]]:
        """
        检查建造师要求
        """
        reasons = []
        score = 1.0

        enterprise_builder_level = self.rules.get('builder_level')
        enterprise_builder_majors = self.rules.get('builder_majors', [])

        if not enterprise_builder_level or enterprise_builder_level == 'none':
            return score, reasons

        level_patterns = {
            'first': [r'一级注册建造师', r'一级建造师', r'一级项目经理'],
            'second': [r'二级注册建造师', r'二级建造师', r'二级项目经理'],
        }

        required_level = None
        for level, patterns in level_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    required_level = level
                    break
            if required_level:
                break

        if required_level:
            level_order = {'first': 1, 'second': 2}
            if level_order.get(enterprise_builder_level, 99) > level_order.get(required_level, 99):
                reasons.append(f'项目要求{required_level}建造师，企业仅有{enterprise_builder_level}建造师')
                score = 0.3

        major_keywords = {
            'architecture': ['建筑工程', '房屋建筑', '建筑'],
            'municipal': ['市政工程', '市政公用', '市政'],
            'mechanical_electrical': ['机电工程', '机电'],
            'highway': ['公路工程', '公路'],
            'water_conservancy': ['水利水电', '水利'],
        }

        required_majors = set()
        for major, keywords in major_keywords.items():
            for keyword in keywords:
                if keyword in text and '建造师' in text:
                    required_majors.add(major)
                    break

        if required_majors and enterprise_builder_majors:
            matched = required_majors & set(enterprise_builder_majors)
            if not matched:
                reasons.append(f'项目要求建造师专业({", ".join(required_majors)})与企业不匹配')
                score *= 0.5

        return score, reasons

    def _check_consortium_requirement(self, text: str) -> Tuple[float, List[str]]:
        """
        检查联合体投标要求
        """
        reasons = []
        score = 1.0

        accept_consortium = self.rules.get('accept_consortium', True)

        consortium_patterns = [
            r'不接受联合体投标',
            r'不接受联合体',
            r'联合体投标.*不接受',
        ]

        requires_consortium = False
        for pattern in consortium_patterns:
            if re.search(pattern, text):
                requires_consortium = True
                break

        if not accept_consortium and not requires_consortium:
            patterns_allow = [
                r'接受联合体投标',
                r'接受联合体',
                r'联合体投标.*接受',
            ]
            for pattern in patterns_allow:
                if re.search(pattern, text):
                    reasons.append('项目接受联合体投标，但企业不接受联合体')
                    score = 0.5
                    break

        return score, reasons

    def _check_budget_requirement(self, budget) -> Tuple[float, List[str]]:
        """
        检查预算金额要求
        """
        reasons = []
        score = 1.0

        if not budget:
            return score, reasons

        min_contract_amount = self.rules.get('min_contract_amount')
        if not min_contract_amount:
            return score, reasons

        if budget < min_contract_amount:
            reasons.append(f'项目预算({budget}万元)低于企业最低合同金额要求({min_contract_amount}万元)')
            score = 0.3

        return score, reasons

    def _check_structure_requirement(self, text: str) -> Tuple[float, List[str]]:
        """
        检查结构类型要求
        """
        reasons = []
        score = 1.0

        enterprise_structure_types = self.rules.get('structure_types', [])
        if not enterprise_structure_types:
            return score, reasons

        required_structure_types = set()
        for struct_type, keywords in self.STRUCTURE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    required_structure_types.add(struct_type)
                    break

        if required_structure_types:
            matched = required_structure_types & set(enterprise_structure_types)
            if not matched:
                reasons.append(f'项目要求结构类型({", ".join(required_structure_types)})与企业能力不匹配')
                score = 0.3

        return score, reasons

    def match_tenders_batch(
        self,
        tenders: List[TenderProject],
        threshold: float = 0.6
    ) -> List[QualificationMatchResult]:
        """
        批量匹配招标项目

        Args:
            tenders: 招标项目列表
            threshold: 匹配阈值

        Returns:
            list: 匹配结果列表
        """
        results = []
        for tender in tenders:
            result = self.match_tender(tender, threshold)
            results.append(result)
        return results


class TenderQualificationMatcher:
    """
    招标项目资质匹配服务
    整合语义匹配和规则匹配
    """

    def __init__(self, enterprise: Enterprise = None, bid_config: EnterpriseBidConfig = None):
        self.qualification_matcher = QualificationMatcher(enterprise, bid_config)

    def process_new_tenders(
        self,
        user_id: int = None,
        auto_delete: bool = False,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        处理新采集的招标项目

        Args:
            user_id: 用户ID，用于获取对应的企业信息
            auto_delete: 是否自动删除不匹配的项目
            threshold: 匹配阈值

        Returns:
            dict: 处理结果统计
        """
        if user_id:
            enterprise = Enterprise.objects.filter(
                created_by_id=user_id,
                is_active=True
            ).first()
            if enterprise:
                bid_config = EnterpriseBidConfig.objects.filter(
                    enterprise=enterprise
                ).first()
                self.qualification_matcher = QualificationMatcher(enterprise, bid_config)

        pending_tenders = TenderProject.objects.filter(status='pending')

        total_count = pending_tenders.count()
        if total_count == 0:
            return {
                'total': 0,
                'matched': 0,
                'unmatched': 0,
                'deleted': 0,
                'results': []
            }

        tenders = list(pending_tenders[:100])

        results = self.qualification_matcher.match_tenders_batch(tenders, threshold)

        matched_count = sum(1 for r in results if r.is_matched)
        unmatched_count = total_count - matched_count

        deleted_count = 0
        if auto_delete:
            unmatched_tenders = [t for t, r in zip(tenders, results) if not r.is_matched]
            if unmatched_tenders:
                tender_ids = [t.id for t in unmatched_tenders]
                with transaction.atomic():
                    deleted_count = TenderProject.objects.filter(id__in=tender_ids).delete()[0]

        for tender, result in zip(tenders, results):
            if result.is_matched:
                tender.status = 'processing'
                tender.keywords_matched = result.match_details
                tender.save(update_fields=['status', 'keywords_matched'])

        return {
            'total': total_count,
            'matched': matched_count,
            'unmatched': unmatched_count,
            'deleted': deleted_count,
            'results': [
                {
                    'tender_id': r.tender_id,
                    'tender_title': r.tender_title,
                    'is_matched': r.is_matched,
                    'match_score': r.match_score,
                    'reject_reasons': r.reject_reasons
                }
                for r in results[:20]
            ]
        }


tender_qualification_matcher = TenderQualificationMatcher()
