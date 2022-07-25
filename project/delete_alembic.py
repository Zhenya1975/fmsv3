# from psycopg2 import connect
import psycopg2

# connect to an existing database
conn = psycopg2.connect(
    database="fms_v3_db",
    user='postgres_fms_v3_user',
    password='123456',
    host='0.0.0.0'
)

# open cursor to perform database operations
cur = conn.cursor()

# query to database
cur.execute("SELECT * FROM 'competition_DB'")
rows = cur.fetchall()

if not len(rows):
    print('empty rows')
else:
    for row in rows:
        print(row)

# close connection
cur.close()
conn.close()

# config = {
#     # "host": "localhost",
#     "dbname": "fms_v3_db",
#     "user": "postgres",
#     "password": "123456",
#     "port": "5432"
# }
#
#
# def query():
#
#     sql_query = 'DROP TABLE IF EXISTS alembic_version;'
#     with connect(**config) as conn:
#         with conn.cursor() as cur:
#             cur.execute(sql_query)
#             # res = cur.fetchall()
#             # print(res)
#
#
# query()
