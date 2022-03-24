from common.consts import CLIENT_FORMAT, SERVER_HEADER_FORMAT, Pos
from common.utils import create_packet, parse


def parse_client_message(packet: bytes) -> tuple | None:
    """
    Use: convert the packets bytes to a list of fields
    """
    print("Server received: ", parse(CLIENT_FORMAT, packet))
    return parse(CLIENT_FORMAT, packet)


def generate_server_message(tools: list, last_valid_pos: Pos, health: int, entities_in_range: list) -> bytes | None:
    """
    Use: creates the server update message
    Format: [tools + last valid pos + HP + entities in range]
    NOTE: the first tool inside the tools will be the equipped one. 
    """
    data = []
    # create data array
    data += tools
    data += [*last_valid_pos]
    data.append(health)
    data.append(len(entities_in_range) // 2)
    # packet data
    data += entities_in_range

    packet_format = SERVER_HEADER_FORMAT + "l" * len(entities_in_range)

    return create_packet(packet_format, data)
