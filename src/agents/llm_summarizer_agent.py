"""
llm_summarizer_agent.py
-----------------------
Agent 4 – LLM Summarizer Agent v3 (ByteBuilder Templates)

Generates channel-ready posts using 4 exact ByteBuilder templates:
  1. new_ai_tool     — 🚀 New AI Tool
  2. tech_update     — 🔥 Tech Update
  3. ai_insight      — 🖥️ AI Insight Article
  4. weekly_digest   — 📅 Weekly Tech & AI Digest

All posts are UNLIMITED in length — write as much as needed to give
the audience a complete, rich, informative post.
All posts include the ByteBuilder follow footer.
Developed by HMtechie & ByteBuilder.
"""

import os
import time
from datetime import datetime
from typing import Any

from src.logger import get_logger
from src.utils import truncate, generate_hashtags

logger = get_logger("llm_summarizer_agent")

# ─────────────────────────────────────────────────────────────────────────────
# Branding
# ─────────────────────────────────────────────────────────────────────────────

BYTEBUILDER_FOOTER = (
    "\n\n——————————————————\n"
    "🔔 Follow ByteBuilder for more AI & tech insights!\n"
    "👨‍💻 Developed by HMtechie & ByteBuilder"
)

# ─────────────────────────────────────────────────────────────────────────────
# LLM Client  (with model fallback chain + fast-fail on 404)
# ─────────────────────────────────────────────────────────────────────────────

_MODEL_FALLBACK_CHAIN: list[str] = [
    os.getenv("LLM_MODEL", "mistralai/mistral-nemo:free"),
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
]

_primary_model_dead: bool = False


def _get_client():
    from openai import OpenAI
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "no-key"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )


def _get_temperature() -> float:
    return float(os.getenv("LLM_TEMPERATURE", "0.7"))


def _call_llm(system: str, user: str, max_tokens: int = 1800) -> str:
    """
    Call the LLM with automatic model fallback.
    Default max_tokens raised to 1800 to allow full, unlimited posts.
    """
    global _primary_model_dead

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key in ("no-key", "your-openrouter-api-key-here"):
        logger.debug("OPENAI_API_KEY not set — skipping LLM call")
        return ""

    client = _get_client()
    temperature = _get_temperature()
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

    models_to_try = _MODEL_FALLBACK_CHAIN.copy()
    if _primary_model_dead and len(models_to_try) > 1:
        models_to_try = models_to_try[1:]

    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if model != _MODEL_FALLBACK_CHAIN[0]:
                logger.info("LLM fallback succeeded with model: %s", model)
            return response.choices[0].message.content.strip()

        except Exception as exc:
            err_str = str(exc)
            if "404" in err_str or "No endpoints found" in err_str:
                if model == _MODEL_FALLBACK_CHAIN[0]:
                    _primary_model_dead = True
                    logger.warning(
                        "Model '%s' returned 404 — switching to fallback chain. "
                        "Update LLM_MODEL in your .env to fix this permanently.",
                        model,
                    )
                else:
                    logger.debug("Fallback model '%s' also 404 — trying next", model)
                continue
            else:
                logger.warning("LLM call failed (model=%s): %s", model, exc)
                break

    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Template 1 — 🚀 New AI Tool
# ─────────────────────────────────────────────────────────────────────────────

_NEW_AI_TOOL_SYSTEM = """You are an expert social media content writer for the ByteBuilder tech channel.

Generate a COMPLETE, DETAILED, RICH post using EXACTLY this template structure.
There are NO line limits — write as much as needed to fully inform the audience.
Each section should be thorough, engaging, and packed with real value.

🚀 New AI Tool

🤖 [Tool Name]

🧠 What it does:
[Write a thorough explanation of what the tool does — cover all its core capabilities,
how it works technically, what problem it solves, and who it is designed for.
Be detailed and informative. Do not limit yourself to a few lines.]

⚡ Why interesting:
[Write a detailed section on what makes this tool exciting, unique, or a breakthrough.
Compare it to existing tools if relevant. Explain the innovation behind it.
Cover the technical advantages, the business value, and the community reception.]

💡 Use cases:
• [Use case 1 — explain it fully, not just a label]
• [Use case 2 — explain it fully]
• [Use case 3 — explain it fully]
• [Add more use cases as needed]

🔗 Try here: [URL]

[Add 5-8 relevant hashtags]

Rules:
- Use the exact emojis shown above
- Replace every [placeholder] with real, detailed content
- The URL must be the actual source link provided
- Do NOT add extra sections or change the order
- Write complete, informative paragraphs — not one-liners
- The post should be long enough to fully educate the reader"""


