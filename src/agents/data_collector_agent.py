"""
data_collector_agent.py
-----------------------
Agent 1 – Data Collector

Responsibilities:
  • Fetch RSS feeds from global tech news, AI blogs, and research sources
  • Parse and NORMALISE published dates to ISO-8601 UTC strings
  • Compute a recency_score (0-1) so the filter agent can rank by freshness
  • Scrape GitHub Trending for AI-related repositories
  • Return a unified list of raw article/repo dicts for downstream agents

Developed by HMtechie & ByteBuilder
"""

import time
import re
import email.utils
import calendar
from typing import Any
from datetime import datetime, timezone, timedelta

import requests
import feedparser
from bs4 import BeautifulSoup

from config.settings import (
    RSS_FEEDS, FEED_CATEGORIES,
    GITHUB_TRENDING_URL, GITHUB_TRENDING_AI_TOPICS,
)
from src.logger import get_logger
from src.utils import clean_text, truncate, extract_domain, now_utc_iso

logger = get_logger("data_collector_agent")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ByteBuilderNewsBot/3.0; "
        "+https://github.com/bytebuilder/ai-news-dashboard)"
    )
}
_REQUEST_TIMEOUT = 12   # per-feed hard timeout (seconds)
_FEED_SLEEP      = 0.15  # polite delay between feeds
_MAX_AGE_DAYS    = 7     # articles older than this get recency_score = 0


