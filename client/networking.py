"""Utils for communicating with the server"""
import struct

from common.consts import SERVER_HEADER_SIZE, SERVER_HEADER_FORMAT, MESSAGE_ENDIANESS, POSITION_FORMAT, INT_SIZE, CLIENT_FORMAT
from typing import Tuple
from common.utils import parse



def parse_server_message(packet: bytes) -> Tuple[Tuple, list] | Tuple:
    """
    Use: convert the packets bytes to a list of fields
    """
    # tools, valid pos, health, entities
    player_status = parse(SERVER_HEADER_FORMAT, packet[:SERVER_HEADER_SIZE])


    # entities
    num_of_entities = player_status[-1]
    player_status = player_status[:-1]

    if num_of_entities == 0:
        return player_status, []

    entity_locations_raw = parse(MESSAGE_ENDIANESS + POSITION_FORMAT * num_of_entities,
                                 packet[SERVER_HEADER_SIZE: SERVER_HEADER_SIZE + num_of_entities * 2 * INT_SIZE])

    if entity_locations_raw:
        entities = [(entity_locations_raw[i], entity_locations_raw[i + 1])
                            for i in range(0, len(entity_locations_raw), 2)]

    
        return player_status, entities


def generate_client_message(seqn: int, x: int, y: int, actions: list) -> bytes | None:
    """
    Use: generate the client message bytes by this format
    Format: [pos(x, y) + (new_msg || attack || attack_directiton || equipped_id )]
    """
    return struct.pack(CLIENT_FORMAT, seqn, x, y, *actions)
