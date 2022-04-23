"""Login/signup networking functions"""
import socket
import struct
from base64 import urlsafe_b64encode
from typing import Any

from cryptography.fernet import Fernet

from common.consts import REDIRECT_FORMAT, RECV_CHUNK, Addr
from common.utils import serialize_ip, get_shared_key, deserialize_public_key, send_public_key


def do_ecdh(conn: socket.socket) -> bytes | None:
    """Does the client part of the ECDH algorithm, and returns the shared, derived key with the server.
    Assumes connection over TCP."""
    private_key = send_public_key(conn)
    server_serialized_key = conn.recv(RECV_CHUNK)
    if server_serialized_key is None:
        return None
    server_public_key = deserialize_public_key(server_serialized_key)
    return get_shared_key(private_key, server_public_key)


def send_credentials(username: str, password: str, conn: socket.socket, shared_key: bytes, client_game_addr: Addr,
                     is_login: bool = False):
    """sends shared key username password ip and """
    fernet = Fernet(urlsafe_b64encode(shared_key))
    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())
    print(client_game_addr[0])
    print(client_game_addr[1])
    conn.send(serialize_ip(client_game_addr[0]) + struct.pack(">l?", client_game_addr[1], is_login) +
              username_token + password_token)
    return fernet


def get_login_response(conn: socket.socket) -> tuple[Any, Any, Any, Any, str]:
    user_uuid, *initial_pos, ip, success, msg_length = struct.unpack(REDIRECT_FORMAT,
                                                                     conn.recv(struct.calcsize(REDIRECT_FORMAT)))
    return ip.decode().rstrip("\x00"), initial_pos, user_uuid.decode(), success, conn.recv(msg_length).decode()