# ─────────────────────────────────────────────────────────────────────────────
# Date Parsing Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _parse_date(raw: str) -> datetime | None:
    """
    Try multiple strategies to parse a date string into an aware UTC datetime.
    Returns None if all strategies fail.
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()

    # Strategy 1: feedparser struct_time (passed as string via entry attributes)
    # feedparser stores parsed_time as a 9-tuple; handle if caller passes struct
    # (not applicable here — we always pass strings)

    # Strategy 2: RFC 2822 (most RSS feeds: "Mon, 24 Feb 2025 10:30:00 +0000")
    try:
        parsed_tuple = email.utils.parsedate_to_datetime(raw)
        return parsed_tuple.astimezone(timezone.utc)
    except Exception:
        pass

    # Strategy 3: ISO 8601 variants
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    # Strategy 4: strip timezone suffix and retry
    cleaned = re.sub(r"\s*(GMT|UTC|EST|PST|[+-]\d{2}:?\d{2})$", "", raw).strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S", "%d %b %Y %H:%M:%S", "%d %b %Y"):
        try:
            dt = datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return None


def _recency_score(published_dt: datetime | None) -> float:
    """
    Return a freshness score between 0.0 and 1.0.
      1.0  = published within the last hour
      0.8  = within 6 hours
      0.6  = within 24 hours
      0.4  = within 48 hours
      0.2  = within 7 days
      0.0  = older than 7 days or unknown date
    """
    if published_dt is None:
        return 0.1   # unknown date — give a tiny score so it's not discarded

    now = datetime.now(timezone.utc)
    age = now - published_dt

    if age < timedelta(hours=1):
        return 1.0
    if age < timedelta(hours=6):
        return 0.8
    if age < timedelta(hours=24):
        return 0.6
    if age < timedelta(hours=48):
        return 0.4
    if age < timedelta(days=_MAX_AGE_DAYS):
        return 0.2
    return 0.0


def _to_iso(dt: datetime | None) -> str:
    """Convert an aware datetime to a compact ISO-8601 UTC string."""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────────────────────────────────────────────────────────────────────────
# RSS Feed Ingestion
# ─────────────────────────────────────────────────────────────────────────────

def fetch_rss_feed(feed_url: str) -> list[dict]:
    """
    Parse a single RSS/Atom feed and return normalised article dicts.
    Each article includes a normalised `published_at` ISO string and
    a `recency_score` (0-1) so downstream agents can sort by freshness.
    """
    articles: list[dict] = []
    try:
        response = requests.get(
            feed_url,
            headers=_HEADERS,
            timeout=_REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        source = extract_domain(feed_url)

        for entry in parsed.entries:
            title = clean_text(getattr(entry, "title", ""))
            url   = getattr(entry, "link", "")
            if not url or not title:
                continue

            # ── Extract raw date string from all possible feedparser fields ──
            raw_date = ""
            if hasattr(entry, "published") and entry.published:
                raw_date = entry.published
            elif hasattr(entry, "updated") and entry.updated:
                raw_date = entry.updated
            elif hasattr(entry, "created") and entry.created:
                raw_date = entry.created

            # ── Also try feedparser's pre-parsed struct_time ──────────────────
            published_dt: datetime | None = None
            for attr in ("published_parsed", "updated_parsed", "created_parsed"):
                struct = getattr(entry, attr, None)
                if struct:
                    try:
                        ts = calendar.timegm(struct)
                        published_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                        break
                    except Exception:
                        pass

            # ── Fall back to string parsing if struct_time unavailable ────────
            if published_dt is None and raw_date:
                published_dt = _parse_date(raw_date)

            recency = _recency_score(published_dt)
            published_iso = _to_iso(published_dt)

            # ── Extract summary / description ─────────────────────────────────
            raw_summary = (
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
                or ""
            )
            summary = truncate(clean_text(raw_summary), 600)

            category = _infer_category(feed_url, title)

            articles.append(
                {
                    "title":        title,
                    "url":          url,
                    "source":       source,
                    "category":     category,
                    "published_at": published_iso,   # normalised ISO UTC
                    "raw_date":     raw_date,        # original string for debug
                    "recency_score": recency,
                    "raw_content":  summary,
                    "summary":      "",
                    "tags":         [],
                    "relevance":    0.0,
                    "trend_score":  0.0,
                    "sentiment":    "neutral",
                    "item_type":    "article",
                }
            )

    except requests.exceptions.Timeout:
        logger.warning("RSS feed timed out (>%ds): %s", _REQUEST_TIMEOUT, feed_url)
    except requests.exceptions.ConnectionError as exc:
        logger.warning("RSS feed connection error %s: %s", feed_url, exc)
    except requests.exceptions.HTTPError as exc:
        logger.warning("RSS feed HTTP error %s: %s", feed_url, exc)
    except Exception as exc:
        logger.warning("Failed to fetch RSS feed %s: %s", feed_url, exc)

    logger.debug("Fetched %d articles from %s", len(articles), feed_url)
    return articles


def fetch_all_rss_feeds() -> list[dict]:
    """
    Fetch all configured RSS feeds sequentially.
    Skips feeds that time out or return errors without blocking the pipeline.
    Returns articles sorted newest-first by recency_score.
    """
    all_articles: list[dict] = []
    total = len(RSS_FEEDS)
    for idx, feed_url in enumerate(RSS_FEEDS, 1):
        logger.debug("Fetching feed %d/%d: %s", idx, total, feed_url)
        articles = fetch_rss_feed(feed_url)
        all_articles.extend(articles)
        time.sleep(_FEED_SLEEP)

    # Sort by recency_score descending so newest articles come first
    all_articles.sort(key=lambda a: a.get("recency_score", 0), reverse=True)

    logger.info(
        "Total articles from %d RSS feeds: %d  (newest first)",
        total, len(all_articles),
    )
    return all_articles


# ─────────────────────────────────────────────────────────────────────────────
# Category Inference
# ─────────────────────────────────────────────────────────────────────────────

def _infer_category(feed_url: str, title: str) -> str:
    """
    Assign a category based on the feed URL using the FEED_CATEGORIES map
    from settings. Falls back to keyword matching on the URL and title.
    """
    # Primary: exact match in the category map
    for category, urls in FEED_CATEGORIES.items():
        if feed_url in urls:
            return category

    url_lower   = feed_url.lower()
    title_lower = title.lower()

    if any(k in url_lower for k in ("arxiv", "research", "nature", "science", "ieee", "phys")):
        return "Research & Science"
    if any(k in url_lower for k in ("github", "hackaday", "stackoverflow", "infoq")):
        return "Developer & Engineering"
    if any(k in url_lower for k in ("krebs", "bleeping", "darkreading", "hacker", "sophos",
                                     "schneier", "threatpost", "securityweek")):
        return "Cybersecurity"
    if any(k in url_lower for k in ("startup", "producthunt", "thenextweb",
                                     "techinasia", "eu-startups")):
        return "Startups & Business"
    if any(k in url_lower for k in ("openai", "deepmind", "anthropic", "mistral",
                                     "huggingface", "stability", "nvidia")):
        return "AI Labs & Research"
    if any(k in url_lower for k in ("azure", "cloud.google", "kubernetes", "docker",
                                     "hashicorp", "thenewstack")):
        return "Cloud & Enterprise"
    if any(k in url_lower for k in ("android", "macrumors", "9to5", "gsmarena",
                                     "phonearena", "xda")):
        return "Mobile & Gadgets"
    if any(k in url_lower for k in ("linux", "foss", "ubuntu", "phoronix",
                                     "opensource", "slashdot", "reddit")):
        return "Open Source & Linux"
    if any(k in url_lower for k in ("towardsdatascience", "machinelearning",
                                     "lilianweng", "deeplearning.ai")):
        return "AI / ML Blogs"
    if any(k in url_lower for k in ("techcrunch", "theverge", "wired", "arstechnica",
                                     "zdnet", "venturebeat", "technologyreview", "cnet",
                                     "engadget", "digitaltrends", "theregister",
                                     "techradar", "pcmag", "siliconangle", "bgr")):
        return "Major Tech News"

    # Title-based fallback
    if any(k in title_lower for k in ("paper", "arxiv", "research", "study", "survey")):
        return "Research & Science"
    if any(k in title_lower for k in ("hack", "breach", "vulnerability", "ransomware", "malware")):
        return "Cybersecurity"
    if any(k in title_lower for k in ("startup", "funding", "raises", "series", "ipo")):
        return "Startups & Business"
    if any(k in title_lower for k in ("iphone", "android", "samsung", "pixel", "smartphone")):
        return "Mobile & Gadgets"
    return "Tech News"


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Trending Scraper
# ─────────────────────────────────────────────────────────────────────────────

def fetch_github_trending() -> list[dict]:
    """
    Scrape GitHub Trending page and return a list of repository dicts.
    """
    repos: list[dict] = []
    try:
        resp = requests.get(
            GITHUB_TRENDING_URL, headers=_HEADERS, timeout=_REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for el in soup.select("article.Box-row"):
            try:
                h2 = el.select_one("h2.h3 a")
                if not h2:
                    continue
                repo_path = h2.get("href", "").strip("/")
                name = repo_path.replace("/", " / ")
                url  = f"https://github.com/{repo_path}"

                desc_el  = el.select_one("p.col-9")
                lang_el  = el.select_one("[itemprop='programmingLanguage']")
                stars_el = el.select_one("a[href$='/stargazers']")
                forks_el = el.select_one("a[href$='/forks']")
                today_el = el.select_one("span.d-inline-block.float-sm-right")

                repos.append({
                    "name":        name,
                    "url":         url,
                    "description": clean_text(desc_el.get_text()) if desc_el else "",
                    "language":    lang_el.get_text(strip=True) if lang_el else "",
                    "stars":       _parse_number(stars_el.get_text(strip=True)) if stars_el else 0,
                    "forks":       _parse_number(forks_el.get_text(strip=True)) if forks_el else 0,
                    "today_stars": _parse_number(today_el.get_text(strip=True)) if today_el else 0,
                    "topics":      [],
                    "summary":     "",
                    "tags":        [],
                    "item_type":   "github_repo",
                    "collected_at": now_utc_iso(),
                })
            except Exception as inner_exc:
                logger.debug("Skipping repo element: %s", inner_exc)

    except Exception as exc:
        logger.error("Failed to scrape GitHub Trending: %s", exc)

    logger.info("Fetched %d GitHub trending repos", len(repos))
    return repos


def _parse_number(text: str) -> int:
    text = text.strip().lower().replace(",", "")
    try:
        if "k" in text:
            return int(float(text.replace("k", "")) * 1000)
        return int(float(text.split()[0]))
    except (ValueError, IndexError):
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# AI Tools Discovery
# ─────────────────────────────────────────────────────────────────────────────

_AI_TOOLS_FEEDS: list[str] = [
    "https://www.producthunt.com/feed?category=artificial-intelligence",
    "https://theresanaiforthat.com/feed/",
]


def fetch_ai_tools() -> list[dict]:
    """Fetch newly released AI tools from curated RSS sources."""
    tools: list[dict] = []
    for feed_url in _AI_TOOLS_FEEDS:
        try:
            response = requests.get(
                feed_url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            for entry in parsed.entries:
                title = clean_text(getattr(entry, "title", ""))
                url   = getattr(entry, "link", "")
                if not title or not url:
                    continue

                # Parse date
                published_dt = None
                for attr in ("published_parsed", "updated_parsed"):
                    struct = getattr(entry, attr, None)
                    if struct:
                        try:
                            ts = calendar.timegm(struct)
                            published_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                            break
                        except Exception:
                            pass
                if published_dt is None:
                    raw_date = getattr(entry, "published", "") or getattr(entry, "updated", "")
                    published_dt = _parse_date(raw_date)

                raw = clean_text(
                    getattr(entry, "summary", "") or getattr(entry, "description", "")
                )
                tools.append({
                    "title":         title,
                    "url":           url,
                    "source":        extract_domain(feed_url),
                    "category":      "AI Tools",
                    "published_at":  _to_iso(published_dt),
                    "recency_score": _recency_score(published_dt),
                    "raw_content":   truncate(raw, 600),
                    "summary":       "",
                    "tags":          [],
                    "relevance":     0.5,
                    "trend_score":   0.0,
                    "sentiment":     "neutral",
                    "item_type":     "ai_tool",
                })
        except Exception as exc:
            logger.warning("AI tools feed %s failed: %s", feed_url, exc)
        time.sleep(0.3)

    logger.info("Fetched %d AI tool entries", len(tools))
    return tools


# ─────────────────────────────────────────────────────────────────────────────
# Agent Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def run_data_collector(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node function for the Data Collector Agent.

    Reads:  state["run_id"]
    Writes: state["raw_articles"], state["raw_repos"]
    """
    logger.info("[DataCollector] Starting data collection …")
    start = datetime.now(timezone.utc)

    raw_articles: list[dict] = []
    raw_repos:    list[dict] = []

    # 1. RSS feeds (already sorted newest-first inside fetch_all_rss_feeds)
    raw_articles.extend(fetch_all_rss_feeds())

    # 2. AI tools
    raw_articles.extend(fetch_ai_tools())

    # 3. GitHub trending
    raw_repos.extend(fetch_github_trending())

    # Final sort: newest articles first across all sources
    raw_articles.sort(key=lambda a: a.get("recency_score", 0), reverse=True)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(
        "[DataCollector] Collected %d articles and %d repos in %.1fs",
        len(raw_articles), len(raw_repos), elapsed,
    )

    return {
        **state,
        "raw_articles":      raw_articles,
        "raw_repos":         raw_repos,
        "collector_elapsed": elapsed,
    }