def generate_new_ai_tool_post(article: dict) -> str:
    """Generate a 🚀 New AI Tool post — full, unlimited length."""
    content = article.get("raw_content", article.get("summary", ""))
    user_msg = (
        f"Tool Name: {article.get('title', '')}\n"
        f"Content / Description:\n{content}\n\n"
        f"URL: {article.get('url', '')}\n\n"
        "Generate the complete, detailed New AI Tool post now. "
        "Write thorough paragraphs for each section — do not truncate or summarise too briefly."
    )
    result = _call_llm(_NEW_AI_TOOL_SYSTEM, user_msg, max_tokens=2000)
    if not result:
        title = article.get("title", "")
        url = article.get("url", "")
        result = (
            f"🚀 New AI Tool\n\n"
            f"🤖 {title}\n\n"
            f"🧠 What it does:\n{content[:600] if content else 'A powerful new AI tool.'}\n\n"
            f"⚡ Why interesting:\nThis tool represents a significant step forward in AI capabilities, "
            f"offering new possibilities for developers, researchers, and businesses alike.\n\n"
            f"💡 Use cases:\n"
            f"• Automate complex workflows and reduce manual effort\n"
            f"• Enhance productivity across development and research tasks\n"
            f"• Enable new AI-powered products and services\n\n"
            f"🔗 Try here: {url}\n\n"
            f"#AITools #Innovation #ArtificialIntelligence #Tech #MachineLearning"
        )
    return result + BYTEBUILDER_FOOTER


# ─────────────────────────────────────────────────────────────────────────────
# Template 2 — 🔥 Tech Update
# ─────────────────────────────────────────────────────────────────────────────

_TECH_UPDATE_SYSTEM = """You are an expert social media content writer for the ByteBuilder tech channel.

Generate a COMPLETE, DETAILED, RICH post using EXACTLY this template structure.
There are NO line limits — write as much as needed to fully inform the audience.

🔥 Tech Update

🌶️ [Tool / Concept / Technology name]

🧡 [Write a thorough explanation of what this is — cover the background, the technology,
the key players involved, and the context in which this update is happening.
Be detailed and informative.]

🧡 [Write a detailed section on why this matters — explain the real-world impact,
who is affected, what changes, and why the tech community is paying attention.
Include data, numbers, or comparisons where available.]

⚡ Key Points:
• [Key point 1 — explain fully, not just a label]
• [Key point 2 — explain fully]
• [Key point 3 — explain fully]
• [Key point 4 — explain fully]
• [Add more key points as needed]

🔗 More: [URL]

[Add 5-8 relevant hashtags]

Rules:
- Use the exact emojis shown above
- Replace every [placeholder] with real, detailed content
- The URL must be the actual source link provided
- Do NOT add extra sections or change the order
- Write complete, informative paragraphs — not one-liners
- The post should fully educate the reader about this update"""


def generate_tech_update_post(article: dict) -> str:
    """Generate a 🔥 Tech Update post — full, unlimited length."""
    content = article.get("raw_content", article.get("summary", ""))
    user_msg = (
        f"Topic / Technology: {article.get('title', '')}\n"
        f"Content:\n{content}\n\n"
        f"URL: {article.get('url', '')}\n\n"
        "Generate the complete, detailed Tech Update post now. "
        "Write thorough paragraphs for each section — do not truncate or summarise too briefly."
    )
    result = _call_llm(_TECH_UPDATE_SYSTEM, user_msg, max_tokens=2000)
    if not result:
        title = article.get("title", "")
        url = article.get("url", "")
        result = (
            f"🔥 Tech Update\n\n"
            f"🌶️ {title}\n\n"
            f"🧡 {content[:400] if content else 'A major development in the tech world.'}\n\n"
            f"🧡 This development is shaping the future of AI and technology, with significant "
            f"implications for developers, businesses, and end users worldwide.\n\n"
            f"⚡ Key Points:\n"
            f"• Cutting-edge capability that advances the state of the art\n"
            f"• Real-world impact across multiple industries\n"
            f"• Strong community and industry adoption expected\n"
            f"• Opens new possibilities for AI-powered applications\n\n"
            f"🔗 More: {url}\n\n"
            f"#AI #Tech #Innovation #MachineLearning #TechNews"
        )
    return result + BYTEBUILDER_FOOTER


