# 📘 PyRoxi - Complete API Documentation

## Table of Contents

- [Overview](#overview)
- [Connection Class](#connection-class)
- [EnhancedProxyManager Class](#enhancedproxymanager-class)
- [ProxyConfig Dataclass](#proxyconfig-dataclass)
- [ProxySelectionStrategy Enum](#proxyselectionstrategy-enum)
- [Packet Module](#packet-module)
  - [PacketBuilder Class](#packetbuilder-class)
  - [AdvancedPacketBuilder Class](#advancedpacketbuilder-class)
  - [PacketParser Class](#packetparser-class)
- [Exceptions](#exceptions)
- [Examples](#examples)

---

## Overview

PyRoxi provides two main classes for proxy connections:

1. **`Connection`** - Low-level direct socket operations
2. **`EnhancedProxyManager`** - High-level proxy pool management with load balancing

---

## Connection Class

### Constructor

```python
Connection(
    proxy_address: str,
    proxy_port: int,
    proxy_type: str = 'http',
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 30,
    buffer_size: int = 8192
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `proxy_address` | str | Required | Proxy server address (IP or hostname) |
| `proxy_port` | int | Required | Proxy server port |
| `proxy_type` | str | `'http'` | Proxy type: `'http'` or `'socks5'` |
| `username` | str | `None` | Username for authentication (optional) |
| `password` | str | `None` | Password for authentication (optional) |
| `timeout` | int | `30` | Socket timeout in seconds |
| `buffer_size` | int | `8192` | Receive buffer size in bytes |

#### Example

```python
# SOCKS5 without auth
conn = Connection("127.0.0.1", 1080, 'socks5')

# HTTP with auth
conn = Connection("proxy.example.com", 8080, 'http', 
                 username="user", password="pass")

# With custom settings
conn = Connection("proxy.example.com", 1080, 'socks5',
                 timeout=60, buffer_size=16384)
```

---

### Methods

#### connect()

Establish connection to target server through proxy.

```python
async def connect(target_host: str, target_port: int) -> bool
```

**Parameters:**
- `target_host` (str): Target server hostname or IP
- `target_port` (int): Target server port

**Returns:** `bool` - True if connection successful

**Raises:**
- `ProxyConnectionError` - Connection failed
- `ProxyAuthenticationError` - Authentication failed

**Example:**
```python
async with Connection("127.0.0.1", 1080, 'socks5') as conn:
    await conn.connect("example.com", 80)
```

---

#### send_data()

Send raw binary data through the connection.

```python
async def send_data(data: bytes) -> int
```

**Parameters:**
- `data` (bytes): Binary data to send

**Returns:** `int` - Number of bytes sent

**Raises:**
- `ProxyConnectionError` - Send failed

**Example:**
```python
await conn.send_data(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
```

---

#### receive_data()

Receive binary data from the connection.

```python
async def receive_data(buffer_size: Optional[int] = None) -> bytes
```

**Parameters:**
- `buffer_size` (int, optional): Override default buffer size

**Returns:** `bytes` - Received data

**Raises:**
- `ProxyConnectionError` - Receive failed

**Example:**
```python
response = await conn.receive_data()
print(f"Received: {len(response)} bytes")
```

---

#### send_packet()

Send binary data with 4-byte length prefix (network byte order).

```python
async def send_packet(packet: bytes) -> int
```

**Parameters:**
- `packet` (bytes): Binary packet data

**Returns:** `int` - Number of bytes sent (including length prefix)

**Example:**
```python
packet = b"\x01\x02\x03\x04"
await conn.send_packet(packet)  # Sends: b"\x00\x00\x00\x04\x01\x02\x03\x04"
```

---

#### receive_packet()

Receive binary data with 4-byte length prefix.

```python
async def receive_packet() -> bytes
```

**Returns:** `bytes` - Received packet data (without length prefix)

**Raises:**
- `PacketError` - Invalid packet format
- `ProxyConnectionError` - Receive failed

**Example:**
```python
packet = await conn.receive_packet()
```

---

#### receive_all()

Receive all data until connection closes or timeout.

```python
async def receive_all(timeout: Optional[float] = None) -> bytes
```

**Parameters:**
- `timeout` (float, optional): Timeout in seconds

**Returns:** `bytes` - All received data

**Example:**
```python
response = await conn.receive_all(timeout=10)
```

---

#### send_http_request()

Send complete HTTP request through the tunnel.

```python
async def send_http_request(
    method: str = 'GET',
    path: str = '/',
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None
) -> bytes
```

**Parameters:**
- `method` (str): HTTP method (GET, POST, etc.)
- `path` (str): Request path
- `headers` (dict): HTTP headers
- `body` (bytes): Request body

**Returns:** `bytes` - HTTP response

**Example:**
```python
response = await conn.send_http_request(
    method='POST',
    path='/api/data',
    headers={'Content-Type': 'application/json'},
    body=b'{"key": "value"}'
)
```

---

#### disconnect()

Close the connection and cleanup resources.

```python
async def disconnect()
```

**Example:**
```python
await conn.disconnect()
```

---

#### is_connected()

Check if connection is active.

```python
def is_connected() -> bool
```

**Returns:** `bool` - True if connected

---

#### get_connection_info()

Get connection information.

```python
def get_connection_info() -> Dict[str, Any]
```

**Returns:** Dictionary with connection details

**Example:**
```python
info = conn.get_connection_info()
print(f"Connected via {info['proxy_type']} to {info['target']}")
```

---

#### set_timeout()

Change socket timeout.

```python
def set_timeout(timeout: int)
```

**Parameters:**
- `timeout` (int): New timeout in seconds

---

#### set_buffer_size()

Change receive buffer size.

```python
def set_buffer_size(size: int)
```

**Parameters:**
- `size` (int): New buffer size in bytes

---

## EnhancedProxyManager Class

### Constructor

```python
EnhancedProxyManager(
    proxies: Optional[Union[Dict, List[Dict], ProxyConfig, List[ProxyConfig]]] = None,
    strategy: ProxySelectionStrategy = ProxySelectionStrategy.ROUND_ROBIN,
    max_concurrent: int = 10,
    enable_failover: bool = True,
    health_check_interval: int = 60,
    max_retries: int = 3
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `proxies` | Dict/List | `None` | Single proxy or list of proxies |
| `strategy` | ProxySelectionStrategy | `ROUND_ROBIN` | Proxy selection strategy |
| `max_concurrent` | int | `10` | Maximum concurrent connections |
| `enable_failover` | bool | `True` | Enable automatic failover |
| `health_check_interval` | int | `60` | Health check interval (seconds, 0=disabled) |
| `max_retries` | int | `3` | Maximum retry attempts |

#### Example

```python
# Single proxy
manager = EnhancedProxyManager(
    proxies={'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}
)

# Multiple proxies
manager = EnhancedProxyManager(
    proxies=[
        {'address': 'proxy1', 'port': 1080, 'type': 'socks5'},
        {'address': 'proxy2', 'port': 1080, 'type': 'socks5'},
    ],
    strategy=ProxySelectionStrategy.FASTEST,
    enable_failover=True,
    max_concurrent=20
)
```

---

### Core Methods

#### get_connection()

Get a connection to target through proxy.

```python
async def get_connection(
    target_host: str,
    target_port: int,
    proxy_config: Optional[ProxyConfig] = None
) -> Connection
```

**Parameters:**
- `target_host` (str): Target hostname
- `target_port` (int): Target port
- `proxy_config` (ProxyConfig, optional): Specific proxy to use

**Returns:** `Connection` - Connected Connection object

**Example:**
```python
conn = await manager.get_connection('example.com', 80)
await conn.send_data(b"...")
await conn.disconnect()
```

---

#### send_tcp_data()

Send TCP data through proxy.

```python
async def send_tcp_data(
    target_host: str,
    target_port: int,
    data: bytes,
    receive: bool = True
) -> Optional[bytes]
```

**Parameters:**
- `target_host` (str): Target hostname
- `target_port` (int): Target port
- `data` (bytes): Data to send
- `receive` (bool): Whether to receive response

**Returns:** `bytes` or `None` - Response data if receive=True

**Example:**
```python
response = await manager.send_tcp_data(
    'example.com', 80,
    b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
)
```

---

#### send_http_request()

Send HTTP request through proxy.

```python
async def send_http_request(
    target_host: str,
    method: str = 'GET',
    path: str = '/',
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    port: int = 80
) -> bytes
```

**Parameters:**
- `target_host` (str): Target hostname
- `method` (str): HTTP method
- `path` (str): Request path
- `headers` (dict): HTTP headers
- `body` (bytes): Request body
- `port` (int): Target port

**Returns:** `bytes` - HTTP response

**Example:**
```python
response = await manager.send_http_request(
    'api.example.com',
    method='POST',
    path='/api/endpoint',
    headers={'Content-Type': 'application/json'},
    body=b'{"data": "value"}'
)
```

---

#### execute_with_proxy()

Execute custom operation through proxy with retry logic.

```python
async def execute_with_proxy(
    target_host: str,
    target_port: int,
    operation: callable,
    **kwargs
) -> Any
```

**Parameters:**
- `target_host` (str): Target hostname
- `target_port` (int): Target port
- `operation` (callable): Async function taking Connection as first arg
- `**kwargs`: Additional arguments for operation

**Returns:** Result from operation

**Example:**
```python
async def custom_operation(conn: Connection, message: str):
    await conn.send_data(message.encode())
    return await conn.receive_data()

result = await manager.execute_with_proxy(
    'example.com', 80,
    custom_operation,
    message="Hello"
)
```

---

#### add_proxy()

Add a proxy to the pool.

```python
def add_proxy(proxy: Union[Dict, ProxyConfig])
```

**Parameters:**
- `proxy` (Dict/ProxyConfig): Proxy configuration

**Example:**
```python
manager.add_proxy({'address': 'new-proxy', 'port': 1080, 'type': 'socks5'})
```

---

#### remove_proxy()

Remove a proxy from the pool.

```python
def remove_proxy(address: str, port: int)
```

**Parameters:**
- `address` (str): Proxy address
- `port` (int): Proxy port

**Example:**
```python
manager.remove_proxy('old-proxy', 1080)
```

---

#### get_statistics()

Get proxy statistics.

```python
def get_statistics() -> List[Dict[str, Any]]
```

**Returns:** List of dictionaries with proxy statistics

**Example:**
```python
stats = manager.get_statistics()
for stat in stats:
    print(f"Proxy: {stat['proxy']}")
    print(f"Success Rate: {stat['success_rate']}")
```

---

#### print_statistics()

Print formatted proxy statistics.

```python
def print_statistics()
```

**Example:**
```python
manager.print_statistics()
```

---

### Exclusive Advanced Methods

#### get_fastest_proxy()

Test all proxies and return the fastest one.

```python
async def get_fastest_proxy(
    test_host: str = "www.google.com",
    test_port: int = 80
) -> Optional[ProxyConfig]
```

**Parameters:**
- `test_host` (str): Host to test against
- `test_port` (int): Port to test

**Returns:** `ProxyConfig` or `None` - Fastest proxy

**Example:**
```python
fastest = await manager.get_fastest_proxy()
print(f"Fastest proxy: {fastest}")
```

---

#### proxy_chain()

Create a chain of proxies (proxy through proxy).

```python
async def proxy_chain(
    target_host: str,
    target_port: int,
    chain_proxies: Optional[List[ProxyConfig]] = None
) -> Connection
```

**Parameters:**
- `target_host` (str): Final target host
- `target_port` (int): Final target port
- `chain_proxies` (List[ProxyConfig]): List of proxies to chain

**Returns:** `Connection` - Connection through the chain

**Example:**
```python
chain = [proxy1, proxy2, proxy3]
conn = await manager.proxy_chain('target.com', 80, chain)
# Connected: You -> proxy1 -> proxy2 -> proxy3 -> target.com
```

---

#### rotating_request()

Send multiple requests rotating through all proxies.

```python
async def rotating_request(
    target_host: str,
    target_port: int,
    data: bytes,
    rotation_count: int = 5
) -> List[bytes]
```

**Parameters:**
- `target_host` (str): Target host
- `target_port` (int): Target port
- `data` (bytes): Data to send
- `rotation_count` (int): Number of requests

**Returns:** `List[bytes]` - List of responses

**Example:**
```python
responses = await manager.rotating_request(
    'example.com', 80,
    b"GET / HTTP/1.1\r\n\r\n",
    rotation_count=10
)
```

---

#### smart_failover()

Smart failover avoiding proxies with low success rates.

```python
async def smart_failover(
    target_host: str,
    target_port: int,
    data: bytes,
    min_success_rate: float = 0.7
) -> bytes
```

**Parameters:**
- `target_host` (str): Target host
- `target_port` (int): Target port
- `data` (bytes): Data to send
- `min_success_rate` (float): Minimum success rate (0.0-1.0)

**Returns:** `bytes` - Response data

**Example:**
```python
response = await manager.smart_failover(
    'api.example.com', 443,
    request_data,
    min_success_rate=0.8  # Only use proxies with 80%+ success
)
```

---

#### load_balance_by_latency()

Distribute requests based on proxy latency.

```python
async def load_balance_by_latency(
    target_host: str,
    target_port: int,
    requests: List[bytes],
    latency_threshold: float = 2.0
) -> List[bytes]
```

**Parameters:**
- `target_host` (str): Target host
- `target_port` (int): Target port
- `requests` (List[bytes]): List of request data
- `latency_threshold` (float): Max latency in seconds

**Returns:** `List[bytes]` - List of responses

**Example:**
```python
requests = [req1, req2, req3, ...]
responses = await manager.load_balance_by_latency(
    'api.example.com', 443,
    requests,
    latency_threshold=1.5  # Only use proxies under 1.5s
)
```

---

#### benchmark_proxies()

Benchmark all proxies with multiple iterations.

```python
async def benchmark_proxies(
    test_host: str = "www.google.com",
    test_port: int = 80,
    iterations: int = 3
) -> Dict[str, Dict[str, float]]
```

**Parameters:**
- `test_host` (str): Host to test
- `test_port` (int): Port to test
- `iterations` (int): Number of test iterations

**Returns:** Dictionary with benchmark results

**Example:**
```python
results = await manager.benchmark_proxies(iterations=5)
for proxy, metrics in results.items():
    print(f"{proxy}: {metrics['avg_time']:.2f}s avg")
```

---

#### export_config()

Export configuration to JSON file.

```python
def export_config(filepath: str)
```

**Parameters:**
- `filepath` (str): Path to save configuration

**Example:**
```python
manager.export_config('my_proxies.json')
```

---

#### import_config()

Load configuration from JSON file (class method).

```python
@classmethod
def import_config(cls, filepath: str) -> 'EnhancedProxyManager'
```

**Parameters:**
- `filepath` (str): Path to configuration file

**Returns:** `EnhancedProxyManager` - Configured manager

**Example:**
```python
manager = EnhancedProxyManager.import_config('my_proxies.json')
```

---

## ProxyConfig Dataclass

```python
@dataclass
class ProxyConfig:
    address: str
    port: int
    type: str = 'socks5'
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    buffer_size: int = 8192
```

### Properties

- `success_rate` (float): Success rate (0.0-1.0)
- `avg_response_time` (float): Average response time in seconds

### Methods

- `to_dict()` - Convert to dictionary
- `from_dict(data)` - Create from dictionary (class method)

**Example:**
```python
from pyroxi import ProxyConfig

# Create
proxy = ProxyConfig('127.0.0.1', 1080, 'socks5')

# Convert
proxy_dict = proxy.to_dict()
proxy2 = ProxyConfig.from_dict(proxy_dict)

# Check stats
print(f"Success rate: {proxy.success_rate*100:.1f}%")
print(f"Avg time: {proxy.avg_response_time:.2f}s")
```

---

## ProxySelectionStrategy Enum

```python
class ProxySelectionStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_USED = "least_used"
    FASTEST = "fastest"
    SEQUENTIAL = "sequential"
```

### Strategies

| Strategy | Description |
|----------|-------------|
| `ROUND_ROBIN` | Cycle through proxies in order |
| `RANDOM` | Random proxy selection |
| `LEAST_USED` | Use proxy with fewest total requests |
| `FASTEST` | Use proxy with best average response time |
| `SEQUENTIAL` | Always use first available proxy |

**Example:**
```python
from pyroxi import ProxySelectionStrategy

manager = EnhancedProxyManager(
    proxies=proxies,
    strategy=ProxySelectionStrategy.FASTEST
)
```

---

## Packet Module

The packet module provides utilities for building and parsing various network packets. All classes are fully tested and production-ready.

### PacketBuilder Class

Build various types of network packets.

#### Constructor

```python
from pyroxi import PacketBuilder

builder = PacketBuilder()
```

#### Methods

##### build_http_packet()

Build an HTTP request packet.

```python
def build_http_packet(
    method: str,
    path: str,
    headers: Optional[Dict] = None,
    body: Optional[Union[str, bytes]] = None,
    version: str = "1.1"
) -> bytes
```

**Parameters:**
- `method` (str): HTTP method (GET, POST, PUT, DELETE, etc.)
- `path` (str): Request path (e.g., "/api/users")
- `headers` (dict, optional): HTTP headers
- `body` (str/bytes, optional): Request body
- `version` (str): HTTP version (default: "1.1")

**Returns:** `bytes` - Complete HTTP packet

**Example:**
```python
from pyroxi import PacketBuilder

builder = PacketBuilder()

# Simple GET request
packet = builder.build_http_packet(
    "GET",
    "/api/data",
    headers={"Host": "api.example.com", "User-Agent": "PyRoxi/1.0"}
)

# POST with body
packet = builder.build_http_packet(
    "POST",
    "/api/users",
    headers={"Host": "api.example.com", "Content-Type": "application/json"},
    body='{"name": "John", "email": "john@example.com"}'
)
```

---

##### build_tcp_packet()

Build a raw TCP packet.

```python
def build_tcp_packet(
    data: Union[str, bytes],
    encoding: str = 'utf-8'
) -> bytes
```

**Parameters:**
- `data` (str/bytes): Raw data to send
- `encoding` (str): Text encoding (default: 'utf-8')

**Returns:** `bytes` - TCP packet

**Example:**
```python
# Text data
packet = builder.build_tcp_packet("Hello, World!")

# Binary data
packet = builder.build_tcp_packet(b"\x00\x01\x02\x03")
```

---

##### build_json_packet()

Build a JSON packet with proper encoding.

```python
def build_json_packet(data: Dict[str, Any]) -> bytes
```

**Parameters:**
- `data` (dict): Python dictionary to convert to JSON

**Returns:** `bytes` - JSON packet

**Example:**
```python
packet = builder.build_json_packet({
    "action": "login",
    "username": "user",
    "password": "pass"
})
```

---

### AdvancedPacketBuilder Class

Build advanced protocol packets (SOCKS5, HTTP CONNECT, WebSocket).

#### Constructor

```python
from pyroxi import AdvancedPacketBuilder

builder = AdvancedPacketBuilder()
```

#### Methods

##### build_socks5_greeting()

Build SOCKS5 greeting packet (authentication negotiation).

```python
def build_socks5_greeting(
    auth_methods: list = [0, 2]
) -> bytes
```

**Parameters:**
- `auth_methods` (list): Authentication methods (0=no auth, 2=username/password)

**Returns:** `bytes` - SOCKS5 greeting packet

**Example:**
```python
builder = AdvancedPacketBuilder()

# No authentication
greeting = builder.build_socks5_greeting([0])

# With username/password support
greeting = builder.build_socks5_greeting([0, 2])
```

---

##### build_socks5_connect()

Build SOCKS5 connect request packet.

```python
def build_socks5_connect(
    address: str,
    port: int,
    address_type: int = 3
) -> bytes
```

**Parameters:**
- `address` (str): Target hostname or IP
- `port` (int): Target port
- `address_type` (int): 1=IPv4, 3=Domain, 4=IPv6 (default: 3)

**Returns:** `bytes` - SOCKS5 connect packet

**Example:**
```python
# Connect to domain
connect = builder.build_socks5_connect("example.com", 80, address_type=3)

# Connect to IPv4
connect = builder.build_socks5_connect("93.184.216.34", 80, address_type=1)
```

---

##### build_http_connect()

Build HTTP CONNECT tunnel request.

```python
def build_http_connect(
    host: str,
    port: int,
    headers: Optional[Dict] = None
) -> bytes
```

**Parameters:**
- `host` (str): Target hostname
- `port` (int): Target port
- `headers` (dict, optional): Additional HTTP headers

**Returns:** `bytes` - HTTP CONNECT packet

**Example:**
```python
# Basic CONNECT
connect = builder.build_http_connect("example.com", 443)

# With proxy authentication
connect = builder.build_http_connect(
    "example.com",
    443,
    headers={"Proxy-Authorization": "Basic dXNlcjpwYXNz"}
)
```

---

##### build_websocket_handshake()

Build WebSocket handshake request.

```python
def build_websocket_handshake(
    host: str,
    path: str = "/",
    headers: Optional[Dict] = None
) -> bytes
```

**Parameters:**
- `host` (str): WebSocket server host
- `path` (str): WebSocket path (default: "/")
- `headers` (dict, optional): Additional headers

**Returns:** `bytes` - WebSocket handshake packet

**Example:**
```python
handshake = builder.build_websocket_handshake(
    "ws.example.com",
    "/socket",
    headers={"Origin": "https://example.com"}
)
```

---

### PacketParser Class

Parse various types of network packets.

#### Constructor

```python
from pyroxi import PacketParser

parser = PacketParser()
```

#### Methods

##### parse_http_response()

Parse HTTP response packet.

```python
def parse_http_response(data: bytes) -> Dict[str, Any]
```

**Parameters:**
- `data` (bytes): Raw HTTP response data

**Returns:** Dictionary with:
- `version` (str): HTTP version
- `status_code` (int): Status code (e.g., 200, 404)
- `reason_phrase` (str): Reason phrase (e.g., "OK")
- `headers` (dict): Response headers
- `body` (str): Response body

**Example:**
```python
parser = PacketParser()

response_data = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nHello"
parsed = parser.parse_http_response(response_data)

print(parsed['status_code'])  # 200
print(parsed['headers']['Content-Type'])  # text/html
print(parsed['body'])  # Hello
```

---

##### parse_json_packet()

Parse JSON packet.

```python
def parse_json_packet(data: bytes) -> Dict[str, Any]
```

**Parameters:**
- `data` (bytes): Raw JSON data

**Returns:** `dict` - Parsed JSON object

**Example:**
```python
json_data = b'{"status": "success", "data": [1, 2, 3]}'
parsed = parser.parse_json_packet(json_data)

print(parsed['status'])  # success
print(parsed['data'])  # [1, 2, 3]
```

---

##### parse_socks5_response()

Parse SOCKS5 server response.

```python
def parse_socks5_response(data: bytes) -> Dict[str, Any]
```

**Parameters:**
- `data` (bytes): SOCKS5 response data

**Returns:** Dictionary with:
- `version` (int): SOCKS version
- `reply` (int): Reply code (0=success)
- `address_type` (int): Address type
- `address` (str): Bound address
- `port` (int): Bound port

**Example:**
```python
response = parser.parse_socks5_response(response_data)
if response['reply'] == 0:
    print("Connection successful!")
```

---

##### parse_length_prefixed()

Parse length-prefixed packet (4-byte big-endian length + data).

```python
def parse_length_prefixed(data: bytes) -> Tuple[bytes, bytes]
```

**Parameters:**
- `data` (bytes): Length-prefixed packet data

**Returns:** Tuple of `(packet_data, remaining_data)`

**Example:**
```python
# Data with length prefix
data = b"\x00\x00\x00\x05Hello\x00\x00\x00\x05World"

packet, remaining = parser.parse_length_prefixed(data)
print(packet)  # b"Hello"

packet2, _ = parser.parse_length_prefixed(remaining)
print(packet2)  # b"World"
```

---

##### detect_packet_type()

Auto-detect packet type from raw data.

```python
def detect_packet_type(data: bytes) -> str
```

**Parameters:**
- `data` (bytes): Raw packet data

**Returns:** `str` - Packet type ("HTTP", "JSON", "SOCKS5", "BINARY", "UNKNOWN")

**Example:**
```python
# Detect HTTP
http_data = b"HTTP/1.1 200 OK\r\n\r\n"
print(parser.detect_packet_type(http_data))  # "HTTP"

# Detect JSON
json_data = b'{"key": "value"}'
print(parser.detect_packet_type(json_data))  # "JSON"

# Detect SOCKS5
socks_data = b"\x05\x00\x00\x01..."
print(parser.detect_packet_type(socks_data))  # "SOCKS5"
```

---

### Packet Module Example

Complete example using packet builders and parsers:

```python
import asyncio
from pyroxi import Connection, PacketBuilder, PacketParser

async def main():
    builder = PacketBuilder()
    parser = PacketParser()
    
    # Connect through proxy
    async with Connection("127.0.0.1", 1080, 'socks5') as conn:
        await conn.connect("api.example.com", 80)
        
        # Build HTTP GET request
        request = builder.build_http_packet(
            "GET",
            "/api/data",
            headers={
                "Host": "api.example.com",
                "User-Agent": "PyRoxi/1.0",
                "Accept": "application/json"
            }
        )
        
        # Send request
        await conn.send_data(request)
        
        # Receive response
        response_data = await conn.receive_data()
        
        # Parse response
        response = parser.parse_http_response(response_data)
        
        print(f"Status: {response['status_code']}")
        print(f"Headers: {response['headers']}")
        print(f"Body: {response['body']}")
        
        # If body is JSON, parse it
        if 'application/json' in response['headers'].get('Content-Type', ''):
            json_data = parser.parse_json_packet(response['body'].encode())
            print(f"JSON Data: {json_data}")

asyncio.run(main())
```

---

## Exceptions

### ProxyConnectionError

Raised when proxy connection fails.

```python
from pyroxi.exceptions import ProxyConnectionError

try:
    await conn.connect('example.com', 80)
except ProxyConnectionError as e:
    print(f"Connection failed: {e}")
```

### ProxyAuthenticationError

Raised when proxy authentication fails.

```python
from pyroxi.exceptions import ProxyAuthenticationError

try:
    await conn.connect('example.com', 80)
except ProxyAuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### PacketError

Raised when packet framing is invalid.

```python
from pyroxi.exceptions import PacketError

try:
    packet = await conn.receive_packet()
except PacketError as e:
    print(f"Invalid packet: {e}")
```

---

## Complete Examples

### Example 1: Simple SOCKS5 Connection

```python
import asyncio
from pyroxi import Connection

async def main():
    conn = Connection("127.0.0.1", 1080, 'socks5')
    
    try:
        await conn.connect("example.com", 80)
        await conn.send_data(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
        response = await conn.receive_data()
        print(response[:100])
    finally:
        await conn.disconnect()

asyncio.run(main())
```

### Example 2: Multi-Proxy Load Balancing

```python
import asyncio
from pyroxi import EnhancedProxyManager, ProxySelectionStrategy

async def main():
    proxies = [
        {'address': 'proxy1', 'port': 1080, 'type': 'socks5'},
        {'address': 'proxy2', 'port': 1080, 'type': 'socks5'},
    ]
    
    async with EnhancedProxyManager(
        proxies=proxies,
        strategy=ProxySelectionStrategy.ROUND_ROBIN,
        enable_failover=True
    ) as manager:
        
        # Make 10 requests
        for i in range(10):
            response = await manager.send_tcp_data(
                'example.com', 80,
                b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
            )
            print(f"Request {i+1}: {len(response)} bytes")
        
        # Print statistics
        manager.print_statistics()

asyncio.run(main())
```

### Example 3: Advanced Features

```python
import asyncio
from pyroxi import EnhancedProxyManager

async def main():
    manager = EnhancedProxyManager(proxies=proxy_list)
    
    async with manager:
        # Find fastest proxy
        fastest = await manager.get_fastest_proxy()
        print(f"Fastest: {fastest}")
        
        # Benchmark all
        results = await manager.benchmark_proxies(iterations=3)
        
        # Smart routing
        response = await manager.smart_failover(
            'api.example.com', 443,
            request_data,
            min_success_rate=0.8
        )
        
        # Rotate requests
        responses = await manager.rotating_request(
            'example.com', 80,
            request_data,
            rotation_count=5
        )
        
        # Export config
        manager.export_config('config.json')

asyncio.run(main())
```

---

## Performance Tips

1. **Use connection pooling** - Reuse connections when possible
2. **Adjust buffer size** - Increase for large transfers
3. **Choose right strategy** - FASTEST for speed, ROUND_ROBIN for fairness
4. **Enable failover** - Always enable in production
5. **Monitor statistics** - Regularly check proxy health
6. **Tune concurrency** - Balance between performance and resource usage

---

## Threading & Concurrency

PyRoxi is built on `asyncio` and must be used with async/await:

```python
# ✅ Correct
async def my_function():
    async with EnhancedProxyManager(...) as manager:
        await manager.send_tcp_data(...)

# ❌ Wrong
def my_function():
    manager = EnhancedProxyManager(...)
    manager.send_tcp_data(...)  # Missing await!
```

---

For more information, see:
- [Complete Usage Examples](../examples/complete_usage_examples.py)
- [Implementation Details](IMPLEMENTATION.md)
- [Quick Reference](QUICK_REFERENCE.md)
