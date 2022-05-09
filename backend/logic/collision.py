"""Utils for checking collision between players."""
import logging

from backend.logic.entity_logic import Player, EntityManager
from common.consts import Pos, SPEED, WORLD_WIDTH, WORLD_HEIGHT, EntityType
from common.utils import is_empty, get_entity_bounding_box


def moved_reasonable_distance(new: Pos, prev: Pos, seqn_delta: int) -> bool:
    bound = 0
    if diff1 := abs(new[0] - prev[0]) != 0:
        bound += SPEED
    if diff2 := abs(new[1] - prev[1]) != 0:
        bound += SPEED
    return diff1 + diff2 <= bound * seqn_delta


def invalid_movement(entity: Player, player_pos: Pos, seqn: int, manager: EntityManager) -> bool:
    """check if a given player movement is valid"""
    if entity.last_updated_seqn == -1:
        return False
    if not moved_reasonable_distance(player_pos, entity.pos, seqn - entity.last_updated_seqn):
        logging.warning(f"player {entity!r} moved more distance than it should, {seqn=}, {entity.last_updated_seqn=}")
        return True
    if not is_empty(manager.get_entities_in_range(get_entity_bounding_box(entity.pos, entity.kind),
                                                  entity_filter=lambda kind, player_uuid: (kind == EntityType.PLAYER
                                                  or kind == EntityType.MOB) and (player_uuid != entity.uuid))):
        logging.warning(
            f"player {entity!r} collided with things, collidables={list(manager.get_collidables_with(entity))}")
        return True
    if not (0 <= player_pos[0] <= WORLD_WIDTH) or not (0 <= player_pos[1] <= WORLD_HEIGHT):
        logging.warning(f"player {entity!r} is out of the world boundaries")
        return True
    return False
