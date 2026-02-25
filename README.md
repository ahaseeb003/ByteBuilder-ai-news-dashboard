# ByteBuilder AI News Dashboard

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.50-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![WhatsApp](https://img.shields.io/badge/ByteBuilder-WhatsApp%20Channel-25D366?logo=whatsapp&logoColor=white)](https://whatsapp.com/channel/0029Vb3uqO6D8SE3VcoOag2f)

> **Your personal AI-powered newsroom.** A multi-agent dashboard that automates the entire process of fetching, filtering, analysing, and creating channel-ready posts from the latest global tech news and research papers.

---

## Overview

The **ByteBuilder AI News Dashboard** is an open-source project built with **LangGraph** and **Streamlit** that deploys a team of specialised AI agents to run a fully automated content pipeline. It is designed for content creators, AI researchers, and tech enthusiasts who want to stay ahead of the curve without the manual effort of browsing dozens of sources every day.

The system is split into two focused panels: a **Trending News Feed** for reading and curating content, and a **Post Creator** for generating polished, channel-ready posts in one click.

---

## Key Features

- **Multi-Agent Pipeline (LangGraph):** A stateful, cyclical graph orchestrates six specialised agents — Collector, Filter, Trend Analyser, LLM Summariser, Research Paper Agent, and Storage Agent — each passing enriched state to the next.
- **80+ Global Sources:** Content is aggregated from major tech news outlets, AI lab blogs, engineering blogs, GitHub trending, arXiv (8 categories), and Papers With Code.
- **Intelligent Scoring:** Every article is scored on a combined metric of freshness (60%) and relevance (40%), ensuring the feed always surfaces the most timely and important content first.
- **Five Post Templates:** Generate channel-ready posts in five distinct styles — Tech Insight, New AI Tool, Tech Update, Weekly Digest, and Deep Dive — all with ByteBuilder branding and reference links included.
- **Real-Time Research Mode:** Enter any topic, URL, or arXiv ID to trigger a live research sub-graph that gathers sources and generates a full post with inline citations in seconds.
- **Premium UI:** A polished dark-mode dashboard with glassmorphism cards, gradient accents, and animated elements — built entirely with Streamlit custom CSS.

---

## Architecture

The backend is a LangGraph `StateGraph` where each node is an independent agent. The graph is compiled once at startup and invoked on demand from the dashboard or the CLI runner.

```
RSS Feeds / arXiv / GitHub
         │
         ▼
┌─────────────────────┐
│  Data Collector     │  Fetches & normalises articles, papers, repos
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Content Filter     │  Deduplicates, scores freshness + relevance
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Trend Analyser     │  TF-IDF scoring, topic clustering, hashtag extraction
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  LLM Summariser     │  Generates card previews via LLM (with fallback)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Research Paper     │  Fetches arXiv + Papers With Code papers
│  Agent              │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Storage Agent      │  Persists everything to SQLite
└─────────────────────┘
```

The **Real-Time Post Generator** is a separate 4-node sub-graph:
`InputClassifier → ContextGatherer → PostWriter → QualityChecker`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph, LangChain |
| LLM | OpenAI-compatible API (OpenRouter free tier supported) |
| Frontend | Streamlit + custom CSS |
| Database | SQLite (via Python `sqlite3`) |
| Feed Parsing | `feedparser` |
| Research APIs | arXiv API, Papers With Code API, Semantic Scholar API |
| Search | DuckDuckGo Search (via `duckduckgo-search`) |
| Scheduling | Python `threading` + `schedule` |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ahaseeb003/ByteBuilder-ai-news-dashboard.git
cd ByteBuilder-ai-news-dashboard
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```
OPENAI_API_KEY=your_key_here
```

A free API key can be obtained from [OpenRouter.ai](https://openrouter.ai), which provides access to several capable open-source models at no cost.

### 4. Run the pipeline

This fetches the latest content from all sources and populates the local database:

```bash
python run.py
```

### 5. Launch the dashboard

```bash
streamlit run app/dashboard.py
```

Open your browser to `http://localhost:8501`.

---

## Project Structure

```
ByteBuilder-ai-news-dashboard/
├── app/
│   └── dashboard.py              # Streamlit UI (all panels and CSS)
├── config/
│   └── settings.py               # All feeds, templates, and config constants
├── src/
│   ├── pipeline.py               # LangGraph StateGraph definition
│   ├── database.py               # SQLite layer (CRUD, freshness queries)
│   ├── logger.py                 # Rotating file + console logger
│   ├── utils.py                  # Text cleaning, scoring, hashtag utilities
│   └── agents/
│       ├── data_collector_agent.py       # RSS + GitHub trending collector
│       ├── content_filter_agent.py       # Deduplication + freshness scoring
│       ├── trend_analyzer_agent.py       # TF-IDF + topic clustering
│       ├── llm_summarizer_agent.py       # All 5 post templates + LLM calls
│       ├── research_paper_agent.py       # arXiv + Papers With Code
│       ├── storage_agent.py              # SQLite persistence
│       ├── scheduler_agent.py            # Background scheduler
│       └── realtime_post_generator.py   # Real-time research sub-graph
├── docs/
│   ├── architecture_v3.png       # System architecture diagram
│   ├── SETUP_GUIDE.md
│   └── DEPLOYMENT.md
├── tests/
│   ├── test_utils.py
│   └── test_database.py
├── run.py                        # CLI entry point
├── requirements.txt
└── .env.example
```

---

## Post Templates

The dashboard supports five post templates, each designed for a specific content style:

| Template | Style | Best For |
|---|---|---|
| 🔥 Tech Update | Short, punchy 5-point update | Breaking news, quick announcements |
| 🚀 New AI Tool | Feature-focused tool breakdown | New product launches, tool reviews |
| 🖥️ AI Insight | Deep educational post | Research papers, complex topics |
| 📅 Weekly Digest | Curated weekly roundup | Newsletter-style weekly posts |
| 📖 Deep Dive | Long-form storytelling guide | Tutorials, comprehensive breakdowns |

Every generated post includes inline reference links and closes with:

```
——————————————————
🔔 Follow ByteBuilder for more AI & tech insights!
👨‍💻 Developed by HMtechie & ByteBuilder
```

---

## Community

Stay up to date with the latest AI and tech insights by joining the **ByteBuilder** WhatsApp channel:

**[➡️ Join ByteBuilder on WhatsApp](https://whatsapp.com/channel/0029Vb3uqO6D8SE3VcoOag2f)**

---

## Contributors

This project is built and maintained by:

| Name | Role | Profile |
|---|---|---|
| **Abdul Haseeb** | Co-Founder & Lead Developer | [LinkedIn](https://www.linkedin.com/in/abd-ul-haseeb) · [GitHub](https://github.com/ahaseeb003) |
| **Musa Khan** | Co-Founder | [LinkedIn](https://www.linkedin.com/in/mussakhan-ai/) |

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change, then submit a pull request.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
