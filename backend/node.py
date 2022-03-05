from database import *
from authN import *

def login(conn: DefaultConnection) -> bool:
    """
    Use: add the the new user to the database, and 
    """
    login_succeeded = True

    username, password_bytes = recv_credentials(conn)
    if not user_in_database(username):
        add_user_to_database(username, *get_user_credentials(password_bytes))
    else:
        login_succeeded =  verify_credentials(*get_user_credentials(username))  # get salt and verify creds

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
    db = database(host)
