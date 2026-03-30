"""
钉钉通知服务
使用 DingtalkChatbot 库集成
支持中标结果实时通知
安全改进：日志中脱敏webhook和secret，禁止泄露
"""
import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


def mask_webhook(url: str) -> str:
    """
    脱敏webhook URL

    Args:
        url: 原始URL

    Returns:
        str: 脱敏后的URL
    """
    if not url:
        return '***'
    match = re.search(r'access_token=([^&]+)', url)
    if match:
        token = match.group(1)
        if len(token) > 8:
            return f"...access_token={token[:4]}***{token[-4:]}***"
    return '***'


def mask_secret(secret: str) -> str:
    """
    脱敏secret

    Args:
        secret: 原始密钥

    Returns:
        str: 脱敏后的密钥
    """
    if not secret:
        return '***'
    if len(secret) > 8:
        return f"{secret[:4]}***{secret[-4:]}"
    return '***'


class DingTalkService:
    """
    钉钉通知服务
    使用 DingtalkChatbot 库
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
        
        self.webhook_url = settings.DINGTALK_WEBHOOK_URL
        self.secret = settings.DINGTALK_SECRET
        self._chatbot = None
        self._initialized = True
    
    def _get_chatbot(self):
        """
        获取 DingtalkChatbot 实例
        安全：日志中脱敏webhook和secret
        """
        if self._chatbot is None:
            try:
                from dingtalkchatbot.chatbot import DingtalkChatbot

                if self.webhook_url:
                    if self.secret:
                        self._chatbot = DingtalkChatbot(
                            webhook=self.webhook_url,
                            secret=self.secret
                        )
                    else:
                        self._chatbot = DingtalkChatbot(webhook=self.webhook_url)
                    logger.info(f"钉钉机器人初始化成功 (webhook: {mask_webhook(self.webhook_url)})")
                else:
                    logger.warning("钉钉 Webhook 未配置")
            except ImportError:
                logger.error("DingtalkChatbot 库未安装")
            except Exception as e:
                logger.error(f"钉钉机器人初始化失败: {str(e)}")

        return self._chatbot
    
    def send_text(
        self,
        content: str,
        at_mobiles: List[str] = None,
        at_all: bool = False
    ) -> bool:
        """
        发送文本消息
        
        Args:
            content: 文本内容
            at_mobiles: @手机号列表
            at_all: 是否@所有人
            
        Returns:
            bool: 是否成功
        """
        chatbot = self._get_chatbot()
        
        if not chatbot:
            logger.warning("钉钉机器人未配置，跳过发送")
            return False
        
        try:
            chatbot.send_text(
                msg=content,
                at_mobiles=at_mobiles,
                is_at_all=at_all
            )
            logger.info(f"钉钉文本消息发送成功: {content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"钉钉文本消息发送失败: {str(e)}")
            return False
    
    def send_markdown(
        self,
        title: str,
        content: str,
        at_mobiles: List[str] = None,
        at_all: bool = False
    ) -> bool:
        """
        发送 Markdown 消息
        
        Args:
            title: 标题
            content: Markdown 内容
            at_mobiles: @手机号列表
            at_all: 是否@所有人
            
        Returns:
            bool: 是否成功
        """
        chatbot = self._get_chatbot()
        
        if not chatbot:
            logger.warning("钉钉机器人未配置，跳过发送")
            return False
        
        try:
            chatbot.send_markdown(
                title=title,
                text=content,
                at_mobiles=at_mobiles,
                is_at_all=at_all
            )
            logger.info(f"钉钉 Markdown 消息发送成功: {title}")
            return True
        except Exception as e:
            logger.error(f"钉钉 Markdown 消息发送失败: {str(e)}")
            return False
    
    def send_link(
        self,
        title: str,
        text: str,
        message_url: str,
        pic_url: str = None
    ) -> bool:
        """
        发送链接消息
        
        Args:
            title: 标题
            text: 描述文本
            message_url: 链接地址
            pic_url: 图片地址
            
        Returns:
            bool: 是否成功
        """
        chatbot = self._get_chatbot()
        
        if not chatbot:
            return False
        
        try:
            chatbot.send_link(
                title=title,
                text=text,
                messageUrl=message_url,
                picUrl=pic_url
            )
            logger.info(f"钉钉链接消息发送成功: {title}")
            return True
        except Exception as e:
            logger.error(f"钉钉链接消息发送失败: {str(e)}")
            return False
    
    def send_action_card(
        self,
        title: str,
        text: str,
        btns: List[Dict[str, str]],
        hide_avatar: bool = False
    ) -> bool:
        """
        发送 ActionCard 消息
        
        Args:
            title: 标题
            text: Markdown 内容
            btns: 按钮列表 [{'title': '按钮1', 'actionURL': 'url1'}, ...]
            hide_avatar: 是否隐藏头像
            
        Returns:
            bool: 是否成功
        """
        chatbot = self._get_chatbot()
        
        if not chatbot:
            return False
        
        try:
            chatbot.send_action_card(
                title=title,
                text=text,
                btns=btns,
                hideAvatar=hide_avatar
            )
            logger.info(f"钉钉 ActionCard 消息发送成功: {title}")
            return True
        except Exception as e:
            logger.error(f"钉钉 ActionCard 消息发送失败: {str(e)}")
            return False


class BidResultNotificationService:
    """
    中标结果通知服务
    每日自动查询中标结果，匹配成功则推送
    """
    
    def __init__(self):
        self.dingtalk = DingTalkService()
    
    def notify_bid_win(
        self,
        tender_title: str,
        tender_url: str,
        bid_amount: float,
        announce_date: str,
        enterprise_name: str = None
    ) -> bool:
        """
        发送中标通知
        
        Args:
            tender_title: 项目标题
            tender_url: 项目链接
            bid_amount: 中标金额
            announce_date: 公告日期
            enterprise_name: 中标企业名称
            
        Returns:
            bool: 是否成功
        """
        title = f"🎉 中标通知 - {tender_title[:30]}"
        
        content = f"""## 🎉 恭喜中标！

