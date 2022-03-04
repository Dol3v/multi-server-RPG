"""Socket-Communication API"""

import hmac
import logging
from datetime import datetime
from enum import IntEnum
from socket import socket
from typing import NamedTuple

from cryptography.hazmat.primitives.asymmetric.ec import (
    generate_private_key,
    ECDH,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from common.consts import *


class PacketID(IntEnum):
    """Packet IDs"""

    GENERAL_DATA = 0
    INITIAL_AUTH = 1

    # Client actions
    CLIENT_ACTION = 2  # action with different clients
    ITEM_ACTION = 3  # action with items (like swords and stuff)

    # Server success response for requests
    CONFIRMED_STATUS = 4

    # User Movement
    MOVE_UP = ord("w")
    MOVE_DOWN = ord("s")
    MOVE_LEFT = ord("a")
    MOVE_RIGHT = ord("d")


class PacketInfo(NamedTuple):
    """Info relevant to a packet: the packet's type, the time it was sent, and its contents"""

    packet_type: PacketID
    time_sent: datetime
    content: bytes


class DefaultConnection:
    """Connection object, that supports send-n-recv functions with ECDH, hmacs, and replay/MITM attack protection.
    
    Usage example:
    `with Connection(sock) as conn:
        conn.send(b'Hello World!', PacketID.GENERAL_DATA)
        print(conn.recv())`
    """

    def __init__(self, conn: socket) -> None:
        self.conn = conn  # FIXME: add SYN attack protection (prob some sort of mini firewall thingy)
        self.key = self.get_shared_key(conn)

    def send(self, content: bytes, type: PacketID):
        encoded_time = int(datetime.now().timestamp() * 1000).to_bytes(TIMESTAMP_SIZE, "big")
        header = (
                int(type).to_bytes(TYPE_SIZE, "big")
                + len(content).to_bytes(CONTENT_LENGTH_SIZE, "big")
                + encoded_time
        )
        data = header + content
        self.conn.sendall(hmac.digest(self.key, data, "md5") + data)

    def recv(self) -> PacketInfo:
        header = self.conn.recv(HEADER_SIZE)
        msg_hmac, header = header[:HMAC_SIZE], header[HMAC_SIZE:]
        try:
            packet_type, content_length, time_stamp = (
                PacketID(header[TYPE_OFFSET]),
                int.from_bytes(header[LENGTH_OFFSET:TIMESTAMP_OFFSET], "big"),
                datetime.fromtimestamp(int.from_bytes(header[TIMESTAMP_OFFSET:], "big") / 1000),
            )
        except Exception:
            logging.warning(
                f"Invalid header was given to socket {self.conn}", exc_info=True
            )
            return None
        content = self.conn.recv(content_length)
        if not hmac.compare_digest(
                msg_hmac, hmac.digest(self.key, header + content, "md5")
        ):
            logging.critical(
                f"HMACs doesn't match in message given to {self.conn}: {content=},{time_stamp=},{content_length=},"
                f"{packet_type=},{msg_hmac=}"
            )
            self.__exit__(None, None, None)
            return None
        return PacketInfo(packet_type, time_stamp, content)

    @staticmethod
    def get_shared_key(conn: socket) -> bytes:
        """
        Uses ECDH to get a shared key between the client and the server.

        :param conn: socket connection with peer
        :type conn: socket
        :return: shared & derived key
        :rtype: bytes
        """
        private_key = generate_private_key(ELLIPTIC_CURVE)
        conn.send(
            private_key.public_key().public_bytes(
                Encoding.X962, PublicFormat.CompressedPoint
            )
        )
        peer_public_key = EllipticCurvePublicKey.from_encoded_point(
            curve=ELLIPTIC_CURVE, data=conn.recv(COMPRESSED_POINT_SIZE)
        )
        shared = private_key.exchange(ECDH(), peer_public_key)
        return HKDF(
            algorithm=SHA256(), length=SHARED_KEY_SIZE, salt=None, info=b"handshake data"
        ).derive(shared)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        logging.info(f"Closed connection {self.conn}. {exception_type=} {exception_value=} {exception_traceback=}")
        self.conn.close()
