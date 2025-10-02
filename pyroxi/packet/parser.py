import json
import struct
from typing import Dict, Any, Union, Optional, Tuple


class PacketParser:
    """Parse various types of network packets"""
    
    def __init__(self):
        pass

    def parse_http_response(self, data: bytes) -> Dict[str, Any]:
        """Parse HTTP response packet"""
        try:
            response_str = data.decode('utf-8', errors='ignore')
            lines = response_str.split('\r\n')
            
            # Parse status line
            status_line = lines[0]
            parts = status_line.split(' ', 2)
            
            if len(parts) >= 3:
                version = parts[0]
                status_code = int(parts[1])
                reason_phrase = parts[2]
            else:
                version = "HTTP/1.1"
                status_code = 200
                reason_phrase = "OK"
            
            # Parse headers
            headers = {}
            body_start = 0
            
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # Extract body
            body_lines = lines[body_start:]
            body = '\r\n'.join(body_lines)
            
            return {
                'version': version,
                'status_code': status_code,
                'reason_phrase': reason_phrase,
                'headers': headers,
                'body': body,
                'raw_data': data
            }
        
        except Exception as e:
            return {
                'error': f"Failed to parse HTTP response: {str(e)}",
                'raw_data': data
            }

    def parse_http_request(self, data: bytes) -> Dict[str, Any]:
        """Parse HTTP request packet"""
        try:
            request_str = data.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            
            # Parse request line
            request_line = lines[0]
            parts = request_line.split(' ')
            
            if len(parts) >= 3:
                method = parts[0]
                path = parts[1]
                version = parts[2]
            else:
                method = "GET"
                path = "/"
                version = "HTTP/1.1"
            
            # Parse headers
            headers = {}
            body_start = 0
            
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            # Extract body
            body_lines = lines[body_start:]
            body = '\r\n'.join(body_lines)
            
            return {
                'method': method,
                'path': path,
                'version': version,
                'headers': headers,
                'body': body,
                'raw_data': data
            }
        
        except Exception as e:
            return {
                'error': f"Failed to parse HTTP request: {str(e)}",
                'raw_data': data
            }

    def parse_json_packet(self, data: bytes) -> Dict[str, Any]:
        """Parse JSON packet"""
        try:
            json_str = data.decode('utf-8')
            parsed_json = json.loads(json_str)
            return {
                'type': 'json',
                'data': parsed_json,
                'raw_data': data
            }
        except Exception as e:
            return {
                'error': f"Failed to parse JSON: {str(e)}",
                'raw_data': data
            }

    def parse_socks5_response(self, data: bytes) -> Dict[str, Any]:
        """Parse SOCKS5 response packet"""
        try:
            if len(data) < 2:
                return {'error': 'Insufficient data for SOCKS5 response', 'raw_data': data}
            
            version = data[0]
            response_code = data[1]
            
            response_codes = {
                0x00: "Request granted",
                0x01: "General failure",
                0x02: "Connection not allowed by ruleset",
                0x03: "Network unreachable",
                0x04: "Host unreachable",
                0x05: "Connection refused by destination host",
                0x06: "TTL expired",
                0x07: "Command not supported or protocol error",
                0x08: "Address type not supported"
            }
            
            return {
                'type': 'socks5_response',
                'version': version,
                'response_code': response_code,
                'message': response_codes.get(response_code, 'Unknown error'),
                'success': response_code == 0x00,
                'raw_data': data
            }
        
        except Exception as e:
            return {
                'error': f"Failed to parse SOCKS5 response: {str(e)}",
                'raw_data': data
            }

    def parse_websocket_frame(self, data: bytes) -> Dict[str, Any]:
        """Parse WebSocket frame"""
        try:
            if len(data) < 2:
                return {'error': 'Insufficient data for WebSocket frame', 'raw_data': data}
            
            # First byte: FIN, RSV, Opcode
            first_byte = data[0]
            fin = (first_byte & 0x80) >> 7
            rsv = (first_byte & 0x70) >> 4
            opcode = first_byte & 0x0F
            
            # Second byte: MASK, Payload length
            second_byte = data[1]
            mask = (second_byte & 0x80) >> 7
            payload_length = second_byte & 0x7F
            
            offset = 2
            
            # Extended payload length
            if payload_length == 126:
                if len(data) < offset + 2:
                    return {'error': 'Insufficient data for extended length', 'raw_data': data}
                payload_length = struct.unpack('>H', data[offset:offset+2])[0]
                offset += 2
            elif payload_length == 127:
                if len(data) < offset + 8:
                    return {'error': 'Insufficient data for extended length', 'raw_data': data}
                payload_length = struct.unpack('>Q', data[offset:offset+8])[0]
                offset += 8
            
            # Masking key
            mask_key = None
            if mask:
                if len(data) < offset + 4:
                    return {'error': 'Insufficient data for mask key', 'raw_data': data}
                mask_key = data[offset:offset+4]
                offset += 4
            
            # Payload data
            if len(data) < offset + payload_length:
                return {'error': 'Insufficient data for payload', 'raw_data': data}
            
            payload = data[offset:offset+payload_length]
            
            # Unmask payload if masked
            if mask and mask_key:
                unmasked_payload = bytearray()
                for i, byte in enumerate(payload):
                    unmasked_payload.append(byte ^ mask_key[i % 4])
                payload = bytes(unmasked_payload)
            
            return {
                'type': 'websocket_frame',
                'fin': fin,
                'rsv': rsv,
                'opcode': opcode,
                'mask': mask,
                'payload_length': payload_length,
                'payload': payload,
                'text': payload.decode('utf-8', errors='ignore') if opcode == 1 else None,
                'raw_data': data
            }
        
        except Exception as e:
            return {
                'error': f"Failed to parse WebSocket frame: {str(e)}",
                'raw_data': data
            }

    def auto_parse(self, data: bytes) -> Dict[str, Any]:
        """Automatically detect and parse packet type"""
        # Try to detect packet type based on content
        
        # Check for HTTP
        if data.startswith(b'HTTP/'):
            return self.parse_http_response(data)
        elif any(data.startswith(method.encode()) for method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'CONNECT']):
            return self.parse_http_request(data)
        
        # Check for JSON
        try:
            data_str = data.decode('utf-8').strip()
            if data_str.startswith('{') and data_str.endswith('}'):
                return self.parse_json_packet(data)
        except:
            pass
        
        # Check for WebSocket (basic check)
        if len(data) >= 2 and (data[0] & 0x0F) in [0, 1, 2, 8, 9, 10]:  # Common WebSocket opcodes
            ws_result = self.parse_websocket_frame(data)
            if 'error' not in ws_result:
                return ws_result
        
        # Default: return as raw data
        return {
            'type': 'raw',
            'data': data,
            'text': data.decode('utf-8', errors='ignore'),
            'raw_data': data
        }

    # Legacy methods for backward compatibility
    def parse_packet(self, packet):
        """Legacy method - parse packet"""
        if isinstance(packet, bytes):
            return self.auto_parse(packet)
        elif isinstance(packet, dict) and 'data' in packet:
            return packet
        else:
            return {'data': packet}

    def extract_data(self, parsed_packet):
        """Legacy method - extract data from parsed packet"""
        if isinstance(parsed_packet, dict):
            return parsed_packet.get('data') or parsed_packet.get('body') or parsed_packet.get('payload')
        return parsed_packet
