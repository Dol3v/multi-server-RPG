import struct


def parse(parse_format: str, data: bytes) -> tuple | None:
    """
    Use: parse a given message by the given format
    """
    try:
        return struct.unpack(parse_format, data)
    except struct.error:
        return None
