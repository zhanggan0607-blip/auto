"""
敏感数据加密工具模块

使用AES-256-GCM加密算法保护敏感数据
GCM模式同时提供加密和完整性校验
"""
import os
import base64
import hashlib
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from django.conf import settings

logger = logging.getLogger(__name__)


class AESCrypto:
    KEY_SIZE = 32
    IV_SIZE = 12
    TAG_SIZE = 16

    @classmethod
    def _get_key(cls) -> bytes:
        secret_key = getattr(settings, 'SENSITIVE_DATA_ENCRYPTION_KEY', None)
        if not secret_key:
            secret_key = settings.SECRET_KEY
        key = hashlib.sha256(secret_key.encode()).digest()
        return key[:cls.KEY_SIZE]

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        if not plaintext:
            return ''

        key = cls._get_key()
        iv = os.urandom(cls.IV_SIZE)

        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        data = plaintext.encode('utf-8')
        ciphertext = encryptor.update(data) + encryptor.finalize()

        encrypted = iv + encryptor.tag + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        if not ciphertext:
            return ''

        try:
            key = cls._get_key()
            encrypted = base64.b64decode(ciphertext.encode('utf-8'))

            iv = encrypted[:cls.IV_SIZE]
            tag = encrypted[cls.IV_SIZE:cls.IV_SIZE + cls.TAG_SIZE]
            actual_ciphertext = encrypted[cls.IV_SIZE + cls.TAG_SIZE:]

            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.error(f"AES-GCM解密失败: {e}")
            raise ValueError(f"解密失败: {e}")

    @classmethod
    def decrypt_cbc(cls, ciphertext: str) -> str:
        """
        兼容旧CBC模式数据的解密
        用于迁移期间解密旧数据
        """
        if not ciphertext:
            return ''

        try:
            key = cls._get_key()
            encrypted = base64.b64decode(ciphertext.encode('utf-8'))

            iv = encrypted[:16]
            actual_ciphertext = encrypted[16:]

            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            padded_data = decryptor.update(actual_ciphertext) + decryptor.finalize()
            padding_len = padded_data[-1]
            return padded_data[:-padding_len].decode('utf-8')
        except Exception as e:
            logger.error(f"AES-CBC兼容解密失败: {e}")
            raise ValueError(f"解密失败: {e}")

    @classmethod
    def decrypt_auto(cls, ciphertext: str) -> str:
        """
        自动检测加密模式并解密
        GCM: IV(12) + TAG(16) + ciphertext
        CBC: IV(16) + ciphertext
        """
        if not ciphertext:
            return ''

        try:
            return cls.decrypt(ciphertext)
        except ValueError:
            try:
                return cls.decrypt_cbc(ciphertext)
            except ValueError:
                raise ValueError("解密失败: 无法识别加密模式")


class EncryptedFieldMixin:
    def __init__(self, *args, **kwargs):
        self._encrypt = kwargs.pop('encrypt', True)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value and self._encrypt:
            value = AESCrypto.encrypt(str(value))
        return super().get_prep_value(value)

    def from_db_value(self, value, expression, connection):
        if value and self._encrypt:
            try:
                value = AESCrypto.decrypt_auto(value)
            except ValueError as e:
                logger.warning(f"字段解密失败，返回原始值: {e}")
        return value

    def to_python(self, value):
        if value and self._encrypt:
            try:
                value = AESCrypto.decrypt_auto(value)
            except ValueError as e:
                logger.warning(f"字段解密失败，返回原始值: {e}")
        return value


def encrypt_sensitive_data(data: str) -> str:
    return AESCrypto.encrypt(data)


def decrypt_sensitive_data(data: str) -> str:
    return AESCrypto.decrypt_auto(data)


def mask_sensitive_data(data: str, data_type: str = 'id_number') -> str:
    from core.sensitive_mask import SensitiveFieldMasker
    mask_map = {
        'id_number': 'id_card',
        'bank_account': 'bank_account',
        'phone': 'phone',
    }
    field_name = mask_map.get(data_type, data_type)
    return SensitiveFieldMasker.mask(field_name, data)
