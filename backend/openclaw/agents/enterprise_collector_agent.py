"""
企业信息采集Agent
负责从天眼查、企查查等平台采集企业信息
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from asgiref.sync import sync_to_async
from openclaw.base_agent import BaseAgent, AgentType, AgentCapability, TaskResult
from openclaw.skill_registry import skill_registry


logger = logging.getLogger(__name__)


class EnterpriseInfoCollectorAgent(BaseAgent):
    """
    企业信息采集Agent
    从天眼查、企查查等平台采集企业信息并保存到数据库
    """
    
    agent_type = AgentType.COLLECTOR
    capabilities = [
        AgentCapability.CRAWLING,
        AgentCapability.PARSING,
        AgentCapability.MATCHING
    ]
    default_tools = ['http_request', 'execute_code']
    
    SYSTEM_PROMPT = """你是一个专业的企业信息采集专家。你的任务是：
1. 根据企业名称从天眼查、企查查等平台采集企业信息
2. 解析和标准化企业数据
3. 将数据保存到企业数据库
4. 处理采集过程中的异常情况

采集的企业信息包括：
- 基本信息：企业名称、统一社会信用代码、法人代表、注册资本、成立日期等
- 联系方式：地址、电话、邮箱、网站等
- 经营信息：经营范围、所属行业、企业类型等
- 资质信息：各类资质证书、认证等

