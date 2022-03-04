"""Logins to the server"""
# to import common.comms
import sys
sys.path.append( '.' )

from common.comms import DefaultConnection, PacketID
from cryptography.fernet import Fernet


def login(username: str, password: str, conn: DefaultConnection):
    fernet = Fernet(conn.key)
    username_token = fernet.encrypt(username.encode())
    password_token = fernet.encrypt(password.encode())
    conn.send(username_token, PacketID.INITIAL_AUTH)
    conn.send(password_token, PacketID.INITIAL_AUTH)
    