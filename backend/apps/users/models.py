"""
用户管理模块 - 数据模型
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('用户名不能为空')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True.')
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('user', '普通用户'),
    ]

    username = models.CharField('用户名', max_length=255, unique=True, db_index=True)
    email = models.EmailField('邮箱', max_length=255, blank=True, null=True)
    phone = models.CharField('手机号', max_length=20, blank=True, null=True)
    real_name = models.CharField('真实姓名', max_length=100, blank=True, null=True)
    company_name = models.CharField('公司名称', max_length=255, blank=True, null=True)
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='user')

    is_staff = models.BooleanField('员工状态', default=False)
    is_active = models.BooleanField('激活状态', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.is_staff or self.is_superuser


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户'
    )
    company_address = models.CharField('公司地址', max_length=500, blank=True, null=True)
    company_phone = models.CharField('公司电话', max_length=50, blank=True, null=True)
    business_license = models.CharField('营业执照号', max_length=100, blank=True, null=True)
    legal_person = models.CharField('法人代表', max_length=100, blank=True, null=True)
    bank_name = models.CharField('开户银行', max_length=200, blank=True, null=True)
    bank_account = models.CharField('银行账号', max_length=100, blank=True, null=True)
    qualification_info = models.JSONField('资质信息', default=dict, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = '用户详情'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username}的详情'


class UserLoginLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='login_logs',
        verbose_name='用户', null=True, blank=True
    )
    username = models.CharField('尝试用户名', max_length=150, blank=True, null=True)
    login_ip = models.GenericIPAddressField('登录IP', blank=True, null=True)
    login_time = models.DateTimeField('登录时间', default=timezone.now)
    user_agent = models.CharField('用户代理', max_length=500, blank=True, null=True)
    login_status = models.CharField('登录状态', max_length=20, default='success')

    class Meta:
        db_table = 'user_login_logs'
        verbose_name = '登录日志'
        verbose_name_plural = verbose_name
        ordering = ['-login_time']

    def __str__(self):
        username = self.username or (self.user.username if self.user else 'Unknown')
        return f'{username} - {self.login_time}'
