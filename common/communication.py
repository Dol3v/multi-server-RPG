import hmac
import logging
import socket
import sys
from datetime import datetime
from enum import IntEnum, auto
# to import from a dir
from typing import NamedTuple, Optional

from consts import *

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
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()


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
