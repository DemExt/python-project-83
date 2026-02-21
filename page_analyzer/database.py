import sqlite3
import os

def get_db_connection():
    conn = sqlite3.connect(os.getenv('SQLALCHEMY_DATABASE_URI', 'db.sqlite3'))
    conn.row_factory = sqlite3.Row
    return conn