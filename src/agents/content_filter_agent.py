"""
content_filter_agent.py
-----------------------
Agent 2 – Content Filter

Responsibilities:
  • Remove off-topic content using keyword-based relevance scoring
  • Deduplicate articles by URL hash
  • Compute a combined freshness+relevance score for sorting
  • Sort articles newest-first (recency weighted) so the feed always shows
    the latest news at the top
  • Attach lightweight sentiment labels and hashtags

Developed by HMtechie & ByteBuilder
"""

from typing import Any
from datetime import datetime, timezone

from src.logger import get_logger
from src.utils import (
    compute_relevance_score,
    is_ai_related,
    deduplicate,
    simple_sentiment,
    generate_hashtags,
)

logger = get_logger("content_filter_agent")

# Minimum relevance score — very low so we keep all tech content, not just AI
_MIN_RELEVANCE = 0.03

# Weight of recency vs relevance in the combined sort score
# 0.6 recency + 0.4 relevance = "latest news first, but quality matters"
_RECENCY_WEIGHT   = 0.6
_RELEVANCE_WEIGHT = 0.4


def _combined_score(article: dict) -> float:
    """
    Compute a combined score that balances freshness and relevance.
    Both components are already normalised to [0, 1].
    """
    recency   = float(article.get("recency_score", 0.1))
    relevance = float(article.get("relevance", 0.0))
    return _RECENCY_WEIGHT * recency + _RELEVANCE_WEIGHT * relevance


def filter_articles(raw_articles: list[dict]) -> list[dict]:
    """
    Filter, deduplicate, and rank a list of raw article dicts.

    Steps:
      1. Compute relevance score for each article.
      2. Discard articles below the minimum threshold.
      3. Deduplicate by URL.
      4. Attach sentiment labels and auto-generated hashtags.
      5. Compute combined freshness+relevance score.
      6. Sort by combined score descending (latest + most relevant first).
    """
    scored: list[dict] = []

    for article in raw_articles:
        title   = article.get("title", "")
        content = article.get("raw_content", "")

        # AI tools always pass through (pre-filtered at source)
        if article.get("item_type") == "ai_tool":
            score = max(float(article.get("relevance", 0.5)), 0.5)
        else:
            score = compute_relevance_score(title, content)

        if score < _MIN_RELEVANCE:
            logger.debug("Filtered out (score=%.3f): %s", score, title[:80])
            continue

        article["relevance"] = score
        article["sentiment"] = simple_sentiment(title + " " + content)
        article["tags"]      = generate_hashtags(title + " " + content)
        scored.append(article)

    # Deduplicate by URL
    unique = deduplicate(scored, key="url")

    # Sort by combined freshness+relevance score — NEWEST + MOST RELEVANT first
    unique.sort(key=_combined_score, reverse=True)

    # Store the combined score for the dashboard to display
    for article in unique:
        article["trend_score"] = round(_combined_score(article), 3)

    logger.info(
        "Filter: %d raw → %d after filtering → %d after deduplication (sorted newest-first)",
        len(raw_articles), len(scored), len(unique),
    )
    return unique


def filter_repos(raw_repos: list[dict]) -> list[dict]:
    """
    Filter GitHub repos to AI/ML-related ones and deduplicate.
    """
    from config.settings import GITHUB_TRENDING_AI_TOPICS

    filtered: list[dict] = []
    for repo in raw_repos:
        desc = (repo.get("description") or "").lower()
        name = (repo.get("name") or "").lower()
        lang = (repo.get("language") or "").lower()

        is_ai = (
            is_ai_related(repo.get("name", ""), repo.get("description", ""))
            or any(t in desc or t in name for t in GITHUB_TRENDING_AI_TOPICS)
            or lang in ("python", "jupyter notebook", "r")
        )

        if is_ai:
            repo["tags"] = generate_hashtags(
                repo.get("name", "") + " " + repo.get("description", "")
            )
            filtered.append(repo)

    unique = deduplicate(filtered, key="url")
    unique.sort(key=lambda r: r.get("today_stars", 0), reverse=True)

    logger.info(
        "Repo filter: %d raw → %d AI-related repos",
        len(raw_repos), len(unique),
    )
    return unique


def run_content_filter(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node function for the Content Filter Agent.

    Reads:  state["raw_articles"], state["raw_repos"]
    Writes: state["filtered_articles"], state["filtered_repos"]
    """
    logger.info("[ContentFilter] Filtering and sorting content …")
    start = datetime.now(timezone.utc)

    filtered_articles = filter_articles(state.get("raw_articles", []))
    filtered_repos    = filter_repos(state.get("raw_repos", []))

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(
        "[ContentFilter] Done in %.1fs — %d articles, %d repos",
        elapsed, len(filtered_articles), len(filtered_repos),
    )

    return {
        **state,
        "filtered_articles": filtered_articles,
        "filtered_repos":    filtered_repos,
        "filter_elapsed":    elapsed,
    }