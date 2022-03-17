import logging
import socket
import sys
import threading
from typing import Tuple

from backend_consts import *
from common.consts import CLIENT_FORMAT, INT_TO_BYTES
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
        return parse(CLIENT_FORMAT, contents)

    def encode_entity_locations_for_player(self, player_pos: Tuple[int, int]) -> bytes | None:
        # converts list of tuples into a list
        entities_pos = flatten(filter(lambda pos: pos != player_pos, self.entities.values()))
        msg_format = "l" + "l" * len(entities_pos)
        print(entities_pos, player_pos, entities_pos == player_pos)
        try:
            return struct.pack(msg_format, len(entities_pos) // 2, *entities_pos)
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
                    continue
                self.entities[addr] = player_pos
                update_msg = self.encode_entity_locations_for_player(player_pos)
                if not update_msg:
                    continue
                self.server_sock.sendto(update_msg, addr)

            except Exception as e:
                logging.error(e)

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
