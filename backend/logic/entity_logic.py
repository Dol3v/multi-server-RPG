import abc
import dataclasses
import logging
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Tuple, Iterable, List, Type, Callable

import numpy as np
from cryptography.fernet import Fernet
from pyqtree import Index

from backend.backend_consts import FRAME_TIME, MOB_ERROR_TERM, MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT, RANGED_OFFSET
from client.client_consts import INVENTORY_COLUMNS, INVENTORY_ROWS
from common.consts import Pos, DEFAULT_POS_MARK, Dir, DEFAULT_DIR, EntityType, Addr, SWORD, AXE, BOW, EMPTY_SLOT, \
    PROJECTILE_TTL, PROJECTILE_HEIGHT, PROJECTILE_WIDTH, MAX_HEALTH, WORLD_WIDTH, WORLD_HEIGHT, MAHAK, MIN_HEALTH, \
    ARROW_OFFSET_FACTOR, MOB_SPEED, BOT_HEIGHT, BOT_WIDTH, CLIENT_HEIGHT, CLIENT_WIDTH
from common.utils import get_entity_bounding_box, get_bounding_box, normalize_vec


@dataclass
class Entity(abc.ABC):
    kind: EntityType
    pos: Pos = DEFAULT_POS_MARK
    direction: Dir = DEFAULT_DIR
    uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def serialize(self) -> dict:
        """Returns a dictionary encoding for a client all necessary data to know about an entity."""
        return {"type": self.kind,
                "pos": self.pos,
                "dir": self.direction,
                "uuid": self.uuid}


class EntityManager:
    """Use to control and access all game entities."""

    def __init__(self, spindex: Index):
        self._grouped_entities: Dict[EntityType, Dict[str, Entity]] = {}
        """Dictionary of entities ordered by type."""

        self.spindex = spindex
        """Quadtree for collision/range detection. Player keys are tuples `(type, uuid)`, with the type being
        projectile/player/mob, and the uuid being, well, the uuid."""

        self.mob_lock = threading.Lock()
        self.projectile_lock = threading.Lock()

    @property
    def players(self) -> dict:
        return self._grouped_entities.get(EntityType.PLAYER, {})

    @property
    def projectiles(self) -> dict:
        return self._grouped_entities.get(EntityType.PROJECTILE, {})

    @property
    def mobs(self) -> dict:
        return self._grouped_entities.get(EntityType.MOB, {})

    def get(self, entity_uuid: str, entity_kind: EntityType) -> Entity | None:
        return self._grouped_entities[entity_kind].get(entity_uuid, None)

    def pop(self, entity_uuid: str, entity_kind: EntityType) -> Entity:
        """Pops an element from the manager's dictionaries. Use with caution, as this doesn't remove
        the entity from the quadtree."""
        return self._grouped_entities[entity_kind].pop(entity_uuid)

    def add_to_dict(self, entity: Entity):
        """Adds am element to the manager's dictionaries. Use with caution, as this doesn't add it to the
        quadtree."""
        if not self._grouped_entities.get(entity.kind, None):
            self._grouped_entities[entity.kind] = {}
        self._grouped_entities[entity.kind][entity.uuid] = entity

    def get_collidables_with(self, pos: Pos, entity_uuid: str, *, kind: EntityType) -> Iterable[Tuple[EntityType, str]]:
        """Get all objects that collide with entity"""
        return filter(lambda data: data[1] != entity_uuid, self.spindex.intersect(
            get_entity_bounding_box(pos, kind)))

    def get_entities_in_range(self, bbox: Tuple[int, int, int, int], *,
                              entity_filter: Callable[[EntityType, str], bool] = lambda a, b: True) -> Iterable[Entity]:
        """Returns the entities in a given bounding box, for which ``entity_filter`` returns true.

        :param bbox: search rectangle, of format (x_min, y_min, x_max, y_max)
        :param entity_filter: filter function for entities, that takes a tuple of the entity
        :returns: an iterable containing all entities in a search rectangle of dimensions `height` and `width`, except
            the entity with uuid `entity_uuid`
        """
        return map(lambda data: self.get(data[1], data[0]),
                   filter(lambda data: entity_filter(*data) and data[0] != EntityType.OBSTACLE, self.spindex.intersect(
                       bbox
                   )))

    def update_entity_location(self, entity: Entity, new_location: Pos, kind: int):
        # logging.debug(f"[debug] updating entity uuid={entity.uuid} of {kind=} to {new_location=}")
        self.spindex.remove((kind, entity.uuid), get_entity_bounding_box(entity.pos, kind))
        entity.pos = new_location
        self._grouped_entities[entity.kind][entity.uuid].pos = new_location
        self.spindex.insert((kind, entity.uuid), get_entity_bounding_box(entity.pos, kind))

    def remove_entity(self, entity: Entity):
        self._grouped_entities[entity.kind].pop(entity.uuid)
        self.spindex.remove((entity.kind, entity.uuid), get_entity_bounding_box(entity.pos, entity.kind))

    def get_available_position(self, kind: int) -> Pos:
        """Finds a position on the map, such that the bounding box of an entity of type ``kind``
           doesn't intersect with any existing object on the map.

        :param: kind entity type
        :returns: available position"""
        pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))

        while len(self.spindex.intersect(get_entity_bounding_box((pos_x, pos_y), kind))) != 0:
            pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))
        return pos_x, pos_y

    def add_entity(self, entity: Entity):
        self.spindex.insert((entity.kind, entity.uuid), get_entity_bounding_box(entity.pos, entity.kind))
        self.add_to_dict(entity)


@dataclass
class Item:
    """An in-game item"""
    type: int

    def on_click(self, clicked_by: Entity, manager: EntityManager):
        """Handles a click on the item.

        :param clicked_by: entity who clicked on the item
        :param manager: entity manager"""
        ...


