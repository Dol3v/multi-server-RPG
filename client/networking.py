import common.consts
from typing import Tuple
from common.utils import parse, create_packet


def parse_server_message(packet: bytes) -> Tuple[list, list]:
    """
    Use: convert the packets bytes to a list of fields
    """
    # tools, valid pos, health, entities
    data = [*parse(common.consts.SERVER_HEADER_FORMAT, packet[:common.consts.SERVER_HEADER_SIZE])]


    # entities
    #print("client received ", data)
    num_of_entities = data[-1]
    if num_of_entities == 0:
        return (data, [])

    entity_locations_raw = parse(common.consts.MESSAGE_ENDIANESS + common.consts.POSITION_FORMAT * num_of_entities,
                                 packet[common.consts.SERVER_HEADER_SIZE: common.consts.SERVER_HEADER_SIZE + num_of_entities * 2 * common.consts.INT_SIZE])

    if entity_locations_raw:
        entity_locations = [(entity_locations_raw[i], entity_locations_raw[i + 1])
                            for i in range(0, len(entity_locations_raw), 2)]

        return data, entity_locations


def generate_client_message(seqn: int, x: int, y: int, actions: list) -> bytes | None:
    """
    Use: generate the client message bytes by this format
    Format: [pos(x, y) + (new_msg || attack || attack_directiton || equipped_id )]
    """
    return create_packet(common.consts.CLIENT_FORMAT, [seqn, x, y, *actions])
