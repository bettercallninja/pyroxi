"""
PyRoxi Usage Examples - Single and Multi-Proxy Support
Demonstrates all features with practical examples
"""

import asyncio
import logging
from pyroxi import (
    Connection,
    EnhancedProxyManager,
    ProxyConfig,
    ProxySelectionStrategy,
    ProxyConnectionError
)

logging.basicConfig(level=logging.INFO)


# ============================================================================
# EXAMPLE 1: Single Proxy - Simple Dictionary Format
# ============================================================================

async def example_1_single_proxy_dict():
    """Use a single proxy defined as a dictionary"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Single Proxy (Dictionary Format)")
    print("="*80)
    
    # Define single proxy as dict
    proxy = {
        'address': '127.0.0.1',
        'port': 1080,
        'type': 'socks5',
        'username': 'user',      # Optional
        'password': 'pass'       # Optional
    }
    
    # Create manager with single proxy
    async with EnhancedProxyManager(proxies=proxy) as manager:
        print(f"✅ Manager created: {manager}")
        
        # Send request
        request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        response = await manager.send_tcp_data('example.com', 80, request)
        print(f"📥 Received {len(response)} bytes")


# ============================================================================
# EXAMPLE 2: Single Proxy - Direct Connection Object
# ============================================================================

async def example_2_single_connection():
    """Use Connection object directly for single proxy"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Single Proxy (Direct Connection)")
    print("="*80)
    
    async with Connection('127.0.0.1', 1080, 'socks5') as conn:
        # Connect to target
        await conn.connect('httpbin.org', 80)
        print("✅ Connected to httpbin.org")
        
        # Send HTTP request
        request = b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n"
        await conn.send_data(request)
        
        # Receive response
        response = await conn.receive_all(timeout=10)
        print(f"📥 Received: {response[:200].decode('utf-8', errors='ignore')}")


# ============================================================================
# EXAMPLE 3: Multiple Proxies - List Format
# ============================================================================

async def example_3_multi_proxy_list():
    """Use multiple proxies defined as list"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Multiple Proxies (List Format)")
    print("="*80)
    
    # Define multiple proxies
    proxies = [
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
        {'address': '127.0.0.1', 'port': 1081, 'type': 'socks5'},
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
    ]
    
    async with EnhancedProxyManager(
        proxies=proxies,
        strategy=ProxySelectionStrategy.ROUND_ROBIN,
        max_concurrent=5
    ) as manager:
        print(f"✅ Manager created with {len(proxies)} proxies")
        
        # Make multiple requests (will use different proxies)
        for i in range(3):
            try:
                request = f"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n".encode()
                response = await manager.send_tcp_data('example.com', 80, request)
                print(f"📥 Request {i+1}: Received {len(response)} bytes")
            except Exception as e:
                print(f"❌ Request {i+1} failed: {e}")
        
        # Show statistics
        manager.print_statistics()


# ============================================================================
# EXAMPLE 4: Multiple Proxies with ProxyConfig Objects
# ============================================================================

async def example_4_multi_proxy_config():
    """Use ProxyConfig objects for better control"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Multiple Proxies (ProxyConfig Objects)")
    print("="*80)
    
    # Create proxy configurations
    proxies = [
        ProxyConfig(
            address='127.0.0.1',
            port=1080,
            type='socks5',
            timeout=30,
            buffer_size=8192
        ),
        ProxyConfig(
            address='proxy.server.com',
            port=8080,
            type='http',
            username='user',
            password='pass',
            timeout=60
        ),
    ]
    
    async with EnhancedProxyManager(
        proxies=proxies,
        strategy=ProxySelectionStrategy.RANDOM
    ) as manager:
        print(f"✅ Manager: {manager}")
        
        # Send request
        response = await manager.send_http_request(
            target_host='httpbin.org',
            method='GET',
            path='/get',
            headers={'User-Agent': 'PyRoxi/1.0'}
        )
        print(f"📥 HTTP Response: {len(response)} bytes")


# ============================================================================
# EXAMPLE 5: Proxy Selection Strategies
# ============================================================================

async def example_5_selection_strategies():
    """Demonstrate different proxy selection strategies"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Proxy Selection Strategies")
    print("="*80)
    
    proxies = [
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
        {'address': '127.0.0.1', 'port': 1081, 'type': 'socks5'},
        {'address': '127.0.0.1', 'port': 1082, 'type': 'socks5'},
    ]
    
    strategies = [
        ('ROUND_ROBIN', ProxySelectionStrategy.ROUND_ROBIN),
        ('RANDOM', ProxySelectionStrategy.RANDOM),
        ('SEQUENTIAL', ProxySelectionStrategy.SEQUENTIAL),
    ]
    
    for name, strategy in strategies:
        print(f"\n📊 Testing {name} strategy:")
        
        async with EnhancedProxyManager(
            proxies=proxies,
            strategy=strategy
        ) as manager:
            # Make 3 requests
            for i in range(3):
                try:
                    request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
                    await manager.send_tcp_data('example.com', 80, request)
                    print(f"  ✅ Request {i+1} completed")
                except Exception as e:
                    print(f"  ❌ Request {i+1} failed: {e}")


# ============================================================================
# EXAMPLE 6: Automatic Failover
# ============================================================================

async def example_6_failover():
    """Demonstrate automatic failover to working proxies"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Automatic Failover")
    print("="*80)
    
    # Mix of invalid and valid proxies
    proxies = [
        {'address': '1.2.3.4', 'port': 9999, 'type': 'socks5'},  # Invalid
        {'address': '5.6.7.8', 'port': 8888, 'type': 'socks5'},  # Invalid
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},  # Valid
    ]
    
    async with EnhancedProxyManager(
        proxies=proxies,
        enable_failover=True,
        max_retries=3
    ) as manager:
        print("✅ Manager created with failover enabled")
        
        try:
            request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
            response = await manager.send_tcp_data('example.com', 80, request)
            print(f"✅ Failover successful! Received {len(response)} bytes")
        except Exception as e:
            print(f"❌ All proxies failed: {e}")


