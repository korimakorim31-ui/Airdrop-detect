from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from .models import Airdrop
from .playbook import plan_score
from .sources.common import Detection


@dataclass
class DailyPick:
    pick_date: str
    rank: int
    slug: str
    score: int
    reason: str
    item: Airdrop


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def pick_reason(item: Airdrop) -> str:
    bits: list[str] = []
    if item.status in {"airdrop_confirmed", "token_confirmed", "points_live"}:
        bits.append(item.status.replace("_", " "))
    if item.channel == "cex":
        bits.append("official CEX campaign")
    if "telegram" in item.detected_from:
        bits.append("seen on official Telegram")
    if "x" in item.detected_from:
        bits.append("circulating on X")
    if item.funding:
        bits.append("has public funding")
    if item.investors:
        bits.append("named investors")
    if item.tvl_usd and item.tvl_usd >= 10_000_000:
        bits.append("material TVL")
    if len(item.detected_from) >= 3:
        bits.append("multi-source")
    if not bits:
        bits.append("highest remaining score today")
    return "; ".join(bits)


def daily_best(items: list[Airdrop], limit: int = 10, pick_date: date | None = None) -> list[DailyPick]:
    day = (pick_date or datetime.now(timezone.utc).date()).isoformat()
    ranked = sorted(items, key=lambda i: (plan_score(i), i.score, i.tvl_usd or 0), reverse=True)
    # Prefer live / confirmed / CEX over stale "ended" names for the daily board.
    live = [i for i in ranked if i.status != "ended"]
    pool = live or ranked
    picks: list[DailyPick] = []
    for idx, item in enumerate(pool[:limit], 1):
        picks.append(
            DailyPick(
                pick_date=day,
                rank=idx,
                slug=item.slug,
                score=item.score,
                reason=pick_reason(item),
                item=item,
            )
        )
    return picks


def detections_today(dets: list[Detection], day: str | None = None) -> list[Detection]:
    day = day or _today()
    out: list[Detection] = []
    for det in dets:
        stamp = (det.published_at or "")[:10]
        if not stamp or stamp == day:
            out.append(det)
    return out
