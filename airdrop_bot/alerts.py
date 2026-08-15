from __future__ import annotations

from dataclasses import dataclass

from .models import Airdrop
from .scanner import detection_to_airdrop
from .sources.common import Detection, looks_like_campaign
from .store import Store

PUSH_DET_CHANNELS = {"cex", "telegram", "x", "website"}


@dataclass
class PushAlert:
    key: str
    kind: str
    item: Airdrop


def detection_key(det: Detection) -> str:
    raw = (det.url or det.title or "").strip().lower()
    return f"det:{det.channel}:{raw}"


def item_key(item: Airdrop) -> str:
    return f"air:{item.slug}"


def is_push_worthy_detection(det: Detection) -> bool:
    if not det.title or det.title == "source-errors":
        return False
    if det.channel == "cex":
        return True
    return looks_like_campaign(f"{det.title} {det.body}")


def is_push_worthy_item(item: Airdrop) -> bool:
    if item.channel == "cex" or "cex" in item.detected_from:
        return True
    if item.channel in {"telegram", "x", "website"}:
        return True
    if item.status == "auto_detected":
        return True
    return False


def collect_push_alerts(items: list[Airdrop], detections: list[Detection], store: Store) -> list[PushAlert]:
    """Return only never-pushed CEX / airdrop hits. First-seen keys are claimed here."""
    out: list[PushAlert] = []
    used_urls: set[str] = set()
    for det in detections:
        if not is_push_worthy_detection(det):
            continue
        key = detection_key(det)
        if not store.mark_alerted(key):
            continue
        matched = next(
            (i for i in items if det.url and i.origin_url == det.url),
            None,
        )
        item = matched or detection_to_airdrop(det)
        kind = item.campaign_type or det.campaign_type or det.channel
        out.append(PushAlert(key=key, kind=kind, item=item))
        if det.url:
            used_urls.add(det.url)
    for item in items:
        if not is_push_worthy_item(item):
            continue
        if item.origin_url and item.origin_url in used_urls:
            continue
        key = item_key(item)
        if not store.mark_alerted(key):
            continue
        kind = item.campaign_type or (
            "cex" if (item.channel == "cex" or "cex" in item.detected_from) else "airdrop"
        )
        out.append(PushAlert(key=key, kind=kind, item=item))
    return out


def baseline_keys(items: list[Airdrop], detections: list[Detection]) -> list[str]:
    keys = [detection_key(d) for d in detections if d.title and d.title != "source-errors"]
    keys.extend(item_key(i) for i in items)
    return keys
