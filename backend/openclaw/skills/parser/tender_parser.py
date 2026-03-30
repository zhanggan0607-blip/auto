"""
招标文件解析技能
使用本地大模型解析招标文件
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from openclaw.skill_registry import Skill, SkillMetadata, SkillResult


logger = logging.getLogger(__name__)


class TenderDocumentParserSkill(Skill):
    """
    招标文件解析技能
    使用LLM解析招标文件，提取关键信息
    """
    
    metadata = SkillMetadata(
        name='tender_document_parser',
        description='解析招标文件，提取项目信息、评分标准、资质要求等',
        version='1.0.0',
        author='OpenClaw',
        category='parser',
        tags=['tender', 'document', 'parser', 'llm'],
        input_schema={
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': '招标文件内容'
                },
                'file_path': {
                    'type': 'string',
                    'description': '招标文件路径'
                },
                'extract_fields': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '需要提取的字段列表'
                }
            },
            'required': []
        }
    )
    
    def __init__(self):
        super().__init__()
        self._llm_client = None
    
    def _get_llm_client(self):
        """
        获取LLM客户端（使用统一LLM服务）
        """
        if self._llm_client is None:
            from services.unified_llm_service import unified_llm_service
            self._llm_client = unified_llm_service
        return self._llm_client
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行解析
        """
        content = kwargs.get('content')
        file_path = kwargs.get('file_path')
        extract_fields = kwargs.get('extract_fields', [
            'project_name', 'project_code', 'budget', 'deadline',
            'purchaser', 'requirements', 'scoring_criteria'
        ])
        
        try:
            if not content and file_path:
                content = await self._read_file(file_path)
            
            if not content:
                return SkillResult(
                    success=False,
                    error='No content provided'
                )
            
            parsed_result = await self._parse_with_llm(content, extract_fields)
            
            return SkillResult(
                success=True,
                data=parsed_result,
                metadata={
                    'fields_extracted': list(parsed_result.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Tender document parsing failed: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _read_file(self, file_path: str) -> str:
        """
        读取文件内容
        """
        import os
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return await self._read_pdf(file_path)
        elif ext in ['.doc', '.docx']:
            return await self._read_docx(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    async def _read_pdf(self, file_path: str) -> str:
        """
        读取PDF文件
        """
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ''
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            logger.warning("PyMuPDF not installed, trying pdfplumber")
            try:
                import pdfplumber
                text = ''
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ''
                return text
            except ImportError:
                raise ImportError("No PDF library installed. Install PyMuPDF or pdfplumber.")
    
    async def _read_docx(self, file_path: str) -> str:
        """
        读取Word文档
        """
        from docx import Document
        doc = Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return text
    
    async def _parse_with_llm(self, content: str, extract_fields: List[str]) -> Dict:
        """
        使用LLM解析内容
        """
        llm = self._get_llm_client()
        
        prompt = f"""请分析以下招标文件内容，提取关键信息。

需要提取的字段：
{json.dumps(extract_fields, ensure_ascii=False, indent=2)}

招标文件内容：
{content[:8000]}

请以JSON格式返回提取结果，格式如下：
{{
    "project_name": "项目名称",
    "project_code": "项目编号",
    "budget": "预算金额",
    "deadline": "投标截止时间",
    "purchaser": "采购人信息",
    "requirements": "资质要求",
    "scoring_criteria": "评分标准"
}}

如果某个字段无法提取，请返回null。只返回JSON，不要其他内容。"""

        response = await llm.chat(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {response}")
            return {}


class OCRSkill(Skill):
    """
    OCR识别技能
    使用阿里云OCR或本地视觉模型
    """
    
    metadata = SkillMetadata(
        name='ocr_recognition',
        description='识别图片中的文字内容',
        version='1.0.0',
        author='OpenClaw',
        category='parser',
        tags=['ocr', 'image', 'vision'],
        input_schema={
            'type': 'object',
            'properties': {
                'image_path': {
                    'type': 'string',
                    'description': '图片路径'
                },
                'image_url': {
                    'type': 'string',
                    'description': '图片URL'
                },
                'image_base64': {
                    'type': 'string',
                    'description': 'Base64编码的图片'
                },
                'provider': {
                    'type': 'string',
                    'enum': ['aliyun', 'local'],
                    'default': 'aliyun'
                }
            }
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行OCR识别
        """
        image_path = kwargs.get('image_path')
        image_url = kwargs.get('image_url')
        image_base64 = kwargs.get('image_base64')
        provider = kwargs.get('provider', 'aliyun')
        
        try:
            if provider == 'aliyun':
                result = await self._ocr_aliyun(image_path, image_url, image_base64)
            else:
                result = await self._ocr_local(image_path, image_url, image_base64)
            
            return SkillResult(
                success=True,
                data={'text': result},
                metadata={'provider': provider}
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _ocr_aliyun(
        self,
        image_path: str = None,
        image_url: str = None,
        image_base64: str = None
    ) -> str:
        """
        使用阿里云OCR
        """
        from services.aliyun_ocr_service import AliyunOCRService
        
        ocr_service = AliyunOCRService()
        
        if image_path:
            return await ocr_service.recognize_from_file(image_path)
        elif image_base64:
            return await ocr_service.recognize_from_base64(image_base64)
        elif image_url:
            return await ocr_service.recognize_from_url(image_url)
        else:
            raise ValueError("No image provided")
    
    async def _ocr_local(
        self,
        image_path: str = None,
        image_url: str = None,
        image_base64: str = None
    ) -> str:
        """
        使用本地视觉模型
        """
        from services.unified_llm_service import unified_llm_service
        if image_path:
            import base64
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        if image_base64:
            prompt = "请识别图片中的所有文字内容，按原文格式输出。"
            result = await unified_llm_service.chat(
                message=prompt,
                system_prompt="你是一个OCR识别助手，请准确识别图片中的文字。"
            )
            return result.get('content', '')
        else:
            raise ValueError("No image provided")


class ScoringCriteriaExtractorSkill(Skill):
    """
    评分标准提取技能
    """
    
    metadata = SkillMetadata(
        name='scoring_criteria_extractor',
        description='从招标文件中提取评分标准和权重',
        version='1.0.0',
        author='OpenClaw',
        category='parser',
        tags=['tender', 'scoring', 'criteria'],
        input_schema={
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': '招标文件内容'
                }
            },
            'required': ['content']
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行评分标准提取
        """
        content = kwargs.get('content')
        
        if not content:
            return SkillResult(
                success=False,
                error='No content provided'
            )
        
        try:
            criteria = await self._extract_criteria(content)
            
            return SkillResult(
                success=True,
                data=criteria,
                metadata={
                    'total_items': len(criteria),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _extract_criteria(self, content: str) -> List[Dict]:
        """
        提取评分标准
        """
        from services.unified_llm_service import unified_llm_service
        
        prompt = f"""请从以下招标文件内容中提取评分标准和权重。

内容：
{content[:6000]}

请以JSON数组格式返回评分标准，格式如下：
[
    {{
        "category": "评分类别",
        "item": "评分项",
        "max_score": 最高分,
        "description": "评分说明"
    }}
]

只返回JSON数组，不要其他内容。"""

        result = await unified_llm_service.chat(message=prompt)
        response = result.get('content', '')
        
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
            return []
        except json.JSONDecodeError:
            return []
