"""utils for database, using SqlDatabase class"""
from sqlalchemy import select, insert
from database import SqlDatabase
from typing import Optional, Tuple
from consts import USERNAME_COL, HASH_COL, SALT_COL
from common.utils import *

def save_user_info(db: SqlDatabase):
    """
    insert a new row inside the users_info table
    """
    
def load_user_info(db: SqlDatabase):
    """
    select and return the result of the given username (maybe change this to uuid?)
    """

def delete_user_info(db: SqlDatabase):
    """
    delete the row of the given username (maybe change this to uuid?)
    """

def add_user_to_database(db: SqlDatabase, username: str, password_hash: bytes, password_salt: bytes):
    """
    add user to the table
    """
    stmt = (
        insert(db.creds_table).values(username=username, password=base64_encode(password_hash),
                                      salt=base64_encode(password_salt))
    )
    return db.exec(stmt)


def user_in_database(db: SqlDatabase, username: str) -> bool:
    """
    check if given username inside the database table
    """
    stmt = select(db.creds_table.c.username)
    columns = [row[USERNAME_COL] for row in db.exec(stmt)]
    return username in columns


def get_user_credentials(db: SqlDatabase, username: str) -> Optional[Tuple[bytes, bytes]]:
    """
    get user hash and salt
    """
    stmt = select(db.creds_table)
    for row in db.exec(stmt):
        if username in row[USERNAME_COL]:
            return base64_decode(row[HASH_COL]), base64_decode(row[SALT_COL])
    return None
