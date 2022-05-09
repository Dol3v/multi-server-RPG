import abc
import contextlib
import dataclasses
import logging
import random
import threading
import time
import uuid
from abc import ABC
from dataclasses import dataclass
from typing import Dict, Iterable, List, Type, Callable, ClassVar, Tuple

import numpy as np
from cryptography.fernet import Fernet
from pyqtree import Index

from backend.backend_consts import BAG_SIZE, MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT, RANGED_OFFSET, MOB_ERROR_TERM, \
    FRAME_TIME, PET_SPAWN_X_DELTA, PET_SPAWN_Y_DELTA
from common.consts import EntityType, DEFAULT_POS_MARK, Pos, Dir, DEFAULT_DIR, WORLD_WIDTH, WORLD_HEIGHT, \
    MIN_ITEM_NUMBER, MAX_ITEM_NUMBER, MAX_HEALTH, PROJECTILE_TTL, PROJECTILE_WIDTH, PROJECTILE_HEIGHT, PROJECTILE_SPEED, \
    SWORD, AXE, BOW, REGENERATION_POTION, EMPTY_SLOT, INVENTORY_COLUMNS, INVENTORY_ROWS, Addr, MIN_SKILL, MAX_SKILL, \
    MOB_MIN_WEAPON, MOB_MAX_WEAPON, MOB_SPEED, BOT_HEIGHT, BOT_WIDTH, CLIENT_HEIGHT, CLIENT_WIDTH, MIN_HEALTH, \
    ARROW_OFFSET_FACTOR, DAMAGE_POTION, RESISTANCE_POTION, USELESS_ITEM, FIRE_BALL, MAHAK, PET_EGG
from common.utils import get_entity_bounding_box, get_bounding_box, normalize_vec


