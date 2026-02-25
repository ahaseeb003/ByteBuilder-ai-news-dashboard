"""
trend_analyzer_agent.py
-----------------------
Agent 3 – Trend Analyzer

Responsibilities:
  • Score articles by popularity / trend signals
  • Identify trending topics using TF-IDF-style keyword frequency
  • Cluster similar articles by shared keywords
  • Attach trend_score to each article
"""

import re
import math
from collections import Counter, defaultdict
from typing import Any
from datetime import datetime, timezone

from src.logger import get_logger
from config.settings import AI_KEYWORDS

logger = get_logger("trend_analyzer_agent")

# ─────────────────────────────────────────────────────────────────────────────
# Keyword Frequency / Trend Scoring
# ─────────────────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "this", "that", "it", "its", "as", "we", "our", "their", "have",
    "has", "had", "do", "does", "did", "will", "would", "can", "could",
    "may", "might", "shall", "should", "not", "no", "so", "if", "then",
    "than", "more", "most", "also", "just", "new", "how", "what", "when",
    "where", "who", "which", "all", "about", "into", "up", "out", "use",
}


def _tokenise(text: str) -> list[str]:
    """Lower-case tokenisation with stopword removal."""
    tokens = re.findall(r"\b[a-z][a-z0-9\-]{2,}\b", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _compute_keyword_frequencies(articles: list[dict]) -> Counter:
    """Count how many articles mention each AI keyword."""
    freq: Counter = Counter()
    for article in articles:
        text = (article.get("title", "") + " " + article.get("raw_content", "")).lower()
        for kw in AI_KEYWORDS:
            if kw in text:
                freq[kw] += 1
    return freq


def score_trend(article: dict, global_freq: Counter, total_docs: int) -> float:
    """
    Compute a trend score using a TF-IDF-inspired formula.
    Higher score = more trending / relevant.
    """
    text = (article.get("title", "") + " " + article.get("raw_content", "")).lower()
    score = 0.0

    for kw in AI_KEYWORDS:
        if kw in text:
            tf = text.count(kw)
            df = global_freq.get(kw, 1)
            idf = math.log((total_docs + 1) / (df + 1)) + 1.0
            score += tf * idf

    # Recency boost: articles published recently get a small bonus
    published = article.get("published_at", "") or article.get("collected_at", "")
    recency_boost = _recency_boost(published)
    score *= (1.0 + recency_boost)

    # Normalise to 0–1 range (soft cap)
    return round(min(1.0, score / 50.0), 4)


def _recency_boost(date_str: str) -> float:
    """Return a 0–0.5 boost based on how recent the article is."""
    if not date_str:
        return 0.0
    try:
        from src.utils import parse_date
        dt = parse_date(date_str)
        if dt is None:
            return 0.0
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_hours = (now - dt).total_seconds() / 3600
        if age_hours < 6:
            return 0.5
        if age_hours < 24:
            return 0.3
        if age_hours < 72:
            return 0.1
        return 0.0
    except Exception:
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Topic Clustering
# ─────────────────────────────────────────────────────────────────────────────

_TOPIC_CLUSTERS: dict[str, list[str]] = {
    "LLMs & Language Models": [
        "large language model", "llm", "gpt", "chatgpt", "claude", "gemini",
        "mistral", "llama", "transformer", "bert", "fine-tuning",
    ],
    "Generative AI & Images": [
        "generative ai", "diffusion", "stable diffusion", "text-to-image",
        "image generation", "dall-e", "midjourney", "multimodal",
    ],
    "AI Agents & Automation": [
        "autonomous agent", "ai agent", "langchain", "langgraph", "rag",
        "retrieval augmented generation", "tool use", "agentic",
    ],
    "Research & Benchmarks": [
        "benchmark", "leaderboard", "sota", "state-of-the-art", "paper",
        "arxiv", "research", "evaluation", "dataset",
    ],
    "MLOps & Infrastructure": [
        "mlops", "model deployment", "inference", "cuda", "gpu", "tpu",
        "pytorch", "tensorflow", "jax", "vector database", "embeddings",
    ],
    "AI Safety & Ethics": [
        "ai safety", "alignment", "bias", "harmful", "regulation",
        "responsible ai", "governance",
    ],
    "Computer Vision & Robotics": [
        "computer vision", "robotics", "autonomous driving", "object detection",
        "image recognition", "video",
    ],
    "NLP & Speech": [
        "natural language processing", "nlp", "speech recognition",
        "text-to-speech", "translation", "sentiment",
    ],
}


def assign_cluster(article: dict) -> str:
    """Assign the best-matching topic cluster to an article."""
    text = (article.get("title", "") + " " + article.get("raw_content", "")).lower()
    best_cluster = "General AI"
    best_hits = 0

    for cluster, keywords in _TOPIC_CLUSTERS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_cluster = cluster

    return best_cluster


def get_trending_topics(articles: list[dict], top_n: int = 10) -> list[dict]:
    """
    Return the top-N trending topics with their article counts.
    """
    cluster_counts: Counter = Counter()
    for article in articles:
        cluster = article.get("cluster", assign_cluster(article))
        cluster_counts[cluster] += 1

    return [
        {"topic": topic, "count": count}
        for topic, count in cluster_counts.most_common(top_n)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Agent Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def run_trend_analyzer(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node function for the Trend Analyzer Agent.

    Reads:  state["filtered_articles"], state["filtered_repos"]
    Writes: state["analyzed_articles"], state["trending_topics"]
    """
    logger.info("[TrendAnalyzer] Analysing trends …")
    start = datetime.utcnow()

    articles: list[dict] = state.get("filtered_articles", [])
    repos: list[dict] = state.get("filtered_repos", [])

    # Compute global keyword frequencies for IDF
    global_freq = _compute_keyword_frequencies(articles)
    total_docs = max(len(articles), 1)

    analyzed: list[dict] = []
    for article in articles:
        article["trend_score"] = score_trend(article, global_freq, total_docs)
        article["cluster"] = assign_cluster(article)
        analyzed.append(article)

    # Sort by combined score
    analyzed.sort(
        key=lambda a: (a["trend_score"] + a["relevance"]) / 2,
        reverse=True,
    )

    trending_topics = get_trending_topics(analyzed)

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(
        "[TrendAnalyzer] Done in %.1fs — top topic: %s",
        elapsed,
        trending_topics[0]["topic"] if trending_topics else "N/A",
    )

    return {
        **state,
        "analyzed_articles": analyzed,
        "trending_topics": trending_topics,
        "analyzer_elapsed": elapsed,
    }
