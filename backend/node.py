import logging
import socket
import sys
import threading

from typing import List
from collections import defaultdict

# to import from a dir
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

    def update_entity(self) -> Tuple[Addr, Pos]:
        """
        Use: receive client message from the server
        """
        data, addr = self.server_sock.recvfrom(RECV_CHUNK)
        seqn, x, y, chat, attacked, *attack_dir, equipped_id = parse_client_message(data)  
        # postions
        player_pos = (x, y)
        secure_pos = VALID_POS

        # if the received packet is dated then update entity
        if self.entities[addr].last_updated < seqn:
            entity = self.entities[addr]

            if invalid_movement(entity, player_pos, seqn):
                secure_pos = self.entities[addr].pos
                
            entity.update(player_pos, CLIENT_WIDTH, CLIENT_HEIGHT, attacked, seqn, health_change=-1)

        return addr, secure_pos


    def update_client(self, addr: Addr, secure_pos: Pos) -> None:
        """
        Use: sends server message to the client
        """
        new_chat = ""
        entity = self.entities[addr]

        
        entities_array = flatten(map(lambda e: (e.ID, *e.pos, *e.direction), self.entities_in_range(entity)))
        print(entities_array)

        # generate and send message
        update_packet = generate_server_message(entity.tools, new_chat, secure_pos, entity.health, entities_array)
        self.server_sock.sendto(update_packet, addr)

    def handle_client(self):
        """
        Use: communicate with client
        """
        while True:

            try:
                client_addr, secure_pos = self.update_entity()

                self.update_client(client_addr, secure_pos)

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


def invalid_movement(entity: Entity, player_pos: Pos, seqn: int) -> bool:
    """
    Use: check if a given player movement is valid
    TODO: Dolev here check if path is free
    """
    
    return entity.last_updated != -1 and not moved_reasonable_distance(
            player_pos, entity.pos, seqn - entity.last_updated)

   #in_range = self.entities_in_range(entity)

   ## collision
   #colliding_players = list(get_colliding_entities_with(entity, entities_to_check=in_range))

   #if len(colliding_players) == 1:
   #    print("Collision")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.WARNING)
    Node(SERVER_PORT)
