import socket
import sys
from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet

# to import from a dir
sys.path.append('../')
from common.communication import send, PacketID, get_shared_key, recv
from common.consts import PASSWORD_OFFSET_LENGTH, SERVER_PORT, SERVER_IP, IS_LOGIN_LENGTH
from game import Game



def send_credentials(username: str, password: str, conn: socket.socket, key: bytes, login=True):
    """
    Use: login to the server
    """
    fernet = Fernet(urlsafe_b64encode(key))

    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())
    is_login_byte = int.to_bytes(1 if login else 0, IS_LOGIN_LENGTH, "little")
    send(is_login_byte + len(username_token).to_bytes(PASSWORD_OFFSET_LENGTH, "little") + username_token
         + password_token, PacketID.LOGIN if login else PacketID.SIGNUP, conn, key)
    print("Sent")


if __name__ == "__main__":
    with socket.socket() as sock:
        sock.connect((SERVER_IP, SERVER_PORT))

        user = input("Enter username: ")
        user_pass = input("Enter password: ")

        shared_key = get_shared_key(sock)

        send_credentials(user, user_pass, sock, shared_key, False)

        response = recv(sock, shared_key)
        print(f"{response=}")
        if response.packet_type == PacketID.SERVER_NOK:
            print(response.content)
            sys.exit(1)
        print("Success!")

        game = Game(sock)   
        game.run()
