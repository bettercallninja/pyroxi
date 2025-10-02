"""
PyRoxi - High-performance async proxy library for Python

Supports SOCKS5 and HTTP proxies with pure socket-based connections.
Features single and multi-proxy support with load balancing and failover.
Designed for speed, reliability, and production use.
"""

from .core.connection import Connection
from .core.manager import (
    EnhancedProxyManager,
    ProxyConfig,
    ProxySelectionStrategy
)
from .packet.builder import PacketBuilder, AdvancedPacketBuilder
from .packet.parser import PacketParser
from .exceptions import ProxyConnectionError, ProxyAuthenticationError, PacketError

__version__ = "1.0.0"
__author__ = "PyRoxi Team"
__description__ = "High-performance async proxy library with socket-based connections"

__all__ = [
    # Core connection
    'Connection',
    
    # Enhanced proxy manager
    'EnhancedProxyManager',
    'ProxyConfig',
    'ProxySelectionStrategy',
    
    # Packet handling
    'PacketBuilder',
    'AdvancedPacketBuilder',
    'PacketParser',
    
    # Exceptions
    'ProxyConnectionError',
    'ProxyAuthenticationError', 
    'PacketError'
]