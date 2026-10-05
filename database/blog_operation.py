import re
import math
from database.db import get_connection


def init_blog_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            summary TEXT,
            content TEXT NOT NULL,
            cover_image TEXT,
            tags TEXT,
            is_published INTEGER DEFAULT 1,
            views INTEGER DEFAULT 0,
            reading_time INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blog_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id INTEGER NOT NULL,
            reaction_type TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(blog_id, reaction_type)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


def calculate_reading_time(content: str) -> int:
    """Estimates reading time in minutes (assuming ~200 words/min, minimum 1 min)."""
    words = len(re.findall(r"\w+", content or ""))
    return max(1, math.ceil(words / 200))


def slugify(text: str) -> str:
    """Converts a title into a clean URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "untitled-post"


def generate_unique_slug(title: str, existing_id: int = None) -> str:
    """Generates a unique slug by appending -1, -2 if duplicates exist."""
    base_slug = slugify(title)
    candidate_slug = base_slug
    counter = 1

    conn = get_connection()
    cur = conn.cursor()

    while True:
        if existing_id:
            cur.execute("SELECT id FROM blogs WHERE slug = ? AND id != ?", (candidate_slug, existing_id))
        else:
            cur.execute("SELECT id FROM blogs WHERE slug = ?", (candidate_slug,))
        row = cur.fetchone()

        if not row:
            break

        candidate_slug = f"{base_slug}-{counter}"
        counter += 1

    conn.close()
    return candidate_slug


def create_blog(
    user_id: int,
    title: str,
    summary: str,
    content: str,
    cover_image: str = "",
    tags: str = "",
    is_published: bool = True,
    custom_slug: str = "",
) -> dict:
    title = title.strip()
    if not title:
        raise ValueError("Blog title cannot be empty")
    if not content:
        raise ValueError("Blog content cannot be empty")

    slug = custom_slug.strip() if custom_slug else ""
    if slug:
        slug = generate_unique_slug(slug)
    else:
        slug = generate_unique_slug(title)

    reading_time = calculate_reading_time(content)
    published_val = 1 if is_published else 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO blogs (user_id, title, slug, summary, content, cover_image, tags, is_published, reading_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, slug, summary, content, cover_image, tags, published_val, reading_time),
        )
        blog_id = cur.lastrowid
        conn.commit()
        return {"id": blog_id, "slug": slug, "status": "Blog created successfully"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_blog(
    blog_id: int,
    user_id: int,
    title: str,
    summary: str,
    content: str,
    cover_image: str = "",
    tags: str = "",
    is_published: bool = True,
    custom_slug: str = "",
) -> dict:
    title = title.strip()
    if not title:
        raise ValueError("Blog title cannot be empty")
    if not content:
        raise ValueError("Blog content cannot be empty")

    slug = custom_slug.strip() if custom_slug else ""
    if slug:
        slug = generate_unique_slug(slug, existing_id=blog_id)
    else:
        slug = generate_unique_slug(title, existing_id=blog_id)

    reading_time = calculate_reading_time(content)
    published_val = 1 if is_published else 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE blogs
            SET title = ?, slug = ?, summary = ?, content = ?,
                cover_image = ?, tags = ?, is_published = ?,
                reading_time = ?, updated_at = datetime('now')
            WHERE id = ? AND user_id = ?
            """,
            (title, slug, summary, content, cover_image, tags, published_val, reading_time, blog_id, user_id),
        )
        if cur.rowcount == 0:
            conn.rollback()
            raise ValueError("Blog post not found or you don't have permission to edit it.")

        conn.commit()
        return {"id": blog_id, "slug": slug, "status": "Blog updated successfully"}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_blog(blog_id: int, user_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM blogs WHERE id = ? AND user_id = ?", (blog_id, user_id))
        if cur.rowcount == 0:
            conn.rollback()
            raise ValueError("Blog post not found or you don't have permission to delete it.")
        conn.commit()
        return {"status": "Blog deleted successfully"}
    finally:
        conn.close()


def get_published_blogs(search: str = None, tag: str = None, limit: int = 50, offset: int = 0) -> list:
    """Returns all published blogs, optionally filtered by keyword search or tag, ordered newest first."""
    conn = get_connection()
    cur = conn.cursor()

    query = (
        "SELECT b.id, b.title, b.slug, b.summary, b.cover_image, b.tags, "
        "b.reading_time, b.views, b.created_at, b.updated_at, u.username as author "
        "FROM blogs b JOIN users u ON b.user_id = u.id "
        "WHERE b.is_published = 1"
    )

    params = []

    if search:
        search_like = f"%{search.lower()}%"
        query += " AND (LOWER(b.title) LIKE ? OR LOWER(b.summary) LIKE ? OR LOWER(b.content) LIKE ?)"
        params.extend([search_like, search_like, search_like])

    if tag:
        tag_like = f"%{tag.lower()}%"
        query += " AND LOWER(b.tags) LIKE ?"
        params.append(tag_like)

    query += " ORDER BY b.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_blog_by_slug(slug: str, increment_view: bool = True):
    """Retrieves a single published blog post by slug and optionally increments view count."""
    conn = get_connection()
    cur = conn.cursor()

    if increment_view:
        cur.execute("UPDATE blogs SET views = views + 1 WHERE slug = ?", (slug,))
        conn.commit()

    query = """
        SELECT b.*, u.username as author
        FROM blogs b
        JOIN users u ON b.user_id = u.id
        WHERE b.slug = ?
    """

    cur.execute(query, (slug,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_blog_by_id(blog_id: int, user_id: int = None):
    """Retrieves a blog post by ID (used for editing)."""
    conn = get_connection()
    cur = conn.cursor()

    if user_id is not None:
        cur.execute("SELECT * FROM blogs WHERE id = ? AND user_id = ?", (blog_id, user_id))
    else:
        cur.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,))

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_blogs_for_user(user_id: int) -> list:
    """Returns all blogs for author dashboard (including drafts and published)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, slug, summary, is_published, views, reading_time, tags, created_at, updated_at
        FROM blogs
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_tags() -> list:
    """Scans all published blogs and returns unique tags with counts."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT tags FROM blogs WHERE is_published = 1 AND tags IS NOT NULL AND tags != ''")
    rows = cur.fetchall()
    conn.close()

    tag_counts = {}
    for r in rows:
        tag_str = r["tags"] if hasattr(r, "keys") else r[0]
        if not tag_str:
            continue
        tags = [t.strip().lower() for t in tag_str.split(",") if t.strip()]
        for t in tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    sorted_tags = sorted([{"tag": k, "count": v} for k, v in tag_counts.items()], key=lambda x: x["count"], reverse=True)
    return sorted_tags


