from __future__ import annotations

import re

import httpx

from ..config import HTTP_TIMEOUT
from .common import Detection, looks_like_airdrop, strip_tags

# Official or well-known public announcement channels (web preview, no login).
# Do not add random "airdrop call" groups — those are mostly drainers.
TG_CHANNELS = (
    "binance_announcements",
    "Bybit_Announcements",
    "OKXOfficial_EN",
    "Bitget_Announcement",
    "KuCoin_News",
    "gateio_news",
    "CoinMarketCapAnnouncements",
)

POST_RE = re.compile(r'data-post="([^"]+)"')
TEXT_RE = re.compile(
    r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
    re.I | re.S,
)
DATE_RE = re.compile(r'datetime="([^"]+)"')
HREF_RE = re.compile(r'href="(https://t\.me/[^"]+)"')


def parse_tg_html(html: str, channel: str) -> list[Detection]:
    chunks = re.split(r'class="tgme_widget_message_wrap', html)
    out: list[Detection] = []
    for chunk in chunks[1:]:
        post = POST_RE.search(chunk)
        text_m = TEXT_RE.search(chunk)
        text = strip_tags(text_m.group(1) if text_m else "")
        if not text:
            continue
        if not looks_like_airdrop(text):
            continue
        href = HREF_RE.search(chunk)
        url = href.group(1) if href else (f"https://t.me/{post.group(1)}" if post else f"https://t.me/s/{channel}")
        date_m = DATE_RE.search(chunk)
        title = text[:160]
        out.append(
            Detection(
                channel="telegram",
                source_name=f"t.me/{channel}",
                title=title,
                url=url,
                body=text[:800],
                published_at=date_m.group(1) if date_m else "",
                extra={"channel": channel},
            )
        )
    return out


async def fetch_telegram_airdrops(client: httpx.AsyncClient) -> tuple[list[Detection], list[str]]:
    hits: list[Detection] = []
    errors: list[str] = []
    headers = {"User-Agent": "AirdropIntelBot/1.0 (+research)"}
    for channel in TG_CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            resp = await client.get(url, headers=headers, timeout=HTTP_TIMEOUT, follow_redirects=True)
            if resp.status_code >= 400:
                errors.append(f"tg/{channel}: HTTP {resp.status_code}")
                continue
            hits.extend(parse_tg_html(resp.text, channel))
        except Exception as exc:
            errors.append(f"tg/{channel}: {exc}")
    return hits, errors
