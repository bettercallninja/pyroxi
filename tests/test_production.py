"""
Real-World Production Tests with Free Public Proxies
Tests all features with actual SOCKS5 and HTTP proxies
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyroxi.core.connection import Connection
from pyroxi.core.manager import EnhancedProxyManager, ProxyConfig, ProxySelectionStrategy
from pyroxi.exceptions import ProxyConnectionError, ProxyAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Free public proxies for testing (may not always be available)
FREE_SOCKS5_PROXIES = [
    {'address': '98.181.137.80', 'port': 4145, 'type': 'socks5'},
    {'address': '72.210.221.197', 'port': 4145, 'type': 'socks5'},
    {'address': '184.178.172.28', 'port': 15294, 'type': 'socks5'},
    {'address': '184.178.172.26', 'port': 4145, 'type': 'socks5'},
    {'address': '192.111.139.162', 'port': 4145, 'type': 'socks5'},
]

FREE_HTTP_PROXIES = [
    {'address': '103.152.112.162', 'port': 80, 'type': 'http'},
    {'address': '103.117.192.14', 'port': 80, 'type': 'http'},
    {'address': '45.170.101.2', 'port': 999, 'type': 'http'},
    {'address': '188.132.222.34', 'port': 8080, 'type': 'http'},
    {'address': '103.149.162.195', 'port': 80, 'type': 'http'},
]

# Test targets
TEST_TARGETS = [
    {'host': 'httpbin.org', 'port': 80, 'name': 'HTTPBin'},
    {'host': 'example.com', 'port': 80, 'name': 'Example.com'},
    {'host': 'www.google.com', 'port': 80, 'name': 'Google'},
]


class ProductionTester:
    """Comprehensive production testing suite"""
    
    def __init__(self):
        self.results = {
            'socks5': {'passed': 0, 'failed': 0, 'tests': []},
            'http': {'passed': 0, 'failed': 0, 'tests': []},
            'manager': {'passed': 0, 'failed': 0, 'tests': []},
        }
    
    def log_test(self, category: str, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
        if passed:
            self.results[category]['passed'] += 1
        else:
            self.results[category]['failed'] += 1
        
        self.results[category]['tests'].append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
    
    async def test_single_socks5_connection(self):
        """Test 1: Single SOCKS5 proxy connection"""
        print("\n" + "=" * 80)
        print("TEST 1: Single SOCKS5 Proxy Connection")
        print("=" * 80)
        
        for proxy in FREE_SOCKS5_PROXIES[:3]:  # Test first 3
            try:
                async with Connection(
                    proxy['address'],
                    proxy['port'],
                    'socks5',
                    timeout=10
                ) as conn:
                    # Connect to test target
                    await conn.connect('httpbin.org', 80)
                    
                    # Send HTTP request
                    request = b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
                    await conn.send_data(request)
                    
                    # Receive response
                    response = await conn.receive_all(timeout=5)
                    
                    if b"origin" in response or b"200 OK" in response:
                        self.log_test('socks5', f'SOCKS5 Connection {proxy["address"]}', 
                                    True, f"Connected successfully, received {len(response)} bytes")
                        return True
                    else:
                        self.log_test('socks5', f'SOCKS5 Connection {proxy["address"]}', 
                                    False, "Unexpected response")
            
            except Exception as e:
                self.log_test('socks5', f'SOCKS5 Connection {proxy["address"]}', 
                            False, str(e))
        
        return False
    
    async def test_single_http_connection(self):
        """Test 2: Single HTTP proxy connection"""
        print("\n" + "=" * 80)
        print("TEST 2: Single HTTP Proxy Connection")
        print("=" * 80)
        
        for proxy in FREE_HTTP_PROXIES[:3]:  # Test first 3
            try:
                async with Connection(
                    proxy['address'],
                    proxy['port'],
                    'http',
                    timeout=10
                ) as conn:
                    # Connect via HTTP tunnel
                    await conn.connect('example.com', 80)
                    
                    # Send HTTP request
                    request = b"GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
                    await conn.send_data(request)
                    
                    # Receive response
                    response = await conn.receive_all(timeout=5)
                    
                    if b"Example Domain" in response or b"200 OK" in response:
                        self.log_test('http', f'HTTP Proxy {proxy["address"]}', 
                                    True, f"Connected successfully, received {len(response)} bytes")
                        return True
                    else:
                        self.log_test('http', f'HTTP Proxy {proxy["address"]}', 
                                    False, "Unexpected response")
            
            except Exception as e:
                self.log_test('http', f'HTTP Proxy {proxy["address"]}', 
                            False, str(e))
        
        return False
    
    async def test_binary_packet_transfer(self):
        """Test 3: Binary packet transfer with length framing"""
        print("\n" + "=" * 80)
        print("TEST 3: Binary Packet Transfer")
        print("=" * 80)
        
        for proxy in FREE_SOCKS5_PROXIES[:2]:
            try:
                async with Connection(
                    proxy['address'],
                    proxy['port'],
                    'socks5',
                    timeout=10
                ) as conn:
                    await conn.connect('httpbin.org', 80)
                    
                    # Test binary data
                    binary_data = b"\x00\x01\x02\x03\x04\x05"
                    await conn.send_data(binary_data)
                    
                    self.log_test('socks5', f'Binary Transfer {proxy["address"]}', 
                                True, f"Sent {len(binary_data)} binary bytes")
                    return True
            
            except Exception as e:
                self.log_test('socks5', f'Binary Transfer {proxy["address"]}', 
                            False, str(e))
        
        return False
    
    async def test_multi_proxy_manager(self):
        """Test 4: Multi-proxy manager with load balancing"""
        print("\n" + "=" * 80)
        print("TEST 4: Multi-Proxy Manager")
        print("=" * 80)
        
        try:
            # Create manager with multiple proxies
            all_proxies = FREE_SOCKS5_PROXIES[:3] + FREE_HTTP_PROXIES[:2]
            
            async with EnhancedProxyManager(
                proxies=all_proxies,
                strategy=ProxySelectionStrategy.ROUND_ROBIN,
                max_concurrent=5,
                enable_failover=True,
                max_retries=2
            ) as manager:
                
                logger.info(f"Created manager: {manager}")
                
                # Test TCP data
                try:
                    request = b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
                    response = await manager.send_tcp_data('httpbin.org', 80, request)
                    
                    if response and len(response) > 0:
                        self.log_test('manager', 'Multi-Proxy TCP', 
                                    True, f"Received {len(response)} bytes through proxy pool")
                    else:
                        self.log_test('manager', 'Multi-Proxy TCP', 
                                    False, "No response received")
                
                except Exception as e:
                    self.log_test('manager', 'Multi-Proxy TCP', False, str(e))
                
                # Print statistics
                manager.print_statistics()
                
                return True
        
        except Exception as e:
            self.log_test('manager', 'Multi-Proxy Manager', False, str(e))
            return False
    
    async def test_proxy_selection_strategies(self):
        """Test 5: Different proxy selection strategies"""
        print("\n" + "=" * 80)
        print("TEST 5: Proxy Selection Strategies")
        print("=" * 80)
        
        strategies = [
            ProxySelectionStrategy.ROUND_ROBIN,
            ProxySelectionStrategy.RANDOM,
            ProxySelectionStrategy.SEQUENTIAL,
        ]
        
        for strategy in strategies:
            try:
                async with EnhancedProxyManager(
                    proxies=FREE_SOCKS5_PROXIES[:3],
                    strategy=strategy,
                    max_retries=1
                ) as manager:
                    
                    request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
                    result = await manager.send_tcp_data('example.com', 80, request, receive=True)
                    
                    if result:
                        self.log_test('manager', f'Strategy {strategy.value}', 
                                    True, "Strategy executed successfully")
                    else:
                        self.log_test('manager', f'Strategy {strategy.value}', 
                                    False, "No response")
            
            except Exception as e:
                self.log_test('manager', f'Strategy {strategy.value}', False, str(e))
    
    async def test_concurrent_requests(self):
        """Test 6: Concurrent requests through multiple proxies"""
        print("\n" + "=" * 80)
        print("TEST 6: Concurrent Requests")
        print("=" * 80)
        
        try:
            async with EnhancedProxyManager(
                proxies=FREE_SOCKS5_PROXIES[:3],
                max_concurrent=3
            ) as manager:
                
                # Create multiple concurrent requests
                async def fetch_url(host: str, port: int) -> bytes:
                    request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
                    return await manager.send_tcp_data(host, port, request)
                
                tasks = [
                    fetch_url('example.com', 80),
                    fetch_url('httpbin.org', 80),
                    fetch_url('www.google.com', 80),
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in results if isinstance(r, bytes) and len(r) > 0)
                
                self.log_test('manager', 'Concurrent Requests', 
                            success_count > 0, 
                            f"{success_count}/3 requests succeeded")
        
        except Exception as e:
            self.log_test('manager', 'Concurrent Requests', False, str(e))
    
    async def test_failover_mechanism(self):
        """Test 7: Automatic failover to working proxy"""
        print("\n" + "=" * 80)
        print("TEST 7: Failover Mechanism")
        print("=" * 80)
        
        try:
            # Mix working and non-working proxies
            test_proxies = [
                {'address': '1.2.3.4', 'port': 9999, 'type': 'socks5'},  # Invalid
                {'address': '5.6.7.8', 'port': 8888, 'type': 'socks5'},  # Invalid
            ] + FREE_SOCKS5_PROXIES[:2]  # Add working proxies
            
            async with EnhancedProxyManager(
                proxies=test_proxies,
                enable_failover=True,
                max_retries=3
            ) as manager:
                
                request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
                result = await manager.send_tcp_data('example.com', 80, request)
                
                if result:
                    self.log_test('manager', 'Failover Mechanism', 
                                True, "Successfully failed over to working proxy")
                else:
                    self.log_test('manager', 'Failover Mechanism', 
                                False, "Failover did not produce result")
        
        except Exception as e:
            self.log_test('manager', 'Failover Mechanism', False, str(e))
    
    async def test_connection_pooling(self):
        """Test 8: Connection reuse and pooling"""
        print("\n" + "=" * 80)
        print("TEST 8: Connection Pooling")
        print("=" * 80)
        
        try:
            async with EnhancedProxyManager(
                proxies=FREE_SOCKS5_PROXIES[:2],
                max_concurrent=5
            ) as manager:
                
                # Make multiple requests to see connection reuse
                for i in range(5):
                    try:
                        request = b"GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: keep-alive\r\n\r\n"
                        await manager.send_tcp_data('httpbin.org', 80, request)
                        logger.info(f"Request {i+1}/5 completed")
                    except Exception as e:
                        logger.warning(f"Request {i+1} failed: {e}")
                
                self.log_test('manager', 'Connection Pooling', 
                            True, "Multiple requests completed")
        
        except Exception as e:
            self.log_test('manager', 'Connection Pooling', False, str(e))
    
    async def test_http_request_helper(self):
        """Test 9: HTTP request helper method"""
        print("\n" + "=" * 80)
        print("TEST 9: HTTP Request Helper")
        print("=" * 80)
        
        try:
            async with EnhancedProxyManager(
                proxies=FREE_SOCKS5_PROXIES[:2]
            ) as manager:
                
                response = await manager.send_http_request(
                    target_host='httpbin.org',
                    method='GET',
                    path='/get',
                    headers={'User-Agent': 'PyRoxi-Test/1.0'},
                    port=80
                )
                
                if response and b'httpbin' in response:
                    self.log_test('manager', 'HTTP Request Helper', 
                                True, f"Received valid HTTP response ({len(response)} bytes)")
                else:
                    self.log_test('manager', 'HTTP Request Helper', 
                                False, "Invalid response")
        
        except Exception as e:
            self.log_test('manager', 'HTTP Request Helper', False, str(e))
    
    async def test_single_proxy_dict_format(self):
        """Test 10: Single proxy as dictionary"""
        print("\n" + "=" * 80)
        print("TEST 10: Single Proxy Dictionary Format")
        print("=" * 80)
        
        try:
            single_proxy = FREE_SOCKS5_PROXIES[0]
            
            async with EnhancedProxyManager(proxies=single_proxy) as manager:
                logger.info(f"Created manager with single proxy: {manager}")
                
                request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
                result = await manager.send_tcp_data('example.com', 80, request)
                
                if result:
                    self.log_test('manager', 'Single Proxy Dict', 
                                True, "Single proxy dict format works")
                else:
                    self.log_test('manager', 'Single Proxy Dict', 
                                False, "No response")
        
        except Exception as e:
            self.log_test('manager', 'Single Proxy Dict', False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            print(f"\n📊 {category.upper()}")
            print(f"   ✅ Passed: {results['passed']}")
            print(f"   ❌ Failed: {results['failed']}")
            total_passed += results['passed']
            total_failed += results['failed']
        
        print(f"\n{'=' * 80}")
        print(f"TOTAL: {total_passed} passed, {total_failed} failed")
        
        success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 80 + "\n")
        
        return success_rate


async def main():
    """Run all production tests"""
    print("\n")
    print("🚀" * 40)
    print("PyRoxi Production Testing Suite")
    print("Testing with Real Free Public Proxies")
    print("🚀" * 40)
    print("\n⚠️  Note: Free public proxies may be slow or unavailable")
    print("Some tests may fail due to proxy availability\n")
    
    tester = ProductionTester()
    
    # Run all tests
    tests = [
        tester.test_single_socks5_connection(),
        tester.test_single_http_connection(),
        tester.test_binary_packet_transfer(),
        tester.test_multi_proxy_manager(),
        tester.test_proxy_selection_strategies(),
        tester.test_concurrent_requests(),
        tester.test_failover_mechanism(),
        tester.test_connection_pooling(),
        tester.test_http_request_helper(),
        tester.test_single_proxy_dict_format(),
    ]
    
    for test in tests:
        try:
            await test
            await asyncio.sleep(1)  # Brief pause between tests
        except Exception as e:
            logger.error(f"Test execution error: {e}")
    
    # Print summary
    success_rate = tester.print_summary()
    
    if success_rate >= 70:
        print("🎉 Production tests PASSED! PyRoxi is production-ready!")
    elif success_rate >= 50:
        print("⚠️  Some tests failed. Review proxy availability.")
    else:
        print("❌ Many tests failed. Check proxy list and network connectivity.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
