from __future__ import annotations

from urllib.parse import quote_plus

import feedparser
import httpx

from ..config import HTTP_TIMEOUT
from .common import Detection, looks_like_airdrop, strip_tags
from .news import parse_feed

# Public RSS only — no unofficial X scraping, no login.
X_FEEDS = [
    "https://news.google.com/rss/search?q="
    + quote_plus(
        "(airdrop OR testnet OR \"trade to earn\" OR \"points season\" OR "
        "bridge OR launchpool) (site:x.com OR site:twitter.com)"
    )
    + "&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q="
    + quote_plus("Binance OR Bybit OR OKX (airdrop OR launchpool OR testnet OR \"trading competition\")")
    + "&hl=en-US&gl=US&ceid=US:en",
]


def parse_x_feed(body: str, source: str) -> list[Detection]:
    news = parse_feed(body, source)
    out: list[Detection] = []
    for hit in news:
        blob = f"{hit.title} {hit.source}"
        if not looks_like_airdrop(blob):
            continue
        out.append(
            Detection(
                channel="x",
                source_name="X / news RSS",
                title=hit.title,
                url=hit.url,
                body=hit.source,
                published_at=hit.published,
                extra={"feed": source},
            )
        )
    return out


def parse_rsshub_like(body: str, source: str) -> list[Detection]:
    parsed = feedparser.parse(body)
    out: list[Detection] = []
    for entry in parsed.entries[:30]:
        title = strip_tags(entry.get("title") or "")
        summary = strip_tags(entry.get("summary") or "")
        if not looks_like_airdrop(f"{title} {summary}"):
            continue
        link = (entry.get("link") or "").strip()
        if title and link:
            out.append(
                Detection(
                    channel="x",
                    source_name=source,
                    title=title,
                    url=link,
                    body=summary[:500],
                    published_at=str(entry.get("published") or ""),
                )
            )
    return out


async def fetch_x_airdrops(client: httpx.AsyncClient) -> tuple[list[Detection], list[str]]:
    hits: list[Detection] = []
    errors: list[str] = []
    headers = {"User-Agent": "AirdropIntelBot/1.0"}
    seen: set[str] = set()
    for url in X_FEEDS:
        try:
            resp = await client.get(url, headers=headers, timeout=HTTP_TIMEOUT, follow_redirects=True)
            resp.raise_for_status()
            for hit in parse_x_feed(resp.text, url):
                key = hit.title.lower()
                if key in seen:
                    continue
                seen.add(key)
                hits.append(hit)
        except Exception as exc:
            errors.append(f"x-feed: {exc}")
    return hits, errors
