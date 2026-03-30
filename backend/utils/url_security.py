"""
URL安全验证模块
防止SSRF攻击，验证URL是否为安全的外部地址
"""
import socket
import ipaddress
from typing import Tuple, List


BLOCKED_IP_RANGES = [
    '127.0.0.0/8',
    '10.0.0.0/8',
    '172.16.0.0/12',
    '192.168.0.0/16',
    '169.254.0.0/16',
    '0.0.0.0/8',
    '224.0.0.0/4',
    '240.0.0.0/4',
    '::1/128',
    'fc00::/7',
    'fe80::/10',
]

BLOCKED_HOSTNAMES = [
    'localhost',
    'localhost.localdomain',
    '127.0.0.1',
    '0.0.0.0',
    '::1',
]


def is_internal_ip(ip_str: str) -> bool:
    """
    检查IP是否为内网IP

    Args:
        ip_str: IP地址字符串

    Returns:
        bool: 是否为内网IP
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in ipaddress.ip_network(blocked_range):
                return True
        return False
    except ValueError:
        return False


def resolve_hostname_to_ips(hostname: str) -> List[str]:
    """
    解析主机名为IP地址列表

    Args:
        hostname: 主机名

    Returns:
        List[str]: IP地址列表
    """
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return list(set([r[4][0] for r in results]))
    except socket.gaierror:
        return []


def is_url_safe(url: str, allowed_domains: List[str] = None) -> Tuple[bool, str]:
    """
    验证URL是否安全（不是SSRF攻击）

    Args:
        url: 待验证的URL
        allowed_domains: 允许的域名白名单（可选）

    Returns:
        tuple: (is_safe: bool, reason: str)
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        if not parsed.scheme:
            return False, "URL缺少协议"

        if parsed.scheme not in ['http', 'https']:
            return False, f"不支持的协议: {parsed.scheme}"

        if not parsed.netloc:
            return False, "URL缺少域名"

        hostname = parsed.hostname
        if not hostname:
            return False, "无法解析域名"

        hostname_lower = hostname.lower()
        if hostname_lower in BLOCKED_HOSTNAMES:
            return False, f"禁止访问: {hostname}"

        if hostname_lower.endswith('.localhost'):
            return False, f"禁止访问: {hostname}"

        if allowed_domains:
            if not any(
                hostname_lower == domain.lower() or
                hostname_lower.endswith('.' + domain.lower())
                for domain in allowed_domains
            ):
                return False, f"域名不在白名单中: {hostname}"

        if parsed.hostname:
            if is_internal_ip(parsed.hostname):
                return False, f"禁止访问内网IP: {hostname}"

        resolved_ips = resolve_hostname_to_ips(hostname)
        for ip in resolved_ips:
            if is_internal_ip(ip):
                return False, f"域名解析到内网IP: {ip}"

        return True, ""

    except Exception as e:
        return False, f"URL验证失败: {str(e)}"


def validate_url_list(urls: List[str], allowed_domains: List[str] = None) -> Tuple[List[str], List[str]]:
    """
    批量验证URL列表

    Args:
        urls: URL列表
        allowed_domains: 允许的域名白名单（可选）

    Returns:
        tuple: (safe_urls: list, unsafe_urls_with_reason: list)
    """
    safe_urls = []
    unsafe_urls = []

    for url in urls:
        is_safe, reason = is_url_safe(url, allowed_domains)
        if is_safe:
            safe_urls.append(url)
        else:
            unsafe_urls.append(f"{url}: {reason}")

    return safe_urls, unsafe_urls