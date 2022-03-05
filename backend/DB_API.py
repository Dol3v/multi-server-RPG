import sqlalchemy
from sqlalchemy import Integer, MetaData, Text, Table, Column, MetaData
import ssl
from consts import *


def init_engine(db_user: str, db_pass: str, db_hostname: str , db_port: int, db_name: str): # -> Engine:
    """
    Use: connect to the DB server throght ssl
    """
    ssl_args = generate_ssl_cert()

    return sqlalchemy.create_engine(
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

# May not work...
def generate_ssl_cert(cert_path: str="") -> dict:
    """
    Use: generate certificats for ssl connection
    """
    ssl_context = ssl.create_default_context(cafile=cert_path)
    ssl_context.verify_mode = ssl.CERT_REQUIRED


    ssl_args = {"ssl" : ssl_context}

    return ssl_args

def init_tables(metadata: MetaData, engine) -> MetaData:

    Table(USERS_CREADS_TABLE , metadata,
        Column("id", Integer, primary_key=True),
        Column("username", Text),
        Column("password", Text),
        Column("salt", Text))

    metadata.create_all(bind=engine)
    return metadata
    

def init_DB():
    """
    Use: init DB talbes
    """
    DB_pass = input("[Enter DB password]: ")
    # connect to the localhost database
    engine = init_engine("host", DB_pass, "localhost", DB_PORT, DB_NAME)
    print(type(engine))
    engine.connect()
    metadata = MetaData()

    # init tables
    metadata = init_tables(metadata, engine)


    
def init_node_comm():
    """
    Use: start connection to the root server on the server's side
    """
    DB_pass = input("[Enter DB password]: ")
    DB_ip = input("[Enter DB password]: ")
    # connect to the database
    engine = init_engine("node", DB_pass, DB_ip, DB_PORT, DB_NAME)
    engine.connect()
    metadata = MetaData()

    # Equivalent to `SELECT * FROM my_table`
    query = sqlalchemy.select([USERS_CREADS_TABLE])  
    # a list of tuples of 
    answer = metadata.execute(query).fetchall()
    print(answer)
