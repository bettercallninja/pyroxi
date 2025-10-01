import asyncio
import aiohttp
import httpx
import random
import urllib.robotparser
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, urlparse
from .connection import Connection
from ..exceptions import ProxyConnectionError, PacketError


class ProxyManager:
    def __init__(self, proxies: List[Dict[str, Any]], max_concurrent: int = 10, 
                 rate_limit_delay: float = 0.1):
        """
        Initialize proxy manager with a list of proxy configurations
        
        Args:
            proxies: List of proxy dictionaries with keys: 
                    'address', 'port', 'type' ('http'/'socks5'), 'username', 'password'
            max_concurrent: Maximum number of concurrent connections (default: 10)
            rate_limit_delay: Delay between requests to be respectful (default: 0.1s)
        """
        self.proxies = proxies
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_connections = {}
        
        # Validate ethical usage
        if max_concurrent > 50:
            import warnings
            warnings.warn(
                "High concurrency detected. Ensure you have permission to make "
                "this many concurrent requests to avoid overwhelming target servers.",
                UserWarning
            )
        
    async def send_tcp_packet(self, target_host: str, target_port: int, 
                             data: bytes, proxy_index: Optional[int] = None) -> bytes:
        """Send TCP packet through proxy and return response"""
        proxy = self._get_proxy(proxy_index)
        
        async with self.semaphore:
            connection = Connection(
                proxy['address'], 
                proxy['port'], 
                proxy['type'],
                proxy.get('username'),
                proxy.get('password')
            )
            
            try:
                await connection.connect(target_host, target_port)
                await connection.send_data(data)
                response = await connection.receive_data()
                return response
            finally:
                await connection.disconnect()

    async def send_http_request(self, url: str, method: str = 'GET', 
                               headers: Optional[Dict] = None, 
                               data: Optional[Union[str, bytes, Dict]] = None,
                               proxy_index: Optional[int] = None) -> Dict:
        """Send HTTP request through proxy"""
        proxy = self._get_proxy(proxy_index)
        proxy_url = self._build_proxy_url(proxy)
        
        async with self.semaphore:
            connector = aiohttp.TCPConnector()
            
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.request(
                        method, 
                        url, 
                        headers=headers, 
                        data=data,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        content = await response.read()
                        return {
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'content': content,
                            'text': content.decode('utf-8', errors='ignore')
                        }
            except Exception as e:
                raise ProxyConnectionError(f"HTTP request failed: {str(e)}")

    async def send_http_request_with_ethics(self, url: str, method: str = 'GET',
                                      headers: Optional[Dict] = None,
                                      data: Optional[Union[str, bytes, Dict]] = None,
                                      proxy_index: Optional[int] = None,
                                      respect_robots: bool = True,
                                      user_agent: str = 'Pyroxy/1.0') -> Dict:
        """
        Send HTTP request with ethical considerations
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            data: Request data
            proxy_index: Specific proxy to use
            respect_robots: Whether to check robots.txt (default: True)
            user_agent: User agent for robots.txt check
        
        Returns:
            Dict: Response data
        """
        if respect_robots:
            if not await self.check_robots_txt(url, user_agent):
                raise ValueError(f"URL {url} is disallowed by robots.txt")
        
        # Add delay to be respectful
        if self.rate_limit_delay > 0:
            await asyncio.sleep(self.rate_limit_delay)
        
        return await self.send_http_request(url, method, headers, data, proxy_index)

    async def check_robots_txt(self, url: str, user_agent: str = '*') -> bool:
        """
        Check if the URL is allowed by robots.txt
        
        Args:
            url: The URL to check
            user_agent: User agent string (default: '*')
        
        Returns:
            bool: True if allowed, False if disallowed
        """
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(user_agent, url)
        except Exception:
            # If robots.txt cannot be fetched, assume allowed
            return True

    async def send_multiple_requests(self, requests: List[Dict], 
                                   distribute_proxies: bool = True) -> List[Dict]:
        """Send multiple requests concurrently through different proxies"""
        tasks = []
        
        for i, request in enumerate(requests):
            proxy_index = i % len(self.proxies) if distribute_proxies else None
            
            if request['type'] == 'http':
                task = self.send_http_request(
                    request['url'],
                    request.get('method', 'GET'),
                    request.get('headers'),
                    request.get('data'),
                    proxy_index
                )
            elif request['type'] == 'tcp':
                task = self.send_tcp_packet(
                    request['host'],
                    request['port'],
                    request['data'],
                    proxy_index
                )
            else:
                raise PacketError(f"Unsupported request type: {request['type']}")
            
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def test_proxy_speed(self, test_url: str = 'http://httpbin.org/ip', 
                              timeout: int = 10) -> List[Dict]:
        """Test speed and functionality of all proxies"""
        results = []
        
        for i, proxy in enumerate(self.proxies):
            start_time = asyncio.get_event_loop().time()
            
            try:
                response = await asyncio.wait_for(
                    self.send_http_request(test_url, proxy_index=i),
                    timeout=timeout
                )
                
                end_time = asyncio.get_event_loop().time()
                response_time = end_time - start_time
                
                results.append({
                    'proxy_index': i,
                    'proxy': proxy,
                    'status': 'success',
                    'response_time': response_time,
                    'response': response
                })
                
            except Exception as e:
                results.append({
                    'proxy_index': i,
                    'proxy': proxy,
                    'status': 'failed',
                    'error': str(e),
                    'response_time': None
                })
        
        return results

    def _get_proxy(self, index: Optional[int] = None) -> Dict:
        """Get proxy by index or random selection"""
        if index is not None:
            if 0 <= index < len(self.proxies):
                return self.proxies[index]
            else:
                raise ValueError(f"Proxy index {index} out of range")
        
        return random.choice(self.proxies)

    def _build_proxy_url(self, proxy: Dict) -> str:
        """Build proxy URL for aiohttp"""
        if proxy.get('username') and proxy.get('password'):
            return f"{proxy['type']}://{proxy['username']}:{proxy['password']}@{proxy['address']}:{proxy['port']}"
        else:
            return f"{proxy['type']}://{proxy['address']}:{proxy['port']}"

    async def close(self):
        """Close all active connections"""
        for connection in self.active_connections.values():
            await connection.disconnect()
        self.active_connections.clear()


class AsyncHTTPClient:
    """Simplified async HTTP client with proxy support"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
    
    async def get(self, url: str, **kwargs) -> Dict:
        """Perform GET request"""
        return await self.proxy_manager.send_http_request(url, 'GET', **kwargs)
    
    async def post(self, url: str, data: Optional[Union[str, bytes, Dict]] = None, **kwargs) -> Dict:
        """Perform POST request"""
        return await self.proxy_manager.send_http_request(url, 'POST', data=data, **kwargs)
    
    async def put(self, url: str, data: Optional[Union[str, bytes, Dict]] = None, **kwargs) -> Dict:
        """Perform PUT request"""
        return await self.proxy_manager.send_http_request(url, 'PUT', data=data, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> Dict:
        """Perform DELETE request"""
        return await self.proxy_manager.send_http_request(url, 'DELETE', **kwargs)


# Legacy Proxy class for backward compatibility
class Proxy:
    def __init__(self):
        self.proxy_address = None
        self.proxy_port = None

    def set_proxy(self, address, port):
        self.proxy_address = address
        self.proxy_port = port

    def get_proxy_info(self):
        return {
            'address': self.proxy_address,
            'port': self.proxy_port
        }

    def send_packet(self, packet):
        if not self.proxy_address or not self.proxy_port:
            raise ValueError("Proxy not set. Please set the proxy before sending packets.")
        
        # Here you would implement the logic to send the packet to the proxy.
        # This is a placeholder for the actual sending logic.
        print(f"Sending packet to {self.proxy_address}:{self.proxy_port}")