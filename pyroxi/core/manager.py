"""
Enhanced Proxy Manager with Single and Multi-Proxy Support
Supports flexible proxy configuration and connection pooling
"""

import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from .connection import Connection
from ..exceptions import ProxyConnectionError, ProxyAuthenticationError

logger = logging.getLogger(__name__)


class ProxySelectionStrategy(Enum):
    """Proxy selection strategies"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_USED = "least_used"
    FASTEST = "fastest"
    SEQUENTIAL = "sequential"


@dataclass
class ProxyConfig:
    """Proxy configuration dataclass"""
    address: str
    port: int
    type: str = 'socks5'  # 'socks5' or 'http'
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    buffer_size: int = 8192
    
    # Statistics
    success_count: int = field(default=0, init=False)
    failure_count: int = field(default=0, init=False)
    total_time: float = field(default=0.0, init=False)
    last_used: Optional[float] = field(default=None, init=False)
    is_active: bool = field(default=True, init=False)
    
    def __post_init__(self):
        if self.type not in ['http', 'socks5']:
            raise ValueError("Proxy type must be 'http' or 'socks5'")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        return self.total_time / self.success_count if self.success_count > 0 else float('inf')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'address': self.address,
            'port': self.port,
            'type': self.type,
            'username': self.username,
            'password': self.password,
            'timeout': self.timeout,
            'buffer_size': self.buffer_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyConfig':
        """Create from dictionary"""
        return cls(
            address=data['address'],
            port=data['port'],
            type=data.get('type', 'socks5'),
            username=data.get('username'),
            password=data.get('password'),
            timeout=data.get('timeout', 30),
            buffer_size=data.get('buffer_size', 8192)
        )
    
    def __repr__(self) -> str:
        return f"ProxyConfig({self.type}://{self.address}:{self.port})"


class EnhancedProxyManager:
    """
    Enhanced Proxy Manager supporting single and multiple proxies
    with load balancing, failover, and connection pooling
    """
    
    def __init__(
        self,
        proxies: Optional[Union[Dict, List[Dict], ProxyConfig, List[ProxyConfig]]] = None,
        strategy: ProxySelectionStrategy = ProxySelectionStrategy.ROUND_ROBIN,
        max_concurrent: int = 10,
        enable_failover: bool = True,
        health_check_interval: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize Enhanced Proxy Manager
        
        Args:
            proxies: Single proxy (dict/ProxyConfig) or list of proxies
                    If None, operates in direct connection mode
            strategy: Proxy selection strategy
            max_concurrent: Maximum concurrent connections
            enable_failover: Enable automatic failover to next proxy
            health_check_interval: Health check interval in seconds (0 to disable)
            max_retries: Maximum retry attempts per request
        """
        self.proxies: List[ProxyConfig] = []
        self.strategy = strategy
        self.max_concurrent = max_concurrent
        self.enable_failover = enable_failover
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries
        
        # Initialize proxies
        if proxies is not None:
            self._initialize_proxies(proxies)
        
        # Connection management
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._current_index = 0
        self._lock = asyncio.Lock()
        
        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None
        if health_check_interval > 0 and self.proxies:
            self._start_health_check()
        
        logger.info(f"ProxyManager initialized with {len(self.proxies)} proxies")
    
    def _initialize_proxies(self, proxies: Union[Dict, List[Dict], ProxyConfig, List[ProxyConfig]]):
        """Initialize proxy configurations"""
        if isinstance(proxies, (dict, ProxyConfig)):
            # Single proxy
            proxies = [proxies]
        
        for proxy in proxies:
            if isinstance(proxy, ProxyConfig):
                self.proxies.append(proxy)
            elif isinstance(proxy, dict):
                self.proxies.append(ProxyConfig.from_dict(proxy))
            else:
                raise ValueError(f"Invalid proxy type: {type(proxy)}")
    
    def add_proxy(self, proxy: Union[Dict, ProxyConfig]):
        """Add a proxy to the pool"""
        if isinstance(proxy, dict):
            proxy = ProxyConfig.from_dict(proxy)
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy}")
    
    def remove_proxy(self, address: str, port: int):
        """Remove a proxy from the pool"""
        self.proxies = [p for p in self.proxies if not (p.address == address and p.port == port)]
        logger.info(f"Removed proxy: {address}:{port}")
    
    async def _select_proxy(self) -> Optional[ProxyConfig]:
        """Select a proxy based on the configured strategy"""
        if not self.proxies:
            return None
        
        active_proxies = [p for p in self.proxies if p.is_active]
        if not active_proxies:
            logger.warning("No active proxies available")
            return None
        
        async with self._lock:
            if self.strategy == ProxySelectionStrategy.ROUND_ROBIN:
                proxy = active_proxies[self._current_index % len(active_proxies)]
                self._current_index += 1
            
            elif self.strategy == ProxySelectionStrategy.RANDOM:
                proxy = random.choice(active_proxies)
            
            elif self.strategy == ProxySelectionStrategy.LEAST_USED:
                proxy = min(active_proxies, key=lambda p: p.success_count + p.failure_count)
            
            elif self.strategy == ProxySelectionStrategy.FASTEST:
                proxy = min(active_proxies, key=lambda p: p.avg_response_time)
            
            elif self.strategy == ProxySelectionStrategy.SEQUENTIAL:
                proxy = active_proxies[0]
            
            else:
                proxy = active_proxies[0]
            
            return proxy
    
    async def get_connection(
        self,
        target_host: str,
        target_port: int,
        proxy_config: Optional[ProxyConfig] = None
    ) -> Connection:
        """
        Get a connection to target through proxy
        
        Args:
            target_host: Target hostname/IP
            target_port: Target port
            proxy_config: Specific proxy to use (optional)
        
        Returns:
            Connected Connection object
        """
        if proxy_config is None:
            proxy_config = await self._select_proxy()
        
        if proxy_config is None:
            # Direct connection mode
            raise ProxyConnectionError("No proxy available and direct mode not supported")
        
        start_time = time.time()
        
        try:
            connection = Connection(
                proxy_address=proxy_config.address,
                proxy_port=proxy_config.port,
                proxy_type=proxy_config.type,
                username=proxy_config.username,
                password=proxy_config.password,
                timeout=proxy_config.timeout,
                buffer_size=proxy_config.buffer_size
            )
            
            await connection.connect(target_host, target_port)
            
            # Update statistics
            elapsed = time.time() - start_time
            proxy_config.success_count += 1
            proxy_config.total_time += elapsed
            proxy_config.last_used = time.time()
            
            logger.debug(f"Connected via {proxy_config} in {elapsed:.2f}s")
            
            return connection
        
        except Exception as e:
            proxy_config.failure_count += 1
            logger.error(f"Connection failed via {proxy_config}: {e}")
            
            if self.enable_failover and self.proxies:
                logger.info("Attempting failover to another proxy...")
                proxy_config.is_active = False
                return await self.get_connection(target_host, target_port)
            
            raise
    
    async def execute_with_proxy(
        self,
        target_host: str,
        target_port: int,
        operation: callable,
        **kwargs
    ) -> Any:
        """
        Execute an operation through a proxy with retry logic
        
        Args:
            target_host: Target hostname
            target_port: Target port
            operation: Async callable that takes Connection as first arg
            **kwargs: Additional arguments for operation
        
        Returns:
            Result from operation
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:
                    conn = await self.get_connection(target_host, target_port)
                    try:
                        result = await operation(conn, **kwargs)
                        return result
                    finally:
                        await conn.disconnect()
            
            except (ProxyConnectionError, ProxyAuthenticationError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        
        raise ProxyConnectionError(f"All {self.max_retries} attempts failed: {last_error}")
    
    async def send_tcp_data(
        self,
        target_host: str,
        target_port: int,
        data: bytes,
        receive: bool = True
    ) -> Optional[bytes]:
        """
        Send TCP data through proxy
        
        Args:
            target_host: Target hostname
            target_port: Target port
            data: Data to send
            receive: Whether to receive response
        
        Returns:
            Response data if receive=True, None otherwise
        """
        async def operation(conn: Connection) -> Optional[bytes]:
            await conn.send_data(data)
            if receive:
                return await conn.receive_data()
            return None
        
        return await self.execute_with_proxy(target_host, target_port, operation)
    
    async def send_http_request(
        self,
        target_host: str,
        method: str = 'GET',
        path: str = '/',
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        port: int = 80
    ) -> bytes:
        """
        Send HTTP request through proxy
        
        Args:
            target_host: Target hostname
            method: HTTP method
            path: Request path
            headers: HTTP headers
            body: Request body
            port: Target port (default: 80)
        
        Returns:
            Response data
        """
        async def operation(conn: Connection) -> bytes:
            return await conn.send_http_request(method, path, headers, body)
        
        return await self.execute_with_proxy(target_host, port, operation)
    
    async def batch_execute(
        self,
        operations: List[Tuple[str, int, callable, Dict]],
        max_workers: Optional[int] = None
    ) -> List[Any]:
        """
        Execute multiple operations concurrently
        
        Args:
            operations: List of (host, port, callable, kwargs) tuples
            max_workers: Max concurrent workers (defaults to max_concurrent)
        
        Returns:
            List of results
        """
        if max_workers is None:
            max_workers = self.max_concurrent
        
        tasks = []
        for host, port, operation, kwargs in operations:
            task = self.execute_with_proxy(host, port, operation, **kwargs)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _health_check(self):
        """Periodic health check for proxies"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                logger.debug("Running health check...")
                
                for proxy in self.proxies:
                    try:
                        conn = Connection(
                            proxy.address,
                            proxy.port,
                            proxy.type,
                            proxy.username,
                            proxy.password,
                            timeout=5
                        )
                        
                        # Try connecting to a reliable host
                        await conn.connect("www.google.com", 80)
                        await conn.disconnect()
                        
                        if not proxy.is_active:
                            proxy.is_active = True
                            logger.info(f"Proxy {proxy} is back online")
                    
                    except Exception as e:
                        if proxy.is_active:
                            proxy.is_active = False
                            logger.warning(f"Proxy {proxy} failed health check: {e}")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def _start_health_check(self):
        """Start health check background task"""
        self._health_check_task = asyncio.create_task(self._health_check())
    
    async def stop_health_check(self):
        """Stop health check background task"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
    
    def get_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all proxies"""
        return [
            {
                'proxy': str(proxy),
                'active': proxy.is_active,
                'success_count': proxy.success_count,
                'failure_count': proxy.failure_count,
                'success_rate': f"{proxy.success_rate * 100:.1f}%",
                'avg_response_time': f"{proxy.avg_response_time:.2f}s",
                'last_used': proxy.last_used
            }
            for proxy in self.proxies
        ]
    
    def print_statistics(self):
        """Print proxy statistics"""
        stats = self.get_statistics()
        print("\n" + "=" * 80)
        print("PROXY STATISTICS")
        print("=" * 80)
        for stat in stats:
            print(f"\n📡 {stat['proxy']}")
            print(f"   Status: {'✅ Active' if stat['active'] else '❌ Inactive'}")
            print(f"   Success: {stat['success_count']} | Failures: {stat['failure_count']}")
            print(f"   Success Rate: {stat['success_rate']}")
            print(f"   Avg Response Time: {stat['avg_response_time']}")
        print("=" * 80 + "\n")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_health_check()
    
    def __repr__(self) -> str:
        active = sum(1 for p in self.proxies if p.is_active)
        return f"<ProxyManager: {active}/{len(self.proxies)} active proxies, strategy={self.strategy.value}>"
    
    # ========================================================================
    # 🚀 EXCLUSIVE FEATURES - Advanced Functionality
    # ========================================================================
    
    async def get_fastest_proxy(self, test_host: str = "www.google.com", test_port: int = 80) -> Optional[ProxyConfig]:
        """
        Test all proxies and return the fastest one
        
        Args:
            test_host: Host to test connection speed
            test_port: Port to test
        
        Returns:
            Fastest proxy or None
        """
        results = []
        
        for proxy in self.proxies:
            if not proxy.is_active:
                continue
            
            start = time.time()
            try:
                conn = Connection(
                    proxy.address, proxy.port, proxy.type,
                    proxy.username, proxy.password, timeout=10
                )
                await conn.connect(test_host, test_port)
                await conn.disconnect()
                
                elapsed = time.time() - start
                results.append((proxy, elapsed))
                logger.info(f"Proxy {proxy} speed test: {elapsed:.2f}s")
            
            except Exception as e:
                logger.warning(f"Proxy {proxy} failed speed test: {e}")
        
        if results:
            fastest = min(results, key=lambda x: x[1])
            logger.info(f"Fastest proxy: {fastest[0]} ({fastest[1]:.2f}s)")
            return fastest[0]
        
        return None
    
    async def proxy_chain(
        self,
        target_host: str,
        target_port: int,
        chain_proxies: Optional[List[ProxyConfig]] = None
    ) -> Connection:
        """
        Create a chain of proxies (proxy through proxy)
        
        Args:
            target_host: Final target host
            target_port: Final target port
            chain_proxies: List of proxies to chain (uses all if None)
        
        Returns:
            Connection through the proxy chain
        """
        if chain_proxies is None:
            chain_proxies = [p for p in self.proxies if p.is_active][:3]  # Max 3 proxies
        
        if not chain_proxies:
            raise ProxyConnectionError("No proxies available for chaining")
        
        # Start with first proxy
        current_proxy = chain_proxies[0]
        
        if len(chain_proxies) == 1:
            # Single proxy, no chaining needed
            return await self.get_connection(target_host, target_port, current_proxy)
        
        # Chain through proxies
        conn = Connection(
            current_proxy.address,
            current_proxy.port,
            current_proxy.type,
            current_proxy.username,
            current_proxy.password
        )
        
        # Connect through chain
        for i, next_proxy in enumerate(chain_proxies[1:], 1):
            if i == len(chain_proxies) - 1:
                # Last proxy, connect to target
                await conn.connect(target_host, target_port)
            else:
                # Intermediate proxy
                await conn.connect(next_proxy.address, next_proxy.port)
        
        logger.info(f"Established proxy chain: {' -> '.join(str(p) for p in chain_proxies)} -> {target_host}:{target_port}")
        return conn
    
    async def rotating_request(
        self,
        target_host: str,
        target_port: int,
        data: bytes,
        rotation_count: int = 5
    ) -> List[bytes]:
        """
        Send multiple requests rotating through all proxies
        
        Args:
            target_host: Target host
            target_port: Target port
            data: Data to send
            rotation_count: Number of requests to make
        
        Returns:
            List of responses
        """
        results = []
        
        for i in range(rotation_count):
            proxy = await self._select_proxy()
            if not proxy:
                logger.warning(f"No proxy available for request {i + 1}")
                continue
            
            try:
                conn = await self.get_connection(target_host, target_port, proxy)
                await conn.send_data(data)
                response = await conn.receive_data()
                await conn.disconnect()
                
                results.append(response)
                logger.info(f"Rotation {i + 1}/{rotation_count} via {proxy} - Success")
            
            except Exception as e:
                logger.error(f"Rotation {i + 1}/{rotation_count} via {proxy} - Failed: {e}")
        
        return results
    
    async def smart_failover(
        self,
        target_host: str,
        target_port: int,
        data: bytes,
        min_success_rate: float = 0.7
    ) -> bytes:
        """
        Smart failover that avoids proxies with low success rates
        
        Args:
            target_host: Target host
            target_port: Target port
            data: Data to send
            min_success_rate: Minimum success rate threshold (0.0-1.0)
        
        Returns:
            Response data
        """
        # Get healthy proxies
        healthy_proxies = [
            p for p in self.proxies
            if p.is_active and (p.success_rate >= min_success_rate or p.success_count + p.failure_count < 5)
        ]
        
        if not healthy_proxies:
            logger.warning(f"No proxies meet success rate threshold of {min_success_rate*100}%")
            healthy_proxies = [p for p in self.proxies if p.is_active]
        
        if not healthy_proxies:
            raise ProxyConnectionError("No healthy proxies available")
        
        # Try proxies in order of success rate
        sorted_proxies = sorted(healthy_proxies, key=lambda p: p.success_rate, reverse=True)
        
        for proxy in sorted_proxies:
            try:
                conn = await self.get_connection(target_host, target_port, proxy)
                await conn.send_data(data)
                response = await conn.receive_data()
                await conn.disconnect()
                
                logger.info(f"Smart failover successful via {proxy} (success rate: {proxy.success_rate*100:.1f}%)")
                return response
            
            except Exception as e:
                logger.warning(f"Smart failover attempt via {proxy} failed: {e}")
        
        raise ProxyConnectionError("All smart failover attempts exhausted")
    
    async def load_balance_by_latency(
        self,
        target_host: str,
        target_port: int,
        requests: List[bytes],
        latency_threshold: float = 2.0
    ) -> List[bytes]:
        """
        Distribute requests based on proxy latency
        
        Args:
            target_host: Target host
            target_port: Target port
            requests: List of request data
            latency_threshold: Max acceptable latency in seconds
        
        Returns:
            List of responses
        """
        # Filter by latency
        fast_proxies = [
            p for p in self.proxies
            if p.is_active and p.avg_response_time <= latency_threshold
        ]
        
        if not fast_proxies:
            logger.warning(f"No proxies under {latency_threshold}s latency, using all")
            fast_proxies = [p for p in self.proxies if p.is_active]
        
        results = []
        tasks = []
        
        for i, request_data in enumerate(requests):
            # Select proxy based on latency
            proxy = min(fast_proxies, key=lambda p: p.avg_response_time)
            
            async def make_request(req_data, prx):
                try:
                    conn = await self.get_connection(target_host, target_port, prx)
                    await conn.send_data(req_data)
                    resp = await conn.receive_data()
                    await conn.disconnect()
                    return resp
                except Exception as e:
                    logger.error(f"Request failed: {e}")
                    return None
            
            tasks.append(make_request(request_data, proxy))
        
        results = await asyncio.gather(*tasks)
        logger.info(f"Load balanced {len(requests)} requests across {len(fast_proxies)} fast proxies")
        
        return [r for r in results if r is not None]
    
    def export_config(self, filepath: str):
        """
        Export proxy configuration to JSON file
        
        Args:
            filepath: Path to save configuration
        """
        import json
        
        config = {
            'strategy': self.strategy.value,
            'max_concurrent': self.max_concurrent,
            'enable_failover': self.enable_failover,
            'health_check_interval': self.health_check_interval,
            'max_retries': self.max_retries,
            'proxies': [p.to_dict() for p in self.proxies]
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration exported to {filepath}")
    
    @classmethod
    def import_config(cls, filepath: str) -> 'EnhancedProxyManager':
        """
        Import proxy configuration from JSON file
        
        Args:
            filepath: Path to configuration file
        
        Returns:
            Configured EnhancedProxyManager instance
        """
        import json
        
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        strategy = ProxySelectionStrategy(config['strategy'])
        proxies = [ProxyConfig.from_dict(p) for p in config['proxies']]
        
        manager = cls(
            proxies=proxies,
            strategy=strategy,
            max_concurrent=config.get('max_concurrent', 10),
            enable_failover=config.get('enable_failover', True),
            health_check_interval=config.get('health_check_interval', 60),
            max_retries=config.get('max_retries', 3)
        )
        
        logger.info(f"Configuration imported from {filepath}")
        return manager
    
    async def benchmark_proxies(
        self,
        test_host: str = "www.google.com",
        test_port: int = 80,
        iterations: int = 3
    ) -> Dict[str, Dict[str, float]]:
        """
        Benchmark all proxies with multiple iterations
        
        Args:
            test_host: Host to test against
            test_port: Port to test
            iterations: Number of test iterations per proxy
        
        Returns:
            Dictionary with benchmark results
        """
        results = {}
        
        for proxy in self.proxies:
            if not proxy.is_active:
                continue
            
            times = []
            successes = 0
            
            for i in range(iterations):
                start = time.time()
                try:
                    conn = Connection(
                        proxy.address, proxy.port, proxy.type,
                        proxy.username, proxy.password, timeout=10
                    )
                    await conn.connect(test_host, test_port)
                    await conn.disconnect()
                    
                    elapsed = time.time() - start
                    times.append(elapsed)
                    successes += 1
                
                except Exception as e:
                    logger.debug(f"Benchmark iteration {i+1} failed for {proxy}: {e}")
            
            if times:
                results[str(proxy)] = {
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'success_rate': successes / iterations,
                    'total_tests': iterations
                }
        
        logger.info(f"Benchmarked {len(results)} proxies with {iterations} iterations each")
        return results
    
    def get_proxy_by_location(self, country_code: str) -> List[ProxyConfig]:
        """
        Get proxies by country code (if address contains country info)
        Note: Requires proxies with country codes in their configuration
        
        Args:
            country_code: Two-letter country code (e.g., 'US', 'UK')
        
        Returns:
            List of proxies matching the country
        """
        # This is a simple implementation - can be enhanced with GeoIP
        matching = []
        
        for proxy in self.proxies:
            # Check if proxy has country metadata or in address
            if hasattr(proxy, 'country') and proxy.country == country_code.upper():
                matching.append(proxy)
        
        return matching
