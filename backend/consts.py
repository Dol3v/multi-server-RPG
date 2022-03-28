# SqlDatabase configurations
from common.consts import SWORD, AXE, BOW

SQL_TYPE = "mysql"
DB_PORT = 3306
DB_NAME = "users"
DB_USERNAME = "dummy"

# Column Numbers
USERNAME_COL = 0
HASH_COL = 1
SALT_COL = 2

# Scrypt Consts
SCRYPT_KEY_LENGTH = 32
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1


# SqlDatabase tables configurations
MAX_SIZE = 0xff
USERS_CREDENTIALS_TABLE = "users_creds"
PLAYER_STATS_TABLE = "players_stats"
CHAT_TABLE = "chat"

# Fernet Consts
FERNET_TOKEN_LENGTH = 100
CREDENTIALS_PACKET_SIZE = 1 + 2 * FERNET_TOKEN_LENGTH

# Entity Consts
TYPE_PLAYER = 0

# Game consts
ATTACK_BBOX_LENGTH = 100
WEAPON_DATA = {
    SWORD: {'cooldown': 100, 'damage': 15, 'melee_attack_range': 70, 'is_melee': True},
    AXE: {'cooldown': 300, 'damage': 30, 'melee_attack_range': 100, 'is_melee': True},
    BOW: {'cooldown': 400, 'damage': 45, 'is_melee': False}
}

