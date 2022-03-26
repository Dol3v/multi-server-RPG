"""Utils for communicating with the server"""
import struct

from common.consts import SERVER_HEADER_SIZE, SERVER_HEADER_FORMAT, MESSAGE_ENDIANESS, POSITION_FORMAT, CLIENT_FORMAT, ENTITY_FORMAT, ENTITY_FIELD_NUM
from typing import Tuple
from common.utils import parse



def parse_server_message(packet: bytes) -> Tuple[Tuple, list] | Tuple:
    """
    Use: convert the packets bytes to a list of fields
    """
    # tools, new_chat, valid pos, health
    player_status = parse(SERVER_HEADER_FORMAT, packet[:SERVER_HEADER_SIZE])
    #print(player_status)

    if not player_status:
        return (), []


    # entities
    num_of_entities = player_status[-1]
    player_status = player_status[:-1]
    print(num_of_entities)

    if num_of_entities == 0:
        return player_status, []

    raw_entities = parse(MESSAGE_ENDIANESS +  ENTITY_FORMAT * num_of_entities, # Format
                                 packet[SERVER_HEADER_SIZE: SERVER_HEADER_SIZE + num_of_entities * struct.calcsize(ENTITY_FORMAT) ]) # partition

    print(raw_entities)
    if raw_entities:
        entities = [(raw_entities[i], (raw_entities[i + 1], raw_entities[i + 2]), (raw_entities[i + 3], raw_entities[i + 4])) 
                    for i in range(0, len(raw_entities) -1, ENTITY_FIELD_NUM)]

    
        return player_status, entities


def generate_client_message(seqn: int, x: int, y: int, actions: list) -> bytes | None:
    """
    Use: generate the client message bytes by this format
    Format: [pos(x, y) + (new_msg || attack || attack_directiton || equipped_id )]
    """
    return struct.pack(CLIENT_FORMAT, seqn, x, y, *actions)
