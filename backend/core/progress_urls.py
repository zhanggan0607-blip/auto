"""
进度追踪API URL配置
"""
from django.urls import path
from . import progress_views

app_name = 'progress'

urlpatterns = [
    path('tasks/', progress_views.list_tasks, name='task-list'),
    path('tasks/create/', progress_views.create_progress_task, name='task-create'),
    path('tasks/<str:task_id>/', progress_views.get_task_status, name='task-detail'),
    path('tasks/<str:task_id>/start/', progress_views.start_task, name='task-start'),
    path('tasks/<str:task_id>/progress/', progress_views.update_progress, name='task-progress'),
    path('tasks/<str:task_id>/complete/', progress_views.complete_task, name='task-complete'),
    path('tasks/<str:task_id>/end/', progress_views.manually_end_task, name='task-end'),
    path('tasks/<str:task_id>/cancel/', progress_views.cancel_task, name='task-cancel'),
    path('tasks/<str:task_id>/fail/', progress_views.fail_task, name='task-fail'),
    path('tasks/<str:task_id>/delete/', progress_views.delete_task, name='task-delete'),
]