请确保采集的数据准确、完整，并符合数据库字段要求。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sources = {
            'tianyancha': '天眼查',
            'qichacha': '企查查'
        }
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行企业信息采集任务
        
        Args:
            task: {
                'company_name': '企业全称',
                'source': 'tianyancha/qichacha/auto',
                'save_to_db': True/False,
                'update_existing': True/False
            }
        """
        company_name = task.get('company_name')
        source = task.get('source', 'auto')
        save_to_db = task.get('save_to_db', True)
        update_existing = task.get('update_existing', False)
        
        if not company_name:
            return TaskResult(
                success=False,
                error='企业名称不能为空'
            )
        
        try:
            self.update_context('company_name', company_name)
            self.update_context('source', source)
            
            enterprise_data, sources_tried = await self._collect_enterprise_info(company_name, source)
            
            if not enterprise_data:
                return TaskResult(
                    success=False,
                    error=f'未找到企业: {company_name}',
                    metadata={'sources_tried': sources_tried}
                )
            
            qualification_data = await self._collect_qualifications(
                company_name, 
                enterprise_data.get('credit_code')
            )
            
            shareholder_data = await self._collect_shareholders(company_name)
            
            merged_data = self._merge_data(enterprise_data, qualification_data, shareholder_data)
            
            enterprise_id = None
            if save_to_db:
                enterprise_id = await self._save_to_database(
                    merged_data, 
                    update_existing
                )
            
            self.add_memory('last_collection', {
                'company_name': company_name,
                'enterprise_id': enterprise_id,
                'data_source': source,
                'timestamp': datetime.now().isoformat()
            })
            
            return TaskResult(
                success=True,
                data={
                    'company_name': company_name,
                    'enterprise_id': enterprise_id,
                    'enterprise_data': merged_data,
                    'source': source,
                    'saved_to_db': save_to_db
                },
                metadata={'agent_id': self.agent_id, 'sources_tried': sources_tried}
            )
            
        except Exception as e:
            logger.error(f"企业信息采集失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e),
                metadata={'sources_tried': ['tianyancha', 'qichacha', 'aiqicha', 'gsxt']}
            )
    
    async def _collect_enterprise_info(self, company_name: str, source: str) -> tuple:
        """
        采集企业基本信息
        
        Returns:
            tuple: (企业数据字典, 尝试过的数据源列表)
        """
        result = await skill_registry.execute_skill(
            'enterprise_info_collector',
            company_name=company_name,
            source=source
        )
        
        if result.success:
            sources_tried = result.metadata.get('sources_tried', [result.metadata.get('source', source)])
            return result.data, sources_tried
        else:
            logger.warning(f"企业信息采集失败: {result.error}")
            sources_tried = result.metadata.get('sources_tried', ['tianyancha', 'qichacha', 'aiqicha', 'gsxt'])
            return {}, sources_tried
    
    async def _collect_qualifications(self, company_name: str, credit_code: str = None) -> List[Dict]:
        """
        采集企业资质信息
        """
        result = await skill_registry.execute_skill(
            'enterprise_qualification_collector',
            company_name=company_name,
            credit_code=credit_code
        )
        
        if result.success:
            return result.data.get('qualifications', [])
        else:
            logger.warning(f"企业资质采集失败: {result.error}")
            return []
    
    async def _collect_shareholders(self, company_name: str) -> List[Dict]:
        """
        采集股东信息
        """
        result = await skill_registry.execute_skill(
            'enterprise_shareholder_collector',
            company_name=company_name
        )
        
        if result.success:
            return result.data.get('shareholders', [])
        else:
            logger.warning(f"股东信息采集失败: {result.error}")
            return []
    
    def _merge_data(
        self, 
        enterprise_data: Dict, 
        qualification_data: List[Dict],
        shareholder_data: List[Dict]
    ) -> Dict:
        """
        合并采集的数据
        """
        merged = enterprise_data.copy()
        
        if qualification_data:
            merged['qualifications'] = qualification_data
        
        if shareholder_data:
            merged['shareholders'] = shareholder_data
        
        return merged
    
    async def _save_to_database(
        self, 
        data: Dict, 
        update_existing: bool = False
    ) -> int:
        """
        保存到数据库
        
        Returns:
            enterprise_id: 企业ID
        """
        return await self._save_enterprise_sync(data, update_existing)
    
    @sync_to_async
    def _save_enterprise_sync(self, data: Dict, update_existing: bool = False) -> int:
        """
        同步保存企业数据到数据库（通过sync_to_async包装后可在异步上下文调用）
        """
        from apps.enterprise.models import Enterprise, EnterpriseQualification
        
        credit_code = data.get('credit_code')
        company_name = data.get('name')
        
        enterprise = None
        
        if credit_code:
            try:
                enterprise = Enterprise.objects.get(credit_code=credit_code)
                if not update_existing:
                    logger.info(f"企业已存在: {company_name}, 跳过更新")
                    return enterprise.id
            except Enterprise.DoesNotExist:
                pass
        
        if not enterprise and company_name:
            try:
                enterprise = Enterprise.objects.get(name=company_name)
                if not update_existing:
                    logger.info(f"企业已存在: {company_name}, 跳过更新")
                    return enterprise.id
            except Enterprise.DoesNotExist:
                pass
        
        enterprise_fields = {
            'name': data.get('name'),
            'short_name': data.get('short_name'),
            'credit_code': credit_code,
            'registration_number': data.get('registration_number'),
            'legal_person': data.get('legal_person'),
            'registered_capital': data.get('registered_capital'),
            'establishment_date': self._parse_date(data.get('establishment_date')),
            'province': data.get('province'),
            'city': data.get('city'),
            'district': data.get('district'),
            'address': data.get('address'),
            'business_scope': data.get('business_scope'),
            'industry': data.get('industry'),
            'contact_phone': data.get('phone'),
            'contact_email': data.get('email'),
            'website': data.get('website'),
            'is_verified': True,
            'extra_info': {
                'company_type': data.get('company_type'),
                'company_status': data.get('company_status'),
                'social_staff_num': data.get('social_staff_num'),
                'taxpayer_id': data.get('taxpayer_id'),
                'organization_code': data.get('organization_code'),
                'source': data.get('source'),
                'collected_at': datetime.now().isoformat()
            }
        }
        
        if data.get('tags'):
            enterprise_fields['tags'] = data.get('tags')
        
        if enterprise:
            for key, value in enterprise_fields.items():
                if value is not None and key != 'name':
                    setattr(enterprise, key, value)
            enterprise.save()
            logger.info(f"更新企业: {enterprise.name}")
        else:
            enterprise_fields = {k: v for k, v in enterprise_fields.items() if v is not None}
            enterprise = Enterprise.objects.create(**enterprise_fields)
            logger.info(f"创建企业: {enterprise.name}")
        
        qualifications = data.get('qualifications', [])
        for qual in qualifications:
            if update_existing:
                EnterpriseQualification.objects.update_or_create(
                    enterprise=enterprise,
                    certificate_number=qual.get('certificate_number'),
                    defaults={
                        'qualification_type': qual.get('qualification_type', 'other'),
                        'qualification_name': qual.get('qualification_name'),
                        'grade': qual.get('grade'),
                        'scope': qual.get('scope'),
                        'issue_date': self._parse_date(qual.get('issue_date')),
                        'expiry_date': self._parse_date(qual.get('expiry_date')),
                        'issuing_authority': qual.get('issuing_authority'),
                    }
                )
            else:
                EnterpriseQualification.objects.get_or_create(
                    enterprise=enterprise,
                    certificate_number=qual.get('certificate_number'),
                    defaults={
                        'qualification_type': qual.get('qualification_type', 'other'),
                        'qualification_name': qual.get('qualification_name'),
                        'grade': qual.get('grade'),
                        'scope': qual.get('scope'),
                        'issue_date': self._parse_date(qual.get('issue_date')),
                        'expiry_date': self._parse_date(qual.get('expiry_date')),
                        'issuing_authority': qual.get('issuing_authority'),
                    }
                )
        
        return enterprise.id
    
    def _parse_date(self, date_value: Any) -> Any:
        """
        解析日期值
        """
        if not date_value:
            return None
        
        if isinstance(date_value, str):
            try:
                from datetime import datetime
                if len(date_value) == 10:
                    return datetime.strptime(date_value, '%Y-%m-%d').date()
                elif len(date_value) >= 19:
                    return datetime.strptime(date_value[:19], '%Y-%m-%d %H:%M:%S').date()
            except ValueError:
                pass
        
        return date_value


class EnterpriseBatchCollectorAgent(BaseAgent):
    """
    企业批量采集Agent
    批量采集多个企业信息
    """
    
    agent_type = AgentType.COLLECTOR
    capabilities = [
        AgentCapability.CRAWLING,
        AgentCapability.ORCHESTRATING
    ]
    
    SYSTEM_PROMPT = """你是一个企业信息批量采集专家。你的任务是：
