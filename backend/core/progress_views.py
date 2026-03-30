"""
进度追踪API视图
提供任务进度管理REST API
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.progress_tracker import progress_tracker
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


@extend_schema(
    summary='创建进度任务',
    description='创建一个新的进度追踪任务'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_progress_task(request):
    """
    创建新的进度任务

    POST /api/v1/progress/tasks/
    {
        "task_id": "unique_task_id",
        "task_name": "任务名称",
        "total_steps": 100,
        "description": "任务描述"
    }
    """
    data = request.data
    task_id = data.get('task_id')
    task_name = data.get('task_name', '未命名任务')
    total_steps = data.get('total_steps', 100)
    description = data.get('description', '')

    if not task_id:
        return Response({
            'success': False,
            'message': 'task_id 是必填字段'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        task = progress_tracker.create_task(
            task_id=task_id,
            task_name=task_name,
            total_steps=total_steps,
            description=description,
            created_by=request.user.username if hasattr(request.user, 'username') else 'unknown'
        )
        return Response({
            'success': True,
            'message': '任务已创建',
            'data': task
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return Response({
            'success': False,
            'message': f'创建任务失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary='获取任务状态',
    description='获取指定任务的当前状态'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    """
    获取任务状态

    GET /api/v1/progress/tasks/{task_id}/
    """
    task = progress_tracker.get_task_status(task_id)

    if task is None:
        return Response({
            'success': False,
            'message': '任务不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'success': True,
        'data': task
    })


@extend_schema(
    summary='开始任务',
    description='将任务状态设置为运行中'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_task(request, task_id):
    """
    开始任务

    POST /api/v1/progress/tasks/{task_id}/start/
    """
    success = progress_tracker.start_task(task_id)

    if not success:
        return Response({
            'success': False,
            'message': '任务不存在或已在运行'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '任务已开始'
    })


@extend_schema(
    summary='更新进度',
    description='更新任务的当前进度'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request, task_id):
    """
    更新任务进度

    POST /api/v1/progress/tasks/{task_id}/progress/
    {
        "current_step": 50,
        "progress": 50.0,
        "message": "正在处理..."
    }
    """
    data = request.data
    current_step = data.get('current_step', 0)
    progress = data.get('progress')
    message = data.get('message', '')

    success = progress_tracker.update_progress(
        task_id=task_id,
        current_step=current_step,
        progress=progress,
        message=message
    )

    if not success:
        return Response({
            'success': False,
            'message': '更新失败，任务可能不存在或已结束'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '进度已更新'
    })


@extend_schema(
    summary='完成任务',
    description='将任务标记为已完成'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_task(request, task_id):
    """
    完成任务

    POST /api/v1/progress/tasks/{task_id}/complete/
    {
        "result": {...}  // 可选的完成结果
    }
    """
    data = request.data
    result = data.get('result')

    success = progress_tracker.complete_task(task_id, result)

    if not success:
        return Response({
            'success': False,
            'message': '完成任务失败'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '任务已完成'
    })


@extend_schema(
    summary='手动结束任务',
    description='用户手动点击完成按钮结束任务（不允许自动超时结束）'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manually_end_task(request, task_id):
    """
    手动结束任务

    POST /api/v1/progress/tasks/{task_id}/end/
    {
        "result": {...}  // 可选的结果
    }
    """
    data = request.data
    result = data.get('result')

    task = progress_tracker.get_task_status(task_id)
    if task is None:
        return Response({
            'success': False,
            'message': '任务不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    if not task.get('can_manually_end', True):
        return Response({
            'success': False,
            'message': '此任务不允许手动结束'
        }, status=status.HTTP_400_BAD_REQUEST)

    if task.get('is_manually_ended'):
        return Response({
            'success': False,
            'message': '任务已被手动结束'
        }, status=status.HTTP_400_BAD_REQUEST)

    success = progress_tracker.manually_end_task(task_id, result)

    if not success:
        return Response({
            'success': False,
            'message': '手动结束失败'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '任务已手动结束'
    })


@extend_schema(
    summary='取消任务',
    description='取消正在运行的任务'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_task(request, task_id):
    """
    取消任务

    POST /api/v1/progress/tasks/{task_id}/cancel/
    """
    success = progress_tracker.cancel_task(task_id)

    if not success:
        return Response({
            'success': False,
            'message': '取消任务失败'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '任务已取消'
    })


@extend_schema(
    summary='失败任务',
    description='将任务标记为失败'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fail_task(request, task_id):
    """
    标记任务失败

    POST /api/v1/progress/tasks/{task_id}/fail/
    {
        "error": "错误信息"
    }
    """
    data = request.data
    error = data.get('error', '未知错误')

    success = progress_tracker.fail_task(task_id, error)

    if not success:
        return Response({
            'success': False,
            'message': '标记失败'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '任务已标记为失败'
    })


@extend_schema(
    summary='获取所有任务',
    description='获取当前所有进度任务'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tasks(request):
    """
    获取所有任务
    GET /api/v1/progress/tasks/
    """
    tasks = progress_tracker.get_all_tasks()
    return Response({
        'success': True,
        'data': list(tasks.values())
    })


@extend_schema(
    summary='删除任务',
    description='删除指定的进度任务（清理）'
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_task(request, task_id):
    """
    删除任务

    DELETE /api/v1/progress/tasks/{task_id}/
    """
    success = progress_tracker.remove_task(task_id)

    if not success:
        return Response({
            'success': False,
            'message': '删除失败'
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'message': '任务已删除'
    })