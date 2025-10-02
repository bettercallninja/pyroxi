# PyRoxi Quick Reference Guide

## 🚀 Quick Start

### Installation
```bash
uv add pyroxi
# or
pip install pyroxi
```

### Basic Import
```python
from pyroxi.core.connection import Connection
from pyroxi.exceptions import ProxyConnectionError, ProxyAuthenticationError
```

## 📖 Common Patterns

### 1. Simple SOCKS5 Connection
```python
import asyncio
from pyroxi.core.connection import Connection

async def main():
    conn = Connection("127.0.0.1", 1080, 'socks5')
    await conn.connect("example.com", 80)
    await conn.send_data(b"Hello")
    response = await conn.receive_data()
    await conn.disconnect()

asyncio.run(main())
```

### 2. Context Manager (Recommended)
```python
async def main():
    async with Connection("127.0.0.1", 1080, 'socks5') as conn:
        await conn.connect("example.com", 80)
        await conn.send_data(b"Hello")
        response = await conn.receive_data()
    # Auto-disconnects
```

### 3. With Authentication
```python
conn = Connection(
    "proxy.server", 1080, 'socks5',
    username="myuser",
    password="mypass"
)
```

### 4. HTTP Proxy
```python
async with Connection("proxy.server", 8080, 'http') as conn:
    await conn.connect("api.example.com", 443)
    # Now you have a tunnel to api.example.com:443
```

## 🎯 Connection Types

### SOCKS5
```python
Connection(host, port, 'socks5')
```
- ✅ Supports IPv4, IPv6, domain names
- ✅ Username/password authentication
- ✅ Binary protocol (RFC 1928)

### HTTP
```python
Connection(host, port, 'http')
```
- ✅ CONNECT method tunneling
- ✅ Basic authentication
- ✅ HTTP/1.1 compliant

## 📊 Data Transfer Methods

### Send Data
```python
# Send raw bytes
bytes_sent = await conn.send_data(b"raw data")

# Send packet with length prefix
bytes_sent = await conn.send_packet(b"packet data")
```

### Receive Data
```python
# Receive with buffer
data = await conn.receive_data(buffer_size=4096)

# Receive packet with length prefix
packet = await conn.receive_packet()

# Receive until connection closes
all_data = await conn.receive_all(timeout=10)
```

### HTTP Request
```python
response = await conn.send_http_request(
    method="GET",
    path="/api/endpoint",
    headers={"Authorization": "Bearer token"},
    body=b'{"key": "value"}'
)
```

## ⚙️ Configuration

### Basic Configuration
```python
Connection(
    proxy_address="127.0.0.1",
    proxy_port=1080,
    proxy_type='socks5',        # 'socks5' or 'http'
    username=None,               # Optional
    password=None,               # Optional
    timeout=30,                  # Socket timeout (seconds)
    buffer_size=8192            # Receive buffer (bytes)
)
```

### Runtime Adjustments
```python
conn.set_timeout(60)            # Change timeout
conn.set_buffer_size(16384)     # Change buffer size
```

### Connection Info
```python
info = conn.get_connection_info()
# Returns:
# {
#     'proxy_address': '127.0.0.1',
#     'proxy_port': 1080,
#     'proxy_type': 'socks5',
#     'target_host': 'example.com',
#     'target_port': 80,
#     'connected': True,
#     'authenticated': True,
#     'timeout': 30,
#     'buffer_size': 8192
# }
```

## 🔒 Error Handling

```python
from pyroxi.exceptions import ProxyConnectionError, ProxyAuthenticationError

try:
    async with Connection("proxy", 1080, 'socks5') as conn:
        await conn.connect("example.com", 80)
        # ... operations ...
        
except ProxyAuthenticationError as e:
    print(f"Auth failed: {e}")
    
except ProxyConnectionError as e:
    print(f"Connection error: {e}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 🎓 Complete Examples

### Example 1: HTTP GET through SOCKS5
```python
import asyncio
from pyroxi.core.connection import Connection

