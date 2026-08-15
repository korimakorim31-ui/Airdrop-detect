from __future__ import annotations

import logging
from datetime import datetime, timezone

from .config import supabase_enabled
from .daily import DailyPick
from .models import Airdrop
from .sources.common import Detection
from .store import Store

log = logging.getLogger("airdrop-intel")


def airdrop_row(item: Airdrop) -> dict:
    payload = item.to_public_dict()
    return {
        "slug": item.slug,
        "name": item.name,
        "symbol": item.symbol,
        "status": item.status,
        "certainty": item.certainty,
        "category": item.category,
        "channel": item.channel,
        "chains": item.chains,
        "summary": item.summary,
        "reward": item.reward,
        "eligibility": item.eligibility,
        "tasks": payload["tasks"],
        "funding": payload["funding"],
        "investors": payload["investors"],
        "links": payload["links"],
        "sources": item.sources,
        "risk_notes": item.risk_notes,
        "twitter": item.twitter,
        "tvl_usd": item.tvl_usd,
        "score": item.score,
        "detected_from": item.detected_from,
        "news_hits": item.news_hits,
        "origin_url": item.origin_url,
        "origin_title": item.origin_title,
        "published_at": item.published_at or None,
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }


def persist_scan(
    store: Store,
    items: list[Airdrop],
    detections: list[Detection],
    picks: list[DailyPick],
    errors: list[str],
    started: float,
) -> dict[str, int]:
    counts = {
        "airdrops": len(items),
        "detections": len(detections),
        "daily_picks": len(picks),
    }
    for item in items:
        store.upsert_airdrop(
            item.slug,
            item.name,
            item.to_public_dict(),
            item.score,
            item.channel,
        )
        store.upsert_seen(item.slug, {"name": item.name, "status": item.status, "score": item.score})
    for det in detections:
        if not det.title or det.title == "source-errors":
            continue
        store.insert_detection(det.channel, det.source_name, det.title, det.url, det.body, det.published_at)
    if picks:
        store.replace_daily_picks(
            picks[0].pick_date,
            [
                {
                    "rank": p.rank,
                    "slug": p.slug,
                    "score": p.score,
                    "reason": p.reason,
                    "payload": p.item.to_public_dict(),
                }
                for p in picks
            ],
        )
    store.log_scan(counts, errors, started)

    if supabase_enabled():
        try:
            pushed = _push_supabase(items, detections, picks, errors, counts)
            counts["supabase"] = pushed
        except Exception:
            log.exception("supabase persist failed")
            counts["supabase"] = 0
    return counts


def _push_supabase(
    items: list[Airdrop],
    detections: list[Detection],
    picks: list[DailyPick],
    errors: list[str],
    counts: dict,
) -> int:
    from .supabase_db import get_client

    client = get_client()
    if client is None:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    rows = [airdrop_row(i) for i in items]
    for chunk in _chunks(rows, 40):
        client.table("airdrops").upsert(chunk, on_conflict="slug").execute()
    det_rows = []
    for det in detections:
        if not det.title or det.title == "source-errors":
            continue
        det_rows.append(
            {
                "channel": det.channel,
                "source_name": det.source_name,
                "title": det.title,
                "url": det.url,
                "body": det.body,
                "published_at": det.published_at or None,
                "seen_at": now,
            }
        )
    for chunk in _chunks(det_rows, 40):
        client.table("detections").upsert(chunk, on_conflict="channel,url,title").execute()
    if picks:
        pick_date = picks[0].pick_date
        client.table("daily_picks").delete().eq("pick_date", pick_date).execute()
        client.table("daily_picks").insert(
            [
                {
                    "pick_date": p.pick_date,
                    "rank": p.rank,
                    "slug": p.slug,
                    "score": p.score,
                    "reason": p.reason,
                    "snapshot": p.item.to_public_dict(),
                }
                for p in picks
            ]
        ).execute()
    client.table("scans").insert(
        {
            "started_at": now,
            "finished_at": now,
            "counts": counts,
            "errors": errors,
        }
    ).execute()
    return len(rows)


def _chunks(rows: list, size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]
