import socket
import sys

# to import from a dir
sys.path.append('../')
from game import Game
from consts import SERVER_PORT, SERVER_IP


def run():
    with socket.socket() as sock:

        sock.connect((SERVER_IP, SERVER_PORT))

        game = Game(sock)   
        game.run()



if __name__ == "__main__":
    run()
