from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from urllib.parse import quote_plus

import feedparser
import httpx

from ..config import HTTP_TIMEOUT
from .common import looks_like_campaign

FEEDS = [
    "https://news.google.com/rss/search?q="
    + quote_plus(
        "crypto (airdrop OR testnet OR \"incentivized testnet\" OR "
        "\"trade to earn\" OR \"points season\" OR \"bridge airdrop\" OR "
        "\"mainnet campaign\" OR launchpool)"
    )
    + "&hl=en-US&gl=US&ceid=US:en",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
]


@dataclass
class NewsHit:
    title: str
    url: str
    source: str
    published: str


def _clean(text: str) -> str:
    return unescape(re_sub_tags(text or "")).strip()


def re_sub_tags(text: str) -> str:
    out = []
    skip = False
    for ch in text:
        if ch == "<":
            skip = True
            continue
        if ch == ">":
            skip = False
            continue
        if not skip:
            out.append(ch)
    return "".join(out)


def parse_feed(body: str, source: str) -> list[NewsHit]:
    parsed = feedparser.parse(body)
    hits: list[NewsHit] = []
    feed_title = source
    if parsed.feed and parsed.feed.get("title"):
        feed_title = parsed.feed.get("title")
    for entry in parsed.entries[:40]:
        title = _clean(entry.get("title") or "")
        summary = _clean(entry.get("summary") or "")
        blob = f"{title} {summary}".lower()
        if not looks_like_campaign(blob):
            continue
        link = (entry.get("link") or "").strip()
        published = entry.get("published") or entry.get("updated") or ""
        if title and link:
            hits.append(NewsHit(title=title, url=link, source=feed_title, published=str(published)))
    return hits


async def fetch_airdrop_news(client: httpx.AsyncClient) -> list[NewsHit]:
    seen: set[str] = set()
    out: list[NewsHit] = []
    for url in FEEDS:
        try:
            resp = await client.get(
                url,
                timeout=HTTP_TIMEOUT,
                headers={"User-Agent": "AirdropIntelBot/1.0"},
                follow_redirects=True,
            )
            resp.raise_for_status()
            for hit in parse_feed(resp.text, url):
                key = hit.title.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(hit)
        except Exception:
            continue
    return out[:40]
