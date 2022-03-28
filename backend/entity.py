from dataclasses import dataclass, field
from typing import List

from common.consts import Pos, MAX_HEALTH, MIN_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT


@dataclass
class Entity:
    entity_type: int = 0
    pos: Pos = DEFAULT_POS_MARK
    width: int = -1
    height: int = -1
    is_attacking: bool = False
    direction = DEFAULT_DIR
    last_updated: int = -1  # latest sequence number basically
    health: int = MAX_HEALTH
    """
    [IDs]
        sword = 1
        axe = 2
        arrow = 3
    tools: [default, tool2, tool3]
    """
    tools: List = field(default_factory=lambda: [SWORD, AXE, BOW, EMPTY_SLOT, EMPTY_SLOT, EMPTY_SLOT])

    def update(self, pos: Pos, width: int, height: int, is_attacking: bool, last_updated: int, health_change=0) -> None:
        """
        Use: update player fields
        """
        self.pos = pos
        self.width = width
        self.height = height
        self.is_attacking = is_attacking
        self.last_updated = last_updated

        if (self.health + health_change >= MIN_HEALTH):
            self.health += health_change  # if health goes to 0 include then send server quit message.
