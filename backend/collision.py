"""Utils for checking collision between players."""
from backend.consts import Pos
from common.consts import CLIENT_WIDTH, CLIENT_HEIGHT


def players_are_colliding(player_center: Pos, other_center: Pos) -> bool:
    """Checks if two players are colliding with each other."""
    return (0 <= abs(player_center[0] - other_center[0]) <= CLIENT_WIDTH) and\
           (0 <= abs(player_center[1] - other_center[1]) <= CLIENT_HEIGHT)
