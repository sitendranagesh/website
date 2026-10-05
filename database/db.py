import os
import sqlite3
from pathlib import Path

# Configurable database file path; defaults to 'notes_database.db' in the database directory.
DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent / "notes_database.db"
SQLITE_PATH = Path(os.environ.get("SQLITE_DB_PATH", DEFAULT_SQLITE_PATH))


def get_connection() -> sqlite3.Connection:
    """
    Returns an SQLite connection configured with:
    - Row factory (sqlite3.Row) for dict/column access
    - WAL journal mode for high-concurrency read/write
    - Foreign key constraints enabled
    - 5-second busy timeout to avoid lock contention
    """
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn