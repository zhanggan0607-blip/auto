"""
日期工具模块
提供统一的日期处理函数
"""
from datetime import datetime, timedelta, date
from typing import Tuple, Optional


def get_date_range(days: int = 7) -> Tuple[date, date]:
    """
    获取最近N天的日期范围

    Args:
        days: 天数

    Returns:
        Tuple[date, date]: (开始日期, 结束日期)
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_week_start_end(ref_date: date = None) -> Tuple[date, date]:
    """
    获取指定日期所在周的开始和结束日期（周一到周日）

    Args:
        ref_date: 参照日期，默认今天

    Returns:
        Tuple[date, date]: (周一, 周日)
    """
    if ref_date is None:
        ref_date = date.today()

    weekday = ref_date.weekday()
    start_date = ref_date - timedelta(days=weekday)
    end_date = start_date + timedelta(days=6)

    return start_date, end_date


def get_month_start_end(ref_date: date = None) -> Tuple[date, date]:
    """
    获取指定日期所在月的开始和结束日期

    Args:
        ref_date: 参照日期，默认今天

    Returns:
        Tuple[date, date]: (月初, 月末)
    """
    if ref_date is None:
        ref_date = date.today()

    start_date = date(ref_date.year, ref_date.month, 1)

    if ref_date.month == 12:
        end_date = date(ref_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(ref_date.year, ref_date.month + 1, 1) - timedelta(days=1)

    return start_date, end_date


def parse_date_string(date_str: str, formats: list = None) -> Optional[datetime]:
    """
    尝试多种格式解析日期字符串

    Args:
        date_str: 日期字符串
        formats: 格式列表，默认常见格式

    Returns:
        datetime 或 None
    """
    if not date_str:
        return None

    if formats is None:
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y%m%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M:%S',
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化日期时间为字符串

    Args:
        dt: datetime对象
        format_str: 格式字符串

    Returns:
        str: 格式化后的日期时间字符串
    """
    if dt is None:
        return ''
    return dt.strftime(format_str)


def format_date(d: date, format_str: str = '%Y-%m-%d') -> str:
    """
    格式化日期为字符串

    Args:
        d: date对象
        format_str: 格式字符串

    Returns:
        str: 格式化后的日期字符串
    """
    if d is None:
        return ''
    return d.strftime(format_str)


def get_quarter_start_end(ref_date: date = None) -> Tuple[date, date]:
    """
    获取指定日期所在季度的开始和结束日期

    Args:
        ref_date: 参照日期，默认今天

    Returns:
        Tuple[date, date]: (季初, 季末)
    """
    if ref_date is None:
        ref_date = date.today()

    quarter = (ref_date.month - 1) // 3
    start_month = quarter * 3 + 1
    start_date = date(ref_date.year, start_month, 1)

    if start_month >= 10:
        end_date = date(ref_date.year + 1, 1, 1) - timedelta(days=1)
    elif start_month >= 7:
        end_date = date(ref_date.year, 10, 1) - timedelta(days=1)
    elif start_month >= 4:
        end_date = date(ref_date.year, 7, 1) - timedelta(days=1)
    else:
        end_date = date(ref_date.year, 4, 1) - timedelta(days=1)

    return start_date, end_date


def is_business_day(d: date) -> bool:
    """
    判断是否为工作日

    Args:
        d: 日期

    Returns:
        bool: 是否为工作日（周一到周五）
    """
    return d.weekday() < 5


def get_next_business_day(d: date) -> date:
    """
    获取下一个工作日

    Args:
        d: 日期

    Returns:
        date: 下一个工作日
    """
    next_day = d + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day
