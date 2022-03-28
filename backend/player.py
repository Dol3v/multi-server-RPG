from dataclasses import dataclass, field
from typing import List, Tuple

from common.consts import Pos, MAX_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT


@dataclass
class Player:
    entity_type: int = 0
    pos: Pos = DEFAULT_POS_MARK
    width: int = -1
    height: int = -1
    is_attacking: bool = False
    direction: Tuple[float, float] = DEFAULT_DIR
    last_updated: int = -1  # latest sequence number basically
    last_time_attacked: float = -1
    current_cooldown: float = -1
    health: int = MAX_HEALTH
    tools: List = field(default_factory=lambda: [SWORD, AXE, BOW, EMPTY_SLOT, EMPTY_SLOT, EMPTY_SLOT])
    """
    [IDs]
        sword = 1
        axe = 2
        arrow = 3
    tools: [default, tool2, tool3]
    """
