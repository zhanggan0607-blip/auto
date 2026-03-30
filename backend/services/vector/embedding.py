"""
Embedding向量化服务
支持多种向量化模型
"""
import logging
from typing import List, Optional
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingModel(ABC):
    """
    Embedding模型基类
    """
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化
        """
        pass


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """
    OpenAI Embedding模型
    """
    
    def __init__(self):
        from openai import OpenAI
        
        api_key = settings.EMBEDDING_CONFIG.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API Key未配置")
        
        self.client = OpenAI(api_key=api_key)
        self.model = settings.EMBEDDING_CONFIG.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    
    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        """
        try:
            text = text.replace("\n", " ").strip()
            if not text:
                return []
            
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI Embedding失败: {str(e)}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化
        """
        try:
            texts = [t.replace("\n", " ").strip() for t in texts]
            texts = [t for t in texts if t]
            
            if not texts:
                return []
            
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI批量Embedding失败: {str(e)}")
            return []


class LocalEmbeddingModel(BaseEmbeddingModel):
    """
    本地Sentence Transformers模型
    """
    
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        
        model_name = settings.EMBEDDING_CONFIG.get('LOCAL_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
        self.model = SentenceTransformer(model_name)
        logger.info(f"本地Embedding模型加载成功: {model_name}")
    
    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        """
        try:
            text = text.replace("\n", " ").strip()
            if not text:
                return []
            
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"本地Embedding失败: {str(e)}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化
        """
        try:
            texts = [t.replace("\n", " ").strip() for t in texts]
            texts = [t for t in texts if t]
            
            if not texts:
                return []
            
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"本地批量Embedding失败: {str(e)}")
            return []


class DummyEmbeddingModel(BaseEmbeddingModel):
    """
    后备Embedding模型
    """
    
    def __init__(self):
        logger.warning("使用Dummy Embedding模型（返回空向量）")
    
    def embed(self, text: str) -> List[float]:
        return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return []


class EmbeddingService:
    """
    Embedding服务
    自动选择可用的模型
    """
    
    _instance = None
    _model = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass
    
    def _ensure_initialized(self):
        """
        确保模型已初始化（延迟初始化）
        """
        if not self._initialized:
            self._initialize_model()
            self._initialized = True
    
    def _initialize_model(self):
        """
        初始化Embedding模型
        """
        model_type = settings.EMBEDDING_CONFIG.get('MODEL_TYPE', 'openai')
        
        try:
            if model_type == 'openai':
                self._model = OpenAIEmbeddingModel()
                logger.info("使用OpenAI Embedding模型")
            else:
                self._model = LocalEmbeddingModel()
                logger.info("使用本地Embedding模型")
        except Exception as e:
            logger.warning(f"初始化{model_type}模型失败: {str(e)}")
            try:
                if model_type != 'local':
                    self._model = LocalEmbeddingModel()
                    logger.info("回退到本地Embedding模型")
                else:
                    raise e
            except Exception as e2:
                logger.error(f"本地模型也失败: {str(e2)}")
                self._model = DummyEmbeddingModel()
                logger.warning("使用Dummy模型作为后备")
    
    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        """
        self._ensure_initialized()
        return self._model.embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化
        """
        self._ensure_initialized()
        return self._model.embed_batch(texts)
    
    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        """
        import numpy as np
        
        if not vec1 or not vec2:
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


embedding_service = EmbeddingService()
