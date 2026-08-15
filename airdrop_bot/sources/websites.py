from __future__ import annotations

from urllib.parse import quote_plus

import httpx

from ..config import HTTP_TIMEOUT
from .common import Detection, looks_like_airdrop
from .news import parse_feed

WEB_FEEDS = [
    "https://news.google.com/rss/search?q="
    + quote_plus("crypto airdrop OR launchpool OR \"token airdrop\"")
    + "&hl=en-US&gl=US&ceid=US:en",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
]


async def fetch_website_airdrops(client: httpx.AsyncClient) -> tuple[list[Detection], list[str]]:
    hits: list[Detection] = []
    errors: list[str] = []
    headers = {"User-Agent": "AirdropIntelBot/1.0"}
    seen: set[str] = set()
    for url in WEB_FEEDS:
        try:
            resp = await client.get(url, headers=headers, timeout=HTTP_TIMEOUT, follow_redirects=True)
            resp.raise_for_status()
            for item in parse_feed(resp.text, url):
                if not looks_like_airdrop(item.title):
                    continue
                key = item.title.lower()
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    Detection(
                        channel="website",
                        source_name=item.source or "web",
                        title=item.title,
                        url=item.url,
                        body=item.source,
                        published_at=item.published,
                    )
                )
        except Exception as exc:
            errors.append(f"web:{url}: {exc}")
    return hits, errors
