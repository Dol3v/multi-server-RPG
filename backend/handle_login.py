import logging
from os import urandom
from typing import Tuple

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from backend.consts import SCRYPT_KEY_LENGTH, SCRYPT_N, SCRYPT_P, SCRYPT_R
from comms import DefaultConnection


def get_credentials(conn: DefaultConnection) -> tuple[str, bytes]:
    fernet = Fernet(conn.key)
    username = conn.recv()
    password = conn.recv()
    try:
        username = fernet.decrypt(username.content).decode()
        password = fernet.decrypt(password.content)
    except InvalidToken as e:
        logging.critical(f"Decryption of username/password failed {e=}")
        return None
    return username, password


def get_password_salt_and_kdf(password: bytes) -> Tuple[bytes, bytes]:
    password_salt = urandom(16)
    kdf = Scrypt(
        salt=password_salt,
        length=SCRYPT_KEY_LENGTH,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    return kdf.derive(password), password_salt


def handle_login_conn(conn: DefaultConnection):
    username, password_bytes = get_credentials(conn)
    if not user_in_database(username):
        add_user_to_database(username, *get_password_salt_and_kdf(password_bytes))
    else:
        ...  # get salt and verify creds


def verify_credentials(expected_key: bytes, unverified_password: bytes, salt: bytes) -> bool:
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


def user_in_database(username: str) -> bool:
    ...


def add_user_to_database(username: str, password_key: bytes, password_salt: bytes):
    ...
