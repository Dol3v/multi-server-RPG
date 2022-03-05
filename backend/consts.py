SQL_TYPE = "mysql"
DB_PASS = "12" # TODO: make this more secure
DB_PORT = 9001
SERVER_PASS = "seceretPass"
# mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
ENGINE_SETTING =  f"{SQL_TYPE}://db:{DB_PASS}@localhost/DB-server?host=localhost?port={DB_PORT}"
