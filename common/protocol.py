import struct
from common.consts import *

# Parsing functions
# ---------------------------------------------------------------------------------------
def parse(parse_format: str, data: bytes) -> tuple | None:
    """
    Use: parse a given message by the given format
    """
    try:
        return struct.unpack(parse_format, data)
    except struct.error:
        return None


def parse_client_message(packet: bytes) -> tuple | None:
    """
    Use: convert the packets bytes to a list of fields
    """
    return parse(CLIENT_FORMAT, packet)

def parse_server_message(packet: bytes) -> list:
    """
    Use: convert the packets bytes to a list of fields
    """
    num_of_entities = parse(SERVER_HEADER_FORMAT, packet[:INT_SIZE])[0]

    if num_of_entities == 0:
        return []

    entity_locations_raw = parse(MESSAGE_ENDIANESS + POSITION_FORMAT * num_of_entities,

                                 packet[INT_SIZE: INT_SIZE + num_of_entities * 2 * INT_SIZE])
    
    if entity_locations_raw:
        entity_locations = [(entity_locations_raw[i], entity_locations_raw[i + 1])
                            for i in range(0, len(entity_locations_raw), 2)]
    return entity_locations
# ---------------------------------------------------------------------------------------


# Generating packets functions
# ---------------------------------------------------------------------------------------
def create_packet(packet_format: str, data: list) -> bytes | None:
    """
    Use: create a packet in the given format and data
    Return value: the new packet bytes, or None
    """
    try:
        return struct.pack(packet_format, *data)
    except struct.error:
        return None

def generate_client_message(x: int, y: int) -> bytes:
    """
    Use: generate the client message bytes by this format
    Format: [pos(x, y) + (new_msg || attack || attack_directiton || pick_up || equipped_id)]
    """
    data = [x, y]
    packet_format = CLIENT_FORMAT

    return create_packet(packet_format, data)



def generate_server_message(entities_in_range: list) -> bytes | None:
    """
    Use: creates the server update message
    Format: [(pickup id || ack equipped || collision data) + HP + entities in range]
    """
    # converts list of tuples into a list
    data = []

    # packet data
    data.append(len(entities_in_range) // 2)
    data += entities_in_range

    packet_format = SERVER_HEADER_FORMAT + "l" * len(entities_in_range)

    return create_packet(packet_format, data)

# ---------------------------------------------------------------------------------------
