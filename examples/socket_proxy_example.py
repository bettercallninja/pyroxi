"""
High-Speed Socket-Based Proxy Connection Examples
Demonstrates SOCKS5 and HTTP proxy connections with binary networking
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyroxi.core.connection import Connection
from pyroxi.exceptions import ProxyConnectionError, ProxyAuthenticationError


async def example_socks5_connection():
    """Example: Connect through SOCKS5 proxy and send HTTP request"""
    print("=" * 60)
    print("SOCKS5 Proxy Connection Example")
    print("=" * 60)
    
    # SOCKS5 proxy configuration
    proxy_address = "127.0.0.1"  # Replace with your SOCKS5 proxy
    proxy_port = 1080
    target_host = "httpbin.org"
    target_port = 80
    
    # Create connection
    connection = Connection(
        proxy_address=proxy_address,
        proxy_port=proxy_port,
        proxy_type='socks5',
        timeout=30,
        buffer_size=8192
    )
    
    try:
        # Connect through SOCKS5 proxy to target
        print(f"\n📡 Connecting to {target_host}:{target_port} via SOCKS5...")
        await connection.connect(target_host, target_port)
        print(f"✅ Connected successfully!")
        print(f"Connection info: {connection.get_connection_info()}")
        
        # Send HTTP GET request
        http_request = (
            f"GET /get HTTP/1.1\r\n"
            f"Host: {target_host}\r\n"
            f"User-Agent: pyroxi/1.0\r\n"
            f"Accept: */*\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        
        print(f"\n📤 Sending HTTP request...")
        await connection.send_data(http_request.encode())
        
        # Receive response
        print(f"📥 Receiving response...")
        response = await connection.receive_all(timeout=10)
        
        # Parse and display response
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\r\n')
        print(f"\n🎯 Response Status: {lines[0]}")
        print(f"📊 Response Size: {len(response)} bytes")
        print(f"\nFirst 500 characters of response:")
        print("-" * 60)
        print(response_str[:500])
        
    except ProxyConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await connection.disconnect()
        print(f"\n🔌 Disconnected from proxy")


async def example_socks5_with_auth():
    """Example: SOCKS5 proxy with username/password authentication"""
    print("\n" + "=" * 60)
    print("SOCKS5 with Authentication Example")
    print("=" * 60)
    
    connection = Connection(
        proxy_address="127.0.0.1",
        proxy_port=1080,
        proxy_type='socks5',
        username="user",
        password="pass",
        timeout=30
    )
    
    try:
        print(f"\n📡 Connecting with authentication...")
        await connection.connect("example.com", 80)
        print(f"✅ Authenticated and connected!")
        
        # Send simple request
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        await connection.send_data(request)
        
        response = await connection.receive_data()
        print(f"📥 Received {len(response)} bytes")
        
    except ProxyAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except ProxyConnectionError as e:
        print(f"❌ Connection error: {e}")
    finally:
        await connection.disconnect()


async def example_http_proxy():
    """Example: Connect through HTTP proxy using CONNECT method"""
    print("\n" + "=" * 60)
    print("HTTP Proxy Connection Example")
    print("=" * 60)
    
    # HTTP proxy configuration
    proxy_address = "127.0.0.1"  # Replace with your HTTP proxy
    proxy_port = 8080
    target_host = "httpbin.org"
    target_port = 80
    
    connection = Connection(
        proxy_address=proxy_address,
        proxy_port=proxy_port,
        proxy_type='http',
        timeout=30
    )
    
    try:
        print(f"\n📡 Connecting to {target_host}:{target_port} via HTTP proxy...")
        await connection.connect(target_host, target_port)
        print(f"✅ HTTP tunnel established!")
        
        # Send HTTP request through tunnel
        http_request = (
            f"GET /headers HTTP/1.1\r\n"
            f"Host: {target_host}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        
        print(f"\n📤 Sending request through tunnel...")
        await connection.send_data(http_request.encode())
        
        print(f"📥 Receiving response...")
        response = await connection.receive_all(timeout=10)
        
        response_str = response.decode('utf-8', errors='ignore')
        print(f"\n🎯 Response ({len(response)} bytes):")
        print("-" * 60)
        print(response_str[:500])
        
    except ProxyConnectionError as e:
        print(f"❌ Connection error: {e}")
    finally:
        await connection.disconnect()


async def example_http_proxy_with_auth():
    """Example: HTTP proxy with authentication"""
    print("\n" + "=" * 60)
    print("HTTP Proxy with Authentication Example")
    print("=" * 60)
    
    connection = Connection(
        proxy_address="127.0.0.1",
        proxy_port=8080,
        proxy_type='http',
        username="proxyuser",
        password="proxypass"
    )
    
    try:
        print(f"\n📡 Connecting with proxy authentication...")
        await connection.connect("httpbin.org", 80)
        print(f"✅ Connected and authenticated!")
        
    except ProxyAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
    except ProxyConnectionError as e:
        print(f"❌ Connection error: {e}")
    finally:
        await connection.disconnect()


async def example_binary_packet_transfer():
    """Example: Send and receive binary packets with length framing"""
    print("\n" + "=" * 60)
    print("Binary Packet Transfer Example")
    print("=" * 60)
    
    connection = Connection(
        proxy_address="127.0.0.1",
        proxy_port=1080,
        proxy_type='socks5'
    )
    
    try:
        # Connect to a target that echoes data
        await connection.connect("echo-server.example.com", 7)  # Echo protocol
        
        # Send binary packet with length prefix
        binary_data = b"\x00\x01\x02\x03\x04\x05"
        print(f"\n📤 Sending binary packet: {binary_data.hex()}")
        await connection.send_packet(binary_data)
        
        # Receive packet with length prefix
        print(f"📥 Receiving binary packet...")
        received = await connection.receive_packet()
        print(f"✅ Received: {received.hex()}")
        
    except ProxyConnectionError as e:
        print(f"❌ Error: {e}")
    finally:
        await connection.disconnect()


async def example_context_manager():
    """Example: Using connection as context manager"""
    print("\n" + "=" * 60)
    print("Context Manager Example")
    print("=" * 60)
    
    # Automatically handles connection cleanup
    async with Connection("127.0.0.1", 1080, 'socks5') as conn:
        await conn.connect("example.com", 80)
        print(f"✅ Connected: {conn.is_connected()}")
        
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        await conn.send_data(request)
        response = await conn.receive_data()
        print(f"📥 Received {len(response)} bytes")
    
    print(f"🔌 Automatically disconnected")


async def main():
    """Run all examples"""
    print("\n🚀 PyRoxi High-Speed Socket Proxy Examples\n")
    
    # Choose which examples to run
    examples = [
        ("SOCKS5 Basic", example_socks5_connection),
        ("SOCKS5 with Auth", example_socks5_with_auth),
        ("HTTP Proxy", example_http_proxy),
        ("HTTP with Auth", example_http_proxy_with_auth),
        ("Binary Packets", example_binary_packet_transfer),
        ("Context Manager", example_context_manager),
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  0. Run all examples")
    
    try:
        choice = input("\nSelect example (0-6): ").strip()
        choice = int(choice) if choice else 0
        
        if choice == 0:
            # Run all examples
            for name, func in examples:
                try:
                    await func()
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"❌ {name} failed: {e}")
        elif 1 <= choice <= len(examples):
            # Run selected example
            await examples[choice - 1][1]()
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