# =========================================================
# Reactions / Claps Engine
# =========================================================
VALID_REACTIONS = {"clap", "idea", "heart", "rocket"}


def get_reactions_for_blog(slug: str) -> dict:
    """Returns counts for all reaction types for a given blog post."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM blogs WHERE slug = ?", (slug,))
    blog_row = cur.fetchone()
    if not blog_row:
        conn.close()
        return {r: 0 for r in VALID_REACTIONS}

    blog_id = blog_row["id"] if hasattr(blog_row, "keys") else blog_row[0]
    cur.execute("SELECT reaction_type, count FROM blog_reactions WHERE blog_id = ?", (blog_id,))
    rows = cur.fetchall()
    conn.close()

    counts = {r: 0 for r in VALID_REACTIONS}
    for row in rows:
        r_type = row["reaction_type"] if hasattr(row, "keys") else row[0]
        r_count = row["count"] if hasattr(row, "keys") else row[1]
        if r_type in counts:
            counts[r_type] = r_count
    return counts


def add_reaction_to_blog(slug: str, reaction_type: str) -> dict:
    """Increments a reaction count (clap, idea, heart, rocket)."""
    reaction_type = reaction_type.lower().strip()
    if reaction_type not in VALID_REACTIONS:
        raise ValueError(f"Invalid reaction type. Must be one of: {', '.join(VALID_REACTIONS)}")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM blogs WHERE slug = ?", (slug,))
        blog_row = cur.fetchone()
        if not blog_row:
            raise ValueError("Blog post not found")

        blog_id = blog_row["id"] if hasattr(blog_row, "keys") else blog_row[0]

        cur.execute(
            """
            INSERT INTO blog_reactions (blog_id, reaction_type, count)
            VALUES (?, ?, 1)
            ON CONFLICT(blog_id, reaction_type)
            DO UPDATE SET count = count + 1
            """,
            (blog_id, reaction_type),
        )

        conn.commit()
    finally:
        conn.close()

    return get_reactions_for_blog(slug)


# =========================================================
# Newsletter Subscription Engine
# =========================================================
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def add_newsletter_subscriber(email: str) -> dict:
    """Adds a subscriber email address."""
    email = email.lower().strip()
    if not EMAIL_REGEX.match(email):
        raise ValueError("Please provide a valid email address.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT OR IGNORE INTO newsletter_subscribers (email) VALUES (?)",
            (email,),
        )
        conn.commit()
        return {"status": "Subscribed successfully", "email": email}
    finally:
        conn.close()


init_blog_db()
