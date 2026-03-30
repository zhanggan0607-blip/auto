"""
敏感数据加密工具模块

使用AES-256加密算法保护敏感数据
"""
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from django.conf import settings


class AESCrypto:
    """
    AES-256加密工具类
    
    使用CBC模式，PKCS7填充
    """
    
    KEY_SIZE = 32  # AES-256
    IV_SIZE = 16   # AES块大小
    
    @classmethod
    def _get_key(cls) -> bytes:
        """
        从Django SECRET_KEY派生加密密钥
        """
        secret_key = getattr(settings, 'SENSITIVE_DATA_ENCRYPTION_KEY', None)
        if not secret_key:
            secret_key = settings.SECRET_KEY
        
        key = hashlib.sha256(secret_key.encode()).digest()
        return key[:cls.KEY_SIZE]
    
    @classmethod
    def _pad(cls, data: str) -> bytes:
        """
        PKCS7填充
        """
        data_bytes = data.encode('utf-8')
        padding_len = cls.IV_SIZE - (len(data_bytes) % cls.IV_SIZE)
        padding = bytes([padding_len] * padding_len)
        return data_bytes + padding
    
    @classmethod
    def _unpad(cls, data: bytes) -> str:
        """
        移除PKCS7填充
        """
        padding_len = data[-1]
        return data[:-padding_len].decode('utf-8')
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            Base64编码的密文（包含IV）
        """
        if not plaintext:
            return ''
        
        key = cls._get_key()
        iv = os.urandom(cls.IV_SIZE)
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        padded_data = cls._pad(plaintext)
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        encrypted = iv + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: Base64编码的密文（包含IV）
            
        Returns:
            明文字符串
        """
        if not ciphertext:
            return ''
        
        try:
            key = cls._get_key()
            encrypted = base64.b64decode(ciphertext.encode('utf-8'))
            
            iv = encrypted[:cls.IV_SIZE]
            actual_ciphertext = encrypted[cls.IV_SIZE:]
            
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            padded_data = decryptor.update(actual_ciphertext) + decryptor.finalize()
            return cls._unpad(padded_data)
        except Exception:
            return ''
    
    @classmethod
    def mask_id_number(cls, id_number: str) -> str:
        """
        身份证号脱敏显示
        
        Args:
            id_number: 身份证号
            
        Returns:
            脱敏后的身份证号（显示前3位和后4位）
        """
        if not id_number or len(id_number) < 8:
            return id_number or ''
        return f"{id_number[:3]}{'*' * (len(id_number) - 7)}{id_number[-4:]}"
    
    @classmethod
    def mask_bank_account(cls, account: str) -> str:
        """
        银行账号脱敏显示
        
        Args:
            account: 银行账号
            
        Returns:
            脱敏后的银行账号（显示前4位和后4位）
        """
        if not account or len(account) < 9:
            return account or ''
        return f"{account[:4]}{'*' * (len(account) - 8)}{account[-4:]}"
    
    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """
        手机号脱敏显示
        
        Args:
            phone: 手机号
            
        Returns:
            脱敏后的手机号（显示前3位和后4位）
        """
        if not phone or len(phone) < 8:
            return phone or ''
        return f"{phone[:3]}{'*' * (len(phone) - 7)}{phone[-4:]}"


class EncryptedFieldMixin:
    """
    加密字段混入类
    
    用于模型字段的加密/解密处理
    """
    
    def __init__(self, *args, **kwargs):
        self._encrypt = kwargs.pop('encrypt', True)
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """
        保存前加密
        """
        if value and self._encrypt:
            value = AESCrypto.encrypt(str(value))
        return super().get_prep_value(value)
    
    def from_db_value(self, value, expression, connection):
        """
        从数据库读取后解密
        """
        if value and self._encrypt:
            value = AESCrypto.decrypt(value)
        return value
    
    def to_python(self, value):
        """
        反序列化时解密
        """
        if value and self._encrypt:
            value = AESCrypto.decrypt(value)
        return value


def encrypt_sensitive_data(data: str) -> str:
    """
    加密敏感数据的便捷函数
    
    Args:
        data: 敏感数据
        
    Returns:
        加密后的数据
    """
    return AESCrypto.encrypt(data)


def decrypt_sensitive_data(data: str) -> str:
    """
    解密敏感数据的便捷函数
    
    Args:
        data: 加密数据
        
    Returns:
        解密后的数据
    """
    return AESCrypto.decrypt(data)


def mask_sensitive_data(data: str, data_type: str = 'id_number') -> str:
    """
    脱敏显示敏感数据
    
    Args:
        data: 敏感数据
        data_type: 数据类型 ('id_number', 'bank_account', 'phone')
        
    Returns:
        脱敏后的数据
    """
    mask_functions = {
        'id_number': AESCrypto.mask_id_number,
        'bank_account': AESCrypto.mask_bank_account,
        'phone': AESCrypto.mask_phone,
    }
    
    mask_func = mask_functions.get(data_type, lambda x: x)
    return mask_func(data)
