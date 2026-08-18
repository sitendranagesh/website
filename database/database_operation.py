from database.db import get_connection, is_postgres, placeholder


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                note TEXT NOT NULL,
                notecontent TEXT NOT NULL
            )
        """)
    else:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "note TEXT NOT NULL, "
            "notecontent TEXT NOT NULL"
            ")"
        )
    conn.commit()

    _migrate_add_user_id(conn)
    if not is_postgres():
        _ensure_unique_note_titles(conn)
    else:
        _ensure_unique_note_titles_pg(conn)

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
    else:
        cur.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cur.fetchall())


def _migrate_add_user_id(conn) -> None:
    """Adds user_id to notes if missing, and backfills existing rows
    to the first user found (assumes a single-user setup pre-migration)."""
    if _column_exists(conn, "notes", "user_id"):
        return

    cur = conn.cursor()
    if is_postgres():
        cur.execute("ALTER TABLE notes ADD COLUMN user_id INTEGER")
    else:
        cur.execute("ALTER TABLE notes ADD COLUMN user_id INTEGER")
    conn.commit()

    # Backfill: assign any existing (ownerless) notes to the first user in the users table
    p = placeholder()
    cur.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1")
    row = cur.fetchone()
    if row:
        first_user_id = row["id"] if hasattr(row, "keys") else row[0]
        cur.execute(f"UPDATE notes SET user_id = {p} WHERE user_id IS NULL", (first_user_id,))
        conn.commit()


def _ensure_unique_note_titles(conn) -> None:
    """SQLite: create the per-user unique index, deduplicating first if needed."""
    cur = conn.cursor()
    index_name = "idx_notes_user_note_unique"
    existing_indexes = {row[1] for row in cur.execute("PRAGMA index_list(notes)").fetchall()}

    # Drop the old global-uniqueness index if it's still around from before
    old_index_name = "idx_notes_note_unique"
    if old_index_name in existing_indexes:
        cur.execute(f"DROP INDEX {old_index_name}")

    if index_name in existing_indexes:
        return

    duplicate_titles = cur.execute(
        "SELECT user_id, note FROM notes GROUP BY user_id, note HAVING COUNT(*) > 1"
    ).fetchall()
    if duplicate_titles:
        cur.execute(
            "DELETE FROM notes WHERE id NOT IN ("
            "SELECT MAX(id) FROM notes GROUP BY user_id, note"
            ")"
        )
    cur.execute(f"CREATE UNIQUE INDEX {index_name} ON notes(user_id, note)")


def _ensure_unique_note_titles_pg(conn) -> None:
    """Postgres: same idea, using a constraint instead of a manual index."""
    cur = conn.cursor()
    cur.execute("""
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_name = 'notes' AND constraint_type = 'UNIQUE'
    """)
    existing = {row["constraint_name"] if hasattr(row, "keys") else row[0] for row in cur.fetchall()}

    if "notes_note_unique" in existing:
        cur.execute("ALTER TABLE notes DROP CONSTRAINT notes_note_unique")

    if "notes_user_note_unique" in existing:
        return

    cur.execute("""
        DELETE FROM notes a USING notes b
        WHERE a.id < b.id AND a.user_id = b.user_id AND a.note = b.note
    """)
    cur.execute("ALTER TABLE notes ADD CONSTRAINT notes_user_note_unique UNIQUE (user_id, note)")


def add_note(user_id: int, note: str, notecontent: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO notes (user_id, note, notecontent) VALUES ({p}, {p}, {p})", (user_id, note, notecontent))
        conn.commit()
        return "Note added successfully"
    except Exception:
        conn.rollback()
        return "Note title already exists"
    finally:
        conn.close()


def delete_note(user_id: int, note: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM notes WHERE user_id = {p} AND note = {p}", (user_id, note))
    conn.commit()
    conn.close()
    return "Note deleted successfully"


def update_note(user_id: int, note: str, notecontent: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE notes SET notecontent = {p} WHERE user_id = {p} AND note = {p}",
            (notecontent, user_id, note),
        )
        conn.commit()
        return "Note updated successfully"
    except Exception:
        conn.rollback()
        return "Note title already exists"
    finally:
        conn.close()


def get_notes_by_title(user_id: int, title: str):
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM notes WHERE user_id = {p} AND note = {p} ORDER BY id DESC", (user_id, title))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_notes(user_id: int):
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM notes WHERE user_id = {p} ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()