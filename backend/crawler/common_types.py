"""
爬虫模块 - 共享数据类型定义
包含爬虫系统中使用的通用数据类，避免重复定义
"""
import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CrawlResult:
    """采集结果数据类"""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    strategy: str = ''
    error_message: str = ''
    retry_count: int = 0
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    server: str = ''
    username: str = ''
    password: str = ''
    proxy_list: List[str] = field(default_factory=list)
    current_index: int = 0

    def get_next_proxy(self) -> Optional[str]:
        """获取下一个代理（轮换）"""
        if not self.proxy_list:
            return self.server
        proxy = self.proxy_list[self.current_index % len(self.proxy_list)]
        self.current_index += 1
        return proxy

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        if not self.enabled or not self.server:
            return {}
        return {
            'server': self.server,
            'username': self.username,
            'password': self.password
        }


@dataclass
class BrowserFingerprint:
    """浏览器指纹配置"""
    user_agent: str = ''
    viewport: Dict[str, int] = field(default_factory=lambda: {'width': 1920, 'height': 1080})
    locale: str = 'zh-CN'
    timezone: str = 'Asia/Shanghai'
    timezone_offset: int = -480
    platform: str = 'Win32'
    webgl_vendor: str = 'Google Inc. (Intel)'
    webgl_renderer: str = 'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.6)'
    hardware_concurrency: int = 8
    device_memory: int = 8
    canvas_noise: str = ''
    audio_noise: str = ''
    screen: Dict[str, int] = field(default_factory=lambda: {'width': 1920, 'height': 1080, 'colorDepth': 24})

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    ]

    VIEWPORTS = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900},
        {'width': 2560, 'height': 1440},
    ]

    WEBGL_RENDERERS = [
        ('Google Inc. (Intel)', 'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.6)'),
        ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060, OpenGL 4.6)'),
        ('Google Inc. (AMD)', 'ANGLE (AMD, AMD Radeon RX 580, OpenGL 4.6)'),
        ('Intel Inc.', 'Intel Iris OpenGL Engine'),
    ]

    @classmethod
    def random_fingerprint(cls) -> 'BrowserFingerprint':
        """生成随机浏览器指纹"""
        canvas_noise = hashlib.md5(str(random.random()).encode()).hexdigest()[:16]
        audio_noise = f"{random.uniform(124.0434, 124.0435):.4f}"
        webgl_vendor, webgl_renderer = random.choice(cls.WEBGL_RENDERERS)

        return cls(
            user_agent=random.choice(cls.USER_AGENTS),
            viewport=random.choice(cls.VIEWPORTS),
            hardware_concurrency=random.choice([4, 8, 12, 16]),
            device_memory=random.choice([4, 8, 16]),
            canvas_noise=canvas_noise,
            audio_noise=audio_noise,
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            screen={'width': 1920, 'height': 1080, 'colorDepth': 24},
        )