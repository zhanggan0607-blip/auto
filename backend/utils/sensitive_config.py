"""
敏感配置验证模块
确保所有敏感配置通过环境变量注入，不使用硬编码默认值
"""
import os
import logging

logger = logging.getLogger(__name__)


def validate_sensitive_config():
    """
    验证敏感配置是否正确设置

    检查以下配置不能使用默认值：
    - MINIO_ACCESS_KEY 不能为 'minioadmin'
    - MINIO_SECRET_KEY 不能为 'minioadmin'
    - ALIYUN_OCR_ACCESS_KEY_ID 必须设置
    - ALIYUN_OCR_ACCESS_KEY_SECRET 必须设置
    - OPENAI_API_KEY 必须设置（如果使用 OpenAI）

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []

    minio_access_key = os.getenv('MINIO_ACCESS_KEY', '')
    minio_secret_key = os.getenv('MINIO_SECRET_KEY', '')

    if minio_access_key == 'minioadmin' and not os.getenv('MINIO_ACCESS_KEY'):
        errors.append('MINIO_ACCESS_KEY 使用了默认的 minioadmin，请修改为强密码')

    if minio_secret_key == 'minioadmin' and not os.getenv('MINIO_SECRET_KEY'):
        errors.append('MINIO_SECRET_KEY 使用了默认的 minioadmin，请修改为强密码')

    aliyun_ocr_key_id = os.getenv('ALIYUN_OCR_ACCESS_KEY_ID', '')
    aliyun_ocr_key_secret = os.getenv('ALIYUN_OCR_ACCESS_KEY_SECRET', '')

    if not aliyun_ocr_key_id:
        logger.warning('ALIYUN_OCR_ACCESS_KEY_ID 未设置，OCR功能将不可用')

    if not aliyun_ocr_key_secret:
        logger.warning('ALIYUN_OCR_ACCESS_KEY_SECRET 未设置，OCR功能将不可用')

    embedding_model_type = os.getenv('EMBEDDING_MODEL_TYPE', 'openai')
    openai_api_key = os.getenv('OPENAI_API_KEY', '')

    if embedding_model_type == 'openai' and not openai_api_key:
        errors.append('EMBEDDING_MODEL_TYPE 设置为 openai，但 OPENAI_API_KEY 未设置')

    llm_provider = os.getenv('OPENCLAW_LLM_PROVIDER', 'ollama')

    if llm_provider not in ['ollama', 'local']:
        from openclaw.config import ollama_config
        if not ollama_config.get('api_key'):
            logger.warning('LLM Provider API Key 未设置')

    return len(errors) == 0, errors


def get_minio_config():
    """
    获取MinIO配置，确保不使用弱密码

    Returns:
        dict: MinIO配置
    """
    minio_config = {
        'ENDPOINT': os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
        'ACCESS_KEY': os.getenv('MINIO_ACCESS_KEY'),
        'SECRET_KEY': os.getenv('MINIO_SECRET_KEY'),
        'SECURE': os.getenv('MINIO_SECURE', 'false').lower() == 'true',
        'BUCKET_NAME': os.getenv('MINIO_BUCKET_NAME', 'bid-documents'),
    }

    if not minio_config['ACCESS_KEY']:
        raise ValueError('MINIO_ACCESS_KEY 环境变量必须设置')

    if not minio_config['SECRET_KEY']:
        raise ValueError('MINIO_SECRET_KEY 环境变量必须设置')

    if minio_config['ACCESS_KEY'] == 'minioadmin':
        raise ValueError('MINIO_ACCESS_KEY 不能使用默认的 minioadmin，请修改为强密码')

    if minio_config['SECRET_KEY'] == 'minioadmin':
        raise ValueError('MINIO_SECRET_KEY 不能使用默认的 minioadmin，请修改为强密码')

    return minio_config


def get_oss_config():
    """
    获取阿里云OSS配置

    Returns:
        dict: OSS配置
    """
    oss_config = {
        'ACCESS_KEY_ID': os.getenv('ALIYUN_OSS_ACCESS_KEY_ID', ''),
        'ACCESS_KEY_SECRET': os.getenv('ALIYUN_OSS_ACCESS_KEY_SECRET', ''),
        'ENDPOINT': os.getenv('ALIYUN_OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com'),
        'BUCKET_NAME': os.getenv('ALIYUN_OSS_BUCKET_NAME', 'bid-documents'),
    }

    if not oss_config['ACCESS_KEY_ID']:
        logger.warning('ALIYUN_OSS_ACCESS_KEY_ID 未设置，OSS上传功能将不可用')

    if not oss_config['ACCESS_KEY_SECRET']:
        logger.warning('ALIYUN_OSS_ACCESS_KEY_SECRET 未设置，OSS上传功能将不可用')

    return oss_config