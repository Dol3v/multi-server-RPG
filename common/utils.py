import struct
from typing import Iterable


def parse(parse_format: str, data: bytes) -> tuple | None:
    """
    Use: parse a given message by the given format
    """
    try:
        return struct.unpack(parse_format, data)
    except struct.error:
        return None


def flatten(iterable: Iterable) -> list:
    """Flattens an iterable of iterables (list of tuples, for instance) to a shallow list in the expected way.
    **Example**
    flatten([(1, 3), (2, 4 ,5)]) = [1, 3, 2, 4, 5]
    :param iterable: iterable to flatten"""
    return list(sum(iterable, ()))