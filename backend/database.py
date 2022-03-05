import ssl
import logging

import sqlalchemy
from sqlalchemy import Text, Table, Column, MetaData, VARCHAR, text

from consts import *
import sys
sys.tracebacklimit = 0

class database:

    def __init__(self, db_hostname: str): 
        """
        Use: connect to the DB server through ssl by a given hostname
        """
        ssl_args = database.generate_ssl_cert()

        self.engine = sqlalchemy.create_engine(
            # Equivalent URL:
            # mysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
            sqlalchemy.engine.url.URL.create(
                drivername=SQL_TYPE,
                username=DB_USERNAME,
                password=DB_PASS,
                host=db_hostname,
                port=DB_PORT,
                database=DB_NAME), connect_args=ssl_args,)

        # creates a metadata that updates with engine
        self.metadata = MetaData(bind=self.engine)

        # Tables
        #---------------------------------------------------------------------------
        self.tables = {
                        # Cerds
                        USERS_CREDENTIALS_TABLE: Table(USERS_CREDENTIALS_TABLE, self.metadata,
                                                    Column("username", VARCHAR(MAX_SIZE), primary_key=True),
                                                    Column("password", Text),
                                                    Column("salt", Text)), 
                                                    # TODO: Column("stats", stats table link),

                        # Stats 
                        PLAYER_STATS_TABLE: Table(PLAYER_STATS_TABLE, self.metadata,
                                                Column("username", VARCHAR(MAX_SIZE), primary_key=True),
                                                Column("skin", Text),
                                                Column("inventory", Text)), # TODO: change to array of Texts

                        # Chat
                        CHAT_TABLE: Table(CHAT_TABLE, self.metadata,
                                            Column("username", VARCHAR(MAX_SIZE), primary_key=True),
                                            Column("date", Text),
                                            Column("content", Text))
         }
        #---------------------------------------------------------------------------

    @ staticmethod
    def generate_ssl_cert(cert_path: str = "") -> dict:
        """
        Use: generate certificats for ssl connection
        """
        ssl_context = ssl.create_default_context(cafile=cert_path)
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        ssl_args = {"ssl": ssl_context}

        return ssl_args


    def execute_stmt(self, statement) : #-> :
        """
        Use: execute a commend on the database
        """
        try:
            with self.engine.connect() as conn:
                return conn.execute(statement)
        except Exception:
            logging.exception(f"[Cannot execute statment]: {statement} a\n", exc_info=True)


    
    def write_tables(self) -> None:
        """
        Use: gen tables if given engine and metadata
        """
        self.metadata.create_all(bind=self.engine)
    
    def print_table(self, table_name: str) -> None:
        """
        Use: prints a given table content
        """
        if table_name in self.tables:

            stmt = self.tables[table_name].select()
            try:
                res = self.execute_stmt(stmt).fetchall()
            except:
                ...

            print(f"Table len: {len(res)}")
            for row in res:
                print(row)



    def user_in_database(username: str) -> bool:
        ...


    def add_user_to_database(username: str, password_key: bytes, password_salt: bytes):
        ...

    def get_user_credentials(username: str):
        ...