async def fetch_url():
    async with Connection("127.0.0.1", 1080, 'socks5') as conn:
        # Connect to web server
        await conn.connect("httpbin.org", 80)
        
        # Build HTTP request
        request = (
            "GET /get HTTP/1.1\r\n"
            "Host: httpbin.org\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        
        # Send request
        await conn.send_data(request.encode())
        
        # Receive response
        response = await conn.receive_all(timeout=10)
        print(response.decode())

asyncio.run(fetch_url())
```

### Example 2: Binary Protocol
```python
async def binary_communication():
    async with Connection("proxy", 1080, 'socks5') as conn:
        await conn.connect("game-server.com", 9999)
        
        # Send binary command
        command = b"\x01\x02\x03\x04"
        await conn.send_data(command)
        
        # Receive binary response
        response = await conn.receive_data()
        print(f"Received: {response.hex()}")
```

### Example 3: Authenticated HTTP Proxy
```python
async def authenticated_proxy():
    conn = Connection(
        "corporate-proxy.com",
        8080,
        'http',
        username="employee123",
        password="SecurePass123"
    )
    
    try:
        # Establish tunnel
        await conn.connect("api.example.com", 443)
        print("Tunnel established!")
        
        # Now you can send SSL/TLS traffic
        # (You'd typically wrap with SSL here)
        
    except ProxyAuthenticationError:
        print("Check your credentials!")
    finally:
        await conn.disconnect()
```

### Example 4: Packet Framing
```python
async def packet_protocol():
    async with Connection("proxy", 1080, 'socks5') as conn:
        await conn.connect("packet-server.com", 5555)
        
        # Send multiple packets with automatic framing
        for i in range(5):
            packet = f"Message {i}".encode()
            await conn.send_packet(packet)
        
        # Receive packets
        for i in range(5):
            packet = await conn.receive_packet()
            print(f"Received: {packet.decode()}")
```

## 🔍 Debugging

### Enable Logging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or just for pyroxi
logger = logging.getLogger('pyroxi')
logger.setLevel(logging.DEBUG)
```

### Check Connection Status
```python
if conn.is_connected():
    print("Connected!")
else:
    print("Not connected")

# Get detailed info
info = conn.get_connection_info()
print(f"Status: {info}")
```

### Inspect Raw Data
```python
# View hex dump of sent data
data = b"\x01\x02\x03"
print(f"Sending: {data.hex()}")
await conn.send_data(data)

# View received data
received = await conn.receive_data()
print(f"Received: {received.hex()}")
```

## ⚡ Performance Tips

### 1. Use Larger Buffers for Bulk Data
```python
conn = Connection(..., buffer_size=65536)  # 64KB
```

### 2. Reuse Connections
```python
# Don't create new connections for each request
async with Connection(...) as conn:
    await conn.connect(...)
    for i in range(100):
        await conn.send_data(...)
        await conn.receive_data()
```

### 3. Use Packet Framing for Message Boundaries
```python
# Instead of parsing application protocol yourself
await conn.send_packet(message)
response = await conn.receive_packet()
```

### 4. Set Appropriate Timeouts
```python
# Long-running operations
conn.set_timeout(300)  # 5 minutes

# Quick operations
conn.set_timeout(5)    # 5 seconds
```

## 🚨 Common Pitfalls

### ❌ Forgetting to Disconnect
```python
# Bad
conn = Connection(...)
await conn.connect(...)
# ... forget to disconnect

# Good
async with Connection(...) as conn:
    await conn.connect(...)
    # Auto-disconnects
```

### ❌ Wrong Proxy Type
```python
# Make sure proxy type matches your proxy server
Connection("proxy", 1080, 'http')   # Wrong if it's SOCKS5
Connection("proxy", 1080, 'socks5') # Correct
```

### ❌ Not Handling Exceptions
```python
# Always wrap in try/except
try:
    await conn.connect(...)
except ProxyConnectionError as e:
    print(f"Error: {e}")
```

### ❌ Encoding Issues
```python
# Bad
await conn.send_data("text")  # Wrong! Needs bytes

# Good
await conn.send_data(b"text")           # Bytes literal
await conn.send_data("text".encode())   # Encode string
```

## 📚 API Summary

### Connection Class Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `connect(host, port)` | Establish proxy connection | `bool` |
| `send_data(data)` | Send raw bytes | `int` |
| `send_packet(packet)` | Send with length prefix | `int` |
| `receive_data(size)` | Receive bytes | `bytes` |
| `receive_packet()` | Receive with length prefix | `bytes` |
| `receive_all(timeout)` | Receive until close | `bytes` |
| `send_http_request(...)` | Send HTTP request | `bytes` |
| `disconnect()` | Close connection | `None` |
| `is_connected()` | Check connection status | `bool` |
| `get_connection_info()` | Get connection details | `dict` |
| `set_timeout(seconds)` | Set socket timeout | `None` |
| `set_buffer_size(bytes)` | Set buffer size | `None` |

### Exceptions

- `ProxyConnectionError` - Connection/network issues
- `ProxyAuthenticationError` - Authentication failures

## 🔗 Resources

- [Full Documentation](./README.md)
- [Implementation Details](./IMPLEMENTATION.md)
- [Examples](./examples/)
- [GitHub Repository](https://github.com/bettercallninja/pyroxi)

## 💡 Tips

1. **Always use async/await** - All connection methods are async
2. **Use context managers** - Ensures proper cleanup
3. **Handle exceptions** - Network operations can fail
4. **Enable logging** - For debugging and monitoring
5. **Test with real proxies** - Before production use
6. **Read RFCs** - For deep protocol understanding
7. **Monitor performance** - Tune buffer sizes and timeouts

---

**Need help?** Check the examples folder or open an issue on GitHub!