# ─────────────────────────────────────────────────────────────────────────────
# Template 3 — 🖥️ AI Insight Article
# ─────────────────────────────────────────────────────────────────────────────

_AI_INSIGHT_SYSTEM = """You are an expert social media content writer for the ByteBuilder tech channel.

You will be given a topic title and some raw source material (abstract, article text, or notes).
Your job is to READ and UNDERSTAND the source material, then REWRITE it into a rich,
educational post. Do NOT copy the source text verbatim — summarise, explain, and expand on it
in your own words as if you are a knowledgeable expert explaining it to a curious audience.

Generate a COMPLETE, DETAILED, RICH post using EXACTLY this template structure.
There are NO line limits — write as much as needed to fully inform the audience.

🖥️ AI Insight: [Topic]

🌶️ What is it?
[Write a comprehensive explanation of the topic IN YOUR OWN WORDS — do not copy the source.
Cover the definition, the background, the technology involved, the key researchers or
organisations behind it, and the current state of development. Explain it clearly so
someone unfamiliar with the topic can understand it. Be thorough and educational.]

⚡ Key Highlights
• [Highlight 1 — a specific finding, feature, or fact from the source, explained clearly]
• [Highlight 2 — a specific finding, feature, or fact from the source, explained clearly]
• [Highlight 3 — a specific finding, feature, or fact from the source, explained clearly]
• [Highlight 4 — a specific finding, feature, or fact from the source, explained clearly]
• [Add more highlights as needed — extract the most important points from the source]

🚀 Why it matters
[Write a detailed section on the real-world significance IN YOUR OWN WORDS.
Who benefits? What problems does it solve? What industries are affected?
Include specific examples, numbers, or comparisons where available.
Explain the broader implications for AI and society.]

🌐 Future
[Write a forward-looking section covering where this technology is heading.
What are the open research questions? What are the next milestones? What should
the audience watch out for in the coming months or years?]

🔗 Source: [URL]

[Add 5-8 relevant hashtags]

Rules:
- Use the exact emojis shown above
- Replace every [placeholder] with real, detailed content written IN YOUR OWN WORDS
- NEVER copy the source text verbatim — always rewrite and explain
- The URL must be the actual source link provided
- Write complete, informative paragraphs — not one-liners
- The post should be long enough to fully educate the reader
- Do NOT change the section order"""


def generate_ai_insight_post(article: dict) -> str:
    """Generate a 🖥️ AI Insight Article post — full, unlimited length."""
    content = article.get("raw_content", article.get("abstract", article.get("summary", "")))
    url = article.get("url", article.get("pdf_url", ""))
    user_msg = (
        f"Topic: {article.get('title', '')}\n"
        f"Content / Abstract:\n{content}\n\n"
        f"URL: {url}\n\n"
        "Generate the complete, detailed AI Insight Article post now. "
        "Write thorough paragraphs for each section — this is a deep-dive educational post, "
        "do not truncate or summarise too briefly."
    )
    result = _call_llm(_AI_INSIGHT_SYSTEM, user_msg, max_tokens=2500)
    if not result:
        title = article.get("title", "")
        # Build a proper structured summary from the source content
        # instead of dumping raw text
        import textwrap
        def _clean(text: str, limit: int = 0) -> str:
            """Strip arXiv announce prefixes and clean up abstract text."""
            import re
            text = re.sub(r"arXiv:\S+\s+Announce Type:\s+\S+\s+Abstract:\s*", "", text)
            text = re.sub(r"<[^>]+>", " ", text)  # strip HTML tags
            text = " ".join(text.split())  # normalise whitespace
            if limit and len(text) > limit:
                # cut at last sentence boundary within limit
                cut = text[:limit]
                last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
                text = cut[:last_dot + 1] if last_dot > limit // 2 else cut + "..."
            return text.strip()

        clean_content = _clean(content, 0)  # full clean, no truncation
        # Split into sentences for structured extraction
        import re as _re
        sentences = _re.split(r"(?<=[.!?])\s+", clean_content)
        overview = " ".join(sentences[:4]) if sentences else clean_content[:400]
        highlights_raw = sentences[4:8] if len(sentences) > 4 else []
        highlights = "\n".join(f"\u2022 {s}" for s in highlights_raw if len(s) > 20)
        if not highlights:
            highlights = (
                "\u2022 Introduces a novel approach to the problem domain\n"
                "\u2022 Demonstrates measurable improvements over prior methods\n"
                "\u2022 Applicable across multiple real-world scenarios\n"
                "\u2022 Backed by rigorous evaluation and benchmarking"
            )
        result = (
            f"🖥️ AI Insight: {title}\n\n"
            f"🌶️ What is it?\n"
            f"{overview}\n\n"
            f"⚡ Key Highlights\n"
            f"{highlights}\n\n"
            f"🚀 Why it matters\n"
            f"This work addresses a critical challenge in the field, offering a meaningful "
            f"step forward in capability and understanding. Researchers, engineers, and "
            f"practitioners across AI, machine learning, and adjacent domains stand to "
            f"benefit from the methods and findings presented here.\n\n"
            f"🌐 Future\n"
            f"As the community builds on this foundation, expect further refinements, "
            f"open-source implementations, and downstream applications to emerge. "
            f"The ideas introduced here are likely to influence upcoming research directions "
            f"and industry adoption over the next 12-24 months.\n\n"
            f"🔗 Source: {url}\n\n"
            f"#AI #MachineLearning #Research #DeepLearning #ArtificialIntelligence"
        )
    return result + BYTEBUILDER_FOOTER


