"""
pipeline.py
-----------
LangGraph Pipeline Orchestration v2

Defines the full multi-agent StateGraph:

  DataCollector → ContentFilter → ResearchPaperAgent → TrendAnalyzer
      → LLMSummarizer → StorageAgent

The pipeline can be triggered manually (run_pipeline()) or via the
SchedulerAgent for automated periodic runs.
"""

import uuid
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from src.logger import get_logger, setup_logging
from src.agents.data_collector_agent import run_data_collector
from src.agents.content_filter_agent import run_content_filter
from src.agents.trend_analyzer_agent import run_trend_analyzer
from src.agents.llm_summarizer_agent import run_llm_summarizer
from src.agents.storage_agent import run_storage_agent
from src.agents.research_paper_agent import run_research_paper_agent
from src.database import init_db, upsert_pipeline_run, log_pipeline_event

setup_logging()
logger = get_logger("pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline State
# ─────────────────────────────────────────────────────────────────────────────

class PipelineState(TypedDict, total=False):
    run_id: str
    started_at: str

    # Data Collector outputs
    raw_articles: list[dict]
    raw_repos: list[dict]
    collector_elapsed: float

    # Content Filter outputs
    filtered_articles: list[dict]
    filtered_repos: list[dict]
    filter_elapsed: float

    # Research Paper Agent outputs
    research_papers: list[dict]
    paper_agent_elapsed: float

    # Trend Analyzer outputs
    analyzed_articles: list[dict]
    trending_topics: list[dict]
    analyzer_elapsed: float

    # LLM Summarizer outputs
    summarized_articles: list[dict]
    summarized_repos: list[dict]
    summarized_papers: list[dict]
    summarizer_elapsed: float

    # Storage Agent outputs
    stored_articles_count: int
    stored_repos_count: int
    stored_papers_count: int
    storage_elapsed: float


# ─────────────────────────────────────────────────────────────────────────────
# Build the LangGraph
# ─────────────────────────────────────────────────────────────────────────────

def build_pipeline() -> Any:
    graph = StateGraph(PipelineState)

    graph.add_node("data_collector",  run_data_collector)
    graph.add_node("content_filter",  run_content_filter)
    graph.add_node("research_papers", run_research_paper_agent)
    graph.add_node("trend_analyzer",  run_trend_analyzer)
    graph.add_node("llm_summarizer",  run_llm_summarizer)
    graph.add_node("storage_agent",   run_storage_agent)

    graph.set_entry_point("data_collector")
    graph.add_edge("data_collector",  "content_filter")
    graph.add_edge("content_filter",  "research_papers")
    graph.add_edge("research_papers", "trend_analyzer")
    graph.add_edge("trend_analyzer",  "llm_summarizer")
    graph.add_edge("llm_summarizer",  "storage_agent")
    graph.add_edge("storage_agent",   END)

    return graph.compile()


_compiled_pipeline = None


def get_pipeline():
    global _compiled_pipeline
    if _compiled_pipeline is None:
        init_db()
        _compiled_pipeline = build_pipeline()
    return _compiled_pipeline


# ─────────────────────────────────────────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline() -> dict:
    """Execute the full multi-agent pipeline. Returns the final state dict."""
    run_id = str(uuid.uuid4())[:12]
    started_at = datetime.utcnow().isoformat()

    logger.info("=" * 60)
    logger.info("Pipeline run starting — run_id=%s", run_id)
    logger.info("=" * 60)

    try:
        upsert_pipeline_run(run_id, started_at=started_at, status="running")
        log_pipeline_event(
            run_id=run_id,
            agent_name="Pipeline",
            status="success",
            message="Pipeline run started",
            started_at=started_at,
        )
    except Exception as exc:
        logger.warning("Could not log pipeline start: %s", exc)

    initial_state: PipelineState = {
        "run_id": run_id,
        "started_at": started_at,
    }

    try:
        pipeline = get_pipeline()
        final_state = pipeline.invoke(initial_state)

        logger.info(
            "Pipeline complete — articles=%d, repos=%d, papers=%d",
            final_state.get("stored_articles_count", 0),
            final_state.get("stored_repos_count", 0),
            final_state.get("stored_papers_count", 0),
        )
        return dict(final_state)

    except Exception as exc:
        logger.error("Pipeline failed — run_id=%s: %s", run_id, exc)
        try:
            upsert_pipeline_run(
                run_id,
                status="error",
                error_message=str(exc),
                finished_at=datetime.utcnow().isoformat(),
            )
        except Exception:
            pass
        return {"error": str(exc), "run_id": run_id}
