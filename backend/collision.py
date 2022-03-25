"""Utils for checking collision between players."""
import pyqtree 
from typing import Iterable

from backend.entity import Entity
from common.consts import CLIENT_WIDTH, CLIENT_HEIGHT, Pos, SPEED


def entities_are_colliding(entity: Entity, other: Entity) -> bool:
    """Checks if two players are colliding with each other. Assumes the entity's position is its center."""
    return (0 <= abs(entity.pos[0] - other.pos[0]) <= 0.5 * (entity.width + other.width)) and \
           (0 <= abs(entity.pos[1] - other.pos[1]) <= 0.5 * (entity.height + other.height))


def get_colliding_entities_with(entity: Entity, *, entities_to_check: Iterable[Entity]):
    """Returns all entities that collided with a given player."""
    # would have refactored players_are_colliding into an inner function, but it'll prob be more complicated in the
    # future
    # TODO: optimize the sh*t out of this routine
    return filter(lambda other: entities_are_colliding(entity, other), entities_to_check)


def moved_reasonable_distance(new: Pos, prev: Pos, seqn_delta: int) -> bool:
    bound = 0
    if diff1 := abs(new[0] - prev[0]) != 0:
        bound += SPEED
    if diff2 := abs(new[1] - prev[1]) != 0:
        bound += SPEED
    return diff1 + diff2 <= bound * seqn_delta

