import sys
import logging
import socket
# to import from a dir
sys.path.append('../')
from database import SqlDatabase
from backend_consts import *

def run():
    with SqlDatabase(DB_IP, DB_PASS) as database,\
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:

        server_sock.bind((SERVER_IP, SERVER_PORT))
        server_sock.listen()

        try:
            while True:
                conn, addr = server_sock.accept()
                logging.info(f"[NEW CLIENT] Client {addr} joined")

        except KeyboardInterrupt:
            logging.info("[SERVER EXIT]: Server closed forcefully")


if __name__ == "__main__":
    run()

