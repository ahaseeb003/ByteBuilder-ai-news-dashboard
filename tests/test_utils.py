"""
test_utils.py
-------------
Basic unit tests for the shared utility functions.
Run with: pytest tests/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import (
    clean_text,
    truncate,
    extract_domain,
    compute_relevance_score,
    is_ai_related,
    url_hash,
    deduplicate,
    generate_hashtags,
    simple_sentiment,
)


def test_clean_text_strips_html():
    assert clean_text("<p>Hello <b>world</b></p>") == "Hello world"


def test_clean_text_collapses_whitespace():
    assert clean_text("  too   many   spaces  ") == "too many spaces"


def test_truncate_short_text():
    assert truncate("short", 100) == "short"


def test_truncate_long_text():
    long = "word " * 200
    result = truncate(long, 50)
    assert len(result) <= 53  # 50 + "…"


def test_extract_domain():
    assert extract_domain("https://www.techcrunch.com/article") == "techcrunch.com"
    assert extract_domain("https://openai.com/blog") == "openai.com"


def test_compute_relevance_score_ai_title():
    score = compute_relevance_score("New GPT-4 model released by OpenAI")
    assert score > 0.0


def test_compute_relevance_score_non_ai():
    score = compute_relevance_score("Local football team wins championship")
    assert score == 0.0


def test_is_ai_related():
    assert is_ai_related("LLM fine-tuning techniques for production") is True
    assert is_ai_related("Best pizza recipes for summer") is False


def test_url_hash_deterministic():
    h1 = url_hash("https://example.com/article")
    h2 = url_hash("https://example.com/article")
    assert h1 == h2
    assert len(h1) == 32


def test_deduplicate():
    items = [
        {"url": "https://a.com"},
        {"url": "https://b.com"},
        {"url": "https://a.com"},
    ]
    result = deduplicate(items, key="url")
    assert len(result) == 2


def test_generate_hashtags_returns_list():
    tags = generate_hashtags("New large language model from OpenAI")
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert "AI" in tags


def test_simple_sentiment_positive():
    assert simple_sentiment("breakthrough innovative new AI model") == "positive"


def test_simple_sentiment_negative():
    assert simple_sentiment("risk danger vulnerability attack threat") == "negative"


def test_simple_sentiment_neutral():
    assert simple_sentiment("the model was released yesterday") == "neutral"
