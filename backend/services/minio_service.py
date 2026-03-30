"""
MinIO 对象存储服务
用于存储招标文件、投标文档等
"""
import io
import logging
from typing import Optional, BinaryIO
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MinIOService:
    """
    MinIO 对象存储服务
    """
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """
        初始化 MinIO 客户端
        """
        try:
            from minio import Minio
            from minio.error import S3Error
            
            config = settings.MINIO_CONFIG
            
            self._client = Minio(
                config['ENDPOINT'],
                access_key=config['ACCESS_KEY'],
                secret_key=config['SECRET_KEY'],
                secure=config['SECURE']
            )
            
            self._bucket_name = config['BUCKET_NAME']
            self._ensure_bucket_exists()
            
            logger.info(f"MinIO 初始化成功，Bucket: {self._bucket_name}")
        except Exception as e:
            logger.error(f"MinIO 初始化失败: {str(e)}")
            self._client = None
    
    @property
    def bucket_name(self):
        """
        获取当前Bucket名称
        """
        return self._bucket_name
    
    def _ensure_bucket_exists(self):
        """
        确保 Bucket 存在
        """
        try:
            if not self._client.bucket_exists(self._bucket_name):
                self._client.make_bucket(self._bucket_name)
                logger.info(f"创建 Bucket: {self._bucket_name}")
        except Exception as e:
            logger.error(f"检查/创建 Bucket 失败: {str(e)}")
    
    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = 'application/octet-stream',
        metadata: dict = None
    ) -> Optional[str]:
        """
        上传文件
        
        Args:
            file_data: 文件数据（二进制流）
            object_name: 对象名称（存储路径）
            content_type: 内容类型
            metadata: 元数据
            
        Returns:
            str: 对象名称，失败返回 None
        """
        if not self._client:
            logger.error("MinIO 客户端未初始化")
            return None
        
        try:
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self._client.put_object(
                self._bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"文件上传成功: {object_name}")
            return object_name
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return None
    
    def upload_file_path(
        self,
        file_path: str,
        object_name: str = None,
        content_type: str = None
    ) -> Optional[str]:
        """
        通过文件路径上传
        
        Args:
            file_path: 本地文件路径
            object_name: 对象名称（可选，默认使用文件名）
            content_type: 内容类型
            
        Returns:
            str: 对象名称
        """
        if not self._client:
            logger.error("MinIO 客户端未初始化")
            return None
        
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None
            
            if object_name is None:
                object_name = path.name
            
            self._client.fput_object(
                self._bucket_name,
                object_name,
                str(path),
                content_type=content_type
            )
            
            logger.info(f"文件上传成功: {object_name}")
            return object_name
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            return None
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        下载文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bytes: 文件内容
        """
        if not self._client:
            logger.error("MinIO 客户端未初始化")
            return None
        
        try:
            response = self._client.get_object(
                self._bucket_name,
                object_name
            )
            
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"文件下载成功: {object_name}")
            return data
        except Exception as e:
            logger.error(f"文件下载失败: {str(e)}")
            return None
    
    def download_to_file(self, object_name: str, file_path: str) -> bool:
        """
        下载文件到本地
        
        Args:
            object_name: 对象名称
            file_path: 本地文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self._client:
            logger.error("MinIO 客户端未初始化")
            return False
        
        try:
            self._client.fget_object(
                self._bucket_name,
                object_name,
                file_path
            )
            
            logger.info(f"文件下载成功: {object_name} -> {file_path}")
            return True
        except Exception as e:
            logger.error(f"文件下载失败: {str(e)}")
            return False
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600
    ) -> Optional[str]:
        """
        获取预签名 URL
        
        Args:
            object_name: 对象名称
            expires: 过期时间（秒）
            
        Returns:
            str: 预签名 URL
        """
        if not self._client:
            logger.error("MinIO 客户端未初始化")
            return None
        
        try:
            url = self._client.presigned_get_object(
                self._bucket_name,
                object_name,
                expires=timedelta(seconds=expires)
            )
            
            return url
        except Exception as e:
            logger.error(f"获取预签名 URL 失败: {str(e)}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 是否成功
        """
        if not self._client:
            logger.error("MinIO 客户端未初始化")
            return False
        
        try:
            self._client.remove_object(
                self._bucket_name,
                object_name
            )
            
            logger.info(f"文件删除成功: {object_name}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 是否存在
        """
        if not self._client:
            return False
        
        try:
            self._client.stat_object(
                self._bucket_name,
                object_name
            )
            return True
        except Exception:
            return False
    
    def get_file_info(self, object_name: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            object_name: 对象名称
            
        Returns:
            dict: 文件信息
        """
        if not self._client:
            return None
        
        try:
            stat = self._client.stat_object(
                self._bucket_name,
                object_name
            )
            
            return {
                'size': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'metadata': stat.metadata
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None
    
    def list_files(self, prefix: str = '') -> list:
        """
        列出文件
        
        Args:
            prefix: 前缀过滤
            
        Returns:
            list: 文件列表
        """
        if not self._client:
            return []
        
        try:
            objects = self._client.list_objects(
                self._bucket_name,
                prefix=prefix
            )
            
            return [
                {
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                }
                for obj in objects
            ]
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            return []


minio_service = MinIOService()
