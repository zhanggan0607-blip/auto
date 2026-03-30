"""
加密工具模块
提供通用的加密解密函数
"""
import os
import hashlib
import hmac
import base64
from typing import Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    Fernet = None


def generate_random_string(length: int = 32) -> str:
    """
    生成随机字符串

    Args:
        length: 字符串长度

    Returns:
        str: 随机字符串
    """
    import string
    import secrets

    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_string(text: str, algorithm: str = 'sha256', salt: str = None) -> str:
    """
    对字符串进行哈希

    Args:
        text: 原始字符串
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256', 'sha512')
        salt: 盐值（可选）

    Returns:
        str: 哈希后的字符串
    """
    if not text:
        return ''

    if salt:
        text = f'{text}{salt}'

    if algorithm == 'md5':
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode('utf-8')).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(text.encode('utf-8')).hexdigest()

    return ''


def hmac_hash(message: str, key: str, algorithm: str = 'sha256') -> str:
    """
    生成HMAC哈希

    Args:
        message: 消息
        key: 密钥
        algorithm: 哈希算法

    Returns:
        str: HMAC哈希值
    """
    if algorithm == 'sha256':
        return hmac.new(
            key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    elif algorithm == 'sha512':
        return hmac.new(
            key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

    return ''


def encrypt_aes(text: str, key: str = None) -> Optional[str]:
    """
    AES加密（Fernet对称加密）

    Args:
        text: 原始文本
        key: 密钥（可选，不提供则自动生成）

    Returns:
        str: 加密后的文本（base64编码）或 None
    """
    if Fernet is None:
        return None

    if key is None:
        key = os.environ.get('ENCRYPTION_KEY', '')

    if not key:
        key = Fernet.generate_key()
    elif len(key) < 32:
        key = key.zfill(32)[:32]

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'bid_auto_system',
        iterations=100000,
    )
    key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))

    f = Fernet(key_bytes)
    encrypted = f.encrypt(text.encode('utf-8'))

    return base64.urlsafe_b64encode(encrypted).decode('utf-8')


def decrypt_aes(encrypted_text: str, key: str = None) -> Optional[str]:
    """
    AES解密

    Args:
        encrypted_text: 加密文本（base64编码）
        key: 密钥

    Returns:
        str: 解密后的文本或 None
    """
    if Fernet is None:
        return None

    if key is None:
        key = os.environ.get('ENCRYPTION_KEY', '')

    if not key:
        return None

    if len(key) < 32:
        key = key.zfill(32)[:32]

    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'bid_auto_system',
            iterations=100000,
        )
        key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode()))

        f = Fernet(key_bytes)
        decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_text))

        return decrypted.decode('utf-8')
    except Exception:
        return None


def generate_token(prefix: str = '') -> str:
    """
    生成随机Token

    Args:
        prefix: 前缀

    Returns:
        str: Token
    """
    import secrets
    token = secrets.token_urlsafe(32)

    if prefix:
        return f'{prefix}_{token}'

    return token
