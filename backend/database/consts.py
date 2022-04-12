"""SqlDatabase configurations"""
SQL_TYPE = "mysql"
DB_PORT = 3306
DB_NAME = "users"
DB_USERNAME = "dummy"
DB_PASS = "dummyPass"

# Column Numbers
USERNAME_COL = 0
HASH_COL = 1
SALT_COL = 2
UUID_COL = 3

# SqlDatabase tables configurations
MAX_SIZE = 0xff
USERS_CREDENTIALS_TABLE = "users_creds"
PLAYER_STATS_TABLE = "players_stats"
CHAT_TABLE = "chat"
USER_TABLE = "users_info"
