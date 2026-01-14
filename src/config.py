from dataclasses import dataclass, field

from typing import List, Optional, Dict, Any
import yaml


@dataclass
class DeepSeekConfig:
    api_key: str
    base_url: str
    model: str
    timeout_sec: int = 60


@dataclass
class ProjectConfig:
    max_articles_per_site: int = 5
    max_total_articles: int = 30
    lookback_days: int = 14
    cache_dir: str = ".cache"
    output_dir: str = "output"
    user_agent: str = "insight-radar/0.1"


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


@dataclass
class WebsiteConfig:
    name: str
    url: str
    news_index: Optional[str] = None


@dataclass
class OutputConfig:
    report_filename: str = "report.md"
    save_raw_articles: bool = True


@dataclass
class AppConfig:
    deepseek: DeepSeekConfig
    project: ProjectConfig
    websites: List[WebsiteConfig]
    rss_feeds: List[str]
    market: MarketConfig
    output: OutputConfig


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    deepseek = DeepSeekConfig(**data["deepseek"])
    project = ProjectConfig(**data.get("project", {}))
    websites = [WebsiteConfig(**w) for w in data.get("websites", [])]
    rss_feeds = data.get("rss_feeds", [])
    output = OutputConfig(**data.get("output", {}))

    market_data = data.get("market", {})
    sigs = market_data.get("signals", {})
    market = MarketConfig(
        benchmark=market_data.get("benchmark", "SPY"),
        history_days=market_data.get("history_days", 365),
        signals=MarketSignalsConfig(
            strong_move_1m=sigs.get("strong_move_1m", 0.08),
            strong_drop_1m=sigs.get("strong_drop_1m", -0.08),
            z_threshold=sigs.get("z_threshold", 2.0),
            drawdown_deep=sigs.get("drawdown_deep", -0.08),
        )
    )

    return AppConfig(
        deepseek=deepseek,
        project=project,
        websites=websites,
        rss_feeds=rss_feeds,
        market=market,
        output=output,
    )
