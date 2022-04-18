import dataclasses
import uuid as uuid
from dataclasses import dataclass, field
from typing import List

from cryptography.fernet import Fernet

from common.consts import Pos, MAX_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT, Addr, Dir, \
    PROJECTILE_TTL, EntityType


@dataclass
class Entity:
    kind: int
    pos: Pos = DEFAULT_POS_MARK
    direction: Dir = DEFAULT_DIR
    uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Combatant(Entity):
    attacking_direction: Dir = DEFAULT_DIR

    is_attacking: bool = False
    last_time_attacked: float = -1
    current_cooldown: float = -1
    health: int = MAX_HEALTH


@dataclass
class Player(Combatant):
    new_message: str = ""
    incoming_message: str = ""  # List[str] = field(default_factory=lambda: [])
    addr: Addr = ("127.0.0.1", 10000)
    last_updated: int = -1  # latest sequence number basically
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
    kind: int = EntityType.PLAYER


@dataclass
class Projectile(Entity):
    damage: int = 0
    ttl: int = PROJECTILE_TTL
    kind: int = EntityType.ARROW

@dataclass
class Mob(Combatant):
    weapon: int = SWORD
    on_player: bool = False
    kind: int = EntityType.MOB

ServerControlled = Projectile | Mob
"""Entity with server-controlled movements and actions"""
