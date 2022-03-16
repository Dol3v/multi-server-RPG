import logging
import socket
import struct
import sys
import threading

from backend_consts import *
from common.utils import *

# to import from a dir
sys.path.append('../')


class Node:

    def __init__(self, ip, port):
        self.address = (ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # timeout of 0.5 seconds
        # self.server_sock.settimeout(0.5)
        self.entities = {}
        # Starts the node
        self.run()

    @staticmethod
    def parse_client_message(contents: bytes) -> tuple | None:
        try:
            return struct.unpack(CLIENT_FORMAT, contents)
        except struct.error:
            return None

    @staticmethod
    def encode_entity_locations_for_player(entities: dict, player_pos: Tuple[int, int]) -> bytes | None:
        """
        Use: generate the client message bytes by this format.
        Format: [entities in range + HP + invalid operation]
        """
        msg_format = "l" + "ll" * len(entities)
        # converts list of tuples into a list
        entities_pos = [item for t in filter(lambda val: entities.get(val) != player_pos, entities.values()) for item in
                        t]
        try:
            return struct.pack(msg_format, len(entities), *entities_pos)
        except Exception:
            return None

    def handle_clients(self):
        """
        Use: communicate with client
        """
        while True:
            try:
                data, addr = self.server_sock.recvfrom(1024)
                # update current player data
                player_pos = self.parse_client_message(data)
                if not player_pos:
                    break
                update_msg = self.encode_entity_locations_for_player(self.entities, player_pos=player_pos)
                self.server_sock.sendto(update_msg, addr)
                self.entities[addr] = player_pos

            except Exception as e:
                print(e)

    def run(self):
        """
        Use: starts node threads
        """

        self.server_sock.bind(self.address)

        try:
            for i in range(THREADS_COUNT):
                # starts thread per client
                client_thread = threading.Thread(target=self.handle_clients)
                client_thread.start()

        except Exception as e:
            logging.error(f"[SERVER Error]: {e}")


if __name__ == "__main__":
    Node(SERVER_IP, SERVER_PORT)
