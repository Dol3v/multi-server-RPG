"""Login/Load-balancing server"""
import logging
import sys
import uuid
import socket
import struct
from threading import Thread
from typing import Tuple, List
from dataclasses import dataclass

# to import from a dir
sys.path.append('../')
from consts import DB_PASS, CREDENTIALS_PACKET_SIZE
from authentication import login, signup, parse_credentials
from database import SqlDatabase
from networking import do_ecdh
from common.consts import ROOT_IP, ROOT_PORT, Addr, REDIRECT_FORMAT, NODE_PORT, NODE_COUNT, DEFAULT_ADDR

from common.utils import valid_ip

@dataclass
class ClientData:
    addr: Addr = DEFAULT_ADDR
    uuid: str = uuid.uuid4()

@dataclass
class NodeData:
    ip: str
    conn: socket.socket
    clients_info : List[ClientData]
    

class EntryNode:
    """Node that all clients will initially access."""

    thread_count = 1

    def __init__(self, db: SqlDatabase, sock: socket.socket):
        self.sock = sock
        self.db_conn = db
        # addresses currently connected to a given server
        self.nodes: List[NodeData] = []


    def get_minimal_load_server(self):
        """
        get the Node with the smallest number of clients
        """
        return min(self.nodes, key=lambda n: len(n.clients_info))


    def handle_incoming_players(self):
        while True:
            conn, addr = self.sock.accept()
            shared_key = do_ecdh(conn)
            is_login, username, password = parse_credentials(shared_key, conn.recv(CREDENTIALS_PACKET_SIZE))
            if is_login:
                success, error_msg = login(username, password, self.db_conn)
            else:
                success, error_msg = signup(username, password, self.db_conn)

            logging.info(f"Error Msg: {error_msg}")
            # find addr entites {:client count}
            target_node = self.get_minimal_load_server()

            # uuid & addr
            logging.info(f"client redirected to {target_node.ip}")
            conn.send(struct.pack(REDIRECT_FORMAT, target_node.ip.encode(), success, len(error_msg)) + error_msg.encode())
            # update redirected node for the upcoming client
            # [uuid, addr]
            
            if success:
                # self.nodes[]

                ...
            conn.close()

    def init_nodes(self):
        """
        """
        for node in range(NODE_COUNT):
            ip = input(f"Enter {node=} ip: ")
            if not valid_ip(ip):
                continue

            self.nodes.append(NodeData(ip, None, [ClientData()]))
        print(self.nodes)

    def run(self):

        self.init_nodes()

        threads = []
        self.sock.listen()
        for _ in range(self.thread_count):
            threads.append(Thread(target=self.handle_incoming_players))

        for thread in threads:
            thread.start()

REDIRECT_FORMAT
if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.INFO)
    sock = socket.socket()
    sock.bind((ROOT_IP, ROOT_PORT))
    db = SqlDatabase("127.0.0.1", DB_PASS)
    node = EntryNode(db, sock)
    node.run()
