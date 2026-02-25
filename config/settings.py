"""
settings.py
-----------
Central configuration for the AI Tech News Multi-Agent Aggregator Dashboard.
All environment variables and defaults are managed here.

Developed by HMtechie & ByteBuilder.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# Base Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DATA_DIR / "news.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# LLM Configuration
# ─────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
# Default free model on OpenRouter. Override via LLM_MODEL in your .env file.
# Current working free models (Feb 2025): mistralai/mistral-nemo:free,
#   google/gemma-3-12b-it:free, meta-llama/llama-3.2-3b-instruct:free
LLM_MODEL: str = os.getenv("LLM_MODEL", "mistralai/mistral-nemo:free")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ─────────────────────────────────────────────
# Scheduler Configuration
# ─────────────────────────────────────────────
SCHEDULER_INTERVAL_MINUTES: int = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))

# ─────────────────────────────────────────────────────────────────────────────
# RSS / News Feeds — Global Tech Sector (80+ verified sources)
#
# Organised into 10 categories so the dashboard can display them by section.
# Every feed URL has been verified to return valid RSS/Atom XML.
# ─────────────────────────────────────────────────────────────────────────────

# ── Category 1: AI Labs & Research ──────────────────────────────────────────
_FEEDS_AI_LABS: list[str] = [
    "https://openai.com/blog/rss.xml",                          # OpenAI
    "https://deepmind.google/blog/rss.xml",                     # Google DeepMind
    "https://ai.googleblog.com/feeds/posts/default",            # Google AI Blog
    "https://blogs.microsoft.com/ai/feed/",                     # Microsoft AI
    "https://aws.amazon.com/blogs/machine-learning/feed/",      # AWS ML
    "https://huggingface.co/blog/feed.xml",                     # Hugging Face
    "https://bair.berkeley.edu/blog/feed.xml",                  # Berkeley AI Research
    "https://mistral.ai/news/rss",                              # Mistral AI
    "https://www.anthropic.com/rss.xml",                        # Anthropic
    "https://stability.ai/news/rss.xml",                        # Stability AI
    "https://blog.research.google/feeds/posts/default",         # Google Research
    "https://developer.nvidia.com/blog//feed",                  # NVIDIA Developer Blog
]

# ── Category 2: Major Tech News (Global) ────────────────────────────────────
_FEEDS_MAJOR_TECH: list[str] = [
    "https://techcrunch.com/feed/",                             # TechCrunch (all)
    "https://www.theverge.com/rss/index.xml",                   # The Verge (all)
    "https://www.wired.com/feed/rss",                           # WIRED (all)
    "https://feeds.arstechnica.com/arstechnica/index",          # Ars Technica (all)
    "https://www.zdnet.com/news/rss.xml",                       # ZDNet
    "https://venturebeat.com/feed/",                            # VentureBeat (all)
    "https://www.technologyreview.com/feed/",                   # MIT Tech Review
    "https://cnet.com/rss/news",                                # CNET
    "https://engadget.com/rss.xml",                             # Engadget
    "https://www.digitaltrends.com/feed/",                      # Digital Trends
    "https://mashable.com/feeds/rss/tech",                      # Mashable Tech
    "https://siliconangle.com/feed/",                           # SiliconANGLE
    "https://techradar.com/feeds.xml",                          # TechRadar
    "https://www.pcmag.com/feeds/rss/latest",                   # PCMag
    "https://www.theregister.com/headlines.atom",               # The Register (all)
    "https://geekwire.com/feed/",                               # GeekWire
    "https://bgr.com/feed/",                                    # BGR
    "https://tech.eu/feed/",                                    # Tech.eu (Europe)
    "https://siliconrepublic.com/feed/",                        # Silicon Republic (Ireland)
    "https://www.techspot.com/backend.xml",                     # TechSpot
    "https://betanews.com/feed/",                               # BetaNews
    "https://extremetech.com/feed",                             # ExtremeTech
    "https://gizmodo.com/feed",                                 # Gizmodo
    "https://www.infoworld.com/index.rss",                      # InfoWorld
    "https://9to5mac.com/feed/",                                # 9to5Mac
    "https://appleinsider.com/rss/news",                        # AppleInsider
]

# ── Category 3: Developer & Engineering ─────────────────────────────────────
_FEEDS_DEVELOPER: list[str] = [
    "https://feeds.feedburner.com/oreilly/radar",               # O'Reilly Radar
    "https://www.infoq.com/feed/",                              # InfoQ (all topics)
    "https://www.infoq.com/devops/rss/",                        # InfoQ DevOps
    "https://www.infoq.com/cloud-computing/rss/",               # InfoQ Cloud
    "https://stackoverflow.blog/feed/",                         # Stack Overflow Blog
    "https://github.blog/feed/",                                # GitHub Blog
    "https://engineering.fb.com/feed/",                         # Meta Engineering
    "https://netflixtechblog.com/feed",                         # Netflix Tech Blog
    "https://eng.uber.com/feed/",                               # Uber Engineering
    "https://engineering.atspotify.com/feed/",                  # Spotify Engineering
    "https://blog.cloudflare.com/rss/",                         # Cloudflare Blog
    "https://aws.amazon.com/blogs/aws/feed/",                   # AWS Official Blog
    "https://cloud.google.com/blog/rss/",                       # Google Cloud Blog
    "https://devblogs.microsoft.com/feed/",                     # Microsoft Dev Blogs
    "https://hackaday.com/blog/feed/",                          # Hackaday
    "https://news.ycombinator.com/rss",                         # Hacker News (top)
    "https://hnrss.org/newest?points=100",                      # Hacker News (100+ pts)
]

# ── Category 4: Cybersecurity ────────────────────────────────────────────────
_FEEDS_SECURITY: list[str] = [
    "https://krebsonsecurity.com/feed/",                        # Krebs on Security
    "https://feeds.feedburner.com/TheHackersNews",              # The Hacker News
    "https://www.darkreading.com/rss.xml",                      # Dark Reading
    "https://www.bleepingcomputer.com/feed/",                   # BleepingComputer
    "https://nakedsecurity.sophos.com/feed/",                   # Sophos Naked Security
    "https://www.schneier.com/blog/atom.xml",                   # Schneier on Security
    "https://threatpost.com/feed/",                             # Threatpost
    "https://www.securityweek.com/feed/",                       # SecurityWeek
    "https://isc.sans.edu/rssfeed_full.xml",                    # SANS Internet Storm Center
    "https://www.csoonline.com/feed/",                          # CSO Online
    "https://www.infosecurity-magazine.com/rss/news/",          # Infosecurity Magazine
]

# ── Category 5: Startups & Business ─────────────────────────────────────────
_FEEDS_STARTUPS: list[str] = [
    "https://techcrunch.com/category/startups/feed/",           # TechCrunch Startups
    "https://www.producthunt.com/feed",                         # Product Hunt
    "https://feeds.feedburner.com/thenextweb",                  # The Next Web
    "https://www.businessinsider.com/tech/rss",                 # Business Insider Tech
    "https://fortune.com/feed/fortune-feeds/?id=3230629",       # Fortune Tech
    "https://www.fastcompany.com/technology/rss",               # Fast Company Tech
    "https://www.inc.com/technology/rss.xml",                   # Inc. Technology
    "https://www.techinasia.com/feed",                          # Tech in Asia
    "https://e27.co/feed/",                                     # e27 (Southeast Asia)
    "https://www.eu-startups.com/feed/",                        # EU Startups (Europe)
    "https://techfundingnews.com/feed/",                        # Tech Funding News
]

# ── Category 6: AI / ML Blogs & Newsletters ─────────────────────────────────
_FEEDS_AI_BLOGS: list[str] = [
    "https://towardsdatascience.com/feed",                      # Towards Data Science
    "https://machinelearningmastery.com/blog/feed/",            # ML Mastery
    "https://lilianweng.github.io/index.xml",                   # Lilian Weng
    "https://sebastianraschka.com/rss_feed.xml",                # Sebastian Raschka
    "https://www.interconnects.ai/feed",                        # Interconnects AI
    "https://newsletter.theaiedge.io/feed",                     # The AI Edge
    "https://www.deeplearning.ai/the-batch/feed/",              # DeepLearning.AI The Batch
    "https://jack-clark.net/feed/",                             # Jack Clark (Import AI)
    "https://lastweekin.ai/feed",                               # Last Week in AI
    "https://www.aiweekly.co/feed/",                            # AI Weekly
    "https://aisnakeoil.substack.com/feed",                     # AI Snake Oil
    "https://www.ben-evans.com/benedictevans/rss.xml",          # Benedict Evans
]

# ── Category 7: Research & Science ──────────────────────────────────────────
_FEEDS_RESEARCH: list[str] = [
    "https://arxiv.org/rss/cs.AI",                              # arXiv AI
    "https://arxiv.org/rss/cs.LG",                              # arXiv ML
    "https://arxiv.org/rss/cs.CL",                              # arXiv NLP
    "https://arxiv.org/rss/cs.CV",                              # arXiv Computer Vision
    "https://arxiv.org/rss/cs.RO",                              # arXiv Robotics
    "https://arxiv.org/rss/stat.ML",                            # arXiv Stat ML
    "https://feeds.feedburner.com/IeeeSpectrumFullText",        # IEEE Spectrum
    "https://www.nature.com/subjects/machine-learning.rss",     # Nature ML
    "https://science.sciencemag.org/rss/current.xml",           # Science Magazine
    "https://www.newscientist.com/subject/technology/feed/",    # New Scientist Tech
    "https://phys.org/rss-feed/technology-news/",               # Phys.org Tech
]

# ── Category 8: Cloud, DevOps & Enterprise ──────────────────────────────────
_FEEDS_CLOUD: list[str] = [
    "https://azure.microsoft.com/en-us/blog/feed/",             # Microsoft Azure Blog
    "https://cloud.google.com/blog/topics/inside-google-cloud/rss/", # Google Cloud Insider
    "https://www.hashicorp.com/blog/feed.xml",                  # HashiCorp Blog
    "https://kubernetes.io/feed.xml",                           # Kubernetes Blog
    "https://www.docker.com/blog/feed/",                        # Docker Blog
    "https://techrepublic.com/rssfeeds/articles/",              # TechRepublic
    "https://www.computerworld.com/index.rss",                  # Computerworld
    "https://redmonk.com/feed/",                                # RedMonk
    "https://thenewstack.io/feed/",                             # The New Stack
    "https://www.infoworld.com/cloud-computing/index.rss",      # InfoWorld Cloud
]

# ── Category 9: Mobile, Gadgets & Consumer Tech ─────────────────────────────
_FEEDS_MOBILE_GADGETS: list[str] = [
    "https://androidcentral.com/feeds.xml",                     # Android Central
    "https://feed.androidauthority.com",                        # Android Authority
    "https://www.macrumors.com/macrumors.xml",                  # MacRumors
    "https://9to5google.com/feed/",                             # 9to5Google
    "https://www.gsmarena.com/rss-news-reviews.php3",           # GSMArena
    "https://www.phonearena.com/news/rss",                      # PhoneArena
    "https://www.notebookcheck.net/News.8.0.html?rss",          # NotebookCheck
    "https://www.xda-developers.com/feed/",                     # XDA Developers
    "https://www.androidpolice.com/feed/",                      # Android Police
    "https://www.ifixit.com/News/rss",                          # iFixit
]

# ── Category 10: Open Source, Linux & FOSS ──────────────────────────────────
_FEEDS_OPENSOURCE: list[str] = [
    "https://www.linux.com/feed/",                              # Linux.com
    "https://itsfoss.com/feed/",                                # It's FOSS
    "https://fossbytes.com/feed/?x=1",                          # Fossbytes
    "https://www.omgubuntu.co.uk/feed",                         # OMG! Ubuntu
    "https://www.phoronix.com/rss.php",                         # Phoronix
    "https://opensource.com/feed",                              # Opensource.com
    "https://lwn.net/headlines/rss",                            # LWN.net
    "https://www.ghacks.net/feed/",                             # gHacks
    "https://slashdot.org/rss/technology.rss",                  # Slashdot Tech
    "https://www.reddit.com/r/technology/top.rss?t=day",        # Reddit r/technology
    "https://www.reddit.com/r/MachineLearning/top.rss?t=day",   # Reddit r/ML
]

# ── Master feed list (all categories combined) ───────────────────────────────
RSS_FEEDS: list[str] = (
    _FEEDS_AI_LABS
    + _FEEDS_MAJOR_TECH
    + _FEEDS_DEVELOPER
    + _FEEDS_SECURITY
    + _FEEDS_STARTUPS
    + _FEEDS_AI_BLOGS
    + _FEEDS_RESEARCH
    + _FEEDS_CLOUD
    + _FEEDS_MOBILE_GADGETS
    + _FEEDS_OPENSOURCE
)

# ── Feed category map (used by dashboard for filtering) ─────────────────────
FEED_CATEGORIES: dict[str, list[str]] = {
    "AI Labs & Research":           _FEEDS_AI_LABS,
    "Major Tech News":              _FEEDS_MAJOR_TECH,
    "Developer & Engineering":      _FEEDS_DEVELOPER,
    "Cybersecurity":                _FEEDS_SECURITY,
    "Startups & Business":          _FEEDS_STARTUPS,
    "AI / ML Blogs":                _FEEDS_AI_BLOGS,
    "Research & Science":           _FEEDS_RESEARCH,
    "Cloud & Enterprise":           _FEEDS_CLOUD,
    "Mobile & Gadgets":             _FEEDS_MOBILE_GADGETS,
    "Open Source & Linux":          _FEEDS_OPENSOURCE,
}

# ─────────────────────────────────────────────
# Research Paper Sources
# ─────────────────────────────────────────────
ARXIV_CATEGORIES: list[str] = [
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "stat.ML", "cs.NE", "cs.IR"
]
ARXIV_MAX_RESULTS: int = int(os.getenv("ARXIV_MAX_RESULTS", "20"))
# Papers With Code API — correct v1 endpoint with JSON Accept header required
PAPERS_WITH_CODE_URL: str = (
    "https://paperswithcode.com/api/v1/papers/"
    "?ordering=-published&items_per_page=20&format=json"
)

# ─────────────────────────────────────────────
# GitHub Trending
# ─────────────────────────────────────────────
GITHUB_TRENDING_URL: str = "https://github.com/trending?since=daily&spoken_language_code=en"
GITHUB_TRENDING_AI_TOPICS: list[str] = [
    "machine-learning", "deep-learning", "artificial-intelligence",
    "nlp", "llm", "transformer", "neural-network", "computer-vision",
    "reinforcement-learning", "generative-ai", "diffusion-model",
    "langchain", "openai", "huggingface", "pytorch", "tensorflow",
    "rag", "agents", "multimodal", "fine-tuning",
]

# ─────────────────────────────────────────────
# Tech Keywords for Content Filtering
# (expanded to cover the full tech sector, not just AI)
# ─────────────────────────────────────────────
TECH_KEYWORDS: list[str] = [
    # AI & ML
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "natural language processing", "nlp", "llm",
    "large language model", "gpt", "bert", "transformer", "diffusion",
    "generative ai", "computer vision", "reinforcement learning",
    "openai", "anthropic", "google deepmind", "hugging face",
    "stable diffusion", "chatgpt", "claude", "gemini", "mistral",
    "llama", "langchain", "langgraph", "vector database", "rag",
    "retrieval augmented generation", "fine-tuning", "embeddings",
    "multimodal", "autonomous agent", "ai agent", "foundation model",
    "pytorch", "tensorflow", "jax", "cuda", "gpu", "tpu",
    "data science", "mlops", "model deployment", "inference",
    "benchmark", "leaderboard", "ai safety", "alignment",
    "robotics", "autonomous driving", "speech recognition",
    "image generation", "text-to-image", "text-to-speech",
    "research paper", "arxiv", "preprint", "dataset", "sota",
    "state-of-the-art", "model architecture", "attention mechanism",
    # Cybersecurity
    "cybersecurity", "data breach", "ransomware", "malware", "phishing",
    "zero-day", "vulnerability", "exploit", "cve", "patch", "firewall",
    "encryption", "vpn", "threat intelligence", "soc", "siem",
    "penetration testing", "bug bounty", "hacking", "infosec",
    # Cloud & Infrastructure
    "cloud computing", "aws", "azure", "google cloud", "gcp",
    "kubernetes", "docker", "devops", "devsecops", "ci/cd",
    "serverless", "microservices", "api", "infrastructure", "saas",
    "platform engineering", "site reliability", "sre", "terraform",
    "edge computing", "cdn", "load balancer", "database", "postgresql",
    # Mobile & Devices
    "smartphone", "iphone", "android", "apple", "samsung", "pixel",
    "tablet", "wearable", "smartwatch", "5g", "6g", "iot",
    "internet of things", "embedded systems", "chip", "semiconductor",
    "processor", "arm", "risc-v", "qualcomm", "mediatek",
    # Software & Development
    "open source", "github", "programming", "software", "developer",
    "python", "javascript", "typescript", "rust", "go", "java",
    "framework", "library", "sdk", "api", "web development",
    "frontend", "backend", "full stack", "react", "node.js",
    "linux", "windows", "macos", "operating system", "kernel",
    # Business & Startups
    "startup", "funding", "venture capital", "ipo", "acquisition",
    "merger", "unicorn", "series a", "series b", "seed round",
    "tech company", "big tech", "faang", "product launch", "release",
    # Emerging Tech
    "blockchain", "cryptocurrency", "web3", "nft", "defi",
    "augmented reality", "virtual reality", "ar", "vr", "metaverse",
    "quantum computing", "space tech", "biotech", "fintech", "edtech",
    "cleantech", "electric vehicle", "ev", "autonomous vehicle",
    "3d printing", "drone", "nanotechnology",
]

# Backward-compatible alias
AI_KEYWORDS = TECH_KEYWORDS

# ─────────────────────────────────────────────
# Post Templates
# ────────────────────────────────────────# ── Template IDs (match the function names in llm_summarizer_agent.py) ──────────────
TEMPLATE_NEW_AI_TOOL    = "new_ai_tool"      # 🚀 New AI Tool
TEMPLATE_TECH_UPDATE    = "tech_update"      # 🔥 Tech Update
TEMPLATE_AI_INSIGHT     = "ai_insight"       # 🖥️ AI Insight Article
TEMPLATE_DEEP_DIVE      = "deep_dive"        # 📖 Deep Dive (long-form conversational)
TEMPLATE_WEEKLY_DIGEST  = "weekly_digest"    # 📅 Weekly Tech & AI Digest

# Legacy aliases kept for backward compatibility
TEMPLATE_WEEKLY_UPDATE  = TEMPLATE_WEEKLY_DIGEST
TEMPLATE_TECH_INSIGHT   = TEMPLATE_AI_INSIGHT
TEMPLATE_RESEARCH_PAPER = TEMPLATE_AI_INSIGHT
TEMPLATE_QUICK_NEWS     = TEMPLATE_TECH_UPDATE

POST_TEMPLATES: dict[str, dict] = {
    TEMPLATE_NEW_AI_TOOL: {
        "name": "🚀 New AI Tool",
        "description": "Highlight a new AI tool: what it does, why it’s interesting, use cases, and a Try Here link.",
        "icon": "🚀",
        "best_for": ["tools", "releases", "products"],
    },
    TEMPLATE_TECH_UPDATE: {
        "name": "🔥 Tech Update",
        "description": "Quick punchy update on a tool, concept, or technology with Key Points and a More link.",
        "icon": "🔥",
        "best_for": ["news", "announcements", "updates"],
    },
    TEMPLATE_AI_INSIGHT: {
        "name": "🖥️ AI Insight",
        "description": "Deep-dive article post: What is it, Key Highlights, Why it matters, Future outlook, Source link.",
        "icon": "🖥️",
        "best_for": ["articles", "research", "papers", "explainers"],
    },
    TEMPLATE_DEEP_DIVE: {
        "name": "📖 Deep Dive",
        "description": "Long-form conversational storytelling post. Explains a topic like a knowledgeable friend — no fluff, inline links, numbered use cases and features. Best for viral educational posts.",
        "icon": "📖",
        "best_for": ["deep-dive", "educational", "viral", "explainer", "tools", "research"],
    },
    TEMPLATE_WEEKLY_DIGEST: {
        "name": "📅 Weekly Tech & AI Digest",
        "description": "Full weekly digest: This Week in Tech, AI & Research Updates, New Tools, Top GitHub Repo, Trend of the Week.",
        "icon": "📅",
        "best_for": ["weekly", "digest", "roundup"],
    },
}
# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Path = LOGS_DIR / "app.log"
LOG_MAX_BYTES: int = 5 * 1024 * 1024
LOG_BACKUP_COUNT: int = 3

# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────
DASHBOARD_TITLE: str = "ByteBuilder AI & Tech News Dashboard"
DASHBOARD_PAGE_SIZE: int = int(os.getenv("DASHBOARD_PAGE_SIZE", "15"))
DASHBOARD_REFRESH_INTERVAL: int = 300

# ─────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────
EXPORT_DIR: Path = DATA_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Summarizer limits
# ─────────────────────────────────────────────
MAX_SUMMARISE_PER_RUN: int = int(os.getenv("MAX_SUMMARISE_PER_RUN", "30"))