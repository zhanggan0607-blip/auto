"""
统一错误码定义
建立全系统统一的错误码体系

错误码格式：MODULE_ERROR_CODE
例如：AUTH_TOKEN_EXPIRED, USER_NOT_FOUND

使用方式：
    from common.constants.error_codes import ErrorCode, get_error_message

    raise BusinessError(ErrorCode.USER_NOT_FOUND, '用户不存在')
"""

from enum import Enum
from typing import Dict, Optional


class ErrorCode(Enum):
    """
    错误码枚举
    所有模块的错误码定义在此
    """

    SUCCESS = ("0", "成功", 200)

    # 通用错误 (1xxx)
    INTERNAL_ERROR = ("1000", "服务器内部错误", 500)
    INVALID_PARAMETER = ("1001", "参数无效", 400)
    MISSING_PARAMETER = ("1002", "缺少必要参数", 400)
    INVALID_FORMAT = ("1003", "格式错误", 400)
    NOT_FOUND = ("1004", "资源不存在", 404)
    ALREADY_EXISTS = ("1005", "资源已存在", 409)
    OPERATION_FAILED = ("1006", "操作失败", 400)
    TIMEOUT = ("1007", "操作超时", 408)
    PERMISSION_DENIED = ("1008", "权限不足", 403)
    RATE_LIMITED = ("1009", "请求过于频繁", 429)
    SERVICE_UNAVAILABLE = ("1010", "服务不可用", 503)

    # 认证授权错误 (2xxx)
    AUTH_TOKEN_EXPIRED = ("2001", "Token已过期", 401)
    AUTH_TOKEN_INVALID = ("2002", "Token无效", 401)
    AUTH_TOKEN_MISSING = ("2003", "Token缺失", 401)
    AUTH_CREDENTIALS_INVALID = ("2004", "用户名或密码错误", 401)
    AUTH_REFRESH_TOKEN_EXPIRED = ("2005", "刷新Token已过期", 401)
    AUTH_REFRESH_TOKEN_INVALID = ("2006", "刷新Token无效", 401)

    # 用户相关错误 (3xxx)
    USER_NOT_FOUND = ("3001", "用户不存在", 404)
    USER_DISABLED = ("3002", "用户已被禁用", 403)
    USER_ALREADY_EXISTS = ("3003", "用户已存在", 409)
    USER_PASSWORD_INVALID = ("3004", "密码格式不正确", 400)
    USER_PASSWORD_WRONG = ("3005", "密码错误", 401)
    USER_EMAIL_NOT_VERIFIED = ("3006", "邮箱未验证", 403)
    USER_PHONE_NOT_VERIFIED = ("3007", "手机号未验证", 403)

    # 企业相关错误 (4xxx)
    ENTERPRISE_NOT_FOUND = ("4001", "企业不存在", 404)
    ENTERPRISE_DISABLED = ("4002", "企业已被禁用", 403)
    ENTERPRISE_ALREADY_EXISTS = ("4003", "企业已存在", 409)
    ENTERPRISE_CREDIT_CODE_INVALID = ("4004", "统一社会信用代码格式错误", 400)
    ENTERPRISE_VERIFICATION_FAILED = ("4005", "企业认证失败", 400)
    QUALIFICATION_EXPIRED = ("4006", "资质已过期", 400)
    QUALIFICATION_NOT_FOUND = ("4007", "资质不存在", 404)

    # 招标相关错误 (5xxx)
    TENDER_NOT_FOUND = ("5001", "招标信息不存在", 404)
    TENDER_DEADLINE_PASSED = ("5002", "招标已截止", 400)
    TENDER_NOT_PUBLISHED = ("5003", "招标未发布", 400)
    TENDER_ALREADY_FAVORITED = ("5004", "招标已收藏", 409)
    TENDER_FAVORITE_NOT_FOUND = ("5005", "收藏不存在", 404)
    KEYWORD_NOT_FOUND = ("5006", "关键词不存在", 404)
    KEYWORD_ALREADY_EXISTS = ("5007", "关键词已存在", 409)

    # 投标相关错误 (6xxx)
    BID_NOT_FOUND = ("6001", "投标记录不存在", 404)
    BID_ALREADY_SUBMITTED = ("6002", "投标已提交", 409)
    BID_ALREADY_WITHDRAWN = ("6003", "投标已撤回", 400)
    BID_CANNOT_WITHDRAW = ("6004", "投标无法撤回", 400)
    BID_AMOUNT_INVALID = ("6005", "投标金额无效", 400)
    BID_STATUS_INVALID = ("6006", "投标状态不允许此操作", 400)

    # 文档相关错误 (7xxx)
    DOCUMENT_NOT_FOUND = ("7001", "文档不存在", 404)
    DOCUMENT_UPLOAD_FAILED = ("7002", "文档上传失败", 500)
    DOCUMENT_FORMAT_NOT_SUPPORTED = ("7003", "文档格式不支持", 400)
    DOCUMENT_TOO_LARGE = ("7004", "文档大小超限", 400)
    DOCUMENT_PARSE_FAILED = ("7005", "文档解析失败", 500)

    # 爬虫相关错误 (8xxx)
    CRAWLER_NOT_FOUND = ("8001", "爬虫不存在", 404)
    CRAWLER_RUNNING = ("8002", "爬虫正在运行中", 409)
    CRAWLER_FAILED = ("8003", "爬虫执行失败", 500)
    CRAWLER_PROXY_ERROR = ("8004", "代理连接失败", 500)
    CRAWLER_TIMEOUT = ("8005", "爬虫超时", 408)
    CRAWLER_BLOCKED = ("8006", "目标网站封锁", 403)

    # 调度器相关错误 (81xx)
    SCHEDULE_NOT_FOUND = ("8101", "采集计划不存在", 404)
    SCHEDULE_RUNNING = ("8102", "采集计划正在执行中", 409)
    SCHEDULE_DISABLED = ("8103", "采集计划已禁用", 400)
    SCHEDULE_INVALID_CRON = ("8104", "定时表达式无效", 400)
    SCHEDULE_TEMPLATE_NOT_FOUND = ("8105", "网站模板不存在", 404)
    SCHEDULE_EXECUTION_FAILED = ("8106", "采集执行失败", 500)
    QUALIFICATION_MATCH_FAILED = ("8107", "资质匹配执行失败", 500)

    # 向量库相关错误 (9xxx)
    VECTOR_NOT_FOUND = ("9001", "向量数据不存在", 404)
    VECTOR_SYNC_FAILED = ("9002", "向量同步失败", 500)
    VECTOR_SEARCH_FAILED = ("9003", "向量检索失败", 500)
    VECTOR_COLLECTION_NOT_FOUND = ("9004", "向量集合不存在", 404)
    EMBEDDING_FAILED = ("9005", "Embedding生成失败", 500)

    # 通知相关错误 (10xx)
    NOTIFICATION_CHANNEL_INVALID = ("10001", "通知渠道无效", 400)
    NOTIFICATION_SEND_FAILED = ("10002", "通知发送失败", 500)
    NOTIFICATION_TEMPLATE_NOT_FOUND = ("10003", "通知模板不存在", 404)

    # LLM相关错误 (11xx)
    LLM_PROVIDER_NOT_FOUND = ("11001", "LLM提供商不存在", 404)
    LLM_MODEL_NOT_FOUND = ("11002", "LLM模型不存在", 404)
    LLM_API_ERROR = ("11003", "LLM API调用失败", 500)
    LLM_RESPONSE_INVALID = ("11004", "LLM响应无效", 500)
    LLM_TIMEOUT = ("11005", "LLM调用超时", 408)

    # 文件存储相关错误 (12xx)
    STORAGE_UPLOAD_FAILED = ("12001", "文件上传失败", 500)
    STORAGE_DOWNLOAD_FAILED = ("12002", "文件下载失败", 500)
    STORAGE_FILE_NOT_FOUND = ("12003", "存储文件不存在", 404)
    STORAGE_CAPACITY_EXCEEDED = ("12004", "存储容量超限", 400)

    def __init__(self, code: str, message: str, http_status: int):
        self.code = code
        self.message = message
        self.http_status = http_status


_error_code_mapping: Dict[str, ErrorCode] = {
    e.value[0]: e for e in ErrorCode
}


def get_error_by_code(code: str) -> Optional[ErrorCode]:
    """根据错误码获取ErrorCode枚举"""
    return _error_code_mapping.get(code)


def get_error_message(code: str, custom_message: str = None) -> str:
    """
    获取错误信息

    Args:
        code: 错误码
        custom_message: 自定义错误信息

    Returns:
        str: 错误信息
    """
    error = get_error_by_code(code)
    if error:
        return custom_message or error.message
    return custom_message or "未知错误"


def get_http_status(code: str) -> int:
    """
    获取错误码对应的HTTP状态码

    Args:
        code: 错误码

    Returns:
        int: HTTP状态码
    """
    error = get_error_by_code(code)
    if error:
        return error.http_status
    return 500
