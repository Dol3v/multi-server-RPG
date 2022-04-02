"""Login/Load-balancing server"""
import logging
import queue
import select
import socket
import struct
import sys
import uuid
from dataclasses import dataclass
from threading import Thread
from typing import List, Iterable

# to import from a dir
sys.path.append('../')
from consts import DB_PASS, CREDENTIALS_PACKET_SIZE, ROOT_SERVER2SERVER_PORT
from authentication import login, signup, parse_credentials
from database import SqlDatabase
from networking import do_ecdh
from common.consts import ROOT_IP, ROOT_PORT, Addr, REDIRECT_FORMAT, DEFAULT_ADDR, RECV_CHUNK, EMPTY_UUID


@dataclass
class ClientData:
    addr: Addr = DEFAULT_ADDR
    uuid: str = uuid.uuid4()


@dataclass
class NodeData:
    ip: str
    clients_info: List[ClientData]
    conn: socket.socket


class EntryNode:
    """Node that all clients will initially access."""

    client_thread_count = 1

    def __init__(self, db: SqlDatabase, sock: socket.socket):
        self.sock = sock
        self.db_conn = db
        # addresses currently connected to a given server
        self.nodes: List[NodeData] = []
        self.server2server = socket.socket()
        self.server2server.bind(("0.0.0.0", ROOT_SERVER2SERVER_PORT))
        self.server_send_queue = queue.Queue()
        """Queue of messages to be broadcast-ed from the root to other nodes"""
        self.server_recv_queue = queue.Queue()
        """Queue of messages that are received from the other nodes"""

    @property
    def conns(self) -> Iterable[socket.socket]:
        """Connections with server"""
        return map(lambda data: data.conn, self.nodes)

    def get_minimal_load_server(self):
        """
        get the Node with the smallest number of clients
        """
        return min(self.nodes, key=lambda n: len(n.clients_info))

    def sender(self):
        """Sends messages to nodes"""
        while True:
            recipients, msg = self.server_send_queue.get()
            for server in recipients:
                server.conn.send(msg)

    def receiver(self):
        """Receives data from servers and puts in the queue."""
        while True:
            if not self.conns:
                break
            ready_socks, _, _ = select.select(self.conns, [], [])
            for readable in ready_socks:
                self.server_recv_queue.put(readable.recv(RECV_CHUNK))

    def servers_handler(self):
        """Handles incoming packets from servers and responds accordingly."""
        ...

    def handle_incoming_players(self):
        while True:
            print("Got to func")
            conn, addr = self.sock.accept()
            print("Got here")
            logging.info(f"[update] client with {addr=} tries to login/signup")
            shared_key = do_ecdh(conn)
            is_login, username, password = parse_credentials(shared_key, conn.recv(CREDENTIALS_PACKET_SIZE))
            if is_login:
                success, error_msg, user_uuid = login(username, password, self.db_conn)
            else:
                success, error_msg, user_uuid = signup(username, password, self.db_conn)

            if not success:
                logging.info(f"[blocked] login/signup failed, error msg: {error_msg}")
                conn.send(struct.pack(REDIRECT_FORMAT, EMPTY_UUID, "0.0.0.0".encode(), success, len(error_msg))
                          + error_msg.encode())
                conn.close()
                continue

            target_node = self.get_minimal_load_server()
            # uuid & addr
            logging.info(f"client redirected to {target_node.ip}")
            conn.send(
                struct.pack(REDIRECT_FORMAT, user_uuid.encode(), target_node.ip.encode(),
                            success, len(error_msg)) + error_msg.encode())

            self.server_send_queue.put((target_node.conn, ))

            conn.close()

    def init_nodes(self):
        """
        Initializes nodes' data based on user input.
        """
        # for node_index in range(NODE_COUNT):
        #     ip = input(f"Enter {node_index=} ip: ")
        #     while not valid_ip(ip):
        #         ip = input(f"Enter {node_index=} ip: ")

        # # TODO: actually make this secure lmao
        # conn, data = self.server2server.accept()
        self.nodes.append(NodeData("127.0.0.1", [], None))

        # TODO: send here the generated SQL password for user
        # self.server_send_queue.put()

    def run(self):
        self.server2server.listen()
        self.init_nodes()

        threads = []
        self.sock.listen()
        # # server2server threads
        # threads.append(Thread(target=self.receiver))
        # threads.append(Thread(target=self.sender))

        # client handling threads
        for _ in range(self.client_thread_count):
            threads.append(Thread(target=self.handle_incoming_players))

        for thread in threads:
            thread.start()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.DEBUG)
    sock = socket.socket()
    sock.bind((ROOT_IP, ROOT_PORT))
    db = SqlDatabase("127.0.0.1", DB_PASS)
    node = EntryNode(db, sock)
    node.run()
