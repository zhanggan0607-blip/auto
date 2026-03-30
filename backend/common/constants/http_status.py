"""
HTTP状态码常量定义
统一HTTP状态码的使用
"""

from enum import Enum


class HttpStatus(Enum):
    """
    HTTP状态码枚举
    定义常用的HTTP状态码
    """

    # 1xx 信息性状态码
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    PROCESSING = 102

    # 2xx 成功状态码
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206
    MULTI_STATUS = 207
    ALREADY_REPORTED = 208
    IM_USED = 226

    # 3xx 重定向状态码
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    USE_PROXY = 305
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    # 4xx 客户端错误状态码
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    UNPROCESSABLE_ENTITY = 422
    LOCKED = 423
    FAILED_DEPENDENCY = 424
    UPGRADE_REQUIRED = 426
    PRECONDITION_REQUIRED = 428
    TOO_MANY_REQUESTS = 429
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    UNAVAILABLE_FOR_LEGAL_REASONS = 451

    # 5xx 服务器错误状态码
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    VARIANT_ALSO_NEGOTIATES = 506
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511


http_status_messages = {
    100: "继续",
    101: "切换协议",
    200: "OK",
    201: "已创建",
    202: "已接受",
    204: "无内容",
    301: "永久移动",
    302: "临时移动",
    304: "未修改",
    400: "请求错误",
    401: "未授权",
    403: "禁止访问",
    404: "未找到",
    405: "方法不允许",
    408: "请求超时",
    409: "冲突",
    410: "已删除",
    422: "无法处理的实体",
    429: "请求过多",
    500: "服务器内部错误",
    501: "未实现",
    502: "错误网关",
    503: "服务不可用",
    504: "网关超时",
}


def get_status_text(status_code: int) -> str:
    """
    获取HTTP状态码的文本描述

    Args:
        status_code: HTTP状态码

    Returns:
        str: 状态码描述
    """
    return http_status_messages.get(status_code, "未知状态")
