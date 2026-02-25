import os
import psycopg2
from urllib.parse import urlparse

def get_db_connection():
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    conn = psycopg2.connect(DATABASE_URL)
    return conn
