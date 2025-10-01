class ProxyConnectionError(Exception):
    """Exception raised for errors in the connection to the proxy."""
    pass

class ProxyAuthenticationError(Exception):
    """Exception raised for proxy authentication failures."""
    pass

class PacketError(Exception):
    """Exception raised for errors in packet processing."""
    pass