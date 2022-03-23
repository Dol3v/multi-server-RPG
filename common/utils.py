import struct
from typing import Iterable


def create_packet(packet_format: str, data: list) -> bytes | None:
    """
    Use: create a packet in the given format and data
    Return value: the new packet bytes, or None
    """
    try:
        return struct.pack(packet_format, *data)
    except struct.error:
        return None


def parse(parse_format: str, data: bytes) -> tuple | None:
    """
    Use: parse a given message by the given format
    """
    try:
        return struct.unpack(parse_format, data)
    except struct.error:
        return None


def flatten(iterable: Iterable) -> list:
    """
    Flattens an iterable of iterables (list of tuples, for instance) to a shallow list in the expected way.
    **Example**
    flatten([(1, 3), (2, 4 ,5)]) = [1, 3, 2, 4, 5]
    :param iterable: iterable to flatten
    """
    return list(sum(iterable, ()))
