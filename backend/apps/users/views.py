"""
用户管理模块 - 视图
"""
import os
import time
import logging
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.db import transaction

from .models import UserProfile, UserLoginLog
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserProfileSerializer, LoginSerializer, UserLoginLogSerializer,
    PasswordChangeSerializer
)
from utils.permissions import IsAdminUser
from utils.responses import UnifiedResponse
from utils.helpers import get_client_ip
from core.throttling import LoginRateThrottle, TokenRefreshRateThrottle
from django.core.cache import cache

User = get_user_model()

logger = logging.getLogger(__name__)

LOGIN_FAILURE_THRESHOLD = 5
LOGIN_FAILURE_WINDOW = 15 * 60
LOGIN_LOCKOUT_DURATION = 15 * 60


def get_user_failure_key(username):
    return f"login_failure_{username}"


def get_ip_failure_key(ip):
    return f"login_failure_ip_{ip}"


def get_user_lockout_key(username):
    return f"login_lockout_{username}"


def get_ip_lockout_key(ip):
    return f"login_lockout_ip_{ip}"


def is_login_locked(username, ip):
    user_lockout_key = get_user_lockout_key(username)
    ip_lockout_key = get_ip_lockout_key(ip)

    user_lockout_expiry = cache.get(user_lockout_key)
    if user_lockout_expiry and user_lockout_expiry > time.time():
        return True, int(user_lockout_expiry - time.time())

    ip_lockout_expiry = cache.get(ip_lockout_key)
    if ip_lockout_expiry and ip_lockout_expiry > time.time():
        return True, int(ip_lockout_expiry - time.time())

    failure_key = get_user_failure_key(username)
    ip_key = get_ip_failure_key(ip)
    failure_count = cache.get(failure_key, 0)
    ip_count = cache.get(ip_key, 0)

    if failure_count >= LOGIN_FAILURE_THRESHOLD:
        lockout_expiry = time.time() + LOGIN_LOCKOUT_DURATION
        cache.set(user_lockout_key, lockout_expiry, LOGIN_LOCKOUT_DURATION)
        cache.delete(failure_key)
        return True, LOGIN_LOCKOUT_DURATION

    if ip_count >= LOGIN_FAILURE_THRESHOLD * 3:
        lockout_expiry = time.time() + LOGIN_LOCKOUT_DURATION
        cache.set(ip_lockout_key, lockout_expiry, LOGIN_LOCKOUT_DURATION)
        cache.delete(ip_key)
        return True, LOGIN_LOCKOUT_DURATION

    return False, 0


def record_login_failure(username, ip):
    failure_key = get_user_failure_key(username)
    ip_key = get_ip_failure_key(ip)
    try:
        cache.incr(failure_key)
    except ValueError:
        cache.set(failure_key, 1, LOGIN_FAILURE_WINDOW)
    try:
        cache.incr(ip_key)
    except ValueError:
        cache.set(ip_key, 1, LOGIN_FAILURE_WINDOW)


def clear_login_failures(username, ip=None):
    failure_key = get_user_failure_key(username)
    lockout_key = get_user_lockout_key(username)
    cache.delete(failure_key)
    cache.delete(lockout_key)
    if ip:
        ip_failure_key = get_ip_failure_key(ip)
        ip_lockout_key = get_ip_lockout_key(ip)
        cache.delete(ip_failure_key)
        cache.delete(ip_lockout_key)


