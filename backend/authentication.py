import logging
import sys
from os import urandom

from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

# to import from a dir
sys.path.append('../')

from database import SqlDatabase
from database_utils import add_user_to_database, user_in_database, get_user_credentials
from common.utils import *
from consts import *


def parse_credentials(shared_key: bytes, data: bytes) -> Tuple[bool, str, bytes] | None:
    """
    Use: receive encrypted (by the shared key) username and password and decrypt them.
    """
    fernet = Fernet(urlsafe_b64encode(shared_key))
    try:
        login, data = bool(data[0]), data[1:]
        username_token, password_token = data[:FERNET_TOKEN_LENGTH], data[FERNET_TOKEN_LENGTH:]
        return login, fernet.decrypt(username_token).decode(), fernet.decrypt(password_token)
    except InvalidToken as e:
        logging.critical(f"Decryption of username/password failed {e=}")
        return None


def generate_hash_and_salt(password: bytes) -> Tuple[bytes, bytes]:
    """
    generate salt and hashed password
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
    verify user password by the hashed password in the database and the salt
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
    if user_in_database(db, username):
        return False, "User exists already"
    res = add_user_to_database(db, username, *generate_hash_and_salt(password))
    return (True, "") if res else (False, "Server encountered error while adding user to database")


def login(username: str, password: bytes, db: SqlDatabase) -> Tuple[bool, str]:
    """
    Verifies that the user's creds match up to existing creds in the database.
    :returns: if the login was successful, returns (True, None). Else, returns (False, err_msg)
    """
    if not user_in_database(db, username):
        return False, "User does not exist"
    creds = get_user_credentials(db, username)
    if not creds:
        return False, "Server encountered error while receiving client data"
    password_hash, salt = creds
    print(password_hash, salt)
    return (True, "") if verify_credentials(password_hash, password, salt) else (False, "Password does not match")


