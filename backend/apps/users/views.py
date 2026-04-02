"""
用户管理模块 - 视图
"""
import os
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
from utils.responses import APIResponse
from utils.helpers import get_client_ip

User = get_user_model()


class CookieTokenRefreshView(APIView):
    """
    Token刷新视图
    支持从httpOnly cookie中读取refresh token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        刷新access token
        优先从cookie中读取refresh token
        """
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
        
        if not refresh_token:
            return APIResponse.error(
                message='Refresh token不存在，请重新登录',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            
            response = APIResponse.success(
                data={'access': access_token},
                message='Token刷新成功'
            )
            
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60 * 60 * 24,
                path='/'
            )
            
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Token刷新失败: {str(e)}')
            return APIResponse.error(
                message=f'Token刷新失败: {str(e)}',
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class UserRegisterView(generics.CreateAPIView):
    """
    用户注册视图
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

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
        return APIResponse.success(
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
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        用户登录
        将Token存储在httpOnly cookie中，提高安全性
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(username=username, password=password)

        if user is None:
            return APIResponse.error(message='用户名或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return APIResponse.error(message='用户已被禁用', status_code=status.HTTP_403_FORBIDDEN)

        UserLoginLog.objects.create(
            user=user,
            login_ip=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_status='success'
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        is_secure = request.is_secure() or os.getenv('COOKIE_SECURE', 'false').lower() == 'true'

        response = APIResponse.success(
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
    permission_classes = [IsAuthenticated]

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
        except Exception:
            pass
        
        response = APIResponse.success(message='登出成功')
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
            return APIResponse.error(message='无权限修改此用户', status_code=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(data=UserSerializer(instance).data, message='更新成功')

    def destroy(self, request, *args, **kwargs):
        """
        删除用户
        """
        instance = self.get_object()
        
        if not request.user.is_admin():
            return APIResponse.error(message='无权限删除用户', status_code=status.HTTP_403_FORBIDDEN)

        instance.is_active = False
        instance.save()
        return APIResponse.success(message='用户已禁用')


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    用户详情视图
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        获取当前用户的详情
        """
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


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
        return APIResponse.success(data=serializer.data)


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


class PasswordChangeView(APIView):
    """
    密码修改视图
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        修改密码
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(message='密码修改成功')


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
            return APIResponse.error(message='用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is None:
            return APIResponse.error(message='缺少is_active参数', status_code=status.HTTP_400_BAD_REQUEST)

        user.is_active = is_active
        user.save()
        return APIResponse.success(data=UserSerializer(user).data, message=f'用户已{"启用" if is_active else "禁用"}')


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
            return APIResponse.error(message='用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        default_password = 'tianqi123456'
        user.set_password(default_password)
        user.save()
        return APIResponse.success(message=f'密码已重置为默认密码')
