# Step-by-Step Setup Guide

This guide walks you through setting up and running the AI Tech News Multi-Agent Aggregator Dashboard from scratch.

## Step 1: Prerequisites

Ensure you have the following installed on your system:

- **Python 3.9 or higher**: Download from [python.org](https://www.python.org/downloads/).
- **pip**: Python's package installer (usually included with Python).
- **Git** (optional): For cloning the repository.

## Step 2: Get an API Key

The LLM Summarizer Agent requires an API key to generate summaries. The system is configured to use **OpenRouter**, which provides access to many free and paid models.

1. Go to [https://openrouter.ai/](https://openrouter.ai/) and create a free account.
2. Navigate to the "Keys" section and create a new API key.
3. Copy the key — you will need it in the next step.

> **Free Models Available on OpenRouter**: `mistralai/mistral-7b-instruct:free`, `google/gemini-flash-1.5:free`, `meta-llama/llama-3.1-8b-instruct:free`.

## Step 3: Configure the Environment

1. Navigate to the project root directory.
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` in a text editor and paste your API key:
   ```
   OPENAI_API_KEY=sk-or-v1-your-key-here
   ```

## Step 4: Install Dependencies

It is strongly recommended to use a virtual environment to avoid conflicts with other Python projects.

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install all required packages
pip install -r requirements.txt
```

## Step 5: Run the Pipeline (First Test)

Before launching the dashboard, run a single pipeline pass to populate the database with initial data.

```bash
python run.py
```

You should see output similar to:
```
Starting AI Tech News Multi-Agent Aggregator Pipeline...
Pipeline complete!
  Articles stored : 45
  Repos stored    : 12
  Trending topics : ['LLMs & Language Models', 'Generative AI & Images', 'AI Agents & Automation']
```

## Step 6: Launch the Dashboard

```bash
streamlit run app/dashboard.py
```

Streamlit will open the dashboard in your default web browser at `http://localhost:8501`.

## Step 7: Enable Automation

In the dashboard sidebar, toggle the **"Auto-run every hour"** switch to enable the scheduler. The pipeline will then run automatically in the background, keeping the dashboard fresh with new content.

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Ensure your virtual environment is activated and `pip install -r requirements.txt` was run. |
| `No articles found` | Run the pipeline manually via the sidebar button or `python run.py`. |
| LLM summaries are empty | Check that `OPENAI_API_KEY` is set correctly in your `.env` file. |
| GitHub Trending shows no repos | GitHub may have temporarily changed their page structure. The scraper may need an update. |
| Database errors | Delete `data/news.db` and restart — the database will be recreated automatically. |
