"""
research_paper_agent.py
-----------------------
Agent 3b – Research Paper Collector

Responsibilities:
  • Fetch latest AI/ML research papers from arXiv API
  • Fetch trending papers from Papers With Code API
  • Normalise all papers into a unified dict schema
  • Return papers ready for the LLM Summarizer
"""

import time
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from config.settings import (
    ARXIV_CATEGORIES,
    ARXIV_MAX_RESULTS,
    PAPERS_WITH_CODE_URL,
)
from src.logger import get_logger
from src.utils import clean_text, truncate, deduplicate

logger = get_logger("research_paper_agent")

_HEADERS = {
    "User-Agent": "AINewsAggregator/2.0 (research-fetcher; contact@example.com)"
}
_TIMEOUT = 20


# ─────────────────────────────────────────────────────────────────────────────
# arXiv API
# ─────────────────────────────────────────────────────────────────────────────

_ARXIV_API = "https://export.arxiv.org/api/query"
_ARXIV_NS = "http://www.w3.org/2005/Atom"
_ARXIV_EXT_NS = "http://arxiv.org/schemas/atom"


def fetch_arxiv_papers(category: str, max_results: int = 10) -> list[dict]:
    """
    Fetch the latest papers from arXiv for a given category.
    Returns a list of normalised paper dicts.
    """
    params = {
        "search_query": f"cat:{category}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    papers: list[dict] = []
    try:
        resp = requests.get(_ARXIV_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        for entry in root.findall(f"{{{_ARXIV_NS}}}entry"):
            try:
                paper = _parse_arxiv_entry(entry, category)
                if paper:
                    papers.append(paper)
            except Exception as inner:
                logger.debug("Skipping arXiv entry: %s", inner)

    except Exception as exc:
        logger.warning("arXiv fetch failed for %s: %s", category, exc)

    logger.debug("arXiv [%s]: fetched %d papers", category, len(papers))
    return papers


def _parse_arxiv_entry(entry: ET.Element, category: str) -> dict | None:
    """Parse a single arXiv Atom entry into a normalised paper dict."""
    ns = _ARXIV_NS

    title_el = entry.find(f"{{{ns}}}title")
    title = clean_text(title_el.text) if title_el is not None else ""
    if not title:
        return None

    # arXiv ID and URL
    id_el = entry.find(f"{{{ns}}}id")
    arxiv_url = id_el.text.strip() if id_el is not None else ""
    arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else ""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else arxiv_url

    # Abstract
    summary_el = entry.find(f"{{{ns}}}summary")
    abstract = clean_text(summary_el.text) if summary_el is not None else ""

    # Authors
    author_els = entry.findall(f"{{{ns}}}author")
    authors = ", ".join(
        a.find(f"{{{ns}}}name").text.strip()
        for a in author_els
        if a.find(f"{{{ns}}}name") is not None
    )[:200]

    # Published date
    published_el = entry.find(f"{{{ns}}}published")
    published_at = published_el.text.strip() if published_el is not None else ""

    return {
        "title": title,
        "url": arxiv_url,
        "pdf_url": pdf_url,
        "source": "arxiv.org",
        "category": "Research",
        "published_at": published_at,
        "abstract": truncate(abstract, 800),
        "raw_content": truncate(abstract, 800),
        "authors": authors,
        "arxiv_id": arxiv_id,
        "tags": [],
        "summary": "",
        "relevance": 0.7,
        "trend_score": 0.5,
        "sentiment": "neutral",
        "item_type": "research_paper",
    }


def fetch_all_arxiv_papers() -> list[dict]:
    """Fetch papers from all configured arXiv categories."""
    all_papers: list[dict] = []
    for cat in ARXIV_CATEGORIES:
        papers = fetch_arxiv_papers(cat, max_results=max(3, ARXIV_MAX_RESULTS // len(ARXIV_CATEGORIES)))
        all_papers.extend(papers)
        time.sleep(1.0)  # arXiv rate limit: be polite
    logger.info("arXiv total: %d papers from %d categories", len(all_papers), len(ARXIV_CATEGORIES))
    return all_papers


# ─────────────────────────────────────────────────────────────────────────────
# Papers With Code API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_papers_with_code() -> list[dict]:
    """
    Fetch trending papers from the Papers With Code API.
    Returns a list of normalised paper dicts.
    """
    papers: list[dict] = []
    try:
        resp = requests.get(PAPERS_WITH_CODE_URL, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("results", []):
            try:
                paper = _parse_pwc_item(item)
                if paper:
                    papers.append(paper)
            except Exception as inner:
                logger.debug("Skipping PWC item: %s", inner)

    except Exception as exc:
        logger.warning("Papers With Code fetch failed: %s", exc)

    logger.info("Papers With Code: fetched %d papers", len(papers))
    return papers


def _parse_pwc_item(item: dict) -> dict | None:
    """Parse a Papers With Code API item into a normalised paper dict."""
    title = clean_text(item.get("title", ""))
    if not title:
        return None

    url = item.get("url_abs", "") or item.get("url_pdf", "") or ""
    if not url.startswith("http"):
        url = f"https://arxiv.org/abs/{item.get('arxiv_id', '')}"

    abstract = clean_text(item.get("abstract", ""))
    authors = ", ".join(item.get("authors", []))[:200]
    published_at = item.get("published", "")

    return {
        "title": title,
        "url": url,
        "pdf_url": item.get("url_pdf", url),
        "source": "paperswithcode.com",
        "category": "Research",
        "published_at": published_at,
        "abstract": truncate(abstract, 800),
        "raw_content": truncate(abstract, 800),
        "authors": authors,
        "arxiv_id": item.get("arxiv_id", ""),
        "github_url": item.get("repository", {}).get("url", "") if item.get("repository") else "",
        "tags": [],
        "summary": "",
        "relevance": 0.75,
        "trend_score": 0.6,
        "sentiment": "neutral",
        "item_type": "research_paper",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Database: Research Papers Table
# ─────────────────────────────────────────────────────────────────────────────

def init_papers_table() -> None:
    """Create the research_papers table if it does not exist."""
    from src.database import get_connection
    sql = """
    CREATE TABLE IF NOT EXISTS research_papers (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        url_hash     TEXT    UNIQUE NOT NULL,
        title        TEXT    NOT NULL,
        url          TEXT    NOT NULL,
        pdf_url      TEXT,
        source       TEXT,
        authors      TEXT,
        published_at TEXT,
        collected_at TEXT    NOT NULL,
        abstract     TEXT,
        summary      TEXT,
        tags         TEXT,
        arxiv_id     TEXT,
        github_url   TEXT,
        relevance    REAL    DEFAULT 0.7,
        trend_score  REAL    DEFAULT 0.5
    );
    CREATE INDEX IF NOT EXISTS idx_papers_collected ON research_papers(collected_at DESC);
    """
    with get_connection() as conn:
        conn.executescript(sql)
    logger.debug("research_papers table ready")


def upsert_paper(paper: dict) -> bool:
    """Insert a research paper if not already stored. Returns True if inserted."""
    import hashlib, json
    from src.database import get_connection

    url_hash = hashlib.sha256(paper["url"].encode()).hexdigest()[:32]
    now = datetime.utcnow().isoformat()
    tags_json = json.dumps(paper.get("tags", []))

    sql = """
        INSERT OR IGNORE INTO research_papers
            (url_hash, title, url, pdf_url, source, authors, published_at,
             collected_at, abstract, summary, tags, arxiv_id, github_url,
             relevance, trend_score)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    params = (
        url_hash,
        paper.get("title", ""),
        paper["url"],
        paper.get("pdf_url", ""),
        paper.get("source", ""),
        paper.get("authors", ""),
        paper.get("published_at", ""),
        now,
        paper.get("abstract", ""),
        paper.get("summary", ""),
        tags_json,
        paper.get("arxiv_id", ""),
        paper.get("github_url", ""),
        paper.get("relevance", 0.7),
        paper.get("trend_score", 0.5),
    )
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount > 0


def get_papers(limit: int = 30, offset: int = 0) -> list[dict]:
    """Fetch stored research papers sorted by collection date."""
    import json
    from src.database import get_connection
    sql = "SELECT * FROM research_papers ORDER BY collected_at DESC LIMIT ? OFFSET ?"
    with get_connection() as conn:
        rows = conn.execute(sql, (limit, offset)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["tags"] = json.loads(d.get("tags") or "[]")
        except Exception:
            d["tags"] = []
        result.append(d)
    return result


def search_papers(query: str, limit: int = 20) -> list[dict]:
    """Search research papers by title or abstract."""
    import json
    from src.database import get_connection
    like = f"%{query.lower()}%"
    sql = """
        SELECT * FROM research_papers
        WHERE LOWER(title) LIKE ? OR LOWER(abstract) LIKE ?
        ORDER BY collected_at DESC LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (like, like, limit)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["tags"] = json.loads(d.get("tags") or "[]")
        except Exception:
            d["tags"] = []
        result.append(d)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Agent Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def run_research_paper_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node function for the Research Paper Agent.

    Reads:  state (no upstream dependency)
    Writes: state["research_papers"]
    """
    logger.info("[ResearchPaperAgent] Fetching research papers …")
    start = datetime.utcnow()

    init_papers_table()

    all_papers: list[dict] = []
    all_papers.extend(fetch_all_arxiv_papers())
    all_papers.extend(fetch_papers_with_code())

    # Deduplicate
    unique = deduplicate(all_papers, key="url")
    unique.sort(key=lambda p: p.get("published_at", ""), reverse=True)

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(
        "[ResearchPaperAgent] Fetched %d unique papers in %.1fs",
        len(unique), elapsed,
    )

    return {
        **state,
        "research_papers": unique,
        "paper_agent_elapsed": elapsed,
    }


def store_papers(papers: list[dict]) -> int:
    """Persist research papers to the database. Returns count inserted."""
    inserted = 0
    for paper in papers:
        try:
            if upsert_paper(paper):
                inserted += 1
        except Exception as exc:
            logger.warning("Failed to store paper '%s': %s", paper.get("title", "")[:60], exc)
    logger.info("Stored %d new research papers", inserted)
    return inserted
