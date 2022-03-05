# to import from a dir
import sys
sys.path.append( '.' )

from common.comms import DefaultConnection, PacketID
from cryptography.fernet import Fernet
from game import Game



def login(username: str, password: str, conn: DefaultConnection):
    """
    Use: login to the server
    """
    fernet = Fernet(conn.key)

    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())

    conn.send(username_token, PacketID.INITIAL_AUTH)
    conn.send(password_token, PacketID.INITIAL_AUTH)
    

if __name__ == "__main__":

    with DefaultConnection() as conn:
        username = input("Enter username: ")
        password = input("Enter password: ")

        login(username, password, conn)


        game = Game()
        game.run()