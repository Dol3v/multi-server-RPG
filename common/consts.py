"""General Common consts"""
import struct
import socket
from typing import Tuple
from enum import Enum

from cryptography.hazmat.primitives.asymmetric.ec import SECP384R1

UUID_SIZE = 36

# sizes of stuff
NUM_NODES = 1

# Useful graphics consts
CLIENT_HEIGHT = 60
CLIENT_WIDTH = 45

WORLD_HEIGHT = 675 * 64
WORLD_WIDTH = 240 * 64

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

PROJECTILE_HEIGHT = 68
PROJECTILE_WIDTH = 20

BOT_HEIGHT = 20
BOT_WIDTH = 20

# Types
Pos = Tuple[int, int]
Addr = Tuple[str, int]
Dir = Tuple[float, float]

# Server configurations
NODE_PORT = 42069
DEFAULT_NODE_IP = "127.0.0.1"
RECV_CHUNK = 1024
UDP_RECV_CHUNK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM).getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
THREADS_COUNT = 1
NODE_COUNT = 1

# Networking conventions
DEFAULT_POS_MARK = (-1, -1)
DEFAULT_DIR = (0.0, 0.0)
DEFAULT_ADDR = (DEFAULT_NODE_IP, -1)

# Useful player information
SPEED = 5
MAX_HEALTH = 100
MIN_HEALTH = 0
PROJECTILE_SPEED = 10
ARROW_OFFSET_FACTOR = 75

# Tools
EMPTY_SLOT = 0
SWORD = 1
AXE = 2
BOW = 3
MAHAK = 5
MIN_WEAPON_NUMBER = 1
MAX_WEAPON_NUMBER = 3


# Entity types
class EntityType(int, Enum):
    PLAYER = 0
    ARROW = 1
    MOB = 2
    OBSTACLE = 3


# ECDH Consts
COMPRESSED_POINT_SIZE = 49
ELLIPTIC_CURVE = SECP384R1()
SHARED_KEY_SIZE = 32

MOB_COUNT = 200
PROJECTILE_TTL = 120
# Some temporary consts
ROOT_IP = "127.0.0.1"
ROOT_PORT = 30000

# mob consts
MOB_SPEED = 2
