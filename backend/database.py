import ssl
import logging

import sqlalchemy
from sqlalchemy import Text, Table, Column, MetaData, VARCHAR, insert, select

from consts import *


class Database:

    def __init__(self, db_hostname: str): 
        """
        Use: connect to the DB server through ssl by a given hostname
        """
        ssl_args = Database.generate_ssl_cert()

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
            logging.exception(f"[Cannot execute statment]: {statement}  \n", exc_info=True)


    
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


    def add_user_to_database(self, username: str, password_key: bytes, password_salt: bytes) -> None:
        """
        Use: add user to the table
        """
        # NOTE: if we add user that already inside the database, an error will occurr
        stmt = (
            insert(self.tables[USERS_CREDENTIALS_TABLE]).
            values(username=username, password=password_key, salt=password_salt)
        )
        self.execute_stmt(stmt)


    def user_in_database(self, username: str) -> bool:
        """
        Use: check if given username inside the database table
        """
        stmt = select(self.tables[USERS_CREDENTIALS_TABLE].c.username)
        columns = [row[USERNAME] for row in self.execute_stmt(stmt)]

        return username in columns

    def get_user_credentials(self, username: str):# -> Tuple[bytes, bytes]:
        """
        Use: get user hash and salt
        """
        stmt = select(self.tables[USERS_CREDENTIALS_TABLE])
        for row in self.execute_stmt(stmt):
            if username in row[USERNAME]:
                return row[HASH], row[SALT]
        
        return None
