# db.py
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "dbname": "ingestion_db",
    "user": "postgres",
    "password": "my password",  #your password
    "host": "localhost",
    "port": "5432"
}

def get_conn():
    """Standard connection — returns rows as tuples."""
    return psycopg2.connect(**DB_CONFIG)

def get_dict_conn():
    """Dictionary connection — returns rows as {column: value} dicts."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn