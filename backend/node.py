import logging
import queue
import sys
import threading
from collections import defaultdict
from typing import Dict, Set

import numpy as np
from cryptography.fernet import InvalidToken
from pyqtree import Index

# to import from a dir
from backend.logic.attacks import attack
from backend.logic.server_controlled_entities import server_entities_handler

sys.path.append('../')

from logic.entities_management import EntityManager
from common.consts import *
from common.utils import *
from consts import FRAME_TIME, MAX_SLOT, ROOT_SERVER2SERVER_PORT

from backend.logic.entities import *
from backend.networks.networking import generate_server_message, parse_client_message


class Node:
    """Server that receive and transfer data to the clients and root server"""
    def __init__(self, port):
        # TODO: uncomment when coding on prod
        # self.node_ip = socket.gethostbyname(socket.gethostname())
        self.node_ip = "127.0.0.1"
        self.address = (self.node_ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.root_sock = socket.socket()
        # TODO: remove when actually deploying exe
        # root_ip = enter_ip("Enter root's IP: ")

        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()

        self.socket_dict = defaultdict(lambda: self.server_sock)
        self.socket_dict[(ROOT_IP, ROOT_PORT)] = self.root_sock

        self.died_clients: Set[str] = set()
        self.should_join: Set[str] = set()

        self.entities_manager = EntityManager(WORLD_WIDTH, WORLD_HEIGHT)
        # Starts the node
        self.run()

    def update_location(self, player_pos: Pos, seqn: int, player: Player) -> Pos:
        """Updates the player location in the server and returns location data to be sent to the client.

        :param player: player to update
        :param player_pos: position of player given by the client
        :param seqn: sequence number given by the client
        :returns: ``DEFAULT_POS_MARK`` if the client position is fine, or the server-side-calculated pos for the client
        otherwise.
        """
        # if the received packet is dated then update player
        secure_pos = DEFAULT_POS_MARK
        if self.entities_manager.invalid_movement(player, player_pos, seqn) or seqn != player.last_updated + 1:
            logging.info(
                f"[update] invalid movement of {player.uuid=} from {player.pos} to {player_pos}. {seqn=}"
                f", {player.last_updated=}")
            secure_pos = self.entities_manager.players[player.uuid].pos
        else:
            self.entities_manager.update_entity_location(player, player_pos, EntityType.PLAYER)
        return secure_pos

    def update_client(self, player_uuid: str, secure_pos: Pos):
        """sends server message to the client"""
        player = self.entities_manager.players[player_uuid]
        entities_array = flatten(self.entities_manager.entities_in_rendering_range(player))
        # generate and send message
        update_packet = generate_server_message(player.tools, player.incoming_message, secure_pos, player.health,
                                                entities_array)
        self.server_sock.sendto(update_packet, player.addr)
        logging.debug(f"[debug] sent message to client {player.uuid=}")

    def receive_client_packet(self, player_uuid, data):
        try:
            data = self.entities_manager.players[player_uuid].fernet.decrypt(data[UUID_SIZE:])
        except InvalidToken:
            logging.warning(f"[security] player sent non-matching uuid={player_uuid}")
            return None
        except KeyError:
            logging.warning(f"{data=}")
            return None
        if player_uuid in self.died_clients:
            return None
        client_msg = parse_client_message(data)
        if not client_msg:
            return None

        return data

    def client_handler(self):
        """Communicate with client"""
        while True:
            data, addr = self.server_sock.recvfrom(RECV_CHUNK)
            player_uuid = data[:UUID_SIZE].decode()
            data = self.receive_client_packet(player_uuid, data)
            if not data:
                continue
            seqn, x, y, chat, _, attacked, *attack_dir, slot_index = parse_client_message(data)
            player_pos = x, y

            if player_uuid in self.should_join:
                self.entities_manager.add_entity(EntityType.PLAYER, player_uuid,
                                                 player_pos, CLIENT_HEIGHT, CLIENT_WIDTH)
                self.should_join.remove(player_uuid)

            if slot_index > MAX_SLOT or slot_index < 0:
                continue

            player = self.entities_manager.players[player_uuid]
            if seqn <= player.last_updated != 0:
                logging.info(f"Got outdated packet from {addr=}")
                continue

            player.attacking_direction = attack_dir
            player.new_message = chat.decode()
            secure_pos = self.update_location(player_pos, seqn, player)

            player.slot = slot_index
            if attacked:
                attack(self.entities_manager, player, player.tools[player.slot])

            self.broadcast_clients(player.uuid)
            self.update_client(player.uuid, secure_pos)
            player.last_updated = seqn

    def root_handler(self):
        """Receive new clients from the root infinitely
        TODO: make this function use networking.py
        NOTE: add msg_type
        """
        while True:
            data = self.root_sock.recv(RECV_CHUNK)
            shared_key, player_uuid = data[:SHARED_KEY_SIZE], data[SHARED_KEY_SIZE:SHARED_KEY_SIZE + UUID_SIZE].decode()
            initial_pos = struct.unpack(POSITION_FORMAT, data[SHARED_KEY_SIZE + UUID_SIZE:SHARED_KEY_SIZE +
                                                                                          UUID_SIZE + INT_SIZE * 2])
            ip, port = deserialize_addr(data[SHARED_KEY_SIZE + UUID_SIZE + INT_SIZE * 2:])
            logging.info(f"[login] notified player {player_uuid=} with addr={(ip, port)} is about to join")

            self.should_join.add(player_uuid)
            self.entities_manager.players[player_uuid] = Player(uuid=player_uuid, addr=(ip, port),
                                                                fernet=Fernet(base64.urlsafe_b64encode(shared_key)),
                                                                pos=initial_pos)

    def broadcast_clients(self, player_uuid: str):
        """Broadcast clients new messages to each other."""
        for uuid_to_broadcast in self.entities_manager.players:
            if player_uuid != uuid_to_broadcast:
                self.entities_manager.players[uuid_to_broadcast].incoming_message = \
                    self.entities_manager.players[player_uuid].new_message

    def run(self):
        """Starts node threads and bind & connect sockets"""
        self.server_sock.bind(self.address)
        self.root_sock.connect((ROOT_IP, ROOT_SERVER2SERVER_PORT)) # may case the bug
        logging.info(f"bound to address {self.address}")

        threading.Thread(target=server_entities_handler, args=(self.entities_manager,)).start()
        threading.Thread(target=self.root_handler).start()
        for _ in range(THREADS_COUNT):
            # starts handlers threads
            client_thread = threading.Thread(target=self.client_handler)
            client_thread.start()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.INFO)
    Node(NODE_PORT)
