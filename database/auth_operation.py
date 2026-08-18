import bcrypt
from database.db import get_connection, is_postgres, placeholder


def create_users_table():
    conn = get_connection()
    cur = conn.cursor()
    if is_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()


def add_user(username: str, password: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cur.execute(
            f"INSERT INTO users (username, password_hash) VALUES ({p}, {p})",
            (username, hashed.decode("utf-8")),
        )
        conn.commit()
        return "User created successfully"
    except Exception:
        conn.rollback()
        return "Username already exists"
    finally:
        conn.close()


def verify_user(username: str, password: str) -> bool:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT password_hash FROM users WHERE username = {p}", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    stored_hash = row["password_hash"].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)