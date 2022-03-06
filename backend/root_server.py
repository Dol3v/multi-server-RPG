import socket

from common.comms import PacketID
from authentication import *


def handle_signup_request(conn: DefaultConnection, db: SqlDatabase):
    username, password = recv_credentials(conn)
    result, error_msg = signup(username, password, db)
    if result:
        conn.send_status(PacketID.SERVER_OK)
    else:
        conn.send(error_msg.encode(), PacketID.SERVER_NOK)


if __name__ == "__main__":
    with SqlDatabase("127.0.0.1", "dummyPass") as database, socket.socket() as sock:
        database.write_tables()
        sock.bind(("127.0.0.1", 5000))
        sock.listen()
        while True:
            client_conn, addr = sock.accept()
            with DefaultConnection(client_conn) as connection:
                handle_signup_request(connection, database)


    