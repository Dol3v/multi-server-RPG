import logging
import threading

import numpy as np
from pyqtree import Index

from backend.consts import MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT, MOB_ERROR_TERM, RANGED_OFFSET, \
    ARM_LENGTH_MULTIPLIER

from backend.logic.collision import moved_reasonable_distance
from common.consts import WORLD_WIDTH, WORLD_HEIGHT, MOB_COUNT, Pos, EntityType, MOB_SPEED, BOT_HEIGHT, BOT_WIDTH, \
    CLIENT_HEIGHT, CLIENT_WIDTH, BOW, EMPTY_SLOT, DEFAULT_DIR, \
    SCREEN_HEIGHT, SCREEN_WIDTH, Dir
from common.utils import get_entity_bounding_box, is_empty, normalize_vec, get_bounding_box
from backend.logic.entities import Projectile, Player, Mob, Entity, Combatant
from collections import defaultdict
from typing import Dict, Iterable, Tuple, Any


class EntityManager:
    """Use to control and access all game entities"""
    def __init__(self, spindex: Index):
        self.players: Dict[str, Player] = {}
        self.mobs: Dict[str, Mob] = {}
        self.projectiles: defaultdict[str, Projectile] = defaultdict(lambda: Projectile())

        self.spindex = spindex
        """Quadtree for collision/range detection. Player keys are tuples `(type, uuid)`, with the type being
        projectile/player/mob, and the uuid being, well, the uuid."""

        self.mob_lock = threading.Lock()
        self.projectile_lock = threading.Lock()

        self.generate_mobs()

    @property
    def entities(self) -> Dict[str, Entity]:
        return self.players | self.mobs | self.projectiles

    def get_collidables_with(self, pos: Pos, entity_uuid: str, *, kind: int) -> Iterable[Tuple[int, str]]:
        """Get all objects that collide with entity"""
        return filter(lambda data: data[1] != entity_uuid, self.spindex.intersect(
            get_entity_bounding_box(pos, kind)))

    def attackable_in_range(self, entity_uuid: str, bbox: Tuple[int, int, int, int]) -> \
            list[tuple[EntityType, Combatant]]:
        return list(map(lambda data: (data[0], self.entities[data[1]]),
                        filter(lambda data: data[1] != entity_uuid and data[0] != EntityType.ARROW and
                                            data[0] != EntityType.OBSTACLE,
                               self.spindex.intersect(bbox))))

    def entities_in_melee_attack_range(self, entity: Combatant, melee_range: int) \
            -> list[tuple[EntityType, Combatant]]:
        """Returns all enemy players that are in the attack range (i.e. in the general direction of the player
        and close enough)."""
        weapon_x, weapon_y = int(entity.pos[0] + ARM_LENGTH_MULTIPLIER * entity.direction[0]), \
                             int(entity.pos[1] + ARM_LENGTH_MULTIPLIER * entity.direction[1])
        return self.attackable_in_range(entity.uuid, (weapon_x - melee_range // 2, weapon_y - melee_range // 2,
                                                      weapon_x + melee_range // 2, weapon_y + melee_range // 2))

    def get_data_from_entity(self, entity_data: Tuple[int, str]) -> tuple[int, bytes, Pos, Dir, int]:
        """Retrieves data about an entity from its quadtree identifier: kind & other data (id/address).

        :returns: flattened tuple of kind, position and direction"""
        entity = self.entities[entity_data[1]]
        tool_id = EMPTY_SLOT
        direction = DEFAULT_DIR
        match entity_data[0]:
            case EntityType.PLAYER:
                tool_id = entity.tools[entity.slot]
                direction = entity.attacking_direction
            case EntityType.MOB:
                tool_id = entity.weapon
                direction = entity.attacking_direction
            case EntityType.ARROW:
                direction = entity.direction

        return entity_data[0], entity.uuid.encode(), *entity.pos, *direction, tool_id

    def entities_in_rendering_range(self, entity: Player) -> Iterable[Entity]:
        """Returns all players that are within render distance of each other."""
        return map(lambda data: self.entities[data[1]],
                   filter(lambda data: data[1] != entity.uuid and data[0] != EntityType.OBSTACLE,
                          self.spindex.intersect(
                              get_bounding_box(entity.pos, SCREEN_HEIGHT, SCREEN_WIDTH))))

    def update_entity_location(self, entity: Entity, new_location: Pos, kind: int):
        logging.debug(f"[debug] updating entity uuid={entity.uuid} of {kind=} to {new_location=}")
        self.spindex.remove((kind, entity.uuid), get_entity_bounding_box(entity.pos, kind))
        # are both necessary? prob not, but I'm not gonna take the risk
        entity.pos = new_location
        self.entities[entity.uuid].pos = new_location
        self.spindex.insert((kind, entity.uuid), get_entity_bounding_box(entity.pos, kind))

    def remove_entity(self, entity: Entity, kind: int):
        match kind:
            case EntityType.PLAYER:
                # TODO: update client
                # self.died_clients.add(entity.uuid)
                # self.update_client(entity.uuid, DEFAULT_POS_MARK)  # sending message with negative hp
                self.players.pop(entity.uuid)

            case EntityType.MOB:
                with self.mob_lock:
                    self.mobs.pop(entity.uuid)

            case EntityType.ARROW:
                with self.projectile_lock:
                    self.projectiles.pop(entity.uuid)

            case _:
                logging.warning(f"invalid entity type to remove")
                return

        self.spindex.remove((kind, entity.uuid), get_entity_bounding_box(entity.pos, kind))

    @staticmethod
    def get_mob_stop_distance(mob: Mob) -> float:
        return 0.5 * (np.sqrt(BOT_HEIGHT ** 2 + BOT_WIDTH ** 2) + np.sqrt(CLIENT_HEIGHT ** 2 + CLIENT_WIDTH ** 2)) + \
               (RANGED_OFFSET if mob.weapon == BOW else 0)

    def players_in_range(self, pos: Pos, width: int, height: int) -> Iterable[Pos]:
        intersecting = self.spindex.intersect(get_bounding_box(pos, height, width))
        filtered = filter(lambda data: data[0] == EntityType.PLAYER, intersecting)
        mapped = list(map(lambda data: self.entities[data[1]].pos, filtered))
        return mapped

    def update_mob_directions(self, mob: Mob):
        """Updates mob's attacking/movement directions, and updates whether he is currently tracking a player."""
        in_range = self.players_in_range(mob.pos, MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT)
        mob.direction = -1, -1  # used to reset calculations each iteration
        if not in_range:
            mob.on_player = False
            mob.direction = 0.0, 0.0
            return

        nearest_player_pos = min(in_range,
                                 key=lambda pos: (mob.pos[0] - pos[0]) ** 2 + (mob.pos[1] - pos[1]) ** 2)
        mob.on_player = True
        if np.sqrt(((mob.pos[0] - nearest_player_pos[0]) ** 2 + (mob.pos[1] - nearest_player_pos[1]) ** 2)) <= \
                self.get_mob_stop_distance(mob) + MOB_ERROR_TERM:
            mob.direction = 0.0, 0.0
        dir_x, dir_y = nearest_player_pos[0] - mob.pos[0], nearest_player_pos[1] - mob.pos[1]
        dir_x, dir_y = normalize_vec(dir_x, dir_y)
        mob.attacking_direction = dir_x, dir_y
        if mob.direction != (0., 0.):
            mob.direction = dir_x * MOB_SPEED, dir_y * MOB_SPEED

    def invalid_movement(self, entity: Player, player_pos: Pos, seqn: int) -> bool:
        """check if a given player movement is valid"""
        return entity.last_updated != -1 and (not moved_reasonable_distance(
            player_pos, entity.pos, seqn - entity.last_updated) or
                                              not is_empty(
                                                  self.get_collidables_with(player_pos, entity.uuid,
                                                                            kind=EntityType.PLAYER))
                                              or not (0 <= player_pos[0] <= WORLD_WIDTH)
                                              or not (0 <= player_pos[1] <= WORLD_HEIGHT))

    def get_available_position(self, kind: int) -> Pos:
        """Generates a position on the map, such that the bounding box of an entity of type ``kind``
           doesn't intersect with any existing object on the map.

        :param: kind entity type
        :returns: available position"""
        pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))

        while len(self.spindex.intersect(get_entity_bounding_box((pos_x, pos_y), kind))) != 0:
            pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))
        return pos_x, pos_y

    def generate_mobs(self):
        """Generate the mobs object with a random positions"""
        for _ in range(MOB_COUNT):
            mob = Mob()
            mob.pos = self.get_available_position(EntityType.MOB)
            mob.weapon = 1  # random.randint(MIN_WEAPON_NUMBER, MAX_WEAPON_NUMBER)
            self.mobs[mob.uuid] = mob
            self.spindex.insert((EntityType.MOB, mob.uuid), get_entity_bounding_box(mob.pos, EntityType.MOB))

    def add_entity(self, kind: EntityType, uuid: str, position: Pos, width: int, height: int):
        """Adds an entity to the quadtree"""
        self.spindex.insert((kind, uuid),
                            get_bounding_box(position, width, height))


