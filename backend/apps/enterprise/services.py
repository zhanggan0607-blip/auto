"""
SAAS企业资料库模块 - 企业匹配服务
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from difflib import SequenceMatcher

from django.db import models

from .models import (
    Enterprise, EnterpriseQualification, EnterprisePerformance,
    EnterpriseMatchRule, EnterpriseMatchResult
)
from services.vector import enterprise_vector_store

logger = logging.getLogger(__name__)


class EnterpriseMatcher:
    """
    企业匹配器 - 将招标信息与企业信息进行智能匹配
    支持规则匹配和语义匹配两种模式
    """
    
    def __init__(self, use_semantic: bool = True):
        """
        初始化企业匹配器
        
        Args:
            use_semantic: 是否启用语义匹配
        """
        self.similarity_threshold = 0.6
        self.use_semantic = use_semantic
        self._semantic_matcher = None
    
    @property
    def semantic_matcher(self):
        """
        延迟初始化语义匹配器
        """
        if self._semantic_matcher is None and self.use_semantic:
            self._semantic_matcher = SemanticMatcher()
        return self._semantic_matcher
    
    def match_enterprise(self, enterprise: Enterprise, tender_data: Dict) -> Optional[EnterpriseMatchResult]:
        """
        匹配单个企业与招标信息
        
        Args:
            enterprise: 企业对象
            tender_data: 招标数据
            
        Returns:
            EnterpriseMatchResult: 匹配结果
        """
        rules = EnterpriseMatchRule.objects.filter(
            enterprise=enterprise,
            is_active=True
        ).order_by('-priority', '-weight')
        
        if not rules.exists():
            return None
        
        total_score = 0
        matched_keywords = []
        matched_industries = []
        matched_regions = []
        matched_rules = []
        
        for rule in rules:
            rule_score, rule_matches = self._apply_match_rule(rule, tender_data)
            
            if rule_score > 0:
                total_score += rule_score * rule.weight
                matched_rules.append(rule.name)
                
                if rule_matches.get('keywords'):
                    matched_keywords.extend(rule_matches['keywords'])
                if rule_matches.get('industries'):
                    matched_industries.extend(rule_matches['industries'])
                if rule_matches.get('regions'):
                    matched_regions.extend(rule_matches['regions'])
        
        if total_score <= 0:
            return None
        
        match_level = self._calculate_match_level(total_score)
        
        match_result = EnterpriseMatchResult.objects.create(
            enterprise=enterprise,
            tender_title=tender_data.get('title', ''),
            tender_url=tender_data.get('url', tender_data.get('source_url', '')),
            tender_source=tender_data.get('source', ''),
            publish_date=tender_data.get('publish_date'),
            deadline_date=tender_data.get('deadline_date'),
            matched_keywords=list(set(matched_keywords)),
            matched_industries=list(set(matched_industries)),
            matched_regions=list(set(matched_regions)),
            match_score=total_score,
            match_level=match_level,
            matched_rules=matched_rules,
            tender_data=tender_data
        )
        
        return match_result
    
    def match_tender(self, tender_data: Dict, enterprise_ids: List[int] = None) -> List[EnterpriseMatchResult]:
        """
        将招标信息与所有企业匹配
        结合规则匹配和语义匹配
        
        Args:
            tender_data: 招标数据
            enterprise_ids: 指定企业ID列表（可选）
            
        Returns:
            list: 匹配结果列表
        """
        results = []
        semantic_scores = {}
        
        if self.use_semantic and self.semantic_matcher:
            try:
                semantic_results = self.semantic_matcher.match_tender_semantic(
                    tender_data, 
                    enterprise_ids,
                    threshold=0.5
                )
                for sr in semantic_results:
                    semantic_scores[sr['enterprise_id']] = sr['similarity']
            except Exception as e:
                logger.warning(f"语义匹配失败，使用规则匹配: {str(e)}")
        
        enterprises = Enterprise.objects.filter(is_active=True)
        if enterprise_ids:
            enterprises = enterprises.filter(id__in=enterprise_ids)
        
        for enterprise in enterprises:
            try:
                match_result = self.match_enterprise(enterprise, tender_data)
                if match_result:
                    semantic_boost = semantic_scores.get(enterprise.id, 0)
                    if semantic_boost > 0:
                        match_result.match_score = match_result.match_score * 0.7 + semantic_boost * 100 * 0.3
                        match_result.match_level = self._calculate_match_level(match_result.match_score)
                        match_result.matched_rules.append('semantic_match')
                    results.append(match_result)
            except Exception as e:
                logger.error(f"匹配企业 {enterprise.name} 失败: {str(e)}")
                continue
        
        results.sort(key=lambda x: x.match_score, reverse=True)
        
        return results
    
    def match_tender_semantic_only(self, tender_data: Dict, enterprise_ids: List[int] = None,
                                    threshold: float = 0.6) -> List[Dict]:
        """
        仅使用语义匹配

        Args:
            tender_data: 招标数据
            enterprise_ids: 指定企业ID列表
            threshold: 相似度阈值

        Returns:
            list: 语义匹配结果
        """
        tender_text = self._build_tender_text(tender_data)
        if not tender_text:
            return []

        return enterprise_vector_store.match_tender(
            tender_content=tender_text,
            enterprise_ids=[str(eid) for eid in enterprise_ids] if enterprise_ids else None,
            n_results=10,
            min_similarity=threshold
        )

    def _build_tender_text(self, tender_data: Dict) -> str:
        """
        构建招标信息文本
        """
        parts = []

        if tender_data.get('title'):
            parts.append(tender_data['title'])
        if tender_data.get('description'):
            parts.append(tender_data['description'])
        if tender_data.get('requirements'):
            parts.append(tender_data['requirements'])
        if tender_data.get('industry'):
            parts.append(f"行业: {tender_data['industry']}")

        return ' '.join([p for p in parts if p])
    
    def _apply_match_rule(self, rule: EnterpriseMatchRule, tender_data: Dict) -> tuple:
        """
        应用匹配规则
        
        Args:
            rule: 匹配规则
            tender_data: 招标数据
            
        Returns:
            tuple: (得分, 匹配详情)
        """
        score = 0
        matches = {
            'keywords': [],
            'industries': [],
            'regions': []
        }
        
        if rule.rule_type == 'keyword':
            score, keyword_matches = self._match_keywords(rule.keywords, tender_data)
            matches['keywords'] = keyword_matches
        
        elif rule.rule_type == 'industry':
            score, industry_matches = self._match_industries(rule.industries, tender_data)
            matches['industries'] = industry_matches
        
        elif rule.rule_type == 'region':
            score, region_matches = self._match_regions(rule.regions, tender_data)
            matches['regions'] = region_matches
        
        elif rule.rule_type == 'qualification':
            score = self._match_qualifications(rule.qualification_requirements, tender_data)
        
        elif rule.rule_type == 'performance':
            score = self._match_performance(rule.performance_requirements, tender_data)
        
        elif rule.rule_type == 'budget':
            score = self._match_budget(rule.budget_min, rule.budget_max, tender_data)
        
        return score, matches
    
    def _match_keywords(self, keywords: List[str], tender_data: Dict) -> tuple:
        """
        关键词匹配
        """
        if not keywords:
            return 0, []
        
        title = tender_data.get('title', '').lower()
        description = tender_data.get('description', '').lower()
        text = f"{title} {description}"
        
        matched = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text:
                matched.append(keyword)
        
        if not matched:
            return 0, []
        
        score = len(matched) / len(keywords) * 100
        
        return score, matched
    
    def _match_industries(self, industries: List[str], tender_data: Dict) -> tuple:
        """
        行业匹配
        """
        if not industries:
            return 0, []
        
        tender_industry = tender_data.get('industry', '').lower()
        category = tender_data.get('category', '').lower()
        description = tender_data.get('description', '').lower()
        
        matched = []
        for industry in industries:
            industry_lower = industry.lower()
            if (industry_lower in tender_industry or 
                industry_lower in category or 
                industry_lower in description):
                matched.append(industry)
        
        if not matched:
            return 0, []
        
        score = len(matched) / len(industries) * 100
        
        return score, matched
    
    def _match_regions(self, regions: List[str], tender_data: Dict) -> tuple:
        """
        地区匹配
        """
        if not regions:
            return 0, []
        
        tender_region = tender_data.get('region', '').lower()
        address = tender_data.get('address', '').lower()
        
        matched = []
        for region in regions:
            region_lower = region.lower()
            if region_lower in tender_region or region_lower in address:
                matched.append(region)
        
        if not matched:
            return 0, []
        
        score = len(matched) / len(regions) * 100
        
        return score, matched
    
    def _match_qualifications(self, requirements: List[Dict], tender_data: Dict) -> float:
        """
        资质匹配
        """
        if not requirements:
            return 0
        
        description = tender_data.get('description', '').lower()
        requirements_text = tender_data.get('requirements', '').lower()
        text = f"{description} {requirements_text}"
        
        matched_count = 0
        for req in requirements:
            qual_name = req.get('name', '').lower()
            qual_grade = req.get('grade', '').lower()
            
            if qual_name in text:
                if not qual_grade or qual_grade in text:
                    matched_count += 1
        
        if matched_count == 0:
            return 0
        
        score = matched_count / len(requirements) * 100
        
        return score
    
    def _match_performance(self, requirements: Dict, tender_data: Dict) -> float:
        """
        业绩匹配
        """
        if not requirements:
            return 0
        
        score = 0
        
        if requirements.get('min_amount'):
            budget = tender_data.get('budget')
            if budget and budget >= requirements['min_amount']:
                score += 30
        
        if requirements.get('project_type'):
            description = tender_data.get('description', '').lower()
            if requirements['project_type'].lower() in description:
                score += 30
        
        if requirements.get('min_years'):
            score += 20
        
        return min(score, 100)
    
    def _match_budget(self, budget_min, budget_max, tender_data: Dict) -> float:
        """
        金额匹配
        """
        budget = tender_data.get('budget')
        
        if not budget:
            return 0
        
        if budget_min and budget < budget_min:
            return 0
        
        if budget_max and budget > budget_max:
            return 0
        
        return 100
    
    def _calculate_match_level(self, score: float) -> str:
        """
        计算匹配等级
        """
        if score >= 80:
            return 'high'
        elif score >= 50:
            return 'medium'
        else:
            return 'low'
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度
        """
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