1. 接收企业名称列表
2. 并发采集多个企业信息
3. 汇总采集结果
4. 处理失败的采集任务"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._child_agents: Dict[str, EnterpriseInfoCollectorAgent] = {}
    
    async def execute(self, task: Dict[str, Any]) -> TaskResult:
        """
        执行批量采集任务
        
        Args:
            task: {
                'company_names': ['企业名称1', '企业名称2', ...],
                'source': 'tianyancha/qichacha/auto',
                'save_to_db': True/False,
                'update_existing': True/False,
                'max_concurrent': 5
            }
        """
        company_names = task.get('company_names', [])
        source = task.get('source', 'auto')
        save_to_db = task.get('save_to_db', True)
        update_existing = task.get('update_existing', False)
        max_concurrent = task.get('max_concurrent', 5)
        
        if not company_names:
            return TaskResult(
                success=False,
                error='企业名称列表不能为空'
            )
        
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def collect_with_limit(company_name: str) -> Dict:
                async with semaphore:
                    agent = EnterpriseInfoCollectorAgent(session_id=self.session_id)
                    result = await agent.run({
                        'company_name': company_name,
                        'source': source,
                        'save_to_db': save_to_db,
                        'update_existing': update_existing
                    })
                    return {
                        'company_name': company_name,
                        'success': result.success,
                        'data': result.data if result.success else None,
                        'error': result.error if not result.success else None
                    }
            
            tasks = [collect_with_limit(name) for name in company_names]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = 0
            failed_count = 0
            collected_enterprises = []
            errors = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    errors.append(str(result))
                elif result.get('success'):
                    success_count += 1
                    collected_enterprises.append(result)
                else:
                    failed_count += 1
                    errors.append(result.get('error'))
            
            return TaskResult(
                success=True,
                data={
                    'total': len(company_names),
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'collected_enterprises': collected_enterprises,
                    'errors': errors[:10]
                },
                metadata={'agent_id': self.agent_id}
            )
            
        except Exception as e:
            logger.error(f"批量采集失败: {str(e)}")
            return TaskResult(
                success=False,
                error=str(e)
            )