**项目名称**：{tender_title}

**中标金额**：¥{bid_amount:,.2f}

**公告日期**：{announce_date}

{"**中标单位**：" + enterprise_name if enterprise_name else ""}

---

[点击查看详情]({tender_url})

> 系统自动推送，请及时跟进后续工作
"""
        
        return self.dingtalk.send_markdown(
            title=title,
            content=content,
            at_all=True
        )
    
    def notify_bid_lost(
        self,
        tender_title: str,
        tender_url: str,
        our_amount: float,
        winner_name: str,
        winner_amount: float,
        our_rank: int = None
    ) -> bool:
        """
        发送未中标通知
        
        Args:
            tender_title: 项目标题
            tender_url: 项目链接
            our_amount: 我方报价
            winner_name: 中标单位
            winner_amount: 中标金额
            our_rank: 我方排名
            
        Returns:
            bool: 是否成功
        """
        title = f"未中标通知 - {tender_title[:30]}"
        
        content = f"""## 未中标通知

**项目名称**：{tender_title}

**我方报价**：¥{our_amount:,.2f}

**中标单位**：{winner_name}

**中标金额**：¥{winner_amount:,.2f}

{"**我方排名**：第" + str(our_rank) + "名" if our_rank else ""}

---

[点击查看详情]({tender_url})

> 请总结经验，继续努力！
"""
        
        return self.dingtalk.send_markdown(
            title=title,
            content=content
        )
    
    def notify_new_tender(
        self,
        tender_title: str,
        tender_url: str,
        publish_date: str,
        deadline_date: str,
        budget: float = None,
        match_score: float = None
    ) -> bool:
        """
        发送新招标通知
        
        Args:
            tender_title: 项目标题
            tender_url: 项目链接
            publish_date: 发布日期
            deadline_date: 截止日期
            budget: 预算金额
            match_score: 匹配分数
            
        Returns:
            bool: 是否成功
        """
        title = f"📋 新招标通知 - {tender_title[:30]}"
        
        budget_str = f"**预算金额**：¥{budget:,.2f}\n\n" if budget else ""
        match_str = f"**匹配度**：{match_score:.0%}\n\n" if match_score else ""
        
        content = f"""## 📋 发现新招标项目

**项目名称**：{tender_title}

{budget_str}{match_str}**发布日期**：{publish_date}

**截止日期**：{deadline_date}

---

[点击查看详情]({tender_url})

> 系统自动匹配推送
"""
        
        return self.dingtalk.send_markdown(
            title=title,
            content=content
        )
    
    def notify_deadline_approaching(
        self,
        tender_title: str,
        tender_url: str,
        deadline_date: str,
        days_remaining: int
    ) -> bool:
        """
        发送截止日期临近通知
        
        Args:
            tender_title: 项目标题
            tender_url: 项目链接
            deadline_date: 截止日期
            days_remaining: 剩余天数
            
        Returns:
            bool: 是否成功
        """
        emoji = "🔴" if days_remaining <= 1 else "🟡" if days_remaining <= 3 else "🟢"
        title = f"{emoji} 投标截止提醒 - {tender_title[:30]}"
        
        content = f"""## {emoji} 投标截止日期临近

**项目名称**：{tender_title}

**截止日期**：{deadline_date}

**剩余天数**：{days_remaining} 天

---

[点击查看详情]({tender_url})

> 请尽快完成投标准备工作！
"""
        
        at_all = days_remaining <= 1
        
        return self.dingtalk.send_markdown(
            title=title,
            content=content,
            at_all=at_all
        )
    
    def notify_crawler_error(
        self,
        website_name: str,
        error_message: str,
        retry_count: int
    ) -> bool:
        """
        发送爬虫错误通知
        
        Args:
            website_name: 网站名称
            error_message: 错误信息
            retry_count: 重试次数
            
        Returns:
            bool: 是否成功
        """
        title = f"⚠️ 采集异常通知 - {website_name}"
        
        content = f"""## ⚠️ 采集异常

**网站**：{website_name}

**错误信息**：{error_message}

**重试次数**：{retry_count}

**时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

> 请检查采集配置或人工介入
"""
        
        return self.dingtalk.send_markdown(
            title=title,
            content=content
        )
    
    def send_daily_summary(
        self,
        total_tenders: int,
        new_tenders: int,
        matched_tenders: int,
        won_bids: int,
        lost_bids: int
    ) -> bool:
        """
        发送每日汇总
        
        Args:
            total_tenders: 总招标数
            new_tenders: 新增招标数
            matched_tenders: 匹配招标数
            won_bids: 中标数
            lost_bids: 未中标数
            
        Returns:
            bool: 是否成功
        """
        today = datetime.now().strftime('%Y-%m-%d')
        title = f"📊 每日汇总 - {today}"
        
        content = f"""## 📊 每日汇总报告

**日期**：{today}

---

### 招标信息

- 总招标数：{total_tenders}
- 今日新增：{new_tenders}
- 匹配推荐：{matched_tenders}

---

### 投标结果

- 🎉 中标：{won_bids}
- 未中标：{lost_bids}

---

> 系统自动生成
"""
        
        return self.dingtalk.send_markdown(
            title=title,
            content=content
        )


dingtalk_service = DingTalkService()
bid_result_notification_service = BidResultNotificationService()
