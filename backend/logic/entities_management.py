import numpy as np
from pyqtree import Index

from common.consts import WORLD_WIDTH, WORLD_HEIGHT, MOB_COUNT, Pos, EntityType
from entities import Projectile, Player, Mob, Entity, ServerControlled
from collections import defaultdict
from typing import Dict


class EntityManager:

    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.mobs: Dict[str, Mob] = {}
        self.projectiles: defaultdict[str, Projectile] = defaultdict(lambda: Projectile())

        self.spindex = Index(bbox=(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        """Quadtree for collision/range detection. Player keys are tuples `(type, uuid)`, with the type being
        projectile/player/mob, and the uuid being, well, the uuid."""

    @property
    def entities(self) -> Dict[str, Entity]:
        return self.players | self.mobs | self.projectiles


    def get_available_position(self, kind: int) -> Pos:
        """Generates a position on the map, such that the bounding box of an entity of type ``kind``
           doesn't intersect with any existing object on the map.

        :param kind: entity type
        :returns: available position"""
        pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))

        while len(self.spindex.intersect(self.get_entity_bounding_box((pos_x, pos_y), kind))) != 0:
            pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))
        return pos_x, pos_y

    def generate_mobs(self):
        """Generate the mobs object with a random positions"""
        for _ in range(MOB_COUNT):
            mob = Mob()
            mob.pos = self.get_available_position(EntityType.MOB)
            mob.weapon = 1 # random.randint(MIN_WEAPON_NUMBER, MAX_WEAPON_NUMBER)
            self.mobs[mob.uuid] = mob
            self.spindex.insert((EntityType.MOB, mob.uuid), self.get_entity_bounding_box(mob.pos, EntityType.MOB))
