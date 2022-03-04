import sqlalchemy
from sqlalchemy import Column, Text, Table, Integer, MetaData
from sqlalchemy.engine.base import Engine

METADATA = None
ENGINE = None

PLAYER_CREDENTIALS_TABLE = None


def create_tables(db_engine: Engine):
    metadata = MetaData()
    metadata.drop_all(bind=db_engine)  # TODO: change
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


if __name__ == "__main__":
    engine = sqlalchemy.create_engine(f"mysql://dummy:dummyPass@localhost/users")
    METADATA = create_tables(engine)
    ENGINE = engine
