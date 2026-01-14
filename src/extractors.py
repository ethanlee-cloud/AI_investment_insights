from typing import Dict, Any
import trafilatura
from dateutil import parser as dateparser

from .cache import Cache


def extract_article(item: Dict[str, Any], cfg, cache: Cache) -> Dict[str, Any]:
    url = item["url"]
    cache_key = f"extracted/{cache.safe_key(url)}.json"
    cached = cache.get_json(cache_key)
    if cached:
        return cached

    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        out = {**item, "text": ""}
        cache.save_json(cache_key, out)
        return out

    extracted = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        output_format="json",
        favor_precision=True,
    )
    if not extracted:
        out = {**item, "text": ""}
        cache.save_json(cache_key, out)
        return out

    import json
    data = json.loads(extracted)

    title = data.get("title") or item.get("title") or ""
    text = data.get("text") or ""

    # date handling
    pub = item.get("published") or data.get("date")
    if pub:
        try:
            pub_dt = dateparser.parse(pub)
            pub = pub_dt.date().isoformat()
        except Exception:
            pub = str(pub)

    out = {
        "site_name": item.get("site_name", "Unknown"),
        "source": item.get("source"),
        "url": url,
        "title": title,
        "published": pub,
        "text": text,
    }
    cache.save_json(cache_key, out)
    return out
