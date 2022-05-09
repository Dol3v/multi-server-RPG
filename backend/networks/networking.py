import base64
import json
import logging
import socket
from enum import IntEnum, auto
from typing import Iterable, Dict, List, Any

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet

from backend.logic.entity_logic import EntityManager, Entity, Player
from common.consts import Pos, RECV_CHUNK, FIRE_BALL
from common.message_type import MessageType
from common.utils import send_public_key, get_shared_key, deserialize_public_key


class S2SMessageType(IntEnum):
    """Types of messages that are sent between servers."""
    PLAYER_LOGIN = auto()
    PLAYER_CONNECTED = auto()
    PLAYER_DISCONNECTED = auto()


def do_ecdh(conn: socket.socket) -> None | bytes:
    """Does the server part of ECDH, and returns the shared key."""
    client_key = conn.recv(RECV_CHUNK)
    try:
        client_public_key = deserialize_public_key(client_key)
    except ValueError:
        return None
    private_key = send_public_key(conn)
    return get_shared_key(private_key, client_public_key)


def decrypt_client_packet(parsed_packet: dict[str, Any], player_fernet: Fernet) -> dict | None:
    try:
        contents = json.loads(player_fernet.decrypt(base64.b64decode(parsed_packet["contents"])))
        parsed_packet["contents"] = contents
        return parsed_packet
    except KeyError as e:
        logging.warning(f"[error] invalid message from client, {parsed_packet=}, {e=}")
    except InvalidKey as e:
        logging.warning(f"[security] invalid key from client, {parsed_packet=}, {e=}")


def serialize_entity_list(entities: Iterable[Entity]) -> dict:
    """Serializes a list of entities to a JSON format."""
    return {"entities": [entity.serialize() for entity in entities]}


def craft_message(message_type: MessageType, message_contents: dict, fernet: Fernet) -> bytes:
    return fernet.encrypt(json.dumps({"id": int(message_type)} | message_contents).encode())


def generate_status_message(status: MessageType, fernet: Fernet) -> bytes:
    """Generates a message with no contents` useful for status updates."""
    return craft_message(status, {}, fernet)


def generate_routine_message(valid_pos: Pos, player: Player, sent_entities: Iterable[Entity]) -> bytes:
    return craft_message(MessageType.ROUTINE_SERVER, {"valid_pos": valid_pos,
                                                      "health": player.health,
                                                      "inventory": player.inventory,
                                                      "skill_id": player.skill_id} | serialize_entity_list(sent_entities),
                         player.fernet)
