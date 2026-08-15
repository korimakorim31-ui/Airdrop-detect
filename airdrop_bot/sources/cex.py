from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from ..config import HTTP_TIMEOUT
from .common import Detection, looks_like_airdrop

BINANCE_CMS = (
    "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    "?type=1&pageNo=1&pageSize=20&catalogId={catalog}"
)
BYBIT_ANN = "https://api.bybit.com/v5/announcements/index?locale=en-US&limit=20"
OKX_ANN = "https://www.okx.com/api/v5/support/announcements?annType={kind}"

OKX_KINDS = (
    "announcements-new-listings",
)

CEX_STRONG = (
    "airdrop",
    "hodler",
    "launchpool",
    "launch pad",
    "launchpad",
    "megadrop",
    "jumpstart",
    "token generation",
    "tge",
    "points season",
    "community allocation",
    "trading competition",
    "trade to earn",
    "trade-to-earn",
    "token buzz",
    "volume campaign",
    "testnet",
)


def _cex_airdrop_copy(text: str) -> bool:
    blob = (text or "").lower()
    if "apr" in blob and "airdrop" not in blob:
        return False
    return any(word in blob for word in CEX_STRONG) or looks_like_airdrop(blob)


def _iso_ms(value: str | int | None) -> str:
    if value in (None, ""):
        return ""
    try:
        ms = int(value)
        if ms > 10_000_000_000:
            ms //= 1000
        return datetime.fromtimestamp(ms, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def parse_binance(payload: dict) -> list[Detection]:
    out: list[Detection] = []
    for catalog in (payload.get("data") or {}).get("catalogs") or []:
        cat_name = catalog.get("catalogName") or "Binance"
        for art in catalog.get("articles") or []:
            title = art.get("title") or ""
            code = art.get("code") or art.get("id") or ""
            url = f"https://www.binance.com/en/support/announcement/{code}" if code else "https://www.binance.com/en/support/announcement"
            blob = f"{title} {cat_name}"
            if not _cex_airdrop_copy(blob):
                continue
            out.append(
                Detection(
                    channel="cex",
                    source_name="Binance",
                    title=title,
                    url=url,
                    body=cat_name,
                    published_at=_iso_ms(art.get("releaseDate") or art.get("publishDate")),
                    extra={"venue": "binance", "catalog": cat_name},
                )
            )
    return out


def parse_bybit(payload: dict) -> list[Detection]:
    out: list[Detection] = []
    rows = ((payload.get("result") or {}).get("list")) or []
    for row in rows:
        title = row.get("title") or ""
        desc = row.get("description") or ""
        kind = (row.get("type") or {}).get("key") or ""
        blob = f"{title} {desc} {kind}"
        if not _cex_airdrop_copy(blob):
            continue
        out.append(
            Detection(
                channel="cex",
                source_name="Bybit",
                title=title,
                url=row.get("url") or "https://announcements.bybit.com",
                body=desc,
                published_at=str(row.get("dateTimestamp") or row.get("publishTime") or ""),
                extra={"venue": "bybit", "type": kind},
            )
        )
    return out


def parse_okx(payload: dict, kind: str) -> list[Detection]:
    out: list[Detection] = []
    for block in payload.get("data") or []:
        for row in block.get("details") or []:
            title = row.get("title") or ""
            if not _cex_airdrop_copy(title):
                continue
            out.append(
                Detection(
                    channel="cex",
                    source_name="OKX",
                    title=title,
                    url=row.get("url") or "https://www.okx.com/help",
                    body=kind,
                    published_at=_iso_ms(row.get("pTime")),
                    extra={"venue": "okx", "ann_type": kind},
                )
            )
    return out


async def fetch_cex_airdrops(client: httpx.AsyncClient) -> list[Detection]:
    hits: list[Detection] = []
    errors: list[str] = []
    headers = {"User-Agent": "AirdropIntelBot/1.0", "Accept": "application/json"}

    for catalog in (49, 48, 161):
        try:
            resp = await client.get(BINANCE_CMS.format(catalog=catalog), headers=headers, timeout=HTTP_TIMEOUT)
            if resp.status_code == 200:
                hits.extend(parse_binance(resp.json()))
        except Exception as exc:
            errors.append(f"binance-{catalog}: {exc}")

    try:
        resp = await client.get(BYBIT_ANN, headers=headers, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        hits.extend(parse_bybit(resp.json()))
    except Exception as exc:
        errors.append(f"bybit: {exc}")

    for kind in OKX_KINDS:
        try:
            resp = await client.get(OKX_ANN.format(kind=kind), headers=headers, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            hits.extend(parse_okx(resp.json(), kind))
        except Exception as exc:
            errors.append(f"okx-{kind}: {exc}")

    # de-dupe by url/title
    seen: set[str] = set()
    unique: list[Detection] = []
    for hit in hits:
        key = (hit.url or hit.title).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    if errors:
        unique.append(
            Detection(
                channel="cex",
                source_name="cex-errors",
                title="source-errors",
                url="",
                body=json.dumps(errors),
                extra={"errors": errors},
            )
        )
    return [h for h in unique if h.source_name != "cex-errors"], errors
