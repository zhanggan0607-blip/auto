"""
自定义异常类

提供统一的异常处理机制，便于前端识别和处理错误
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class BaseAPIException(APIException):
    """
    基础API异常类
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '请求处理失败'
    default_code = 'error'

    def __init__(self, detail=None, code=None, status_code=None):
        if detail is not None:
            self.detail = {'message': detail, 'code': code or self.default_code}
        else:
            self.detail = {'message': self.default_detail, 'code': self.default_code}
        
        if status_code is not None:
            self.status_code = status_code


class ValidationError(BaseAPIException):
    """
    数据验证错误
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '数据验证失败'
    default_code = 'validation_error'

    def __init__(self, detail=None, errors=None):
        if errors:
            self.detail = {
                'message': detail or self.default_detail,
                'code': self.default_code,
                'errors': errors
            }
        else:
            super().__init__(detail)


class AuthenticationFailed(BaseAPIException):
    """
    认证失败
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = '认证失败'
    default_code = 'authentication_failed'


class PermissionDenied(BaseAPIException):
    """
    权限不足
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '权限不足'
    default_code = 'permission_denied'


class NotFound(BaseAPIException):
    """
    资源不存在
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '资源不存在'
    default_code = 'not_found'


class ConflictError(BaseAPIException):
    """
    资源冲突
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = '资源冲突'
    default_code = 'conflict'


class RateLimitExceeded(BaseAPIException):
    """
    请求频率超限
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = '请求频率超限，请稍后再试'
    default_code = 'rate_limit_exceeded'


class InternalServerError(BaseAPIException):
    """
    服务器内部错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '服务器内部错误'
    default_code = 'internal_error'


class ServiceUnavailable(BaseAPIException):
    """
    服务不可用
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = '服务暂时不可用'
    default_code = 'service_unavailable'


class LLMServiceError(BaseAPIException):
    """
    LLM服务错误
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'AI模型服务暂时不可用'
    default_code = 'llm_service_error'


class CrawlerError(BaseAPIException):
    """
    爬虫错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '数据采集失败'
    default_code = 'crawler_error'


class DocumentGenerationError(BaseAPIException):
    """
    文档生成错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '文档生成失败'
    default_code = 'document_generation_error'


class QualificationMatchError(BaseAPIException):
    """
    资质匹配错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '资质匹配失败'
    default_code = 'qualification_match_error'


class EnterpriseConfigError(BaseAPIException):
    """
    企业配置错误
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '企业配置不完整'
    default_code = 'enterprise_config_error'


class VectorStoreError(BaseAPIException):
    """
    向量库错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '向量检索服务异常'
    default_code = 'vector_store_error'


class CacheError(BaseAPIException):
    """
    缓存错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '缓存服务异常'
    default_code = 'cache_error'


class DatabaseError(BaseAPIException):
    """
    数据库错误
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '数据库操作失败'
    default_code = 'database_error'


class ExternalAPIError(BaseAPIException):
    """
    外部API调用错误
    """
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = '外部服务调用失败'
    default_code = 'external_api_error'


class FileUploadError(BaseAPIException):
    """
    文件上传错误
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '文件上传失败'
    default_code = 'file_upload_error'


class FileSizeExceeded(BaseAPIException):
    """
    文件大小超限
    """
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = '文件大小超过限制'
    default_code = 'file_size_exceeded'


class UnsupportedMediaType(BaseAPIException):
    """
    不支持的媒体类型
    """
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = '不支持的文件类型'
    default_code = 'unsupported_media_type'


class BusinessLogicError(BaseAPIException):
    """
    业务逻辑错误
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '业务处理失败'
    default_code = 'business_logic_error'


class DuplicateError(BaseAPIException):
    """
    重复数据错误
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = '数据已存在'
    default_code = 'duplicate_error'


class OperationNotAllowed(BaseAPIException):
    """
    操作不允许
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '当前状态不允许此操作'
    default_code = 'operation_not_allowed'


class ResourceLocked(BaseAPIException):
    """
    资源被锁定
    """
    status_code = status.HTTP_423_LOCKED
    default_detail = '资源已被锁定，请稍后再试'
    default_code = 'resource_locked'
