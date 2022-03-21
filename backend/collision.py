"""Utils for checking collision between players."""
from typing import Iterable

from common.consts import CLIENT_WIDTH, CLIENT_HEIGHT, Pos


def players_are_colliding(player_center: Pos, other_center: Pos) -> bool:
    """Checks if two players are colliding with each other."""
    return (0 <= abs(player_center[0] - other_center[0]) <= CLIENT_WIDTH) and \
           (0 <= abs(player_center[1] - other_center[1]) <= CLIENT_HEIGHT)


def get_colliding_entities(player_pos: Pos, *, entities_to_check: Iterable[Pos]):
    """Returns all entities that collided with a given player."""
    # would have refactored players_are_colliding into an inner function, but it'll prob be more complicated in the
    # future
    # TODO: optimize the sh*t out of this routine
    return filter(lambda pos: players_are_colliding(pos, player_pos), entities_to_check)
