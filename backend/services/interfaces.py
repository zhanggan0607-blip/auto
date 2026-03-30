"""
公共服务接口定义

定义了系统中使用的各种服务接口，支持多种实现方式切换
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, BinaryIO


class NotificationServiceInterface(ABC):
    """
    通知服务接口
    
    定义了通知发送的标准接口，支持多种通知渠道实现
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 是否可用
        """
        return True


class StorageServiceInterface(ABC):
    """
    存储服务接口
    
    定义了对象存储的标准接口，支持多种存储后端实现
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        下载文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bytes: 文件内容
        """
        pass
    
    @abstractmethod
    def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 是否存在
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 是否可用
        """
        return True


class OCRServiceInterface(ABC):
    """
    OCR服务接口
    
    定义了文字识别的标准接口，支持多种OCR引擎实现
    """
    
    @abstractmethod
    def recognize_general(
        self,
        image_url: str = None,
        image_content: bytes = None
    ) -> Dict[str, Any]:
        """
        通用文字识别
        
        Args:
            image_url: 图片URL
            image_content: 图片二进制内容
            
        Returns:
            dict: 识别结果
        """
        pass
    
    @abstractmethod
    def recognize_id_card(
        self,
        image_url: str = None,
        image_content: bytes = None,
        side: str = 'face'
    ) -> Dict[str, Any]:
        """
        身份证识别
        
        Args:
            image_url: 图片URL
            image_content: 图片二进制内容
            side: 正反面 (face/back)
            
        Returns:
            dict: 识别结果
        """
        pass
    
    @abstractmethod
    def recognize_business_license(
        self,
        image_url: str = None,
        image_content: bytes = None
    ) -> Dict[str, Any]:
        """
        营业执照识别
        
        Args:
            image_url: 图片URL
            image_content: 图片二进制内容
            
        Returns:
            dict: 识别结果
        """
        pass
    
    def recognize_bank_card(
        self,
        image_url: str = None,
        image_content: bytes = None
    ) -> Dict[str, Any]:
        """
        银行卡识别
        
        Args:
            image_url: 图片URL
            image_content: 图片二进制内容
            
        Returns:
            dict: 识别结果
        """
        return {'success': False, 'error': '未实现'}
    
    def recognize_captcha(
        self,
        image_url: str = None,
        image_content: bytes = None
    ) -> Dict[str, Any]:
        """
        验证码识别
        
        Args:
            image_url: 图片URL
            image_content: 图片二进制内容
            
        Returns:
            dict: 识别结果
        """
        return {'success': False, 'error': '未实现'}
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 是否可用
        """
        return True


class LLMServiceInterface(ABC):
    """
    大语言模型服务接口
    
    定义了LLM调用的标准接口，支持多种模型实现
    """
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        对话补全
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            dict: 响应结果
        """
        pass
    
    @abstractmethod
    def embed(
        self,
        text: str,
        model: str = None
    ) -> Optional[List[float]]:
        """
        文本嵌入
        
        Args:
            text: 输入文本
            model: 模型名称
            
        Returns:
            list: 嵌入向量
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 是否可用
        """
        return True


class VectorStoreInterface(ABC):
    """
    向量存储接口
    
    定义了向量数据库的标准接口，支持多种向量库实现
    """
    
    @abstractmethod
    def add_vectors(
        self,
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ) -> bool:
        """
        添加向量
        
        Args:
            vectors: 向量列表
            metadatas: 元数据列表
            ids: ID列表
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        向量搜索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            filter_dict: 过滤条件
            
        Returns:
            list: 搜索结果
        """
        pass
    
    @abstractmethod
    def delete_vectors(self, ids: List[str]) -> bool:
        """
        删除向量
        
        Args:
            ids: ID列表
            
        Returns:
            bool: 是否成功
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 是否可用
        """
        return True


class CacheServiceInterface(ABC):
    """
    缓存服务接口
    
    定义了缓存的标准接口，支持多种缓存后端实现
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值
        """
        pass
    
    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        timeout: int = None
    ) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 过期时间（秒）
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 是否可用
        """
        return True


class ServiceFactory:
    """
    服务工厂
    
    用于获取各种服务的实例
    """
    
    _notification_service = None
    _storage_service = None
    _ocr_service = None
    _llm_service = None
    _vector_store = None
    _cache_service = None
    
    @classmethod
    def get_notification_service(cls) -> NotificationServiceInterface:
        """
        获取通知服务实例
        """
        if cls._notification_service is None:
            from services.dingtalk_service import DingTalkService
            cls._notification_service = DingTalkService()
        return cls._notification_service
    
    @classmethod
    def get_storage_service(cls) -> StorageServiceInterface:
        """
        获取存储服务实例
        """
        if cls._storage_service is None:
            from services.minio_service import MinIOService
            cls._storage_service = MinIOService()
        return cls._storage_service
    
    @classmethod
    def get_ocr_service(cls) -> OCRServiceInterface:
        """
        获取OCR服务实例
        """
        if cls._ocr_service is None:
            from services.aliyun_ocr_service import AliyunOCRService
            cls._ocr_service = AliyunOCRService()
        return cls._ocr_service
    
    @classmethod
    def get_llm_service(cls) -> LLMServiceInterface:
        """
        获取LLM服务实例
        """
        if cls._llm_service is None:
            from services.unified_llm_service import UnifiedLLMService
            cls._llm_service = UnifiedLLMService()
        return cls._llm_service
    
    @classmethod
    def get_vector_store(cls) -> VectorStoreInterface:
        """
        获取向量存储实例
        """
        if cls._vector_store is None:
            from services.vector import chroma_client
            cls._vector_store = chroma_client
        return cls._vector_store
    
    @classmethod
    def get_cache_service(cls) -> CacheServiceInterface:
        """
        获取缓存服务实例
        """
        if cls._cache_service is None:
            from django.core.cache import cache
            cls._cache_service = DjangoCacheAdapter(cache)
        return cls._cache_service


class DjangoCacheAdapter(CacheServiceInterface):
    """
    Django缓存适配器
    
    将Django缓存适配到CacheServiceInterface
    """
    
    def __init__(self, django_cache):
        self._cache = django_cache
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        self._cache.set(key, value, timeout)
        return True
    
    def delete(self, key: str) -> bool:
        self._cache.delete(key)
        return True
    
    def exists(self, key: str) -> bool:
        return self._cache.get(key) is not None
