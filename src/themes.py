from typing import List, Dict, Any


def build_themes(llm, articles: List[Dict[str, Any]], etf_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    clustered = llm.cluster_themes(articles, etf_map)
    themes = clustered.get("themes", [])
    # Normalize fields
    out = []
    for t in themes:
        out.append({
            "theme": t.get("theme", "unknown"),
            "description": t.get("description", ""),
            "articles": t.get("articles", []),
            "theme_sentiment_score": float(t.get("theme_sentiment_score", 0.0)),
            "etfs": t.get("etfs", []),
            "suggested_etfs": t.get("suggested_etfs", []),
        })
    return out
