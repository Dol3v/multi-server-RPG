"""Login/Load-balancing server"""
import logging
import sys
import socket
import struct
from base64 import urlsafe_b64encode
from collections import defaultdict
from threading import Thread
from typing import Tuple, Dict, List
from dataclasses import dataclass
from authentication import login, signup
from cryptography.fernet import Fernet, InvalidToken

# to import from a dir
sys.path.append('../')
from consts import FERNET_TOKEN_LENGTH, CREDENTIALS_PACKET_SIZE, DB_PASS
from database import SqlDatabase
from networking import do_ecdh
from common.consts import ROOT_IP, ROOT_PORT, Addr, REDIRECT_FORMAT
import uuid

@dataclass
class ClientData:
    addr: Addr
    uuid: str = uuid.uuid4()

@dataclass
class NodeData:
    clients_info : List[ClientData]
    conn: socket.socket
    


# uuid, addr

def parse_credentials(shared_key: bytes, data: bytes) -> Tuple[bool, str, bytes] | None:
    """
    Use: receive encrypted (by the shared key) username and password and decrypt them.
    """
    fernet = Fernet(urlsafe_b64encode(shared_key))
    try:
        login, data = bool(data[0]), data[1:]
        username_token, password_token = data[:FERNET_TOKEN_LENGTH], data[FERNET_TOKEN_LENGTH:]
        return login, fernet.decrypt(username_token).decode(), fernet.decrypt(password_token)
    except InvalidToken as e:
        logging.critical(f"Decryption of username/password failed {e=}")
        return None


class EntryNode:
    """Node that all clients will initially access."""

    thread_count = 1

    def __init__(self, db: SqlDatabase, sock: socket.socket):
        self.sock = sock
        self.db_conn = db
        # addresses currently connected to a given server
        self.servers: Dict[Addr, NodeData] = {}

    def get_minimal_load_server(self):
        """

        """




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

            # uuid & addr
            conn.send(struct.pack(REDIRECT_FORMAT, '127.0.0.1'.encode(), success, len(error_msg)) + error_msg.encode())
            # send to the server
            # [uuid, addr]
            # 
            if success:
                # self.servers[]

                ...
            conn.close()

    def run(self):
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
