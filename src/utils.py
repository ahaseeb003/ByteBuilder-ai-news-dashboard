"""
utils.py
--------
Shared utility helpers for the AI Tech News Multi-Agent Aggregator Dashboard.
"""

import re
import json
import hashlib
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from config.settings import AI_KEYWORDS


# ─────────────────────────────────────────────────────────────────────────────
# Text Cleaning
# ─────────────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove HTML tags, excess whitespace, and normalise unicode."""
    if not text:
        return ""
    # Strip HTML
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalise unicode
    text = unicodedata.normalize("NFKC", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate(text: str, max_chars: int = 500) -> str:
    """Truncate text to a maximum character count, appending ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def extract_domain(url: str) -> str:
    """Return the domain name from a URL."""
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# AI Relevance Scoring
# ─────────────────────────────────────────────────────────────────────────────

def compute_relevance_score(title: str, content: str = "") -> float:
    """
    Compute a 0–1 relevance score based on AI keyword density.
    Title matches are weighted more heavily than body matches.
    """
    combined = (title.lower() + " " + content.lower())
    title_lower = title.lower()

    title_hits = sum(1 for kw in AI_KEYWORDS if kw in title_lower)
    body_hits = sum(1 for kw in AI_KEYWORDS if kw in combined)

    # Weighted score: title hit = 0.15, body hit = 0.05, capped at 1.0
    score = min(1.0, title_hits * 0.15 + body_hits * 0.05)
    return round(score, 4)


def is_ai_related(title: str, content: str = "", threshold: float = 0.05) -> bool:
    """Return True if the content meets the minimum AI relevance threshold."""
    return compute_relevance_score(title, content) >= threshold


# ─────────────────────────────────────────────────────────────────────────────
# Deduplication
# ─────────────────────────────────────────────────────────────────────────────

def url_hash(url: str) -> str:
    """Return a 32-character SHA-256 hex digest of a URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def deduplicate(items: list[dict], key: str = "url") -> list[dict]:
    """Remove duplicate dicts by a given key, preserving order."""
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        val = item.get(key, "")
        h = url_hash(val)
        if h not in seen:
            seen.add(h)
            result.append(item)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Date / Time Helpers
# ─────────────────────────────────────────────────────────────────────────────

def now_utc_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Attempt to parse a date string in multiple common formats.
    Returns None if parsing fails.
    """
    if not date_str:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def format_date_display(date_str: Optional[str]) -> str:
    """Return a human-readable date string for display in the dashboard."""
    dt = parse_date(date_str)
    if dt is None:
        return date_str or "Unknown"
    return dt.strftime("%b %d, %Y %H:%M UTC")


# ─────────────────────────────────────────────────────────────────────────────
# Tag / Hashtag Helpers
# ─────────────────────────────────────────────────────────────────────────────

_HASHTAG_MAP: dict[str, str] = {
    "artificial intelligence": "ArtificialIntelligence",
    "machine learning": "MachineLearning",
    "deep learning": "DeepLearning",
    "natural language processing": "NLP",
    "large language model": "LLM",
    "generative ai": "GenerativeAI",
    "computer vision": "ComputerVision",
    "reinforcement learning": "ReinforcementLearning",
    "neural network": "NeuralNetwork",
    "openai": "OpenAI",
    "hugging face": "HuggingFace",
    "langchain": "LangChain",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "diffusion": "DiffusionModel",
    "transformer": "Transformer",
    "chatgpt": "ChatGPT",
    "llama": "LLaMA",
    "mistral": "Mistral",
    "gemini": "Gemini",
    "claude": "Claude",
    "rag": "RAG",
    "mlops": "MLOps",
    "data science": "DataScience",
    "robotics": "Robotics",
    "autonomous": "AutonomousAI",
}


def generate_hashtags(text: str, max_tags: int = 5) -> list[str]:
    """
    Generate relevant hashtags from text by matching against a curated map.
    Returns a list of hashtag strings (without the '#' prefix).
    """
    text_lower = text.lower()
    tags: list[str] = []
    for phrase, tag in _HASHTAG_MAP.items():
        if phrase in text_lower and tag not in tags:
            tags.append(tag)
        if len(tags) >= max_tags:
            break
    # Always include a generic AI tag
    if "AI" not in tags:
        tags.append("AI")
    return tags[:max_tags]


# ─────────────────────────────────────────────────────────────────────────────
# JSON Helpers
# ─────────────────────────────────────────────────────────────────────────────

def safe_json_loads(value: Any, default: Any = None) -> Any:
    """Safely parse a JSON string, returning default on failure."""
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


# ─────────────────────────────────────────────────────────────────────────────
# Sentiment (lightweight keyword-based)
# ─────────────────────────────────────────────────────────────────────────────

_POSITIVE_WORDS = {
    "breakthrough", "innovative", "impressive", "powerful", "efficient",
    "state-of-the-art", "sota", "best", "improved", "new", "launch",
    "release", "advance", "achieve", "success", "gain", "boost",
}
_NEGATIVE_WORDS = {
    "risk", "danger", "concern", "fail", "problem", "issue", "bug",
    "vulnerability", "attack", "threat", "bias", "harmful", "unsafe",
    "controversial", "ban", "restrict", "limit",
}


def simple_sentiment(text: str) -> str:
    """
    Return a simple sentiment label: 'positive', 'negative', or 'neutral'.
    Uses keyword matching — suitable for quick triage without an LLM.
    """
    words = set(text.lower().split())
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"
