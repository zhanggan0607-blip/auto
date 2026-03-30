import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print('管理员用户已创建: admin / admin123')
else:
    print('管理员用户已存在')
    user = User.objects.get(username='admin')
    print(f'用户: {user.username}, 邮箱: {user.email}, 是否激活: {user.is_active}, 是否超级用户: {user.is_superuser}')
