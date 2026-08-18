from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import os
import re

from database.database_operation import add_note, get_all_notes, update_note, get_notes_by_title, delete_note
from database.auth_operation import create_users_table, verify_user, add_user

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI()

SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "dev-secret-change-me")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

create_users_table()

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def require_login(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@app.get("/")
def root(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login.html")
    return RedirectResponse(url="/index.html")


@app.post("/signup")
def signup(request: Request, username: str, password: str):
    username = username.strip()

    if not USERNAME_PATTERN.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-20 characters: letters, numbers, underscores only.",
        )
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    status = add_user(username, password)
    if status != "User created successfully":
        raise HTTPException(status_code=400, detail=status)

    # Log the new user in immediately
    user_id = verify_user(username, password)
    request.session["user_id"] = user_id
    request.session["username"] = username
    return {"status": "Account created"}


@app.post("/login")
def login(request: Request, username: str, password: str):
    user_id = verify_user(username, password)
    if user_id:
        request.session["user_id"] = user_id
        request.session["username"] = username
        return {"status": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "Logged out"}


@app.get("/me")
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    username = request.session.get("username")
    return {"logged_in": bool(user_id), "username": username}


@app.post("/note")
def add_notes(note_title: str, note_content: str, user_id: int = Depends(require_login)):
    status = add_note(user_id, note_title, note_content)
    return {"status": status}

@app.get("/notes")
def get_notes(user_id: int = Depends(require_login)):
    return get_all_notes(user_id)

@app.get("/note")
def get_a_note(title: str, user_id: int = Depends(require_login)):
    return get_notes_by_title(user_id, title)

@app.put("/note")
def update_notes(note_title: str, note_content: str, user_id: int = Depends(require_login)):
    update_note(user_id, note_title, note_content)
    return {"status": "notes updated successfully"}

@app.delete("/note")
def delete_notes(note_title: str, user_id: int = Depends(require_login)):
    delete_note(user_id, note_title)

@app.get("/titles")
def list_notes(user_id: int = Depends(require_login)):
    titles = []
    for note in get_all_notes(user_id):
        titles.append(note["note"])
    return titles


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")