"""
采集完成通知服务
在每次网页数据采集任务完成后，自动生成并发送站内通知给系统管理员
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class CrawlCompletionNotificationService:
    """
    采集完成通知服务
    
    在采集任务完成后，自动生成格式化的站内通知，发送给系统管理员。
    通知包含：采集URL、成功数量、失败数量、失败原因明细等。
    """
    
    @staticmethod
    def send_crawl_completion_notification(
        schedule_id: int,
        schedule_name: str,
        target_url: str,
        result_count: int,
        saved_count: int,
        recognized_count: int = 0,
        recognition_errors: int = 0,
        matched_count: int = 0,
        deleted_count: int = 0,
        error_message: Optional[str] = None,
        duration: Optional[float] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        发送采集完成通知
        
        Args:
            schedule_id: 采集计划ID
            schedule_name: 采集计划名称
            target_url: 目标网站URL
            result_count: 采集到的总数据条数
            saved_count: 成功保存到招标项目的数量
            recognized_count: 内容识别成功数量
            recognition_errors: 内容识别失败数量
            matched_count: 资质匹配成功数量
            deleted_count: 自动删除的不匹配数量
            error_message: 错误信息（如果有）
            duration: 耗时（秒）
            started_at: 开始时间
            finished_at: 结束时间
            details: 其他详细信息
            
        Returns:
            发送成功的通知数量
        """
        try:
            from apps.notifications.models import Notification
            from apps.users.models import User
            from core.constants import (
                NOTIFICATION_TYPE_CRAWL_COMPLETED,
                PRIORITY_NORMAL,
                PRIORITY_HIGH,
            )
            
            title = CrawlCompletionNotificationService._build_title(
                schedule_name=schedule_name,
                result_count=result_count,
                has_error=bool(error_message)
            )
            
            content = CrawlCompletionNotificationService._build_content(
                schedule_id=schedule_id,
                schedule_name=schedule_name,
                target_url=target_url,
                result_count=result_count,
                saved_count=saved_count,
                recognized_count=recognized_count,
                recognition_errors=recognition_errors,
                matched_count=matched_count,
                deleted_count=deleted_count,
                error_message=error_message,
                duration=duration,
                started_at=started_at,
                finished_at=finished_at,
                details=details,
            )
            
            recipients = User.objects.filter(is_active=True, is_staff=True)
            if not recipients.exists():
                recipients = User.objects.filter(is_active=True, is_superuser=True)
            if not recipients.exists():
                recipients = User.objects.filter(is_active=True)[:3]
            
            priority = PRIORITY_HIGH if error_message else PRIORITY_NORMAL
            
            sent_count = 0
            for recipient in recipients:
                Notification.objects.create(
                    title=title,
                    content=content,
                    notification_type=NOTIFICATION_TYPE_CRAWL_COMPLETED,
                    priority=priority,
                    related_object_type='crawl_schedule',
                    related_object_id=schedule_id,
                    recipient=recipient,
                    is_sent=True,
                    sent_at=timezone.now(),
                    sent_channels=['in_system'],
                )
                sent_count += 1
            
            logger.info(f'采集完成通知已发送: {title}, 接收人{sent_count}个')
            return sent_count
            
        except Exception as e:
            logger.error(f'发送采集完成通知失败: {str(e)}')
            return 0
    
    @staticmethod
    def send_crawler_task_notification(
        task_id: int,
        task_name: str,
        source_code: str,
        source_url: str,
        result_count: int,
        total_count: int = 0,
        error_message: Optional[str] = None,
        task_errors: Optional[List[Dict[str, Any]]] = None,
        duration: Optional[float] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> int:
        """
        发送简单爬虫任务完成通知（用于 execute_crawler_task 路径）
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            source_code: 数据来源代码
            source_url: 来源URL
            result_count: 保存的结果数量
            total_count: 采集到的总数据条数
            error_message: 错误信息（如果有）
            task_errors: 错误详情列表
            duration: 耗时（秒）
            started_at: 开始时间
            finished_at: 结束时间
            
        Returns:
            发送成功的通知数量
        """
        try:
            from apps.notifications.models import Notification
            from apps.users.models import User
            from core.constants import (
                NOTIFICATION_TYPE_CRAWL_COMPLETED,
                PRIORITY_NORMAL,
                PRIORITY_HIGH,
            )
            
            title = f"【采集任务完成】{task_name}"
            if error_message:
                title = f"【采集任务失败】{task_name}"
            
            failed_count = len(task_errors) if task_errors else 0
            actual_total = total_count if total_count > 0 else result_count + failed_count
            success_rate = (result_count / actual_total * 100) if actual_total > 0 else 0
            
            content_lines = [
                "## 采集任务执行报告",
                "",
                "---",
                "",
                "### 📊 统计摘要",
                "",
                "| 指标 | 数量 |",
                "|------|------|",
                f"| 采集总数 | **{actual_total}** 条 |",
                f"| 成功保存 | **{result_count}** 条 |",
                f"| 失败数量 | **{failed_count}** 条 |",
                f"| 成功率 | **{success_rate:.1f}%** |",
                "",
                "---",
                "",
                "### 📋 基本信息",
                "",
                f"- **任务名称**: {task_name}",
                f"- **数据来源**: {source_code}",
                f"- **来源URL**: [{source_url}]({source_url})" if source_url else "- **来源URL**: 未指定",
            ]
            
            if started_at:
                content_lines.append(f"- **开始时间**: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if finished_at:
                content_lines.append(f"- **结束时间**: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if duration:
                if duration < 60:
                    content_lines.append(f"- **总耗时**: {duration:.1f} 秒")
                else:
                    minutes = int(duration // 60)
                    seconds = duration % 60
                    content_lines.append(f"- **总耗时**: {minutes} 分 {seconds:.1f} 秒")
            
            if error_message:
                content_lines.extend([
                    "",
                    "---",
                    "",
                    "### ❌ 错误信息",
                    "",
                    f"```\n{error_message}\n```",
                ])
            
            if task_errors:
                content_lines.extend([
                    "",
                    "---",
                    "",
                    "### ⚠️ 失败详情",
                    "",
                ])
                for i, err in enumerate(task_errors[:10], 1):
                    err_time = err.get('timestamp', '未知时间')
                    err_type = err.get('error_type', '未知错误')
                    err_title = err.get('title', '')
                    err_msg = err.get('message', str(err))[:100]
                    content_lines.append(f"{i}. [{err_time}] {err_type}: {err_title} - {err_msg}")
                
                if len(task_errors) > 10:
                    content_lines.append(f"\n*...还有 {len(task_errors) - 10} 条错误未显示*")
            
            content_lines.extend([
                "",
                "---",
                "",
                f"*通知时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ])
            
            content = "\n".join(content_lines)
            
            recipients = User.objects.filter(is_active=True, is_staff=True)
            if not recipients.exists():
                recipients = User.objects.filter(is_active=True, is_superuser=True)
            if not recipients.exists():
                recipients = User.objects.filter(is_active=True)[:3]
            
            priority = PRIORITY_HIGH if error_message else PRIORITY_NORMAL
            
            sent_count = 0
            for recipient in recipients:
                Notification.objects.create(
                    title=title,
                    content=content,
                    notification_type=NOTIFICATION_TYPE_CRAWL_COMPLETED,
                    priority=priority,
                    related_object_type='crawler_task',
                    related_object_id=task_id,
                    recipient=recipient,
                    is_sent=True,
                    sent_at=timezone.now(),
                    sent_channels=['in_system'],
                )
                sent_count += 1
            
            logger.info(f'爬虫任务完成通知已发送: {title}, 接收人{sent_count}个')
            return sent_count
            
        except Exception as e:
            logger.error(f'发送爬虫任务完成通知失败: {str(e)}')
            return 0
    
    @staticmethod
    def _build_title(
        schedule_name: str,
        result_count: int,
        has_error: bool,
    ) -> str:
        """构建通知标题"""
        if has_error:
            return f"【采集失败】{schedule_name}"
        elif result_count == 0:
            return f"【采集完成·无数据】{schedule_name}"
        else:
            return f"【采集完成】{schedule_name} - 成功 {result_count} 条"
    
    @staticmethod
    def _build_content(
        schedule_id: int,
        schedule_name: str,
        target_url: str,
        result_count: int,
        saved_count: int,
        recognized_count: int,
        recognition_errors: int,
        matched_count: int,
        deleted_count: int,
        error_message: Optional[str],
        duration: Optional[float],
        started_at: Optional[datetime],
        finished_at: Optional[datetime],
        details: Optional[Dict[str, Any]],
    ) -> str:
        """构建通知内容"""
        content_lines = [
            "## 网页数据采集执行报告",
            "",
            "---",
            "",
            "### 📊 统计摘要",
            "",
            "| 指标 | 数量 |",
            "|------|------|",
            f"| 采集总数 | **{result_count}** 条 |",
            f"| 保存成功 | **{saved_count}** 条 |",
            f"| 内容识别成功 | {recognized_count} 条 |",
            f"| 内容识别失败 | {recognition_errors} 条 |",
            f"| 资质匹配成功 | {matched_count} 条 |",
            f"| 自动删除 | {deleted_count} 条 |",
        ]
        
        if result_count > 0:
            success_rate = (saved_count / result_count * 100) if result_count > 0 else 0
            content_lines.append(f"| 保存成功率 | **{success_rate:.1f}%** |")
        
        content_lines.extend([
            "",
            "---",
            "",
            "### 📋 基本信息",
            "",
            f"- **采集计划**: {schedule_name} (ID: {schedule_id})",
            f"- **目标网站**: [{target_url}]({target_url})" if target_url else "- **目标网站**: 未指定",
        ])
        
        if started_at:
            content_lines.append(f"- **开始时间**: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if finished_at:
            content_lines.append(f"- **结束时间**: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if duration:
            if duration < 60:
                content_lines.append(f"- **总耗时**: {duration:.1f} 秒")
            else:
                minutes = int(duration // 60)
                seconds = duration % 60
                content_lines.append(f"- **总耗时**: {minutes} 分 {seconds:.1f} 秒")
        
        if error_message:
            content_lines.extend([
                "",
                "---",
                "",
                "### ❌ 错误信息",
                "",
                f"```\n{error_message}\n```",
            ])
        
        if recognition_errors > 0 or deleted_count > 0:
            content_lines.extend([
                "",
                "---",
                "",
                "### ⚠️ 失败详情",
                "",
            ])
            
            if recognition_errors > 0:
                content_lines.append(f"- **内容识别失败**: {recognition_errors} 条数据无法正确识别内容结构")
            
            if deleted_count > 0:
                content_lines.append(f"- **资质匹配删除**: {deleted_count} 条数据因不符合企业资质要求被自动删除")
        
        if details and details.get('errors'):
            errors_list = details.get('errors', [])
            if errors_list:
                content_lines.extend([
                    "",
                    "#### 错误明细",
                    "",
                ])
                for i, err in enumerate(errors_list[:10], 1):
                    err_time = err.get('timestamp', '未知时间')
                    err_type = err.get('error_type', '未知错误')
                    err_msg = err.get('message', str(err))[:100]
                    content_lines.append(f"{i}. [{err_time}] {err_type}: {err_msg}")
                
                if len(errors_list) > 10:
                    content_lines.append(f"\n*...还有 {len(errors_list) - 10} 条错误未显示*")
        
        content_lines.extend([
            "",
            "---",
            "",
            f"*通知时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])
        
        return "\n".join(content_lines)


crawl_completion_notification_service = CrawlCompletionNotificationService()
