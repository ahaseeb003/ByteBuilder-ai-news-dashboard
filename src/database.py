"""
database.py
-----------
SQLite database layer for the ByteBuilder AI & Tech News Dashboard.
Handles all CRUD operations, schema migrations, and duplicate prevention.

Key freshness improvements:
  • published_at_ts  — normalised ISO-8601 UTC timestamp (indexed)
  • recency_score    — pre-computed freshness float (0-1)
  • Default sort is published_at_ts DESC so newest news always comes first
  • get_latest_articles() helper returns only articles from the last N hours

Developed by HMtechie & ByteBuilder
"""

import sqlite3
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from config.settings import DB_PATH

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash        TEXT    UNIQUE NOT NULL,
    title           TEXT    NOT NULL,
    url             TEXT    NOT NULL,
    source          TEXT,
    category        TEXT,
    published_at    TEXT,           -- original raw date string
    published_at_ts TEXT,           -- normalised ISO-8601 UTC (sortable)
    recency_score   REAL    DEFAULT 0.0,
    collected_at    TEXT    NOT NULL,
    summary         TEXT,
    tags            TEXT,           -- JSON array stored as text
    relevance       REAL    DEFAULT 0.0,
    trend_score     REAL    DEFAULT 0.0,
    sentiment       TEXT,
    raw_content     TEXT,
    is_published    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS github_repos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash      TEXT    UNIQUE NOT NULL,
    name          TEXT    NOT NULL,
    url           TEXT    NOT NULL,
    description   TEXT,
    language      TEXT,
    stars         INTEGER DEFAULT 0,
    forks         INTEGER DEFAULT 0,
    today_stars   INTEGER DEFAULT 0,
    topics        TEXT,             -- JSON array
    collected_at  TEXT    NOT NULL,
    summary       TEXT,
    tags          TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT    NOT NULL,
    agent_name      TEXT    NOT NULL,
    status          TEXT    NOT NULL,  -- success | error | warning
    message         TEXT,
    started_at      TEXT    NOT NULL,
    finished_at     TEXT,
    items_processed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           TEXT    UNIQUE NOT NULL,
    started_at       TEXT    NOT NULL,
    finished_at      TEXT,
    status           TEXT    DEFAULT 'running',
    total_collected  INTEGER DEFAULT 0,
    total_filtered   INTEGER DEFAULT 0,
    total_summarized INTEGER DEFAULT 0,
    error_message    TEXT
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_articles_published_ts ON articles(published_at_ts DESC);
CREATE INDEX IF NOT EXISTS idx_articles_recency      ON articles(recency_score DESC);
CREATE INDEX IF NOT EXISTS idx_articles_collected    ON articles(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_relevance    ON articles(relevance DESC);
CREATE INDEX IF NOT EXISTS idx_articles_trend        ON articles(trend_score DESC);
CREATE INDEX IF NOT EXISTS idx_articles_category     ON articles(category);
CREATE INDEX IF NOT EXISTS idx_repos_collected       ON github_repos(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_repos_stars           ON github_repos(today_stars DESC);
CREATE INDEX IF NOT EXISTS idx_logs_run_id           ON pipeline_logs(run_id);
"""

# Migration: add new columns to existing databases without breaking them
MIGRATION_SQL = [
    "ALTER TABLE articles ADD COLUMN published_at_ts TEXT",
    "ALTER TABLE articles ADD COLUMN recency_score REAL DEFAULT 0.0",
]


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Create all tables, indexes, and run any pending migrations."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.executescript(INDEX_SQL)
        # Run migrations — ignore errors for columns that already exist
        for sql in MIGRATION_SQL:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError:
                pass  # column already exists
    logger.info("Database initialised at %s", db_path)


# ─────────────────────────────────────────────────────────────────────────────
# Article CRUD
# ─────────────────────────────────────────────────────────────────────────────

def upsert_article(article: dict) -> bool:
    """
    Insert an article if its URL has not been seen before.
    Returns True if inserted, False if duplicate.

    Stores both the raw published_at string AND the normalised
    published_at_ts ISO UTC string for reliable date-based sorting.
    """
    url_hash  = _hash_url(article["url"])
    now       = datetime.now(timezone.utc).isoformat()
    tags_json = json.dumps(article.get("tags", []))

    # Use the normalised ISO timestamp if available, else fall back to raw
    published_at_ts = (
        article.get("published_at", "")   # already ISO UTC from data_collector
        or now
    )

    sql = """
        INSERT OR IGNORE INTO articles
            (url_hash, title, url, source, category,
             published_at, published_at_ts, recency_score,
             collected_at, summary, tags, relevance, trend_score,
             sentiment, raw_content)
        VALUES
            (?, ?, ?, ?, ?,
             ?, ?, ?,
             ?, ?, ?, ?, ?,
             ?, ?)
    """
    params = (
        url_hash,
        article.get("title", ""),
        article["url"],
        article.get("source", ""),
        article.get("category", ""),
        article.get("published_at", ""),
        published_at_ts,
        float(article.get("recency_score", 0.0)),
        now,
        article.get("summary", ""),
        tags_json,
        float(article.get("relevance", 0.0)),
        float(article.get("trend_score", 0.0)),
        article.get("sentiment", "neutral"),
        article.get("raw_content", ""),
    )
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        inserted = cursor.rowcount > 0
    return inserted


def update_article_summary(url: str, summary: str, tags: list[str]) -> None:
    """Update the LLM-generated summary and tags for an existing article."""
    url_hash  = _hash_url(url)
    tags_json = json.dumps(tags)
    with get_connection() as conn:
        conn.execute(
            "UPDATE articles SET summary=?, tags=? WHERE url_hash=?",
            (summary, tags_json, url_hash),
        )


def get_articles(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    min_relevance: float = 0.0,
    order_by: str = "published_at_ts",   # DEFAULT: newest published first
    hours: Optional[int] = None,          # if set, only return articles from last N hours
) -> list[dict]:
    """
    Fetch articles with optional filtering and pagination.

    Default sort is `published_at_ts DESC` so the dashboard always shows
    the most recently published articles first.
    """
    allowed_order = {
        "published_at_ts", "collected_at", "relevance",
        "trend_score", "recency_score",
    }
    if order_by not in allowed_order:
        order_by = "published_at_ts"

    where_clauses = ["relevance >= ?"]
    params: list = [min_relevance]

    if category:
        where_clauses.append("category = ?")
        params.append(category)

    if hours is not None:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=hours)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        where_clauses.append("published_at_ts >= ?")
        params.append(cutoff)

    where_sql = " AND ".join(where_clauses)
    sql = f"""
        SELECT * FROM articles
        WHERE {where_sql}
        ORDER BY {order_by} DESC
        LIMIT ? OFFSET ?
    """
    params += [limit, offset]

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    results = [dict(r) for r in rows]
    # Deserialise tags JSON
    for r in results:
        try:
            r["tags"] = json.loads(r.get("tags") or "[]")
        except (json.JSONDecodeError, TypeError):
            r["tags"] = []
    return results


def get_latest_articles(limit: int = 50, hours: int = 48) -> list[dict]:
    """
    Convenience wrapper — returns only articles published in the last `hours`
    hours, sorted newest first. Falls back to all articles if none found.
    """
    recent = get_articles(limit=limit, hours=hours, order_by="published_at_ts")
    if recent:
        return recent
    # Fallback: return whatever is in the DB sorted by published_at_ts
    return get_articles(limit=limit, order_by="published_at_ts")


def get_article_count(category: Optional[str] = None) -> int:
    if category:
        sql    = "SELECT COUNT(*) FROM articles WHERE category = ?"
        params = (category,)
    else:
        sql    = "SELECT COUNT(*) FROM articles"
        params = ()
    with get_connection() as conn:
        return conn.execute(sql, params).fetchone()[0]


def get_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM articles WHERE category != '' ORDER BY category"
        ).fetchall()
    return [r[0] for r in rows]


def mark_published(url: str) -> None:
    url_hash = _hash_url(url)
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE articles SET is_published=1 WHERE url_hash=?",
            (url_hash,),
        )


def search_articles(query: str, limit: int = 20) -> list[dict]:
    """Full-text search across title and summary, sorted newest first."""
    like = f"%{query.lower()}%"
    sql = """
        SELECT * FROM articles
        WHERE LOWER(title) LIKE ? OR LOWER(summary) LIKE ?
        ORDER BY published_at_ts DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (like, like, limit)).fetchall()
    results = [dict(r) for r in rows]
    for r in results:
        try:
            r["tags"] = json.loads(r.get("tags") or "[]")
        except (json.JSONDecodeError, TypeError):
            r["tags"] = []
    return results


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Repos CRUD
# ─────────────────────────────────────────────────────────────────────────────

def upsert_repo(repo: dict) -> bool:
    url_hash     = _hash_url(repo["url"])
    now          = datetime.now(timezone.utc).isoformat()
    topics_json  = json.dumps(repo.get("topics", []))
    tags_json    = json.dumps(repo.get("tags", []))

    sql = """
        INSERT INTO github_repos
            (url_hash, name, url, description, language, stars, forks,
             today_stars, topics, collected_at, summary, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url_hash) DO UPDATE SET
            stars        = excluded.stars,
            forks        = excluded.forks,
            today_stars  = excluded.today_stars,
            collected_at = excluded.collected_at,
            summary      = COALESCE(excluded.summary, github_repos.summary),
            tags         = COALESCE(excluded.tags, github_repos.tags)
    """
    params = (
        url_hash,
        repo.get("name", ""),
        repo["url"],
        repo.get("description", ""),
        repo.get("language", ""),
        repo.get("stars", 0),
        repo.get("forks", 0),
        repo.get("today_stars", 0),
        topics_json,
        now,
        repo.get("summary", ""),
        tags_json,
    )
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount > 0


def get_repos(limit: int = 20) -> list[dict]:
    sql = "SELECT * FROM github_repos ORDER BY today_stars DESC LIMIT ?"
    with get_connection() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_repo_count() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM github_repos").fetchone()[0]


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Logging
# ─────────────────────────────────────────────────────────────────────────────

def log_pipeline_event(
    run_id: str,
    agent_name: str,
    status: str,
    message: str = "",
    items_processed: int = 0,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO pipeline_logs
                (run_id, agent_name, status, message, started_at, finished_at, items_processed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, agent_name, status, message,
             started_at or now, finished_at, items_processed),
        )


def upsert_pipeline_run(run_id: str, **kwargs) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM pipeline_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if existing:
            set_clauses = ", ".join(f"{k}=?" for k in kwargs)
            params = list(kwargs.values()) + [run_id]
            conn.execute(
                f"UPDATE pipeline_runs SET {set_clauses} WHERE run_id=?", params
            )
        else:
            conn.execute(
                "INSERT INTO pipeline_runs (run_id, started_at) VALUES (?, ?)",
                (run_id, now),
            )


def get_pipeline_logs(limit: int = 100) -> list[dict]:
    sql = """
        SELECT pl.*, pr.started_at AS run_started
        FROM pipeline_logs pl
        LEFT JOIN pipeline_runs pr ON pl.run_id = pr.run_id
        ORDER BY pl.id DESC
        LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_pipeline_runs(limit: int = 20) -> list[dict]:
    sql = "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?"
    with get_connection() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Export helpers
# ─────────────────────────────────────────────────────────────────────────────

def export_articles_to_list(limit: int = 500) -> list[dict]:
    """Return articles as plain dicts suitable for CSV/JSON export."""
    return get_articles(limit=limit, order_by="published_at_ts")