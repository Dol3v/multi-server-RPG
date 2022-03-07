import logging
import sys
from os import urandom
from typing import Optional, Tuple
from base64 import urlsafe_b64encode

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from sqlalchemy import select, insert

from backend.database import SqlDatabase
from common.comms import DefaultConnection
from consts import SCRYPT_KEY_LENGTH, SCRYPT_N, SCRYPT_P, SCRYPT_R, USERNAME_COL, HASH_COL, SALT_COL
from common.utils import *

# to import from a dir
sys.path.append('.')


def gen_hash_and_salt(password: bytes) -> Tuple[bytes, bytes]:
    """
    Use: generate salt and hashed password
    """
    password_salt = urandom(16)
    kdf = Scrypt(
        salt=password_salt,
        length=SCRYPT_KEY_LENGTH,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return kdf.derive(password), password_salt


def verify_credentials(expected_key: bytes, unverified_password: bytes, salt: bytes) -> bool:
    """
    Use: verify user password by the hashed password in the database and the salt
    """
    kdf = Scrypt(
        salt=salt,
        length=SCRYPT_KEY_LENGTH,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    try:
        kdf.verify(unverified_password, expected_key)
    except InvalidKey:
        logging.info("User login failed")
        return False
    return True


def signup(username: str, password: bytes, db: SqlDatabase) -> Tuple[bool, str]:
    """
    Gets user credentials and tries to sign up. If successful, the user's credentials will be entered to the
    database, where byte data will be entered in base64 format.
    Returns whether the signup was successful.

    :param username: username
    :packet_id username: str
    :param password: user password
    :packet_id password: bytes
    :param db: database object
    :packet_id db: SqlDatabase
    :returns: if the signup was successful, returns (True, None). Else, returns (False, err_msg)
    """
    if user_in_database(username, db):
        return False, "User exists already"
    res = add_user_to_database(db, username, *gen_hash_and_salt(password))
    return (True, None) if res else (False, "Server encountered error while adding user to database")


def login(username: str, password: bytes, db: SqlDatabase) -> Tuple[bool, str]:
    """
    Verifies that the user's creds match up to existing creds in the database.

    :returns: if the login was successful, returns (True, None). Else, returns (False, err_msg)
    """
    if not user_in_database(username, db):
        return False, "User does not exist"
    creds = get_user_credentials(username, db)
    if not creds:
        return False, "Server encountered error while receiving client data"
    password_hash, salt = creds
    return (True, None) if verify_credentials(password_hash, password, salt) else (False, "Password does not match")


def recv_credentials(conn: DefaultConnection) -> Optional[Tuple[str, bytes]]:
    """
    Use: receive symmetrically encrypted (by the shared key) username and password and decrypt them.
    """
    fernet = Fernet(urlsafe_b64encode(conn.key))
    username = conn.recv()
    password = conn.recv()
    try:
        username = fernet.decrypt(username.content).decode()
        password = fernet.decrypt(password.content)

    except InvalidToken as e:
        logging.critical(f"Decryption of username/password failed {e=}")
        return None

    return username, password


def add_user_to_database(db: SqlDatabase, username: str, password_hash: bytes, password_salt: bytes):
    """
    Use: add user to the table
    """
    stmt = (
        insert(db.creds_table).values(username=username, password=base64_encode(password_hash),
                                      salt=base64_encode(password_salt))
    )
    return db.exec(stmt)


def user_in_database(username: str, db: SqlDatabase) -> bool:
    """
    Use: check if given username inside the database table
    """
    stmt = select(db.creds_table.c.username)
    columns = [row[USERNAME_COL] for row in db.exec(stmt)]
    return username in columns


def get_user_credentials(username: str, db: SqlDatabase) -> Optional[Tuple[bytes, bytes]]:
    """
    Use: get user hash and salt
    """
    stmt = select(db.creds_table)
    for row in db.exec(stmt):
        if username in row[USERNAME_COL]:
            return base64_decode(row[HASH_COL]), base64_decode(row[SALT_COL])
    return None