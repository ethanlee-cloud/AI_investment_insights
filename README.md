# Insight Radar

Scans chosen websites for latest news/insights, summarizes with citations, maps themes to ETFs,
pulls market data from Yahoo Finance, and estimates what looks priced-in vs not.

## Setup
1. `pip install -r requirements.txt`
2. Copy `config.example.yaml` -> `config.yaml` and fill DeepSeek key/model/base_url
3. Copy `etf_map.example.json` -> `etf_map.json`
4. Run: `python main.py`

## Customize
- Websites: `config.yaml -> websites`
- RSS feeds: `config.yaml -> rss_feeds`
- ETF map: `etf_map.json`
- Prompts: `prompts/*.txt`

## Output
- `output/report.md`
- Cached extracted articles in `.cache/`

## Disclaimer
Not financial advice.