class CookieTokenRefreshView(APIView):
    """
    Token刷新视图
    支持从httpOnly cookie中读取refresh token
    处理ROTATE_REFRESH_TOKENS: 每次刷新后生成新的refresh token并更新Cookie
    """
    permission_classes = [AllowAny]
    throttle_classes = [TokenRefreshRateThrottle]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
        
        if not refresh_token:
            return UnifiedResponse.error(
                message='Refresh token不存在，请重新登录',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            old_refresh = RefreshToken(refresh_token)
            user = old_refresh.get('user_id')
            
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                old_refresh.blacklist()
            
            new_refresh = RefreshToken.for_user(User.objects.get(pk=user))
            access_token = str(new_refresh.access_token)
            new_refresh_token = str(new_refresh)
            
            is_secure = request.is_secure() or os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
            
            response = UnifiedResponse.success(
                data={'access': access_token},
                message='Token刷新成功'
            )
            
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=is_secure,
                samesite='Lax',
                max_age=60 * 60 * 24,
                path='/'
            )
            
            response.set_cookie(
                key='refresh_token',
                value=new_refresh_token,
                httponly=True,
                secure=is_secure,
                samesite='Lax',
                max_age=60 * 60 * 24 * 7,
                path='/'
            )
            
            return response
        except Exception as e:
            logger.warning(f'Token刷新失败: {str(e)}')
            return UnifiedResponse.error(
                message='Token刷新失败，请重新登录',
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class UserRegisterView(generics.CreateAPIView):
    """
    用户注册视图
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def create(self, request, *args, **kwargs):
        """
        创建用户并返回token
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            UserProfile.objects.get_or_create(user=user)
        
        refresh = RefreshToken.for_user(user)
        return UnifiedResponse.success(
            data={
                'user': UserSerializer(user).data,
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            },
            message='注册成功',
            status_code=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    """
    用户登录视图
    支持httpOnly cookie存储Token
    添加登录失败锁定机制防止暴力破解
    """
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        """
        用户登录
        将Token存储在httpOnly cookie中，提高安全性
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        client_ip = get_client_ip(request)

        locked, remaining_seconds = is_login_locked(username, client_ip)
        if locked:
            remaining_minutes = max(1, remaining_seconds // 60)
            return UnifiedResponse.error(
                message=f'登录失败次数过多，账户已被锁定，请在{remaining_minutes}分钟后重试',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        user = authenticate(username=username, password=password)

        if user is None:
            record_login_failure(username, client_ip)
            UserLoginLog.objects.create(
                user=None,
                username=username,
                login_ip=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_status='failed'
            )
            return UnifiedResponse.error(message='用户名或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            record_login_failure(username, client_ip)
            return UnifiedResponse.error(message='用户已被禁用', status_code=status.HTTP_403_FORBIDDEN)

        clear_login_failures(username, client_ip)

        UserLoginLog.objects.create(
            user=user,
            login_ip=client_ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_status='success'
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        is_secure = request.is_secure() or os.getenv('COOKIE_SECURE', 'false').lower() == 'true'

        response = UnifiedResponse.success(
            data={
                'user': UserSerializer(user).data,
                'token': {
                    'access': access_token,
                    'refresh': refresh_token
                }
            },
            message='登录成功'
        )

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite='Lax',
            max_age=60 * 60 * 24,
            path='/'
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,
            path='/'
        )

        return response


class UserLogoutView(APIView):
    """
    用户登出视图
    清除httpOnly cookie中的Token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        用户登出
        清除cookie中的Token并使refresh token失效
        """
        try:
            refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            logger.warning(f'Token黑名单操作失败: {str(e)}')
        
        response = UnifiedResponse.success(message='登出成功')
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


class UserListView(generics.ListAPIView):
    """
    用户列表视图
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """
        支持搜索过滤，默认只显示启用用户
        """
        queryset = super().get_queryset()
        username = self.request.query_params.get('username')
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')

        if username:
            queryset = queryset.filter(username__icontains=username)
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        else:
            queryset = queryset.filter(is_active=True)

        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    用户详情视图
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        根据请求方法选择序列化器
        """
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        """
        更新用户信息
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if not request.user.is_admin() and request.user.id != instance.id:
            return UnifiedResponse.error(message='无权限修改此用户', status_code=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=UserSerializer(instance).data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        """
        删除用户
        """
        instance = self.get_object()
        
        if not request.user.is_admin():
            return UnifiedResponse.error(message='无权限删除用户', status_code=status.HTTP_403_FORBIDDEN)

        instance.is_active = False
        instance.save()
        return UnifiedResponse.success(message='用户已禁用')

class CurrentUserView(APIView):
    """
    当前用户信息视图
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取当前用户信息
        """
        serializer = UserSerializer(request.user)
        return UnifiedResponse.success(data=serializer.data)

    def patch(self, request):
        """
        更新当前用户信息
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=UserSerializer(request.user).data, message='更新成功')

    def patch(self, request):
        """
        更新当前用户信息
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return UnifiedResponse.success(data=UserSerializer(request.user).data, message='更新成功')


class UserLoginLogListView(generics.ListAPIView):
    """
    登录日志列表视图
    """
    serializer_class = UserLoginLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        获取当前用户的登录日志
        """
        if self.request.user.is_admin():
            return UserLoginLog.objects.all()
        return UserLoginLog.objects.filter(user=self.request.user)

class UserToggleStatusView(APIView):
    """
    用户启用/禁用视图
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        """
        切换用户状态
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return UnifiedResponse.error(message='用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is None:
            return UnifiedResponse.error(message='缺少is_active参数', status_code=status.HTTP_400_BAD_REQUEST)

        user.is_active = is_active
        user.save()
        return UnifiedResponse.success(data=UserSerializer(user).data, message=f'用户已{"启用" if is_active else "禁用"}')


class UserResetPasswordView(APIView):
    """
    用户密码重置视图
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        """
        重置用户密码为默认密码
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return UnifiedResponse.error(message='用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        default_password = settings.DEFAULT_PASSWORD
        user.set_password(default_password)
        user.save()
        return UnifiedResponse.success(message=f'密码已重置为默认密码')


class AccountUnlockView(APIView):
    """
    管理员解锁账户视图
    清除指定用户的登录失败计数和锁定状态
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return UnifiedResponse.error(message='用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        clear_login_failures(user.username)
        return UnifiedResponse.success(message=f'账户 {user.username} 已解锁')