class CanHit(abc.ABC):
    """An interface for game objects that can hit others, such as weapons and projectiles."""

    @abc.abstractmethod
    def on_hit(self, hit_objects: Iterable[Entity], manager: EntityManager):
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
    def advance_per_tick(self, manager: EntityManager) -> bool:
        """Advances the object per game tick: calculates collisions and updates stats locally (not in the manager).

        :returns: whether the entity should be removed from the game"""
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
class Projectile(ServerControlled, CanHit):
    damage: int = 0
    ttl: int = PROJECTILE_TTL
    kind: int = EntityType.PROJECTILE
    width: int = PROJECTILE_WIDTH
    height: int = PROJECTILE_HEIGHT

    def advance_per_tick(self, manager: EntityManager) -> bool:
        pass

    def on_hit(self, hit_objects: Iterable[Entity], manager: EntityManager):
        pass


@dataclass
class Player(Combatant):
    new_message: str = ""
    incoming_message: str = ""  # List[str] = field(default_factory=lambda: [])
    addr: Addr = ("127.0.0.1", 10000)
    last_updated: int = -1  # latest sequence number basically
    slot: int = 0
    inventory: List[int] = dataclasses.field(default_factory=lambda: [SWORD, AXE, BOW] + [EMPTY_SLOT
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
    def item(self):
        return get_item(self.weapon)

    def serialize(self) -> dict:
        return super().serialize() | {"weapon": self.weapon}

    def get_mob_stop_distance(self) -> float:
        return 0.5 * (np.sqrt(BOT_HEIGHT ** 2 + BOT_WIDTH ** 2) + np.sqrt(CLIENT_HEIGHT ** 2 + CLIENT_WIDTH ** 2)) + \
               (RANGED_OFFSET if isinstance(self.item, RangedWeapon) else 0)

    def update_direction(self, manager: EntityManager):
        """Updates mob's attacking/movement directions, and updates whether he is currently tracking a player."""
        in_range = list(map(lambda entity: entity.pos,
                       manager.get_entities_in_range(get_bounding_box(self.pos, MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT),
                                                     entity_filter=lambda kind, _: kind == EntityType.PLAYER)))
        self.direction = -1, -1  # used to reset calculations each iteration
        if not in_range:
            self.on_player = False
            self.direction = 0.0, 0.0
            return

        nearest_player_pos = min(in_range,
                                 key=lambda pos: (self.pos[0] - pos[0]) ** 2 + (self.pos[1] - pos[1]) ** 2)
        self.on_player = True
        if np.sqrt(((self.pos[0] - nearest_player_pos[0]) ** 2 + (self.pos[1] - nearest_player_pos[1]) ** 2)) <= \
                self.get_mob_stop_distance() + MOB_ERROR_TERM:
            self.direction = 0.0, 0.0
        dir_x, dir_y = nearest_player_pos[0] - self.pos[0], nearest_player_pos[1] - self.pos[1]
        dir_x, dir_y = normalize_vec(dir_x, dir_y)
        self.attacking_direction = dir_x, dir_y
        if self.direction != (0., 0.):
            self.direction = dir_x * MOB_SPEED, dir_y * MOB_SPEED

    def advance_per_tick(self, manager: EntityManager) -> bool:
        pass

    def on_hit(self, hit_objects: Iterable[Entity], manager: EntityManager):
        pass


@dataclass
class Weapon(Item):
    """An in-game weapon."""
    cooldown: int
    damage: int

    def on_click(self, clicked_by: Combatant, manager: EntityManager):
        self.use_to_attack(clicked_by, manager)
        clicked_by.last_time_attacked = time.time()
        clicked_by.current_cooldown = self.cooldown * FRAME_TIME

    @abc.abstractmethod
    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        """Attack using this weapon."""
        ...


@dataclass
class MeleeWeapon(Weapon):
    melee_attack_range: int

    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        in_range: Iterable[Combatant] = manager.get_entities_in_range(get_bounding_box(attacker.pos, self.melee_attack_range,
                                                                  self.melee_attack_range),
                                        entity_filter=lambda entity_kind,
                                        entity_uuid: entity_kind != EntityType.PROJECTILE and
                                        entity_uuid != attacker.uuid)
        for attackable in in_range:
            if attackable.kind == EntityType.MOB == attackable.kind:
                continue  # mobs shouldn't attack mobs
            attackable.health -= self.damage
            if attackable.health <= MIN_HEALTH:
                manager.remove_entity(attackable)
                logging.info(f"killed {attackable=}")
            logging.info(f"updated entity health to {attackable.health}")


@dataclass
class RangedWeapon(Weapon):
    projectile_class: Type[Projectile]
    """Projectile type to be shot. Can be any class which inherits from `Projectile`."""

    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        projectile = self.projectile_class(
            pos=(int(attacker.pos[0] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[0]),
                 int(attacker.pos[1] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[1])))
        manager.add_entity(projectile)
        with manager.projectile_lock:
            manager.projectiles[projectile.uuid] = projectile
            logging.info(f"added projectile {projectile}")


_item_pool: Dict[int, Item] = {
    SWORD: MeleeWeapon(type=SWORD, cooldown=100, damage=15, melee_attack_range=100),
    AXE: MeleeWeapon(type=AXE, cooldown=300, damage=40, melee_attack_range=150),
    BOW: RangedWeapon(type=BOW, cooldown=400, damage=30, projectile_class=Projectile),
    MAHAK: RangedWeapon(type=MAHAK, cooldown=200, damage=100, projectile_class=Projectile)
}


def get_item(kind: int) -> Item:
    return _item_pool[kind]
