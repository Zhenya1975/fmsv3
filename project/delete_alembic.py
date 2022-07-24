from psycopg2 import connect
import psycopg2

config = {
    # "host": "localhost",
    "dbname": "fms_v3_db",
    "user": "postgres",
    "password": "123456",
    "port": "5432"
}


def query():

    sql_query = 'DROP TABLE IF EXISTS alembic_version;'
    with connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_query)
            # res = cur.fetchall()
            # print(res)


query()
