"""
用户管理模块 - 服务层
"""
import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, UserLoginLog

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """
    用户服务类
    """
    
    @staticmethod
    @transaction.atomic
    def create_user(username, password, email=None, phone=None, real_name=None, 
                    company_name=None, role='user'):
        """
        创建用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            phone: 手机号
            real_name: 真实姓名
            company_name: 公司名称
            role: 角色
            
        Returns:
            User: 用户对象
        """
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            phone=phone,
            real_name=real_name,
            company_name=company_name,
            role=role
        )
        UserProfile.objects.create(user=user)
        logger.info(f"用户创建成功: {username}")
        return user
    
    @staticmethod
    @transaction.atomic
    def update_user(user_id, **kwargs):
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 更新字段
            
        Returns:
            User: 用户对象
        """
        user = User.objects.get(pk=user_id)
        
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.save()
        logger.info(f"用户信息更新成功: {user_id}")
        return user
    
    @staticmethod
    @transaction.atomic
    def delete_user(user_id):
        """
        删除用户（软删除）
        
        Args:
            user_id: 用户ID
        """
        user = User.objects.get(pk=user_id)
        user.is_active = False
        user.save()
        logger.info(f"用户已禁用: {user_id}")
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        根据ID获取用户
        """
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """
        根据用户名获取用户
        """
        try:
            return User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def generate_tokens(user):
        """
        生成用户Token
        
        Args:
            user: 用户对象
            
        Returns:
            dict: 包含access和refresh token
        """
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }


class UserProfileService:
    """
    用户详情服务类
    """
    
    @staticmethod
    def get_or_create_profile(user):
        """
        获取或创建用户详情
        """
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile
    
    @staticmethod
    @transaction.atomic
    def update_profile(user, **kwargs):
        """
        更新用户详情
        """
        profile = UserProfileService.get_or_create_profile(user)
        
        for field, value in kwargs.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        profile.save()
        return profile


class UserLoginLogService:
    """
    登录日志服务类
    """
    
    @staticmethod
    def create_login_log(user, request, status='success'):
        """
        创建登录日志
        
        Args:
            user: 用户对象
            request: 请求对象
            status: 登录状态
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        UserLoginLog.objects.create(
            user=user,
            login_ip=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_status=status
        )
    
    @staticmethod
    def get_user_login_logs(user, limit=10):
        """
        获取用户登录日志
        """
        return UserLoginLog.objects.filter(user=user).order_by('-login_time')[:limit]
