import struct
from common.consts import CLIENT_FORMAT, SERVER_HEADER_FORMAT, Pos, ENTITY_FORMAT, ENTITY_FIELD_NUM
from common.utils import parse


def parse_client_message(packet: bytes) -> tuple | None:
    """
    Use: convert the packets bytes to a list of fields
    """
    return parse(CLIENT_FORMAT, packet)


def generate_server_message(tools: list, new_msg: str, last_valid_pos: Pos, health: int, entities_in_range: list) -> bytes | None:
    """
    Use: creates the server update message
    Format: [tools + new_msg + last valid pos + HP + entities in range]
    NOTE: the first tool inside the tools will be the equipped one. 
    """
    data = []
    entities_count = len(entities_in_range) // ENTITY_FIELD_NUM
    # create data array
    data += tools
    data.append(new_msg.encode())
    data += [*last_valid_pos]
    data.append(health)
    data.append(entities_count)
    # packet data
    data += entities_in_range

    packet_format = SERVER_HEADER_FORMAT + ENTITY_FORMAT * entities_count
    print(data)
    print(packet_format)

    return struct.pack(packet_format, *data)
