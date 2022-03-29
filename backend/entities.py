import sched
import time
from dataclasses import dataclass, field
from typing import List, Tuple

from backend.consts import FRAME_TIME
from common.consts import Pos, MAX_HEALTH, SWORD, AXE, BOW, DEFAULT_POS_MARK, DEFAULT_DIR, EMPTY_SLOT


@dataclass
class Player:
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


@dataclass
class Projectile:
    pos: Pos = DEFAULT_POS_MARK
    direction: Tuple[float, float] = DEFAULT_DIR


@dataclass
class Bot:
    pos: Pos = DEFAULT_POS_MARK
    direction: Tuple[float, float] = DEFAULT_DIR
    health: int = MAX_HEALTH


ServerControlled = Projectile | Bot
"""Entity with server-controlled movements and actions"""

Attackable = Bot | Player
"""Entity that can be attacked."""

Entity = ServerControlled | Player
"""In game object with a position that should be rendered."""


def location_update(s, entities: List[ServerControlled]):
    """
    Use: update all projectiles and bots positions inside a loop
    """
    for entity in entities:
        entity.pos = entity.pos[0] + int(entity.direction[0]), entity.pos[1] + int(entity.direction[1])

    s.enter(FRAME_TIME, 1, location_update, (s, entities,))


def start_location_update(entities: List[ServerControlled]):
    """
    Use: starts the schedular and the function
    """
    s = sched.scheduler(time.time, time.sleep)
    s.enter(FRAME_TIME, 1, location_update, (s, entities,))
    s.run()
