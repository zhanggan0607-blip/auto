"""
文件上传安全模块
验证文件真实MIME类型，防止文件伪装攻击
安全改进：使用python-magic检测文件真实类型
"""
import logging
import os
import uuid
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
    'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv'],
    'archive': ['zip', 'rar', '7z', 'tar', 'gz'],
}

ALLOWED_MIME_TYPES = {
    'image/jpeg': ['jpg', 'jpeg'],
    'image/png': ['png'],
    'image/gif': ['gif'],
    'image/bmp': ['bmp'],
    'image/webp': ['webp'],
    'application/pdf': ['pdf'],
    'application/msword': ['doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
    'application/vnd.ms-excel': ['xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
    'application/vnd.ms-powerpoint': ['ppt'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['pptx'],
    'text/plain': ['txt'],
    'text/csv': ['csv'],
    'application/zip': ['zip'],
    'application/x-rar-compressed': ['rar'],
    'application/x-7z-compressed': ['7z'],
    'application/x-tar': ['tar'],
    'application/gzip': ['gz'],
}

MAGIC_SIGNATURES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'BM': 'image/bmp',
    b'RIFF': 'image/webp',
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'application/zip',
}


class FileUploadValidator:
    """
    文件上传验证器
    验证文件真实MIME类型和扩展名
    """

    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,
        allowed_categories: list = None
    ):
        """
        初始化验证器

        Args:
            max_file_size: 最大文件大小（字节），默认10MB
            allowed_categories: 允许的文件类别，默认所有类别
        """
        self.max_file_size = max_file_size
        self.allowed_categories = allowed_categories or list(ALLOWED_EXTENSIONS.keys())

    def get_file_extension(self, filename: str) -> str:
        """
        获取文件扩展名

        Args:
            filename: 文件名

        Returns:
            str: 扩展名（小写，不含点）
        """
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[1].lower()

    def detect_mime_by_signature(self, file_path: str) -> Optional[str]:
        """
        通过文件签名检测真实MIME类型

        Args:
            file_path: 文件路径

        Returns:
            str: MIME类型或None
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)

            for signature, mime_type in MAGIC_SIGNATURES.items():
                if header.startswith(signature):
                    return mime_type

            return None
        except Exception as e:
            logger.error(f"检测文件签名失败: {e}")
            return None

    def detect_mime_by_python_magic(self, file_path: str) -> Optional[str]:
        """
        使用python-magic检测MIME类型

        Args:
            file_path: 文件路径

        Returns:
            str: MIME类型或None
        """
        try:
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except ImportError:
            logger.warning("python-magic未安装，使用文件扩展名检测")
            return None
        except Exception as e:
            logger.error(f"python-magic检测失败: {e}")
            return None

    def get_real_mime_type(self, file_path: str) -> str:
        """
        获取文件真实MIME类型（优先使用magic，其次使用签名）

        Args:
            file_path: 文件路径

        Returns:
            str: MIME类型
        """
        mime_by_magic = self.detect_mime_by_python_magic(file_path)
        if mime_by_magic:
            return mime_by_magic

        mime_by_signature = self.detect_mime_by_signature(file_path)
        if mime_by_signature:
            return mime_by_signature

        return 'application/octet-stream'

    def validate_extension(self, filename: str) -> Tuple[bool, str]:
        """
        验证文件扩展名

        Args:
            filename: 文件名

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        ext = self.get_file_extension(filename)

        if not ext:
            return False, "文件缺少扩展名"

        for category in self.allowed_categories:
            if ext in ALLOWED_EXTENSIONS[category]:
                return True, ""

        return False, f"不允许的文件扩展名: .{ext}"

    def validate_mime_type(self, file_path: str, filename: str) -> Tuple[bool, str]:
        """
        验证MIME类型

        Args:
            file_path: 文件路径
            filename: 文件名

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        real_mime = self.get_real_mime_type(file_path)
        ext = self.get_file_extension(filename)

        if real_mime not in ALLOWED_MIME_TYPES:
            return False, f"不允许的MIME类型: {real_mime}"

        allowed_exts = ALLOWED_MIME_TYPES[real_mime]
        if ext not in allowed_exts:
            return False, f"MIME类型({real_mime})与扩展名(.{ext})不匹配"

        return True, ""

    def validate_file_size(self, file_path: str) -> Tuple[bool, str]:
        """
        验证文件大小

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            size = os.path.getsize(file_path)
            if size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                return False, f"文件大小超过限制({max_mb:.0f}MB)"
            if size == 0:
                return False, "文件为空"
            return True, ""
        except Exception as e:
            return False, f"获取文件大小失败: {e}"

    def validate_file(
        self,
        file_path: str,
        filename: str,
        skip_size_check: bool = False
    ) -> Tuple[bool, str]:
        """
        完整文件验证

        Args:
            file_path: 文件路径
            filename: 文件名
            skip_size_check: 是否跳过大小检查（用于已检查过的情况）

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        is_valid, error = self.validate_extension(filename)
        if not is_valid:
            return False, error

        if not skip_size_check:
            is_valid, error = self.validate_file_size(file_path)
            if not is_valid:
                return False, error

        is_valid, error = self.validate_mime_type(file_path, filename)
        if not is_valid:
            return False, error

        return True, ""

    def generate_secure_filename(self, original_filename: str) -> str:
        """
        生成安全的随机文件名

        Args:
            original_filename: 原始文件名

        Returns:
            str: 安全的新文件名
        """
        ext = self.get_file_extension(original_filename)
        unique_id = uuid.uuid4().hex[:12]
        return f"{unique_id}.{ext}" if ext else unique_id


def validate_upload_file(file_path: str, filename: str) -> Tuple[bool, str]:
    """
    文件上传验证便捷函数

    Args:
        file_path: 文件路径
        filename: 文件名

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    validator = FileUploadValidator()
    return validator.validate_file(file_path, filename)
