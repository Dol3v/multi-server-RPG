"""General constants"""
from cryptography.hazmat.primitives.asymmetric.ec import SECP384R1

# Packet structure consts, sizes in bytes
SHARED_KEY_SIZE = 32
HMAC_SIZE = 16
TYPE_SIZE = 1
CONTENT_LENGTH_SIZE = 2
TIMESTAMP_SIZE = 8

TYPE_OFFSET = 0
LENGTH_OFFSET = TYPE_OFFSET + TYPE_SIZE
TIMESTAMP_OFFSET = LENGTH_OFFSET + CONTENT_LENGTH_SIZE

HEADER_SIZE = HMAC_SIZE + TYPE_SIZE + CONTENT_LENGTH_SIZE + TIMESTAMP_SIZE

# ECDH Consts
COMPRESSED_POINT_SIZE = 49
ELLIPTIC_CURVE = SECP384R1()

# Comms constants
SERVER_IP = "127.0.0.1"
SERVER_PORT = 10001
