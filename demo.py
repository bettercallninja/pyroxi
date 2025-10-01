"""
Pyroxy Library Demo - Complete Feature Showcase

This script demonstrates all the key features of the Pyroxy library
in a practical, working example.
"""

import asyncio
import json
import sys
import os

# Add current directory to path for import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from pyroxy import (
    ProxyManager, 
    AsyncHTTPClient, 
    PacketBuilder, 
    PacketParser,
    AdvancedPacketBuilder
)
from pyroxy.exceptions import ProxyConnectionError


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


async def demo_packet_building():
    """Demonstrate packet building capabilities"""
    print_section("PACKET BUILDING DEMO")
    
    # Basic packet builder
    builder = PacketBuilder()
    
    # Build different types of packets
    print("1. Building HTTP GET packet:")
    http_packet = builder.build_http_packet(
        method='GET',
        path='/api/users',
        headers={
            'Host': 'api.example.com',
            'User-Agent': 'Pyroxy/1.0',
            'Accept': 'application/json'
        }
    )
    print(f"   Packet size: {len(http_packet)} bytes")
    print(f"   First 100 chars: {http_packet[:100].decode('utf-8')}")
    
    print("\n2. Building TCP packet:")
    tcp_packet = builder.build_tcp_packet("Hello Server!")
    print(f"   TCP data: {tcp_packet}")
    
    print("\n3. Building JSON packet:")
    json_data = {'user': 'john', 'action': 'login', 'timestamp': 1234567890}
    json_packet = builder.build_json_packet(json_data)
    print(f"   JSON packet: {json_packet.decode('utf-8')}")
    
    # Advanced packet builder
    print("\n4. Advanced packet building:")
    advanced_builder = AdvancedPacketBuilder()
    
    # WebSocket frame
    ws_frame = advanced_builder.build_websocket_frame("Hello WebSocket!")
    print(f"   WebSocket frame: {ws_frame.hex()[:40]}...")
    
    # SOCKS5 auth packet
    socks_auth = advanced_builder.build_socks5_auth_packet("user", "pass")
    print(f"   SOCKS5 auth: {socks_auth.hex()}")


async def demo_packet_parsing():
    """Demonstrate packet parsing capabilities"""
    print_section("PACKET PARSING DEMO")
    
    parser = PacketParser()
    
    print("1. Parsing HTTP response:")
    http_response = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 25\r\n\r\n{\"status\": \"success\"}"
    parsed_http = parser.parse_http_response(http_response)
    print(f"   Status: {parsed_http['status_code']}")
    print(f"   Headers: {len(parsed_http['headers'])} headers")
    print(f"   Body: {parsed_http['body']}")
    
    print("\n2. Parsing HTTP request:")
    http_request = b"POST /login HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json\r\n\r\n{\"user\":\"john\"}"
    parsed_request = parser.parse_http_request(http_request)
    print(f"   Method: {parsed_request['method']}")
    print(f"   Path: {parsed_request['path']}")
    print(f"   Host: {parsed_request['headers'].get('Host')}")
    
    print("\n3. Auto-parsing different packet types:")
    test_packets = [
        b"HTTP/1.1 404 Not Found\r\n\r\n",
        b'{"message": "auto-detected JSON"}',
        b"GET /test HTTP/1.1\r\n\r\n",
        b"Raw binary data"
    ]
    
    for i, packet in enumerate(test_packets, 1):
        parsed = parser.auto_parse(packet)
        packet_type = parsed.get('type', 'HTTP response' if 'status_code' in parsed else 'HTTP request' if 'method' in parsed else 'unknown')
        print(f"   Packet {i}: {packet_type}")


async def demo_proxy_management():
    """Demonstrate proxy management without actual connections"""
    print_section("PROXY MANAGEMENT DEMO")
    
    # Define example proxy configurations
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http',
            'username': None,
            'password': None
        },
        {
            'address': '127.0.0.1',
            'port': 1080,
            'type': 'socks5',
            'username': 'user',
            'password': 'pass'
        },
        {
            'address': '10.0.0.1',
            'port': 3128,
            'type': 'http',
            'username': 'admin',
            'password': 'secret'
        }
    ]
    
    print(f"1. Configuring {len(proxies)} proxy servers:")
    for i, proxy in enumerate(proxies, 1):
        auth_info = "with auth" if proxy.get('username') else "no auth"
        print(f"   Proxy {i}: {proxy['type'].upper()} {proxy['address']}:{proxy['port']} ({auth_info})")
    
    # Create proxy manager
    proxy_manager = ProxyManager(proxies, max_concurrent=5)
    print(f"\n2. Created ProxyManager with max {proxy_manager.max_concurrent} concurrent connections")
    
    # Test proxy selection
    print("\n3. Proxy selection examples:")
    for i in range(3):
        proxy = proxy_manager._get_proxy()
        print(f"   Random proxy: {proxy['address']}:{proxy['port']} ({proxy['type']})")
    
    # Test specific proxy selection
    specific_proxy = proxy_manager._get_proxy(1)  # Second proxy
    print(f"   Specific proxy (index 1): {specific_proxy['address']}:{specific_proxy['port']}")
    
    # Test proxy URL building
    print("\n4. Proxy URL building:")
    for proxy in proxies:
        url = proxy_manager._build_proxy_url(proxy)
        print(f"   {proxy['type']} proxy URL: {url}")
    
    await proxy_manager.close()


