"""
自定义认证类
支持从httpOnly cookie中读取JWT Token
"""
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    支持从Cookie读取Token的JWT认证类

    认证顺序：
    1. Authorization Header (Bearer token)
    2. Cookie中的access_token

    对于AllowAny权限的视图，无效Token返回None而非抛异常
    """

    def authenticate(self, request):
        """
        认证请求
        优先从Authorization header读取，其次从cookie读取

        Args:
            request: Django请求对象

        Returns:
            tuple: (user, token) 或 None
        """
        header = self.get_header(request)

        if header is None:
            cookie_token = request.COOKIES.get('access_token')
            if cookie_token:
                header = f'Bearer {cookie_token}'.encode('utf-8')

        if header is None:
            return None

        raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            logger.debug(f'Token验证失败: {e}')
            return None
        except TokenError as e:
            logger.debug(f'Token验证失败: {e}')
            return None
        except Exception as e:
            logger.warning(f'Token验证异常: {e}')
            return None