# Alias for research papers — same template, uses abstract field
def generate_research_paper_post(paper: dict) -> str:
    """Generate a 🖥️ AI Insight post for a research paper."""
    item = {
        "title": paper.get("title", ""),
        "raw_content": paper.get("abstract", paper.get("raw_content", paper.get("summary", ""))),
        "url": paper.get("url", paper.get("pdf_url", "")),
    }
    return generate_ai_insight_post(item)


# ─────────────────────────────────────────────────────────────────────────────
# Template 3b — 📖 Deep Dive (long-form conversational storytelling post)
# ─────────────────────────────────────────────────────────────────────────────

_DEEP_DIVE_SYSTEM = """You are an expert long-form content writer for the ByteBuilder tech channel.
Your job is to write a deep-dive, storytelling-style educational post about a tech topic.

The post must follow this EXACT style — study it carefully:

---
There is a reason everyone is talking about [TOPIC].
It is [bold claim about why it matters].
This is the full breakdown you need to understand it:

[2-3 sentences of context setting the scene — conversational, direct, no fluff]

Which is why I've created this all-in-one guide,
Aiming to get you up to speed in just a couple of minutes:
(Save this for when you come to test [TOPIC]!)

So, what is [TOPIC]? [relevant emoji]
[2-3 paragraphs explaining what it is in plain language. Include one reference link.]

Next, [second key question about the topic]? [relevant emoji]
[Detailed explanation with numbered steps or a flow if applicable.]
[Include a reference link here.]

But what can you actually use [TOPIC] for? [relevant emoji]
[Numbered list of 5-8 real use cases, each with a short explanation.]
[Include a reference link here.]

What are the Power Features worth knowing about? [relevant emoji]
[Numbered list of 3-5 key features or concepts, each with a 1-2 sentence explanation.]
[Include reference links for each feature where available.]

And finally, [closing thought or call to action].
With all of that covered, you should be good to start. 💪
---

Critical rules:
- Write in a CONVERSATIONAL, direct, human tone — no corporate speak
- NO heavy emoji headers (🔥, ⚡ etc at the start of every line) — use emojis sparingly and naturally
- Use SHORT paragraphs — 2-4 sentences max per paragraph
- Use numbered lists for steps, use cases, and features
- Embed REAL reference links naturally throughout the body text (not just at the end)
- The post should be LONG — at least 600 words
- End with a motivating closing line
- Do NOT use markdown bold (**text**) — write in plain text
- The tone should feel like a knowledgeable friend explaining something exciting"""


