import ssl

import sqlalchemy
from sqlalchemy import Text, Table, Column, MetaData, VARCHAR

from backend_consts import *


class SqlDatabase:

    def __init__(self, db_hostname: str, user_password: str):
        """
        Use: connect to the DB server through ssl by a given hostname

        :param db_hostname: ip address to connect to
        :param user_password: DB_USERNAME@"$db_hostname"'s password
        """
        ssl_args = SqlDatabase.generate_ssl_cert()

        self.engine = sqlalchemy.create_engine(
            # mysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
            sqlalchemy.engine.url.URL.create(
                drivername=SQL_TYPE,
                username=DB_USERNAME,
                password=user_password,
                host=db_hostname,
                port=DB_PORT,
                database=DB_NAME),
            connect_args=ssl_args
        )

        # creates a metadata that updates with engine
        self.metadata = MetaData(bind=self.engine)
        self.creds_table = Table(USERS_CREDENTIALS_TABLE, self.metadata,
                                 Column("username", VARCHAR(MAX_SIZE), primary_key=True),
                                 Column("password", Text),
                                 Column("salt", Text))
        self.players_table = Table(PLAYER_STATS_TABLE, self.metadata,
                                   Column("username", VARCHAR(MAX_SIZE), primary_key=True),
                                   Column("skin", Text),
                                   Column("inventory", Text))
        self.chat_table = Table(CHAT_TABLE, self.metadata,
                                Column("username", VARCHAR(MAX_SIZE), primary_key=True),
                                Column("date", Text),
                                Column("content", Text))

        self.conn = self.engine.connect()

    @staticmethod
    def generate_ssl_cert(cert_path: str = "") -> dict:
        """
        Use: generate certificates for ssl connection
        """
        ssl_context = ssl.create_default_context(cafile=cert_path)
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        ssl_args = {"ssl": ssl_context}

        return ssl_args

    def write_tables(self) -> None:
        """
        Use: gen tables given engine and metadata
        """
        self.metadata.create_all(bind=self.engine)

    def exec(self, statement):
        return self.conn.execute(statement)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
