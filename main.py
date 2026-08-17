from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import os

from database.database_operation import add_note, get_all_notes, update_note, get_notes_by_title, delete_note
from database.auth_operation import create_users_table, verify_user

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI()

SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "dev-secret-change-me")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

create_users_table()


def require_login(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session["user"]


@app.get("/")
def root(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login.html")
    return RedirectResponse(url="/index.html")


@app.post("/login")
def login(request: Request, username: str, password: str):
    if verify_user(username, password):
        request.session["user"] = username
        return {"status": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "Logged out"}


@app.get("/me")
def get_current_user(request: Request):
    user = request.session.get("user")
    return {"logged_in": bool(user), "username": user}


@app.post("/note")
def add_notes(note_title: str, note_content: str, user: str = Depends(require_login)):
    status = add_note(note_title, note_content)
    return {"status": status}

@app.get("/notes")
def get_notes(user: str = Depends(require_login)):
    return get_all_notes()

@app.get("/note")
def get_a_note(title: str, user: str = Depends(require_login)):
    return get_notes_by_title(title)

@app.put("/note")
def update_notes(note_title: str, note_content: str, user: str = Depends(require_login)):
    update_note(note_title, note_content)
    return {"status": "notes updated successfully"}

@app.delete("/note")
def delete_notes(note_title: str, user: str = Depends(require_login)):
    delete_note(note_title)

@app.get("/titles")
def list_notes(user: str = Depends(require_login)):
    titles = []
    for note in get_all_notes():
        titles.append(note["note"])
    return titles


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")