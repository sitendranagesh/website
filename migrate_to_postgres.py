# migrate_to_postgres.py
import sqlite3
import os
import psycopg2

SQLITE_PATH = "database/notes_database.db"
DATABASE_URL = os.environ["DATABASE_URL"]  # set this to the EXTERNAL Render Postgres URL


def migrate():
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cur = pg_conn.cursor()

    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            note TEXT NOT NULL,
            notecontent TEXT NOT NULL,
            CONSTRAINT notes_note_unique UNIQUE (note)
        )
    """)
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    pg_conn.commit()

    notes = sqlite_conn.execute("SELECT note, notecontent FROM notes").fetchall()
    for row in notes:
        pg_cur.execute(
            "INSERT INTO notes (note, notecontent) VALUES (%s, %s) ON CONFLICT (note) DO NOTHING",
            (row["note"], row["notecontent"]),
        )

    try:
        users = sqlite_conn.execute("SELECT username, password_hash FROM users").fetchall()
        for row in users:
            pg_cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING",
                (row["username"], row["password_hash"]),
            )
    except sqlite3.OperationalError:
        print("No users table in SQLite — skipping user migration.")

    pg_conn.commit()
    sqlite_conn.close()
    pg_conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()