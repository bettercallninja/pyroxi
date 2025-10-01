import json
import struct
from typing import Dict, Any, Union, Optional


class PacketBuilder:
    """Build various types of packets for network communication"""
    
    def __init__(self):
        self.packet = {}

    def build_http_packet(self, method: str, path: str, headers: Optional[Dict] = None, 
                         body: Optional[Union[str, bytes]] = None, version: str = "1.1") -> bytes:
        """Build HTTP packet"""
        if headers is None:
            headers = {}
        
        # Ensure Host header exists
        if 'Host' not in headers:
            headers['Host'] = 'localhost'
        
        # Build request line
        request_line = f"{method.upper()} {path} HTTP/{version}\r\n"
        
        # Build headers
        header_lines = ""
        for key, value in headers.items():
            header_lines += f"{key}: {value}\r\n"
        
        # Add Content-Length if body exists
        if body:
            if isinstance(body, str):
                body = body.encode('utf-8')
            header_lines += f"Content-Length: {len(body)}\r\n"
        
        # Combine all parts
        packet = request_line + header_lines + "\r\n"
        packet_bytes = packet.encode('utf-8')
        
        if body:
            packet_bytes += body
        
        return packet_bytes

    def build_tcp_packet(self, data: Union[str, bytes], encoding: str = 'utf-8') -> bytes:
        """Build TCP packet with raw data"""
        if isinstance(data, str):
            return data.encode(encoding)
        return data

    def build_json_packet(self, data: Dict[str, Any]) -> bytes:
        """Build JSON packet"""
        return json.dumps(data).encode('utf-8')

    def build_custom_packet(self, packet_type: str, **kwargs) -> bytes:
        """Build custom packet based on type"""
        if packet_type.lower() == 'http':
            return self.build_http_packet(
                kwargs.get('method', 'GET'),
                kwargs.get('path', '/'),
                kwargs.get('headers'),
                kwargs.get('body'),
                kwargs.get('version', '1.1')
            )
        elif packet_type.lower() == 'tcp':
            return self.build_tcp_packet(
                kwargs.get('data', ''),
                kwargs.get('encoding', 'utf-8')
            )
        elif packet_type.lower() == 'json':
            return self.build_json_packet(kwargs.get('data', {}))
        else:
            raise ValueError(f"Unsupported packet type: {packet_type}")

    # Legacy methods for backward compatibility
    def build_packet(self, data):
        """Legacy method - build simple packet"""
        self.packet['data'] = data
        return self.packet

    def add_header(self, header, value):
        """Legacy method - add header to packet"""
        if 'headers' not in self.packet:
            self.packet['headers'] = {}
        self.packet['headers'][header] = value


class AdvancedPacketBuilder(PacketBuilder):
    """Advanced packet builder with protocol-specific features"""
    
    def build_socks5_auth_packet(self, username: str, password: str) -> bytes:
        """Build SOCKS5 authentication packet"""
        packet = b'\x01'  # Version
        packet += bytes([len(username)]) + username.encode()
        packet += bytes([len(password)]) + password.encode()
        return packet

    def build_socks5_connect_packet(self, host: str, port: int) -> bytes:
        """Build SOCKS5 connection request packet"""
        packet = b'\x05\x01\x00'  # Version 5, connect, reserved
        
        # Add target address
        try:
            import socket
            ip = socket.inet_aton(host)
            packet += b'\x01' + ip  # IPv4
        except socket.error:
            # Domain name
            packet += b'\x03' + bytes([len(host)]) + host.encode()
        
        # Add port
        packet += struct.pack('>H', port)
        return packet

    def build_http_connect_packet(self, host: str, port: int, 
                                 auth: Optional[tuple] = None) -> bytes:
        """Build HTTP CONNECT packet for tunneling"""
        packet = f"CONNECT {host}:{port} HTTP/1.1\r\n"
        packet += f"Host: {host}:{port}\r\n"
        
        if auth:
            import base64
            username, password = auth
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            packet += f"Proxy-Authorization: Basic {auth_string}\r\n"
        
        packet += "\r\n"
        return packet.encode('utf-8')

    def build_websocket_frame(self, data: Union[str, bytes], opcode: int = 1, 
                             mask: bool = True) -> bytes:
        """Build WebSocket frame"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        frame = bytearray()
        
        # First byte: FIN (1) + RSV (000) + Opcode (4 bits)
        frame.append(0x80 | opcode)
        
        # Payload length and mask bit
        payload_length = len(data)
        if payload_length < 126:
            frame.append((0x80 if mask else 0x00) | payload_length)
        elif payload_length < 65536:
            frame.append((0x80 if mask else 0x00) | 126)
            frame.extend(struct.pack('>H', payload_length))
        else:
            frame.append((0x80 if mask else 0x00) | 127)
            frame.extend(struct.pack('>Q', payload_length))
        
        # Masking key (if masked)
        if mask:
            import os
            mask_key = os.urandom(4)
            frame.extend(mask_key)
            
            # Mask the payload
            masked_data = bytearray()
            for i, byte in enumerate(data):
                masked_data.append(byte ^ mask_key[i % 4])
            frame.extend(masked_data)
        else:
            frame.extend(data)
        
        return bytes(frame)