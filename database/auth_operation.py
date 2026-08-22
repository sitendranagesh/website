import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
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

    _migrate_add_email_column(conn)
    _create_password_resets_table(conn)
    conn.commit()
    conn.close()


def _column_exists(conn, table: str, column: str) -> bool:
    cur = conn.cursor()
    if is_postgres():
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (table, column),
        )
        return cur.fetchone() is not None
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def _migrate_add_email_column(conn) -> None:
    if _column_exists(conn, "users", "email"):
        return
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    conn.commit()
    try:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique "
            "ON users(email) WHERE email IS NOT NULL"
        )
        conn.commit()
    except Exception:
        conn.rollback()


def _create_password_resets_table(conn) -> None:
    cur = conn.cursor()
    if is_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0
            )
        """)
    conn.commit()


def add_user(username: str, password: str, email: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        cur.execute(
            f"INSERT INTO users (username, password_hash, email) VALUES ({p}, {p}, {p})",
            (username, hashed.decode("utf-8"), email),
        )
        conn.commit()
        return "User created successfully"
    except Exception:
        conn.rollback()
        return "Username or email already exists"
    finally:
        conn.close()


def verify_user(username: str, password: str):
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT id, password_hash FROM users WHERE username = {p}", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return row["id"]
    return None


def get_user_id_by_email(email: str):
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM users WHERE email = {p}", (email,))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(user_id: int) -> str:
    """Generates a reset token, stores only its hash, and returns the raw
    token — only the raw token is ever emailed, never persisted."""
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    unused_val = False if is_postgres() else 0
    cur.execute(
        f"UPDATE password_resets SET used = {p} WHERE user_id = {p} AND used = {p}",
        (True if is_postgres() else 1, user_id, unused_val),
    )
    cur.execute(
        f"INSERT INTO password_resets (user_id, token_hash, expires_at, used) VALUES ({p}, {p}, {p}, {p})",
        (user_id, token_hash, expires_at, unused_val),
    )
    conn.commit()
    conn.close()
    return token


def verify_reset_token(token: str):
    token_hash = _hash_token(token)
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"SELECT user_id, expires_at, used FROM password_resets WHERE token_hash = {p}",
        (token_hash,),
    )
    row = cur.fetchone()
    conn.close()

    if not row or row["used"]:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        return None

    return row["user_id"]


def consume_reset_token_and_set_password(token: str, new_password: str) -> bool:
    user_id = verify_reset_token(token)
    if not user_id:
        return False

    token_hash = _hash_token(token)
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET password_hash = {p} WHERE id = {p}", (hashed.decode("utf-8"), user_id))
    cur.execute(
        f"UPDATE password_resets SET used = {p} WHERE token_hash = {p}",
        (True if is_postgres() else 1, token_hash),
    )
    conn.commit()
    conn.close()
    return True