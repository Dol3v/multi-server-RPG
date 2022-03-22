from typing import Tuple

# Format 
MESSAGE_ENDIANESS = "<"
SEQUENCE_FORMAT = 'l'
POSITION_FORMAT = 'll'
CLIENT_FORMAT = MESSAGE_ENDIANESS + SEQUENCE_FORMAT + POSITION_FORMAT

NUMBER_OF_POSITIONS_FORMAT = 'l'
SERVER_HEADER_FORMAT = MESSAGE_ENDIANESS + NUMBER_OF_POSITIONS_FORMAT
INT_SIZE = 4

# Useful graphics consts
CLIENT_HEIGHT = 64
CLIENT_WIDTH = 64

# Types
Pos = Tuple[int, int]


# Server configurations
SERVER_PORT = 42069
SERVER_IP = "127.0.0.1"
RECV_CHUNK = 1024
THREADS_COUNT = 1

# Useful player information
SPEED = 5