# ============================================================================
# EXAMPLE 7: Concurrent Requests
# ============================================================================

async def example_7_concurrent():
    """Send multiple concurrent requests through proxy pool"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Concurrent Requests")
    print("="*80)
    
    proxies = [
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
        {'address': '127.0.0.1', 'port': 1081, 'type': 'socks5'},
    ]
    
    async with EnhancedProxyManager(
        proxies=proxies,
        max_concurrent=10
    ) as manager:
        print("✅ Sending 5 concurrent requests...")
        
        # Create concurrent tasks
        async def fetch(url: str, port: int):
            request = f"GET / HTTP/1.1\r\nHost: {url}\r\n\r\n".encode()
            return await manager.send_tcp_data(url, port, request)
        
        tasks = [
            fetch('example.com', 80),
            fetch('httpbin.org', 80),
            fetch('www.google.com', 80),
            fetch('api.github.com', 443),
            fetch('www.python.org', 80),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes
        success_count = sum(1 for r in results if isinstance(r, bytes))
        print(f"📊 Results: {success_count}/5 successful")


# ============================================================================
# EXAMPLE 8: Dynamic Proxy Management
# ============================================================================

async def example_8_dynamic_management():
    """Add/remove proxies dynamically"""
    print("\n" + "="*80)
    print("EXAMPLE 8: Dynamic Proxy Management")
    print("="*80)
    
    # Start with one proxy
    manager = EnhancedProxyManager(
        proxies={'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}
    )
    
    print(f"✅ Started with: {manager}")
    
    # Add more proxies
    manager.add_proxy({'address': '127.0.0.1', 'port': 1081, 'type': 'socks5'})
    manager.add_proxy({'address': '127.0.0.1', 'port': 8080, 'type': 'http'})
    
    print(f"✅ After adding: {manager}")
    
    # Remove a proxy
    manager.remove_proxy('127.0.0.1', 1081)
    
    print(f"✅ After removing: {manager}")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"📊 Proxy count: {len(stats)}")


# ============================================================================
# EXAMPLE 9: HTTP Request Helper
# ============================================================================

async def example_9_http_helper():
    """Use the convenient HTTP request helper"""
    print("\n" + "="*80)
    print("EXAMPLE 9: HTTP Request Helper")
    print("="*80)
    
    proxies = [{'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}]
    
    async with EnhancedProxyManager(proxies=proxies) as manager:
        # Simple GET request
        response = await manager.send_http_request(
            target_host='httpbin.org',
            method='GET',
            path='/get?param=value',
            headers={
                'User-Agent': 'PyRoxi/1.0',
                'Accept': 'application/json'
            }
        )
        
        print(f"✅ GET response: {len(response)} bytes")
        
        # POST request with body
        response = await manager.send_http_request(
            target_host='httpbin.org',
            method='POST',
            path='/post',
            headers={'Content-Type': 'application/json'},
            body=b'{"key": "value"}'
        )
        
        print(f"✅ POST response: {len(response)} bytes")


# ============================================================================
# EXAMPLE 10: Error Handling
# ============================================================================

async def example_10_error_handling():
    """Proper error handling"""
    print("\n" + "="*80)
    print("EXAMPLE 10: Error Handling")
    print("="*80)
    
    proxies = [{'address': 'invalid.proxy', 'port': 9999, 'type': 'socks5'}]
    
    async with EnhancedProxyManager(
        proxies=proxies,
        enable_failover=False,
        max_retries=1
    ) as manager:
        try:
            request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
            await manager.send_tcp_data('example.com', 80, request)
        
        except ProxyConnectionError as e:
            print(f"❌ Connection error (expected): {e}")
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        finally:
            print("✅ Cleanup completed")


# ============================================================================
# Main Runner
# ============================================================================

async def main():
    """Run all examples"""
    print("\n" + "🚀"*40)
    print("PyRoxi Usage Examples - Single & Multi-Proxy")
    print("🚀"*40)
    
    examples = [
        ("Single Proxy Dict", example_1_single_proxy_dict),
        ("Single Connection", example_2_single_connection),
        ("Multi-Proxy List", example_3_multi_proxy_list),
        ("Multi-Proxy Config", example_4_multi_proxy_config),
        ("Selection Strategies", example_5_selection_strategies),
        ("Failover", example_6_failover),
        ("Concurrent Requests", example_7_concurrent),
        ("Dynamic Management", example_8_dynamic_management),
        ("HTTP Helper", example_9_http_helper),
        ("Error Handling", example_10_error_handling),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print("  0. Run all examples")
    
    try:
        choice = input("\nSelect example (0-10, or Enter for all): ").strip()
        choice = int(choice) if choice else 0
        
        if choice == 0:
            for name, func in examples:
                print(f"\n{'='*80}")
                print(f"Running: {name}")
                print(f"{'='*80}")
                try:
                    await func()
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"❌ Example failed: {e}")
                    import traceback
                    traceback.print_exc()
        
        elif 1 <= choice <= len(examples):
            await examples[choice - 1][1]()
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
