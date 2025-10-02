import asyncio
import socket
import struct
import base64
import logging
from typing import Dict, Optional, Tuple, Union, List
from ..exceptions import ProxyConnectionError, ProxyAuthenticationError

logger = logging.getLogger(__name__)


class Connection:
    """High-performance socket-based proxy connection handler"""
    
    # SOCKS5 Constants
    SOCKS5_VERSION = 0x05
    SOCKS5_AUTH_NONE = 0x00
    SOCKS5_AUTH_USERPASS = 0x02
    SOCKS5_CMD_CONNECT = 0x01
    SOCKS5_ATYP_IPV4 = 0x01
    SOCKS5_ATYP_DOMAIN = 0x03
    SOCKS5_ATYP_IPV6 = 0x04
    
    # SOCKS5 Reply codes
    SOCKS5_REPLY_SUCCESS = 0x00
    SOCKS5_REPLY_GENERAL_FAILURE = 0x01
    SOCKS5_REPLY_CONN_NOT_ALLOWED = 0x02
    SOCKS5_REPLY_NETWORK_UNREACHABLE = 0x03
    SOCKS5_REPLY_HOST_UNREACHABLE = 0x04
    SOCKS5_REPLY_CONNECTION_REFUSED = 0x05
    SOCKS5_REPLY_TTL_EXPIRED = 0x06
    SOCKS5_REPLY_CMD_NOT_SUPPORTED = 0x07
    SOCKS5_REPLY_ATYP_NOT_SUPPORTED = 0x08
    
    def __init__(self, proxy_address: str, proxy_port: int, proxy_type: str = 'http', 
                 username: Optional[str] = None, password: Optional[str] = None,
                 timeout: int = 30, buffer_size: int = 8192):
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port
        self.proxy_type = proxy_type.lower()
        self.username = username
        self.password = password
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.connected = False
        self.socket = None
        self._target_host = None
        self._target_port = None
        
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
        """
        Connect through SOCKS5 proxy using pure socket operations
        Implements RFC 1928 (SOCKS5) with binary networking
        """
        try:
            # Create high-performance socket with optimized settings
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
            self.socket.settimeout(self.timeout)
            
            # Connect to proxy server
            logger.debug(f"Connecting to SOCKS5 proxy {self.proxy_address}:{self.proxy_port}")
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.proxy_address, self.proxy_port)
            )
            
            # SOCKS5 Handshake - Send greeting with authentication methods
            auth_methods = [self.SOCKS5_AUTH_NONE]
            if self.username and self.password:
                auth_methods.append(self.SOCKS5_AUTH_USERPASS)
            
            greeting = struct.pack('BB', self.SOCKS5_VERSION, len(auth_methods))
            greeting += bytes(auth_methods)
            
            await self._socket_send_all(greeting)
            logger.debug(f"Sent SOCKS5 greeting: {greeting.hex()}")
            
            # Receive server's chosen authentication method
            response = await self._socket_recv_exact(2)
            version, auth_method = struct.unpack('BB', response)
            
            if version != self.SOCKS5_VERSION:
                raise ProxyConnectionError(f"Invalid SOCKS5 version: {version}")
            
            logger.debug(f"Server chose auth method: {auth_method}")
            
            # Handle authentication
            if auth_method == self.SOCKS5_AUTH_USERPASS:
                if not self.username or not self.password:
                    raise ProxyAuthenticationError("Proxy requires authentication but no credentials provided")
                await self._socks5_authenticate()
            elif auth_method == self.SOCKS5_AUTH_NONE:
                logger.debug("No authentication required")
            elif auth_method == 0xFF:
                raise ProxyAuthenticationError("No acceptable authentication methods")
            else:
                raise ProxyAuthenticationError(f"Unsupported authentication method: {auth_method}")
            
            # Send connection request
            await self._socks5_send_connect_request(target_host, target_port)
            
            # Receive connection response
            response = await self._socket_recv_exact(4)
            version, reply, reserved, atyp = struct.unpack('BBBB', response)
            
            if version != self.SOCKS5_VERSION:
                raise ProxyConnectionError(f"Invalid SOCKS5 version in reply: {version}")
            
            # Read bound address based on address type
            if atyp == self.SOCKS5_ATYP_IPV4:
                await self._socket_recv_exact(4)  # IPv4 address
            elif atyp == self.SOCKS5_ATYP_DOMAIN:
                domain_len = struct.unpack('B', await self._socket_recv_exact(1))[0]
                await self._socket_recv_exact(domain_len)  # Domain name
            elif atyp == self.SOCKS5_ATYP_IPV6:
                await self._socket_recv_exact(16)  # IPv6 address
            else:
                raise ProxyConnectionError(f"Invalid address type: {atyp}")
            
            # Read bound port
            await self._socket_recv_exact(2)
            
            # Check reply code
            if reply != self.SOCKS5_REPLY_SUCCESS:
                error_msg = self._get_socks5_error_message(reply)
                raise ProxyConnectionError(f"SOCKS5 connection failed: {error_msg}")
            
            self.connected = True
            self._target_host = target_host
            self._target_port = target_port
            logger.info(f"Successfully connected to {target_host}:{target_port} via SOCKS5")
            return True
            
        except ProxyConnectionError:
            raise
        except Exception as e:
            if self.socket:
                self.socket.close()
            raise ProxyConnectionError(f"SOCKS5 connection failed: {str(e)}")

    async def _socks5_authenticate(self):
        """
        Perform SOCKS5 username/password authentication (RFC 1929)
        Uses binary packing for optimal performance
        """
        username_bytes = self.username.encode('utf-8')
        password_bytes = self.password.encode('utf-8')
        
        if len(username_bytes) > 255 or len(password_bytes) > 255:
            raise ProxyAuthenticationError("Username or password too long (max 255 bytes)")
        
        # Build authentication request: version + username_len + username + password_len + password
        auth_request = struct.pack('B', 0x01)  # Auth version
        auth_request += struct.pack('B', len(username_bytes)) + username_bytes
        auth_request += struct.pack('B', len(password_bytes)) + password_bytes
        
        await self._socket_send_all(auth_request)
        logger.debug("Sent SOCKS5 authentication request")
        
        # Receive authentication response
        response = await self._socket_recv_exact(2)
        auth_version, status = struct.unpack('BB', response)
        
        if status != 0x00:
            raise ProxyAuthenticationError(f"SOCKS5 authentication failed with status: {status}")
        
        logger.debug("SOCKS5 authentication successful")
    
    async def _socks5_send_connect_request(self, target_host: str, target_port: int):
        """
        Send SOCKS5 CONNECT request with binary address encoding
        Supports IPv4, IPv6, and domain names
        """
        # Request header: VER + CMD + RSV
        request = struct.pack('BBB', self.SOCKS5_VERSION, self.SOCKS5_CMD_CONNECT, 0x00)
        
        # Encode destination address
        try:
            # Try IPv4
            ipv4_bytes = socket.inet_aton(target_host)
            request += struct.pack('B', self.SOCKS5_ATYP_IPV4) + ipv4_bytes
            logger.debug(f"Using IPv4 address: {target_host}")
        except socket.error:
            try:
                # Try IPv6
                ipv6_bytes = socket.inet_pton(socket.AF_INET6, target_host)
                request += struct.pack('B', self.SOCKS5_ATYP_IPV6) + ipv6_bytes
                logger.debug(f"Using IPv6 address: {target_host}")
            except socket.error:
                # Use domain name
                domain_bytes = target_host.encode('utf-8')
                if len(domain_bytes) > 255:
                    raise ProxyConnectionError("Domain name too long (max 255 bytes)")
                request += struct.pack('BB', self.SOCKS5_ATYP_DOMAIN, len(domain_bytes)) + domain_bytes
                logger.debug(f"Using domain name: {target_host}")
        
        # Add destination port (big-endian)
        request += struct.pack('>H', target_port)
        
        await self._socket_send_all(request)
        logger.debug(f"Sent SOCKS5 CONNECT request to {target_host}:{target_port}")
    
    def _get_socks5_error_message(self, reply_code: int) -> str:
        """Get human-readable error message for SOCKS5 reply codes"""
        error_messages = {
            self.SOCKS5_REPLY_GENERAL_FAILURE: "General SOCKS server failure",
            self.SOCKS5_REPLY_CONN_NOT_ALLOWED: "Connection not allowed by ruleset",
            self.SOCKS5_REPLY_NETWORK_UNREACHABLE: "Network unreachable",
            self.SOCKS5_REPLY_HOST_UNREACHABLE: "Host unreachable",
            self.SOCKS5_REPLY_CONNECTION_REFUSED: "Connection refused",
            self.SOCKS5_REPLY_TTL_EXPIRED: "TTL expired",
            self.SOCKS5_REPLY_CMD_NOT_SUPPORTED: "Command not supported",
            self.SOCKS5_REPLY_ATYP_NOT_SUPPORTED: "Address type not supported",
        }
        return error_messages.get(reply_code, f"Unknown error code: {reply_code}")

    async def _connect_http(self, target_host: str, target_port: int) -> bool:
        """
        Connect through HTTP proxy using CONNECT method (RFC 7231)
        Implements HTTP tunnel with binary socket operations
        """
        try:
            # Create high-performance socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.settimeout(self.timeout)
            
            # Connect to HTTP proxy
            logger.debug(f"Connecting to HTTP proxy {self.proxy_address}:{self.proxy_port}")
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.proxy_address, self.proxy_port)
            )
            
            # Build HTTP CONNECT request
            connect_lines = [
                f"CONNECT {target_host}:{target_port} HTTP/1.1",
                f"Host: {target_host}:{target_port}",
                "User-Agent: pyroxi/1.0",
                "Proxy-Connection: Keep-Alive",
            ]
            
            # Add proxy authentication if provided
            if self.username and self.password:
                credentials = f"{self.username}:{self.password}"
                auth_encoded = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
                connect_lines.append(f"Proxy-Authorization: Basic {auth_encoded}")
                logger.debug("Added proxy authentication header")
            
            # Build complete request with proper line endings
            connect_request = "\r\n".join(connect_lines) + "\r\n\r\n"
            connect_bytes = connect_request.encode('utf-8')
            
            # Send CONNECT request
            await self._socket_send_all(connect_bytes)
            logger.debug(f"Sent HTTP CONNECT request to {target_host}:{target_port}")
            
            # Read HTTP response with efficient buffering
            response_buffer = b""
            max_header_size = 8192
            
            # Read response in larger chunks for better performance
            while len(response_buffer) < max_header_size:
                try:
                    chunk = await asyncio.get_event_loop().run_in_executor(
                        None, self.socket.recv, 4096  # Read 4KB chunks instead of 1 byte
                    )
                    if not chunk:
                        raise ProxyConnectionError("Connection closed by proxy")
                    
                    response_buffer += chunk
                    
                    # Check for end of headers
                    if b"\r\n\r\n" in response_buffer:
                        break
                        
                except socket.timeout:
                    raise ProxyConnectionError("Timeout reading HTTP proxy response")
                except Exception as e:
                    raise ProxyConnectionError(f"Error reading HTTP proxy response: {str(e)}")
            
            # Prevent oversized headers
            if len(response_buffer) >= max_header_size and b"\r\n\r\n" not in response_buffer:
                raise ProxyConnectionError("HTTP response headers too large")
            
            # Parse HTTP response
            response_str = response_buffer.decode('utf-8', errors='ignore')
            response_lines = response_str.split('\r\n')
            
            if not response_lines:
                raise ProxyConnectionError("Empty HTTP response from proxy")
            
            # Parse status line
            status_line = response_lines[0]
            logger.debug(f"HTTP proxy response: {status_line}")
            
            # Check for successful connection
            if not any(code in status_line for code in ['200', '201', '202']):
                # Extract status code and message
                parts = status_line.split(' ', 2)
                status_code = parts[1] if len(parts) > 1 else "Unknown"
                status_msg = parts[2] if len(parts) > 2 else "Unknown error"
                
                if '407' in status_line:
                    raise ProxyAuthenticationError(f"HTTP proxy authentication required: {status_msg}")
                else:
                    raise ProxyConnectionError(f"HTTP CONNECT failed [{status_code}]: {status_msg}")
            
            self.connected = True
            self._target_host = target_host
            self._target_port = target_port
            logger.info(f"Successfully connected to {target_host}:{target_port} via HTTP proxy")
            return True
            
        except ProxyConnectionError:
            raise
        except Exception as e:
            if self.socket:
                self.socket.close()
            raise ProxyConnectionError(f"HTTP proxy connection failed: {str(e)}")

    async def _socket_send_all(self, data: bytes):
        """
        Send all data through socket with proper error handling
        Ensures all bytes are sent even with partial writes
        """
        total_sent = 0
        data_len = len(data)
        
        while total_sent < data_len:
            try:
                sent = await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.send, data[total_sent:]
                )
                if sent == 0:
                    raise ProxyConnectionError("Socket connection broken")
                total_sent += sent
            except socket.timeout:
                raise ProxyConnectionError("Socket send timeout")
            except Exception as e:
                raise ProxyConnectionError(f"Socket send error: {str(e)}")
    
    async def _socket_recv_exact(self, num_bytes: int) -> bytes:
        """
        Receive exact number of bytes from socket
        Blocks until all requested bytes are received
        """
        data = b""
        while len(data) < num_bytes:
            try:
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.recv, num_bytes - len(data)
                )
                if not chunk:
                    raise ProxyConnectionError("Socket connection closed by remote")
                data += chunk
            except socket.timeout:
                raise ProxyConnectionError("Socket receive timeout")
            except Exception as e:
                raise ProxyConnectionError(f"Socket receive error: {str(e)}")
        
        return data

    async def send_data(self, data: bytes) -> int:
        """
        Send raw binary data through the established proxy connection
        High-performance method for sending packets
        """
        if not self.connected or not self.socket:
            raise ProxyConnectionError("Not connected to proxy")
        
        try:
            await self._socket_send_all(data)
            return len(data)
        except Exception as e:
            raise ProxyConnectionError(f"Failed to send data: {str(e)}")
    
    async def send_packet(self, packet: bytes) -> int:
        """
        Send a complete packet with length prefix (for framing)
        Useful for protocols that need message boundaries
        """
        if not isinstance(packet, bytes):
            raise ValueError("Packet must be bytes")
        
        # Send 4-byte length prefix (big-endian) followed by packet
        length_prefix = struct.pack('>I', len(packet))
        full_packet = length_prefix + packet
        
        return await self.send_data(full_packet)

    async def receive_data(self, buffer_size: Optional[int] = None) -> bytes:
        """
        Receive raw binary data through the established connection
        High-performance method for receiving packets
        """
        if not self.connected or not self.socket:
            raise ProxyConnectionError("Not connected to proxy")
        
        if buffer_size is None:
            buffer_size = self.buffer_size
        
        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self.socket.recv, buffer_size
            )
            if not data:
                raise ProxyConnectionError("Connection closed by remote host")
            return data
        except socket.timeout:
            raise ProxyConnectionError("Socket receive timeout")
        except Exception as e:
            raise ProxyConnectionError(f"Failed to receive data: {str(e)}")
    
    async def receive_packet(self) -> bytes:
        """
        Receive a complete packet with length prefix
        Reads 4-byte length prefix and then the exact packet size
        """
        # Read 4-byte length prefix
        length_bytes = await self._socket_recv_exact(4)
        packet_length = struct.unpack('>I', length_bytes)[0]
        
        # Validate packet length
        if packet_length > 10 * 1024 * 1024:  # 10MB max
            raise ProxyConnectionError(f"Packet too large: {packet_length} bytes")
        
        # Read exact packet data
        packet = await self._socket_recv_exact(packet_length)
        return packet
    
    async def receive_all(self, timeout: Optional[float] = None) -> bytes:
        """
        Receive all available data until connection closes
        Useful for HTTP responses and similar protocols
        """
        if not self.connected or not self.socket:
            raise ProxyConnectionError("Not connected to proxy")
        
        all_data = b""
        original_timeout = self.socket.gettimeout()
        
        try:
            if timeout:
                self.socket.settimeout(timeout)
            
            while True:
                try:
                    chunk = await asyncio.get_event_loop().run_in_executor(
                        None, self.socket.recv, self.buffer_size
                    )
                    if not chunk:
                        break
                    all_data += chunk
                except socket.timeout:
                    break
                except Exception:
                    break
            
            return all_data
        finally:
            self.socket.settimeout(original_timeout)

    async def send_http_request(self, method: str, path: str, headers: Optional[Dict[str, str]] = None,
                               body: Optional[bytes] = None) -> bytes:
        """
        Send HTTP request through the tunnel and receive response
        Useful for HTTP-over-proxy scenarios
        """
        if not self.connected:
            raise ProxyConnectionError("Not connected")
        
        # Build HTTP request
        request_lines = [f"{method.upper()} {path} HTTP/1.1"]
        
        # Add default headers
        default_headers = {
            "Host": f"{self._target_host}:{self._target_port}" if self._target_port != 80 else self._target_host,
            "Connection": "keep-alive",
            "User-Agent": "pyroxi/1.0"
        }
        
        if headers:
            default_headers.update(headers)
        
        if body:
            default_headers["Content-Length"] = str(len(body))
        
        # Add headers to request
        for key, value in default_headers.items():
            request_lines.append(f"{key}: {value}")
        
        # Build complete request
        request = "\r\n".join(request_lines) + "\r\n\r\n"
        request_bytes = request.encode('utf-8')
        
        if body:
            request_bytes += body
        
        # Send request
        await self.send_data(request_bytes)
        
        # Receive response
        return await self.receive_all(timeout=30)
    
    def set_timeout(self, timeout: int):
        """Set socket timeout"""
        self.timeout = timeout
        if self.socket:
            self.socket.settimeout(timeout)
    
    def set_buffer_size(self, size: int):
        """Set receive buffer size"""
        if size < 1024 or size > 1024 * 1024:
            raise ValueError("Buffer size must be between 1KB and 1MB")
        self.buffer_size = size
    
    def get_connection_info(self) -> Dict[str, any]:
        """Get connection information"""
        return {
            "proxy_address": self.proxy_address,
            "proxy_port": self.proxy_port,
            "proxy_type": self.proxy_type,
            "target_host": self._target_host,
            "target_port": self._target_port,
            "connected": self.connected,
            "authenticated": bool(self.username and self.password),
            "timeout": self.timeout,
            "buffer_size": self.buffer_size
        }

    async def disconnect(self):
        """Disconnect from the proxy server and cleanup resources"""
        if self.socket:
            try:
                # Graceful shutdown
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        logger.debug(f"Disconnected from {self.proxy_type} proxy")

    def is_connected(self) -> bool:
        """Check if connection is established and socket is alive"""
        if not self.connected or not self.socket:
            return False
        
        try:
            # Try to get socket error state
            error = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            return error == 0
        except:
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    def __repr__(self) -> str:
        status = "connected" if self.connected else "disconnected"
        target = f" to {self._target_host}:{self._target_port}" if self._target_host else ""
        return f"<Connection {self.proxy_type}://{self.proxy_address}:{self.proxy_port} ({status}){target}>"