@dataclass
class Entity(abc.ABC):
    speed: ClassVar[int] = 0
    kind: ClassVar[EntityType]
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

        self.mob_lock = threading.RLock()
        self.projectile_lock = threading.RLock()

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

    def get_entities_in_range(self, bbox: Tuple[int, int, int, int], *,
                              entity_filter: Callable[[EntityType, str], bool] = lambda a, b: True) -> Iterable[Entity]:
        """Returns the entities in a given bounding box, for which ``entity_filter`` returns true.

        :param bbox: search rectangle, of format (x_min, y_min, x_max, y_max)
        :param entity_filter: filter function for entities, that takes a tuple of the entity
        :returns: an iterable containing all entities in a search rectangle of dimensions `height` and `width`, except
            the entity with uuid `entity_uuid`
        """
        return map(lambda data: self.get(data[1], data[0]),
                   filter(lambda data: entity_filter(*data) and data[0] != EntityType.OBSTACLE,
                          self.spindex.intersect(bbox)))

    def get_collidables_with(self, entity: Entity) -> Iterable[Entity]:
        """Get all objects that collide with entity"""
        return self.get_entities_in_range(get_entity_bounding_box(entity.pos, entity.kind),
                                          entity_filter=lambda _, entity_id: entity_id != entity.uuid)

    def get_entity_lock(self, entity: Entity):
        """Returns a matching lock for an entity, or a null context handler otherwise."""
        match entity.kind:
            case EntityType.PROJECTILE:
                return self.projectile_lock
            case EntityType.MOB:
                return self.mob_lock
            case EntityType.PLAYER:
                return entity.lock
            case _:
                return contextlib.nullcontext()

    def update_entity_location(self, entity: Entity, new_location: Pos):
        # with self.get_entity_lock(entity):
        # logging.debug(f"[debug] updating entity uuid={entity.uuid} of {kind=} to {new_location=}")
        self.spindex.remove((entity.kind, entity.uuid), get_entity_bounding_box(entity.pos, entity.kind))
        entity.pos = new_location
        self._grouped_entities[entity.kind][entity.uuid].pos = new_location
        self.spindex.insert((entity.kind, entity.uuid), get_entity_bounding_box(entity.pos, entity.kind))

    def remove_entity(self, entity: Entity):
        with self.get_entity_lock(entity):
            self._grouped_entities[entity.kind].pop(entity.uuid)
            self.spindex.remove((entity.kind, entity.uuid), get_entity_bounding_box(entity.pos, entity.kind))

    def get_available_position(self, kind: EntityType, x_min: int = 0, x_max: int = WORLD_WIDTH // 3, y_min: int = 0,
                               y_max: int = WORLD_HEIGHT // 3) -> Pos:
        """Finds a position on the map, such that the bounding box of an entity of type ``kind``
           doesn't intersect with any existing object on the map.

        :param: kind entity type
        :returns: available position"""
        pos_x, pos_y = int(np.random.uniform(x_min, x_max)), int(np.random.uniform(y_min, y_max))

        while len(self.spindex.intersect(get_entity_bounding_box((pos_x, pos_y), kind))) != 0:
            pos_x, pos_y = int(np.random.uniform(x_min, x_max)), int(np.random.uniform(y_min, y_max))
        return pos_x, pos_y

    def add_entity(self, entity: Entity):
        with self.get_entity_lock(entity):
            self.spindex.insert((entity.kind, entity.uuid), get_entity_bounding_box(entity.pos, entity.kind))
            self.add_to_dict(entity)


@dataclass(frozen=True)
class Item:
    """An in-game item"""
    type: int

    def on_click(self, clicked_by: Entity, manager: EntityManager):
        """Handles a click on the item.

        :param clicked_by: entity who clicked on the item
        :param manager: entity manager"""
        ...


@dataclass
class Bag(Entity):
    kind = EntityType.BAG
    items: List = dataclasses.field(
        default_factory=lambda: [random.randint(MIN_ITEM_NUMBER, MAX_ITEM_NUMBER) for _ in range(BAG_SIZE)]
    )


class CanHit(abc.ABC):
    """An interface for game objects that can hit others, such as weapons and projectiles."""

    @abc.abstractmethod
    def on_hit(self, hit_objects: Iterable[Entity], manager: EntityManager) -> bool:
        """Handles a hit between self and other objects.

        :param hit_objects: objects that were hit by self
        :param manager: entity manager
        :returns: whether the hit was fatal for hte object, i.e if he would be removed after it"""
        ...


class ServerControlled(Entity, abc.ABC):
    """An abstract class for server controlled objects, i.e., objects with server-controlled
    movement and general behaviour such as mobs and projectiles."""

    @abc.abstractmethod
    def action_per_tick(self, manager: EntityManager) -> bool:
        """Advances the object per game tick: calculates collisions and updates stats locally (not in the manager).

        :returns: whether the entity should be removed from the game"""
        ...

    def advance_per_tick(self, manager: EntityManager) -> bool:
        """Wrapper for ``self.action_per_tick`` that also advances the entity's location."""
        res = self.action_per_tick(manager)
        manager.update_entity_location(self, (self.pos[0] + int(self.speed * self.direction[0]),
                                              self.pos[1] + int(self.speed * self.direction[1])))
        # if self.kind != EntityType.PROJECTILE:
            # logging.debug(f"updated mob location to {self.pos}, {self.speed=}, {self.direction=}, {self.uuid}")
        return res


@dataclass
class Combatant(Entity):
    attacking_direction: Dir = DEFAULT_DIR
    is_attacking: bool = False
    last_time_attacked: float = -1
    current_cooldown: float = -1
    health: int = MAX_HEALTH
    resistance: int = 0
    damage_multiplier: int = 1

    @property
    @abc.abstractmethod
    def item(self) -> Item:
        """Currently held item."""
        ...

    @property
    def has_ranged_weapon(self) -> bool:
        return isinstance(self.item, RangedWeapon)

    def deal_damage_to(self, other, damage: int):
        """Deals some amount of damage to another combatant, factoring in the resistance/damage boost of both."""
        other.health -= (damage * self.damage_multiplier) + other.resistance

    def serialize(self) -> dict:
        return super().serialize() | {"is_attacking": self.is_attacking,
                                      "hp": self.health,
                                      "resistance": self.resistance}


@dataclass
class Projectile(ServerControlled, CanHit):
    damage: int = 0
    ttl: int = PROJECTILE_TTL
    shot_by: Combatant = dataclasses.field(default_factory=lambda: Combatant())
    kind: ClassVar[EntityType] = EntityType.PROJECTILE
    width: ClassVar[int] = PROJECTILE_WIDTH
    height: ClassVar[int] = PROJECTILE_HEIGHT
    speed: ClassVar[int] = PROJECTILE_SPEED

    def action_per_tick(self, manager: EntityManager) -> bool:
        self.ttl -= 1
        if self.ttl == 0:
            logging.debug(f"[debug] gonna remove uuid={self.uuid}, ttl=0")
            return True

        intersection = list(manager.get_collidables_with(self))
        if intersection:
            logging.debug(f"gonna remove projectile uuid={self.uuid}, hit, intersection {list(intersection)}")
            return self.on_hit(intersection, manager)
        return False

    def on_hit(self, hit_objects: Iterable[Entity], manager: EntityManager) -> bool:
        should_remove = True
        for hit in hit_objects:
            match hit.kind:
                case EntityType.PROJECTILE:
                    should_remove = False
                case EntityType.MOB | EntityType.PLAYER:
                    logging.info(f"projectile {self.uuid} hit entity {hit!r}")
                    with manager.get_entity_lock(hit):
                        self.shot_by.deal_damage_to(hit, self.damage)
                        logging.info(f"entity {hit!r} was updated after hit")

        return should_remove


@dataclass
class Player(Combatant):
    addr: Addr = ("", 0)
    last_updated_seqn: int = -1  # latest sequence number basically
    last_updated_time: float = dataclasses.field(default_factory=time.time)
    slot: int = 0
    inventory: List[int] = dataclasses.field(default_factory=lambda: [SWORD, AXE, BOW, REGENERATION_POTION] + [EMPTY_SLOT
                                                                                                   for _ in range(
            INVENTORY_COLUMNS * INVENTORY_ROWS - 4)])
    skill: int = dataclasses.field(default_factory=lambda: random.randint(MIN_SKILL, MAX_SKILL))
    fernet: Fernet | None = None
    kind: int = EntityType.PLAYER
    last_time_used_skill: int = 0
    skill_cooldown: int = -1
    lock: threading.RLock = threading.RLock()

    @property
    def item(self) -> Item:
        return get_item(self.inventory[self.slot])

    def serialize(self) -> dict:
        return super().serialize() | {"tool": self.inventory[self.slot], "skill": self.skill}

    def __repr__(self):
        return f"Player(uuid={self.uuid}, addr={self.addr}, pos={self.pos}, item={self.item!r}, health={self.health})"

    def fill_inventory(self, bag: Bag):
        """Fills player's inventory with the bag's items."""
        new_item_slot = 0
        for index, item in enumerate(self.inventory):
            if new_item_slot == len(bag.items):
                break
            if item == EMPTY_SLOT:
                self.inventory[index] = bag.items[new_item_slot]
                new_item_slot += 1


@dataclass
class Mob(Combatant, ServerControlled):
    weapon: int = dataclasses.field(default_factory=lambda: random.randint(MOB_MIN_WEAPON, MOB_MAX_WEAPON))
    tracked_player_uuid: str | None = None
    kind: ClassVar[EntityType] = EntityType.MOB
    speed: ClassVar[int] = MOB_SPEED
    parent_uuid: str = ""

    @property
    def item(self):
        return get_item(self.weapon)

    def serialize(self) -> dict:
        return super().serialize() | {"weapon": self.weapon}

    def in_attack_range(self, pos: Pos) -> bool:
        return abs(self.pos[0] - pos[0]) <= MOB_SIGHT_WIDTH and \
               abs(self.pos[1] - pos[1]) <= MOB_SIGHT_HEIGHT

    def get_mob_stop_distance(self) -> float:
        return 0.5 * (np.sqrt(BOT_HEIGHT ** 2 + BOT_WIDTH ** 2) + np.sqrt(CLIENT_HEIGHT ** 2 + CLIENT_WIDTH ** 2)) + \
               (RANGED_OFFSET if isinstance(self.item, RangedWeapon) else 0)

    def update_direction(self, manager: EntityManager):
        """Updates mob's attacking/movement directions, and updates whether he is currently tracking a player."""
        in_range = list(manager.get_entities_in_range(get_bounding_box(self.pos, MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT),
                                                      entity_filter=lambda kind,
                                                                           entity_uuid: kind == EntityType.PLAYER and
                                                                                        entity_uuid != self.parent_uuid))
        self.direction = -1, -1  # used to reset calculations each iteration
        if not in_range:
            self.tracked_player_uuid = None
            self.direction = 0.0, 0.0
            return

        nearest_player = min(in_range,
                             key=lambda p: (self.pos[0] - p.pos[0]) ** 2 + (self.pos[1] - p.pos[1]) ** 2)
        self.tracked_player_uuid = nearest_player.uuid
        logging.debug(f"mob {self.uuid} tracking player {self.tracked_player_uuid}")
        if np.sqrt(((self.pos[0] - nearest_player.pos[0]) ** 2 + (self.pos[1] - nearest_player.pos[1]) ** 2)) <= \
                self.get_mob_stop_distance() + MOB_ERROR_TERM:
            logging.debug(f"mob {self.uuid} staying put cuz stop distance")
            self.direction = 0.0, 0.0
        dir_x, dir_y = nearest_player.pos[0] - self.pos[0], nearest_player.pos[1] - self.pos[1]
        dir_x, dir_y = normalize_vec(dir_x, dir_y)
        self.attacking_direction = dir_x, dir_y
        if self.direction != (0., 0.):
            self.direction = (dir_x * MOB_SPEED, dir_y * MOB_SPEED)
            logging.debug(f"mob {self.uuid} has updated direction {self.direction}")

    def action_per_tick(self, manager: EntityManager) -> bool:
        if self.health <= MIN_HEALTH:
            return True

        self.update_direction(manager)
        if self.tracked_player_uuid and (player := manager.get(self.tracked_player_uuid, EntityType.PLAYER)):
            if self.in_attack_range(player.pos):
                self.item.on_click(self, manager)

        colliding = list(manager.get_collidables_with(self))
        if colliding and self.tracked_player_uuid:
            self.direction = (0.0, 0.0)
            logging.debug(f"mob {self.uuid} stopped due to colliding with {colliding}")

        return False


@dataclass(frozen=True)
class Weapon(Item):
    """An in-game weapon."""
    cooldown: int
    damage: int

    def on_click(self, clicked_by: Combatant, manager: EntityManager):
        if clicked_by.current_cooldown == -1 or clicked_by.last_time_attacked + clicked_by.current_cooldown <= time.time():
            self.use_to_attack(clicked_by, manager)
            clicked_by.last_time_attacked = time.time()
            clicked_by.current_cooldown = self.cooldown * FRAME_TIME

    @abc.abstractmethod
    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        """Attack using this weapon."""
        ...


@dataclass(frozen=True)
class Skill(Weapon, ABC):

    def on_click(self, player: Player, manager: EntityManager):
        if player.skill_cooldown == -1 or player.last_time_used_skill + player.skill_cooldown <= time.time():
            self.use_to_attack(player, manager)
            player.last_time_used_skill = time.time()
            player.skill_cooldown = self.cooldown * FRAME_TIME


@dataclass(frozen=True)
class MeleeWeapon(Weapon):
    melee_attack_range: int

    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        in_range = manager.get_entities_in_range(
            get_bounding_box(attacker.pos, self.melee_attack_range,
                             self.melee_attack_range),
            entity_filter=lambda entity_kind,
                                 entity_uuid: entity_kind != EntityType.PROJECTILE and
                                              entity_uuid != attacker.uuid and
                                              entity_kind != EntityType.BAG)
        for attackable in in_range:
            if attackable.kind == EntityType.MOB == attacker.kind:
                continue  # mobs shouldn't attack mobs
            with manager.get_entity_lock(attackable):
                attacker.deal_damage_to(attackable, self.damage)
                logging.info(f"updated entity (uuid={attackable.uuid}) health to {attackable.health}")


@dataclass(frozen=True)
class RangedWeapon(Weapon):
    projectile_class: Type[Projectile]
    """Projectile type to be shot. Can be any class which inherits from `Projectile`."""

    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        projectile = self.projectile_class(
            pos=(int(attacker.pos[0] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[0]),
                 int(attacker.pos[1] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[1])),
            direction=attacker.attacking_direction,
            damage=self.damage,
            shot_by=attacker
        )
        manager.add_entity(projectile)
        logging.debug(f"added projectile {projectile}")


@dataclass(frozen=True)
class OneClickItem(Item):
    """An Item that disappears after one click."""

    def on_click(self, clicked_by: Player, manager: EntityManager):
        with clicked_by.lock:
            self.action(clicked_by, manager)
            clicked_by.inventory[clicked_by.slot] = EMPTY_SLOT

    @abc.abstractmethod
    def action(self, clicked_by: Player, manager: EntityManager):
        ...


@dataclass(frozen=True)
class RegenerationPotion(OneClickItem):
    type = REGENERATION_POTION
    regen_strength: ClassVar[int] = 35

    def action(self, clicked_by: Player, manager: EntityManager):
        prev_health = clicked_by.health
        clicked_by.health += self.regen_strength
        clicked_by.health = min(MAX_HEALTH, clicked_by.health)
        logging.info(f"player {clicked_by!r} had his health regenerated to {clicked_by.health} from {prev_health}")


@dataclass(frozen=True)
class DamagePotion(OneClickItem):
    """Increases the damage done by an entity. The effect stacks, meaning applying some damage potions
    will increase the damage continuously."""
    type = DAMAGE_POTION
    damage_multiplier: ClassVar[int] = 1.1

    def action(self, clicked_by: Player, manager: EntityManager):
        clicked_by.damage_multiplier *= self.damage_multiplier


@dataclass(frozen=True)
class ResistancePotion(OneClickItem):
    """Adds damage resistance to an entity. The boost stacks until the resistance reaches a known threshold."""
    type = RESISTANCE_POTION
    resistance_strength: ClassVar[int] = 5
    max_resistance: ClassVar[int] = 25

    def action(self, clicked_by: Player, manager: EntityManager):
        clicked_by.resistance += self.resistance_strength
        clicked_by.resistance = min(self.max_resistance, clicked_by.resistance)


@dataclass(frozen=True)
class UselessItem(Item):
    type = USELESS_ITEM


class FireballSkill(Skill, RangedWeapon):
    type = FIRE_BALL
    projectile_class = Projectile


class EraserSkill(Skill, RangedWeapon):
    type: int = MAHAK
    projectile_class = Projectile


class PetEggSkill(Skill):
    type = PET_EGG

    def use_to_attack(self, player: Player, manager: EntityManager):
        to_spawn = Mob(parent_uuid=player.uuid, pos=manager.get_available_position
        (EntityType.MOB, *get_bounding_box(player.pos, PET_SPAWN_X_DELTA, PET_SPAWN_Y_DELTA)))
        manager.add_entity(to_spawn)


_item_pool: Dict[int, Item] = {
    EMPTY_SLOT: UselessItem(USELESS_ITEM),
    SWORD: MeleeWeapon(type=SWORD, cooldown=25, damage=15, melee_attack_range=100),
    AXE: MeleeWeapon(type=AXE, cooldown=100, damage=40, melee_attack_range=150),
    BOW: RangedWeapon(type=BOW, cooldown=100, damage=30, projectile_class=Projectile),
    USELESS_ITEM: UselessItem(USELESS_ITEM),
    REGENERATION_POTION: RegenerationPotion(type=REGENERATION_POTION),
    DAMAGE_POTION: DamagePotion(type=DAMAGE_POTION),
    RESISTANCE_POTION: ResistancePotion(type=RESISTANCE_POTION),
    MAHAK: EraserSkill(type=MAHAK, cooldown=200, damage=100),
    FIRE_BALL: FireballSkill(type=FIRE_BALL, cooldown=200, damage=100),
    PET_EGG: PetEggSkill(type=PET_EGG, cooldown=300, damage=0)
}


def get_item(kind: int) -> Item:
    return _item_pool[kind]
