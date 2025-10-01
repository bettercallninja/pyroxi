def log_message(message):
    """Logs a message to the console."""
    print(f"[LOG] {message}")

def validate_ip(ip_address):
    """Validates the format of an IP address."""
    import re
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if re.match(pattern, ip_address):
        return True
    return False

def validate_port(port):
    """Validates the port number."""
    return isinstance(port, int) and 0 <= port <= 65535

def format_packet(packet):
    """Formats a packet for sending."""
    return bytes(str(packet), 'utf-8')