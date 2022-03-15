import struct
from typing import Tuple

from common.consts import CLIENT_FORMAT


def parse(parse_format: str, data: bytes) -> tuple | None:
    """
    Use: parse a given message by the given format
    """
    try:
        return struct.unpack(parse_format, data)
    except struct.error:
        return None


def generate_client_message(x: int, y: int) -> bytes:
    """
    Use: generate the client message bytes by this format
    Format: [ pos(x, y) + (new_msg || attack || attack_directiton || pick_up || equipped_id) ]
    """
    return struct.pack(CLIENT_FORMAT, x, y)


def encode_entity_locations_for_player(entities: dict, player_pos: Tuple[int, int]) -> bytes | None:
    """
    Use: generate the client message bytes by this format.
    Format: [entities in range + HP + invalid operation]
    """
    msg_format = "l" + "ll" * len(entities)
    # converts list of tuples into a list
    entities_pos = [item for t in filter(lambda val: entities.get(val) != player_pos, entities.values()) for item in t]
    try:
        return struct.pack(msg_format, len(entities), *entities_pos)
    except Exception:
        return None
