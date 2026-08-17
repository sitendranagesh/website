import sqlite3
import bcrypt
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "notes_database.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_users_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_user(username: str, password: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed.decode("utf-8")),
        )
        conn.commit()
        return "User created successfully"
    except sqlite3.IntegrityError:
        return "Username already exists"
    finally:
        conn.close()


def verify_user(username: str, password: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    stored_hash = row[0].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)