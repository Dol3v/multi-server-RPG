"""General consts for client side"""
# Images

from common.consts import EntityType

PLAYER_SIZE_MULTIPLIER = 3
PLAYER_IMG = "assets/idle_down.png"
HEALTH_BACKGROUND_IMG = "assets/health/health_background.png"
HEALTH_BAR_IMG = "assets/health/health_bar.png"
LOGIN_BACKGROUND = "assets/login_bg.png"
LOGIN_BUTTON_IMG = "assets/login_btn.png"
REGISTER_BACKGROUND = "assets/register_bg.png"
CONNECT_BUTTON_IMG = "assets/connect_btn.png"
REGISTER_BUTTON_IMG = "assets/register_btn.png"
TREE_IMG = "assets/tree.png"
SWORD_IMG = "assets/weapons/sword/full.png"

# Game data
GAME_NAME = "MMORPG Game"

FPS = 60
TILE_SIZE = 64

# General player data
SPEED = 5
ATTACK_COOLDOWN = 250
MAX_HEALTH = 100

weapon_data = {
    'sword': {"id": 1, "is_ranged": False, 'cooldown': 100, 'damage': 15, 'graphics': "assets/weapons/sword/full.png",
              "hand_position": (9, 45)},

    'axe': {"id": 2, "is_ranged": False, 'cooldown': 300, 'damage': 30, 'graphics': "assets/weapons/axe/full.png",
            "hand_position": (15, 40)},

    'bow': {"id": 3, "is_ranged": True, 'cooldown': 400, 'damage': 40, 'graphics': "assets/weapons/bow/full.png",
            "hand_position": (20, 15)},

    'potion': {"id": 4, "is_ranged": False, 'cooldown': 0, 'damage': 0, "hand_position": (10, 20)}
}

ENTITY_DATA = {
    # (texture, [animation], frame per second, size_multiplier
    EntityType.ARROW: ("entity/arrow/projectile.png", [], 10, 1),
    EntityType.MOB: ("entity/dino/lizard.png", ["entity/dino/lizard.png", "entity/dino/lizard_run_0.png",
                                          "entity/dino/lizard_run_1.png",
                                          "entity/dino/lizard_run_2.png", "entity/dino/lizard_run_3.png"], 1, 4),
    EntityType.PLAYER: ("character/knight/knight.png", ["character/knight/move_0.png",
                                                  "character/knight/move_1.png", "character/knight/move_2.png"],
                  10, PLAYER_SIZE_MULTIPLIER)
}

# Actions format
CHAT = 0
ATTACK = 2
ATTACK_DIR_X = 3
ATTACK_DIR_Y = 4
SELECTED_SLOT = 5
