from database import *
from authN import *

def login(conn: DefaultConnection, db: Database) -> bool:
    """
    Use: add the the new user to the database, and 
    """
    login_succeeded = True

    username, password_bytes = recv_credentials(conn)
    if not db.user_in_database(username):
        db.add_user_to_database(username, *db.get_user_credentials(password_bytes))
    else:
        login_succeeded =  verify_credentials(*db.get_user_credentials(username))  # get salt and verify creds

    return login_succeeded



def recv_credentials(conn: DefaultConnection) -> tuple[str, bytes]:
    """
    Use: recevie symatric encrypted (by the shared key) username and password and decrypt them.
    """
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

if __name__ == "__main__":
    host = input("[Enter host]: ")
    db = Database(host)
    #print(db.user_in_database("second_reem"))
    #db.add_user_to_database("second_reem", "secertPass", "asdfasdljwr49033")
    print(db.get_user_credentials("second_reem"))
    db.print_table(USERS_CREDENTIALS_TABLE)
