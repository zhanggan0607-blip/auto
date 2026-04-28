"""
AI 企业信息提取器
使用 LLM 进行语义提取
"""
import asyncio
import logging
import re
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AIEnterpriseExtractor:
    """
    AI 企业信息提取器
    使用 LLM 从 HTML 中提取企业信息
    """
    
    EXTRACTION_PROMPT = """请从以下HTML内容中提取企业信息，以JSON格式返回。

需要提取的字段：
- name: 企业名称
- credit_code: 统一社会信用代码（18位）
- legal_person: 法定代表人姓名
- registered_capital: 注册资本（数字，单位万元）
- establishment_date: 成立日期（YYYY-MM-DD格式）
- address: 注册地址
- business_scope: 经营范围
- industry: 所属行业
- phone: 联系电话
- email: 邮箱

HTML内容：
{html_content}

请直接返回JSON格式的数据，不要包含其他说明文字。如果某个字段无法提取，则不返回该字段。"""

    def __init__(self, model: str = 'qwen'):
        """
        初始化 AI 提取器
        
        Args:
            model: 使用的模型 (qwen/openai/local)
        """
        self.model = model
        self._llm_client = None
    
    def _get_llm_client(self):
        """
        获取 LLM 客户端（延迟加载）
        """
        if self._llm_client is None:
            try:
                from services.unified_llm_service import UnifiedLLMService
                self._llm_client = UnifiedLLMService()
            except ImportError:
                try:
                    from openclaw.llm import get_llm_client
                    self._llm_client = get_llm_client()
                except ImportError:
                    logger.warning("LLM 服务未配置，AI 提取功能不可用")
                    self._llm_client = None
        return self._llm_client
    
    async def extract(self, html: str, company_name: str) -> Dict[str, Any]:
        """
        使用 AI 提取企业信息
        
        Args:
            html: HTML 内容
            company_name: 企业名称
            
        Returns:
            Dict: 提取的企业信息
        """
        llm_client = self._get_llm_client()
        
        if llm_client is None:
            return {}
        
        try:
            truncated_html = self._truncate_html(html)
            
            prompt = self.EXTRACTION_PROMPT.format(html_content=truncated_html)
            
            response = await self._call_llm(llm_client, prompt)
            
            if response:
                return self._parse_ai_response(response, company_name)
                
        except Exception as e:
            logger.error(f"AI 提取失败: {str(e)}")
        
        return {}
    
    def _truncate_html(self, html: str, max_length: int = 15000) -> str:
        """
        截断 HTML 内容
        """
        if len(html) <= max_length:
            return html
        
        important_patterns = [
            r'<title[^>]*>.*?</title>',
            r'<meta[^>]*name=["\']description["\'][^>]*>',
            r'<div[^>]*class=["\'][^"\']*company[^"\']*["\'][^>]*>.*?</div>',
            r'<div[^>]*class=["\'][^"\']*info[^"\']*["\'][^>]*>.*?</div>',
            r'<table[^>]*>.*?</table>',
        ]
        
        important_content = []
        for pattern in important_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            important_content.extend(matches)
        
        combined = '\n'.join(important_content)
        
        if len(combined) > max_length:
            return combined[:max_length]
        
        remaining_length = max_length - len(combined)
        if remaining_length > 0:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                body_content = body_match.group(1)
                combined += '\n' + body_content[:remaining_length]
        
        return combined[:max_length]
    
    async def _call_llm(self, client, prompt: str) -> Optional[str]:
        """
        调用 LLM
        """
        import inspect

        try:
            if hasattr(client, 'achat'):
                return await client.achat(prompt)
            elif hasattr(client, 'chat'):
                chat_method = getattr(client, 'chat')
                if inspect.iscoroutinefunction(chat_method):
                    return await chat_method(prompt)
                else:
                    return chat_method(prompt)
            elif hasattr(client, 'invoke'):
                result = client.invoke(prompt)
                if asyncio.iscoroutine(result):
                    result = await result
                return str(result)
            else:
                logger.warning("LLM 客户端不支持已知的调用方法")
                return None
        except Exception as e:
            logger.error(f"LLM 调用失败: {str(e)}")
            return None
    
    def _parse_ai_response(self, response: str, company_name: str) -> Dict[str, Any]:
        """
        解析 AI 响应
        """
        result = {'name': company_name}
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                field_mapping = {
                    'name': 'name',
                    'credit_code': 'credit_code',
                    'creditCode': 'credit_code',
                    'legal_person': 'legal_person',
                    'legalPerson': 'legal_person',
                    'registered_capital': 'registered_capital',
                    'regCapital': 'registered_capital',
                    'establishment_date': 'establishment_date',
                    'estiblishTime': 'establishment_date',
                    'address': 'address',
                    'regLocation': 'address',
                    'business_scope': 'business_scope',
                    'businessScope': 'business_scope',
                    'industry': 'industry',
                    'phone': 'phone',
                    'phoneNumber': 'phone',
                    'email': 'email',
                }
                
                for key, value in data.items():
                    if value and str(value).strip():
                        mapped_key = field_mapping.get(key, key)
                        result[mapped_key] = self._clean_value(value, mapped_key)
                        
        except json.JSONDecodeError:
            logger.warning("AI 响应不是有效的 JSON 格式")
        except Exception as e:
            logger.warning(f"解析 AI 响应失败: {str(e)}")
        
        return result
    
    def _clean_value(self, value: Any, field: str) -> Any:
        """
        清理字段值
        """
        if value is None:
            return None
        
        value = str(value).strip()
        
        if field == 'credit_code':
            match = re.search(r'[A-Z0-9]{18}', value)
            return match.group(0) if match else value
        
        elif field == 'registered_capital':
            match = re.search(r'([\d,.]+)\s*(万|亿元)?', value)
            if match:
                num = float(match.group(1).replace(',', ''))
                unit = match.group(2)
                if unit == '亿':
                    num *= 10000
                elif unit != '万':
                    num /= 10000
                return num
            return value
        
        elif field == 'establishment_date':
            match = re.search(r'(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})', value)
            if match:
                return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
            return value
        
        elif field == 'phone':
            match = re.search(r'[\d\-]{7,15}', value)
            return match.group(0) if match else value
        
        elif field == 'email':
            match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', value)
            return match.group(0) if match else value
        
        return value
