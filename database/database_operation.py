from database.db import get_connection, is_postgres, placeholder


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    if is_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                note TEXT NOT NULL,
                notecontent TEXT NOT NULL,
                CONSTRAINT notes_note_unique UNIQUE (note)
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
        _ensure_unique_note_titles(conn)
    conn.commit()
    conn.close()


def _ensure_unique_note_titles(conn) -> None:
    cur = conn.cursor()
    index_name = "idx_notes_note_unique"
    existing_indexes = {row[1] for row in cur.execute("PRAGMA index_list(notes)").fetchall()}
    if index_name in existing_indexes:
        return

    duplicate_titles = cur.execute(
        "SELECT note FROM notes GROUP BY note HAVING COUNT(*) > 1"
    ).fetchall()
    if duplicate_titles:
        cur.execute(
            "DELETE FROM notes WHERE id NOT IN ("
            "SELECT MAX(id) FROM notes GROUP BY note"
            ")"
        )
    cur.execute(f"CREATE UNIQUE INDEX {index_name} ON notes(note)")


def add_note(note: str, notecontent: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO notes (note, notecontent) VALUES ({p}, {p})", (note, notecontent))
        conn.commit()
        return "Note added successfully"
    except Exception:
        conn.rollback()
        return "Note title already exists"
    finally:
        conn.close()


def delete_note(note: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM notes WHERE note = {p}", (note,))
    conn.commit()
    conn.close()
    return "Note deleted successfully"


def update_note(note: str, notecontent: str) -> str:
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE notes SET note = {p}, notecontent = {p} WHERE note = {p}",
            (note, notecontent, note),
        )
        conn.commit()
        return "Note updated successfully"
    except Exception:
        conn.rollback()
        return "Note title already exists"
    finally:
        conn.close()


def get_notes_by_title(title: str):
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM notes WHERE note = {p} ORDER BY id DESC", (title,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_notes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()