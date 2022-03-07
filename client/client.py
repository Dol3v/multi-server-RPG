import socket
import sys

from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet

from common.comms import DefaultConnection
from common.communication import send, PacketID
from common.consts import PASSWORD_OFFSET_LENGTH
from game import Game

# to import from a dir
sys.path.append('.')


def send_credentials(username: str, password: str, conn: socket.socket, key: bytes, login=True):
    """
    Use: login to the server
    """
    fernet = Fernet(urlsafe_b64encode(key))

    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())
    send(len(username_token).to_bytes(PASSWORD_OFFSET_LENGTH, "little") + username_token + password_token,
         PacketID.LOGIN if login else PacketID.SIGNUP, conn, key)


if __name__ == "__main__":
    with socket.socket() as sock:
        sock.connect(("127.0.0.1", 5000))
        with DefaultConnection(sock) as connection:
            user = input("Enter username: ")
            user_pass = input("Enter password: ")

            send_credentials(user, user_pass, connection)

            response = connection.recv()
            if response.packet_type == PacketID.SERVER_NOK:
                print(response.content)
                sys.exit(1)
            print("Success!")
            game = Game()
            game.run()
