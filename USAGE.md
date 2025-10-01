# Pyroxy Usage Guide

## Quick Start

### 1. Basic HTTP Request Through Proxy

```python
import asyncio
from pyroxy import ProxyManager

async def simple_request():
    # Define your proxy
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http'  # or 'socks5'
        }
    ]
    
    # Create proxy manager
    manager = ProxyManager(proxies)
    
    # Send request
    response = await manager.send_http_request('http://httpbin.org/ip')
    print(f"Your IP: {response['text']}")
    
    await manager.close()

asyncio.run(simple_request())
```

### 2. Multiple Concurrent Requests

```python
import asyncio
from pyroxy import ProxyManager

async def concurrent_requests():
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}
    ]
    
    manager = ProxyManager(proxies, max_concurrent=10)
    
    requests = [
        {'type': 'http', 'url': 'http://httpbin.org/ip', 'method': 'GET'},
        {'type': 'http', 'url': 'http://httpbin.org/user-agent', 'method': 'GET'},
        # Add more requests...
    ]
    
    results = await manager.send_multiple_requests(requests)
    print(f"Completed {len(results)} requests")
    
    await manager.close()

asyncio.run(concurrent_requests())
```

### 3. Custom TCP Packets

```python
import asyncio
from pyroxy import ProxyManager, PacketBuilder

async def tcp_example():
    proxies = [{'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}]
    manager = ProxyManager(proxies)
    
    # Build custom packet
    builder = PacketBuilder()
    packet = builder.build_http_packet('GET', '/', {'Host': 'example.com'})
    
    # Send through proxy
    response = await manager.send_tcp_packet('example.com', 80, packet)
    print(f"Response: {response}")
    
    await manager.close()

asyncio.run(tcp_example())
```

## Proxy Configuration

### HTTP Proxy

```python
proxy = {
    'address': '127.0.0.1',
    'port': 8080,
    'type': 'http',
    'username': 'user',      # Optional
    'password': 'password'   # Optional
}
```

### SOCKS5 Proxy

```python
proxy = {
    'address': '127.0.0.1',
    'port': 1080,
    'type': 'socks5',
    'username': 'user',      # Optional
    'password': 'password'   # Optional
}
```

## Advanced Features

### HTTP Client Interface

```python
from pyroxy import ProxyManager, AsyncHTTPClient

async def http_client_example():
    proxies = [{'address': '127.0.0.1', 'port': 8080, 'type': 'http'}]
    manager = ProxyManager(proxies)
    client = AsyncHTTPClient(manager)
    
    # Simple requests
    response = await client.get('http://example.com')
    response = await client.post('http://example.com/api', data='{"key": "value"}')
    
    await manager.close()
```

### Performance Testing

```python
async def test_proxies():
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}
    ]
    
    manager = ProxyManager(proxies)
    results = await manager.test_proxy_speed()
    
    for result in results:
        if result['status'] == 'success':
            print(f"✓ Proxy working - {result['response_time']:.3f}s")
        else:
            print(f"✗ Proxy failed - {result['error']}")
    
    await manager.close()
```

### Custom Packet Building

```python
from pyroxy.packet.builder import AdvancedPacketBuilder

builder = AdvancedPacketBuilder()

# HTTP packet
http_packet = builder.build_http_packet(
    method='POST',
    path='/api/data',
    headers={'Content-Type': 'application/json'},
    body='{"message": "hello"}'
)

# WebSocket frame
ws_frame = builder.build_websocket_frame("Hello WebSocket!")

# SOCKS5 authentication
socks_auth = builder.build_socks5_auth_packet("username", "password")
```

### Packet Parsing

```python
from pyroxy.packet.parser import PacketParser

parser = PacketParser()

# Auto-detect and parse
parsed = parser.auto_parse(response_data)

# Specific parsing
http_response = parser.parse_http_response(data)
json_data = parser.parse_json_packet(data)
```

## Error Handling

```python
from pyroxy.exceptions import ProxyConnectionError, ProxyAuthenticationError

try:
    response = await manager.send_http_request('http://example.com')
except ProxyConnectionError as e:
    print(f"Connection failed: {e}")
except ProxyAuthenticationError as e:
    print(f"Authentication failed: {e}")
```

## Performance Tips

1. **Use multiple proxies** for better throughput
2. **Adjust max_concurrent** based on your needs
3. **Test proxy speeds** regularly with `test_proxy_speed()`
4. **Distribute requests** across proxies for load balancing
5. **Handle failures gracefully** with try/except blocks

## Examples Directory

- `basic_usage.py` - Simple examples
- `async_usage.py` - Advanced async features
- `performance_test.py` - High-performance testing
- `demo.py` - Complete feature showcase

## Common Use Cases

### Web Scraping
```python
# Rotate through multiple proxies for scraping
requests = [{'type': 'http', 'url': f'http://example.com/page/{i}', 'method': 'GET'} 
           for i in range(100)]
results = await manager.send_multiple_requests(requests, distribute_proxies=True)
```

### API Testing
```python
# Test API endpoints through different proxies
client = AsyncHTTPClient(manager)
response = await client.post('/api/test', 
                           data=json.dumps(test_data),
                           headers={'Content-Type': 'application/json'})
```

### Network Monitoring
```python
# Monitor proxy health
health_results = await manager.test_proxy_speed(timeout=5)
working_proxies = [r for r in health_results if r['status'] == 'success']
```