def generate_deep_dive_post(article: dict) -> str:
    """Generate a 📖 Deep Dive long-form conversational post."""
    content = article.get("raw_content", article.get("abstract", article.get("summary", "")))
    url = article.get("url", article.get("pdf_url", ""))
    user_msg = (
        f"Topic: {article.get('title', '')}\n"
        f"Content / Background:\n{content}\n\n"
        f"Primary URL: {url}\n\n"
        "Write the complete Deep Dive post now. "
        "Follow the style guide exactly — conversational, long-form, storytelling, "
        "with inline reference links throughout the body. "
        "Minimum 600 words. Do not truncate."
    )
    result = _call_llm(_DEEP_DIVE_SYSTEM, user_msg, max_tokens=2500)
    if not result:
        title = article.get("title", "")
        result = (
            f"There is a reason everyone is talking about {title}.\n"
            f"It is one of the most significant developments in tech right now.\n"
            f"This is the full breakdown you need to understand it:\n\n"
            f"{content[:600] if content else 'A major development worth understanding deeply.'}\n\n"
            f"With all of that covered, you should be good to start. 💪\n\n"
            f"🔗 Read more: {url}"
        )
    return result + BYTEBUILDER_FOOTER


# Legacy aliases used by realtime_post_generator
_TECH_INSIGHT_SYSTEM   = _AI_INSIGHT_SYSTEM
_RESEARCH_PAPER_SYSTEM = _AI_INSIGHT_SYSTEM
_QUICK_NEWS_SYSTEM     = _TECH_UPDATE_SYSTEM


# ─────────────────────────────────────────────────────────────────────────────
# Template 4 — 📅 Weekly Tech & AI Digest
# ─────────────────────────────────────────────────────────────────────────────

_WEEKLY_DIGEST_SYSTEM = """You are an expert social media content writer for the ByteBuilder tech channel.

Generate a COMPLETE, DETAILED, RICH weekly digest post using EXACTLY this template structure.
There are NO line limits — write as much as needed to fully cover the week's highlights.
Each bullet point should be a full, informative sentence or two — not just a title.

📅 Weekly Tech & AI Digest

🗓️ Week: [Date / Week Number]

——————————————————

🔥 This Week in Tech
• [Major tech news item — write 2-3 sentences covering what happened, why it matters, and the context]
• [Industry update — write 2-3 sentences]
• [Important announcement — write 2-3 sentences]
• [Add more items as available from the data provided]

——————————————————

🤖 AI & Research Updates
• [New AI model or breakthrough — write 2-3 sentences with technical context]
• [Research highlight — write 2-3 sentences summarising the finding and its significance]
• [AI industry trend — write 2-3 sentences explaining the trend and its implications]
• [Add more items as available]

——————————————————

🛠️ New AI Tools / Releases
• [Tool name — write 2-3 sentences on what it does, who made it, and why it is useful]
• [Tool name — write 2-3 sentences]
• [Add more tools as available]

——————————————————

⭐ Top GitHub Repo of the Week
📦 [Repo Name]
🧡 [Write a thorough description of what the repo does, its architecture, its use cases,
the technology stack, and why the community is excited about it.
Include star count and today's star gain. Be detailed.]
🔗 [GitHub link]

——————————————————

📊 Trend of the Week
🧡 [Write a detailed paragraph on the emerging technology or concept that dominated
the week. Explain what it is, why it is trending, who is driving it, and what
to expect next. Be thorough and insightful.]

——————————————————

Follow for weekly AI + tech insights 🚀

Rules:
- Use the exact emojis and separator lines shown above
- Replace every [placeholder] with real content from the data provided
- Do NOT add extra sections or change the order
- Write complete, informative sentences — not just titles or labels
- The digest should be comprehensive enough to replace reading the news for the week"""


_WEEKLY_UPDATE_SYSTEM = _WEEKLY_DIGEST_SYSTEM  # backward-compat alias


