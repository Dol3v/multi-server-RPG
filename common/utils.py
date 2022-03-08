import base64


def base64_encode(raw: bytes, str_encoding="ascii") -> str:
    """Encodes raw byte data to str using base64 format."""
    base64_bytes = base64.b64encode(raw)
    return base64_bytes.decode(str_encoding)


def base64_decode(data: str, str_encoding="ascii") -> bytes:
    base64_bytes = data.encode(str_encoding)
    return base64.b64encode(base64_bytes)

