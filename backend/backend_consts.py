
# SqlDatabase configurations
SQL_TYPE = "mysql"
DB_PORT = 3306
DB_NAME = "users"
DB_USERNAME = "dummy"


# SqlDatabase configurations
MAX_SIZE = 0xff
USERS_CREDENTIALS_TABLE = "users_creds"
PLAYER_STATS_TABLE = "players_stats"
CHAT_TABLE = "chat"

# Column Numbers
USERNAME_COL = 0
HASH_COL = 1
SALT_COL = 2

# Scrypt Consts
SCRYPT_KEY_LENGTH = 32
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
