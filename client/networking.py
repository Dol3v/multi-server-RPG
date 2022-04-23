"""Utils for communicating with the server"""
import base64
import json

from cryptography.fernet import Fernet

from player import Player
from common.message_type import MessageType


def parse_message(data: bytes, fernet: Fernet) -> dict:
    return json.loads(fernet.decrypt(data))


def craft_client_message(message_type: MessageType, client_uuid: str, contents: dict, fernet: Fernet) -> bytes:
    return json.dumps({"uuid": client_uuid,
                       "contents": base64.b64encode(fernet.encrypt(json.dumps({"id": int(message_type)} |
                                                    contents).encode())).decode()}).encode()


def generate_client_routine_message(player_uuid: str, seqn: int, x: int, y: int, player: Player, chat_message: str,
                                    fernet: Fernet) -> bytes:
    return craft_client_message(MessageType.ROUTINE_CLIENT, player_uuid, {
        "pos": (x, y),
        "seqn": seqn,
        "chat": chat_message,
        "dir": player.get_direction_vec(),
        "slot": player.current_slot,
        "is_attacking": player.attacking
    }, fernet)
