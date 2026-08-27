from fastapi import FastAPI, Request, HTTPException, Depends, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, PlainTextResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime
import os
import re
import html

from database.database_operation import (
    add_note,
    get_all_notes,
    update_note,
    get_notes_by_title,
    delete_note,
    toggle_note_sharing,
    get_shared_note,
    save_quick_message,
)
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
    get_reactions_for_blog,
    add_reaction_to_blog,
    add_newsletter_subscriber,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INTRO_DIR = BASE_DIR / "intro"

app = FastAPI(title="Sitendra Multi-Subdomain Platform", version="3.0.0")

SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "dev-secret-change-me")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Initialize database tables
create_users_table()
init_blog_db()

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


# =========================================================
# Pydantic Schemas
# =========================================================
class BlogPayload(BaseModel):
    title: str
    content: str
    summary: Optional[str] = ""
    slug: Optional[str] = ""
    tags: Optional[str] = ""
    cover_image: Optional[str] = ""
    is_published: Optional[bool] = True


class NewsletterPayload(BaseModel):
    email: str


class ReactionPayload(BaseModel):
    reaction: str


class ShareNotePayload(BaseModel):
    title: str
    enable: Optional[bool] = True


# =========================================================
# Authentication Helpers
# =========================================================
def require_login(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


# =========================================================
# Multi-Subdomain Routing Engine
# =========================================================
def extract_subdomain(request: Request) -> Optional[str]:
    """
    Extracts the subdomain from the incoming Host header.
    Examples:
      - blog.sitendra.store -> 'blog'
      - tools.sitendra.store -> 'tools'
      - projects.sitendra.store -> 'projects'
      - app.sitendra.store  -> 'app'
      - about.sitendra.store -> 'about'
      - sitendra.store      -> None
      - www.sitendra.store  -> None
      - blog.localhost:8000 -> 'blog'
      - localhost:8000      -> None
    """
    host = request.headers.get("host", "").lower().split(":")[0]
    if not host or re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        return None

    parts = host.split(".")
    
    # Localhost development (e.g. blog.localhost)
    if len(parts) == 2 and parts[1] == "localhost":
        return parts[0] if parts[0] != "www" else None
        
    # Production custom domain (e.g. blog.sitendra.store)
    if len(parts) > 2:
        sub = parts[0]
        if sub != "www":
            return sub

    return None


# =========================================================
# Dynamic Host & Subdomain Root Dispatcher
# =========================================================
@app.get("/")
def dynamic_root_dispatcher(request: Request):
    subdomain = extract_subdomain(request)

    # 1. Blog Subdomain (blog.sitendra.store)
    if subdomain == "blog":
        return FileResponse(STATIC_DIR / "blog" / "index.html")

    # 2. Tools & Image Subdomains
    if subdomain in ("image", "img", "images"):
        return FileResponse(STATIC_DIR / "image_tools.html")
    if subdomain == "tools":
        return FileResponse(STATIC_DIR / "tools.html")

    # 3. Projects Subdomain (projects.sitendra.store)
    if subdomain in ("projects", "portfolio"):
        return FileResponse(STATIC_DIR / "projects.html")

    # 4. About / Profile Subdomain (about.sitendra.store / me.sitendra.store)
    if subdomain in ("about", "me", "intro"):
        intro_file = INTRO_DIR / "index.html"
        if intro_file.exists():
            return FileResponse(intro_file)

    # 5. Notes App / Main Root Domain (sitendra.store or app.sitendra.store)
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login.html")
    return RedirectResponse(url="/index.html")


# =========================================================
# Universal Navigation Pages
# =========================================================
@app.get("/about")
def about_page():
    intro_file = INTRO_DIR / "index.html"
    if intro_file.exists():
        return FileResponse(intro_file)
    return RedirectResponse(url="/")


@app.get("/tools")
def tools_page():
    return FileResponse(STATIC_DIR / "tools.html")


@app.get("/image-tools")
@app.get("/image-studio")
@app.get("/tools/image")
def image_tools_page():
    return FileResponse(STATIC_DIR / "image_tools.html")


@app.get("/projects")
def projects_page():
    return FileResponse(STATIC_DIR / "projects.html")


@app.get("/share/{share_id}")
def view_shared_note_page(share_id: str):
    return FileResponse(STATIC_DIR / "share.html")


# =========================================================
# Universal Blog Routes
# =========================================================
@app.get("/blog")
@app.get("/blog/")
def blog_home():
    return FileResponse(STATIC_DIR / "blog" / "index.html")


@app.get("/blog/write")
@app.get("/write")
def blog_write(request: Request):
    if not request.session.get("user_id"):
        sub = extract_subdomain(request)
        next_param = "/write" if sub == "blog" else "/blog/write"
        return RedirectResponse(url=f"/login.html?next={next_param}")
    return FileResponse(STATIC_DIR / "blog" / "write.html")


@app.get("/blog/post/{slug}")
@app.get("/post/{slug}")
def blog_single_post(slug: str):
    return FileResponse(STATIC_DIR / "blog" / "post.html")


# =========================================================
# SEO: Dynamic RSS 2.0 Feed & XML Sitemap & Robots.txt
# =========================================================
@app.get("/feed.xml")
@app.get("/rss.xml")
def rss_feed():
    blogs = get_published_blogs(limit=50)
    base_url = "https://blog.sitendra.store"

    items_xml = []
    for b in blogs:
        title = html.escape(b["title"])
        summary = html.escape(b["summary"] or "")
        post_link = f"{base_url}/post/{b['slug']}"
        date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        if b.get("created_at"):
            try:
                dt = datetime.fromisoformat(str(b["created_at"]).replace("Z", "+00:00"))
                date_str = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            except Exception:
                pass

        items_xml.append(f"""
        <item>
            <title>{title}</title>
            <link>{post_link}</link>
            <guid isPermaLink="true">{post_link}</guid>
            <description>{summary}</description>
            <pubDate>{date_str}</pubDate>
            <author>sitendranagesh@gmail.com (Sitendra Kumar Nagesh)</author>
        </item>""")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Sitendra's Engineering &amp; Systems Blog</title>
        <link>https://blog.sitendra.store</link>
        <description>Technical articles on software architecture, backend systems, and mechanical engineering by Sitendra Kumar Nagesh.</description>
        <language>en-us</language>
        <atom:link href="https://blog.sitendra.store/feed.xml" rel="self" type="application/rss+xml"/>
        {"".join(items_xml)}
    </channel>
</rss>"""

    return Response(content=xml_content.strip(), media_type="application/xml")


@app.get("/sitemap.xml")
def sitemap_xml():
    blogs = get_published_blogs(limit=100)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    urls = [
        {"loc": "https://sitendra.store/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "https://sitendra.store/about", "priority": "0.9", "changefreq": "monthly"},
        {"loc": "https://blog.sitendra.store/", "priority": "0.95", "changefreq": "daily"},
        {"loc": "https://sitendra.store/tools", "priority": "0.85", "changefreq": "weekly"},
        {"loc": "https://sitendra.store/image-tools", "priority": "0.9", "changefreq": "weekly"},
        {"loc": "https://sitendra.store/projects", "priority": "0.85", "changefreq": "monthly"},
    ]

    for b in blogs:
        urls.append({
            "loc": f"https://blog.sitendra.store/post/{b['slug']}",
            "priority": "0.8",
            "changefreq": "weekly"
        })

    urls_xml = []
    for u in urls:
        urls_xml.append(f"""
    <url>
        <loc>{u['loc']}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{u['changefreq']}</changefreq>
        <priority>{u['priority']}</priority>
    </url>""")

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {"".join(urls_xml)}
</urlset>"""

    return Response(content=sitemap_content.strip(), media_type="application/xml")


@app.get("/robots.txt")
def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /write

Sitemap: https://sitendra.store/sitemap.xml
"""
    return PlainTextResponse(content=content)


# =========================================================
# User Auth Endpoints (Universal)
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
# Notes Endpoints & Public Note Sharing
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


@app.post("/api/note/share")
def share_note_endpoint(payload: ShareNotePayload, user_id: int = Depends(require_login)):
    """Generates or toggles a public sharing link for a note."""
    try:
        return toggle_note_sharing(user_id, payload.title, payload.enable)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/note/shared/{share_id}")
def fetch_public_shared_note(share_id: str):
    """Public read-only endpoint for viewing a shared note."""
    note = get_shared_note(share_id)
    if not note:
        raise HTTPException(status_code=404, detail="Shared note not found or link expired.")
    return note


# =========================================================
# Blog REST API & Reactions Endpoints
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


@app.get("/api/blogs/{slug}/reactions")
def get_reactions(slug: str):
    """Public: Get claps/reaction counts for an article."""
    return get_reactions_for_blog(slug)


@app.post("/api/blogs/{slug}/react")
def post_reaction(slug: str, payload: ReactionPayload):
    """Public: Add a clap/reaction to an article."""
    try:
        return add_reaction_to_blog(slug, payload.reaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/newsletter/subscribe")
def subscribe_newsletter(payload: NewsletterPayload):
    """Public: Subscribe email to newsletter dispatch."""
    try:
        return add_newsletter_subscriber(payload.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@app.post("/api/chat/message")
async def api_post_chat_message(request: Request):
    """Receive a quick message from the chat assistant widget."""
    try:
        data = await request.json()
        message = (data.get("message") or "").strip()
        if not message:
            return JSONResponse({"error": "Message cannot be empty"}, status_code=400)
        name = (data.get("name") or "Anonymous Visitor").strip()
        email = (data.get("email") or "").strip()
        save_quick_message(name, email, message)
        return JSONResponse({"status": "success", "message": "Message saved successfully!"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# =========================================================
# Static Files Mount
# =========================================================
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")