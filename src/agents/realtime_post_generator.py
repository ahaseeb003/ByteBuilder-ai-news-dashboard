"""
realtime_post_generator.py
--------------------------
Real-Time Research Post Generator v3

Developed by HMtechie & ByteBuilder

This module powers the "Custom Topic" feature in the Post Creator panel.
Given a topic keyword, URL, or arXiv ID, it:
  1. Detects the input type (keyword / URL / arXiv ID)
  2. Gathers real-time information from multiple sources:
       - arXiv API (for research topics)
       - DuckDuckGo / web search (for news topics)
       - Direct URL scraping (for URL inputs)
  3. Synthesises gathered information into a structured context
  4. Calls the LLM with the appropriate template prompt
  5. Returns the generated post + list of reference links

Architecture note:
  This is a standalone LangGraph sub-graph with 4 nodes:
    InputClassifier → ContextGatherer → PostWriter → QualityChecker
  The QualityChecker uses a conditional edge: if quality < threshold,
  it loops back to PostWriter for a revision (max 2 retries).
"""

import os
import re
import time
import json
from datetime import datetime
from typing import TypedDict, Any

import requests
from bs4 import BeautifulSoup

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from src.logger import get_logger
from src.agents.llm_summarizer_agent import (
    _call_llm,
    BYTEBUILDER_FOOTER,
    _AI_INSIGHT_SYSTEM,
    _TECH_UPDATE_SYSTEM,
    _NEW_AI_TOOL_SYSTEM,
    _WEEKLY_DIGEST_SYSTEM,
    _DEEP_DIVE_SYSTEM,
    # legacy aliases still exported
    _TECH_INSIGHT_SYSTEM,
    _RESEARCH_PAPER_SYSTEM,
    _QUICK_NEWS_SYSTEM,
)

logger = get_logger("realtime_post_generator")

# ─────────────────────────────────────────────────────────────────────────────
# Sub-Graph State
# ─────────────────────────────────────────────────────────────────────────────

class RTPostState(TypedDict, total=False):
    # Input
    user_input: str
    template_id: str
    extra_context: str

    # Classifier outputs
    input_type: str          # "arxiv_id" | "url" | "keyword"
    arxiv_id: str
    clean_url: str
    search_query: str

    # Gatherer outputs
    gathered_text: str
    references: list[dict]   # [{"title": ..., "url": ...}]
    sources_used: int

    # Writer outputs
    draft_post: str
    revision_count: int

    # Checker outputs
    quality_ok: bool
    quality_feedback: str

    # Final
    final_post: str
    elapsed: float


# ─────────────────────────────────────────────────────────────────────────────
# Node 1: Input Classifier
# ─────────────────────────────────────────────────────────────────────────────

def _classify_input(state: RTPostState) -> RTPostState:
    user_input = state.get("user_input", "").strip()

    # arXiv ID pattern: 2401.12345 or arxiv:2401.12345
    arxiv_pattern = re.compile(r"(?:arxiv[:\s])?(\d{4}\.\d{4,5})", re.IGNORECASE)
    arxiv_match = arxiv_pattern.search(user_input)

    if arxiv_match:
        return {**state, "input_type": "arxiv_id", "arxiv_id": arxiv_match.group(1)}

    # URL pattern
    if re.match(r"https?://", user_input):
        return {**state, "input_type": "url", "clean_url": user_input}

    # Default: keyword search
    return {**state, "input_type": "keyword", "search_query": user_input}


# ─────────────────────────────────────────────────────────────────────────────
# Node 2: Context Gatherer
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_arxiv(arxiv_id: str) -> tuple[str, list[dict]]:
    """Fetch paper details from arXiv API."""
    try:
        url = f"https://export.arxiv.org/abs/{arxiv_id}"
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "xml")
        entry = soup.find("entry")
        if not entry:
            return "", []

        title = entry.find("title").get_text(strip=True) if entry.find("title") else ""
        summary = entry.find("summary").get_text(strip=True) if entry.find("summary") else ""
        authors_tags = entry.find_all("author")
        authors = ", ".join(a.find("name").get_text(strip=True) for a in authors_tags[:5])
        published = entry.find("published").get_text(strip=True)[:10] if entry.find("published") else ""
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        text = (
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Published: {published}\n"
            f"Abstract: {summary}\n"
            f"PDF: {pdf_url}"
        )
        refs = [
            {"title": f"{title} (arXiv)", "url": url},
            {"title": f"{title} — PDF", "url": pdf_url},
        ]
        return text, refs
    except Exception as exc:
        logger.warning("arXiv fetch failed for %s: %s", arxiv_id, exc)
        return "", []