class EnterpriseService:
    """
    企业服务 - 企业信息管理
    """
    
    @staticmethod
    def create_enterprise_from_user(user) -> Optional[Enterprise]:
        """
        从用户信息创建企业
        """
        if not user.company_name:
            return None
        
        enterprise, created = Enterprise.objects.get_or_create(
            name=user.company_name,
            defaults={
                'contact_person': user.real_name,
                'contact_phone': user.phone,
                'contact_email': user.email,
                'created_by': user
            }
        )
        
        return enterprise
    
    @staticmethod
    def update_enterprise_from_profile(user, profile) -> Optional[Enterprise]:
        """
        从用户详情更新企业信息
        """
        if not user.company_name:
            return None
        
        try:
            enterprise = Enterprise.objects.get(name=user.company_name)
        except Enterprise.DoesNotExist:
            enterprise = Enterprise.objects.create(
                name=user.company_name,
                created_by=user
            )
        
        enterprise.contact_person = user.real_name
        enterprise.contact_phone = user.phone
        enterprise.contact_email = user.email
        
        if profile:
            enterprise.address = profile.company_address
            enterprise.bank_name = profile.bank_name
            enterprise.bank_account = profile.bank_account
            enterprise.credit_code = profile.business_license
            enterprise.legal_person = profile.legal_person
        
        enterprise.save()
        
        return enterprise
    
    @staticmethod
    def get_enterprise_statistics(enterprise: Enterprise) -> Dict:
        """
        获取企业统计信息
        """
        return {
            'qualification_count': enterprise.qualifications.count(),
            'valid_qualification_count': enterprise.qualifications.filter(is_valid=True).count(),
            'performance_count': enterprise.performances.count(),
            'match_result_count': enterprise.match_results.count(),
            'high_match_count': enterprise.match_results.filter(match_level='high').count(),
            'medium_match_count': enterprise.match_results.filter(match_level='medium').count(),
            'low_match_count': enterprise.match_results.filter(match_level='low').count(),
        }
    
    @staticmethod
    def check_qualification_expiry(enterprise: Enterprise, days: int = 30) -> List[EnterpriseQualification]:
        """
        检查即将过期的资质
        """
        from datetime import timedelta
        
        today = date.today()
        expiry_date = today + timedelta(days=days)
        
        return enterprise.qualifications.filter(
            is_valid=True,
            expiry_date__lte=expiry_date,
            expiry_date__gte=today
        ).order_by('expiry_date')
    
    @staticmethod
    def search_enterprises(keyword: str, filters: Dict = None) -> List[Enterprise]:
        """
        搜索企业
        """
        queryset = Enterprise.objects.filter(is_active=True)
        
        if keyword:
            queryset = queryset.filter(
                models.Q(name__icontains=keyword) |
                models.Q(short_name__icontains=keyword) |
                models.Q(credit_code__icontains=keyword)
            )
        
        if filters:
            if filters.get('enterprise_type'):
                queryset = queryset.filter(enterprise_type=filters['enterprise_type'])
            
            if filters.get('province'):
                queryset = queryset.filter(province=filters['province'])
            
            if filters.get('city'):
                queryset = queryset.filter(city=filters['city'])
            
            if filters.get('industry'):
                queryset = queryset.filter(industry__icontains=filters['industry'])
        
        return queryset.order_by('-created_at')
