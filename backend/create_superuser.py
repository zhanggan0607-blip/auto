#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if User.objects.filter(username='admin').exists():
    print('Admin user already exists')
else:
    User.objects.create_superuser(username='admin', email='admin@bid-auto.com', password='Admin@2026auto')
    print('Superuser created: admin / Admin@2026auto')
