import abc
import dataclasses
import logging
import time
import uuid as uuid
from dataclasses import dataclass, field
from typing import List, Iterable, Type, Dict

from cryptography.fernet import Fernet

import backend.logic.entities_management as entities_management
from backend.backend_consts import FRAME_TIME
from client.client_consts import INVENTORY_COLUMNS, INVENTORY_ROWS
from common.consts import Pos, MAX_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT, Addr, Dir, \
    PROJECTILE_TTL, EntityType, MIN_HEALTH, ARROW_OFFSET_FACTOR, PROJECTILE_HEIGHT, PROJECTILE_WIDTH, MAHAK


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


class CanHit(abc.ABC):
    """An interface for game objects that can hit others, such as weapons and projectiles."""

    @abc.abstractmethod
    def on_hit(self, hit_objects: Iterable[Entity], manager: entities_management.EntityManager):
        """Handles a hit between self and other objects.

        :param hit_objects: objects that were hit by self
        :param manager: entity manager"""
        ...


# class TickInfo(NamedTuple):
#     """Info describing events that occurred to a server-controlled entity during a tick."""
#     should_remove: bool


class ServerControlled(Entity, abc.ABC):
    """An abstract class for server controlled objects, i.e., objects with server-controlled
    movement and general behaviour such as mobs and projectiles."""

    @abc.abstractmethod
    def advance_per_tick(self, manager: entities_management.EntityManager) -> bool:
        """Advances the object per game tick: calculates collisions and updates stats locally (not in the manager).

        :returns: whether the entity should be removed from the game"""
        ...


@dataclass
class Item:
    """An in-game item"""
    type: int

    def on_click(self, clicked_by: Entity, manager: entities_management.EntityManager):
        """Handles a click on the item.

        :param clicked_by: entity who clicked on the item
        :param manager: entity manager"""
        ...


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
class Weapon(Item):
    """An in-game weapon."""
    cooldown: int
    damage: int

    def on_click(self, clicked_by: Combatant, manager: entities_management.EntityManager):
        self.use_to_attack(clicked_by, manager)
        clicked_by.last_time_attacked = time.time()
        clicked_by.current_cooldown = self.cooldown * FRAME_TIME

    @abc.abstractmethod
    def use_to_attack(self, attacker: Combatant, manager: entities_management.EntityManager):
        """Attack using this weapon."""
        ...


@dataclass
class MeleeWeapon(Weapon):
    melee_attack_range: int

    def use_to_attack(self, attacker: Combatant, manager: entities_management.EntityManager):
        in_range = manager.entities_in_melee_attack_range(attacker, self.melee_attack_range)
        for kind, attackable in in_range:
            if kind == EntityType.MOB == attackable.kind:
                continue  # mobs shouldn't attack mobs
            attackable.health -= self.damage
            if attackable.health <= MIN_HEALTH:
                manager.remove_entity(attackable, kind)
                logging.info(f"killed {attackable=}")
            logging.info(f"updated entity health to {attackable.health}")


@dataclass
class Projectile(ServerControlled, CanHit):
    damage: int = 0
    ttl: int = PROJECTILE_TTL
    kind: int = EntityType.ARROW
    width: int = PROJECTILE_WIDTH
    height: int = PROJECTILE_HEIGHT

    def advance_per_tick(self, manager: entities_management.EntityManager) -> bool:
        pass

    def on_hit(self, hit_objects: Iterable[Entity], manager: entities_management.EntityManager):
        pass


@dataclass
class RangedWeapon(Weapon):
    projectile_class: Type[Projectile]
    """Projectile type to be shot. Can be any class which inherits from `Projectile`."""

    def use_to_attack(self, attacker: Combatant, manager: entities_management.EntityManager):
        projectile = self.projectile_class(
            pos=(int(attacker.pos[0] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[0]),
                 int(attacker.pos[1] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[1])))
        manager.add_entity(projectile.kind, projectile.uuid, projectile.pos, projectile.height,
                           projectile.width)
        with manager.projectile_lock:
            manager.projectiles[projectile.uuid] = projectile
            logging.info(f"added projectile {projectile}")


_item_pool: Dict[int, Item] = {
    SWORD: MeleeWeapon(type=SWORD, cooldown=100, damage=15, melee_attack_range=100),
    AXE: MeleeWeapon(type=SWORD, cooldown=300, damage=40, melee_attack_range=150),
    BOW: RangedWeapon(type=BOW, cooldown=400, damage=30, projectile_class=Projectile),
    MAHAK: RangedWeapon(type=MAHAK, cooldown=200, damage=100, projectile_class=Projectile)
}


def get_item(kind: int) -> Item:
    return _item_pool[kind]


@dataclass
class Player(Combatant):
    new_message: str = ""
    incoming_message: str = ""  # List[str] = field(default_factory=lambda: [])
    addr: Addr = ("127.0.0.1", 10000)
    last_updated: int = -1  # latest sequence number basically
    slot: int = 0
    inventory: List[int] = field(default_factory=lambda: [SWORD, AXE, BOW] + [EMPTY_SLOT
                                                                              for _ in range(
            INVENTORY_COLUMNS * INVENTORY_ROWS - 3)])
    fernet: Fernet | None = None
    kind: int = EntityType.PLAYER

    @property
    def item(self) -> Item:
        return get_item(self.inventory[self.slot])

    def serialize(self) -> dict:
        return super().serialize() | {"tool": self.inventory[self.slot]}


@dataclass
class Mob(Combatant, ServerControlled, CanHit):
    weapon: int = SWORD
    on_player: bool = False
    kind: int = EntityType.MOB

    @property
    def item(self) -> Item:
        return get_item(self.weapon)

    def serialize(self) -> dict:
        return super().serialize() | {"weapon": self.weapon}

    def advance_per_tick(self, manager: entities_management.EntityManager) -> bool:
        pass

    def on_hit(self, hit_objects: Iterable[Entity], manager: entities_management.EntityManager):
        pass
