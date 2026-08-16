import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "notes_database.db"

def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with get_connection() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "note TEXT NOT NULL, "
            "notecontent TEXT NOT NULL"
            ")"
        )
        _ensure_unique_note_titles(con)
        con.commit()

def _ensure_unique_note_titles(con: sqlite3.Connection) -> None:
    index_name = "idx_notes_note_unique"
    existing_indexes = {
        row[1] for row in con.execute("PRAGMA index_list(notes)").fetchall()
    }
    if index_name in existing_indexes:
        return

    duplicate_titles = con.execute(
        "SELECT note FROM notes GROUP BY note HAVING COUNT(*) > 1"
    ).fetchall()
    if duplicate_titles:
        con.execute(
            "DELETE FROM notes WHERE id NOT IN ("
            "SELECT MAX(id) FROM notes GROUP BY note"
            ")"
        )

    con.execute(f"CREATE UNIQUE INDEX {index_name} ON notes(note)")

def add_note(note: str, notecontent: str) -> str:
    try:
        with get_connection() as con:
            con.execute(
                "INSERT INTO notes (note, notecontent) VALUES (?, ?)",
                (note, notecontent),
            )
            con.commit()
        return "Note added successfully"
    except sqlite3.IntegrityError:
        return "Note title already exists"

def delete_note(note: str) -> str:
    with get_connection() as con:
        con.execute("DELETE FROM notes WHERE note = ?", (note,))
        con.commit()
    return "Note deleted successfully"

def update_note( note: str, notecontent: str) -> str:
    try:
        with get_connection() as con:
            con.execute(
                "UPDATE notes SET note = ?, notecontent = ? WHERE note = ?",
                (note, notecontent, note),
            )
            con.commit()
        return "Note updated successfully"
    except sqlite3.IntegrityError:
        return "Note title already exists"

def get_notes_by_title(title: str):
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM notes WHERE note = ? ORDER BY id DESC", (title,)
        ).fetchall()
    return [dict(r) for r in rows]

def get_all_notes():
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM notes ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]

init_db()

if __name__ == "__main__":
    add_note("first note", "my first note")
    add_note("second note", "my first note")
    delete_note("first note")
    # print(get_all_notes())
    # update_note("second note", "now it is the second note")
    print(get_notes_by_title("second note"))
