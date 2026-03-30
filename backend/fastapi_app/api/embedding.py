"""
向量检索相关API接口
直连Milvus分布式集群进行高性能向量检索
"""
import asyncio
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from fastapi_app.services.milvus_client import milvus_cluster_client

logger = logging.getLogger(__name__)
router = APIRouter()


class VectorSearchRequest(BaseModel):
    """向量检索请求"""
    query_text: str = Field(..., description="查询文本")
    top_k: int = Field(default=10, ge=1, le=100, description="返回数量")
    collection_name: str = Field(default="enterprise_embeddings", description="集合名称")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")


class VectorSearchResult(BaseModel):
    """向量检索结果"""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]


class VectorAddRequest(BaseModel):
    """添加向量请求"""
    collection_name: str = Field(default="enterprise_embeddings", description="集合名称")
    texts: List[str] = Field(..., description="文本列表")
    metadatas: Optional[List[Dict[str, Any]]] = Field(default=None, description="元数据列表")


class VectorDeleteRequest(BaseModel):
    """删除向量请求"""
    collection_name: str = Field(default="enterprise_embeddings", description="集合名称")
    ids: List[str] = Field(..., description="向量ID列表")


@router.post("/search/", response_model=List[VectorSearchResult])
async def search_vectors(request: VectorSearchRequest):
    """
    向量语义检索
    将查询文本向量化后，在Milvus分布式集群中检索相似文本
    """
    try:
        query_vector = _get_embedding_sync(request.query_text)

        if not query_vector:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")

        results = await milvus_cluster_client.search(
            collection_name=request.collection_name,
            query_vector=query_vector,
            top_k=request.top_k,
            filters=request.filters,
        )

        return results

    except Exception as e:
        logger.error(f"向量检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_embedding_sync(text: str) -> List[float]:
    """同步获取embedding"""
    from services.vector.embedding import embedding_service
    return embedding_service.embed(text)


@router.post("/add/")
async def add_vectors(request: VectorAddRequest, background_tasks: BackgroundTasks):
    """
    批量添加向量
    将文本向量化后存入Milvus分布式集群
    """
    try:
        from services.vector.embedding import embedding_service

        texts = request.texts
        embeddings = embedding_service.embed_batch(texts)

        if not embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate embeddings")

        vectors_data = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            metadata = request.metadatas[i] if request.metadatas and i < len(request.metadatas) else {}
            vectors_data.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "vector": embedding,
                "metadata": metadata,
                "created_at": datetime.now().timestamp(),
            })

        ids = await milvus_cluster_client.insert(
            collection_name=request.collection_name,
            data=vectors_data,
        )

        return {
            "status": "success",
            "count": len(texts),
            "ids": ids,
        }

    except Exception as e:
        logger.error(f"添加向量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete/")
async def delete_vectors(request: VectorDeleteRequest):
    """
    删除向量
    """
    try:
        success = await milvus_cluster_client.delete(
            collection_name=request.collection_name,
            ids=request.ids,
        )

        return {
            "status": "success" if success else "failed",
            "count": len(request.ids),
        }

    except Exception as e:
        logger.error(f"删除向量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/")
async def list_collections():
    """
    获取所有集合
    """
    try:
        health = await milvus_cluster_client.health_check()
        return health

    except Exception as e:
        logger.error(f"获取集合列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/")
async def create_collection(collection_name: str, dimension: int = 1536):
    """
    创建集合
    """
    try:
        await milvus_cluster_client.create_collection_if_not_exists(
            collection_name=collection_name,
            dimension=dimension,
        )

        return {
            "status": "success",
            "collection_name": collection_name,
            "dimension": dimension,
        }

    except Exception as e:
        logger.error(f"创建集合失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/")
async def milvus_health_check():
    """
    Milvus分布式集群健康检查
    """
    try:
        health = await milvus_cluster_client.health_check()
        return health

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/stats/{collection_name}/")
async def get_collection_stats(collection_name: str):
    """
    获取集合统计信息
    """
    try:
        stats = await milvus_cluster_client.get_collection_stats(collection_name)
        return stats

    except Exception as e:
        logger.error(f"获取集合统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
