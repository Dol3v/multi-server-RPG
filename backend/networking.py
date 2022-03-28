import socket
import struct

from common.consts import CLIENT_FORMAT, SERVER_HEADER_FORMAT, Pos, ENTITY_FORMAT, ENTITY_DATA_SIZE, RECV_CHUNK
from common.utils import parse, send_public_key, get_shared_key, deserialize_public_key


def do_ecdh(conn: socket.socket) -> None | bytes:
    """Does the server part of ECDH, and returns the shared key."""
    client_key = conn.recv(RECV_CHUNK)
    try:
        client_public_key = deserialize_public_key(client_key)
    except ValueError:
        return None
    private_key = send_public_key(conn)
    return get_shared_key(private_key, client_public_key)


def parse_client_message(packet: bytes) -> tuple | None:
    """
    Use: convert the packets bytes to a list of fields
    """
    return parse(CLIENT_FORMAT, packet)


def generate_server_message(tools: list, new_msg: str, last_valid_pos: Pos, health: int,
                            entities_in_range: list) -> bytes | None:
    """
    Use: creates the server update message
    Format: [tools + new_msg + last valid pos + HP + entities in range]
    NOTE: the first tool inside the tools will be the equipped one. 
    """
    data = []
    entities_count = len(entities_in_range) // ENTITY_DATA_SIZE
    # # create data array
    data += tools
    data.append(new_msg.encode())
    data += [*last_valid_pos]
    data.append(health)
    data.append(entities_count)
    data += entities_in_range
    packet_format = SERVER_HEADER_FORMAT + ENTITY_FORMAT * entities_count
    return struct.pack(packet_format, *data)
