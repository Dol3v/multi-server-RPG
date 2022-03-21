from common.consts import CLIENT_FORMAT, SERVER_HEADER_FORMAT
from common.utils import create_packet, parse


def parse_client_message(packet: bytes) -> tuple | None:
    """
    Use: convert the packets bytes to a list of fields
    """
    return parse(CLIENT_FORMAT, packet)


def generate_server_message(entities_in_range: list) -> bytes | None:
    """
    Use: creates the server update message
    Format: [(pickup id || ack equipped || collision data) + HP + entities in range]
    """
    # converts list of tuples into a list
    data = [len(entities_in_range) // 2]
    # packet data
    data += entities_in_range

    packet_format = SERVER_HEADER_FORMAT + "l" * len(entities_in_range)

    return create_packet(packet_format, data)
