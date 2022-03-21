import logging
import socket
import sys
import threading

# to import from a dir
from collections import defaultdict
from typing import Any

sys.path.append('../')

from collision import *
from client.consts import WIDTH, HEIGHT
from common.consts import *
from common.utils import *
from backend.networking import generate_server_message, parse_client_message


class EntityData:
    """Data to be stored about every entity"""
    __slots__ = ["data", "seqn"]

    def __init__(self, data: Any, seqn: int):
        self.data = data
        self.seqn = seqn


class Node:

    def __init__(self, ip, port):
        self.address = (ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.entities = {}
        self.sequences = defaultdict(lambda: -1)
        # Starts the node
        self.run()

    def entities_in_range(self, player_pos: Pos) -> list:
        """
        Use: Returns all entities that are within render distance of each other.
        """

        def entity_in_range(pos1: Pos, pos2: Pos) -> bool:
            return (0 <= abs(pos1[0] - pos2[0]) < WIDTH // 2 + CLIENT_WIDTH) and \
                   (0 <= abs(pos1[1] - pos2[1]) < HEIGHT // 2 + CLIENT_HEIGHT)

        return list(filter(lambda pos: entity_in_range(player_pos, pos) and pos != player_pos,
                           self.entities.values()))

    def handle_client(self):
        """
        Use: communicate with client
        """
        while True:
            try:
                data, addr = self.server_sock.recvfrom(RECV_CHUNK)
                # update current player data
                seqn, x, y = parse_client_message(data)
                player_pos = x, y
                if self.sequences[addr] >= seqn:
                    continue

                logging.debug(f"Received position {player_pos} from {addr=}")
                self.entities[addr] = player_pos
                entities = self.entities_in_range(player_pos)

                # collision
                colliding_players = list(get_colliding_entities(player_pos, entities_to_check=entities))

                if len(colliding_players) == 1:
                    print("Collision")

                # send relevant entities
                update_msg = generate_server_message(flatten(entities))
                self.server_sock.sendto(update_msg, addr)

                logging.debug(f"Sent positions {list(entities)} to {addr=}")
            except Exception as e:
                logging.exception(e)

    def run(self):
        """
        Use: starts node threads
        """

        self.server_sock.bind(self.address)
        try:
            for i in range(THREADS_COUNT):
                # starts handlers threads
                client_thread = threading.Thread(target=self.handle_client)
                client_thread.start()

        except Exception as e:
            logging.exception(f"{e}")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.WARNING)
    Node(SERVER_IP, SERVER_PORT)
