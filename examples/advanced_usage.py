# Advanced Usage Example for Pyroxy

# This script demonstrates advanced features of the pyroxy package, including connecting to a proxy, sending packets, and handling responses.

from pyroxy.core.connection import Connection
from pyroxy.core.proxy import Proxy
from pyroxy.packet.builder import PacketBuilder
from pyroxy.packet.parser import PacketParser
from pyroxy.exceptions import ProxyConnectionError, PacketError



def main():
    # Create a connection to the proxy server
    conn = Connection("8.8.8.8:8080")  # Example proxy server address and port
    try:
        conn.connect('proxy.example.com', 8080)
        print("Connected to proxy server.")
    except ProxyConnectionError as e:
        print(f"Failed to connect to proxy: {e}")
        return

    # Create a proxy instance
    proxy = Proxy(conn)

    # Build a packet to send
    packet_builder = PacketBuilder()
    packet = packet_builder.build_packet(data="Hello, Proxy!")
    
    # Send the packet through the proxy
    try:
        response = proxy.send_packet(packet)
        print("Packet sent successfully. Response received:")
        print(response)
    except PacketError as e:
        print(f"Error sending packet: {e}")

    # Disconnect from the proxy
    conn.disconnect()
    print("Disconnected from proxy server.")

if __name__ == "__main__":
    main()