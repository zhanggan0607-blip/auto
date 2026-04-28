"""
统一通知服务
支持钉钉、飞书、企业微信、邮件、短信、Webhook多渠道通知
"""
import hashlib
import hmac
import base64
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class FeishuNotificationService:
    """
    飞书通知服务
    使用飞书自定义机器人Webhook
    """

    def __init__(self):
        self.webhook_url = getattr(settings, 'FEISHU_WEBHOOK_URL', '')
        self.secret = getattr(settings, 'FEISHU_SECRET', '')

    def _generate_sign(self, timestamp: int) -> str:
        """
        生成飞书签名
        """
        if not self.secret:
            return ''

        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def send_text(self, content: str) -> bool:
        """
        发送文本消息
        """
        if not self.webhook_url:
            logger.warning("飞书 Webhook 未配置")
            return False

        payload = {
            'msg_type': 'text',
            'content': {
                'text': content
            }
        }

        if self.secret:
            timestamp = int(time.time())
            payload['timestamp'] = str(timestamp)
            payload['sign'] = self._generate_sign(timestamp)

        return self._send_request(payload)

    def send_markdown(self, title: str, content: str) -> bool:
        """
        发送富文本消息（飞书使用interactive卡片）
        """
        if not self.webhook_url:
            logger.warning("飞书 Webhook 未配置")
            return False

        payload = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {
                        'tag': 'plain_text',
                        'content': title
                    },
                    'template': 'blue'
                },
                'elements': [
                    {
                        'tag': 'markdown',
                        'content': content
                    }
                ]
            }
        }

        if self.secret:
            timestamp = int(time.time())
            payload['timestamp'] = str(timestamp)
            payload['sign'] = self._generate_sign(timestamp)

        return self._send_request(payload)

    def send_rich_text(self, title: str, sections: List[Dict]) -> bool:
        """
        发送富文本消息（多段落）

        Args:
            title: 标题
            sections: 段落列表，每个段落包含 tag 和 content
        """
        if not self.webhook_url:
            return False

        elements = []
        for section in sections:
            tag = section.get('tag', 'markdown')
            elements.append({
                'tag': tag,
                'content': section.get('content', '')
            })

        payload = {
            'msg_type': 'interactive',
            'card': {
                'header': {
                    'title': {
                        'tag': 'plain_text',
                        'content': title
                    }
                },
                'elements': elements
            }
        }

        if self.secret:
            timestamp = int(time.time())
            payload['timestamp'] = str(timestamp)
            payload['sign'] = self._generate_sign(timestamp)

        return self._send_request(payload)

    def _send_request(self, payload: Dict) -> bool:
        """
        发送HTTP请求
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0 or result.get('StatusCode') == 0:
                    logger.info(f"飞书消息发送成功")
                    return True
                else:
                    logger.error(f"飞书消息发送失败: {result}")
                    return False
            else:
                logger.error(f"飞书消息发送失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"飞书消息发送异常: {str(e)}")
            return False


class WeComNotificationService:
    """
    企业微信通知服务
    使用企业微信群机器人Webhook
    """

    def __init__(self):
        self.webhook_url = getattr(settings, 'WECOM_WEBHOOK_URL', '')

    def send_text(self, content: str, mentioned_list: List[str] = None) -> bool:
        """
        发送文本消息

        Args:
            content: 文本内容
            mentioned_list: @用户ID列表（'all'表示@所有人）
        """
        if not self.webhook_url:
            logger.warning("企业微信 Webhook 未配置")
            return False

        payload = {
            'msgtype': 'text',
            'text': {
                'content': content
            }
        }

        if mentioned_list:
            payload['text']['mentioned_list'] = mentioned_list

        return self._send_request(payload)

    def send_markdown(self, content: str) -> bool:
        """
        发送Markdown消息

        Args:
            content: Markdown内容（企业微信支持有限的Markdown语法）
        """
        if not self.webhook_url:
            logger.warning("企业微信 Webhook 未配置")
            return False

        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'content': content
            }
        }

        return self._send_request(payload)

    def send_news(self, articles: List[Dict]) -> bool:
        """
        发送图文消息

        Args:
            articles: 图文列表 [{'title': '', 'description': '', 'url': '', 'picurl': ''}]
        """
        if not self.webhook_url:
            return False

        payload = {
            'msgtype': 'news',
            'news': {
                'articles': articles
            }
        }

        return self._send_request(payload)

    def send_file(self, media_id: str) -> bool:
        """
        发送文件消息

        Args:
            media_id: 素材ID
        """
        if not self.webhook_url:
            return False

        payload = {
            'msgtype': 'file',
            'file': {
                'media_id': media_id
            }
        }

        return self._send_request(payload)

    def _send_request(self, payload: Dict) -> bool:
        """
        发送HTTP请求
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info(f"企业微信消息发送成功")
                    return True
                else:
                    logger.error(f"企业微信消息发送失败: {result.get('errmsg', '')}")
                    return False
            else:
                logger.error(f"企业微信消息发送失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"企业微信消息发送异常: {str(e)}")
            return False


class UnifiedNotificationService:
    """
    统一通知服务
    支持同时向多个渠道发送通知
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.dingtalk = self._init_dingtalk()
        self.feishu = FeishuNotificationService()
        self.wecom = WeComNotificationService()

    def _init_dingtalk(self):
        try:
            from services.dingtalk_service import dingtalk_service
            return dingtalk_service
        except Exception:
            return None

    def send(
        self,
        title: str,
        content: str,
        channels: List[str] = None,
        markdown: bool = True,
        at_all: bool = False
    ) -> Dict[str, bool]:
        """
        统一发送通知

        Args:
            title: 通知标题
            content: 通知内容
            channels: 通知渠道列表，默认使用所有已配置渠道
                     可选: ['dingtalk', 'feishu', 'wecom', 'email', 'webhook']
            markdown: 是否使用Markdown格式
            at_all: 是否@所有人

        Returns:
            Dict[str, bool]: 各渠道发送结果
        """
        if channels is None:
            channels = self._get_configured_channels()

        results = {}

        for channel in channels:
            try:
                if channel == 'dingtalk':
                    results['dingtalk'] = self._send_dingtalk(title, content, markdown, at_all)
                elif channel == 'feishu':
                    results['feishu'] = self._send_feishu(title, content, markdown)
                elif channel == 'wecom':
                    results['wecom'] = self._send_wecom(title, content, markdown, at_all)
                elif channel == 'email':
                    results['email'] = self._send_email(title, content)
                elif channel == 'webhook':
                    results['webhook'] = self._send_webhook(title, content)
                else:
                    logger.warning(f"未知通知渠道: {channel}")
                    results[channel] = False
            except Exception as e:
                logger.error(f"通知发送失败 channel={channel}: {str(e)}")
                results[channel] = False

        success_count = sum(1 for v in results.values() if v)
        logger.info(
            f"通知发送完成: {success_count}/{len(results)} 渠道成功, "
            f"channels={list(results.keys())}"
        )

        return results

    def _get_configured_channels(self) -> List[str]:
        """
        获取已配置的渠道列表
        """
        channels = []

        if getattr(settings, 'DINGTALK_WEBHOOK_URL', None):
            channels.append('dingtalk')
        if getattr(settings, 'FEISHU_WEBHOOK_URL', None):
            channels.append('feishu')
        if getattr(settings, 'WECOM_WEBHOOK_URL', None):
            channels.append('wecom')

        if not channels:
            channels.append('dingtalk')

        return channels

    def _send_dingtalk(self, title: str, content: str, markdown: bool, at_all: bool) -> bool:
        if not self.dingtalk:
            return False
        if markdown:
            return self.dingtalk.send_markdown(title=title, content=content, at_all=at_all)
        return self.dingtalk.send_text(content=content, at_all=at_all)

    def _send_feishu(self, title: str, content: str, markdown: bool) -> bool:
        if markdown:
            return self.feishu.send_markdown(title=title, content=content)
        return self.feishu.send_text(content=content)

    def _send_wecom(self, title: str, content: str, markdown: bool, at_all: bool) -> bool:
        if markdown:
            wecom_content = f"**{title}**\n\n{content}"
            return self.wecom.send_markdown(content=wecom_content)
        return self.wecom.send_text(content=f"{title}\n{content}", mentioned_list=['all'] if at_all else None)

    def _send_email(self, title: str, content: str) -> bool:
        try:
            from django.core.mail import send_mail

            recipient_list = getattr(settings, 'NOTIFICATION_EMAIL_RECIPIENTS', [])
            if not recipient_list:
                return False

            send_mail(
                subject=title,
                message=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True
            )
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False

    def _send_webhook(self, title: str, content: str) -> bool:
        try:
            webhook_url = getattr(settings, 'NOTIFICATION_WEBHOOK_URL', None)
            if not webhook_url:
                return False

            requests.post(
                webhook_url,
                json={'title': title, 'content': content, 'timestamp': datetime.now().isoformat()},
                timeout=10
            )
            return True
        except Exception as e:
            logger.error(f"Webhook发送失败: {str(e)}")
            return False

    def notify_bid_result(
        self,
        tender_title: str,
        result: str,
        amount: float = None,
        winner_name: str = None,
        our_rank: int = None,
        tender_url: str = None,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        发送投标结果通知

        Args:
            tender_title: 项目标题
            result: 结果 (won/lost/rejected)
            amount: 金额
            winner_name: 中标单位
            our_rank: 我方排名
            tender_url: 项目链接
            channels: 通知渠道
        """
        if result == 'won':
            emoji = '🎉'
            title = f'{emoji} 中标通知 - {tender_title[:30]}'
            content = f"""## {emoji} 恭喜中标！

**项目名称**：{tender_title}
**中标金额**：¥{amount:,.2f}
{f'**中标单位**：{winner_name}' if winner_name else ''}
{f'[查看详情]({tender_url})' if tender_url else ''}

> 系统自动推送"""

        elif result == 'rejected':
            emoji = '🔴'
            title = f'{emoji} 废标通知 - {tender_title[:30]}'
            content = f"""## {emoji} 废标通知

**项目名称**：{tender_title}
{f'**废标原因**：{winner_name}' if winner_name else ''}
{f'[查看详情]({tender_url})' if tender_url else ''}

> 请总结教训，避免同类问题"""

        else:
            emoji = '📋'
            title = f'{emoji} 未中标通知 - {tender_title[:30]}'
            content = f"""## {emoji} 未中标通知

**项目名称**：{tender_title}
{f'**我方报价**：¥{amount:,.2f}' if amount else ''}
{f'**中标单位**：{winner_name}' if winner_name else ''}
{f'**我方排名**：第{our_rank}名' if our_rank else ''}
{f'[查看详情]({tender_url})' if tender_url else ''}

> 请总结经验，继续努力！"""

        return self.send(
            title=title,
            content=content,
            channels=channels,
            at_all=(result == 'won')
        )

    def notify_workflow_failure(
        self,
        workflow_id: str,
        stage_name: str,
        error: str,
        tender_id: int = None,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        发送工作流失败通知
        """
        title = f'⚠️ 工作流异常 - {stage_name}'
        content = f"""## ⚠️ 工作流执行异常

**工作流ID**：`{workflow_id}`
**异常阶段**：`{stage_name}`
{f'**招标项目ID**：`{tender_id}`' if tender_id else ''}

---

### 错误信息

```
{error[:500]}
```

> 此通知由系统自动发送，请及时处理。"""

        return self.send(title=title, content=content, channels=channels)

    def notify_new_tender(
        self,
        tender_title: str,
        budget: float = None,
        match_score: float = None,
        deadline: str = None,
        tender_url: str = None,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        发送新招标通知
        """
        title = f'📋 新招标 - {tender_title[:30]}'
        content = f"""## 📋 发现新招标项目

**项目名称**：{tender_title}
{f'**预算金额**：¥{budget:,.2f}' if budget else ''}
{f'**匹配度**：{match_score:.0%}' if match_score else ''}
{f'**截止日期**：{deadline}' if deadline else ''}
{f'[查看详情]({tender_url})' if tender_url else ''}

> 系统自动匹配推送"""

        return self.send(title=title, content=content, channels=channels)


unified_notification_service = UnifiedNotificationService()
