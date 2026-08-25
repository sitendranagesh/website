from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os
import re

from database.database_operation import add_note, get_all_notes, update_note, get_notes_by_title, delete_note
from database.auth_operation import create_users_table, verify_user, add_user
from database.blog_operation import (
    init_blog_db,
    create_blog,
    update_blog,
    delete_blog,
    get_published_blogs,
    get_blog_by_slug,
    get_blog_by_id,
    get_all_blogs_for_user,
    get_all_tags,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INTRO_DIR = BASE_DIR / "intro"

app = FastAPI(title="Sitendra Platform & Blog", version="2.0.0")

SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "dev-secret-change-me")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Initialize database tables
create_users_table()
init_blog_db()

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


# =========================================================
# Pydantic Schemas for Blog Operations
# =========================================================
class BlogPayload(BaseModel):
    title: str
    content: str
    summary: Optional[str] = ""
    slug: Optional[str] = ""
    tags: Optional[str] = ""
    cover_image: Optional[str] = ""
    is_published: Optional[bool] = True


# =========================================================
# Authentication Helpers
# =========================================================
def require_login(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


def is_blog_subdomain(request: Request) -> bool:
    host = request.headers.get("host", "").lower().split(":")[0]
    return host.startswith("blog.")


# =========================================================
# Subdomain & Page Routing
# =========================================================
@app.get("/")
def root(request: Request):
    if is_blog_subdomain(request):
        return FileResponse(STATIC_DIR / "blog" / "index.html")
    
    # Main domain routing: if logged in -> notes dashboard, else -> login
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login.html")
    return RedirectResponse(url="/index.html")


@app.get("/about")
def about_page():
    intro_file = INTRO_DIR / "index.html"
    if intro_file.exists():
        return FileResponse(intro_file)
    return RedirectResponse(url="/")


# Direct Blog Routes (available on both main domain and subdomain)
@app.get("/blog")
@app.get("/blog/")
def blog_home():
    return FileResponse(STATIC_DIR / "blog" / "index.html")


@app.get("/blog/write")
@app.get("/write")
def blog_write(request: Request):
    if not request.session.get("user_id"):
        next_param = "/write" if is_blog_subdomain(request) else "/blog/write"
        return RedirectResponse(url=f"/login.html?next={next_param}")
    return FileResponse(STATIC_DIR / "blog" / "write.html")


@app.get("/blog/post/{slug}")
@app.get("/post/{slug}")
def blog_single_post(slug: str):
    return FileResponse(STATIC_DIR / "blog" / "post.html")


# =========================================================
# User Auth Endpoints
# =========================================================
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


# =========================================================
# Notes Endpoints (Existing App)
# =========================================================
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
    return {"status": "note deleted successfully"}


@app.get("/titles")
def list_notes(user_id: int = Depends(require_login)):
    titles = []
    for note in get_all_notes(user_id):
        titles.append(note["note"])
    return titles


# =========================================================
# Blog REST API Endpoints
# =========================================================
@app.get("/api/blogs")
def list_published_blogs(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Public: List published blogs with optional search and tag filters."""
    return get_published_blogs(search=search, tag=tag, limit=limit, offset=offset)


@app.get("/api/blogs/tags")
def list_blog_tags():
    """Public: Get all unique tags and their post counts."""
    return get_all_tags()


@app.get("/api/blogs/post/{slug}")
def fetch_single_blog(slug: str, increment: bool = True):
    """Public: Fetch a single blog post by its slug (increments view count)."""
    post = get_blog_by_slug(slug, increment_view=increment)
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return post


@app.get("/api/blogs/admin/my-posts")
def list_my_blogs(user_id: int = Depends(require_login)):
    """Author: Fetch all blogs (drafts & published) authored by current user."""
    return get_all_blogs_for_user(user_id)


@app.post("/api/blogs")
def create_new_blog(blog: BlogPayload, user_id: int = Depends(require_login)):
    """Author: Create a new blog post."""
    try:
        result = create_blog(
            user_id=user_id,
            title=blog.title,
            summary=blog.summary or "",
            content=blog.content,
            cover_image=blog.cover_image or "",
            tags=blog.tags or "",
            is_published=blog.is_published,
            custom_slug=blog.slug or "",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create blog: {str(e)}")


@app.put("/api/blogs/{blog_id}")
def update_existing_blog(blog_id: int, blog: BlogPayload, user_id: int = Depends(require_login)):
    """Author: Update an existing blog post."""
    try:
        result = update_blog(
            blog_id=blog_id,
            user_id=user_id,
            title=blog.title,
            summary=blog.summary or "",
            content=blog.content,
            cover_image=blog.cover_image or "",
            tags=blog.tags or "",
            is_published=blog.is_published,
            custom_slug=blog.slug or "",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update blog: {str(e)}")


@app.delete("/api/blogs/{blog_id}")
def delete_existing_blog(blog_id: int, user_id: int = Depends(require_login)):
    """Author: Delete a blog post."""
    try:
        return delete_blog(blog_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete blog: {str(e)}")


# =========================================================
# Static Files Mount
# =========================================================
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")