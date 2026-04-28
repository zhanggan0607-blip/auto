"""
统一文件服务
提供文件上传、下载、删除的统一接口
支持多种存储后端：MinIO、本地存储、阿里OSS
"""
import os
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO, Tuple
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)


class FileService:
    """
    统一文件服务

    提供统一的文件操作接口，封装不同存储后端的差异
    """

    STORAGE_LOCAL = 'local'
    STORAGE_MINIO = 'minio'
    STORAGE_OSS = 'oss'

    DEFAULT_BUCKET = 'default'
    FILE_TYPE_MAP = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.zip': 'application/zip',
        '.txt': 'text/plain',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    }

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
        self._minio_service = None
        self._init_storage()

    def _init_storage(self):
        """初始化存储后端"""
        try:
            from services.minio_service import minio_service
            self._minio_service = minio_service
        except Exception as e:
            logger.warning(f"MinIO服务初始化失败: {e}")

    def _get_content_type(self, filename: str) -> str:
        """根据文件名获取Content-Type"""
        ext = os.path.splitext(filename)[1].lower()
        return self.FILE_TYPE_MAP.get(ext, 'application/octet-stream')

    def _generate_object_name(
        self,
        folder: str,
        filename: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> str:
        """
        生成对象存储路径

        Args:
            folder: 文件夹路径
            filename: 原始文件名
            entity_type: 实体类型（如 enterprise, tender）
            entity_id: 实体ID

        Returns:
            str: 对象名称（存储路径）
        """
        now = datetime.now()
        date_path = now.strftime('%Y/%m/%d')

        if entity_type and entity_id:
            parts = [folder, entity_type, entity_id, date_path, filename]
        else:
            parts = [folder, date_path, filename]

        return '/'.join(parts)

    def _calculate_file_hash(self, file_data: BinaryIO) -> str:
        """计算文件MD5哈希"""
        md5 = hashlib.md5()
        for chunk in file_data.chunks():
            md5.update(chunk)
        return md5.hexdigest()

    def upload(
        self,
        file_obj: InMemoryUploadedFile,
        folder: str = 'uploads',
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        storage: str = None,
        bucket: str = None,
        replace_existing: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        上传文件

        Args:
            file_obj: Django上传文件对象
            folder: 存储文件夹
            entity_type: 实体类型
            entity_id: 实体ID
            storage: 存储后端（默认使用MinIO）
            bucket: 存储桶名称
            replace_existing: 是否替换已存在的文件

        Returns:
            Tuple[bool, Dict]: (是否成功, {url, object_name, file_hash, ...})
        """
        filename = file_obj.name
        content_type = file_obj.content_type or self._get_content_type(filename)

        object_name = self._generate_object_name(
            folder=folder,
            filename=filename,
            entity_type=entity_type,
            entity_id=entity_id
        )

        result = {
            'filename': filename,
            'object_name': object_name,
            'content_type': content_type,
            'size': file_obj.size,
            'storage': storage or self.STORAGE_MINIO,
            'bucket': bucket or self.DEFAULT_BUCKET,
        }

        if storage == self.STORAGE_LOCAL:
            return self._upload_to_local(file_obj, object_name, result)
        else:
            return self._upload_to_minio(file_obj, object_name, content_type, result)

    def _upload_to_minio(
        self,
        file_obj: InMemoryUploadedFile,
        object_name: str,
        content_type: str,
        result: Dict
    ) -> Tuple[bool, Dict[str, Any]]:
        """上传到MinIO"""
        if not self._minio_service:
            logger.error("MinIO服务不可用")
            result['error'] = 'MinIO服务不可用'
            return False, result

        try:
            file_obj.seek(0)
            success = self._minio_service.upload_file(
                file_data=file_obj,
                object_name=object_name,
                content_type=content_type
            )

            if success:
                result['url'] = self._minio_service.get_presigned_url(object_name)
                result['object_name'] = object_name
                result['success'] = True
                return True, result
            else:
                result['error'] = 'MinIO上传失败'
                return False, result

        except Exception as e:
            logger.error(f"MinIO上传异常: {e}")
            result['error'] = str(e)
            return False, result

    def _upload_to_local(
        self,
        file_obj: InMemoryUploadedFile,
        object_name: str,
        result: Dict
    ) -> Tuple[bool, Dict[str, Any]]:
        """上传到本地存储"""
        try:
            media_root = settings.MEDIA_ROOT
            file_path = os.path.join(media_root, object_name)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            result['url'] = f"{settings.MEDIA_URL}{object_name}"
            result['local_path'] = file_path
            result['success'] = True
            return True, result

        except Exception as e:
            logger.error(f"本地存储上传异常: {e}")
            result['error'] = str(e)
            return False, result

    def delete(self, object_name: str, storage: str = None) -> bool:
        """
        删除文件

        Args:
            object_name: 对象名称
            storage: 存储后端

        Returns:
            bool: 是否成功
        """
        if storage == self.STORAGE_LOCAL:
            return self._delete_local(object_name)
        else:
            return self._delete_minio(object_name)

    def _delete_minio(self, object_name: str) -> bool:
        """从MinIO删除"""
        if not self._minio_service:
            return False
        return self._minio_service.delete_file(object_name)

    def _delete_local(self, object_name: str) -> bool:
        """从本地存储删除"""
        try:
            media_root = settings.MEDIA_ROOT
            file_path = os.path.join(media_root, object_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"本地文件删除异常: {e}")
            return False

    def get_url(self, object_name: str, storage: str = None, expires: int = 3600) -> Optional[str]:
        """
        获取文件访问URL

        Args:
            object_name: 对象名称
            storage: 存储后端
            expires: 预签名URL过期时间（秒）

        Returns:
            str: 访问URL
        """
        if storage == self.STORAGE_LOCAL:
            return f"{settings.MEDIA_URL}{object_name}"
        elif self._minio_service:
            return self._minio_service.get_presigned_url(object_name, expires)
        return None

    def exists(self, object_name: str, storage: str = None) -> bool:
        """
        检查文件是否存在

        Args:
            object_name: 对象名称
            storage: 存储后端

        Returns:
            bool: 是否存在
        """
        if storage == self.STORAGE_LOCAL:
            media_root = settings.MEDIA_ROOT
            file_path = os.path.join(media_root, object_name)
            return os.path.exists(file_path)
        elif self._minio_service:
            return self._minio_service.file_exists(object_name)
        return False

    def get_info(self, object_name: str, storage: str = None) -> Optional[Dict]:
        """
        获取文件信息

        Args:
            object_name: 对象名称
            storage: 存储后端

        Returns:
            Dict: 文件信息
        """
        if storage == self.STORAGE_LOCAL:
            media_root = settings.MEDIA_ROOT
            file_path = os.path.join(media_root, object_name)
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                return {
                    'size': stat.st_size,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime),
                    'content_type': self._get_content_type(object_name),
                }
        elif self._minio_service:
            return self._minio_service.get_file_info(object_name)
        return None

    def batch_upload(
        self,
        files: list,
        folder: str = 'uploads',
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量上传文件

        Args:
            files: 文件对象列表
            folder: 存储文件夹
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            Dict: {success_count, failed_count, results}
        """
        results = []
        success_count = 0
        failed_count = 0

        for file_obj in files:
            success, info = self.upload(
                file_obj=file_obj,
                folder=folder,
                entity_type=entity_type,
                entity_id=entity_id
            )
            if success:
                success_count += 1
            else:
                failed_count += 1
            results.append({'filename': file_obj.name, 'success': success, **info})

        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total': len(files),
            'results': results
        }


file_service = FileService()
