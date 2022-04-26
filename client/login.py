"""Login/signup networking functions"""
import socket

from cryptography.fernet import Fernet

from common.consts import RECV_CHUNK, Addr
from common.utils import get_shared_key, deserialize_public_key, send_public_key, serialize_json


def do_ecdh(conn: socket.socket) -> bytes | None:
    """Does the client part of the ECDH algorithm, and returns the shared, derived key with the server.
    Assumes connection over TCP."""
    private_key = send_public_key(conn)
    server_serialized_key = conn.recv(RECV_CHUNK)
    if server_serialized_key is None:
        return None
    server_public_key = deserialize_public_key(server_serialized_key)
    return get_shared_key(private_key, server_public_key)


def send_credentials(username: str, password: str, conn: socket.socket, fernet: Fernet, client_game_addr: Addr,
                     is_login: bool = False):
    """Sends over a TCP connection the encrypted login data of a client: its username, password, and UDP game address.
    """
    conn.send(serialize_json({"username": username,
                              "password": password,
                              "game_addr": client_game_addr,
                              "is_login": is_login},
                             fernet))
