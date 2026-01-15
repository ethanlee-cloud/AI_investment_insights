from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import yaml
import os


# ========= LLM CONFIG =========

@dataclass
class DeepSeekConfig:
    api_key: str
    base_url: str
    model: str
    timeout_sec: int = 60


# ========= PROJECT CONFIG =========

@dataclass
class ProjectConfig:
    max_articles_per_site: int = 5
    max_total_articles: int = 30
    lookback_days: int = 14
    cache_dir: str = ".cache"
    output_dir: str = "output"
    user_agent: str = "insight-radar/0.1"
    llm_enabled: bool = True


# ========= MARKET CONFIG =========

@dataclass
class MarketSignalsConfig:
    strong_move_1m: float = 0.08
    strong_drop_1m: float = -0.08
    z_threshold: float = 2.0
    drawdown_deep: float = -0.08


@dataclass
class MarketConfig:
    benchmark: str = "SPY"
    history_days: int = 365
    signals: MarketSignalsConfig = field(default_factory=MarketSignalsConfig)


# ========= WEBSITE CONFIG =========

@dataclass
class WebsiteConfig:
    name: str
    url: str
    news_index: Optional[str] = None


# ========= OUTPUT CONFIG =========

@dataclass
class OutputConfig:
    report_filename: str = "report.md"
    save_raw_articles: bool = True


# ========= APP CONFIG =========

@dataclass
class AppConfig:
    deepseek: DeepSeekConfig
    project: ProjectConfig
    websites: List[WebsiteConfig]
    rss_feeds: List[str]
    market: MarketConfig
    output: OutputConfig
    filters: Dict[str, Any] = field(default_factory=dict)


# ========= LOAD CONFIG =========

def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # --- Resolve API key (env var supported) ---
    raw_key = data["deepseek"]["api_key"]
    if isinstance(raw_key, str) and raw_key.startswith("${") and raw_key.endswith("}"):
        env_var = raw_key[2:-1]
        api_key = os.getenv(env_var, "")
    else:
        api_key = raw_key

    deepseek = DeepSeekConfig(
        api_key=api_key,
        base_url=data["deepseek"]["base_url"],
        model=data["deepseek"]["model"],
        timeout_sec=data["deepseek"].get("timeout_sec", 60),
    )

    project = ProjectConfig(**data.get("project", {}))

    websites = [
        WebsiteConfig(**w)
        for w in data.get("websites", [])
    ]

    rss_feeds = data.get("rss_feeds", [])

    market_data = data.get("market", {})
    signals_data = market_data.get("signals", {})

    market = MarketConfig(
        benchmark=market_data.get("benchmark", "SPY"),
        history_days=market_data.get("history_days", 365),
        signals=MarketSignalsConfig(**signals_data),
    )

    output = OutputConfig(**data.get("output", {}))

    filters = data.get("filters", {})

    return AppConfig(
        deepseek=deepseek,
        project=project,
        websites=websites,
        rss_feeds=rss_feeds,
        market=market,
        output=output,
        filters=filters,
    )
