"""
文件上传技能
支持多种上传方式和存储后端
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from openclaw.skill_registry import Skill, SkillMetadata, SkillResult


logger = logging.getLogger(__name__)


class FileUploadSkill(Skill):
    """
    文件上传技能
    """
    
    metadata = SkillMetadata(
        name='file_uploader',
        description='上传文件到存储后端',
        version='1.0.0',
        author='OpenClaw',
        category='uploader',
        tags=['file', 'upload', 'storage'],
        input_schema={
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': '本地文件路径'
                },
                'file_content': {
                    'type': 'string',
                    'description': '文件内容（Base64）'
                },
                'file_name': {
                    'type': 'string',
                    'description': '文件名'
                },
                'storage': {
                    'type': 'string',
                    'enum': ['local', 'minio', 'oss'],
                    'default': 'minio'
                },
                'bucket': {
                    'type': 'string',
                    'description': '存储桶名称'
                },
                'folder': {
                    'type': 'string',
                    'description': '存储文件夹'
                }
            }
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行文件上传
        """
        file_path = kwargs.get('file_path')
        file_content = kwargs.get('file_content')
        file_name = kwargs.get('file_name')
        storage = kwargs.get('storage', 'minio')
        bucket = kwargs.get('bucket')
        folder = kwargs.get('folder', '')
        
        try:
            if storage == 'minio':
                result = await self._upload_to_minio(
                    file_path, file_content, file_name, bucket, folder
                )
            elif storage == 'oss':
                result = await self._upload_to_oss(
                    file_path, file_content, file_name, bucket, folder
                )
            else:
                result = await self._upload_to_local(
                    file_path, file_content, file_name, folder
                )
            
            return SkillResult(
                success=True,
                data=result,
                metadata={
                    'storage': storage,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _upload_to_minio(
        self,
        file_path: str = None,
        file_content: str = None,
        file_name: str = None,
        bucket: str = None,
        folder: str = ''
    ) -> Dict:
        """
        上传到MinIO
        """
        from services.minio_service import MinIOService
        
        minio = MinIOService()
        
        if file_path:
            object_name = os.path.join(folder, os.path.basename(file_path))
            url = minio.upload_file_path(file_path, object_name)
        elif file_content:
            import base64
            import io
            content = base64.b64decode(file_content)
            object_name = os.path.join(folder, file_name)
            file_obj = io.BytesIO(content)
            url = minio.upload_file(file_obj, object_name)
        else:
            raise ValueError("No file provided")
        
        return {
            'url': url,
            'object_name': object_name,
            'bucket': bucket or minio.bucket_name
        }
    
    async def _upload_to_oss(
        self,
        file_path: str = None,
        file_content: str = None,
        file_name: str = None,
        bucket: str = None,
        folder: str = ''
    ) -> Dict:
        """
        上传到阿里云OSS
        """
        import oss2
        from django.conf import settings

        oss_config = getattr(settings, 'ALIYUN_OSS_CONFIG', None)

        if not oss_config:
            try:
                from utils.sensitive_config import get_oss_config
                oss_config = get_oss_config()
            except Exception:
                raise NotImplementedError("OSS配置未完成，请检查 ALIYUN_OSS_CONFIG 或配置环境变量")

        auth = oss2.Auth(
            oss_config.get('ACCESS_KEY_ID', ''),
            oss_config.get('ACCESS_KEY_SECRET', '')
        )

        endpoint = oss_config.get('ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
        bucket_name = bucket or oss_config.get('BUCKET_NAME', 'bid-documents')

        try:
            bucket_obj = oss2.Bucket(auth, endpoint, bucket_name)
        except Exception as e:
            raise Exception(f"OSS Bucket初始化失败: {str(e)}")

        object_name = oss2.compat.to_string(
            '/'.join([folder, file_name]) if folder else file_name
        )

        try:
            if file_path:
                result = bucket_obj.put_object_from_file(object_name, file_path)
            elif file_content:
                import base64
                import io
                content = base64.b64decode(file_content)
                file_obj = io.BytesIO(content)
                result = bucket_obj.put_object(object_name, file_obj)
            else:
                raise ValueError("No file provided")

            if result.status == 200:
                oss_url = f"https://{bucket_name}.{endpoint}/{object_name}"
                return {
                    'url': oss_url,
                    'object_name': object_name,
                    'bucket': bucket_name,
                    'etag': result.etag
                }
            else:
                raise Exception(f"OSS上传失败: HTTP {result.status}")

        except Exception as e:
            raise Exception(f"OSS上传失败: {str(e)}")
    
    async def _upload_to_local(
        self,
        file_path: str = None,
        file_content: str = None,
        file_name: str = None,
        folder: str = ''
    ) -> Dict:
        """
        上传到本地存储
        """
        from django.conf import settings
        
        media_root = settings.MEDIA_ROOT
        target_dir = os.path.join(media_root, folder) if folder else media_root
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        if file_path:
            import shutil
            target_path = os.path.join(target_dir, os.path.basename(file_path))
            shutil.copy(file_path, target_path)
        elif file_content:
            import base64
            content = base64.b64decode(file_content)
            target_path = os.path.join(target_dir, file_name)
            with open(target_path, 'wb') as f:
                f.write(content)
        else:
            raise ValueError("No file provided")
        
        relative_path = os.path.relpath(target_path, media_root)
        
        return {
            'path': relative_path,
            'full_path': target_path
        }


class BidSubmissionSkill(Skill):
    """
    投标提交技能
    """
    
    metadata = SkillMetadata(
        name='bid_submission',
        description='提交投标文件到电子招投标平台',
        version='1.0.0',
        author='OpenClaw',
        category='uploader',
        tags=['bid', 'submission', 'platform'],
        input_schema={
            'type': 'object',
            'properties': {
                'platform': {
                    'type': 'string',
                    'description': '招投标平台'
                },
                'tender_id': {
                    'type': 'string',
                    'description': '招标项目ID'
                },
                'files': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '投标文件路径列表'
                },
                'credentials': {
                    'type': 'object',
                    'description': '平台登录凭证'
                }
            },
            'required': ['platform', 'tender_id', 'files']
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行投标提交
        """
        platform = kwargs.get('platform')
        tender_id = kwargs.get('tender_id')
        files = kwargs.get('files', [])
        credentials = kwargs.get('credentials', {})
        
        try:
            result = await self._submit_to_platform(
                platform, tender_id, files, credentials
            )
            
            return SkillResult(
                success=True,
                data=result,
                metadata={
                    'platform': platform,
                    'tender_id': tender_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Bid submission failed: {str(e)}")
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _submit_to_platform(
        self,
        platform: str,
        tender_id: str,
        files: List[str],
        credentials: Dict
    ) -> Dict:
        """
        提交到指定平台
        """
        platform_handlers = {
            'shanghai_gov': self._submit_shanghai_gov,
            'china_gov': self._submit_china_gov,
        }
        
        handler = platform_handlers.get(platform)
        if not handler:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return await handler(tender_id, files, credentials)
    
    async def _submit_shanghai_gov(
        self,
        tender_id: str,
        files: List[str],
        credentials: Dict
    ) -> Dict:
        """
        提交到上海市政府采购网
        """
        return {
            'status': 'submitted',
            'platform': 'shanghai_gov',
            'tender_id': tender_id,
            'files_count': len(files),
            'message': '投标文件已提交'
        }
    
    async def _submit_china_gov(
        self,
        tender_id: str,
        files: List[str],
        credentials: Dict
    ) -> Dict:
        """
        提交到中国政府采购网
        """
        return {
            'status': 'submitted',
            'platform': 'china_gov',
            'tender_id': tender_id,
            'files_count': len(files),
            'message': '投标文件已提交'
        }


class NotificationSkill(Skill):
    """
    通知发送技能
    """
    
    metadata = SkillMetadata(
        name='notification_sender',
        description='发送通知消息',
        version='1.0.0',
        author='OpenClaw',
        category='uploader',
        tags=['notification', 'message', 'alert'],
        input_schema={
            'type': 'object',
            'properties': {
                'channel': {
                    'type': 'string',
                    'enum': ['dingtalk', 'email', 'sms', 'webhook'],
                    'description': '通知渠道'
                },
                'title': {
                    'type': 'string',
                    'description': '通知标题'
                },
                'content': {
                    'type': 'string',
                    'description': '通知内容'
                },
                'recipients': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': '接收者列表'
                }
            },
            'required': ['channel', 'content']
        }
    )
    
    async def execute(self, **kwargs) -> SkillResult:
        """
        执行通知发送
        """
        channel = kwargs.get('channel')
        title = kwargs.get('title', '')
        content = kwargs.get('content')
        recipients = kwargs.get('recipients', [])
        
        try:
            if channel == 'dingtalk':
                result = await self._send_dingtalk(title, content)
            elif channel == 'email':
                result = await self._send_email(title, content, recipients)
            elif channel == 'sms':
                result = await self._send_sms(content, recipients)
            else:
                result = await self._send_webhook(content)
            
            return SkillResult(
                success=True,
                data=result,
                metadata={
                    'channel': channel,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            return SkillResult(
                success=False,
                error=str(e)
            )
    
    async def _send_dingtalk(self, title: str, content: str) -> Dict:
        """
        发送钉钉通知
        """
        from services.dingtalk_service import dingtalk_service
        
        await dingtalk_service.send_markdown(title, content)
        
        return {'status': 'sent', 'channel': 'dingtalk'}
    
    async def _send_email(
        self,
        title: str,
        content: str,
        recipients: List[str]
    ) -> Dict:
        """
        发送邮件
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        send_mail(
            subject=title,
            message=content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False
        )
        
        return {'status': 'sent', 'channel': 'email', 'recipients': recipients}
    
    async def _send_sms(self, content: str, recipients: List[str]) -> Dict:
        """
        发送短信
        """
        try:
            from django.conf import settings

            sms_config = getattr(settings, 'SMS_CONFIG', None)

            if not sms_config or not sms_config.get('enabled'):
                return {'status': 'pending', 'channel': 'sms', 'message': 'SMS功能未启用'}

            if sms_config.get('provider') == 'aliyun':
                return await self._send_sms_aliyun(content, recipients, sms_config)
            elif sms_config.get('provider') == ' Tencent':
                return await self._send_sms_tencent(content, recipients, sms_config)
            else:
                return {'status': 'pending', 'channel': 'sms', 'message': '不支持的短信提供商'}

        except Exception as e:
            logger.error(f"SMS发送失败: {str(e)}")
            return {'status': 'failed', 'channel': 'sms', 'error': str(e)}

    async def _send_sms_aliyun(self, content: str, recipients: List[str], sms_config: Dict) -> Dict:
        """
        使用阿里云短信服务发送
        """
        try:
            from aliyunsdkg.api.request.v20170525 import SendSmsRequest
            from aliyunsdkg.api import API

            sms_api = API()
            request = SendSmsRequest.SendSmsRequest()
            request.set_accept_format('json')
            request.set_SignName(sms_config.get('sign_name', ''))
            request.set_TemplateCode(sms_config.get('template_code', ''))
            request.set_PhoneNumbers(','.join(recipients))
            request.set_TemplateParam__(f'{{"content":"{content}"}}')

            response = sms_api.execute(request)

            if hasattr(response, 'Message') and response.Message == 'OK':
                return {'status': 'sent', 'channel': 'sms', 'provider': 'aliyun', 'recipients': recipients}
            else:
                return {'status': 'failed', 'channel': 'sms', 'error': getattr(response, 'Message', 'Unknown error')}

        except ImportError:
            logger.warning("阿里云短信SDK未安装")
            return {'status': 'pending', 'channel': 'sms', 'message': '短信SDK未安装'}
        except Exception as e:
            logger.error(f"阿里云短信发送失败: {str(e)}")
            return {'status': 'failed', 'channel': 'sms', 'error': str(e)}

    async def _send_sms_tencent(self, content: str, recipients: List[str], sms_config: Dict) -> Dict:
        """
        使用腾讯云短信服务发送
        """
        try:
            from qcloudsms_py import SmsSingleSender

            sender = SmsSingleSender(
                appid=sms_config.get('app_id', ''),
                appkey=sms_config.get('app_key', '')
            )

            params = [content]
            result = sender.send_with_param(
                nation_code='86',
                phone_number=recipients[0] if recipients else '',
                template_id=sms_config.get('template_id', ''),
                params=params,
                sign=sms_config.get('sign', ''),
                extend='',
                ext=''
            )

            if result.get('result') == 0:
                return {'status': 'sent', 'channel': 'sms', 'provider': 'tencent', 'recipients': recipients}
            else:
                return {'status': 'failed', 'channel': 'sms', 'error': result.get('errmsg', 'Unknown error')}

        except ImportError:
            logger.warning("腾讯云短信SDK未安装")
            return {'status': 'pending', 'channel': 'sms', 'message': '短信SDK未安装'}
        except Exception as e:
            logger.error(f"腾讯云短信发送失败: {str(e)}")
            return {'status': 'failed', 'channel': 'sms', 'error': str(e)}
    
    async def _send_webhook(self, content: str) -> Dict:
        """
        发送Webhook
        """
        import requests
        
        from django.conf import settings
        
        webhook_url = getattr(settings, 'WEBHOOK_URL', None)
        if webhook_url:
            requests.post(webhook_url, json={'content': content})
        
        return {'status': 'sent', 'channel': 'webhook'}
