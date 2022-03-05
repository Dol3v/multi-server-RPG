from common.comms import DLS, PacketID
from cryptography.fernet import Fernet
from game import Game


def login(username: str, password: str, conn: DLS):
    """
    Use: login to the server
    """
    fernet = Fernet(conn.key)

    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())

    conn.send(username_token, PacketID.INITIAL_AUTH)
    conn.send(password_token, PacketID.INITIAL_AUTH)
    

if __name__ == "__main__":

    with DLS() as conn:
        username = input("Enter username: ")
        password = input("Enter password: ")

        login(username, password, conn)


        game = Game()
        game.run()