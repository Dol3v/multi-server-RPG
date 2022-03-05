import logging
from os import urandom
from sre_constants import SUCCESS
from typing import Tuple

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from common.consts import SCRYPT_KEY_LENGTH, SCRYPT_N, SCRYPT_P, SCRYPT_R
from common.comms import DefaultConnection

from db_api import *

def gen_hash_and_salt(password: bytes) -> Tuple[bytes, bytes]:
    """
    Use: generate salt and hashed passowrd
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
    Use: verify user password by the hashed password in the data base and the salt
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