"""
Test the basic functionality of the pyroxy library
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pyroxy import ProxyManager, AsyncHTTPClient, PacketBuilder, PacketParser
from pyroxy.exceptions import ProxyConnectionError


class TestProxyManager:
    def test_proxy_manager_init(self):
        """Test ProxyManager initialization"""
        proxies = [
            {'address': '127.0.0.1', 'port': 8080, 'type': 'http'}
        ]
        manager = ProxyManager(proxies, max_concurrent=5)
        
        assert manager.proxies == proxies
        assert manager.max_concurrent == 5
        assert manager.semaphore._value == 5

    def test_get_proxy(self):
        """Test proxy selection"""
        proxies = [
            {'address': '127.0.0.1', 'port': 8080, 'type': 'http'},
            {'address': '127.0.0.1', 'port': 1080, 'type': 'socks5'}
        ]
        manager = ProxyManager(proxies)
        
        # Test specific index
        proxy = manager._get_proxy(0)
        assert proxy == proxies[0]
        
        # Test random selection
        proxy = manager._get_proxy()
        assert proxy in proxies

    def test_build_proxy_url(self):
        """Test proxy URL building"""
        manager = ProxyManager([])
        
        # Without auth
        proxy = {'address': '127.0.0.1', 'port': 8080, 'type': 'http'}
        url = manager._build_proxy_url(proxy)
        assert url == 'http://127.0.0.1:8080'
        
        # With auth
        proxy = {
            'address': '127.0.0.1', 
            'port': 8080, 
            'type': 'http',
            'username': 'user',
            'password': 'pass'
        }
        url = manager._build_proxy_url(proxy)
        assert url == 'http://user:pass@127.0.0.1:8080'


class TestPacketBuilder:
    def test_build_tcp_packet(self):
        """Test TCP packet building"""
        builder = PacketBuilder()
        
        # String input
        packet = builder.build_tcp_packet("Hello")
        assert packet == b"Hello"
        
        # Bytes input
        packet = builder.build_tcp_packet(b"Hello")
        assert packet == b"Hello"

    def test_build_http_packet(self):
        """Test HTTP packet building"""
        builder = PacketBuilder()
        
        packet = builder.build_http_packet(
            method='GET',
            path='/test',
            headers={'Host': 'example.com'},
            body='test body'
        )
        
        packet_str = packet.decode('utf-8')
        assert 'GET /test HTTP/1.1' in packet_str
        assert 'Host: example.com' in packet_str
        assert 'Content-Length: 9' in packet_str
        assert 'test body' in packet_str

    def test_build_json_packet(self):
        """Test JSON packet building"""
        builder = PacketBuilder()
        
        data = {'key': 'value', 'number': 42}
        packet = builder.build_json_packet(data)
        
        import json
        assert json.loads(packet.decode('utf-8')) == data

    def test_build_custom_packet(self):
        """Test custom packet building"""
        builder = PacketBuilder()
        
        # HTTP type
        packet = builder.build_custom_packet(
            'http',
            method='POST',
            path='/api',
            body='data'
        )
        assert b'POST /api HTTP/1.1' in packet
        
        # TCP type
        packet = builder.build_custom_packet('tcp', data='Hello')
        assert packet == b'Hello'
        
        # JSON type
        packet = builder.build_custom_packet('json', data={'test': True})
        assert b'"test": true' in packet


class TestPacketParser:
    def test_parse_http_response(self):
        """Test HTTP response parsing"""
        parser = PacketParser()
        
        response_data = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 13\r\n\r\n{\"status\":\"ok\"}"
        
        parsed = parser.parse_http_response(response_data)
        
        assert parsed['version'] == 'HTTP/1.1'
        assert parsed['status_code'] == 200
        assert parsed['reason_phrase'] == 'OK'
        assert parsed['headers']['Content-Type'] == 'application/json'
        assert parsed['body'] == '{"status":"ok"}'

    def test_parse_http_request(self):
        """Test HTTP request parsing"""
        parser = PacketParser()
        
        request_data = b"GET /api/data HTTP/1.1\r\nHost: example.com\r\nUser-Agent: TestAgent\r\n\r\n"
        
        parsed = parser.parse_http_request(request_data)
        
        assert parsed['method'] == 'GET'
        assert parsed['path'] == '/api/data'
        assert parsed['version'] == 'HTTP/1.1'
        assert parsed['headers']['Host'] == 'example.com'
        assert parsed['headers']['User-Agent'] == 'TestAgent'

    def test_parse_json_packet(self):
        """Test JSON packet parsing"""
        parser = PacketParser()
        
        json_data = b'{"message": "hello", "value": 123}'
        parsed = parser.parse_json_packet(json_data)
        
        assert parsed['type'] == 'json'
        assert parsed['data']['message'] == 'hello'
        assert parsed['data']['value'] == 123

    def test_auto_parse(self):
        """Test automatic packet type detection"""
        parser = PacketParser()
        
        # HTTP response
        http_data = b"HTTP/1.1 200 OK\r\n\r\n"
        parsed = parser.auto_parse(http_data)
        assert parsed['status_code'] == 200
        
        # HTTP request
        http_request = b"GET / HTTP/1.1\r\n\r\n"
        parsed = parser.auto_parse(http_request)
        assert parsed['method'] == 'GET'
        
        # JSON
        json_data = b'{"test": true}'
        parsed = parser.auto_parse(json_data)
        assert parsed['type'] == 'json'
        
        # Raw data
        raw_data = b"random data"
        parsed = parser.auto_parse(raw_data)
        assert parsed['type'] == 'raw'


class TestAsyncHTTPClient:
    @pytest.mark.asyncio
    async def test_http_client_init(self):
        """Test AsyncHTTPClient initialization"""
        proxies = [{'address': '127.0.0.1', 'port': 8080, 'type': 'http'}]
        manager = ProxyManager(proxies)
        client = AsyncHTTPClient(manager)
        
        assert client.proxy_manager == manager
        
        await manager.close()


def test_package_imports():
    """Test that all main classes can be imported"""
    from pyroxy import (
        ProxyManager, 
        AsyncHTTPClient, 
        PacketBuilder, 
        PacketParser,
        Connection,
        ProxyConnectionError,
        ProxyAuthenticationError,
        PacketError
    )
    
    # Just test that imports work
    assert ProxyManager is not None
    assert AsyncHTTPClient is not None
    assert PacketBuilder is not None
    assert PacketParser is not None
    assert Connection is not None


if __name__ == "__main__":
    # Run basic tests
    print("Running Pyroxy tests...")
    
    # Test imports
    test_package_imports()
    print("✓ Package imports work")
    
    # Test basic functionality
    manager_test = TestProxyManager()
    manager_test.test_proxy_manager_init()
    manager_test.test_get_proxy()
    manager_test.test_build_proxy_url()
    print("✓ ProxyManager tests pass")
    
    builder_test = TestPacketBuilder()
    builder_test.test_build_tcp_packet()
    builder_test.test_build_http_packet()
    builder_test.test_build_json_packet()
    builder_test.test_build_custom_packet()
    print("✓ PacketBuilder tests pass")
    
    parser_test = TestPacketParser()
    parser_test.test_parse_http_response()
    parser_test.test_parse_http_request()
    parser_test.test_parse_json_packet()
    parser_test.test_auto_parse()
    print("✓ PacketParser tests pass")
    
    print("\n🎉 All tests passed! The Pyroxy library is working correctly.")
    print("\nNext steps:")
    print("1. Set up your proxy servers")
    print("2. Run examples/basic_usage.py")
    print("3. Check examples/async_usage.py for advanced features")
    print("4. Test performance with examples/performance_test.py")
