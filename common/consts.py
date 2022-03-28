"""General Common consts"""
import struct
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.ec import SECP384R1

INT_SIZE = 4
# Format 
MESSAGE_ENDIANESS = "<"
SEQUENCE_FORMAT = 'q'
POSITION_FORMAT = 'll'
# [chat msg, attack, attack dir, equipped id]
ACTIONS_FORMAT = '255si?ffi'
CLIENT_FORMAT = MESSAGE_ENDIANESS + SEQUENCE_FORMAT + POSITION_FORMAT + ACTIONS_FORMAT

NUMBER_OF_POSITIONS_FORMAT = 'l'
TOOLS = 'iii'
HEALTH = 'i'
NEW_CHAT_MSG = '255s'
ENTITY_FORMAT = 'i' + POSITION_FORMAT + 'ff'
ENTITY_FIELD_NUM = 4
SERVER_HEADER_FORMAT = MESSAGE_ENDIANESS + TOOLS + NEW_CHAT_MSG + POSITION_FORMAT + HEALTH + NUMBER_OF_POSITIONS_FORMAT
SERVER_HEADER_SIZE = struct.calcsize(SERVER_HEADER_FORMAT)

# Useful graphics consts
CLIENT_HEIGHT = 64
CLIENT_WIDTH = 64

WORLD_HEIGHT = 20 * 64
WORLD_WIDTH = 20 * 64
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Types
Pos = Tuple[int, int]
Addr = Tuple[str, int]

# Server configurations
SERVER_PORT = 42069
SERVER_IP = "127.0.0.1"
RECV_CHUNK = 1024
THREADS_COUNT = 1

# Networking conventions
VALID_POS = (-1, -1)
DEFAULT_DIR = (0.0, 0.0)

# Useful player information
SPEED = 5
MAX_HEALTH = 100
MIN_HEALTH = 0

# Tools 
SWORD = 1
AXE = 2
BOW = 3

# ECDH Consts
COMPRESSED_POINT_SIZE = 49
ELLIPTIC_CURVE = SECP384R1()
SHARED_KEY_SIZE = 32

# Some temporary consts
ROOT_IP = "127.0.0.1"
ROOT_PORT = 30000