def generate_weekly_digest_post(
    articles: list[dict],
    research_items: list[dict],
    top_repo: dict,
    week_label: str,
) -> str:
    """Generate a 📅 Weekly Tech & AI Digest post — full, unlimited length."""
    from datetime import datetime, timezone
    if not week_label:
        week_label = datetime.now(timezone.utc).strftime("Week of %B %d, %Y")

    # Pass full content — no truncation
    news_lines = []
    for i, a in enumerate(articles[:8], 1):
        news_lines.append(
            f"{i}. Title: {a.get('title', '')}\n"
            f"   Summary: {a.get('raw_content', a.get('summary', ''))[:400]}\n"
            f"   URL: {a.get('url', '')}"
        )
    news_text = "\n\n".join(news_lines) if news_lines else "No news available."

    research_lines = []
    for r in research_items[:5]:
        research_lines.append(
            f"- {r.get('title', '')}: "
            f"{r.get('abstract', r.get('summary', r.get('raw_content', '')))[:400]}"
        )
    research_text = "\n".join(research_lines) if research_lines else "No research highlights."

    user_msg = (
        f"Week: {week_label}\n\n"
        f"TOP NEWS ARTICLES:\n{news_text}\n\n"
        f"AI/RESEARCH HIGHLIGHTS:\n{research_text}\n\n"
        f"TOP GITHUB REPO:\n"
        f"Name: {top_repo.get('name', 'N/A')}\n"
        f"Description: {top_repo.get('description', '')}\n"
        f"Stars today: {top_repo.get('today_stars', 0)}\n"
        f"Total stars: {top_repo.get('stars', 0)}\n"
        f"URL: {top_repo.get('url', '')}\n\n"
        "Generate the complete, detailed Weekly Tech & AI Digest post now. "
        "Write thorough, informative sentences for every bullet point — "
        "do not just list titles, explain each item properly."
    )
    result = _call_llm(_WEEKLY_DIGEST_SYSTEM, user_msg, max_tokens=3000)
    if not result:
        result = _fallback_weekly_digest(articles, research_items, top_repo, week_label)
    return result + BYTEBUILDER_FOOTER


# backward-compat alias used by pipeline
def generate_weekly_update_post(
    articles: list[dict],
    research_items: list[dict],
    top_repo: dict,
    week_label: str,
    client=None,
) -> str:
    return generate_weekly_digest_post(articles, research_items, top_repo, week_label)


