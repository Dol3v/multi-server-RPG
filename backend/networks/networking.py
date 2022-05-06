import base64
import json
import logging
import socket
from enum import IntEnum, auto
from typing import Iterable

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet

from backend.logic.entity_logic import EntityManager, Entity, Player
from common.consts import Pos, RECV_CHUNK
from common.message_type import MessageType
from common.utils import send_public_key, get_shared_key, deserialize_public_key


class S2SMessageType(IntEnum):
    """Types of messages that are sent between servers."""
    PLAYER_LOGIN = auto()


def do_ecdh(conn: socket.socket) -> None | bytes:
    """Does the server part of ECDH, and returns the shared key."""
    client_key = conn.recv(RECV_CHUNK)
    try:
        client_public_key = deserialize_public_key(client_key)
    except ValueError:
        return None
    private_key = send_public_key(conn)
    return get_shared_key(private_key, client_public_key)


def parse_message_from_client(packet: bytes, entity_manager: EntityManager) -> dict | None:
    try:
        message_json = json.loads(packet)
        player_fernet = entity_manager.players[message_json["uuid"]].fernet
        contents = json.loads(player_fernet.decrypt(base64.b64decode(message_json["contents"])))
        message_json["contents"] = contents
        return message_json
    except KeyError as e:
        logging.warning(f"[error] invalid message from client, {message_json=}, {e=}")
    except InvalidKey as e:
        logging.warning(f"[security] invalid key from client, {message_json=}, {e=}")


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
                                                      "inventory": player.inventory} | serialize_entity_list(sent_entities),
                         player.fernet)
