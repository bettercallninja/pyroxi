"""
Pyroxy - High-performance async proxy library for Python

Supports SOCKS5 and HTTP proxies with TCP and HTTP packet transmission.
Designed for speed and concurrent connections.
"""

from .core.connection import Connection
from .core.proxy import ProxyManager, AsyncHTTPClient, Proxy
from .packet.builder import PacketBuilder, AdvancedPacketBuilder
from .packet.parser import PacketParser
from .exceptions import ProxyConnectionError, ProxyAuthenticationError, PacketError

__version__ = "1.0.0"
__author__ = "Pyroxy Team"
__description__ = "High-performance async proxy library"

__all__ = [
    'Connection',
    'ProxyManager', 
    'AsyncHTTPClient',
    'Proxy',  # Legacy support
    'PacketBuilder',
    'AdvancedPacketBuilder',
    'PacketParser',
    'ProxyConnectionError',
    'ProxyAuthenticationError', 
    'PacketError'
]