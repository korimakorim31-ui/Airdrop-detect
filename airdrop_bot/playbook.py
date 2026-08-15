from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from .models import Airdrop

TYPE_PROFILE = {
    "testnet": ("gas", "days", "Official faucet + the published testnet flows only."),
    "mainnet": ("low", "weeks", "Use official apps on mainnet. Consistency beats one weekend."),
    "trade": ("mid", "weeks", "Real volume on the official venue. Do not wash-trade."),
    "bridge": ("low", "days", "Official bridge in, leave funds on the destination."),
    "liquidity": ("high", "weeks", "LP only size you can lose to IL."),
    "stake": ("mid", "weeks", "Stake via official docs. Know the unbonding time."),
    "points": ("low", "weeks", "Official points dashboard only."),
    "cex": ("cex", "days", "Do it inside the official exchange app. Read the snapshot rules."),
    "airdrop": ("low", "days", "Official links only. No claim site until the team posts one."),
}

CAPITAL_LABEL = {
    "gas": "gas only",
    "low": "small ($0–100 + gas)",
    "mid": "medium (trade / hold size)",
    "high": "high (LP / serious size)",
    "cex": "CEX hold or trade",
    "unknown": "unknown",
}

EFFORT_LABEL = {
    "minutes": "minutes",
    "days": "days",
    "weeks": "weeks of history",
    "unknown": "unknown",
}

DATE_RE = re.compile(
    r"\b(20\d{2}-\d{2}-\d{2})\b"
    r"|\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,?\s*20\d{2})?)\b"
    r"|\b(Q[1-4]\s*20\d{2})\b",
    re.I,
)

CHAIN_ALIASES = {
    "eth": "ethereum",
    "ether": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "base": "base",
    "arb": "arbitrum",
    "arbitrum": "arbitrum",
    "op": "optimism",
    "optimism": "optimism",
    "polygon": "polygon",
    "matic": "polygon",
    "hl": "hyperliquid",
    "hyperliquid": "hyperliquid",
    "bnb": "bsc",
    "bsc": "bsc",
    "binance": "bsc",
}


@dataclass
class Prefs:
    digest: bool = False
    min_score: int = 0
    types: list[str] = field(default_factory=lambda: ["*"])
    chains: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class PlanItem:
    rank: int
    item: Airdrop
    why: str
    action: str


def extract_deadline(text: str) -> str:
    match = DATE_RE.search(text or "")
    if not match:
        return ""
    return next(g for g in match.groups() if g)


def infer_profile(item: Airdrop) -> tuple[str, str, str]:
    capital, effort, action = TYPE_PROFILE.get(
        item.campaign_type, ("unknown", "unknown", "Use the official product only.")
    )
    if item.channel == "cex":
        capital, effort, action = TYPE_PROFILE["cex"]
    if item.status == "ended":
        action = "Token already live. Do not chase fake claim pages."
    return capital, effort, action


def enrich_item(item: Airdrop) -> Airdrop:
    capital, effort, action = infer_profile(item)
    if not item.capital or item.capital == "unknown":
        item.capital = capital
    if not item.effort or item.effort == "unknown":
        item.effort = effort
    if not item.playbook:
        item.playbook = action
    if not item.deadline:
        blob = " ".join(
            [
                item.summary,
                item.reward,
                item.origin_title,
                item.eligibility,
                " ".join(item.news_hits),
            ]
        )
        item.deadline = extract_deadline(blob)
    return item


