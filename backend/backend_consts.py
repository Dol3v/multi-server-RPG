from common.consts import SWORD, AXE, BOW, INVENTORY_ROWS, INVENTORY_COLUMNS

# Scrypt Consts
SCRYPT_KEY_LENGTH = 32
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1

ARM_LENGTH_MULTIPLIER = 10

# Game consts
ATTACK_BBOX_LENGTH = 100
WEAPON_DATA = {
    SWORD: {'cooldown': 50, 'damage': 15, 'melee_attack_range': 100, 'is_melee': True},
    AXE: {'cooldown': 75, 'damage': 30, 'melee_attack_range': 150, 'is_melee': True},
    BOW: {'cooldown': 100, 'damage': 45, 'is_melee': False}
}
FRAME_TIME = 1 / 60
MAX_SLOT = INVENTORY_ROWS * INVENTORY_COLUMNS - 1
AFK_THRESHOLD_SECS = 6.5

# Server communication ports
ROOT_SERVER2SERVER_PORT = 35000

# other
MOB_SIGHT_WIDTH = 700
MOB_SIGHT_HEIGHT = 700
MOB_ERROR_TERM = 30
RANGED_OFFSET = 270
