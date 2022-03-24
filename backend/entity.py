from dataclasses import dataclass, field
from typing import List
from common.consts import Pos, MAX_HEALTH

@dataclass
class Entity:
    pos: Pos = (-1, -1)
    width: int = -1
    height: int = -1
    is_attacking: bool = False
    last_updated: int  = -1 # latest sequence number basically
    health: int = MAX_HEALTH
    """
    [IDs]
        sword = 1
        axe = 2
        arrow = 3
    tools: [default, tool2, tool3]
    """
    tools: List = field(default_factory=lambda: [1, 0, 0])


    def update(self, pos: Pos, width: int, height: int, is_attacking: bool, last_updated: int, health_change=0) -> None:
        """
        Use: update entity fields
        """
        self.pos = pos
        self.width = width
        self.height = height
        self.is_attacking = is_attacking
        self.last_updated = last_updated
        self.health += health_change # if health goes under 0 include then send server quit message.
