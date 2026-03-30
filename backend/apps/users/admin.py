from django.contrib import admin
from .models import User, UserProfile, UserLoginLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'company_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'legal_person', 'created_at']
    search_fields = ['user__username']


@admin.register(UserLoginLog)
class UserLoginLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_ip', 'login_time', 'login_status']
    list_filter = ['login_status']
    search_fields = ['user__username', 'login_ip']
    readonly_fields = ['user', 'login_ip', 'login_time', 'user_agent', 'login_status']
