"""Utils for checking collision between players."""

from common.consts import Pos, SPEED


def moved_reasonable_distance(new: Pos, prev: Pos, seqn_delta: int) -> bool:
    bound = 0
    if diff1 := abs(new[0] - prev[0]) != 0:
        bound += SPEED
    if diff2 := abs(new[1] - prev[1]) != 0:
        bound += SPEED
    return diff1 + diff2 <= bound * seqn_delta
