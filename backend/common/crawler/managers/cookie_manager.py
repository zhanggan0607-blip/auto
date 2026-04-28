"""
Cookie 管理器
提供统一的Cookie存储、验证、格式化功能
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CookieManager:
    """
    Cookie 管理器
    支持：
    - Cookie 存储（内存 + 文件持久化）
    - Cookie 有效期检查
    - Cookie 导入/导出
    - 多平台支持
    - 多种格式输出（浏览器、Playwright、Scrapling）
    """

    DEFAULT_COOKIE_DIR = Path('storage/cookies')
    DEFAULT_EXPIRE_HOURS = 24

    DEFAULT_PLATFORMS = {
        'tianyancha': {
            'domain': '.tianyancha.com',
            'login_url': 'https://www.tianyancha.com/login',
            'check_url': 'https://www.tianyancha.com/user/index',
            'essential_cookies': ['auth_token', 'TYCID', 'ssuid'],
        },
        'qichacha': {
            'domain': '.qcc.com',
            'login_url': 'https://www.qcc.com/weblogin',
            'check_url': 'https://www.qcc.com/user/home',
            'essential_cookies': ['QCCSESSID', 'token', 'userId'],
        },
        'aiqicha': {
            'domain': '.baidu.com',
            'login_url': 'https://passport.baidu.com/',
            'check_url': 'https://aiqicha.baidu.com/usercenter',
            'essential_cookies': ['BDUSS', 'STOKEN', 'BAIDUID'],
        },
        'qixin': {
            'domain': '.qixin.com',
            'login_url': 'https://www.qixin.com/login',
            'check_url': 'https://www.qixin.com/user',
            'essential_cookies': ['qixin_token', 'session_id'],
        },
        'gsxt': {
            'domain': '.gsxt.gov.cn',
            'login_url': 'https://www.gsxt.gov.cn/',
            'check_url': 'https://www.gsxt.gov.cn/usercenter',
            'essential_cookies': ['JSESSIONID', 'token'],
        },
    }

    def __init__(
        self,
        cookie_dir: str = None,
        platforms: Dict[str, Dict] = None,
        expire_hours: int = None
    ):
        """
        初始化 Cookie 管理器

        Args:
            cookie_dir: Cookie存储目录
            platforms: 自定义平台配置
            expire_hours: 默认过期时间（小时）
        """
        self._cookie_dir = Path(cookie_dir) if cookie_dir else self.DEFAULT_COOKIE_DIR
        self._platforms = platforms or self.DEFAULT_PLATFORMS.copy()
        self._expire_hours = expire_hours or self.DEFAULT_EXPIRE_HOURS
        self._cookies: Dict[str, Dict[str, Any]] = {}

        self._ensure_storage_dir()
        self._load_all_cookies()

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self._cookie_dir.mkdir(parents=True, exist_ok=True)

    def _get_cookie_file(self, platform: str) -> Path:
        """获取Cookie存储文件路径"""
        return self._cookie_dir / f"{platform}_cookies.json"

    def _load_all_cookies(self):
        """加载所有平台的Cookie"""
        for platform in self._platforms:
            self._load_cookies(platform)

    def _load_cookies(self, platform: str) -> bool:
        """从文件加载Cookie"""
        cookie_file = self._get_cookie_file(platform)

        if not cookie_file.exists():
            return False

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if self._is_cookie_expired(data):
                logger.info(f"Cookie 已过期: {platform}")
                return False

            self._cookies[platform] = data
            logger.info(f"加载 Cookie 成功: {platform}")
            return True

        except Exception as e:
            logger.error(f"加载 Cookie 失败 {platform}: {str(e)}")
            return False

    def _is_cookie_expired(self, cookie_data: Dict) -> bool:
        """检查Cookie是否过期"""
        if not cookie_data:
            return True

        expire_at = cookie_data.get('expire_at')
        if not expire_at:
            return True

        try:
            expire_time = datetime.fromisoformat(expire_at)
            return datetime.now() > expire_time
        except (ValueError, TypeError):
            return True

    def save_cookies(
        self,
        platform: str,
        cookies: List[Dict],
        expire_hours: int = None,
        metadata: Dict = None
    ) -> bool:
        """
        保存Cookie

        Args:
            platform: 平台名称
            cookies: Cookie列表（浏览器格式）
            expire_hours: 过期时间（小时）
            metadata: 额外元数据

        Returns:
            bool: 是否保存成功
        """
        if platform not in self._platforms:
            logger.error(f"不支持的平台: {platform}")
            return False

        expire_hours = expire_hours or self._expire_hours
        expire_at = datetime.now() + timedelta(hours=expire_hours)

        cookie_data = {
            'platform': platform,
            'cookies': cookies,
            'expire_at': expire_at.isoformat(),
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {},
        }

        self._cookies[platform] = cookie_data

        cookie_file = self._get_cookie_file(platform)
        try:
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, ensure_ascii=False, indent=2)

            logger.info(f"保存 Cookie 成功: {platform}, 过期时间: {expire_at}")
            return True

        except Exception as e:
            logger.error(f"保存 Cookie 失败 {platform}: {str(e)}")
            return False

    def get_cookies(self, platform: str) -> Optional[List[Dict]]:
        """
        获取Cookie

        Args:
            platform: 平台名称

        Returns:
            List[Dict]: Cookie列表
        """
        if platform not in self._cookies:
            return None

        cookie_data = self._cookies[platform]

        if self._is_cookie_expired(cookie_data):
            logger.warning(f"Cookie 已过期: {platform}")
            return None

        return cookie_data.get('cookies', [])

    def get_cookies_for_playwright(self, platform: str) -> Optional[List[Dict]]:
        """
        获取 Playwright 格式的 Cookie

        Args:
            platform: 平台名称

        Returns:
            List[Dict]: Playwright Cookie格式
        """
        cookies = self.get_cookies(platform)
        if not cookies:
            return None

        platform_config = self._platforms.get(platform, {})
        domain = platform_config.get('domain', '')

        playwright_cookies = []
        for cookie in cookies:
            pw_cookie = {
                'name': cookie.get('name', ''),
                'value': cookie.get('value', ''),
                'domain': cookie.get('domain', domain),
                'path': cookie.get('path', '/'),
            }

            if cookie.get('secure'):
                pw_cookie['secure'] = True
            if cookie.get('httpOnly'):
                pw_cookie['httpOnly'] = True

            playwright_cookies.append(pw_cookie)

        return playwright_cookies

    def get_cookies_for_scrapling(self, platform: str) -> Optional[Dict[str, str]]:
        """
        获取 Scrapling 格式的 Cookie（字典格式）

        Args:
            platform: 平台名称

        Returns:
            Dict[str, str]: Cookie字典
        """
        cookies = self.get_cookies(platform)
        if not cookies:
            return None

        return {c.get('name'): c.get('value') for c in cookies if c.get('name')}

    def get_cookies_string(self, platform: str) -> Optional[str]:
        """
        获取 Cookie 字符串格式

        Args:
            platform: 平台名称

        Returns:
            str: Cookie字符串
        """
        cookies = self.get_cookies(platform)
        if not cookies:
            return None

        return '; '.join([f"{c.get('name')}={c.get('value')}" for c in cookies if c.get('name')])

    def has_valid_cookies(self, platform: str) -> bool:
        """检查是否有有效的Cookie"""
        return self.get_cookies(platform) is not None

    def clear_cookies(self, platform: str = None):
        """清除Cookie"""
        if platform:
            if platform in self._cookies:
                del self._cookies[platform]
            cookie_file = self._get_cookie_file(platform)
            if cookie_file.exists():
                cookie_file.unlink()
            logger.info(f"清除 Cookie: {platform}")
        else:
            self._cookies.clear()
            for pf in self._platforms:
                cookie_file = self._get_cookie_file(pf)
                if cookie_file.exists():
                    cookie_file.unlink()
            logger.info("清除所有 Cookie")

    def import_from_browser(
        self,
        platform: str,
        cookie_string: str = None,
        cookie_json: str = None,
        cookie_list: List[Dict] = None
    ) -> bool:
        """
        从浏览器导入Cookie

        Args:
            platform: 平台名称
            cookie_string: Cookie字符串格式 (name=value; name2=value2)
            cookie_json: JSON格式字符串
            cookie_list: Cookie列表

        Returns:
            bool: 是否导入成功
        """
        cookies = []

        if cookie_list:
            cookies = cookie_list
        elif cookie_json:
            try:
                cookies = json.loads(cookie_json)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"解析Cookie JSON失败")
                pass
        elif cookie_string:
            for item in cookie_string.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                    })

        if not cookies:
            logger.error("未提供有效的Cookie数据")
            return False

        return self.save_cookies(platform, cookies)

    def get_status(self) -> Dict[str, Any]:
        """获取Cookie状态"""
        status = {}

        for platform in self._platforms:
            cookie_data = self._cookies.get(platform)

            if cookie_data and not self._is_cookie_expired(cookie_data):
                status[platform] = {
                    'valid': True,
                    'expire_at': cookie_data.get('expire_at'),
                    'cookie_count': len(cookie_data.get('cookies', [])),
                }
            else:
                status[platform] = {
                    'valid': False,
                    'expire_at': None,
                    'cookie_count': 0,
                }

        return status

    def get_platform_config(self, platform: str) -> Optional[Dict]:
        """获取平台配置"""
        return self._platforms.get(platform)

    def register_platform(self, platform: str, config: Dict):
        """
        注册新平台

        Args:
            platform: 平台名称
            config: 平台配置
        """
        self._platforms[platform] = config
        logger.info(f"注册新平台: {platform}")


cookie_manager = CookieManager()