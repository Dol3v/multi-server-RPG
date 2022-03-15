CLIENT_FORMAT = 'll'
SERVER_FORMAT = 'll'
LONG_INT_SIZE = 4
from struct import *
import traceback

# Terms:
# CM -> Client Message
# SM -> Server Message

def parse(parse_format: str, data: bytes) -> tuple:
    """
    Use: parse a given message by the given format
    """
    try:
        return unpack(parse_format, data)
    except struct.error:
        return None

def gen_client_msg(x: int, y: int) -> bytes:
    """
    Use: generate the client message bytes by this format
    Format: [ pos(x, y) + (new_msg || attack || attack_directiton || pick_up || equipped_id) ]
    """
    return pack(CLIENT_FORMAT, x, y)


def gen_server_msg(entities: dict) -> bytes:
    """
    Use: generate the client message bytes by this format
    Format: [entities in range + HP + invalid operation]
    """
    msg_format = 'l' + SERVER_FORMAT * len(entities)
    

    print(msg_format)

    # converts list of tuples into a list
    entities_pos = [item for t in entities.values() for item in t]

    print(entities_pos)

    try:
        packet = pack(msg_format, len(entities), *entities_pos)
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return None


    
