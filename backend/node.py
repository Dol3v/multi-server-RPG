import logging
import socket
import sys
import threading

from backend_consts import *
from common.protocol_api import *

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

    def handle_clients(self):
        """
        Use: communicate with client
        """
        while True:
            try:
                data, addr = self.server_sock.recvfrom(1024)
                # update current player data
                update_msg = encode_entity_locations(self.entities)

                # send message to client only if there is something to update
                if update_msg:
                    self.server_sock.sendto(update_msg, addr)

                self.entities[addr] = parse(CLIENT_FORMAT, data)

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
