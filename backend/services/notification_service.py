"""
通知发送服务
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

from apps.notifications.models import Notification, NotificationChannel, NotificationLog

logger = logging.getLogger(__name__)


class NotificationService:
    """
    通知发送服务
    """
    def __init__(self):
        self.dingtalk_webhook = settings.DINGTALK_WEBHOOK_URL

    def send_notification(self, notification: Notification, channels: List[str] = None) -> bool:
        """
        发送通知
        """
        if channels is None:
            channels = ['dingtalk', 'email']
        
        sent_channels = []
        
        for channel_type in channels:
            try:
                if channel_type == 'dingtalk':
                    if self.send_dingtalk(notification):
                        sent_channels.append('dingtalk')
                elif channel_type == 'email':
                    if self.send_email(notification):
                        sent_channels.append('email')
            except Exception as e:
                logger.error(f"发送通知失败: {channel_type}, 错误: {str(e)}")
        
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.sent_channels = sent_channels
        notification.save()
        
        return len(sent_channels) > 0

    def send_dingtalk(self, notification: Notification) -> bool:
        """
        发送钉钉消息
        """
        if not self.dingtalk_webhook:
            logger.warning("钉钉Webhook未配置")
            return False
        
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": notification.title,
                    "text": f"### {notification.title}\n\n{notification.content}"
                }
            }
            
            response = requests.post(
                self.dingtalk_webhook,
                json=data,
                timeout=10
            )
            
            result = response.json()
            if result.get('errcode') == 0:
                self._create_log(notification, 'dingtalk', 'sent')
                return True
            else:
                self._create_log(notification, 'dingtalk', 'failed', result.get('errmsg'))
                return False
                
        except Exception as e:
            self._create_log(notification, 'dingtalk', 'failed', str(e))
            logger.error(f"钉钉发送失败: {str(e)}")
            return False

    def send_email(self, notification: Notification) -> bool:
        """
        发送邮件
        """
        from django.core.mail import send_mail
        
        try:
            recipient_email = notification.recipient.email
            if not recipient_email:
                logger.warning(f"用户 {notification.recipient.username} 没有配置邮箱")
                return False
            
            send_mail(
                subject=notification.title,
                message=notification.content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False
            )
            
            self._create_log(notification, 'email', 'sent')
            return True
            
        except Exception as e:
            self._create_log(notification, 'email', 'failed', str(e))
            logger.error(f"邮件发送失败: {str(e)}")
            return False

    def _create_log(self, notification: Notification, channel_type: str, status: str, error_message: str = None):
        """
        创建发送日志
        """
        try:
            channel = NotificationChannel.objects.filter(
                user=notification.recipient,
                channel_type=channel_type,
                is_active=True
            ).first()
            
            NotificationLog.objects.create(
                notification=notification,
                channel=channel,
                status=status,
                error_message=error_message,
                sent_at=timezone.now() if status == 'sent' else None
            )
        except Exception as e:
            logger.error(f"创建通知日志失败: {str(e)}")
