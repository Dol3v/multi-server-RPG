import socket
import sys

# to import from a dir
sys.path.append('../')
from game import Game
from consts import SERVER_PORT, SERVER_IP


def run():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        game = Game(sock, (SERVER_IP, SERVER_PORT))
        game.run()


if __name__ == "__main__":
    run()
