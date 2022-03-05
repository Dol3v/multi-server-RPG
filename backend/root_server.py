from database import *

if __name__ == "__main__":
    host = input("[Enter host]: ")
    db = Database(host)
    db.write_tables()

    