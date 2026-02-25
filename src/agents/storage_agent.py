"""
storage_agent.py
----------------
Agent 5 – Storage Agent v2

Persists all processed data from the pipeline into the SQLite database:
  • Summarised articles  → articles table
  • Summarised repos     → github_repos table
  • Summarised papers    → research_papers table
  • Pipeline run metadata → pipeline_runs / pipeline_logs tables
"""

from datetime import datetime
from typing import Any

from src.database import upsert_article, upsert_repo, upsert_pipeline_run, log_pipeline_event
from src.logger import get_logger

logger = get_logger("storage_agent")


def store_articles(articles: list[dict], run_id: str) -> int:
    """Persist articles to SQLite. Returns count of newly inserted records."""
    inserted = 0
    for article in articles:
        try:
            if upsert_article(article):
                inserted += 1
        except Exception as exc:
            logger.warning("Failed to store article '%s': %s", article.get("title", "")[:60], exc)
    logger.info("Stored %d new articles (out of %d)", inserted, len(articles))
    return inserted


def store_repos(repos: list[dict], run_id: str) -> int:
    """Persist GitHub repos to SQLite. Returns count of upserted records."""
    upserted = 0
    for repo in repos:
        try:
            if upsert_repo(repo):
                upserted += 1
        except Exception as exc:
            logger.warning("Failed to store repo '%s': %s", repo.get("name", ""), exc)
    logger.info("Stored %d new repos (out of %d)", upserted, len(repos))
    return upserted


def store_papers_local(papers: list[dict]) -> int:
    """Persist research papers to SQLite. Returns count of newly inserted records."""
    inserted = 0
    try:
        from src.agents.research_paper_agent import store_papers
        inserted = store_papers(papers)
    except Exception as exc:
        logger.warning("Failed to store research papers: %s", exc)
    logger.info("Stored %d new research papers (out of %d)", inserted, len(papers))
    return inserted


def run_storage_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node function for the Storage Agent.

    Reads:  state["summarized_articles"], state["summarized_repos"],
            state["summarized_papers"], state["run_id"]
    Writes: state["stored_articles_count"], state["stored_repos_count"],
            state["stored_papers_count"]
    """
    logger.info("[StorageAgent] Persisting data to database …")
    start = datetime.utcnow()

    run_id: str = state.get("run_id", "unknown")
    articles: list[dict] = state.get("summarized_articles", [])
    repos: list[dict] = state.get("summarized_repos", [])
    papers: list[dict] = state.get("summarized_papers", [])

    stored_articles = store_articles(articles, run_id)
    stored_repos = store_repos(repos, run_id)
    stored_papers = store_papers_local(papers)

    elapsed = (datetime.utcnow() - start).total_seconds()

    # Update pipeline run record
    try:
        upsert_pipeline_run(
            run_id,
            total_collected=len(state.get("raw_articles", [])),
            total_filtered=len(state.get("filtered_articles", [])),
            total_summarized=len(articles),
            finished_at=datetime.utcnow().isoformat(),
            status="success",
        )
        log_pipeline_event(
            run_id=run_id,
            agent_name="StorageAgent",
            status="success",
            message=(
                f"Stored {stored_articles} articles, "
                f"{stored_repos} repos, "
                f"{stored_papers} papers"
            ),
            items_processed=stored_articles + stored_repos + stored_papers,
            finished_at=datetime.utcnow().isoformat(),
        )
    except Exception as exc:
        logger.error("Failed to update pipeline run record: %s", exc)

    logger.info("[StorageAgent] Done in %.1fs", elapsed)

    return {
        **state,
        "stored_articles_count": stored_articles,
        "stored_repos_count": stored_repos,
        "stored_papers_count": stored_papers,
        "storage_elapsed": elapsed,
    }
