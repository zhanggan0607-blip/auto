"""
企业资质匹配服务

业务逻辑说明：
1. 企业信息 = 用户企业拥有的资质类型
2. 招标公告 = 项目的要求
3. 匹配逻辑 = 用企业资质类型对比招标公告要求
4. 结果处理：
   - 符合资质要求 → 进入投标报名（status='processing'）
   - 不符合资质要求 → 自动删除（如果开启自动删除）

匹配规则：
- 资质类型：企业拥有的资质类型必须包含项目要求的资质类型
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from django.db import transaction

from apps.tenders.models import TenderProject
from apps.enterprise.models import Enterprise, EnterpriseQualification

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
    只比对资质类型
    """

    QUALIFICATION_KEYWORDS = {
        'building_construction': ['建筑工程', '房屋建筑', '建筑施工', '住宅', '商业建筑', '办公楼', '施工总承包', '建筑装修'],
        'municipal_engineering': ['市政工程', '市政公用', '道路工程', '桥梁工程', '给排水', '污水处理', '市政施工'],
        'mechanical_electrical': ['机电工程', '机电安装', '电气工程', '暖通空调', '消防工程', '机电设备', '设备安装'],
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

    CATEGORY_TO_MATCH_KEYS = {
        'construction': [
            'building_construction', 'municipal_engineering', 'mechanical_electrical',
            'steel_structure', 'foundation', 'decoration', 'curtain_wall',
            'fire_protection', 'waterproof_anticorrosion', 'environmental',
            'lighting', 'special'
        ],
        'design': ['building_construction', 'municipal_engineering', 'environmental'],
        'survey': ['foundation', 'environmental'],
        'supervision': ['building_construction', 'municipal_engineering'],
    }

    def __init__(self, enterprise: Enterprise = None):
        self.enterprise = enterprise
        self.qualification_types = self._get_enterprise_qualifications()

    def _get_enterprise_qualifications(self) -> List[str]:
        """
        获取企业资质类型列表
        """
        if not self.enterprise:
            return []

        qualifications = EnterpriseQualification.objects.filter(
            enterprise=self.enterprise,
            is_valid=True
        )

        qual_types = set()
        for qual in qualifications:
            if qual.qualification_category:
                qual_types.add(qual.qualification_category)

        return list(qual_types)

    def match_tender(
        self,
        tender: TenderProject,
        threshold: float = 0.6
    ) -> QualificationMatchResult:
        """
        匹配单个招标项目

        Args:
            tender: 招标项目
            threshold: 匹配阈值（保留参数兼容性）

        Returns:
            QualificationMatchResult: 匹配结果
        """
        full_text = f"{tender.title} {tender.description or ''}"

        qual_score, qual_reasons = self._check_qualification_match(full_text)

        is_matched = qual_score >= threshold and len(qual_reasons) == 0

        return QualificationMatchResult(
            tender_id=tender.id,
            tender_title=tender.title,
            is_matched=is_matched,
            match_score=qual_score,
            match_details={'qualification_match': {'score': qual_score, 'reasons': qual_reasons}},
            reject_reasons=qual_reasons
        )

    def _check_qualification_match(self, text: str) -> Tuple[float, List[str]]:
        """
        检查资质类型匹配
        """
        reasons = []
        score = 1.0

        if not self.qualification_types:
            reasons.append('企业未配置资质类型')
            return 0.0, reasons

        enterprise_match_keys = set()
        for cat in self.qualification_types:
            mapped_keys = self.CATEGORY_TO_MATCH_KEYS.get(cat, [])
            enterprise_match_keys.update(mapped_keys)

        if not enterprise_match_keys:
            enterprise_match_keys = set(self.qualification_types)

        required_qual_types = set()
        for qual_type, keywords in self.QUALIFICATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    required_qual_types.add(qual_type)
                    break

        if not required_qual_types:
            return 1.0, reasons

        matched = required_qual_types & enterprise_match_keys
        if not matched:
            reasons.append(f'项目要求资质类型({", ".join(required_qual_types)})与企业资质不匹配')
            score = 0.0
        else:
            match_ratio = len(matched) / len(required_qual_types)
            score = match_ratio

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
    只比对资质类型
    """

    def __init__(self, enterprise: Enterprise = None):
        self.qualification_matcher = QualificationMatcher(enterprise)

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
                self.qualification_matcher = QualificationMatcher(enterprise)

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