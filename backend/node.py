import logging
import socket
import sys
import threading

# to import from a dir
from collections import defaultdict
from typing import List

sys.path.append('../')

from common.consts import *
from common.utils import *
from backend.entity import Entity
from backend.collision import *
from backend.networking import generate_server_message, parse_client_message




class Node:

    def __init__(self, port) -> None:
        self.node_ip = SERVER_IP #socket.gethostbyname(socket.gethostname())
        self.address = (self.node_ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.entities = defaultdict(lambda: Entity())
        # Starts the node
        self.run()

    def entities_in_range(self, entity: Entity) -> List[Entity]:
        """
        Use: Returns all entities that are within render distance of each other.
        """

        def entity_in_range(pos1: Pos, pos2: Pos) -> bool:
            return (0 <= abs(pos1[0] - pos2[0]) < SCREEN_WIDTH // 2 + entity.width) and \
                   (0 <= abs(pos1[1] - pos2[1]) < SCREEN_HEIGHT // 2 + entity.height)

        return list(filter(lambda other: entity_in_range(entity.pos, other.pos) and other.pos != entity.pos,
                           self.entities.values()))

    def handle_client(self):
        """
        Use: communicate with client
        """
        while True:
            try:
                last_valid_pos = (-1, -1) 
                data, addr = self.server_sock.recvfrom(RECV_CHUNK)
                # update current player data
                seqn, x, y, *actions = parse_client_message(data) # action_array
                player_pos = x, y
                if self.entities[addr].last_updated >= seqn:
                    continue

                logging.debug(f"Received position {player_pos} from {addr=}")
                entity = self.entities[addr]

                # TODO: Dolev here check if path is free
                if entity.last_updated != -1 and not moved_reasonable_distance(
                        player_pos, entity.pos, seqn - entity.last_updated):

                    # Is this conventional?
                    player_pos = last_valid_pos = self.entities[addr].pos
                    print("Teleported")
                    

                # Update current entity
                entity.update(player_pos, CLIENT_WIDTH, CLIENT_HEIGHT, False, seqn, health_change=-1)
                in_range = self.entities_in_range(entity)

                # collision
                colliding_players = list(get_colliding_entities_with(entity, entities_to_check=in_range))

                if len(colliding_players) == 1:
                    print("Collision")

                # send relevant entities
                entities_array = flatten(map(lambda e: e.pos, in_range))
                update_msg = generate_server_message(entity.tools, last_valid_pos, entity.health, entities_array)
                self.server_sock.sendto(update_msg, addr)

                logging.debug(f"Sent positions {list(in_range)} to {addr=}")
            except Exception as e:
                logging.exception(e)


    def run(self) -> None:
        """
        Use: starts node threads
        """

        self.server_sock.bind(self.address)
        print(f"Node address: {self.address}")

        try:
            for i in range(THREADS_COUNT):
                # starts handlers threads
                client_thread = threading.Thread(target=self.handle_client)
                client_thread.start()

        except Exception as e:
            logging.exception(f"{e}")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.WARNING)
    Node(SERVER_PORT)
