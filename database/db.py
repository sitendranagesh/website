import os
import sqlite3
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_PATH = Path(__file__).resolve().parent / "notes_database.db"

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras


def is_postgres() -> bool:
    return DATABASE_URL is not None


def placeholder() -> str:
    return "%s" if is_postgres() else "?"


def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn