"""
消息内容审核模块
对用户输入、Agent消息、外部搜索结果等进行内容安全审核
"""
import re
import logging
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentRiskLevel(Enum):
    """内容风险等级"""
    SAFE = 'safe'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    BLOCKED = 'blocked'


@dataclass
class ContentCheckResult:
    """内容检查结果"""
    is_safe: bool
    risk_level: ContentRiskLevel
    risk_type: str
    risk_description: str
    matched_keywords: List[str]
    suggestions: List[str]


class ContentModeration:
    """
    内容审核类
    支持关键词过滤、正则匹配、敏感信息检测
    """

    BLOCKED_KEYWORDS = [
        '钓鱼',
        '诈骗',
        '传销',
        '赌博',
        '色情',
        '暴力',
        '恐怖',
        '分裂',
        '颠覆',
        '谣言',
    ]

    SENSITIVE_PATTERNS = [
        (r'\d{15,18}', 'ID_CARD', '身份证号'),
        (r'\d{4}[-/]\d{2}[-/]\d{2}', 'DATE', '日期'),
        (r'1[3-9]\d{9}', 'PHONE', '手机号'),
        (r'\d{6,}', 'NUMBERS', '长数字序列'),
    ]

    PROMPT_INJECTION_PATTERNS = [
        r'(?i)ignore\s*(all\s*)?(previous|above|prior)\s*(instructions?|prompts?|constraints?)',
        r'(?i)(forget|disregard)\s*(all\s*)?(previous|above|prior)\s*(instructions?|prompts?)',
        r'(?i)you\s+are\s+now\s+(?:a|an)\s+(?:different|new|another)\s+(?:AI|assistant|bot)',
        r'(?i)system\s*:\s*',
        r'(?i)user\s*:\s*',
        r'(?i)assistant\s*:\s*',
        r'(?i)context\s*:\s*',
        r'(?i)new\s+instruction',
        r'(?i)<\|?\w+\|>?',
        r'(?i)\[INST\]',
        r'(?i)\[/INST\]',
        r'(?i)<<\+>>',
        r'(?i)<<\|>>',
        r'\$\{.*\}',
        r'\{\{.*\}\}',
    ]

    def __init__(self):
        self._blocked_keywords_pattern = None
        self._initialize_patterns()

    def _initialize_patterns(self):
        """初始化正则表达式模式"""
        try:
            blocked_pattern = '|'.join([re.escape(kw) for kw in self.BLOCKED_KEYWORDS])
            self._blocked_keywords_pattern = re.compile(blocked_pattern, re.IGNORECASE)
        except re.error as e:
            logger.error(f"正则表达式编译失败: {e}")
            self._blocked_keywords_pattern = None

    def check_text(self, text: str, user_id: int = None) -> ContentCheckResult:
        """
        检查文本内容安全性

        Args:
            text: 待检查文本
            user_id: 用户ID

        Returns:
            ContentCheckResult: 检查结果
        """
        if not text:
            return ContentCheckResult(
                is_safe=True,
                risk_level=ContentRiskLevel.SAFE,
                risk_type='',
                risk_description='',
                matched_keywords=[],
                suggestions=[]
            )

        matched_keywords = []
        risk_types = []
        suggestions = []

        blocked_match = self._blocked_keywords_pattern.search(text) if self._blocked_keywords_pattern else None
        if blocked_match:
            matched_keywords.append(blocked_match.group())
            risk_types.append('BLOCKED_KEYWORD')

        for pattern, pattern_type, description in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                risk_types.append(pattern_type)
                suggestions.append(f'检测到{description}，建议脱敏处理')

        prompt_injection_found = False
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text):
                prompt_injection_found = True
                risk_types.append('PROMPT_INJECTION')
                suggestions.append('检测到提示词注入攻击特征')
                break

        if len(text) > 50000:
            risk_types.append('OVER_LENGTH')
            suggestions.append('文本过长，建议拆分处理')

        if 'select' in text.lower() and 'from' in text.lower():
            if re.search(r'(?i)(union|select|insert|update|delete|drop)\s', text):
                risk_types.append('SQL_LIKE')
                suggestions.append('检测到SQL语句特征，建议验证输入来源')

        if any(proto in text.lower() for proto in ['http://', 'https://', 'ftp://']):
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, text)
            if urls:
                risk_types.append('EXTERNAL_URL')
                suggestions.append(f'包含{len(urls)}个外部链接，请确认链接安全性')

        risk_level = self._calculate_risk_level(risk_types)

        return ContentCheckResult(
            is_safe=risk_level not in [ContentRiskLevel.HIGH, ContentRiskLevel.BLOCKED],
            risk_level=risk_level,
            risk_type=','.join(risk_types) if risk_types else '',
            risk_description=self._get_risk_description(risk_types),
            matched_keywords=matched_keywords,
            suggestions=suggestions
        )

    def _calculate_risk_level(self, risk_types: List[str]) -> ContentRiskLevel:
        """计算风险等级"""
        if not risk_types:
            return ContentRiskLevel.SAFE

        if 'BLOCKED_KEYWORD' in risk_types:
            return ContentRiskLevel.BLOCKED

        high_risks = ['PROMPT_INJECTION']
        medium_risks = ['SQL_LIKE', 'EXTERNAL_URL']
        low_risks = ['ID_CARD', 'PHONE', 'DATE', 'NUMBERS', 'OVER_LENGTH']

        if any(r in high_risks for r in risk_types):
            return ContentRiskLevel.HIGH

        if any(r in medium_risks for r in risk_types):
            return ContentRiskLevel.MEDIUM

        if any(r in low_risks for r in risk_types):
            return ContentRiskLevel.LOW

        return ContentRiskLevel.SAFE

    def _get_risk_description(self, risk_types: List[str]) -> str:
        """获取风险描述"""
        descriptions = {
            'BLOCKED_KEYWORD': '包含敏感关键词',
            'PROMPT_INJECTION': '可能存在提示词注入攻击',
            'SQL_LIKE': '包含SQL语句特征',
            'EXTERNAL_URL': '包含外部链接',
            'ID_CARD': '可能包含身份证信息',
            'PHONE': '可能包含手机号信息',
            'DATE': '包含日期信息',
            'NUMBERS': '包含长数字序列',
            'OVER_LENGTH': '文本过长'
        }
        return '; '.join([descriptions.get(r, r) for r in risk_types])

    def sanitize_text(self, text: str) -> str:
        """
        对文本进行脱敏处理

        Args:
            text: 待脱敏文本

        Returns:
            str: 脱敏后的文本
        """
        if not text:
            return text

        result = text

        for pattern, pattern_type, description in self.SENSITIVE_PATTERNS:
            if pattern_type == 'ID_CARD':
                result = re.sub(r'\d{15,18}', '[身份证号]', result)
            elif pattern_type == 'PHONE':
                result = re.sub(r'1[3-9]\d{9}', '[手机号]', result)

        return result

    def check_batch(self, texts: List[str], user_id: int = None) -> List[ContentCheckResult]:
        """
        批量检查文本内容

        Args:
            texts: 文本列表
            user_id: 用户ID

        Returns:
            List[ContentCheckResult]: 检查结果列表
        """
        return [self.check_text(text, user_id) for text in texts]


