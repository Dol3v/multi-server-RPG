from pyqtree import Index

from common.consts import WORLD_WIDTH, WORLD_HEIGHT
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





