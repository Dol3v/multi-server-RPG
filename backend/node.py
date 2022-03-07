import socket
from dataclasses import dataclass
from enum import Enum, auto
from selectors import DefaultSelector, SelectorKey, EVENT_READ, EVENT_WRITE
from typing import List

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey, generate_private_key, \
    EllipticCurvePublicKey, ECDH
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from authentication import *
from backend.player import Player
from common.communication import recv, PacketID, PacketInfo, send_status, send
from common.consts import ELLIPTIC_CURVE, COMPRESSED_POINT_SIZE, SHARED_KEY_SIZE, SERVER_IP, SERVER_PORT

sel = DefaultSelector()
hkdf = HKDF(algorithm=SHA256(), length=SHARED_KEY_SIZE, salt=None, info=b"handshake data")
players = []


class ConnectionState(Enum):
    WAITING_FOR_DH = auto()
    CLIENT_RECEIVED_KEY = auto()
    SERVER_RECEIVED_KEY = auto()
    # and signup
    WAITING_FOR_LOGIN = auto()
    WAITING_FOR_LOGIN_CONFIRM = auto()
    # basically default afterwards
    CONNECTION_UP = auto()


@dataclass
class ConnectionData:
    shared_key: bytes
    private_key: EllipticCurvePrivateKey
    player: Player | None
    state: ConnectionState
    send_list: List[tuple[PacketID, bytes]]


def handle_signup_request(data: ConnectionData, conn: socket.socket, db: SqlDatabase):
    """Handles sign up. If successful, adds the player's creds to the database, adds a player object to players,
    and adds SERVER_OK to send_list. Else, it adds SERVER_NOK."""
    username, password = recv_credentials(conn, data.shared_key)
    result, error_msg = signup(username, password, db)
    if result:
        data.send_list.append((PacketID.SERVER_OK, bytes()))
        data.player.username = username
        players.append(data.player)
    else:
        data.send_list.append((PacketID.SERVER_NOK, bytes()))


def accept(server_sock: socket.socket):
    conn, addr = server_sock.accept()
    conn.setblocking(False)
    logging.info(f"Client {addr} joined")
    sel.register(conn, EVENT_READ | EVENT_WRITE, data=ConnectionData(
        bytes(), generate_private_key(ELLIPTIC_CURVE), Player(), ConnectionState.WAITING_FOR_DH, []))


def handle_movement(state: ConnectionState, conn: socket.socket):
    pass


def serve(key: SelectorKey, mask: int):
    conn: socket.socket = key.fileobj
    data = key.data
    if mask & EVENT_READ:
        if data.state == ConnectionState.WAITING_FOR_DH or data.state == ConnectionState.CLIENT_RECEIVED_KEY:
            # receive client public key, and create shared-derived key from it
            peer_public_key = EllipticCurvePublicKey.from_encoded_point(
                curve=ELLIPTIC_CURVE, data=conn.recv(COMPRESSED_POINT_SIZE))
            shared = data.private_key.exchange(ECDH(), peer_public_key)
            data.shared_key = hkdf.derive(shared)
            # state update
            data.state = ConnectionState.WAITING_FOR_LOGIN \
                if data.state == ConnectionState.CLIENT_RECEIVED_KEY else ConnectionState.SERVER_RECEIVED_KEY

        elif data.state == ConnectionState.WAITING_FOR_LOGIN:
            recv_credentials(conn, data.shared_key)

        elif data.state == ConnectionState.CONNECTION_UP:
            # connection is up, we can receive data and handle it accordingly
            info = recv(conn, data.shared_key)
            if not info:
                logging.critical(f"Could not receive data from {conn=}")
            else:
                match info.packet_type:
                    case PacketID.MOVE_DOWN | PacketID.MOVE_UP | PacketID.MOVE_LEFT | PacketID.MOVE_RIGHT:
                        handle_movement(data.state, conn)

    if mask & EVENT_WRITE:
        if data.state == ConnectionState.WAITING_FOR_DH or data.state == ConnectionState.SERVER_RECEIVED_KEY:
            # send server's public key
            conn.send(data.private_key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint))
            # state update
            data.state = ConnectionState.WAITING_FOR_LOGIN \
                if data.state == ConnectionState.SERVER_RECEIVED_KEY else ConnectionState.CLIENT_RECEIVED_KEY
        elif len(data.send_list) != 0:
            send()


if __name__ == "__main__":
    with SqlDatabase("127.0.0.1", "dummyPass") as database, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # initialization stuff
        database.write_tables()
        sock.bind((SERVER_IP, SERVER_PORT))
        print(sock)
        sock.listen()
        sock.setblocking(False)
        sel.register(sock, EVENT_READ, data=None)
        # listening loop
        try:
            while True:
                for key, mask in sel.select(timeout=None):
                    print(mask, f"{EVENT_WRITE=}", f"{EVENT_READ=}")
                    if key.data is None:
                        accept(key.fileobj)
                    else:
                        serve(key, mask)
        except KeyboardInterrupt:
            print("Bye byte")
        finally:
            sel.close()
