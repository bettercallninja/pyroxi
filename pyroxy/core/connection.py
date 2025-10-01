import asyncio
import socket
import struct
import base64
from typing import Dict, Optional, Tuple, Union
from ..exceptions import ProxyConnectionError, ProxyAuthenticationError


class Connection:
    def __init__(self, proxy_address: str, proxy_port: int, proxy_type: str = 'http', 
                 username: Optional[str] = None, password: Optional[str] = None):
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.proxy_type = proxy_type.lower()
        self.username = username
        self.password = password
        self.connected = False
        self.socket = None
        
        if self.proxy_type not in ['http', 'socks5']:
            raise ValueError("Proxy type must be 'http' or 'socks5'")

    async def connect(self, target_host: str, target_port: int) -> bool:
        """Establish connection through proxy to target destination"""
        try:
            if self.proxy_type == 'socks5':
                return await self._connect_socks5(target_host, target_port)
            elif self.proxy_type == 'http':
                return await self._connect_http(target_host, target_port)
        except Exception as e:
            raise ProxyConnectionError(f"Failed to connect through proxy: {str(e)}")

    async def _connect_socks5(self, target_host: str, target_port: int) -> bool:
        """Connect through SOCKS5 proxy"""
        try:
            # Create socket connection to proxy
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.proxy_address, self.proxy_port)
            )
            
            # SOCKS5 greeting
            if self.username and self.password:
                # Authentication required
                greeting = b'\x05\x02\x00\x02'  # Version 5, 2 methods, no auth + username/password
            else:
                greeting = b'\x05\x01\x00'      # Version 5, 1 method, no auth
            
            await asyncio.get_event_loop().run_in_executor(None, self.socket.send, greeting)
            response = await asyncio.get_event_loop().run_in_executor(None, self.socket.recv, 2)
            
            if response[0] != 0x05:
                raise ProxyConnectionError("Invalid SOCKS5 proxy response")
            
            # Handle authentication
            if response[1] == 0x02:  # Username/password authentication
                if not self.username or not self.password:
                    raise ProxyAuthenticationError("Proxy requires authentication")
                await self._socks5_authenticate()
            elif response[1] != 0x00:
                raise ProxyAuthenticationError("Proxy authentication method not supported")
            
            # SOCKS5 connection request
            request = b'\x05\x01\x00'  # Version 5, connect, reserved
            
            # Add target address
            try:
                # Try to parse as IP address
                ip = socket.inet_aton(target_host)
                request += b'\x01' + ip
            except socket.error:
                # It's a domain name
                request += b'\x03' + bytes([len(target_host)]) + target_host.encode()
            
            # Add target port
            request += struct.pack('>H', target_port)
            
            await asyncio.get_event_loop().run_in_executor(None, self.socket.send, request)
            response = await asyncio.get_event_loop().run_in_executor(None, self.socket.recv, 10)
            
            if response[1] != 0x00:
                raise ProxyConnectionError(f"SOCKS5 connection failed with code: {response[1]}")
            
            self.connected = True
            return True
            
        except Exception as e:
            if self.socket:
                self.socket.close()
            raise ProxyConnectionError(f"SOCKS5 connection failed: {str(e)}")

    async def _socks5_authenticate(self):
        """Perform SOCKS5 username/password authentication"""
        auth_request = (b'\x01' + 
                       bytes([len(self.username)]) + self.username.encode() +
                       bytes([len(self.password)]) + self.password.encode())
        
        await asyncio.get_event_loop().run_in_executor(None, self.socket.send, auth_request)
        response = await asyncio.get_event_loop().run_in_executor(None, self.socket.recv, 2)
        
        if response[1] != 0x00:
            raise ProxyAuthenticationError("SOCKS5 authentication failed")

    async def _connect_http(self, target_host: str, target_port: int) -> bool:
        """Connect through HTTP proxy using CONNECT method"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.proxy_address, self.proxy_port)
            )
            
            # HTTP CONNECT request
            connect_request = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
            connect_request += f"Host: {target_host}:{target_port}\r\n"
            
            # Add authentication if provided
            if self.username and self.password:
                auth_string = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
                connect_request += f"Proxy-Authorization: Basic {auth_string}\r\n"
            
            connect_request += "\r\n"
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.send, connect_request.encode()
            )
            
            # Read response
            response = await asyncio.get_event_loop().run_in_executor(None, self.socket.recv, 1024)
            response_str = response.decode()
            
            if "200 Connection established" not in response_str:
                raise ProxyConnectionError(f"HTTP CONNECT failed: {response_str}")
            
            self.connected = True
            return True
            
        except Exception as e:
            if self.socket:
                self.socket.close()
            raise ProxyConnectionError(f"HTTP proxy connection failed: {str(e)}")

    async def send_data(self, data: bytes) -> int:
        """Send raw data through the established connection"""
        if not self.connected or not self.socket:
            raise ProxyConnectionError("Not connected to proxy")
        
        try:
            return await asyncio.get_event_loop().run_in_executor(None, self.socket.send, data)
        except Exception as e:
            raise ProxyConnectionError(f"Failed to send data: {str(e)}")

    async def receive_data(self, buffer_size: int = 4096) -> bytes:
        """Receive data through the established connection"""
        if not self.connected or not self.socket:
            raise ProxyConnectionError("Not connected to proxy")
        
        try:
            return await asyncio.get_event_loop().run_in_executor(None, self.socket.recv, buffer_size)
        except Exception as e:
            raise ProxyConnectionError(f"Failed to receive data: {str(e)}")

    async def disconnect(self):
        """Disconnect from the proxy server"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False

    def is_connected(self) -> bool:
        """Check if connection is established"""
        return self.connected

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()