content_moderation = ContentModeration()


def check_user_input(text: str, user_id: int = None) -> ContentCheckResult:
    """
    检查用户输入安全性

    Args:
        text: 用户输入文本
        user_id: 用户ID

    Returns:
        ContentCheckResult: 检查结果
    """
    return content_moderation.check_text(text, user_id)


def check_llm_response(text: str) -> ContentCheckResult:
    """
    检查LLM响应安全性

    Args:
        text: LLM响应文本

    Returns:
        ContentCheckResult: 检查结果
    """
    result = content_moderation.check_text(text)

    if not result.is_safe:
        logger.warning(f"LLM响应包含风险内容: {result.risk_description}")

    return result


def check_search_result(text: str) -> ContentCheckResult:
    """
    检查搜索结果安全性

    Args:
        text: 搜索结果文本

    Returns:
        ContentCheckResult: 检查结果
    """
    result = content_moderation.check_text(text)

    if result.risk_level in [ContentRiskLevel.HIGH, ContentRiskLevel.BLOCKED]:
        logger.warning(f"搜索结果包含风险内容: {result.risk_description}")

    return result


def sanitize_sensitive_data(text: str) -> str:
    """
    对敏感数据进行脱敏

    Args:
        text: 原始文本

    Returns:
        str: 脱敏后的文本
    """
    return content_moderation.sanitize_text(text)