import psycopg2
from psycopg2.extras import NamedTupleCursor
import dotenv
import os

dotenv.load_dotenv("../.env")


def GetCursor(connection):
    return connection.cursor(cursor_factory=NamedTupleCursor)


def GetConnection():
    return psycopg2.connect(database=f'{os.getenv("NAME")}', user=f'{os.getenv("USER")}',
                            password=f'{os.getenv("PASSWORD")}', host=f'{os.getenv("HOST")}', port=os.getenv("PORT"))
