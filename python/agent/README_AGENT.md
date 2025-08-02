# Trading Agent (OpenRouter-enabled)

This agent provides:
1) API key management for OpenRouter (persisted in config.yaml)
2) Orchestrating the main pipeline (runs python/main.py once on demand)
3) Artifact discovery (latest dataset in ./python/data and latest visualization in ./python/visualization)
4) LLM-backed analysis via OpenRouter to produce a concise report

Files added:
- python/agent/agent.py
- python/utils/config.py additions (ensure_path, set_path, get_path helpers)

Prerequisites
- Python 3.9+
- Dependencies in python/requirements.txt (plus `requests` if not already present for OpenRouter HTTP calls)
- A valid OpenRouter API key (https://openrouter.ai/)

Configuration
The agent expects OpenRouter configuration under these YAML keys (created if missing):
llm:
  openrouter:
    api_key: "YOUR_KEY_HERE"
    model: "openrouter/auto"

Your existing python/config.yaml remains the single source of truth.

CLI Usage
From the python directory:

1) Set or update your OpenRouter API key (persist to config.yaml)
python -m agent.agent --update-key YOUR_OPENROUTER_API_KEY

2) Run the main pipeline once (uses yaml config for sources and storage)
python -m agent.agent --run-main
Optional flags:
  --sources coingecko,cointelegraph    # restrict sources
  --verbose                            # verbose logs to console

3) Analyze latest artifacts with LLM
python -m agent.agent --analyze
Optional flags:
  --model openrouter/auto:free    # override llm.openrouter.model for this run

What the analysis does
- Loads a small preview of the newest dataset (CSV/JSON) from ./python/data:
  - shape, columns, dtypes, head, numeric describe
- Summarizes the newest visualization from ./python/visualization:
  - filename, extension, title (if HTML)
- Calls OpenRouter with a concise system instruction for trading-relevant insights
- Writes a JSON report to ./python/data/agent_analysis_YYYYMMDD_HHMMSS.json

Programmatic Usage
from agent.agent import TradingAgent, AgentConfig

agent = TradingAgent(AgentConfig(config_path="python/config.yaml"))
agent.update_api_key("YOUR_OPENROUTER_API_KEY")
agent.run_main(sources=["coingecko"], schedule="once", verbose=True)
result = agent.analyze(model="openrouter/auto")  # returns dict with analysis and artifact paths

Notes
- The agent does not store API keys in environment variables; it persists directly to yaml per your preference.
- If python/visualization is empty, analysis still runs with a note indicating no visuals were found.
- The main pipeline writes data files to ./python/data via CSV/JSON/SQLite depending on your yaml settings; the agent looks for CSV/JSON for analysis preview.

Troubleshooting
- If you see "Configuration missing or invalid": ensure python/config.yaml exists and is not empty.
- If OpenRouter request fails, verify the API key and network access. The agent raises the HTTP status and error body.
