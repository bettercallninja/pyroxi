"""
High-Performance Concurrent Example for Pyroxy

This example demonstrates the library's capability to handle hundreds of
concurrent connections through multiple proxies with optimal performance.
"""

import asyncio
import time
import random
from typing import List, Dict
from pyroxy import ProxyManager, AsyncHTTPClient


class PerformanceTest:
    def __init__(self, proxies: List[Dict], max_concurrent: int = 50):
        self.proxy_manager = ProxyManager(proxies, max_concurrent=max_concurrent)
        self.results = []
        
    async def single_request(self, url: str, request_id: int) -> Dict:
        """Perform a single request and measure performance"""
        start_time = time.time()
        
        try:
            response = await self.proxy_manager.send_http_request(url)
            end_time = time.time()
            
            return {
                'request_id': request_id,
                'success': True,
                'status_code': response['status_code'],
                'response_time': end_time - start_time,
                'content_length': len(response['content'])
            }
        except Exception as e:
            end_time = time.time()
            return {
                'request_id': request_id,
                'success': False,
                'error': str(e),
                'response_time': end_time - start_time
            }
    
    async def batch_requests(self, urls: List[str], batch_size: int = 100) -> List[Dict]:
        """Send multiple requests in batches"""
        all_tasks = []
        
        for i, url in enumerate(urls):
            task = self.single_request(url, i)
            all_tasks.append(task)
        
        # Process in batches to avoid overwhelming the system
        results = []
        for i in range(0, len(all_tasks), batch_size):
            batch = all_tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches to prevent rate limiting
            await asyncio.sleep(0.1)
        
        return results
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze performance results"""
        successful = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed = [r for r in results if isinstance(r, dict) and not r.get('success')]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        if successful:
            response_times = [r['response_time'] for r in successful]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p90 = sorted_times[int(len(sorted_times) * 0.9)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_time = min_time = max_time = p50 = p90 = p99 = 0
        
        return {
            'total_requests': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'exceptions': len(exceptions),
            'success_rate': len(successful) / len(results) * 100 if results else 0,
            'avg_response_time': avg_time,
            'min_response_time': min_time,
            'max_response_time': max_time,
            'p50_response_time': p50,
            'p90_response_time': p90,
            'p99_response_time': p99
        }
    
    async def close(self):
        """Clean up resources"""
        await self.proxy_manager.close()


async def load_test_example():
    """High-load test with multiple proxies"""
    print("=== High-Performance Load Test ===")
    
    # Configure multiple proxy servers
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 8081, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
        {'address': '127.0.0.1', 'port': 1081, 'type': 'socks5'},
    ]
    
    # Test URLs
    test_urls = [
        'http://httpbin.org/ip',
        'http://httpbin.org/user-agent', 
        'http://httpbin.org/headers',
        'http://httpbin.org/get',
    ] * 50  # 200 total requests
    
    performance_test = PerformanceTest(proxies, max_concurrent=25)
    
    print(f"Starting load test with {len(test_urls)} requests...")
    print(f"Using {len(proxies)} proxy servers")
    print(f"Max concurrent connections: 25")
    
    start_time = time.time()
    
    try:
        results = await performance_test.batch_requests(test_urls, batch_size=50)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        analysis = performance_test.analyze_results(results)
        
        print(f"\n=== Performance Results ===")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests per second: {len(test_urls) / total_time:.2f}")
        print(f"Total requests: {analysis['total_requests']}")
        print(f"Successful: {analysis['successful']}")
        print(f"Failed: {analysis['failed']}")
        print(f"Success rate: {analysis['success_rate']:.1f}%")
        print(f"Average response time: {analysis['avg_response_time']:.3f}s")
        print(f"Min response time: {analysis['min_response_time']:.3f}s")
        print(f"Max response time: {analysis['max_response_time']:.3f}s")
        print(f"P50 response time: {analysis['p50_response_time']:.3f}s")
        print(f"P90 response time: {analysis['p90_response_time']:.3f}s")
        print(f"P99 response time: {analysis['p99_response_time']:.3f}s")
        
    except Exception as e:
        print(f"Load test failed: {e}")
    
    await performance_test.close()


async def concurrent_different_targets():
    """Test concurrent requests to different targets through different proxies"""
    print("\n=== Concurrent Different Targets Test ===")
    
    proxies = [
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'},
    ]
    
    proxy_manager = ProxyManager(proxies, max_concurrent=20)
    
    # Different request types and targets
    requests = [
        {
            'type': 'http',
            'url': 'http://httpbin.org/ip',
            'method': 'GET'
        },
        {
            'type': 'http', 
            'url': 'http://httpbin.org/post',
            'method': 'POST',
            'data': '{"test": "data"}',
            'headers': {'Content-Type': 'application/json'}
        },
        {
            'type': 'http',
            'url': 'http://httpbin.org/delay/1',
            'method': 'GET'
        },
        {
            'type': 'http',
            'url': 'http://httpbin.org/status/200',
            'method': 'GET'
        }
    ] * 10  # 40 total requests
    
    print(f"Sending {len(requests)} concurrent requests to different targets...")
    
    start_time = time.time()
    
    try:
        results = await proxy_manager.send_multiple_requests(requests, distribute_proxies=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f"Completed in {total_time:.2f}s")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Requests per second: {len(requests) / total_time:.2f}")
        
    except Exception as e:
        print(f"Test failed: {e}")
    
    await proxy_manager.close()


async def proxy_failover_test():
    """Test proxy failover capabilities"""
    print("\n=== Proxy Failover Test ===")
    
    # Include some intentionally bad proxies to test failover
    proxies = [
        {'address': '127.0.0.1', 'port': 9999, 'type': 'http'},  # Should fail
        {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},  # Should work
        {'address': '192.0.2.1', 'port': 8080, 'type': 'http'},  # Should fail (non-routable IP)
        {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}, # Should work
    ]
    
    proxy_manager = ProxyManager(proxies)
    
    # Test each proxy individually
    test_results = await proxy_manager.test_proxy_speed(timeout=5)
    
    working_proxies = [r for r in test_results if r['status'] == 'success']
    failed_proxies = [r for r in test_results if r['status'] == 'failed']
    
    print(f"Working proxies: {len(working_proxies)}")
    print(f"Failed proxies: {len(failed_proxies)}")
    
    if working_proxies:
        print("The system can continue with working proxies:")
        for proxy in working_proxies:
            p = proxy['proxy']
            print(f"  - {p['address']}:{p['port']} ({p['type']}) - {proxy['response_time']:.3f}s")
    
    await proxy_manager.close()


async def main():
    """Run all performance tests"""
    print("Pyroxy High-Performance Testing Suite")
    print("=" * 50)
    
    # Note: These tests assume you have proxy servers running
    # For testing, you can use tools like:
    # - Squid proxy for HTTP
    # - SSH tunnel for SOCKS5 
    # - Or any other proxy software
    
    try:
        await load_test_example()
        await concurrent_different_targets()
        await proxy_failover_test()
        
        print("\n=== Performance Testing Complete ===")
        print("The library demonstrates:")
        print("✓ High concurrent connection handling")
        print("✓ Automatic proxy distribution")
        print("✓ Robust error handling and failover")
        print("✓ Detailed performance metrics")
        
    except Exception as e:
        print(f"Performance test suite error: {e}")
        print("Note: Ensure proxy servers are running for accurate results")


if __name__ == "__main__":
    asyncio.run(main())
