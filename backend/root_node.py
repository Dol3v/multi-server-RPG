"""Login/Load-balancing server"""
import base64
import json
import logging
import queue
import socket
import sys
import uuid
from dataclasses import dataclass
from threading import Thread
from typing import List, Iterable, Set

# to import from a dir
import numpy as np
import select
from cryptography.fernet import Fernet

from backend.database.database_utils import load_user_info
from backend.networks.networking import S2SMessageType

sys.path.append('../')
from database import DB_PASS
from database import SqlDatabase

from networks import login, signup
from networks import do_ecdh

from common.utils import deserialize_json, serialize_json
from common.consts import ROOT_IP, ROOT_PORT, Addr, DEFAULT_ADDR, RECV_CHUNK, NUM_NODES, \
    WORLD_WIDTH, WORLD_HEIGHT, MIN_HEALTH, MAX_HEALTH
from backend_consts import ROOT_SERVER2SERVER_PORT


@dataclass
class ClientData:
    addr: Addr = DEFAULT_ADDR
    uuid: str = uuid.uuid4()


@dataclass
class NodeData:
    ip: str
    map_id: int
    clients_info: List[ClientData]
    conn: socket.socket


class EntryNode:
    """Node that all clients will initially access."""

    client_thread_count = 1

    def __init__(self, db: SqlDatabase, sock: socket.socket):
        self.servers_white_list = []
        self.sock = sock
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ROOT_IP, ROOT_PORT))

        self.db_conn = db
        # addresses currently connected to a given server
        self.nodes: List[NodeData] = []
        self.server2server = socket.socket()
        self.server2server.bind((ROOT_IP, ROOT_SERVER2SERVER_PORT))

        self.server_send_queue = queue.Queue()
        """Queue of messages to be broadcast-ed from the root to other nodes"""
        self.server_recv_queue = queue.Queue()
        """Queue of messages that are received from the other nodes"""

        self.connected_players: Set[str] = set()

    @property
    def conns(self) -> Iterable[socket.socket]:
        """Connections with server"""
        return map(lambda data: data.conn, self.nodes)

    def get_minimal_load_server(self):
        """get the Node with the smallest number of clients"""
        return min(self.nodes, key=lambda n: len(n.clients_info))

    def sender(self):
        """Sends messages to nodes"""
        while True:
            recipients, msg = self.server_send_queue.get()
            logging.info(f"[action] sending {msg=} to {recipients=}")
            for server in recipients:
                server.conn.send(json.dumps(msg).encode())

    def receiver(self):
        """Receives data from servers and puts in the queue."""
        while True:
            if not self.conns:
                break
            ready_socks, _, _ = select.select(self.conns, [], [])
            for readable in ready_socks:
                print("got here")
                self.server_recv_queue.put(readable.recv(RECV_CHUNK))

    def servers_handler(self):
        """Handles incoming packets from servers and responds accordingly."""
        while True:
            try:
                message = json.loads(self.server_recv_queue.get())
                logging.info(f"root: got {message=}")
                match S2SMessageType(message["status"]):
                    case S2SMessageType.PLAYER_CONNECTED:
                        self.connected_players.add(message["uuid"])
                    case S2SMessageType.PLAYER_DISCONNECTED:
                        self.connected_players.remove(message["uuid"])

            except KeyError | ValueError:
                continue

    def handle_incoming_players(self):
        while True:
            conn, addr = self.sock.accept()
            logging.info(f"[update] client with {addr=} tries to login/signup, {list(self.conns)}")
            shared_key = do_ecdh(conn)
            fernet = Fernet(base64.urlsafe_b64encode(shared_key))

            data = deserialize_json(conn.recv(RECV_CHUNK), fernet)
            is_login, username, password, client_game_addr = data["is_login"], data["username"], data["password"], \
                                                             data["game_addr"]
            initial_pos = self.get_initial_position()
            if is_login:
                success, error_msg, user_uuid = login(username, password.encode(), self.db_conn)
            else:
                success, error_msg, user_uuid = signup(username, password.encode(), self.db_conn)

            if not success:
                logging.info(f"[blocked] login/signup failed, error msg: {error_msg}")
                conn.send(serialize_json({"success": False, "error": error_msg}, fernet))
                conn.close()
                continue

            if user_uuid in self.connected_players:
                logging.info("player tried to login twice")
                conn.send(serialize_json({"success": False, "error": "logged in already"}, fernet))
                conn.close()
                continue

            target_node = self.get_minimal_load_server()

            data = {"id": S2SMessageType.PLAYER_LOGIN,
                    "key": base64.b64encode(shared_key).decode(),
                    "uuid": user_uuid,
                    "initial_pos": initial_pos,
                    "client_ip": client_game_addr[0],
                    "client_port": client_game_addr[1],
                    "is_login": False}

            if is_login:
                for row in load_user_info(self.db_conn, user_uuid):
                    data["is_login"] = True
                    _, initial_pos, hp, slot, inventory = row
                    data["initial_pos"] = initial_pos
                    data = data | {"initial_hp": MAX_HEALTH if hp < MIN_HEALTH else hp,
                                   "initial_slot": slot,
                                   "initial_inventory": inventory}

            conn.send(serialize_json({"ip": target_node.ip,
                                      "initial_pos": initial_pos,
                                      "uuid": user_uuid,
                                      "success": True}, fernet))

            self.server_send_queue.put(([target_node], data))
            conn.close()
            logging.info(f"client redirected to {target_node.ip}")

    def init_nodes(self):
        """Initializes nodes' data based on user input."""
        # for map_id in range(NUM_NODES):
        #     ip = enter_ip(f"Enter node {map_id} IP: ")
        #     self.servers_white_list.append(ip)
        self.servers_white_list.append("127.0.0.1")
        self.server2server.listen()
        map_id = 0

        while map_id < NUM_NODES:
            conn, addr = self.server2server.accept()
            if addr[0] not in self.servers_white_list:
                logging.warning(f"unauthorized server is trying to talk with root")
                continue

            logging.info(f"[update] accepted one server connection with {addr=}")

            # conn.send(struct.pack(map_id, ))
            self.nodes.append(NodeData(addr[0], map_id, [], conn))
            map_id += 1
        # TODO: send here the generated SQL password for user
        # self.server_send_queue.put()

    @staticmethod
    def get_initial_position():
        """Gets an initial position for the player,
        MAP NOTE: the function is in range but pygame didn't load the map for all places, so I will shrink the range """
        return int(np.random.uniform(0, WORLD_WIDTH // 3)), int(np.random.uniform(0, WORLD_HEIGHT // 3))

    def run(self):
        self.init_nodes()

        threads = []
        self.sock.listen()
        # # server2server threads
        threads.append(Thread(target=self.receiver))
        threads.append(Thread(target=self.sender))
        threads.append(Thread(target=self.servers_handler))

        # client handling threads
        for _ in range(self.client_thread_count):
            threads.append(Thread(target=self.handle_incoming_players))

        for thread in threads:
            thread.start()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.DEBUG)
    sock = socket.socket()
    db = SqlDatabase("127.0.0.1", DB_PASS)
    node = EntryNode(db, sock)
    node.run()
