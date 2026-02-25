"""
run.py
------
CLI entry point for the AI Tech News Multi-Agent Aggregator.

Usage:
    # Run a single pipeline pass
    python run.py

    # Run the Streamlit dashboard
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.logger import setup_logging
from src.pipeline import run_pipeline

if __name__ == "__main__":
    setup_logging()
    print("Starting AI Tech News Multi-Agent Aggregator Pipeline...")
    result = run_pipeline()
    print(
        f"\nPipeline complete!"
        f"\n  Articles stored : {result.get('stored_articles_count', 0)}"
        f"\n  Repos stored    : {result.get('stored_repos_count', 0)}"
        f"\n  Trending topics : {[t['topic'] for t in result.get('trending_topics', [])[:3]]}"
    )
