"""
dashboard.py — AI Tech News Dashboard v3
-----------------------------------------
Developed by HMtechie & ByteBuilder

Two-Panel Architecture:
  📡 Trending News Feed  — Browse latest AI/tech news, papers, repos.
                           Click "Add to Post Creator" on any item.
  ✍️  Post Creator       — Choose template + content source (saved items
                           or custom topic) → generate channel-ready post.
"""

import sys
import os
import json
import html as html_lib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config — MUST be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI News Dashboard · ByteBuilder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Clean, modern dark theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
[data-testid="stAppViewContainer"] {
    background: #0d1117;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] {
    background: #010409;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] > div:first-child { padding: 0; }

/* ── Typography ── */
h1, h2, h3, h4, h5 { color: #f0f6fc !important; font-weight: 700; }
p, li, label { color: #8b949e; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Cards ── */
.bb-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.bb-card:hover {
    border-color: #388bfd;
    box-shadow: 0 0 0 1px #388bfd22;
}
.bb-card-title {
    font-size: 0.97rem;
    font-weight: 600;
    color: #f0f6fc;
    margin: 0 0 6px 0;
    line-height: 1.4;
}
.bb-card-title a { color: #f0f6fc; }
.bb-card-title a:hover { color: #58a6ff; text-decoration: none; }
.bb-card-meta {
    font-size: 0.75rem;
    color: #6e7681;
    margin-bottom: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
}
.bb-card-meta span { color: #6e7681; }
.bb-card-body {
    font-size: 0.85rem;
    color: #8b949e;
    line-height: 1.6;
    margin-bottom: 10px;
    min-height: 20px;
}
.bb-card-footer {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 6px;
    border-top: 1px solid #21262d;
    padding-top: 8px;
}

/* ── Tags ── */
.bb-tag {
    display: inline-block;
    background: #1f2937;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 1px 9px;
    font-size: 0.7rem;
    color: #58a6ff;
    margin-right: 3px;
    margin-bottom: 3px;
}

/* ── Badges ── */
.bb-badge {
    display: inline-block;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.7rem;
    font-weight: 600;
    white-space: nowrap;
}
.bb-badge-green  { background: #1a3a1f; color: #3fb950; border: 1px solid #2ea04344; }
.bb-badge-yellow { background: #2d2a0f; color: #d29922; border: 1px solid #d2992244; }
.bb-badge-blue   { background: #0c2340; color: #58a6ff; border: 1px solid #58a6ff44; }
.bb-badge-red    { background: #3a1a1a; color: #f85149; border: 1px solid #f8514944; }
.bb-badge-gray   { background: #21262d; color: #8b949e; border: 1px solid #30363d; }
.bb-badge-live   { background: #3a1a1a; color: #ff7b72; border: 1px solid #ff7b7244; }

/* ── Trend score bar ── */
.bb-score-bar-wrap { display: flex; align-items: center; gap: 6px; min-width: 90px; }
.bb-score-bar-bg {
    flex: 1; height: 4px; background: #21262d; border-radius: 2px; overflow: hidden;
}
.bb-score-bar-fill { height: 100%; border-radius: 2px; }

/* ── Section headers ── */
.bb-section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #f0f6fc;
    padding-bottom: 10px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 16px;
}

/* ── Post preview ── */
.bb-post-box {
    background: #010409;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.85rem;
    color: #e6edf3;
    white-space: pre-wrap;
    line-height: 1.65;
    max-height: 500px;
    overflow-y: auto;
}

/* ── Stat tiles ── */
.bb-stat {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
}
.bb-stat-num { font-size: 1.9rem; font-weight: 700; color: #58a6ff; line-height: 1; }
.bb-stat-label { font-size: 0.75rem; color: #6e7681; margin-top: 4px; }

/* ── Template card ── */
.bb-template-card {
    background: #161b22;
    border: 2px solid #21262d;
    border-radius: 10px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.15s;
    text-align: center;
    margin-bottom: 8px;
}
.bb-template-card:hover { border-color: #388bfd; }
.bb-template-icon { font-size: 1.8rem; margin-bottom: 6px; }
.bb-template-name { font-size: 0.88rem; font-weight: 600; color: #e6edf3; }
.bb-template-desc { font-size: 0.75rem; color: #6e7681; margin-top: 3px; }

/* ── Branding footer ── */
.bb-brand-footer {
    padding: 12px 16px;
    border-top: 1px solid #21262d;
}
.bb-brand-name { font-size: 0.85rem; font-weight: 700; color: #e6edf3; }
.bb-brand-sub  { font-size: 0.72rem; color: #6e7681; margin-top: 2px; }

/* ── Streamlit overrides ── */
.stButton > button {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 7px !important;
    font-size: 0.82rem !important;
    padding: 5px 12px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
    color: #58a6ff !important;
}
[data-testid="baseButton-primary"] {
    background: #1f6feb !important;
    border-color: #1f6feb !important;
    color: #fff !important;
}
[data-testid="baseButton-primary"]:hover {
    background: #388bfd !important;
    border-color: #388bfd !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #010409 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 7px !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #21262d !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #8b949e !important;
    background: transparent !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 6px 16px !important;
    font-size: 0.85rem !important;
}
.stTabs [aria-selected="true"] {
    color: #58a6ff !important;
    background: #0c2340 !important;
    border-bottom: 2px solid #58a6ff !important;
}
hr { border-color: #21262d !important; margin: 12px 0 !important; }
.stAlert { border-radius: 8px !important; }
.stSpinner > div { border-top-color: #58a6ff !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session State Initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "page": "feed",
        "selected_for_post": [],
        "creator_template": "new_ai_tool",
        "generated_post": None,
        "post_references": [],
        "post_meta": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─────────────────────────────────────────────────────────────────────────────
# DB / Agent helpers (cached)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _init_db():
    try:
        from src.database import init_db
        from src.agents.research_paper_agent import init_papers_table
        init_db()
        init_papers_table()
    except Exception:
        pass

_init_db()


def _run_pipeline():
    try:
        from src.pipeline import run_pipeline
        return run_pipeline()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=60, show_spinner=False)
def _get_articles(limit=50, search=None, category=None, sort_by="Latest"):
    try:
        from src.database import get_articles, search_articles
        if search:
            return search_articles(search, limit=limit)
        order_map = {
            "Latest":    "published_at_ts",
            "Trending":  "trend_score",
            "Relevance": "relevance",
            "Freshness": "recency_score",
        }
        order_by = order_map.get(sort_by, "published_at_ts")
        return get_articles(limit=limit, offset=0, category=category, order_by=order_by)
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _get_repos(limit=20):
    try:
        from src.database import get_repos
        return get_repos(limit=limit)
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _get_papers(limit=30, search=None):
    try:
        from src.agents.research_paper_agent import get_papers, search_papers
        if search:
            return search_papers(search, limit=limit)
        return get_papers(limit=limit)
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _get_stats():
    try:
        from src.database import get_article_count, get_repo_count, get_pipeline_logs
        return {
            "articles": get_article_count(),
            "repos":    get_repo_count(),
            "logs":     get_pipeline_logs(limit=3),
        }
    except Exception:
        return {"articles": 0, "repos": 0, "logs": []}


def _generate_post(item, template_id):
    try:
        from src.agents.llm_summarizer_agent import generate_post_for_template
        return generate_post_for_template(item, template_id)
    except Exception as e:
        return f"⚠️ Error generating post: {e}"


def _generate_realtime_post(user_input, template_id, extra_context=""):
    try:
        from src.agents.realtime_post_generator import generate_realtime_post
        return generate_realtime_post(user_input, template_id, extra_context)
    except Exception as e:
        return {"post": f"⚠️ Error: {e}", "references": [], "sources_used": 0, "topic": user_input, "elapsed": 0}


def _generate_weekly_post(articles, papers, repos):
    try:
        from src.agents.llm_summarizer_agent import generate_weekly_update_post
        week_label = datetime.now().strftime("%B %d, %Y — Week %W")
        top_repo = repos[0] if repos else {}
        return generate_weekly_update_post(articles, papers, top_repo, week_label)
    except Exception as e:
        return f"⚠️ Error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Pure helper functions (no HTML injection risk)
# ─────────────────────────────────────────────────────────────────────────────

def _add_to_post_creator(item: dict) -> bool:
    existing_urls = {i.get("url", "") for i in st.session_state.selected_for_post}
    url = item.get("url", "")
    if url and url not in existing_urls:
        st.session_state.selected_for_post.append(item)
        return True
    return False


def _parse_dt(dt_str: str):
    """Parse an ISO UTC string to an aware datetime. Returns None on failure."""
    if not dt_str:
        return None
    try:
        clean = str(dt_str).strip()
        # Handle Z suffix
        if clean.endswith("Z"):
            clean = clean[:-1] + "+00:00"
        # Handle naive ISO strings
        if "+" not in clean and len(clean) >= 19:
            clean = clean[:19] + "+00:00"
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def _time_ago(dt_str: str) -> str:
    """Return a human-readable 'Xh ago' string from an ISO UTC timestamp."""
    dt = _parse_dt(dt_str)
    if dt is None:
        return ""
    now = datetime.now(timezone.utc)
    seconds = int((now - dt).total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    days = seconds // 86400
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days}d ago"
    return dt.strftime("%b %d, %Y")


def _freshness_label(dt_str: str) -> tuple[str, str]:
    """
    Returns (label_text, css_class) for a freshness badge.
    Returns ("", "") if article is older than 48 hours.
    """
    dt = _parse_dt(dt_str)
    if dt is None:
        return "", ""
    hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    if hours < 1:
        return "🔴 LIVE", "bb-badge-live"
    if hours < 6:
        return "🟢 New", "bb-badge-green"
    if hours < 24:
        return "🔵 Today", "bb-badge-blue"
    if hours < 48:
        return "⚪ Yesterday", "bb-badge-gray"
    return "", ""


def _score_color(score: float) -> str:
    if score >= 0.7:
        return "#3fb950"
    if score >= 0.4:
        return "#d29922"
    return "#6e7681"


def _safe(text) -> str:
    """HTML-escape a value for safe insertion into HTML attributes or body."""
    return html_lib.escape(str(text or ""))


def _tags_html(tags) -> str:
    """Build tag pill HTML from a list or JSON string."""
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    if not tags:
        return ""
    return "".join(
        f'<span class="bb-tag">{_safe(t)}</span>'
        for t in (tags[:5] if isinstance(tags, list) else [])
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 16px 12px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                <span style="font-size:1.8rem;">🤖</span>
                <div>
                    <div style="font-size:1rem;font-weight:700;color:#f0f6fc;line-height:1.2;">
                        AI News Dashboard
                    </div>
                    <div style="font-size:0.72rem;color:#6e7681;">by ByteBuilder</div>
                </div>
            </div>
        </div>
        <hr>
        """, unsafe_allow_html=True)

        # Navigation
        n_selected = len(st.session_state.selected_for_post)
        st.markdown('<div style="padding:0 8px;">', unsafe_allow_html=True)

        if st.button(
            "📡  Trending News Feed",
            key="nav_feed",
            use_container_width=True,
            type="primary" if st.session_state.page == "feed" else "secondary",
        ):
            st.session_state.page = "feed"
            st.rerun()

        creator_label = f"✍️  Post Creator  ({n_selected})" if n_selected > 0 else "✍️  Post Creator"
        if st.button(
            creator_label,
            key="nav_creator",
            use_container_width=True,
            type="primary" if st.session_state.page == "creator" else "secondary",
        ):
            st.session_state.page = "creator"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        # Stats
        stats = _get_stats()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="bb-stat">
                <div class="bb-stat-num">{stats['articles']}</div>
                <div class="bb-stat-label">Articles</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="bb-stat">
                <div class="bb-stat-num">{stats['repos']}</div>
                <div class="bb-stat-label">Repos</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # Pipeline run button
        st.markdown('<div style="padding:0 8px;">', unsafe_allow_html=True)
        if st.button("▶  Refresh Feed", use_container_width=True, type="primary"):
            with st.spinner("Running pipeline…"):
                result = _run_pipeline()
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.success(
                    f"✅ {result.get('stored_articles_count', 0)} articles, "
                    f"{result.get('stored_repos_count', 0)} repos"
                )
                st.cache_data.clear()
                st.rerun()

        logs = stats.get("logs", [])
        last_run = logs[0].get("started_at", "Never")[:16] if logs else "Never"
        st.caption(f"Last refresh: {last_run}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Footer branding
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="bb-brand-footer">
            <div class="bb-brand-name">🔷 ByteBuilder</div>
            <div class="bb-brand-sub">AI &amp; Tech Insights Channel</div>
            <div style="margin-top:6px;">
                <div class="bb-brand-sub">👨‍💻 HMtechie &amp; ByteBuilder</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Card Renderers
# ─────────────────────────────────────────────────────────────────────────────

import re as _re


def _build_article_html(
    title, url, source, time_str,
    fresh_label, fresh_cls,
    category,
    sentiment, score_pct, score_col,
    body_display, tags_html,
) -> str:
    """
    Build the full article card HTML as a single string.
    All dynamic values are already HTML-escaped before being passed in.
    Badge HTML is constructed here — never in a variable that gets interpolated.
    """
    # Build badge fragments as local strings (not variables interpolated into outer f-string)
    freshness_span = (
        '<span class="bb-badge ' + fresh_cls + '">' + fresh_label + '</span>'
        if fresh_label else ''
    )
    category_span = (
        '<span class="bb-badge bb-badge-gray">' + category + '</span>'
        if category else ''
    )
    sent_map = {
        'positive': ('bb-badge-green', '🟢 Positive'),
        'negative': ('bb-badge-red',   '🔴 Negative'),
        'neutral':  ('bb-badge-gray',  '⚪ Neutral'),
    }
    s_cls, s_lbl = sent_map.get(sentiment, ('bb-badge-gray', '⚪ Neutral'))
    sentiment_span = '<span class="bb-badge ' + s_cls + '">' + s_lbl + '</span>'

    return (
        '<div class="bb-card">'
        '<div class="bb-card-title">'
        '<a href="' + url + '" target="_blank" rel="noopener">' + title + '</a>'
        '</div>'
        '<div class="bb-card-meta">'
        '<span>🌐 ' + source + '</span>'
        + ('<span>⏱ ' + time_str + '</span>' if time_str else '')
        + freshness_span
        + category_span
        + sentiment_span
        + '<div class="bb-score-bar-wrap">'
          '<div class="bb-score-bar-bg">'
          '<div class="bb-score-bar-fill" style="width:' + str(score_pct) + '%;background:' + score_col + ';"></div>'
          '</div>'
          '<span style="font-size:0.7rem;color:' + score_col + ';font-weight:600;">' + str(score_pct) + '%</span>'
          '</div>'
        '</div>'
        '<div class="bb-card-body">' + body_display + '</div>'
        + ('<div style="margin-bottom:8px;">' + tags_html + '</div>' if tags_html else '')
        + '<div class="bb-card-footer">'
          '<a href="' + url + '" target="_blank" rel="noopener" style="font-size:0.78rem;color:#58a6ff;">'
          '🔗 Read full article →</a>'
          '</div>'
        '</div>'
    )


def render_article_card(article: dict, idx: int):
    title    = _safe(article.get('title', 'Untitled'))
    url      = article.get('url', '#') or '#'
    source   = _safe(article.get('source', ''))
    category = _safe(article.get('category', ''))

    pub_ts   = article.get('published_at_ts') or article.get('published_at', '')
    time_str = _time_ago(pub_ts)
    fresh_label, fresh_cls = _freshness_label(pub_ts)

    body_raw   = article.get('summary') or article.get('raw_content') or ''
    body_clean = _re.sub(r'<[^>]+>', ' ', str(body_raw)).strip()
    body_display = _safe(body_clean[:300])

    trend_score = float(article.get('trend_score', 0) or 0)
    score_pct   = min(int(trend_score * 100), 100)
    score_col   = _score_color(trend_score)
    sentiment   = str(article.get('sentiment', 'neutral')).lower()
    tags_html   = _tags_html(article.get('tags', []))

    card_html = _build_article_html(
        title, url, source, time_str,
        fresh_label, fresh_cls,
        category, sentiment,
        score_pct, score_col,
        body_display, tags_html,
    )
    st.markdown(card_html, unsafe_allow_html=True)

    col1, _ = st.columns([1, 3])
    with col1:
        if st.button('➕ Add to Post Creator', key=f'add_art_{idx}', use_container_width=True):
            if _add_to_post_creator(article):
                st.success('Added!')
                st.rerun()
            else:
                st.info('Already added.')


def render_paper_card(paper: dict, idx: int):
    title      = _safe(paper.get('title', 'Untitled'))
    url        = paper.get('url', '#') or '#'
    pdf_url    = paper.get('pdf_url', url) or url
    github_url = paper.get('github_url', '') or ''
    source     = _safe(paper.get('source', 'arXiv'))
    authors    = _safe(str(paper.get('authors', ''))[:80])

    pub_ts      = paper.get('published_at_ts') or paper.get('published_at', '')
    time_str    = _time_ago(pub_ts)
    fresh_label, fresh_cls = _freshness_label(pub_ts)

    abstract_raw   = paper.get('abstract') or paper.get('summary') or paper.get('raw_content') or ''
    abstract_clean = _re.sub(r'<[^>]+>', ' ', str(abstract_raw)).strip()
    abstract_disp  = _safe(abstract_clean[:300])

    freshness_span = (
        '<span class="bb-badge ' + fresh_cls + '">' + fresh_label + '</span>'
        if fresh_label else ''
    )
    authors_span = ('<span>👥 ' + authors + '</span>') if authors else ''
    code_link    = (
        '<a href="' + github_url + '" target="_blank" rel="noopener" '
        'style="font-size:0.78rem;color:#58a6ff;">💻 Code</a>'
        if github_url else ''
    )

    card_html = (
        '<div class="bb-card">'
        '<div class="bb-card-title">'
        '<a href="' + url + '" target="_blank" rel="noopener">' + title + '</a>'
        '</div>'
        '<div class="bb-card-meta">'
        '<span>📚 ' + source + '</span>'
        + ('<span>⏱ ' + time_str + '</span>' if time_str else '')
        + freshness_span
        + authors_span
        + '</div>'
        '<div class="bb-card-body">' + abstract_disp + '</div>'
        '<div class="bb-card-footer">'
        '<a href="' + url + '" target="_blank" rel="noopener" style="font-size:0.78rem;color:#58a6ff;">🔗 Abstract</a>'
        '<a href="' + pdf_url + '" target="_blank" rel="noopener" style="font-size:0.78rem;color:#58a6ff;">📄 PDF</a>'
        + code_link
        + '</div>'
        '</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    col1, _ = st.columns([1, 3])
    with col1:
        if st.button('➕ Add to Post Creator', key=f'add_paper_{idx}', use_container_width=True):
            if _add_to_post_creator(paper):
                st.success('Added!')
                st.rerun()
            else:
                st.info('Already added.')


def render_repo_card(repo: dict, idx: int):
    name        = _safe(repo.get('name', ''))
    url         = repo.get('url', '#') or '#'
    desc_raw    = str(repo.get('description', ''))[:200]
    desc        = _safe(_re.sub(r'<[^>]+>', ' ', desc_raw).strip())
    lang        = _safe(repo.get('language', '') or 'Unknown')
    stars       = int(repo.get('stars', 0) or 0)
    today_stars = int(repo.get('today_stars', 0) or 0)
    tags_html   = _tags_html(repo.get('topics', []))

    card_html = (
        '<div class="bb-card">'
        '<div class="bb-card-title">'
        '<a href="' + url + '" target="_blank" rel="noopener">📦 ' + name + '</a>'
        '</div>'
        '<div class="bb-card-meta">'
        '<span>💻 ' + lang + '</span>'
        '<span>⭐ ' + f'{stars:,}' + '</span>'
        '<span class="bb-badge bb-badge-green">🔥 +' + str(today_stars) + ' today</span>'
        '</div>'
        '<div class="bb-card-body">' + desc + '</div>'
        + ('<div style="margin-bottom:8px;">' + tags_html + '</div>' if tags_html else '')
        + '<div class="bb-card-footer">'
          '<a href="' + url + '" target="_blank" rel="noopener" style="font-size:0.78rem;color:#58a6ff;">'
          '🔗 View on GitHub →</a>'
          '</div>'
        '</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    col1, _ = st.columns([1, 3])
    with col1:
        if st.button('➕ Add to Post Creator', key=f'add_repo_{idx}', use_container_width=True):
            if _add_to_post_creator(repo):
                st.success('Added!')
                st.rerun()
            else:
                st.info('Already added.')


# ─────────────────────────────────────────────────────────────────────────────
# Feed Panel
# ─────────────────────────────────────────────────────────────────────────────

def page_feed():
    n_selected = len(st.session_state.selected_for_post)

    col_title, col_badge = st.columns([5, 2])
    with col_title:
        st.markdown(
            '<div class="bb-section-title">📡 Trending News Feed</div>',
            unsafe_allow_html=True,
        )
    with col_badge:
        if n_selected > 0:
            st.markdown(
                f'<div style="text-align:right;padding-top:4px;">'
                f'<span class="bb-badge bb-badge-blue">✍️ {n_selected} item'
                f'{"s" if n_selected != 1 else ""} in Post Creator</span></div>',
                unsafe_allow_html=True,
            )
            if st.button("Go to Post Creator →", use_container_width=True, type="primary"):
                st.session_state.page = "creator"
                st.rerun()

    tab_news, tab_papers, tab_github = st.tabs([
        "📰 Latest News",
        "📄 Research Papers",
        "⭐ GitHub Trending",
    ])

    # ── News Tab ──────────────────────────────────────────────────────────────
    with tab_news:
        col_search, col_cat, col_sort = st.columns([3, 2, 2])
        with col_search:
            search = st.text_input(
                "Search", placeholder="🔍 Search articles…",
                label_visibility="collapsed", key="news_search",
            )
        with col_cat:
            # Build category list from DB
            try:
                from src.database import get_categories
                db_cats = get_categories()
            except Exception:
                db_cats = []
            cat_options = ["All"] + db_cats if db_cats else [
                "All", "AI Labs & Research", "Major Tech News",
                "Developer & Engineering", "Cybersecurity",
                "Startups & Business", "Research & Science",
            ]
            category = st.selectbox(
                "Category", cat_options,
                label_visibility="collapsed", key="news_cat",
            )
        with col_sort:
            sort_by = st.selectbox(
                "Sort", ["Latest", "Trending", "Relevance", "Freshness"],
                label_visibility="collapsed", key="news_sort",
            )

        articles = _get_articles(
            limit=50,
            search=search or None,
            category=None if category == "All" else category,
            sort_by=sort_by,
        )

        if not articles:
            st.info(
                "No articles yet. Click **▶ Refresh Feed** in the sidebar "
                "to fetch the latest news from 80+ global tech sources."
            )
        else:
            # Count how many are from last 24h
            cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            fresh_count = sum(
                1 for a in articles
                if _parse_dt(a.get("published_at_ts") or a.get("published_at", ""))
                and _parse_dt(a.get("published_at_ts") or a.get("published_at", "")) > cutoff_24h
            )
            st.caption(
                f"Showing {len(articles)} articles · "
                f"🟢 {fresh_count} from last 24h"
            )
            for i, article in enumerate(articles):
                render_article_card(article, i)

    # ── Papers Tab ────────────────────────────────────────────────────────────
    with tab_papers:
        col_ps, col_pfetch = st.columns([4, 2])
        with col_ps:
            paper_search = st.text_input(
                "Search papers", placeholder="🔍 Search papers…",
                label_visibility="collapsed", key="paper_search",
            )
        with col_pfetch:
            if st.button("🔄 Fetch Latest Papers", use_container_width=True, key="fetch_papers"):
                with st.spinner("Fetching from arXiv…"):
                    try:
                        from src.agents.research_paper_agent import run_research_paper_agent, store_papers
                        from src.agents.llm_summarizer_agent import batch_summarise_papers
                        result = run_research_paper_agent({})
                        papers_new = result.get("research_papers", [])
                        papers_new = batch_summarise_papers(papers_new)
                        stored = store_papers(papers_new)
                        st.success(f"✅ {len(papers_new)} fetched, {stored} new")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        papers = _get_papers(limit=40, search=paper_search or None)
        if not papers:
            st.info("No research papers yet. Click **Fetch Latest Papers** to load from arXiv.")
        else:
            st.caption(f"Showing {len(papers)} papers")
            for i, paper in enumerate(papers):
                render_paper_card(paper, i)

    # ── GitHub Tab ────────────────────────────────────────────────────────────
    with tab_github:
        repos = _get_repos(limit=30)
        if not repos:
            st.info("No repositories yet. Click **▶ Refresh Feed** in the sidebar.")
        else:
            repos_sorted = sorted(repos, key=lambda r: r.get("today_stars", 0), reverse=True)

            if len(repos_sorted) >= 3:
                st.markdown("#### 🏆 Top 3 Today")
                c1, c2, c3 = st.columns(3)
                for col, medal, repo in zip(
                    [c1, c2, c3], ["🥇", "🥈", "🥉"], repos_sorted[:3]
                ):
                    with col:
                        rname = _safe(repo.get("name", ""))
                        rurl  = repo.get("url", "#")
                        rstars = int(repo.get("today_stars", 0))
                        st.markdown(f"""
<div class="bb-stat" style="margin-bottom:12px;">
  <div style="font-size:1.5rem;">{medal}</div>
  <div style="color:#e6edf3;font-weight:600;font-size:0.85rem;margin:4px 0;">{rname}</div>
  <div class="bb-stat-num" style="font-size:1.4rem;color:#3fb950;">+{rstars}</div>
  <div class="bb-stat-label">stars today</div>
  <div style="margin-top:8px;">
    <a href="{rurl}" target="_blank" style="font-size:0.75rem;color:#58a6ff;">View →</a>
  </div>
</div>
""", unsafe_allow_html=True)
                st.markdown("---")

            st.caption(f"{len(repos_sorted)} trending repositories")
            for i, repo in enumerate(repos_sorted):
                render_repo_card(repo, i)


# ─────────────────────────────────────────────────────────────────────────────
# Post Creator Panel
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES = {
    "new_ai_tool": {
        "icon": "🚀",
        "name": "New AI Tool",
        "desc": "Tool name, what it does, why interesting, use cases, Try Here link",
    },
    "tech_update": {
        "icon": "🔥",
        "name": "Tech Update",
        "desc": "What it is, why it matters, key points, Read More link",
    },
    "ai_insight": {
        "icon": "🖥️",
        "name": "AI Insight",
        "desc": "Deep-dive: highlights, why it matters, future, source link",
    },
    "deep_dive": {
        "icon": "📖",
        "name": "Deep Dive",
        "desc": "Long-form conversational storytelling — like a knowledgeable friend explaining a topic. Best for viral educational posts with inline links.",
    },
    "weekly_digest": {
        "icon": "📅",
        "name": "Weekly Digest",
        "desc": "Full digest: news + AI updates + new tools + GitHub repo + trend",
    },
}


def page_creator():
    st.markdown(
        '<div class="bb-section-title">✍️ Post Creator</div>',
        unsafe_allow_html=True,
    )

    # ── Step 1: Choose Template ───────────────────────────────────────────────
    st.markdown("### Step 1 — Choose a Template")
    st.caption("Select the post format for your ByteBuilder channel.")

    cols = st.columns(5)
    for col, (tid, tmpl) in zip(cols, TEMPLATES.items()):
        with col:
            is_sel = st.session_state.creator_template == tid
            border = "#58a6ff" if is_sel else "#21262d"
            bg     = "#0c2340" if is_sel else "#161b22"
            st.markdown(f"""
<div class="bb-template-card" style="border-color:{border};background:{bg};">
  <div class="bb-template-icon">{tmpl['icon']}</div>
  <div class="bb-template-name">{_safe(tmpl['name'])}</div>
  <div class="bb-template-desc">{_safe(tmpl['desc'])}</div>
</div>
""", unsafe_allow_html=True)
            if st.button(
                f"Select {tmpl['icon']}",
                key=f"sel_tmpl_{tid}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state.creator_template = tid
                st.rerun()

    selected_tmpl = TEMPLATES[st.session_state.creator_template]
    st.markdown(f"""
<div style="margin:8px 0 16px;padding:10px 14px;background:#161b22;
            border-left:3px solid #58a6ff;border-radius:0 6px 6px 0;">
  <span style="color:#58a6ff;font-weight:600;">
    {selected_tmpl['icon']} {_safe(selected_tmpl['name'])}
  </span>
  <span style="color:#6e7681;font-size:0.82rem;margin-left:8px;">
    {_safe(selected_tmpl['desc'])}
  </span>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Step 2: Choose Content Source ─────────────────────────────────────────
    st.markdown("### Step 2 — Choose Content Source")

    n_saved = len(st.session_state.selected_for_post)
    source_options = [
        f"📌 Use Saved Items from Feed ({n_saved} saved)",
        "🔬 Custom Topic / URL / arXiv ID",
    ]
    if st.session_state.creator_template == "weekly_digest":
        source_options.append("🚀 Auto-compile Weekly Digest")

    source_choice = st.radio(
        "Content source",
        source_options,
        label_visibility="collapsed",
        key="source_radio",
    )

    st.markdown("---")

    # ── Step 3: Configure & Generate ──────────────────────────────────────────
    st.markdown("### Step 3 — Configure & Generate")

    # ── Source A: Saved items ─────────────────────────────────────────────────
    if "Saved Items" in source_choice:
        if n_saved == 0:
            st.info(
                "No items saved yet. Go to the **📡 Trending News Feed** and click "
                "**➕ Add to Post Creator** on any article, paper, or repo."
            )
            if st.button("← Go to Feed", type="primary"):
                st.session_state.page = "feed"
                st.rerun()
        else:
            st.markdown(f"**{n_saved} item(s) saved from the feed:**")
            items_to_remove = []
            for i, item in enumerate(st.session_state.selected_for_post):
                col_t, col_r = st.columns([5, 1])
                with col_t:
                    item_url   = item.get("url", "#")
                    item_title = _safe(item.get("title", "Untitled")[:70])
                    item_src   = _safe(item.get("source", ""))
                    st.markdown(
                        f'<div style="padding:6px 0;color:#e6edf3;font-size:0.85rem;">'
                        f'<a href="{item_url}" target="_blank" style="color:#58a6ff;">'
                        f'{item_title}</a>'
                        f'<span style="color:#6e7681;font-size:0.75rem;margin-left:8px;">'
                        f'{item_src}</span></div>',
                        unsafe_allow_html=True,
                    )
                with col_r:
                    if st.button("✕", key=f"rm_{i}", help="Remove"):
                        items_to_remove.append(i)

            if items_to_remove:
                for idx in sorted(items_to_remove, reverse=True):
                    st.session_state.selected_for_post.pop(idx)
                st.rerun()

            if st.session_state.creator_template != "weekly_digest":
                titles = [
                    f"{i+1}. {item.get('title', 'Untitled')[:65]}"
                    for i, item in enumerate(st.session_state.selected_for_post)
                ]
                selected_idx = st.selectbox(
                    "Select item to use for this post",
                    range(len(titles)),
                    format_func=lambda i: titles[i],
                    key="saved_item_select",
                )
                selected_item = st.session_state.selected_for_post[selected_idx]

                # Preview
                preview_body = _safe(str(
                    selected_item.get("abstract")
                    or selected_item.get("summary")
                    or selected_item.get("raw_content", "")
                )[:200])
                preview_url   = selected_item.get("url", "#")
                preview_title = _safe(selected_item.get("title", ""))
                preview_src   = _safe(selected_item.get("source", ""))
                st.markdown(f"""
<div class="bb-card" style="margin-top:8px;">
  <div class="bb-card-title">
    <a href="{preview_url}" target="_blank">{preview_title}</a>
  </div>
  <div class="bb-card-meta"><span>🌐 {preview_src}</span></div>
  <div class="bb-card-body">{preview_body}</div>
  <div class="bb-card-footer">
    <a href="{preview_url}" target="_blank" style="font-size:0.78rem;color:#58a6ff;">
      🔗 Source →
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

                if st.button(
                    f"🚀 Generate {selected_tmpl['icon']} {selected_tmpl['name']} Post",
                    type="primary",
                    key="gen_saved",
                    use_container_width=True,
                ):
                    with st.spinner(f"Generating {selected_tmpl['name']} post…"):
                        post = _generate_post(selected_item, st.session_state.creator_template)
                    st.session_state.generated_post = post
                    st.session_state.post_references = [{
                        "title": selected_item.get("title", ""),
                        "url":   selected_item.get("url", ""),
                    }]
                    st.rerun()
            else:
                if st.button(
                    "🚀 Generate Weekly Digest Post",
                    type="primary", key="gen_weekly_saved", use_container_width=True,
                ):
                    with st.spinner("Compiling weekly digest…"):
                        saved = st.session_state.selected_for_post
                        arts  = [i for i in saved if "abstract" not in i]
                        paps  = [i for i in saved if "abstract" in i]
                        repos = _get_repos(limit=1)
                        post  = _generate_weekly_post(
                            arts or _get_articles(limit=5),
                            paps or _get_papers(limit=3),
                            repos,
                        )
                    st.session_state.generated_post = post
                    st.session_state.post_references = [
                        {"title": i.get("title", ""), "url": i.get("url", "")}
                        for i in saved
                    ]
                    st.rerun()

    # ── Source B: Custom Topic ────────────────────────────────────────────────
    elif "Custom Topic" in source_choice:
        st.markdown(
            '<div style="color:#8b949e;font-size:0.85rem;margin-bottom:12px;">'
            'Enter a <strong>topic keyword</strong>, <strong>URL</strong>, or '
            '<strong>arXiv ID</strong>. The agent gathers real-time sources and '
            'generates a post with all reference links included.'
            '</div>',
            unsafe_allow_html=True,
        )
        user_input = st.text_input(
            "Topic / URL / arXiv ID",
            placeholder="e.g.  'LLM fine-tuning'  ·  'https://...'  ·  '2401.12345'",
            key="custom_topic_input",
        )
        extra_context = st.text_area(
            "Extra instructions (optional)",
            placeholder="e.g. 'Focus on enterprise use cases' · 'Keep it beginner-friendly'",
            height=70,
            key="custom_extra",
        )
        if st.button(
            f"🚀 Research & Generate {selected_tmpl['icon']} {selected_tmpl['name']} Post",
            type="primary",
            key="gen_custom",
            use_container_width=True,
            disabled=not (user_input or "").strip(),
        ):
            with st.spinner(f"Researching '{user_input}' and generating post…"):
                result = _generate_realtime_post(
                    user_input,
                    st.session_state.creator_template,
                    extra_context,
                )
            st.session_state.generated_post = result.get("post", "")
            st.session_state.post_references = result.get("references", [])
            st.session_state.post_meta = {
                "sources_used": result.get("sources_used", 0),
                "elapsed":      result.get("elapsed", 0),
            }
            st.rerun()

    # ── Source C: Auto Weekly Digest ──────────────────────────────────────────
    elif "Auto-compile" in source_choice:
        st.markdown(
            '<div style="color:#8b949e;font-size:0.85rem;margin-bottom:12px;">'
            'Automatically compiles the top articles, research papers, and trending '
            'GitHub repo into a complete <strong>Weekly Tech &amp; AI Digest</strong>.'
            '</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            n_news     = st.number_input("Top news articles",    1, 5, 3, key="wk_n_news")
            n_research = st.number_input("Research highlights",  1, 5, 2, key="wk_n_research")
        with c2:
            week_label = st.text_input(
                "Week label",
                value=datetime.now().strftime("%B %d, %Y — Week %W"),
                key="wk_label",
            )

        if st.button(
            "🚀 Generate Weekly Digest",
            type="primary", key="gen_weekly_auto", use_container_width=True,
        ):
            with st.spinner("Compiling weekly digest…"):
                arts  = _get_articles(limit=int(n_news))
                paps  = _get_papers(limit=int(n_research))
                repos = _get_repos(limit=1)
                post  = _generate_weekly_post(arts, paps, repos)
            st.session_state.generated_post = post
            st.session_state.post_references = []
            st.rerun()

    # ── Step 4: Display Generated Post ────────────────────────────────────────
    if st.session_state.generated_post:
        st.markdown("---")
        st.markdown("### Step 4 — Your Generated Post")

        meta = st.session_state.get("post_meta", {})
        if meta:
            st.markdown(
                f'<div style="color:#6e7681;font-size:0.78rem;margin-bottom:10px;">'
                f'✅ Generated in {meta.get("elapsed", 0):.1f}s '
                f'using {meta.get("sources_used", 0)} sources</div>',
                unsafe_allow_html=True,
            )

        st.text_area(
            "📋 Copy your post below",
            value=st.session_state.generated_post,
            height=420,
            key="final_post_ta",
        )

        refs = st.session_state.post_references
        if refs:
            st.markdown("**📚 References & Source Links:**")
            for ref in refs:
                ref_title = _safe(ref.get("title", ref.get("url", ""))[:80])
                ref_url   = ref.get("url", "#")
                if ref_url and ref_url != "#":
                    st.markdown(
                        f'<a href="{ref_url}" target="_blank" '
                        f'style="font-size:0.82rem;color:#58a6ff;display:block;margin-bottom:4px;">'
                        f'🔗 {ref_title}</a>',
                        unsafe_allow_html=True,
                    )

        col_regen, col_clear, _ = st.columns([1, 1, 2])
        with col_regen:
            if st.button("🔄 Regenerate", key="regen_post"):
                st.session_state.generated_post = None
                st.session_state.post_meta = {}
                st.rerun()
        with col_clear:
            if st.button("🗑️ Clear Post", key="clear_post"):
                st.session_state.generated_post = None
                st.session_state.post_references = []
                st.session_state.post_meta = {}
                st.rerun()

        st.markdown("""
<div style="margin-top:12px;padding:10px 14px;background:#161b22;
            border:1px solid #21262d;border-radius:8px;font-size:0.8rem;color:#6e7681;">
  🔔 Post includes <strong style="color:#58a6ff;">Follow ByteBuilder</strong> footer automatically.
  Ready to share on your channel!
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main Router
# ─────────────────────────────────────────────────────────────────────────────

def main():
    render_sidebar()
    page = st.session_state.get("page", "feed")
    if page == "creator":
        page_creator()
    else:
        page_feed()


if __name__ == "__main__":
    main()