async def demo_http_client():
    """Demonstrate HTTP client interface"""
    print_section("HTTP CLIENT DEMO")
    
    # This demo shows the interface without making real requests
    proxies = [{'address': '127.0.0.1', 'port': 8080, 'type': 'http'}]
    proxy_manager = ProxyManager(proxies)
    client = AsyncHTTPClient(proxy_manager)
    
    print("1. AsyncHTTPClient created with methods:")
    methods = ['get', 'post', 'put', 'delete']
    for method in methods:
        print(f"   - client.{method}(url, ...)")
    
    print("\n2. Example usage patterns:")
    print("   # Simple GET request")
    print("   response = await client.get('http://example.com')")
    print()
    print("   # POST with JSON data")
    print("   response = await client.post('http://api.com/users',")
    print("                                data=json.dumps({'name': 'John'}),")
    print("                                headers={'Content-Type': 'application/json'})")
    print()
    print("   # Custom headers")
    print("   response = await client.get('http://api.com/data',")
    print("                               headers={'Authorization': 'Bearer token'})")
    
    await proxy_manager.close()


async def demo_concurrent_requests():
    """Demonstrate concurrent request patterns"""
    print_section("CONCURRENT REQUESTS DEMO")
    
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
    ]
    
    proxy_manager = ProxyManager(proxies, max_concurrent=10)
    
    # Define example requests
    requests = [
        {
            'type': 'http',
            'url': 'http://example.com/api/users',
            'method': 'GET'
        },
        {
            'type': 'http',
            'url': 'http://example.com/api/posts',
            'method': 'GET'
        },
        {
            'type': 'http',
            'url': 'http://example.com/api/comments',
            'method': 'POST',
            'data': json.dumps({'text': 'Hello'}),
            'headers': {'Content-Type': 'application/json'}
        },
        {
            'type': 'tcp',
            'host': 'example.com',
            'port': 80,
            'data': b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n'
        }
    ]
    
    print(f"1. Configured {len(requests)} concurrent requests:")
    for i, req in enumerate(requests, 1):
        if req['type'] == 'http':
            print(f"   Request {i}: {req['method']} {req['url']}")
        else:
            print(f"   Request {i}: TCP to {req['host']}:{req['port']}")
    
    print(f"\n2. Requests will be distributed across {len(proxies)} proxies")
    print("3. Maximum concurrent connections: 10")
    print("4. Automatic proxy failover enabled")
    
    # Note: We don't actually send these requests in the demo
    print("\n   [Requests not sent in demo mode - use with real proxies]")
    
    await proxy_manager.close()


def demo_performance_features():
    """Demonstrate performance monitoring features"""
    print_section("PERFORMANCE FEATURES DEMO")
    
    print("1. Built-in Performance Monitoring:")
    print("   ✓ Automatic response time measurement")
    print("   ✓ Success/failure rate tracking")
    print("   ✓ Proxy health monitoring")
    print("   ✓ Concurrent connection management")
    
    print("\n2. Speed Testing Capabilities:")
    print("   # Test all proxies")
    print("   results = await proxy_manager.test_proxy_speed()")
    print("   for result in results:")
    print("       if result['status'] == 'success':")
    print("           print(f\"Proxy response time: {result['response_time']:.3f}s\")")
    
    print("\n3. Performance Metrics Available:")
    metrics = [
        "Response time (min, max, average)",
        "Success rate percentage", 
        "Request throughput (req/sec)",
        "Percentile analysis (P50, P90, P99)",
        "Error rate and failure analysis"
    ]
    for metric in metrics:
        print(f"   ✓ {metric}")
    
    print("\n4. Scalability Features:")
    features = [
        "Async/await for non-blocking I/O",
        "Configurable connection pooling",
        "Automatic proxy load balancing",
        "Graceful error handling and retry",
        "Memory-efficient packet processing"
    ]
    for feature in features:
        print(f"   ✓ {feature}")


async def main():
    """Run all demonstration modules"""
    print("🚀 PYROXY LIBRARY - COMPLETE FEATURE DEMONSTRATION")
    print("High-Performance Async Proxy Library for Python")
    
    try:
        await demo_packet_building()
        await demo_packet_parsing()
        await demo_proxy_management()
        await demo_http_client()
        await demo_concurrent_requests()
        demo_performance_features()
        
        print_section("DEMO COMPLETE")
        print("✅ All features demonstrated successfully!")
        print("\n🎯 Key Benefits:")
        print("   • High-speed async operations")
        print("   • SOCKS5 and HTTP proxy support")
        print("   • Concurrent request handling")
        print("   • Custom packet building/parsing")
        print("   • Built-in performance monitoring")
        print("   • Easy-to-use API")
        
        print("\n📚 Next Steps:")
        print("   1. Set up your proxy servers")
        print("   2. Run examples/basic_usage.py")
        print("   3. Explore examples/async_usage.py")
        print("   4. Performance test with examples/performance_test.py")
        print("   5. Read the documentation in README.md")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the complete demonstration
    asyncio.run(main())
