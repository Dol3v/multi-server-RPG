"""Utils for checking collision between players."""
from backend.logic.entity_logic import Player, EntityManager
from common.consts import Pos, SPEED, WORLD_WIDTH, WORLD_HEIGHT, EntityType
from common.utils import is_empty


def moved_reasonable_distance(new: Pos, prev: Pos, seqn_delta: int) -> bool:
    bound = 0
    if diff1 := abs(new[0] - prev[0]) != 0:
        bound += SPEED
    if diff2 := abs(new[1] - prev[1]) != 0:
        bound += SPEED
    return diff1 + diff2 <= bound * seqn_delta


def invalid_movement(entity: Player, player_pos: Pos, seqn: int, manager: EntityManager) -> bool:
    """check if a given player movement is valid"""
    return entity.last_updated != -1 and (not moved_reasonable_distance(
        player_pos, entity.pos, seqn - entity.last_updated) or
                                          not is_empty(
                                              manager.get_collidables_with(player_pos, entity.uuid,
                                                                           kind=EntityType.PLAYER))
                                          or not (0 <= player_pos[0] <= WORLD_WIDTH)
                                          or not (0 <= player_pos[1] <= WORLD_HEIGHT))
