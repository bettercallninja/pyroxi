# 🚀 PyRoxi - Quick Start Guide

**Version**: 1.0.0  
**Release Date**: October 2, 2025  
**Installation**: `pip install pyroxi` or `uv add pyroxi`

---

## ⚡ 30-Second Quick Start

### Install
```bash
pip install pyroxi
```

### Use (Simple)
```python
import asyncio
from pyroxi import Connection

async def main():
    async with Connection("127.0.0.1", 1080, 'socks5') as conn:
        await conn.connect("example.com", 80)
        await conn.send_data(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
        response = await conn.receive_data()
        print(f"✅ Received {len(response)} bytes")

asyncio.run(main())
```

**That's it!** You're using PyRoxi! 🎉

---

## 📚 3-Minute Guide

### 1. Single Proxy (Beginner)
```python
from pyroxi import Connection

# SOCKS5 proxy
async with Connection("proxy.example.com", 1080, 'socks5') as conn:
    await conn.connect("target.com", 80)
    # Now send/receive data

# HTTP proxy
async with Connection("proxy.example.com", 8080, 'http') as conn:
    await conn.connect("target.com", 443)
    # Now send/receive data
```

### 2. Multi-Proxy Pool (Intermediate)
```python
from pyroxi import EnhancedProxyManager

proxies = [
    {'host': '1.2.3.4', 'port': 1080, 'type': 'socks5'},
    {'host': '5.6.7.8', 'port': 8080, 'type': 'http'},
]

async with EnhancedProxyManager(proxies=proxies) as manager:
    request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    response = await manager.send_tcp_data('example.com', 80, request)
    print(f"✅ Got response: {len(response)} bytes")
```

### 3. Advanced Features (Power User)
```python
from pyroxi import EnhancedProxyManager, ProxySelectionStrategy

async with EnhancedProxyManager(
    proxies=proxies,
    strategy=ProxySelectionStrategy.FASTEST,  # Use fastest proxy
    max_retries=3,                             # Retry on failure
    max_concurrent=10                          # Allow 10 parallel connections
) as manager:
    # Get fastest proxy automatically
    fastest = await manager.get_fastest_proxy()
    
    # Rotate through all proxies
    responses = await manager.rotating_request(
        'api.example.com', 443,
        request_data,
        rotation_count=5
    )
    
    # Smart failover (avoids bad proxies)
    response = await manager.smart_failover(
        'example.com', 80,
        request_data,
        threshold=0.8
    )
    
    # View statistics
    manager.print_statistics()
```

---

## 🎯 Common Use Cases

### Web Scraping
```python
proxies = [{'host': 'proxy1.com', 'port': 1080, 'type': 'socks5'}]

async with EnhancedProxyManager(proxies=proxies) as manager:
    for url in urls_to_scrape:
        request = f"GET {url} HTTP/1.1\r\nHost: target.com\r\n\r\n".encode()
        response = await manager.send_tcp_data('target.com', 80, request)
        # Process response
```

### Load Testing
```python
async with EnhancedProxyManager(
    proxies=proxy_pool,
    strategy=ProxySelectionStrategy.RANDOM,
    max_concurrent=100
) as manager:
    tasks = [
        manager.send_tcp_data('api.example.com', 443, request)
        for _ in range(1000)
    ]
    results = await asyncio.gather(*tasks)
```

### High Availability
```python
async with EnhancedProxyManager(
    proxies=proxy_pool,
    strategy=ProxySelectionStrategy.FASTEST,
    max_retries=5,
    health_check_interval=30
) as manager:
    # Automatic failover and health monitoring
    response = await manager.send_http_request(
        'api.example.com',
        method='GET',
        path='/endpoint'
    )
```

---

## 📖 Full Documentation

- **README.md** - Complete overview and examples
- **docs/API_REFERENCE.md** - All 28 methods documented
- **docs/IMPLEMENTATION.md** - Technical deep-dive
- **docs/COMPARISON.md** - vs other libraries
- **docs/VISUAL_GUIDE.md** - Diagrams and visuals
- **docs/QUICK_REFERENCE.md** - Cheat sheet

---

## 🆘 Troubleshooting

### Import Error
```bash
pip install --upgrade pyroxi
```

### Connection Timeout
- Check proxy is online
- Increase timeout: `Connection(..., timeout=30)`
- Try different proxy

### Authentication Failed
```python
Connection(
    "proxy.com", 1080, 'socks5',
    username="user",
    password="pass"
)
```

---

## 🔗 Links

- **PyPI**: https://pypi.org/project/pyroxi/
- **GitHub**: https://github.com/bettercallninja/pyroxi
- **Issues**: https://github.com/bettercallninja/pyroxi/issues
- **License**: MIT

---

## ⭐ Support

If you find PyRoxi useful:
- ⭐ **Star on GitHub**: https://github.com/bettercallninja/pyroxi
- 🐦 **Share on social media**
- 💬 **Contribute feedback**

---

<div align="center">

**Made with ❤️ by bettercallninja**

Copyright © 2025 • [MIT License](LICENSE)

</div>
