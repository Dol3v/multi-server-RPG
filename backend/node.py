import sys, logging, socket, threading

# to import from a dir
sys.path.append('../')
from database import SqlDatabase
from backend_consts import *

class Node:

    def __init__(self, ip, port):
        self.address = (ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.entities = {}
        # Starts the node
        self.run()


    def handle_clients(self):
        """
        Use: communicate with client
        param: conn: socket for communication
        """
        while True:
            data, addr = self.server_sock.recvfrom(1024) 
            print(f"[CLIENT]{addr}: {data}")

            self.server_sock.sendto(b"[SERVER]: hello from server", addr)



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

