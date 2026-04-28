"""
User-Agent 管理器
提供随机UA生成、UA池管理功能
"""
import random
from typing import List, Optional


class UserAgentManager:
    """
    User-Agent 管理器
    支持随机选择、指定浏览器类型、UA池更新
    """

    DEFAULT_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ]

    CHROME_USER_AGENTS = [
        ua for ua in DEFAULT_USER_AGENTS
        if 'Chrome' in ua and 'Edg' not in ua
    ]

    FIREFOX_USER_AGENTS = [
        ua for ua in DEFAULT_USER_AGENTS
        if 'Firefox' in ua
    ]

    SAFARI_USER_AGENTS = [
        ua for ua in DEFAULT_USER_AGENTS
        if 'Safari' in ua and 'Chrome' not in ua
    ]

    def __init__(self, user_agents: List[str] = None):
        """
        初始化 UA 管理器

        Args:
            user_agents: 自定义UA列表，如果为None则使用默认列表
        """
        self._user_agents = user_agents or self.DEFAULT_USER_AGENTS.copy()

    def get_random(self) -> str:
        """
        获取随机 User-Agent

        Returns:
            str: 随机选择的UA字符串
        """
        return random.choice(self._user_agents)

    def get_chrome(self) -> str:
        """
        获取随机 Chrome UA

        Returns:
            str: Chrome浏览器UA
        """
        chrome_agents = self.CHROME_USER_AGENTS or self._user_agents
        return random.choice(chrome_agents)

    def get_firefox(self) -> str:
        """
        获取随机 Firefox UA

        Returns:
            str: Firefox浏览器UA
        """
        firefox_agents = self.FIREFOX_USER_AGENTS or self._user_agents
        return random.choice(firefox_agents)

    def get_safari(self) -> str:
        """
        获取随机 Safari UA

        Returns:
            str: Safari浏览器UA
        """
        safari_agents = self.SAFARI_USER_AGENTS or self._user_agents
        return random.choice(safari_agents)

    def add(self, user_agent: str):
        """
        添加新的 UA 到池中

        Args:
            user_agent: UA字符串
        """
        if user_agent not in self._user_agents:
            self._user_agents.append(user_agent)

    def remove(self, user_agent: str):
        """
        从池中移除 UA

        Args:
            user_agent: UA字符串
        """
        if user_agent in self._user_agents:
            self._user_agents.remove(user_agent)

    def get_all(self) -> List[str]:
        """
        获取所有 UA

        Returns:
            List[str]: UA列表
        """
        return self._user_agents.copy()

    def __len__(self) -> int:
        """获取UA池大小"""
        return len(self._user_agents)


user_agent_manager = UserAgentManager()