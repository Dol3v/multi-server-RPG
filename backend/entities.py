import time
import uuid as uuid
from dataclasses import dataclass, field
from typing import List, Tuple

from cryptography.fernet import Fernet

from common.consts import Pos, MAX_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT, Addr, Dir, \
    CLIENT_HEIGHT, CLIENT_WIDTH, PROJECTILE_WIDTH, PROJECTILE_HEIGHT, BOT_WIDTH, BOT_HEIGHT


@dataclass
class Entity:
    pos: Pos = DEFAULT_POS_MARK
    direction: Dir = DEFAULT_DIR
    uuid: str = str(uuid.uuid4())
    width: int = -1
    height: int = -1


@dataclass
class Player(Entity):
    is_attacking: bool = False
    addr: Addr = ("127.0.0.1", 10000)
    last_updated: int = -1  # latest sequence number basically
    last_time_attacked: float = -1
    current_cooldown: float = -1
    health: int = MAX_HEALTH
    slot: int = 0
    tools: List = field(default_factory=lambda: [SWORD, AXE, BOW, EMPTY_SLOT, EMPTY_SLOT, EMPTY_SLOT])
    """
    [IDs]
        sword = 1
        axe = 2
        arrow = 3
    tools: [default, tool2, tool3]
    """
    fernet: Fernet = None
    width = CLIENT_WIDTH
    height = CLIENT_HEIGHT


@dataclass
class Projectile(Entity):
    damage: int = 0
    width = PROJECTILE_WIDTH
    height = PROJECTILE_HEIGHT


@dataclass
class Bot(Entity):
    health: int = MAX_HEALTH
    weapon: int = SWORD
    width = BOT_WIDTH
    height = BOT_HEIGHT


ServerControlled = Projectile | Bot
"""Entity with server-controlled movements and actions"""

Attackable = Bot | Player
"""Entity that can be attacked."""
