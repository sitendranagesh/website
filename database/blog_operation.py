import re
import math
from datetime import datetime
from database.db import get_connection, is_postgres, placeholder


def init_blog_db():
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blogs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                summary TEXT,
                content TEXT NOT NULL,
                cover_image TEXT,
                tags TEXT,
                is_published BOOLEAN DEFAULT TRUE,
                views INTEGER DEFAULT 0,
                reading_time INTEGER DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blog_reactions (
                id SERIAL PRIMARY KEY,
                blog_id INTEGER NOT NULL,
                reaction_type TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                CONSTRAINT unique_blog_reaction UNIQUE (blog_id, reaction_type)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
    else:
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

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    while True:
        if existing_id:
            query = f"SELECT id FROM blogs WHERE slug = {p} AND id != {p}"
            cur.execute(query, (candidate_slug, existing_id))
        else:
            query = f"SELECT id FROM blogs WHERE slug = {p}"
            cur.execute(query, (candidate_slug,))
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
    published_val = True if is_postgres() else (1 if is_published else 0)
    if is_postgres():
        published_val = bool(is_published)

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    try:
        if is_postgres():
            cur.execute(
                f"""
                INSERT INTO blogs (user_id, title, slug, summary, content, cover_image, tags, is_published, reading_time)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                RETURNING id, slug
                """,
                (user_id, title, slug, summary, content, cover_image, tags, published_val, reading_time),
            )
            row = cur.fetchone()
            blog_id = row["id"] if hasattr(row, "keys") else row[0]
        else:
            cur.execute(
                f"""
                INSERT INTO blogs (user_id, title, slug, summary, content, cover_image, tags, is_published, reading_time)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
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
    published_val = bool(is_published) if is_postgres() else (1 if is_published else 0)

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    try:
        now_val = "CURRENT_TIMESTAMP" if is_postgres() else "datetime('now')"
        cur.execute(
            f"""
            UPDATE blogs
            SET title = {p}, slug = {p}, summary = {p}, content = {p},
                cover_image = {p}, tags = {p}, is_published = {p},
                reading_time = {p}, updated_at = {now_val}
            WHERE id = {p} AND user_id = {p}
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
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"DELETE FROM blogs WHERE id = {p} AND user_id = {p}", (blog_id, user_id))
        if cur.rowcount == 0:
            conn.rollback()
            raise ValueError("Blog post not found or you don't have permission to delete it.")
        conn.commit()
        return {"status": "Blog deleted successfully"}
    finally:
        conn.close()


def get_published_blogs(search: str = None, tag: str = None, limit: int = 50, offset: int = 0) -> list:
    """Returns all published blogs, optionally filtered by keyword search or tag, ordered newest first."""
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT b.id, b.title, b.slug, b.summary, b.cover_image, b.tags, b.reading_time, b.views, b.created_at, b.updated_at, u.username as author FROM blogs b JOIN users u ON b.user_id = u.id WHERE "
    if is_postgres():
        query += "b.is_published = TRUE"
    else:
        query += "b.is_published = 1"

    params = []

    if search:
        search_like = f"%{search.lower()}%"
        query += f" AND (LOWER(b.title) LIKE {p} OR LOWER(b.summary) LIKE {p} OR LOWER(b.content) LIKE {p})"
        params.extend([search_like, search_like, search_like])

    if tag:
        tag_like = f"%{tag.lower()}%"
        query += f" AND LOWER(b.tags) LIKE {p}"
        params.append(tag_like)

    query += f" ORDER BY b.created_at DESC LIMIT {p} OFFSET {p}"
    params.extend([limit, offset])

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_blog_by_slug(slug: str, increment_view: bool = True):
    """Retrieves a single published blog post by slug and optionally increments view count."""
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    if increment_view:
        cur.execute(f"UPDATE blogs SET views = views + 1 WHERE slug = {p}", (slug,))
        conn.commit()

    query = f"""
        SELECT b.*, u.username as author
        FROM blogs b
        JOIN users u ON b.user_id = u.id
        WHERE b.slug = {p}
    """

    cur.execute(query, (slug,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_blog_by_id(blog_id: int, user_id: int = None):
    """Retrieves a blog post by ID (used for editing)."""
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    if user_id is not None:
        query = f"SELECT * FROM blogs WHERE id = {p} AND user_id = {p}"
        cur.execute(query, (blog_id, user_id))
    else:
        query = f"SELECT * FROM blogs WHERE id = {p}"
        cur.execute(query, (blog_id,))

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_blogs_for_user(user_id: int) -> list:
    """Returns all blogs for author dashboard (including drafts and published)."""
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT id, title, slug, summary, is_published, views, reading_time, tags, created_at, updated_at
        FROM blogs
        WHERE user_id = {p}
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

    is_pub_cond = "is_published = TRUE" if is_postgres() else "is_published = 1"
    cur.execute(f"SELECT tags FROM blogs WHERE {is_pub_cond} AND tags IS NOT NULL AND tags != ''")
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
    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"SELECT id FROM blogs WHERE slug = {p}", (slug,))
    blog_row = cur.fetchone()
    if not blog_row:
        conn.close()
        return {r: 0 for r in VALID_REACTIONS}

    blog_id = blog_row["id"] if hasattr(blog_row, "keys") else blog_row[0]
    cur.execute(f"SELECT reaction_type, count FROM blog_reactions WHERE blog_id = {p}", (blog_id,))
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

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT id FROM blogs WHERE slug = {p}", (slug,))
        blog_row = cur.fetchone()
        if not blog_row:
            raise ValueError("Blog post not found")

        blog_id = blog_row["id"] if hasattr(blog_row, "keys") else blog_row[0]

        if is_postgres():
            cur.execute(
                f"""
                INSERT INTO blog_reactions (blog_id, reaction_type, count)
                VALUES ({p}, {p}, 1)
                ON CONFLICT (blog_id, reaction_type)
                DO UPDATE SET count = blog_reactions.count + 1
                """,
                (blog_id, reaction_type),
            )
        else:
            cur.execute(
                f"""
                INSERT INTO blog_reactions (blog_id, reaction_type, count)
                VALUES ({p}, {p}, 1)
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

    p = placeholder()
    conn = get_connection()
    cur = conn.cursor()

    try:
        if is_postgres():
            cur.execute(
                f"INSERT INTO newsletter_subscribers (email) VALUES ({p}) ON CONFLICT (email) DO NOTHING",
                (email,),
            )
        else:
            cur.execute(
                f"INSERT OR IGNORE INTO newsletter_subscribers (email) VALUES ({p})",
                (email,),
            )
        conn.commit()
        return {"status": "Subscribed successfully", "email": email}
    finally:
        conn.close()


init_blog_db()
