"""
Embedding向量化服务
支持多种向量化模型
"""
import json
import logging
import urllib.request
import urllib.error
import numpy as np
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


class OllamaEmbeddingModel(BaseEmbeddingModel):
    """
    Ollama Embedding模型
    通过Ollama的/api/embeddings端点获取向量
    """

    OLLAMA_MODEL_DIMENSIONS = {
        'nomic-embed-text': 768,
        'mxbai-embed-large': 1024,
        'bge-m3': 1024,
        'all-minilm': 384,
    }

    def __init__(self):
        self.base_url = settings.EMBEDDING_CONFIG.get(
            'OLLAMA_BASE_URL',
            settings.OPENCLAW_CONFIG.get('LLM_BASE_URL', 'http://localhost:11434')
        )
        self.model = settings.EMBEDDING_CONFIG.get(
            'OLLAMA_EMBEDDING_MODEL',
            settings.OPENCLAW_CONFIG.get('EMBEDDING_MODEL', 'nomic-embed-text')
        )
        self._dimension = self.OLLAMA_MODEL_DIMENSIONS.get(self.model, 768)
        self._test_connection()
        logger.info(f"使用Ollama Embedding模型: {self.model}, dimension={self._dimension}")

    def _test_connection(self):
        try:
            req = urllib.request.Request(f'{self.base_url}/api/version')
            resp = urllib.request.urlopen(req, timeout=5)
            logger.info(f"Ollama连接测试成功: {resp.status}")
        except Exception as e:
            raise ConnectionError(f"Ollama服务不可用: {e}")

    def embed(self, text: str) -> List[float]:
        try:
            text = text.replace("\n", " ").strip()
            if not text:
                return []
            payload = json.dumps({
                'model': self.model,
                'prompt': text
            }).encode()
            req = urllib.request.Request(
                f'{self.base_url}/api/embeddings',
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            return data.get('embedding', [])
        except Exception as e:
            logger.error(f"Ollama Embedding失败: {str(e)}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            results.append(self.embed(text))
        return results


class DummyEmbeddingModel(BaseEmbeddingModel):
    
    def __init__(self):
        logger.error("所有Embedding模型均不可用，向量搜索功能将无法正常工作！")
        self._available = False
    
    @property
    def available(self):
        return False
    
    def embed(self, text: str) -> List[float]:
        raise RuntimeError("Embedding模型不可用，请检查Ollama/OpenAI服务配置")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise RuntimeError("Embedding模型不可用，请检查Ollama/OpenAI服务配置")


class EmbeddingService:
    """
    Embedding服务
    自动选择可用的模型
    """

    _instance = None
    _model = None
    _initialized = False
    _dimension = None

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
        优先级: ollama > openai > local > dummy
        """
        model_type = settings.EMBEDDING_CONFIG.get('MODEL_TYPE', 'ollama')

        init_chain = []
        if model_type == 'ollama':
            init_chain = [
                ('ollama', OllamaEmbeddingModel, 768),
                ('local', LocalEmbeddingModel, 384),
            ]
        elif model_type == 'openai':
            init_chain = [
                ('openai', OpenAIEmbeddingModel, 1536),
                ('ollama', OllamaEmbeddingModel, 768),
                ('local', LocalEmbeddingModel, 384),
            ]
        elif model_type == 'local':
            init_chain = [
                ('local', LocalEmbeddingModel, 384),
                ('ollama', OllamaEmbeddingModel, 768),
            ]
        else:
            init_chain = [
                ('ollama', OllamaEmbeddingModel, 768),
            ]

        for name, model_class, dimension in init_chain:
            try:
                self._model = model_class()
                self._dimension = dimension
                if hasattr(self._model, '_dimension'):
                    self._dimension = self._model._dimension
                logger.info(f"使用{name} Embedding模型, dimension={self._dimension}")
                return
            except Exception as e:
                logger.warning(f"初始化{name}模型失败: {str(e)}")
                continue

        self._model = DummyEmbeddingModel()
        self._dimension = 0
        logger.warning("所有Embedding模型均不可用，使用Dummy模型作为后备")

    @property
    def dimension(self) -> int:
        """
        获取当前模型的向量维度
        """
        self._ensure_initialized()
        return self._dimension

    def get_dimension_for_model(self, model_type: str) -> int:
        """
        获取指定模型类型的向量维度
        """
        DIMENSION_MAP = {
            'openai': 1536,
            'local': 384,
            'ollama': 768,
        }
        return DIMENSION_MAP.get(model_type, 0)
    
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
