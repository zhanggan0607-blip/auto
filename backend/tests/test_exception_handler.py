"""
异常处理模块单元测试
"""
import pytest
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from utils.exception_handler import (
    api_exception_handler,
    catch_and_log,
    ExceptionHandlerContext,
    ErrorContext,
)


class TestAPIExceptionHandler:
    """
    API异常处理装饰器测试
    """

    def test_success_case(self):
        """
        测试正常执行
        """
        @api_exception_handler
        def success_func():
            return {'code': 0, 'data': 'success'}

        result = success_func()
        assert result.data['code'] == 0
        assert result.data['data'] == 'success'

    def test_validation_error(self):
        """
        测试验证错误
        """
        @api_exception_handler
        def validation_error_func():
            raise ValidationError({'field': ['Invalid value']})

        result = validation_error_func()
        assert result.status_code == status.HTTP_400_BAD_REQUEST

    def test_not_found_error(self):
        """
        测试资源不存在错误
        """
        @api_exception_handler
        def not_found_func():
            raise NotFound('Resource not found')

        result = not_found_func()
        assert result.status_code == status.HTTP_404_NOT_FOUND

    def test_permission_denied_error(self):
        """
        测试权限拒绝错误
        """
        @api_exception_handler
        def permission_denied_func():
            raise PermissionDenied('Permission denied')

        result = permission_denied_func()
        assert result.status_code == status.HTTP_403_FORBIDDEN

    def test_generic_error(self):
        """
        测试通用错误
        """
        @api_exception_handler
        def generic_error_func():
            raise Exception('Something went wrong')

        result = generic_error_func()
        assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestCatchAndLog:
    """
    错误记录装饰器测试
    """
    
    def test_success_case(self):
        """
        测试正常执行
        """
        @catch_and_log(scenario="测试场景", reraise=False)
        def success_func():
            return 'success'
        
        result = success_func()
        assert result == 'success'
    
    def test_error_case_reraise_false(self):
        """
        测试错误处理（不重新抛出）
        """
        @catch_and_log(scenario="测试场景", reraise=False, return_on_error='error')
        def error_func():
            raise ValueError('Test error')
        
        result = error_func()
        assert result == 'error'
    
    def test_error_case_reraise_true(self):
        """
        测试错误处理（重新抛出）
        """
        @catch_and_log(scenario="测试场景", reraise=True)
        def error_func():
            raise ValueError('Test error')
        
        with pytest.raises(ValueError):
            error_func()


class TestExceptionHandlerContext:
    """
    API异常处理上下文管理器测试
    """
    
    def test_success_case(self):
        """
        测试正常执行
        """
        with ExceptionHandlerContext('test_func') as ctx:
            result = 'success'
        
        assert ctx.exception is None
        assert result == 'success'
    
    def test_error_case(self):
        """
        测试异常捕获
        """
        with ExceptionHandlerContext('test_func') as ctx:
            raise ValueError('Test error')
        
        assert ctx.exception is not None
        assert isinstance(ctx.exception, ValueError)
        
        response = ctx.get_response()
        assert response is not None
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestErrorContext:
    """
    错误上下文管理器测试
    """
    
    def test_success_case(self):
        """
        测试正常执行
        """
        with ErrorContext("测试场景", "测试解决方案"):
            result = 'success'
        
        assert result == 'success'
    
    def test_error_case_reraise_false(self):
        """
        测试异常捕获（不重新抛出）
        """
        with ErrorContext("测试场景", "测试解决方案", reraise=False):
            raise ValueError('Test error')
    
    def test_error_case_reraise_true(self):
        """
        测试异常捕获（重新抛出）
        """
        with pytest.raises(ValueError):
            with ErrorContext("测试场景", "测试解决方案", reraise=True):
                raise ValueError('Test error')
