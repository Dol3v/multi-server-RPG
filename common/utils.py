"""Some useful common utils"""
import base64
import math
import re
import socket
import struct
from typing import Iterable, Tuple

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey, generate_private_key, \
    EllipticCurvePublicKey, ECDH
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from common.consts import ELLIPTIC_CURVE, SHARED_KEY_SIZE, Pos, MESSAGE_ENDIANESS


def enter_ip(enter_string: str):
    """enter ip only if valid"""
    ip = input(enter_string)
    while not valid_ip(ip):
        ip = input(enter_string)
    return ip


def get_random_port():
    """Find a free port for the client"""
    sock = socket.socket()
    sock.bind(('', 0))
    free_port = sock.getsockname()[1]
    sock.close()
    return free_port


def parse(parse_format: str, data: bytes) -> tuple | None:
    """parse a given message by the given format"""
    try:
        return struct.unpack(parse_format, data)
    except struct.error as error:
        print(error)
        return None


def valid_ip(ip: str):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def flatten(iterable: Iterable) -> list:
    """
    Flattens an iterable of iterables (list of tuples, for instance) to a shallow list in the expected way.
    **Example**
    flatten([(1, 3), (2, 4 ,5)]) = [1, 3, 2, 4, 5]
    :param iterable: iterable to flatten
    """
    return list(sum(iterable, ()))


def normalize_vec(x, y) -> Tuple[float, float]:
    factor = math.sqrt(x ** 2 + y ** 2)
    if factor == 0:
        return 0, 0
    return x / factor, y / factor


def base64_encode(raw: bytes, str_encoding="utf-8") -> str:
    """Encodes raw byte data to str using base64 format."""
    base64_bytes = base64.b64encode(raw)
    return base64_bytes.decode(str_encoding)


def base64_decode(data: str, str_encoding="utf-8") -> bytes:
    base64_bytes = data.encode(str_encoding)
    return base64.b64decode(base64_bytes)


def is_valid_ip(ip: str) -> bool:
    return bool(re.match(r"^((\d|\d\d|1\d\d|2[0-5]{2})\.){3}(\d|\d\d|1\d\d|2[0-5]{2})$", ip))


def send_public_key(conn: socket.socket) -> EllipticCurvePrivateKey:
    """Generates a private key, sends its matching public key
     and returns the generated private key, together with any other data the server had sent.

     :param conn: TCP connection
    """
    private_key = generate_private_key(ELLIPTIC_CURVE)
    conn.send(private_key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint))
    return private_key


def deserialize_public_key(key_material: bytes) -> EllipticCurvePublicKey:
    return EllipticCurvePublicKey.from_encoded_point(
        curve=ELLIPTIC_CURVE, data=key_material)


def get_shared_key(private_key: EllipticCurvePrivateKey, peer_public_key: EllipticCurvePublicKey) -> bytes:
    """Returns shared, derived key from the private key and the peer's public key."""
    shared = private_key.exchange(ECDH(), peer_public_key)
    derived = HKDF(algorithm=SHA256(), length=SHARED_KEY_SIZE, salt=None, info=b"handshake data").derive(shared)
    return derived


def get_bounding_box(pos: Pos, height: int, width: int) -> Tuple[int, int, int, int]:
    return pos[0] - width // 2, pos[1] - height // 2, pos[0] + width // 2, pos[1] + height // 2


def serialize_ip(ip: str) -> bytes:
    return socket.inet_aton(ip)


def deserialize_addr(addr_bytes: bytes) -> Tuple[str, int]:
    components = struct.unpack(MESSAGE_ENDIANESS + "4Bl", addr_bytes)
    return "".join(str(ip_byte) + "." for ip_byte in components[:-1])[:-1], components[-1]


def is_empty(iterable) -> bool:
    return next(iterable, None) is None
