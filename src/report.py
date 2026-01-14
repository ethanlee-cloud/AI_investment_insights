from typing import List, Dict, Any
from datetime import datetime


def _md_escape(s: str) -> str:
    return (s or "").replace("\n", " ").strip()


def write_report(path: str, themes: List[Dict[str, Any]], articles: List[Dict[str, Any]], cfg) -> None:
    now = datetime.utcnow().isoformat()

    # quick buckets by LLM verdict
    buckets = {
        "possibly not priced in": [],
        "partially priced in": [],
        "likely priced in / crowded": [],
        "negative priced in": [],
        "mixed/unclear": [],
    }

    for t in themes:
        verdict = (t.get("llm_priced_in") or {}).get("verdict", "mixed/unclear")
        buckets.setdefault(verdict, []).append(t)

    lines = []
    lines.append(f"# Insight Radar Report\n")
    lines.append(f"- Generated (UTC): {now}\n")
    lines.append(f"- Sites scanned: {len(cfg.websites)}\n")
    lines.append(f"- Articles summarized: {len(articles)}\n")
    lines.append("\n---\n")
    lines.append("## Executive summary\n")

    def add_bucket(title, key):
        lines.append(f"### {title}\n")
        if not buckets.get(key):
            lines.append("- (none)\n")
            return
        for t in buckets[key]:
            lines.append(f"- **{_md_escape(t['theme'])}**: {_md_escape(t.get('description',''))}\n")
        lines.append("\n")

    add_bucket("Possibly not priced in", "possibly not priced in")
    add_bucket("Partially priced in", "partially priced in")
    add_bucket("Likely priced in / crowded", "likely priced in / crowded")
    add_bucket("Negative priced in", "negative priced in")
    add_bucket("Mixed / unclear", "mixed/unclear")

    lines.append("\n---\n")
    lines.append("## Themes (details)\n")

    for t in themes:
        verdict = (t.get("llm_priced_in") or {}).get("verdict", "mixed/unclear")
        reasons = (t.get("llm_priced_in") or {}).get("reasoning_bullets", [])

        lines.append(f"### {t.get('theme','unknown')}\n")
        lines.append(f"- **Verdict:** {verdict}\n")
        lines.append(f"- **Theme sentiment:** {t.get('theme_sentiment_score', 0.0)}\n")
        if t.get("description"):
            lines.append(f"- **Theme:** {_md_escape(t['description'])}\n")

        if reasons:
            lines.append("\n**Why (LLM):**\n")
            for r in reasons[:8]:
                lines.append(f"- {_md_escape(r)}\n")

        # ETFs and signals
        sigs = t.get("etf_signals", [])
        if sigs:
            lines.append("\n**ETFs checked (Yahoo Finance signals):**\n")
            for s in sigs:
                if "error" in s:
                    lines.append(f"- `{s.get('ticker')}`: {s.get('error')}\n")
                    continue
                lines.append(
                    f"- `{s.get('ticker')}`: 1M={s.get('ret_1m'):.2%}  "
                    f"3M={s.get('ret_3m'):.2%}  "
                    f"z={s.get('last_move_z') if s.get('last_move_z') is not None else 'n/a'}  "
                    f"dd90={s.get('drawdown_from_90d_high'):.2%}\n"
                )

        # Citations: list linked articles + evidence snippets from per-article summaries
        lines.append("\n**Citations:**\n")
        # build lookup from articles list
        by_url = {a["url"]: a for a in articles}
        for a_ref in t.get("articles", []):
            url = a_ref.get("url")
            a = by_url.get(url)
            if not a:
                lines.append(f"- {a_ref.get('title','(unknown)')} | {url}\n")
                continue
            pub = a.get("published") or "unknown date"
            lines.append(f"- {a.get('title','(untitled)')} ({pub}) | {a.get('url')}\n")
            ev = (a.get("summary") or {}).get("evidence_snippets", [])
            for snip in ev[:4]:
                lines.append(f"  - Evidence: “{_md_escape(snip)}”\n")

        lines.append("\n---\n")

    lines.append("\n## Disclaimer\n")
    lines.append("Not financial advice.\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(lines))
