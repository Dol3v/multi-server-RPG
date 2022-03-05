import sqlalchemy
import ssl
from consts import *

class DB_communicator():
    """
    Use: engine tables 
    """
    # Members
    engine = None

    def init_engine(self, db_user: str, db_pass: str, db_hostname: str , db_port: int, db_name: str) -> None:
        """
        Use: connect to the DB server throght ssl
        """
        ssl_args = self.generate_ssl_cert()

        self.engine = sqlalchemy.create_engine(
            # Equivalent URL:
            # mysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
            sqlalchemy.engine.url.URL.create(
                drivername=SQL_TYPE,
                username=db_user, 
                password=db_pass, 
                host=db_hostname, 
                port=db_port,  
                database=db_name 
            ),
            connect_args=ssl_args, 
        )

    def init_table():
        pass

    def generate_ssl_cert(self, cert_path: str="") -> dict:
        """
        Use: generate certificats for ssl connection
        """
        ssl_context = ssl.create_default_context(cafile=cert_path)
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        print(ssl_context)

        ssl_args = {"ssl" : ssl_context}

        return ssl_args



if __name__ == "__main__":

    DB_communicator().connect_to_DB("host", SERVER_PASS, "localhost", DB_PORT, "DB-server")
    




"""
METADATA = create_tables(engine)
ENGINE = engine
from sqlalchemy import Column, Text, Table, Integer, MetaData
from sqlalchemy.engine.base import Engine
METADATA = None
ENGINE = None

PLAYER_CREDENTIALS_TABLE = None


def create_tables(db_engine: Engine):
    metadata = MetaData()
    
    global PLAYER_CREDENTIALS_TABLE  # TODO: change
    PLAYER_CREDENTIALS_TABLE = Table(
        "players_creds", metadata,
        Column("id", Integer, primary_key=True),
        Column("username", Text),
        Column("password", Text),
        Column("salt", Text)
    )

    metadata.create_all(bind=db_engine)
    return metadata
"""