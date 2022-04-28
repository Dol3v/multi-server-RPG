import abc
import dataclasses
import uuid as uuid
from dataclasses import dataclass, field
from typing import List

from cryptography.fernet import Fernet

from client.client_consts import INVENTORY_COLUMNS, INVENTORY_ROWS, HOTBAR_LENGTH
from common.consts import Pos, MAX_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT, Addr, Dir, \
    PROJECTILE_TTL, EntityType


@dataclass
class Entity(abc.ABC):
    kind: int
    pos: Pos = DEFAULT_POS_MARK
    direction: Dir = DEFAULT_DIR
    uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def serialize(self) -> dict:
        """Returns a dictionary encoding for a client all necessary data to know about an entity."""
        return {"type": self.kind,
                "pos": self.pos,
                "dir": self.direction,
                "uuid": self.uuid}


@dataclass
class Combatant(Entity):
    attacking_direction: Dir = DEFAULT_DIR
    is_attacking: bool = False
    last_time_attacked: float = -1
    current_cooldown: float = -1
    health: int = MAX_HEALTH

    def serialize(self) -> dict:
        return super().serialize() | {"is_attacking": self.is_attacking}


@dataclass
class Player(Combatant):
    new_message: str = ""
    incoming_message: str = ""  # List[str] = field(default_factory=lambda: [])
    addr: Addr = ("127.0.0.1", 10000)
    last_updated: int = -1  # latest sequence number basically
    slot: int = 0
    inventory: List[int] = field(default_factory=lambda: [SWORD, AXE, BOW] + [EMPTY_SLOT
                                 for _ in range(INVENTORY_COLUMNS * INVENTORY_ROWS - 3)])
    fernet: Fernet | None = None
    kind: int = EntityType.PLAYER

    @property
    def hotbar(self):
        return self.inventory[:HOTBAR_LENGTH]

    def serialize(self) -> dict:
        return super().serialize() | {"tool": self.hotbar[self.slot]}


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

    def serialize(self) -> dict:
        return super().serialize() | {"weapon": self.weapon}


ServerControlled = Projectile | Mob
"""Entity with server-controlled movements and actions"""
