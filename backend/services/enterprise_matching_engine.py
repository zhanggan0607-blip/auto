"""
企业库匹配引擎
使用 Embedding 向量化模型进行语义匹配
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from django.conf import settings

from apps.enterprise.models import Enterprise, EnterpriseQualification, EnterprisePerformance
from services.vector import embedding_service, enterprise_vector_store

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """
    匹配结果
    """
    enterprise_id: int
    enterprise_name: str
    match_score: float
    match_level: str
    matched_reasons: List[str]
    tender_data: Dict[str, Any]


class EnterpriseMatchingEngine:
    """
    企业库匹配引擎
    使用 Embedding 向量化进行语义匹配
    """
    
    MATCH_THRESHOLD = {
        'high': 0.8,
        'medium': 0.6,
        'low': 0.4
    }
    
    def __init__(self):
        self._ensure_index_built()
    
    def _ensure_index_built(self):
        """
        确保索引已构建
        """
        try:
            count = enterprise_vector_store.get_count()
            logger.info(f"当前向量库中有 {count} 条企业数据")
        except Exception as e:
            logger.warning(f"检查向量库失败: {str(e)}")
    
    def build_enterprise_index(self) -> int:
        """
        构建企业向量索引
        
        Returns:
            int: 成功构建的数量
        """
        enterprises = Enterprise.objects.filter(is_active=True).select_related()
        
        batch_data = []
        
        for enterprise in enterprises:
            text = self._build_enterprise_text(enterprise)
            
            if not text:
                continue
            
            metadata = {
                'enterprise_id': enterprise.id,
                'name': enterprise.name,
                'industry': enterprise.industry or '',
                'province': enterprise.province or '',
                'city': enterprise.city or '',
            }
            
            batch_data.append({
                'id': str(enterprise.id),
                'text': text,
                'metadata': metadata
            })
        
        if batch_data:
            texts = [e['text'] for e in batch_data]
            embeddings = embedding_service.embed_batch(texts)

            for i, (data, embedding) in enumerate(zip(batch_data, embeddings)):
                data['embedding'] = embedding

            count = enterprise_vector_store.batch_add_enterprises(batch_data)
            logger.info(f"企业向量索引构建完成: {count} 条")
            return count
        
        return 0
    
    def _build_enterprise_text(self, enterprise: Enterprise) -> str:
        """
        构建企业文本描述（用于向量化）
        """
        parts = []
        
        parts.append(enterprise.name or '')
        
        if enterprise.business_scope:
            parts.append(f"经营范围: {enterprise.business_scope}")
        
        if enterprise.industry:
            parts.append(f"行业: {enterprise.industry}")
        
        qualifications = EnterpriseQualification.objects.filter(
            enterprise=enterprise,
            is_valid=True
        ).values_list('qualification_name', 'scope')
        
        for name, scope in qualifications[:5]:
            if name:
                parts.append(f"资质: {name}")
            if scope:
                parts.append(f"资质范围: {scope}")
        
        performances = EnterprisePerformance.objects.filter(
            enterprise=enterprise
        ).values_list('project_name', 'description')[:5]
        
        for name, desc in performances:
            if name:
                parts.append(f"业绩项目: {name}")
            if desc:
                parts.append(f"项目描述: {desc}")
        
        return ' '.join([p for p in parts if p])
    
    def match_tender(
        self,
        tender_data: Dict[str, Any],
        top_k: int = 10,
        min_score: float = None
    ) -> List[MatchResult]:
        """
        匹配招标信息
        
        Args:
            tender_data: 招标信息数据
            top_k: 返回前K个匹配结果
            min_score: 最小匹配分数
            
        Returns:
            list: 匹配结果列表
        """
        if min_score is None:
            min_score = self.MATCH_THRESHOLD['low']
        
        query_text = self._build_tender_text(tender_data)
        
        search_results = enterprise_vector_store.search_similar(
            query_text=query_text,
            n_results=top_k
        )
        
        results = []
        
        for item in search_results:
            try:
                score = 1.0 - item.get('distance', 1.0)
                
                if score < min_score:
                    continue
                
                if score >= self.MATCH_THRESHOLD['high']:
                    level = 'high'
                elif score >= self.MATCH_THRESHOLD['medium']:
                    level = 'medium'
                else:
                    level = 'low'
                
                enterprise_id = int(item['id'])
                enterprise = Enterprise.objects.filter(id=enterprise_id).first()
                
                if not enterprise:
                    continue
                
                matched_reasons = self._generate_match_reasons(
                    enterprise,
                    tender_data,
                    score
                )
                
                result = MatchResult(
                    enterprise_id=enterprise_id,
                    enterprise_name=enterprise.name,
                    match_score=score,
                    match_level=level,
                    matched_reasons=matched_reasons,
                    tender_data=tender_data
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理匹配结果失败: {str(e)}")
                continue
        
        return results
    
    def _build_tender_text(self, tender_data: Dict[str, Any]) -> str:
        """
        构建招标信息文本
        """
        parts = []
        
        if tender_data.get('title'):
            parts.append(tender_data['title'])
        
        if tender_data.get('description'):
            parts.append(tender_data['description'])
        
        if tender_data.get('budget'):
            parts.append(f"预算金额: {tender_data['budget']}")
        
        if tender_data.get('region'):
            parts.append(f"地区: {tender_data['region']}")
        
        if tender_data.get('industry'):
            parts.append(f"行业: {tender_data['industry']}")
        
        return ' '.join([p for p in parts if p])
    
    def _generate_match_reasons(
        self,
        enterprise: Enterprise,
        tender_data: Dict[str, Any],
        score: float
    ) -> List[str]:
        """
        生成匹配原因
        """
        reasons = []
        
        if tender_data.get('title'):
            title_lower = tender_data['title'].lower()
            
            if enterprise.business_scope:
                scope_lower = enterprise.business_scope.lower()
                if any(kw in title_lower for kw in ['采购', '供应', '服务']):
                    if any(kw in scope_lower for kw in ['采购', '供应', '服务']):
                        reasons.append('经营范围匹配')
            
            if enterprise.industry:
                if any(kw in title_lower for kw in [enterprise.industry]):
                    reasons.append('行业匹配')
        
        if tender_data.get('region'):
            if enterprise.province:
                if enterprise.province in tender_data['region']:
                    reasons.append('地区匹配')
            if enterprise.city:
                if enterprise.city in tender_data['region']:
                    reasons.append('城市匹配')
        
        if score >= self.MATCH_THRESHOLD['high']:
            reasons.append(f'语义相似度高 ({score:.2f})')
        
        return reasons
    
    def match_tender_batch(
        self,
        tenders: List[Dict[str, Any]],
        top_k: int = 5,
        min_score: float = 0.6
    ) -> Dict[str, List[MatchResult]]:
        """
        批量匹配招标信息
        
        Args:
            tenders: 招标信息列表
            top_k: 每个招标匹配的企业数量
            min_score: 最小匹配分数
            
        Returns:
            dict: {tender_id: [匹配结果列表]}
        """
        results = {}
        
        for tender in tenders:
            tender_id = tender.get('id') or tender.get('title', '')
            
            try:
                matches = self.match_tender(
                    tender_data=tender,
                    top_k=top_k,
                    min_score=min_score
                )
                
                results[tender_id] = matches
                
            except Exception as e:
                logger.error(f"匹配招标失败 {tender_id}: {str(e)}")
                results[tender_id] = []
        
        return results
    
    def save_match_results(
        self,
        matches: List[MatchResult],
        save_to_db: bool = True
    ) -> int:
        """
        保存匹配结果
        
        Args:
            matches: 匹配结果列表
            save_to_db: 是否保存到数据库
            
        Returns:
            int: 保存的数量
        """
        if not save_to_db:
            return len(matches)
        
        from apps.enterprise.models import EnterpriseMatchResult
        
        saved_count = 0
        
        for match in matches:
            try:
                EnterpriseMatchResult.objects.create(
                    enterprise_id=match.enterprise_id,
                    tender_title=match.tender_data.get('title', ''),
                    tender_url=match.tender_data.get('source_url', ''),
                    publish_date=match.tender_data.get('publish_date'),
                    deadline_date=match.tender_data.get('deadline_date'),
                    match_score=match.match_score,
                    match_level=match.match_level,
                    matched_reasons=match.matched_reasons,
                    tender_data=match.tender_data,
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"保存匹配结果失败: {str(e)}")
        
        return saved_count


enterprise_matching_engine = EnterpriseMatchingEngine()
