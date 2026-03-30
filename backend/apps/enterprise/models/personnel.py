"""
企业关键人员模型
"""
from django.db import models
from django.utils import timezone

from .base import Enterprise


class EnterpriseKeyPersonnel(models.Model):
    """
    企业关键人员模型 - 存储项目经理、技术负责人，专业工程师、八大员等关键人员信息
    """
    PERSONNEL_TYPE_CHOICES = [
        ('project_manager', '项目经理'),
        ('technical_director', '技术负责人'),
        ('professional_engineer', '专业工程师'),
        ('eight_officers', '八大员'),
    ]

    CERTIFICATE_STATUS_CHOICES = [
        ('valid', '有效'),
        ('expired', '已过期'),
        ('expiring', '即将过期'),
    ]

    TITLE_LEVEL_CHOICES = [
        ('senior', '高级'),
        ('intermediate', '中级'),
        ('junior', '初级'),
        ('assistant', '助理'),
    ]

    OFFICER_TYPE_CHOICES = [
        ('construction', '施工员'),
        ('quality', '质量员'),
        ('safety', '安全员'),
        ('standard', '标准员'),
        ('material', '材料员'),
        ('machinery', '机械员'),
        ('labor', '劳务员'),
        ('data', '资料员'),
    ]

    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.CASCADE,
        verbose_name='企业',
        related_name='key_personnel'
    )

    personnel_type = models.CharField('人员类型', max_length=30, choices=PERSONNEL_TYPE_CHOICES)
    officer_type = models.CharField('八大员类型', max_length=20, choices=OFFICER_TYPE_CHOICES, blank=True, null=True)

    personnel_id = models.CharField('人员唯一标识', max_length=50, unique=True, blank=True, null=True,
                                    help_text='系统自动生成的流水号或人员ID')
    name = models.CharField('姓名', max_length=100)
    id_number = models.CharField('身份证号', max_length=20, blank=True, null=True)
    birth_date = models.DateField('出生年月', blank=True, null=True)

    builder_certificate = models.CharField('建造师证书', max_length=200, blank=True, null=True)
    builder_certificate_file = models.FileField('建造师证书文件', upload_to='personnel/builder_cert/%Y/%m/',
                                              blank=True, null=True)
    safety_certificate_b = models.CharField('安全生产考核合格证B证', max_length=200, blank=True, null=True)
    safety_certificate_b_file = models.FileField('安全生产B证文件', upload_to='personnel/safety_cert/%Y/%m/',
                                                 blank=True, null=True)
    engineer_title_certificate = models.CharField('工程师职称证', max_length=200, blank=True, null=True)
    engineer_certificate_file = models.FileField('工程师职称证文件', upload_to='personnel/engineer_cert/%Y/%m/',
                                               blank=True, null=True)

    certificate_number = models.CharField('证书编号', max_length=100, blank=True, null=True)
    certificate_major = models.CharField('注册专业', max_length=100, blank=True, null=True)
    expiry_date = models.DateField('证书有效期', blank=True, null=True)

    issuing_authority = models.CharField('发证机关', max_length=200, blank=True, null=True)
    issuing_authority_full = models.CharField('发证单位全称', max_length=300, blank=True, null=True)

    title_level = models.CharField('职称等级', max_length=20, choices=TITLE_LEVEL_CHOICES, blank=True, null=True)

    social_security_proof = models.FileField('社保缴纳证明', upload_to='personnel/social_security/%Y/%m/',
                                             blank=True, null=True)
    no_ongoing_commitment = models.FileField('无在建承诺', upload_to='personnel/commitment/%Y/%m/',
                                             blank=True, null=True)
    labor_contract = models.FileField('劳动合同', upload_to='personnel/contract/%Y/%m/',
                                    blank=True, null=True)
    similar_performance_proof = models.FileField('类似业绩证明', upload_to='personnel/performance/%Y/%m/',
                                                blank=True, null=True)

    is_registered_locally = models.BooleanField('是否为本单位注册人员', default=True,
                                               help_text='用于系统自动比对住建部"四库一平台"数据')
    social_security_code = models.CharField('社保验证码', max_length=50, blank=True, null=True,
                                           help_text='部分地区社保系统支持生成带有验证码的电子社保证明')
    professional_years = models.IntegerField('从事本专业年限', blank=True, null=True,
                                          help_text='用于量化打分（如：10年以上得满分）')

    phone = models.CharField('联系电话', max_length=50, blank=True, null=True)
    email = models.EmailField('邮箱', max_length=100, blank=True, null=True)

    certificate_status = models.CharField('证书状态', max_length=20, choices=CERTIFICATE_STATUS_CHOICES, default='valid')
    is_available = models.BooleanField('是否可用', default=True, help_text='是否可用于投标')

    remarks = models.TextField('备注', blank=True, null=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'enterprise_key_personnel'
        verbose_name = '企业关键人员'
        verbose_name_plural = verbose_name
        ordering = ['personnel_type', '-is_available', 'name']
        indexes = [
            models.Index(fields=['enterprise', 'personnel_type']),
            models.Index(fields=['certificate_status']),
            models.Index(fields=['personnel_id']),
        ]

    def __str__(self):
        return f'{self.enterprise.name} - {self.get_personnel_type_display()} - {self.name}'

    def generate_personnel_id(self):
        """生成人员唯一标识"""
        import random
        import string
        prefix = {
            'project_manager': 'PM',
            'technical_director': 'TD',
            'professional_engineer': 'PE',
            'eight_officers': 'EO',
        }.get(self.personnel_type, 'XX')
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f'{prefix}{timestamp}{random_str}'

    def check_certificate_status(self):
        """检查证书状态"""
        from datetime import date, timedelta

        if not self.expiry_date:
            return 'valid'

        today = date.today()

        if self.expiry_date < today:
            return 'expired'
        elif self.expiry_date <= today + timedelta(days=30):
            return 'expiring'
        else:
            return 'valid'

    def save(self, *args, **kwargs):
        if not self.personnel_id:
            self.personnel_id = self.generate_personnel_id()
        self.certificate_status = self.check_certificate_status()
        super().save(*args, **kwargs)