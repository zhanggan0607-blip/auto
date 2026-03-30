"""
用户管理模块 - URL路由
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegisterView, UserLoginView, UserLogoutView,
    UserListView, UserDetailView, UserProfileView,
    CurrentUserView, UserLoginLogListView, PasswordChangeView,
    CookieTokenRefreshView, UserToggleStatusView, UserResetPasswordView
)

app_name = 'users'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('token/refresh/body/', TokenRefreshView.as_view(), name='token_refresh_body'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('me/profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('login-logs/', UserLoginLogListView.as_view(), name='login_logs'),
    path('', UserListView.as_view(), name='user_list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/toggle_status/', UserToggleStatusView.as_view(), name='user_toggle_status'),
    path('<int:pk>/reset_password/', UserResetPasswordView.as_view(), name='user_reset_password'),
]
