#!/usr/bin/env python3
"""
Test script for PyRoxi packet module
Tests PacketBuilder, AdvancedPacketBuilder, and PacketParser
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyroxi import PacketBuilder, AdvancedPacketBuilder, PacketParser

def test_packet_builder():
    """Test PacketBuilder class"""
    print("=" * 60)
    print("TEST 1: PacketBuilder - HTTP Packet")
    print("=" * 60)
    
    builder = PacketBuilder()
    
    # Test HTTP packet
    http_packet = builder.build_http_packet(
        method="GET",
        path="/test",
        headers={"Host": "example.com", "User-Agent": "PyRoxi/1.0"},
        version="1.1"
    )
    
    print(f"✅ HTTP packet built: {len(http_packet)} bytes")
    print(f"Content:\n{http_packet.decode()[:200]}...")
    
    # Test TCP packet
    print("\n" + "=" * 60)
    print("TEST 2: PacketBuilder - TCP Packet")
    print("=" * 60)
    
    tcp_packet = builder.build_tcp_packet("Hello, World!")
    print(f"✅ TCP packet built: {len(tcp_packet)} bytes")
    print(f"Content: {tcp_packet}")
    
    # Test JSON packet
    print("\n" + "=" * 60)
    print("TEST 3: PacketBuilder - JSON Packet")
    print("=" * 60)
    
    json_packet = builder.build_json_packet({"message": "test", "count": 42})
    print(f"✅ JSON packet built: {len(json_packet)} bytes")
    print(f"Content: {json_packet.decode()}")
    
    return True

def test_advanced_packet_builder():
    """Test AdvancedPacketBuilder class"""
    print("\n" + "=" * 60)
    print("TEST 4: AdvancedPacketBuilder - SOCKS5 Auth")
    print("=" * 60)
    
    builder = AdvancedPacketBuilder()
    
    # Test SOCKS5 auth packet
    auth_packet = builder.build_socks5_auth_packet("user123", "pass456")
    print(f"✅ SOCKS5 auth packet built: {len(auth_packet)} bytes")
    print(f"Content (hex): {auth_packet.hex()}")
    
    # Test SOCKS5 connect packet
    print("\n" + "=" * 60)
    print("TEST 5: AdvancedPacketBuilder - SOCKS5 Connect")
    print("=" * 60)
    
    connect_packet = builder.build_socks5_connect_packet("example.com", 80)
    print(f"✅ SOCKS5 connect packet built: {len(connect_packet)} bytes")
    print(f"Content (hex): {connect_packet.hex()}")
    
    # Test HTTP CONNECT packet
    print("\n" + "=" * 60)
    print("TEST 6: AdvancedPacketBuilder - HTTP CONNECT")
    print("=" * 60)
    
    connect_http = builder.build_http_connect_packet("example.com", 443)
    print(f"✅ HTTP CONNECT packet built: {len(connect_http)} bytes")
    print(f"Content:\n{connect_http.decode()}")
    
    # Test WebSocket frame
    print("\n" + "=" * 60)
    print("TEST 7: AdvancedPacketBuilder - WebSocket Frame")
    print("=" * 60)
    
    ws_frame = builder.build_websocket_frame("Hello WebSocket!", opcode=1, mask=True)
    print(f"✅ WebSocket frame built: {len(ws_frame)} bytes")
    print(f"Content (hex): {ws_frame[:20].hex()}...")
    
    return True

def test_packet_parser():
    """Test PacketParser class"""
    print("\n" + "=" * 60)
    print("TEST 8: PacketParser - HTTP Response")
    print("=" * 60)
    
    parser = PacketParser()
    
    # Test HTTP response parsing
    http_response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 13\r\n\r\nHello, World!"
    parsed = parser.parse_http_response(http_response)
    print(f"✅ HTTP response parsed:")
    print(f"  Status: {parsed['status_code']} {parsed['reason_phrase']}")
    print(f"  Headers: {len(parsed['headers'])} items")
    print(f"  Body: {parsed['body']}")
    
    # Test HTTP request parsing
    print("\n" + "=" * 60)
    print("TEST 9: PacketParser - HTTP Request")
    print("=" * 60)
    
    http_request = b"GET /test HTTP/1.1\r\nHost: example.com\r\n\r\n"
    parsed = parser.parse_http_request(http_request)
    print(f"✅ HTTP request parsed:")
    print(f"  Method: {parsed['method']}")
    print(f"  Path: {parsed['path']}")
    print(f"  Version: {parsed['version']}")
    
    # Test JSON parsing
    print("\n" + "=" * 60)
    print("TEST 10: PacketParser - JSON Packet")
    print("=" * 60)
    
    json_data = b'{"status": "success", "count": 42}'
    parsed = parser.parse_json_packet(json_data)
    print(f"✅ JSON packet parsed:")
    print(f"  Data: {parsed['data']}")
    
    # Test SOCKS5 response parsing
    print("\n" + "=" * 60)
    print("TEST 11: PacketParser - SOCKS5 Response")
    print("=" * 60)
    
    socks5_response = b'\x05\x00'  # Version 5, success
    parsed = parser.parse_socks5_response(socks5_response)
    print(f"✅ SOCKS5 response parsed:")
    print(f"  Version: {parsed['version']}")
    print(f"  Code: {parsed['response_code']}")
    print(f"  Message: {parsed['message']}")
    print(f"  Success: {parsed['success']}")
    
    # Test auto parse
    print("\n" + "=" * 60)
    print("TEST 12: PacketParser - Auto Parse")
    print("=" * 60)
    
    test_data = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    parsed = parser.auto_parse(test_data)
    print(f"✅ Auto parse detected: {parsed.get('method', parsed.get('type', 'unknown'))}")
    
    return True

def main():
    """Run all tests"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║           🧪 PYROXI PACKET MODULE TESTS 🧪                          ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    tests = [
        ("PacketBuilder", test_packet_builder),
        ("AdvancedPacketBuilder", test_advanced_packet_builder),
        ("PacketParser", test_packet_parser)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name} tests PASSED")
            else:
                failed += 1
                print(f"\n❌ {name} tests FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} tests FAILED with exception:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL PACKET MODULE TESTS PASSED! 🎉")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
