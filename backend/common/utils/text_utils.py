"""
文本工具模块
提供统一的文本处理函数
"""
import re
import hashlib
from typing import List, Optional


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断文本到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        str: 截断后的文本
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str, remove_special: bool = True) -> str:
    """
    清理文本，去除多余空白和特殊字符

    Args:
        text: 原始文本
        remove_special: 是否移除特殊字符

    Returns:
        str: 清理后的文本
    """
    if not text:
        return ''

    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    if remove_special:
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()（）。，；：！？\d+-]', '', text)

    return text


def extract_numbers(text: str) -> List[float]:
    """
    从文本中提取所有数字

    Args:
        text: 文本

    Returns:
        List[float]: 提取的数字列表
    """
    if not text:
        return []

    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)

    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue

    return numbers


def mask_sensitive(text: str, mask_type: str = 'phone') -> str:
    """
    脱敏处理

    Args:
        text: 原始文本
        mask_type: 脱敏类型 ('phone', 'id_card', 'bank_card', 'email')

    Returns:
        str: 脱敏后的文本
    """
    if not text:
        return text

    if mask_type == 'phone':
        return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)

    elif mask_type == 'id_card':
        return re.sub(r'(\d{6})\d{8}(\d{4})', r'\1********\2', text)

    elif mask_type == 'bank_card':
        return re.sub(r'(\d{4})\d+(\d{4})', r'\1****\2', text)

    elif mask_type == 'email':
        parts = text.split('@')
        if len(parts) == 2:
            name = parts[0]
            if len(name) > 2:
                masked = name[0] + '*' * (len(name) - 2) + name[-1]
            else:
                masked = name[0] + '*'
            return f'{masked}@{parts[1]}'
        return text

    return text


def normalize_text(text: str) -> str:
    """
    标准化文本（全角转半角，大小写统一等）

    Args:
        text: 原始文本

    Returns:
        str: 标准化后的文本
    """
    if not text:
        return ''

    text = text.strip()

    rclone = str.maketrans('（）', '()')
    text = text.translate(rclone)

    text = text.replace('，', ',')
    text = text.replace('。', '.')
    text = text.replace('：', ':')
    text = text.replace('；', ';')
    text = text.replace('！', '!')
    text = text.replace('？', '?')

    return text


def get_text_hash(text: str, algorithm: str = 'md5') -> str:
    """
    获取文本哈希值

    Args:
        text: 文本
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')

    Returns:
        str: 哈希值
    """
    if not text:
        return ''

    if algorithm == 'md5':
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode('utf-8')).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    return ''


def contains_chinese(text: str) -> bool:
    """
    判断文本是否包含中文

    Args:
        text: 文本

    Returns:
        bool: 是否包含中文
    """
    if not text:
        return False

    return bool(re.search(r'[\u4e00-\u9fff]', text))


def remove_html_tags(text: str) -> str:
    """
    移除HTML标签

    Args:
        text: 原始文本

    Returns:
        str: 移除标签后的文本
    """
    if not text:
        return ''

    return re.sub(r'<[^>]+>', '', text)
