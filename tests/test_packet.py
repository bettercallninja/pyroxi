import pytest
from pyroxy.packet.builder import PacketBuilder
from pyroxy.packet.parser import PacketParser

def test_packet_builder():
    builder = PacketBuilder()
    packet = builder.build_packet(data="Test data")
    
    assert packet is not None
    assert isinstance(packet, bytes)  # Assuming the packet is built as bytes
    assert builder.add_header(packet, header="Test Header") is not None

def test_packet_parser():
    parser = PacketParser()
    test_packet = b'Test data'  # Example byte packet
    
    parsed_data = parser.parse_packet(test_packet)
    
    assert parsed_data == "Test data"  # Assuming the parser extracts the string correctly
    assert parser.extract_data(parsed_data) == "Test data"  # Assuming it returns the same data