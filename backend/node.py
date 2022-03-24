import dataclasses
import logging
import socket
import sys
import threading
import uuid

# to import from a dir
from collections import defaultdict
from typing import List

import pyqtree as pyqtree

sys.path.append('../')

from common.consts import *
from common.utils import *
from backend.networking import generate_server_message, parse_client_message


@dataclasses.dataclass
class Entity:
    pos: Pos
    width: int
    height: int
    is_attacking: bool
    last_updated: int  # latest sequence number basically
    health: int

    # for solving "missing 6 required positional arguments"
    def __init__(self):
        self.health = MAX_HEALTH
        self.update()

    def update(self, pos=(-1, -1), width=-1, height=-1, is_attacking=False, last_updated=-1, health_change=MAX_HEALTH):
        self.pos = pos
        self.width = width
        self.height = height
        self.is_attacking = is_attacking
        self.last_updated = last_updated
        self.health += health_change # if health goes under 0 include then send server quit message.


def entities_are_colliding(entity: Entity, other: Entity) -> bool:
    """Checks if two players are colliding with each other. Assumes the entity's position is its center."""
    return (0 <= abs(entity.pos[0] - other.pos[0]) <= 0.5 * (entity.width + other.width)) and \
           (0 <= abs(entity.pos[1] - other.pos[1]) <= 0.5 * (entity.height + other.height))


def get_colliding_entities_with(entity: Entity, *, entities_to_check: Iterable[Entity]):
    """Returns all entities that collided with a given player."""
    # would have refactored players_are_colliding into an inner function, but it'll prob be more complicated in the
    # future
    # TODO: optimize the sh*t out of this routine
    return filter(lambda other: entities_are_colliding(entity, other), entities_to_check)


def moved_reasonable_distance(new: Pos, prev: Pos, seqn_delta: int) -> bool:
    bound = 0
    if diff1 := abs(new[0] - prev[0]) != 0:
        bound += SPEED
    if diff2 := abs(new[1] - prev[1]) != 0:
        bound += SPEED
    return diff1 + diff2 <= bound * seqn_delta


class Node:

    def __init__(self, port):
        self.node_ip = SERVER_IP#socket.gethostbyname(socket.gethostname())
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
                data, addr = self.server_sock.recvfrom(RECV_CHUNK)
                # update current player data
                seqn, x, y, *actions = parse_client_message(data) # action_array
                print(actions)
                player_pos = x, y
                if self.entities[addr].last_updated >= seqn:
                    continue

                logging.debug(f"Received position {player_pos} from {addr=}")
                # NOTE: this should not add new entities only the signup option should do that 
                entity = self.entities[addr]

                if entity.last_updated != -1 and not moved_reasonable_distance(
                        player_pos, entity.pos, seqn - entity.last_updated):
                    print("Teleported")

                entity.update(player_pos, CLIENT_WIDTH, CLIENT_HEIGHT, False, seqn)
                in_range = self.entities_in_range(entity)

                # collision
                colliding_players = list(get_colliding_entities_with(entity, entities_to_check=in_range))

                if len(colliding_players) == 1:
                    print("Collision")

                # send relevant entities
                update_msg = generate_server_message(flatten(map(lambda e: e.pos, in_range)))
                self.server_sock.sendto(update_msg, addr)

                logging.debug(f"Sent positions {list(in_range)} to {addr=}")
            except Exception as e:
                logging.exception(e)

    def run(self):
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
