"""
Basic Usage Example for Pyroxy - Simple sync-style interface

This script demonstrates basic usage patterns for the pyroxy library.
For advanced async features, see async_usage.py
"""

import asyncio
from pyroxy import ProxyManager, AsyncHTTPClient


def simple_example():
    """Simple synchronous-style example using asyncio.run()"""
    print("=== Simple Proxy Usage ===")
    
    # Define your proxies
    proxies = [
        {
            'address': '127.0.0.1',
            'port': 8080,
            'type': 'http'  # or 'socks5'
        }
    ]
    
    async def make_request():
        # Create proxy manager
        proxy_manager = ProxyManager(proxies)
        
        try:
            # Send HTTP request through proxy
            response = await proxy_manager.send_http_request(
                'http://httpbin.org/ip',
                method='GET'
            )
            
            print(f"Status: {response['status_code']}")
            print(f"Your IP through proxy: {response['text']}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await proxy_manager.close()
    
    # Run the async function
    asyncio.run(make_request())


def multiple_requests_example():
    """Example with multiple concurrent requests"""
    print("\n=== Multiple Requests Example ===")
    
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
    ]
    
    async def make_multiple_requests():
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
                'method': 'GET'
            },
            {
                'type': 'http',
                'url': 'http://httpbin.org/headers',
                'method': 'GET'
            }
        ]
        
        try:
            # Send all requests concurrently
            results = await proxy_manager.send_multiple_requests(requests)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Request {i} failed: {result}")
                else:
                    print(f"Request {i} successful: Status {result['status_code']}")
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await proxy_manager.close()
    
    asyncio.run(make_multiple_requests())


def http_client_example():
    """Example using the simplified HTTP client interface"""
    print("\n=== HTTP Client Example ===")
    
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'}
    ]
    
    async def use_http_client():
        proxy_manager = ProxyManager(proxies)
        client = AsyncHTTPClient(proxy_manager)
        
        try:
            # Simple GET request
            response = await client.get('http://httpbin.org/get')
            print(f"GET request status: {response['status_code']}")
            
            # POST request with JSON data
            import json
            post_data = {'message': 'Hello from Pyroxy!'}
            response = await client.post(
                'http://httpbin.org/post',
                data=json.dumps(post_data),
                headers={'Content-Type': 'application/json'}
            )
            print(f"POST request status: {response['status_code']}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await proxy_manager.close()
    
    asyncio.run(use_http_client())


def main():
    """Run all basic examples"""
    print("Pyroxy Basic Usage Examples")
    print("=" * 30)
    
    # Note: These examples assume you have proxy servers running locally
    # You can test with your own proxies or set up test proxies
    
    simple_example()
    multiple_requests_example()
    http_client_example()
    
    print("\n=== Examples Complete ===")
    print("For more advanced features, check out:")
    print("- async_usage.py - Full async capabilities")
    print("- performance_test.py - High-performance testing")


if __name__ == "__main__":
    main()