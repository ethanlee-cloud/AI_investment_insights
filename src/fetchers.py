from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from .dedupe import dedupe_links


def _http_get(url: str, user_agent: str, timeout: int = 30) -> str:
    r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    r.raise_for_status()
    return r.text


def _parse_rss_feed(feed_url: str, user_agent: str) -> List[Dict[str, Any]]:
    xml = _http_get(feed_url, user_agent=user_agent)
    soup = BeautifulSoup(xml, "xml")
    items = []
    for item in soup.find_all("item"):
        title = (item.title.text if item.title else "").strip()
        link = (item.link.text if item.link else "").strip()
        pub = (item.pubDate.text if item.pubDate else "").strip()
        dt = None
        if pub:
            try:
                dt = dateparser.parse(pub)
            except Exception:
                dt = None
        if link:
            items.append({
                "title": title,
                "url": link,
                "published": dt.isoformat() if dt else None,
                "source": feed_url,
            })
    return items


def _simple_news_index_scrape(index_url: str, user_agent: str) -> List[Dict[str, Any]]:
    html = _http_get(index_url, user_agent=user_agent)
    soup = BeautifulSoup(html, "lxml")

    # Generic strategy: collect a-tags with plausible article URLs
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        txt = a.get_text(" ", strip=True)
        if not href:
            continue
        if href.startswith("/"):
            # build absolute
            from urllib.parse import urljoin
            href = urljoin(index_url, href)
        if href.startswith("http") and len(txt) >= 8:
            links.append({"title": txt, "url": href, "published": None, "source": index_url})
    return links


def collect_latest_articles(cfg, cache) -> List[Dict[str, Any]]:
    """
    Returns list of items: {title, url, published, source, site_name}
    """
    all_items: List[Dict[str, Any]] = []

    # RSS first (most reliable)
    for feed in cfg.rss_feeds:
        try:
            items = _parse_rss_feed(feed, user_agent=cfg.project.user_agent)
            all_items.extend(items)
        except Exception:
            continue

    # Then scrape each site's news_index if provided
    for site in cfg.websites:
        if not site.news_index:
            continue
        try:
            items = _simple_news_index_scrape(site.news_index, user_agent=cfg.project.user_agent)
            for it in items:
                it["site_name"] = site.name
            all_items.extend(items)
        except Exception:
            continue

    # Attach site_name if missing
    for it in all_items:
        it.setdefault("site_name", "Unknown")

    # Dedupe
    all_items = dedupe_links(all_items)

    # Filter by lookback if we have dates
    cutoff = datetime.utcnow() - timedelta(days=cfg.project.lookback_days)
    filtered = []
    for it in all_items:
        pub = it.get("published")
        if not pub:
            filtered.append(it)
            continue
        try:
            dt = dateparser.parse(pub)
            if dt and dt >= cutoff:
                filtered.append(it)
        except Exception:
            filtered.append(it)

    # Limit per site and total
    per_site = {}
    out = []
    for it in filtered:
        s = it.get("site_name", "Unknown")
        per_site.setdefault(s, 0)
        if per_site[s] >= cfg.project.max_articles_per_site:
            continue
        per_site[s] += 1
        out.append(it)
        if len(out) >= cfg.project.max_total_articles:
            break

    return out
