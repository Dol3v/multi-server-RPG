import sqlalchemy
from sqlalchemy.engine.base import Connection


def init_db(db_conn: Connection):
    """
    Initializes tables and stuff.

    :param db_conn: Database Connection
    :type db_conn: Connection
    """
    ...


if __name__ == "__main__":
    engine = sqlalchemy.create_engine(f"mysql://dummy:dummyPass@localhost/users")
    db_connection = engine.connect()
    print(type(db_connection))
    metadata = sqlalchemy.MetaData()
    print(f"{db_connection=} {metadata=}")