def why_now(item: Airdrop) -> list[str]:
    lines: list[str] = []
    if item.status in {"airdrop_confirmed", "token_confirmed", "points_live"}:
        lines.append(f"Status is {item.status.replace('_', ' ')} — not a random rumor.")
    elif item.channel == "cex":
        lines.append("Official CEX campaign. Snapshot rules live in the exchange app.")
    elif item.campaign_type == "testnet":
        lines.append("Testnet is cheap history. Gas-only if you use the official faucet.")
    elif item.funding or item.investors:
        lines.append("Public funding / named investors. Still not a guaranteed drop.")
    else:
        lines.append("Auto-detected. Treat as a hint until a primary source confirms it.")

    if item.capital in {"gas", "low", "cex"}:
        lines.append(f"Capital: {CAPITAL_LABEL.get(item.capital, item.capital)}. Cheap to position.")
    elif item.capital == "high":
        lines.append("Capital is high. Only size you can lose.")
    else:
        lines.append(f"Capital: {CAPITAL_LABEL.get(item.capital, item.capital)}.")

    if item.deadline:
        lines.append(f"Date in the copy: {item.deadline}. Verify on the official post.")
    elif item.risk_notes:
        lines.append(item.risk_notes[0])
    else:
        lines.append("No published deadline. Fake claim pages will appear first.")
    return lines[:3]


def plan_score(item: Airdrop) -> int:
    score = item.score
    if item.status == "ended":
        return 0
    if item.status in {"airdrop_confirmed", "token_confirmed", "points_live"}:
        score += 12
    if item.channel == "cex" or item.campaign_type == "cex":
        score += 10
    if item.campaign_type == "testnet":
        score += 8
    if item.capital in {"gas", "low", "cex"}:
        score += 8
    if item.capital == "high":
        score -= 6
    if item.deadline:
        score += 6
    if item.certainty == "low" and item.status == "rumored":
        score -= 10
    return score


def build_plan(items: list[Airdrop], skip: set[str] | None = None, limit: int = 5) -> list[PlanItem]:
    skip = skip or set()
    ranked = [i for i in items if i.slug not in skip and i.status != "ended"]
    ranked.sort(key=plan_score, reverse=True)
    picked: list[Airdrop] = []
    type_counts: dict[str, int] = {}
    for item in ranked:
        kind = item.campaign_type or "other"
        if type_counts.get(kind, 0) >= 2:
            continue
        picked.append(item)
        type_counts[kind] = type_counts.get(kind, 0) + 1
        if len(picked) >= limit:
            break
    if len(picked) < limit:
        for item in ranked:
            if item in picked:
                continue
            picked.append(item)
            if len(picked) >= limit:
                break
    out: list[PlanItem] = []
    for idx, item in enumerate(picked, 1):
        out.append(
            PlanItem(
                rank=idx,
                item=item,
                why=why_now(item)[0],
                action=item.playbook or infer_profile(item)[2],
            )
        )
    return out


def parse_prefs(digest: int = 0, min_score: int = 0, types: str = "*", chains: str = "*") -> Prefs:
    t = [x.strip().lower() for x in (types or "*").split(",") if x.strip()]
    c = [normalize_chain(x) for x in (chains or "*").split(",") if x.strip()]
    return Prefs(digest=bool(digest), min_score=int(min_score or 0), types=t or ["*"], chains=c or ["*"])


def normalize_chain(name: str) -> str:
    raw = (name or "").strip().lower()
    return CHAIN_ALIASES.get(raw, raw)


def matches_prefs(item: Airdrop, prefs: Prefs) -> bool:
    if item.score < prefs.min_score:
        return False
    if prefs.types and "*" not in prefs.types:
        if (item.campaign_type or "") not in prefs.types and item.channel not in prefs.types:
            return False
    if prefs.chains and "*" not in prefs.chains:
        item_chains = {normalize_chain(c) for c in item.chains}
        if item.channel == "cex":
            item_chains.add("cex")
        if item_chains and item_chains.isdisjoint(set(prefs.chains)):
            return False
    return True


def export_csv(items: list[Airdrop], title: str = "airdrops") -> tuple[str, bytes]:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "name",
            "slug",
            "type",
            "status",
            "score",
            "capital",
            "effort",
            "deadline",
            "chains",
            "reward",
            "playbook",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.name,
                item.slug,
                item.campaign_type,
                item.status,
                item.score,
                item.capital,
                item.effort,
                item.deadline,
                "|".join(item.chains),
                item.reward,
                item.playbook,
            ]
        )
    filename = f"{title}.csv"
    return filename, buf.getvalue().encode("utf-8")
