from enum import IntEnum, auto


class MessageType(IntEnum):
    """Message type enum."""
    ROUTINE_CLIENT = auto()
    CLOSED_GAME_CLIENT = auto()

    ROUTINE_SERVER = auto()
    NEW_CHAT_SERVER = auto()
    REDIRECT_SERVER = auto()
    DIED_SERVER = auto()
