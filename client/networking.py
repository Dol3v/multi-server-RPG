"""Utils for communicating with the server"""
from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet

from common.consts import SERVER_HEADER_SIZE, SERVER_HEADER_FORMAT, MESSAGE_ENDIANESS, CLIENT_FORMAT, ENTITY_FORMAT, \
    RECV_CHUNK, ENTITY_NUM_OF_FIELDS, REDIRECT_FORMAT
from common.utils import *


def do_ecdh(conn: socket.socket) -> bytes | None:
    """Does the client part of the ECDH algorithm, and returns the shared, derived key with the server.
    Assumes connection over TCP."""
    private_key = send_public_key(conn)
    server_serialized_key = conn.recv(RECV_CHUNK)
    if server_serialized_key is None:
        return None
    server_public_key = deserialize_public_key(server_serialized_key)
    return get_shared_key(private_key, server_public_key)


def send_credentials(username: str, password: str, conn: socket.socket, shared_key: bytes, is_login: bool = False):
    """
    Use: login to the server
    """
    print(f"len={len(shared_key)}, {shared_key=}, urlsafe={urlsafe_b64encode(shared_key) == shared_key}")
    fernet = Fernet(urlsafe_b64encode(shared_key))
    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())
    conn.send(int(is_login).to_bytes(1, "big") + username_token + password_token)
    return fernet


def get_login_response(conn: socket.socket) -> Tuple[str, str, bool, str]:
    user_uuid, ip, success, msg_length = struct.unpack(REDIRECT_FORMAT, conn.recv(struct.calcsize(REDIRECT_FORMAT)))
    return ip.decode().rstrip("\x00"), user_uuid.decode(), success, conn.recv(msg_length).decode()


def parse_server_message(packet: bytes) -> Tuple[Tuple, list]:
    """
    Use: convert the packets bytes to a list of fields.
    """
    # tools, new_chat, valid player_pos, health
    player_status = parse(SERVER_HEADER_FORMAT, packet[:SERVER_HEADER_SIZE])

    if not player_status:
        return (), []
    # players
    num_of_entities = player_status[-1]
    player_status = player_status[:-1]

    if num_of_entities == 0:
        return player_status, []

    raw_entities = parse(MESSAGE_ENDIANESS + ENTITY_FORMAT * num_of_entities,  # Format
                         packet[SERVER_HEADER_SIZE: SERVER_HEADER_SIZE + num_of_entities * struct.calcsize(
                             ENTITY_FORMAT)])  # partition

    if raw_entities:
        entities = [
            (raw_entities[i], raw_entities[i + 1], (raw_entities[i + 2], raw_entities[i + 3]),
             (raw_entities[i + 4], raw_entities[i + 5]), raw_entities[i + 6])
            for i in range(0, len(raw_entities), ENTITY_NUM_OF_FIELDS)]

        return player_status, entities


def generate_client_message(player_uuid: str, seqn: int, x: int, y: int, actions: list, fernet: Fernet) -> bytes | None:
    """
    Use: generate the client message bytes by this format
    Format: [player_pos(x, y) + (new_msg || attack || attack_directiton || equipped_id )]
    """
    return player_uuid.encode() + fernet.encrypt(struct.pack(CLIENT_FORMAT, seqn, x, y, *actions))
