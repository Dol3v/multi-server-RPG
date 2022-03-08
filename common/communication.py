import hmac
import logging
import socket
import sys
from datetime import datetime
from enum import IntEnum, auto
# to import from a dir
from typing import NamedTuple, Optional

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric.ec import generate_private_key, EllipticCurvePublicKey, ECDH
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from common.consts import *

sys.path.append('.')


class PacketID(IntEnum):
    """Packet IDs"""

    GENERAL_DATA = auto()
    INITIAL_AUTH = auto()
    SIGNUP = auto()
    LOGIN = auto()

    # Client actions
    CLIENT_ACTION = auto()  # action with different clients
    ITEM_ACTION = auto()  # action with items (like swords and stuff)

    # Server success response for requests
    SERVER_OK = auto()
    SERVER_NOK = auto()

    # User Movement
    USER_DIR = auto()


class PacketInfo(NamedTuple):
    """Info relevant to a packet: the packet's packet_id, the time it was sent, and its contents"""

    packet_type: PacketID
    time_sent: datetime
    content: bytes


def send(content: bytes, packet_id: PacketID, conn: socket.socket, key: bytes):
    """
    Use: send data with time stamp and shared key.

    Format: [hmac(header + data, key) + header + data]
    """
    encoded_time = int(datetime.now().timestamp() * 1000).to_bytes(TIMESTAMP_SIZE, "big")

    header = (
            int(packet_id).to_bytes(TYPE_SIZE, "big")
            + len(content).to_bytes(CONTENT_LENGTH_SIZE, "big")
            + encoded_time)

    data = header + content
    conn.sendall(hmac.digest(key, data, "md5") + data)


def recv(conn: socket.socket, key: bytes) -> Optional[PacketInfo]:
    """
    Use: recv data using the shared key in the format.

    Format: [hmac(header + data, key) + header + data]
    """
    header = conn.recv(HEADER_SIZE)
    msg_hmac, header = header[:HMAC_SIZE], header[HMAC_SIZE:]
    try:
        packet_type, content_length, time_stamp = (
            PacketID(header[TYPE_OFFSET]),
            int.from_bytes(header[LENGTH_OFFSET:TIMESTAMP_OFFSET], "big"),
            datetime.fromtimestamp(int.from_bytes(header[TIMESTAMP_OFFSET:], "big") / 1000),)

    except Exception:
        logging.warning(f"Invalid header was given to socket {conn}", exc_info=True)
        return None

    content = conn.recv(content_length)

    if not hmac.compare_digest(msg_hmac, hmac.digest(key, header + content, "md5")):
        logging.critical(
            f"HMACs doesn't match in message given to {conn}: {content=},{time_stamp=},{content_length=},"
            f"{packet_type=},{msg_hmac=}")

        return None

    return PacketInfo(packet_type, time_stamp, content)


def send_status(status: PacketID, conn: socket.socket, key: bytes):
    send(b"", status, conn, key)


def get_shared_key(conn: socket.socket) -> bytes:
    """
    Uses ECDH to get a shared key between the client and the server. Note: to be used only by the client

    :param conn: socket connection with peer
    :return: shared & derived key
    :rtype: bytes
    """
    # generate key set
    private_key = generate_private_key(ELLIPTIC_CURVE)

    # Send public key
    conn.send(private_key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint))

    # Receive public key of peer
    peer_public_key = EllipticCurvePublicKey.from_encoded_point(
        curve=ELLIPTIC_CURVE, data=conn.recv(COMPRESSED_POINT_SIZE))

    # Generate shared key and return it
    shared = private_key.exchange(ECDH(), peer_public_key)

    return HKDF(algorithm=SHA256(), length=SHARED_KEY_SIZE, salt=None, info=b"handshake data").derive(shared)