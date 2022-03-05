"""Logins to the server"""

from common.comms import DLS, PacketID
from cryptography.fernet import Fernet


def login(username: str, password: str, conn: DLS):
    fernet = Fernet(conn.key)
    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())
    conn.send(username_token, PacketID.INITIAL_AUTH)
    conn.send(password_token, PacketID.INITIAL_AUTH)
    