import socket
import sys

# to import from a dir

from window import Window
from consts import SERVER_PORT, SERVER_IP


def run():
    window = Window()
    window.run()


if __name__ == "__main__":
    run()
