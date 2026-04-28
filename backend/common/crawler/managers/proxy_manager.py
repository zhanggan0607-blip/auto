"""
代理管理器
提供代理池管理、失败代理标记、代理轮换等功能
"""
import random
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    代理管理器
    支持：
    - 代理池管理
    - 失败代理自动标记
    - 代理轮换策略
    - 代理健康检查
    """

    DEFAULT_PROXY_TYPES = ['http', 'https', 'socks5']

    def __init__(self, proxy_list: List[str] = None):
        """
        初始化代理管理器

        Args:
            proxy_list: 代理列表，格式如 ['http://ip:port', 'socks5://ip:port']
        """
        self._proxy_list: List[str] = proxy_list or []
        self._failed_proxies: set = set()
        self._proxy_stats: Dict[str, Dict[str, Any]] = {}
        self._current_index: int = 0

    def add(self, proxy: str) -> bool:
        """
        添加代理到池中

        Args:
            proxy: 代理地址，格式如 'http://ip:port'

        Returns:
            bool: 是否添加成功
        """
        if not self._validate_proxy(proxy):
            logger.warning(f"代理格式无效: {proxy}")
            return False

        if proxy not in self._proxy_list:
            self._proxy_list.append(proxy)
            self._proxy_stats[proxy] = {
                'success_count': 0,
                'fail_count': 0,
                'last_used': None,
                'total_latency': 0
            }
            logger.info(f"添加代理成功: {proxy}")
            return True
        return False

    def remove(self, proxy: str) -> bool:
        """
        从池中移除代理

        Args:
            proxy: 代理地址

        Returns:
            bool: 是否移除成功
        """
        if proxy in self._proxy_list:
            self._proxy_list.remove(proxy)
            self._failed_proxies.discard(proxy)
            if proxy in self._proxy_stats:
                del self._proxy_stats[proxy]
            return True
        return False

    def get_proxy(self, strategy: str = 'random') -> Optional[str]:
        """
        获取可用代理

        Args:
            strategy: 获取策略
                - 'random': 随机选择
                - 'round_robin': 轮询
                - 'least_used': 使用次数最少

        Returns:
            Optional[str]: 可用代理地址，如果无可用代理返回None
        """
        available = self._get_available_proxies()

        if not available:
            self._failed_proxies.clear()
            available = self._proxy_list.copy()

        if not available:
            return None

        if strategy == 'random':
            proxy = random.choice(available)
        elif strategy == 'round_robin':
            proxy = self._get_round_robin_proxy(available)
        elif strategy == 'least_used':
            proxy = self._get_least_used_proxy(available)
        else:
            proxy = random.choice(available)

        if proxy:
            self._record_proxy_usage(proxy)

        return proxy

    def _get_available_proxies(self) -> List[str]:
        """
        获取可用代理列表（排除失败的）

        Returns:
            List[str]: 可用代理列表
        """
        return [p for p in self._proxy_list if p not in self._failed_proxies]

    def _get_round_robin_proxy(self, available: List[str]) -> str:
        """
        轮询获取代理

        Args:
            available: 可用代理列表

        Returns:
            str: 代理地址
        """
        if not available:
            return None

        self._current_index = self._current_index % len(available)
        proxy = available[self._current_index]
        self._current_index += 1
        return proxy

    def _get_least_used_proxy(self, available: List[str]) -> str:
        """
        获取使用次数最少的代理

        Args:
            available: 可用代理列表

        Returns:
            str: 代理地址
        """
        if not available:
            return None

        min_usage = float('inf')
        selected = available[0]

        for proxy in available:
            stats = self._proxy_stats.get(proxy, {})
            total = stats.get('success_count', 0) + stats.get('fail_count', 0)
            if total < min_usage:
                min_usage = total
                selected = proxy

        return selected

    def mark_success(self, proxy: str, latency: float = None):
        """
        标记代理成功

        Args:
            proxy: 代理地址
            latency: 响应延迟（毫秒）
        """
        if proxy in self._proxy_list:
            self._failed_proxies.discard(proxy)
            if proxy not in self._proxy_stats:
                self._proxy_stats[proxy] = {
                    'success_count': 0,
                    'fail_count': 0,
                    'last_used': None,
                    'total_latency': 0
                }

            self._proxy_stats[proxy]['success_count'] += 1
            self._proxy_stats[proxy]['last_used'] = self._get_timestamp()

            if latency is not None:
                self._proxy_stats[proxy]['total_latency'] += latency

            logger.debug(f"代理成功: {proxy}")

    def mark_failed(self, proxy: str):
        """
        标记代理失败

        Args:
            proxy: 代理地址
        """
        if proxy in self._proxy_list:
            self._failed_proxies.add(proxy)

            if proxy in self._proxy_stats:
                self._proxy_stats[proxy]['fail_count'] += 1
                self._proxy_stats[proxy]['last_used'] = self._get_timestamp()

            logger.warning(f"代理失败，已标记: {proxy}")

    def reset_failed(self):
        """
        重置所有失败标记
        """
        self._failed_proxies.clear()
        logger.info("已重置所有失败代理标记")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取代理统计信息

        Returns:
            Dict: 统计信息
        """
        total = len(self._proxy_list)
        available = len(self._get_available_proxies())
        failed = len(self._failed_proxies)

        success_count = sum(s.get('success_count', 0) for s in self._proxy_stats.values())
        fail_count = sum(s.get('fail_count', 0) for s in self._proxy_stats.values())

        return {
            'total': total,
            'available': available,
            'failed': failed,
            'success_count': success_count,
            'fail_count': fail_count,
            'success_rate': success_count / (success_count + fail_count) if (success_count + fail_count) > 0 else 0
        }

    def get_proxy_dict(self, proxy: str) -> Optional[Dict[str, str]]:
        """
        获取代理字典格式（用于requests）

        Args:
            proxy: 代理地址

        Returns:
            Dict: {'http': 'http://proxy', 'https': 'http://proxy'}
        """
        if not proxy:
            return None

        if proxy.startswith('socks5://'):
            return {
                'http': proxy,
                'https': proxy
            }
        elif proxy.startswith('http://') or proxy.startswith('https://'):
            return {
                'http': proxy,
                'https': proxy
            }
        else:
            return {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }

    def _validate_proxy(self, proxy: str) -> bool:
        """
        验证代理格式

        Args:
            proxy: 代理地址

        Returns:
            bool: 是否有效
        """
        if not proxy:
            return False

        valid_prefixes = ['http://', 'https://', 'socks5://']
        return any(proxy.startswith(p) for p in valid_prefixes) or '://' in proxy

    def _record_proxy_usage(self, proxy: str):
        """
        记录代理使用

        Args:
            proxy: 代理地址
        """
        if proxy in self._proxy_stats:
            self._proxy_stats[proxy]['last_used'] = self._get_timestamp()

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def __len__(self) -> int:
        """获取代理池大小"""
        return len(self._proxy_list)

    def __repr__(self) -> str:
        return f"<ProxyManager total={len(self._proxy_list)} available={len(self._get_available_proxies())}>"


proxy_manager = ProxyManager()