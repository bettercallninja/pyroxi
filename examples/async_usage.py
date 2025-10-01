"""
Advanced Async Usage Examples for Pyroxy

This script demonstrates the powerful async capabilities of the pyroxy library,
including SOCKS5/HTTP proxy support, concurrent requests, and custom packet handling.
"""

import asyncio
import json
from pyroxy import ProxyManager, AsyncHTTPClient, PacketBuilder, PacketParser


async def basic_proxy_example():
    """Basic example of using a single proxy"""
    print("=== Basic Proxy Example ===")
    
    # Define proxy configuration
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http',
            'username': None,
            'password': None
        }
    ]
    
    # Create proxy manager
    proxy_manager = ProxyManager(proxies)
    
    try:
        # Send HTTP request through proxy
        response = await proxy_manager.send_http_request(
            'http://httpbin.org/ip',
            method='GET'
        )
        
        print(f"Status Code: {response['status_code']}")
        print(f"Response: {response['text']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    await proxy_manager.close()


async def multiple_proxies_example():
    """Example using multiple proxies for concurrent requests"""
    print("\n=== Multiple Proxies Example ===")
    
    # Define multiple proxy configurations
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http'
        },
        {
            'address': '127.0.0.1', 
            'port': 1080,
            'type': 'socks5'
        },
        {
            'address': '127.0.0.1',
            'port': 8888,
            'type': 'http',
            'username': 'user',
            'password': 'pass'
        }
    ]
    
    proxy_manager = ProxyManager(proxies, max_concurrent=5)
    
    # Define multiple requests
    requests = [
        {
            'type': 'http',
            'url': 'http://httpbin.org/ip',
            'method': 'GET'
        },
        {
            'type': 'http',
            'url': 'http://httpbin.org/user-agent',
            'method': 'GET',
            'headers': {'User-Agent': 'Pyroxy/1.0'}
        },
        {
            'type': 'http',
            'url': 'http://httpbin.org/post',
            'method': 'POST',
            'data': json.dumps({'test': 'data'}),
            'headers': {'Content-Type': 'application/json'}
        }
    ]
    
    try:
        # Send all requests concurrently through different proxies
        results = await proxy_manager.send_multiple_requests(requests)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Request {i} failed: {result}")
            else:
                print(f"Request {i} success: Status {result['status_code']}")
                
    except Exception as e:
        print(f"Error: {e}")
    
    await proxy_manager.close()


async def tcp_packet_example():
    """Example of sending custom TCP packets through proxy"""
    print("\n=== TCP Packet Example ===")
    
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 1080,
            'type': 'socks5'
        }
    ]
    
    proxy_manager = ProxyManager(proxies)
    packet_builder = PacketBuilder()
    
    try:
        # Build custom TCP packet
        custom_data = packet_builder.build_tcp_packet("Hello, Server!")
        
        # Send through SOCKS5 proxy to target server
        response = await proxy_manager.send_tcp_packet(
            target_host='example.com',
            target_port=80,
            data=custom_data
        )
        
        # Parse response
        parser = PacketParser()
        parsed_response = parser.auto_parse(response)
        
        print(f"Response type: {parsed_response.get('type', 'unknown')}")
        print(f"Response data: {parsed_response.get('text', 'N/A')[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")
    
    await proxy_manager.close()


async def http_client_example():
    """Example using the simplified AsyncHTTPClient"""
    print("\n=== Async HTTP Client Example ===")
    
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http'
        }
    ]
    
    proxy_manager = ProxyManager(proxies)
    client = AsyncHTTPClient(proxy_manager)
    
    try:
        # Simple GET request
        response = await client.get('http://httpbin.org/get')
        print(f"GET Response: {response['status_code']}")
        
        # POST request with data
        post_data = {'key': 'value', 'test': True}
        response = await client.post(
            'http://httpbin.org/post',
            data=json.dumps(post_data),
            headers={'Content-Type': 'application/json'}
        )
        print(f"POST Response: {response['status_code']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    await proxy_manager.close()


async def proxy_speed_test():
    """Test the speed and functionality of all proxies"""
    print("\n=== Proxy Speed Test ===")
    
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http'
        },
        {
            'address': '127.0.0.1',
            'port': 1080, 
            'type': 'socks5'
        }
    ]
    
    proxy_manager = ProxyManager(proxies)
    
    try:
        results = await proxy_manager.test_proxy_speed(
            test_url='http://httpbin.org/ip',
            timeout=10
        )
        
        print("Proxy Speed Test Results:")
        for result in results:
            proxy_info = result['proxy']
            status = result['status']
            response_time = result.get('response_time')
            
            print(f"Proxy {proxy_info['address']}:{proxy_info['port']} ({proxy_info['type']})")
            print(f"  Status: {status}")
            if response_time:
                print(f"  Response time: {response_time:.3f}s")
            if status == 'failed':
                print(f"  Error: {result.get('error', 'Unknown')}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
    
    await proxy_manager.close()


async def advanced_packet_building():
    """Example of advanced packet building capabilities"""
    print("\n=== Advanced Packet Building ===")
    
    from pyroxy.packet.builder import AdvancedPacketBuilder
    
    builder = AdvancedPacketBuilder()
    
    # Build HTTP packet
    http_packet = builder.build_http_packet(
        method='GET',
        path='/api/data',
        headers={
            'Host': 'api.example.com',
            'User-Agent': 'Pyroxy/1.0',
            'Accept': 'application/json'
        }
    )
    
    print("HTTP Packet:")
    print(http_packet.decode('utf-8'))
    
    # Build SOCKS5 authentication packet
    socks5_auth = builder.build_socks5_auth_packet('username', 'password')
    print(f"\nSOCKS5 Auth Packet: {socks5_auth.hex()}")
    
    # Build WebSocket frame
    ws_frame = builder.build_websocket_frame('Hello WebSocket!', opcode=1)
    print(f"WebSocket Frame: {ws_frame.hex()}")


async def main():
    """Run all examples"""
    print("Pyroxy Async Library Examples")
    print("=" * 40)
    
    # Note: These examples assume you have proxy servers running locally
    # You may need to start test proxies or modify the addresses/ports
    
    try:
        await basic_proxy_example()
        await multiple_proxies_example() 
        await tcp_packet_example()
        await http_client_example()
        await proxy_speed_test()
        await advanced_packet_building()
        
    except Exception as e:
        print(f"Example execution error: {e}")
        print("Note: Make sure you have proxy servers running for these examples")


if __name__ == "__main__":
    # Run the async examples
    asyncio.run(main())
