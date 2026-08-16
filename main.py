from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database.database_operation import add_note, get_all_notes, update_note, get_notes_by_title, delete_note

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI()


@app.post("/note")
def add_notes(note_title: str, note_content: str):
    status = add_note(note_title, note_content)
    return {"status": status}

@app.get("/notes")
def get_notes():
    return get_all_notes()

@app.get("/note")
def get_a_note(title: str):
    return get_notes_by_title(title)

@app.put("/note")
def update_notes(note_title: str, note_content: str):
    update_note(note_title, note_content)
    return {"status": "notes updated successfully"}

@app.delete("/note")
def delete_notes(note_title: str):
    delete_note(note_title)

@app.get("/titles")
def list_notes():
    titles = []
    for note in get_all_notes():
        titles.append(note["note"])
    return titles

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")