import common.consts
from common.utils import parse, create_packet


def parse_server_message(packet: bytes) -> list | None:
    """
    Use: convert the packets bytes to a list of fields
    """
    num_of_entities = parse(common.consts.SERVER_HEADER_FORMAT, packet[:common.consts.INT_SIZE])[0]

    if num_of_entities == 0:
        return []

    entity_locations_raw = parse(common.consts.MESSAGE_ENDIANESS + common.consts.POSITION_FORMAT * num_of_entities,
                                 packet[common.consts.INT_SIZE: common.consts.INT_SIZE + num_of_entities * 2 * common.consts.INT_SIZE])

    if entity_locations_raw:
        entity_locations = [(entity_locations_raw[i], entity_locations_raw[i + 1])
                            for i in range(0, len(entity_locations_raw), 2)]
        return entity_locations


def generate_client_message(seqn: int, x: int, y: int) -> bytes | None:
    """
    Use: generate the client message bytes by this format
    Format: [pos(x, y) + (new_msg || attack || attack_directiton || pick_up || equipped_id)]
    """
    return create_packet(common.consts.CLIENT_FORMAT, [seqn, x, y])