def _fetch_url(url: str) -> tuple[str, list[dict]]:
    """Scrape text content from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AINewsDashboard/3.0)"}
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script/style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Get title
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else url

        # Get main content
        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text(strip=True) for p in paragraphs[:20])
        content = content[:2000]

        text = f"Title: {title_text}\nURL: {url}\nContent: {content}"
        refs = [{"title": title_text, "url": url}]
        return text, refs
    except Exception as exc:
        logger.warning("URL fetch failed for %s: %s", url, exc)
        return "", []


def _search_ddg(query: str, max_results: int = 5) -> tuple[str, list[dict]]:
    """Search DuckDuckGo for a query and return text + references."""
    try:
        search_url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        resp = requests.get(search_url, params=params, timeout=8)
        data = resp.json()

        snippets = []
        refs = []

        # Abstract (main result)
        if data.get("AbstractText"):
            snippets.append(f"Overview: {data['AbstractText']}")
            if data.get("AbstractURL"):
                refs.append({"title": data.get("Heading", query), "url": data["AbstractURL"]})

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                snippets.append(topic["Text"])
                if topic.get("FirstURL"):
                    refs.append({
                        "title": topic["Text"][:60],
                        "url": topic["FirstURL"],
                    })

        text = "\n\n".join(snippets) if snippets else ""
        return text, refs
    except Exception as exc:
        logger.warning("DDG search failed for '%s': %s", query, exc)
        return "", []


def _search_arxiv_by_keyword(query: str, max_results: int = 3) -> tuple[str, list[dict]]:
    """Search arXiv for recent papers matching a keyword."""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(query)
        api_url = (
            f"http://export.arxiv.org/api/query?"
            f"search_query=all:{encoded}&start=0&max_results={max_results}"
            f"&sortBy=submittedDate&sortOrder=descending"
        )
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "xml")
        entries = soup.find_all("entry")

        snippets = []
        refs = []
        for entry in entries:
            title = entry.find("title").get_text(strip=True) if entry.find("title") else ""
            summary = entry.find("summary").get_text(strip=True)[:300] if entry.find("summary") else ""
            link = entry.find("id").get_text(strip=True) if entry.find("id") else ""
            if title:
                snippets.append(f"Paper: {title}\nAbstract: {summary}")
                refs.append({"title": f"{title} (arXiv)", "url": link})

        text = "\n\n".join(snippets)
        return text, refs
    except Exception as exc:
        logger.warning("arXiv keyword search failed for '%s': %s", query, exc)
        return "", []


def _gather_context(state: RTPostState) -> RTPostState:
    input_type = state.get("input_type", "keyword")
    all_texts = []
    all_refs = []

    if input_type == "arxiv_id":
        text, refs = _fetch_arxiv(state.get("arxiv_id", ""))
        if text:
            all_texts.append(text)
            all_refs.extend(refs)

    elif input_type == "url":
        text, refs = _fetch_url(state.get("clean_url", ""))
        if text:
            all_texts.append(text)
            all_refs.extend(refs)

    else:
        query = state.get("search_query", state.get("user_input", ""))

        # DDG search
        ddg_text, ddg_refs = _search_ddg(query)
        if ddg_text:
            all_texts.append(f"Web Search Results:\n{ddg_text}")
            all_refs.extend(ddg_refs)

        # arXiv search (for AI/ML topics)
        arxiv_text, arxiv_refs = _search_arxiv_by_keyword(query, max_results=2)
        if arxiv_text:
            all_texts.append(f"Related Research Papers:\n{arxiv_text}")
            all_refs.extend(arxiv_refs)

    # Add extra context from user
    extra = state.get("extra_context", "").strip()
    if extra:
        all_texts.append(f"Additional context: {extra}")

    gathered = "\n\n---\n\n".join(all_texts)[:5000]

    return {
        **state,
        "gathered_text": gathered,
        "references": all_refs[:8],
        "sources_used": len(all_refs),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 3: Post Writer
# ─────────────────────────────────────────────────────────────────────────────

_WRITER_SYSTEM = {
    "tech_insight":   _AI_INSIGHT_SYSTEM,
    "ai_insight":     _AI_INSIGHT_SYSTEM,
    "research_paper": _AI_INSIGHT_SYSTEM,
    "quick_news":     _TECH_UPDATE_SYSTEM,
    "tech_update":    _TECH_UPDATE_SYSTEM,
    "new_ai_tool":    _NEW_AI_TOOL_SYSTEM,
    "weekly_digest":  _WEEKLY_DIGEST_SYSTEM,
    "weekly_update":  _WEEKLY_DIGEST_SYSTEM,
    "deep_dive":      _DEEP_DIVE_SYSTEM,
}

_WRITER_SYSTEM_DEFAULT = """You are an expert AI/tech content writer for a Telegram channel.
Write a detailed, engaging post about the given topic based on the research gathered.
Use emojis, clear structure, and include reference links.
Format it professionally for a tech audience.
"""


def _write_post(state: RTPostState) -> RTPostState:
    template_id = state.get("template_id", "tech_insight")
    user_input = state.get("user_input", "")
    gathered_text = state.get("gathered_text", "")
    references = state.get("references", [])
    revision_count = state.get("revision_count", 0)
    quality_feedback = state.get("quality_feedback", "")

    system_prompt = _WRITER_SYSTEM.get(template_id, _WRITER_SYSTEM_DEFAULT)

    # Build reference list for prompt
    ref_lines = "\n".join(
        f"- {r.get('title', '')} — {r.get('url', '')}"
        for r in references[:6]
    )

    revision_note = ""
    if revision_count > 0 and quality_feedback:
        revision_note = f"\n\nIMPROVEMENT NEEDED: {quality_feedback}\nPlease revise accordingly."

    user_prompt = (
        f"Topic: {user_input}\n\n"
        f"Research gathered:\n{gathered_text}\n\n"
        f"Reference links to include:\n{ref_lines}\n"
        f"{revision_note}\n\n"
        "Write the post now. Include at least one reference link in the post body."
    )

    post = _call_llm(system_prompt, user_prompt, max_tokens=2000)

    if not post:
        # Fallback
        post = (
            f"🔥 Tech Insight: {user_input}\n\n"
            f"📌 Overview:\n{gathered_text[:400]}\n\n"
        )
        if references:
            post += f"🔗 Learn More: {references[0].get('url', '')}\n"
        post += "\n#AI #Tech #Innovation"

    return {
        **state,
        "draft_post": post,
        "revision_count": revision_count + 1,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 4: Quality Checker
# ─────────────────────────────────────────────────────────────────────────────

def _check_quality(state: RTPostState) -> RTPostState:
    post = state.get("draft_post", "")
    revision_count = state.get("revision_count", 0)

    issues = []

    # Must have some content
    if len(post) < 200:
        issues.append("Post is too short (under 200 characters)")

    # Must have at least one URL
    if "http" not in post:
        issues.append("No reference URL found in post")

    # Must have at least one emoji
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF\U00002600-\U000027BF]", flags=re.UNICODE
    )
    if not emoji_pattern.search(post):
        issues.append("No emojis found — add relevant emojis for engagement")

    quality_ok = len(issues) == 0 or revision_count >= 2

    return {
        **state,
        "quality_ok": quality_ok,
        "quality_feedback": "; ".join(issues) if issues else "",
    }


def _route_quality(state: RTPostState) -> str:
    if state.get("quality_ok", True):
        return "finalize"
    return "revise"


# ─────────────────────────────────────────────────────────────────────────────
# Node 5: Finalizer
# ─────────────────────────────────────────────────────────────────────────────

def _finalize(state: RTPostState) -> RTPostState:
    post = state.get("draft_post", "")
    return {**state, "final_post": post + BYTEBUILDER_FOOTER}


# ─────────────────────────────────────────────────────────────────────────────
# Build the Sub-Graph
# ─────────────────────────────────────────────────────────────────────────────

def _build_rt_graph():
    if not LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(RTPostState)
    graph.add_node("classify",  _classify_input)
    graph.add_node("gather",    _gather_context)
    graph.add_node("write",     _write_post)
    graph.add_node("check",     _check_quality)
    graph.add_node("finalize",  _finalize)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "gather")
    graph.add_edge("gather",   "write")
    graph.add_edge("write",    "check")
    graph.add_conditional_edges(
        "check",
        _route_quality,
        {"finalize": "finalize", "revise": "write"},
    )
    graph.add_edge("finalize", END)

    return graph.compile()


_RT_GRAPH = None


def _get_rt_graph():
    global _RT_GRAPH
    if _RT_GRAPH is None:
        _RT_GRAPH = _build_rt_graph()
    return _RT_GRAPH


# ─────────────────────────────────────────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def generate_realtime_post(
    user_input: str,
    template_id: str = "tech_insight",
    extra_context: str = "",
) -> dict:
    """
    Generate a real-time research-based post.

    Args:
        user_input:    Topic keyword, URL, or arXiv ID
        template_id:   "tech_insight" | "research_paper" | "quick_news"
        extra_context: Optional extra instructions from the user

    Returns:
        {
            "post":         str,
            "references":   list[dict],
            "sources_used": int,
            "topic":        str,
            "elapsed":      float,
        }
    """
    start = time.time()
    logger.info("[RTPostGen] Generating post for: '%s' (template: %s)", user_input, template_id)

    initial_state: RTPostState = {
        "user_input": user_input,
        "template_id": template_id,
        "extra_context": extra_context,
        "revision_count": 0,
    }

    try:
        graph = _get_rt_graph()
        if graph:
            final_state = graph.invoke(initial_state)
        else:
            # Fallback: run nodes manually without LangGraph
            s = _classify_input(initial_state)
            s = _gather_context(s)
            s = _write_post(s)
            s = _check_quality(s)
            s = _finalize(s)
            final_state = s

        elapsed = time.time() - start
        logger.info("[RTPostGen] Done in %.1fs using %d sources", elapsed, final_state.get("sources_used", 0))

        return {
            "post": final_state.get("final_post", ""),
            "references": final_state.get("references", []),
            "sources_used": final_state.get("sources_used", 0),
            "topic": user_input,
            "elapsed": elapsed,
        }

    except Exception as exc:
        logger.error("[RTPostGen] Failed: %s", exc)
        elapsed = time.time() - start
        return {
            "post": f"⚠️ Error generating post: {exc}",
            "references": [],
            "sources_used": 0,
            "topic": user_input,
            "elapsed": elapsed,
        }