"""
用户管理模块 - 序列化器（优化版）
"""
import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import UserProfile, UserLoginLog
from common.serializers.validators import validate_phone

User = get_user_model()


def validate_email(value):
    """
    验证邮箱格式
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if value and not re.match(pattern, value):
        raise ValidationError('请输入正确的邮箱地址')
    return value


def validate_password_strength(value):
    """
    验证密码强度
    """
    if len(value) < 8:
        raise ValidationError('密码长度不能少于8位')
    if len(value) > 32:
        raise ValidationError('密码长度不能超过32位')
    if not re.search(r'[A-Za-z]', value):
        raise ValidationError('密码必须包含字母')
    if not re.search(r'\d', value):
        raise ValidationError('密码必须包含数字')
    return value


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'real_name', 
            'company_name', 'role', 'is_active', 'is_staff', 'is_superuser',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_staff', 'is_superuser']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    用户创建序列化器
    """
    password = serializers.CharField(write_only=True, min_length=8, max_length=32)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=11)
    
    class Meta:
        model = User
        fields = [
            'username', 'password', 'password_confirm', 'email', 
            'phone', 'real_name', 'company_name', 'role'
        ]
    
    def validate_username(self, value):
        """
        验证用户名
        """
        if len(value) < 3:
            raise serializers.ValidationError('用户名长度不能少于3位')
        if len(value) > 20:
            raise serializers.ValidationError('用户名长度不能超过20位')
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError('用户名只能包含字母、数字和下划线')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value
    
    def validate_phone(self, value):
        """
        验证手机号
        """
        if value:
            validate_phone(value)
            if User.objects.filter(phone=value).exists():
                raise serializers.ValidationError('该手机号已被注册')
        return value
    
    def validate_email(self, value):
        """
        验证邮箱
        """
        if value:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError('该邮箱已被注册')
        return value
    
    def validate_password(self, value):
        """
        验证密码强度
        """
        validate_password_strength(value)
        return value
    
    def validate(self, attrs):
        """
        验证密码是否一致
        """
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': '两次密码输入不一致'})
        return attrs
    
    def create(self, validated_data):
        """
        创建用户
        """
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    用户更新序列化器
    """
    phone = serializers.CharField(required=False, allow_blank=True, max_length=11)
    
    class Meta:
        model = User
        fields = ['email', 'phone', 'real_name', 'company_name']
    
    def validate_phone(self, value):
        """
        验证手机号
        """
        if value:
            validate_phone(value)
            user = self.instance
            if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError('该手机号已被其他用户使用')
        return value
    
    def validate_email(self, value):
        """
        验证邮箱
        """
        if value:
            user = self.instance
            if User.objects.filter(email=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError('该邮箱已被其他用户使用')
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    密码修改序列化器
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8, max_length=32)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        """
        验证旧密码
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码错误')
        return value
    
    def validate_new_password(self, value):
        """
        验证新密码强度
        """
        validate_password_strength(value)
        return value
    
    def validate(self, attrs):
        """
        验证新密码是否一致
        """
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({'new_password_confirm': '两次密码输入不一致'})
        if attrs.get('old_password') == attrs.get('new_password'):
            raise serializers.ValidationError({'new_password': '新密码不能与原密码相同'})
        return attrs
    
    def save(self):
        """
        保存新密码
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户详情序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='user.company_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'company_name', 'company_address', 'company_phone',
            'business_license', 'legal_person', 'bank_name', 'bank_account',
            'qualification_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_bank_account(self, value):
        """
        验证银行账号
        """
        if value and not re.match(r'^\d{16,19}$', value):
            raise serializers.ValidationError('请输入正确的银行账号')
        return value
    
    def validate_company_phone(self, value):
        """
        验证公司电话
        """
        if value and not re.match(r'^[\d\-]+$', value):
            raise serializers.ValidationError('请输入正确的电话号码')
        return value


class LoginSerializer(serializers.Serializer):
    """
    登录序列化器
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate_username(self, value):
        """
        验证用户名
        """
        if len(value) < 1:
            raise serializers.ValidationError('请输入用户名')
        return value
    
    def validate_password(self, value):
        """
        验证密码
        """
        if len(value) < 1:
            raise serializers.ValidationError('请输入密码')
        return value


class UserLoginLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    login_ip = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = UserLoginLog
        fields = ['id', 'username', 'login_ip', 'login_time', 'login_status']
