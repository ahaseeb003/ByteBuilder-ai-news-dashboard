"""
test_database.py
----------------
Unit tests for the database module using an in-memory SQLite database.
Run with: pytest tests/
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch

# Patch DB_PATH to use an in-memory database for testing
import src.database as db_module


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    """Redirect all DB calls to a temporary file for each test."""
    temp_db = tmp_path / "test_news.db"
    with patch.object(db_module, "DB_PATH", temp_db):
        db_module.init_db(temp_db)
        yield temp_db


def _sample_article(**kwargs) -> dict:
    base = {
        "title": "GPT-5 Released by OpenAI",
        "url": "https://openai.com/blog/gpt-5",
        "source": "openai.com",
        "category": "AI Labs",
        "published_at": "2025-01-01T12:00:00Z",
        "summary": "OpenAI releases GPT-5 with improved reasoning.",
        "tags": ["OpenAI", "LLM", "AI"],
        "relevance": 0.9,
        "trend_score": 0.8,
        "sentiment": "positive",
        "raw_content": "Full article content here.",
    }
    base.update(kwargs)
    return base


def test_upsert_article_inserts_new(tmp_path):
    article = _sample_article()
    inserted = db_module.upsert_article(article)
    assert inserted is True


def test_upsert_article_prevents_duplicate(tmp_path):
    article = _sample_article()
    db_module.upsert_article(article)
    inserted_again = db_module.upsert_article(article)
    assert inserted_again is False


def test_get_articles_returns_inserted(tmp_path):
    db_module.upsert_article(_sample_article())
    articles = db_module.get_articles(limit=10)
    assert len(articles) == 1
    assert articles[0]["title"] == "GPT-5 Released by OpenAI"


def test_get_article_count(tmp_path):
    db_module.upsert_article(_sample_article())
    db_module.upsert_article(_sample_article(url="https://openai.com/blog/gpt-5-v2", title="GPT-5 v2"))
    assert db_module.get_article_count() == 2


def test_search_articles(tmp_path):
    db_module.upsert_article(_sample_article())
    results = db_module.search_articles("GPT-5")
    assert len(results) == 1


def test_upsert_repo(tmp_path):
    repo = {
        "name": "openai / openai-python",
        "url": "https://github.com/openai/openai-python",
        "description": "Official Python library for OpenAI API",
        "language": "Python",
        "stars": 15000,
        "forks": 2000,
        "today_stars": 150,
        "topics": ["openai", "llm"],
        "tags": ["OpenAI", "AI"],
        "summary": "",
    }
    result = db_module.upsert_repo(repo)
    assert result is True
    repos = db_module.get_repos(limit=5)
    assert len(repos) == 1
    assert repos[0]["name"] == "openai / openai-python"


def test_pipeline_logging(tmp_path):
    db_module.upsert_pipeline_run("run-001")
    db_module.log_pipeline_event(
        run_id="run-001",
        agent_name="DataCollector",
        status="success",
        message="Fetched 50 articles",
        items_processed=50,
    )
    logs = db_module.get_pipeline_logs(limit=10)
    assert len(logs) >= 1
    assert logs[0]["agent_name"] == "DataCollector"