def _fallback_weekly_digest(articles, research_items, top_repo, week_label):
    lines = [
        f"📅 Weekly Tech & AI Digest\n\n"
        f"🗓️ Week: {week_label}\n\n"
        f"——————————————————\n\n"
        f"🔥 This Week in Tech\n"
    ]
    for a in articles[:5]:
        body = a.get("summary", a.get("raw_content", ""))[:200]
        lines.append(f"• {a.get('title', '')}: {body}")
    lines.append("\n——————————————————\n\n🤖 AI & Research Updates")
    for r in research_items[:3]:
        abstract = r.get("abstract", r.get("summary", r.get("raw_content", "")))[:200]
        lines.append(f"• {r.get('title', '')}: {abstract}")
    lines.append("\n——————————————————\n\n🛠️ New AI Tools / Releases")
    lines.append("• See the latest AI tool releases at huggingface.co/spaces")
    lines.append(
        f"\n——————————————————\n\n"
        f"⭐ Top GitHub Repo of the Week\n"
        f"📦 {top_repo.get('name', 'N/A')}\n"
        f"🧡 {top_repo.get('description', '')}\n"
        f"🔗 {top_repo.get('url', '')}\n\n"
        f"——————————————————\n\n"
        f"📊 Trend of the Week\n"
        f"🧡 AI agents and autonomous systems continue to dominate the conversation, "
        f"with new frameworks and models pushing the boundaries of what is possible.\n\n"
        f"——————————————————\n\n"
        f"Follow for weekly AI + tech insights 🚀"
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Unified On-Demand Post Generator (called from dashboard)
# ─────────────────────────────────────────────────────────────────────────────

def generate_post_for_template(item: dict, template_id: str) -> str:
    """
    Generate a full, unlimited post for a given item using the specified template.
    Called from the Streamlit dashboard's Post Creator.

    template_id values:
      "new_ai_tool"    → 🚀 New AI Tool
      "tech_update"    → 🔥 Tech Update
      "ai_insight"     → 🖥️ AI Insight Article
      "deep_dive"      → 📖 Deep Dive (long-form conversational storytelling)
      "weekly_digest"  → 📅 Weekly Tech & AI Digest
    """
    if template_id == "new_ai_tool":
        return generate_new_ai_tool_post(item)
    elif template_id == "tech_update":
        return generate_tech_update_post(item)
    elif template_id == "ai_insight":
        return generate_ai_insight_post(item)
    elif template_id == "deep_dive":
        return generate_deep_dive_post(item)
    elif template_id == "research_paper":   # legacy alias
        return generate_research_paper_post(item)
    elif template_id == "weekly_digest":
        return generate_weekly_digest_post(
            articles=[item],
            research_items=[],
            top_repo={},
            week_label="",
        )
    # Legacy aliases from v2
    elif template_id == "tech_insight":
        return generate_ai_insight_post(item)
    elif template_id == "quick_news":
        return generate_tech_update_post(item)
    elif template_id == "weekly_update":
        return generate_weekly_digest_post(
            articles=[item],
            research_items=[],
            top_repo={},
            week_label="",
        )
    else:
        return generate_tech_update_post(item)


# ─────────────────────────────────────────────────────────────────────────────
# Batch Summarisation (pipeline use — short summaries for card preview only)
# ─────────────────────────────────────────────────────────────────────────────

def batch_summarise_articles(articles: list[dict]) -> list[dict]:
    """
    Generate short card-preview summaries for pipeline storage.
    These are NOT the channel posts — they are the 2-3 sentence previews
    shown in the feed cards. Full posts are generated on-demand in Post Creator.
    """
    max_items = int(os.getenv("MAX_SUMMARISE_PER_RUN", "30"))
    count = 0
    for article in articles:
        if count >= max_items:
            break
        if article.get("summary"):
            continue
        raw = article.get("raw_content", "")[:800]
        if not raw:
            continue
        title = article.get("title", "")
        summary = _call_llm(
            "You are a concise tech news summariser. Write 3-4 clear, informative sentences "
            "that capture the key points of the article. Be specific and include any numbers, "
            "names, or technical details mentioned.",
            f"Summarise this article:\nTitle: {title}\nContent: {raw}",
            max_tokens=200,
        )
        if summary:
            article["summary"] = summary
        count += 1
        time.sleep(0.3)
    logger.info("[LLMSummarizer] Summarised %d articles", count)
    return articles


def batch_summarise_repos(repos: list[dict]) -> list[dict]:
    """Generate short summaries for GitHub repos (no LLM needed)."""
    for repo in repos[:20]:
        if repo.get("summary"):
            continue
        tags = " ".join(f"#{t}" for t in generate_hashtags(
            repo.get("name", "") + " " + repo.get("description", "")
        ))
        repo["summary"] = (
            f"⭐ **{repo.get('name', '')}**\n\n"
            f"🧠 {repo.get('description', '')}\n\n"
            f"🔥 +{repo.get('today_stars', 0)} stars today | "
            f"⭐ {repo.get('stars', 0):,} total | "
            f"🌐 {repo.get('language', 'Unknown')}\n\n"
            f"🔗 {repo.get('url', '')}\n\n{tags}"
        )
    return repos


def batch_summarise_papers(papers: list[dict]) -> list[dict]:
    """
    Generate short card-preview summaries for research papers.
    These are NOT the channel posts — they are the 2-3 sentence previews
    shown in the feed cards.
    """
    max_items = int(os.getenv("MAX_SUMMARISE_PER_RUN", "20"))
    count = 0
    for paper in papers[:max_items]:
        if paper.get("summary"):
            continue
        abstract = paper.get("abstract", paper.get("raw_content", ""))[:800]
        if not abstract:
            continue
        title = paper.get("title", "")
        summary = _call_llm(
            "You are a research communicator. Write 3-4 clear, accessible sentences "
            "that explain what this paper is about, what it found, and why it matters. "
            "Be specific about the method and results.",
            f"Summarise this paper:\nTitle: {title}\nAbstract: {abstract}",
            max_tokens=200,
        )
        if summary:
            paper["summary"] = summary
        count += 1
        time.sleep(0.3)
    logger.info("[LLMSummarizer] Summarised %d papers", count)
    return papers


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Node
# ─────────────────────────────────────────────────────────────────────────────

def run_llm_summarizer(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function for the LLM Summarizer Agent."""
    logger.info("[LLMSummarizer] Generating summaries …")
    start = datetime.utcnow()

    articles = state.get("analyzed_articles", state.get("filtered_articles", []))
    repos = state.get("filtered_repos", [])
    papers = state.get("research_papers", [])

    summarized_articles = batch_summarise_articles(articles)
    summarized_repos = batch_summarise_repos(repos)
    summarized_papers = batch_summarise_papers(papers)

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info("[LLMSummarizer] Done in %.1fs", elapsed)

    return {
        **state,
        "summarized_articles": summarized_articles,
        "summarized_repos": summarized_repos,
        "summarized_papers": summarized_papers,
        "summarizer_elapsed": elapsed,
    }