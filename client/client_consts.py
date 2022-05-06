"""General consts for client side"""
# Images

from common.consts import EntityType, INVENTORY_COLUMNS

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
SWORD_IMG = "assets/items/sword/full.png"

# general game data
GAME_NAME = "MMORPG Game"

FPS = 60
TILE_SIZE = 64

# general player data
SPEED = 5
ATTACK_COOLDOWN = 250
MAX_HEALTH = 100

# inventory data
INVENTORY_SIZE_MULTIPLIER = 3
ICON_SIZE = 16 * INVENTORY_SIZE_MULTIPLIER

HOTBAR_LENGTH = INVENTORY_COLUMNS

# weapon data
weapon_data = {
    'sword':
        {
            "id": 1, "is_ranged": False, 'cooldown': 25, 'damage': 15, 'graphics': "assets/items/sword/full.png",
            'icon': "assets/items/sword/full.png",
            "resize_icon": False,
            "hand_position": (9, 45), "size_multiplier": 1,
            "display_name": ("Sword", (255, 255, 255), False),  # (item_name, color, is_bold)
            "description":
                ["This is a regular sword", "You use it to kill or smth"]
        },

    'axe':
        {
            "id": 2, "is_ranged": False, 'cooldown': 50, 'damage': 30, 'graphics': "assets/items/axe/full.png",
            'icon': "assets/items/axe/full.png",
            "resize_icon": True,
            "hand_position": (15, 40), "size_multiplier": 1,
            "display_name": ("Axe", (255, 255, 255), False),
            "description":
                ["This is a regular axe", "Nothing interesting here"]
        },

    'bow':
        {
            "id": 3, "is_ranged": True, 'cooldown': 100, 'damage': 40, 'graphics': "assets/items/bow/full.png",
            'icon': "assets/items/bow/full.png",
            "resize_icon": True,
            "hand_position": (20, 15), "size_multiplier": 1,
            "display_name": ("Bow", (255, 255, 255), False),
            "description":
                ["This is a regular bow", "It can go pew pew and shoot arrows"]
        },

    'health_potion':
        {
            "id": 4, "is_ranged": False, 'cooldown': 0, 'damage': 0, "hand_position": (10, 20),
            'graphics': "assets/items/health_potion/full.png",
            'icon': "assets/items/health_potion/full.png",
            "resize_icon": True,
            "size_multiplier": 3,
            "display_name": ("Health Potion", (255, 51, 51), False),
            "description":
                ["A regular health potion", "Basically go slurp and get some health"]
        },

    "shmulik_mahak":
        {
            "id": 5, "is_ranged": False, 'cooldown': 200, 'damage': 100, "hand_position": (25, 50),
            'graphics': "assets/items/mahak/mahak2.png",
            'icon': "assets/items/mahak/mahak2.png",
            "resize_icon": False,
            "size_multiplier": 3,
            "display_name": ("Shmulik's Eraser", (255, 215, 0), True),
            "description":
                ["This is an ancient legendary weapon", "that is used to kill gods",
                 "(or some kids in cyber class)"]
        },
    "fire_ball":
        {
            "id": 6, "is_ranged": False, 'cooldown': 200, 'damage': 100, "hand_position": (25, 50),
            'graphics': "assets/items/mahak/mahak2.png",
            'icon': "assets/items/mahak/mahak2.png",
            "display_name": ("Fireball", (255, 215, 0), True),
            "resize_icon": False,
            "size_multiplier": 1,
            "description":
                ["Your hands can shoot fireballs", "use this skill wisely",
                 "(or ...)"]
        }
}

ENTITY_DATA = {
    # (texture, [animation], frame per second, size_multiplier
    EntityType.PROJECTILE: ("entity/arrow/projectile.png", [], 10, 1),
    EntityType.MOB: ("entity/dino/lizard.png", ["entity/dino/lizard.png", "entity/dino/lizard_run_0.png",
                                                "entity/dino/lizard_run_1.png",
                                                "entity/dino/lizard_run_2.png", "entity/dino/lizard_run_3.png"], 1, 4),
    EntityType.PLAYER: ("character/knight/knight.png", ["character/knight/move_0.png",
                                                        "character/knight/move_1.png", "character/knight/move_2.png"],
                        10, PLAYER_SIZE_MULTIPLIER),
    EntityType.BAG: ("character/knight/knight.png", [], 10, PLAYER_SIZE_MULTIPLIER)
}

# Actions format
CHAT = 0
ATTACK = 2
ATTACK_DIR_X = 3
ATTACK_DIR_Y = 4
SELECTED_SLOT = 5
