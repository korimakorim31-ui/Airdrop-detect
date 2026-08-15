from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx

from ..config import HTTP_TIMEOUT

LLAMA_PROTOCOLS = "https://api.llama.fi/protocols"

SKIP_CATEGORIES = {
    "CEX",
    "Canonical Bridge",
    "RWA",
    "Risk Curators",
    "CDP Manager",
    "Treasury Manager",
    "Liquidity Manager",
    "Basis Trading",
}

AIRDROP_CATEGORIES = {
    "Bridge",
    "Dexs",
    "Derivatives",
    "Yield",
    "Lending",
    "Farm",
    "Launchpad",
    "Prediction Market",
    "NFT Marketplace",
    "Liquid Restaking",
    "Restaking",
    "Perps",
    "Options",
    "Synthetics",
    "Privacy",
    "Chain",
    "Rollup",
    "Yield Aggregator",
    "DEX Aggregator",
    "Insurance",
    "Algo-Stables",
    "Uncollateralized Lending",
    "Liquidity Automation",
    "Indexes",
}

SKIP_NAME_BITS = (
    "wbtc",
    "staked eth",
    "staked sol",
    "bitcoin",
    "usyc",
    "usdt0",
    "usdc",
    "blackrock",
    "circle ",
    "invesco",
    "wisdomtree",
    "coinbase bridge",
    "base bridge",
)


@dataclass
class LlamaHit:
    slug: str
    name: str
    category: str
    chain: str
    chains: list[str]
    url: str
    twitter: str
    description: str
    tvl_usd: float
    tvl_change_7d: float | None
    listed_at: int | None
    symbol: str
    reasons: list[str] = field(default_factory=list)


def _is_no_token(symbol: str | None) -> bool:
    return (symbol or "").strip() in {"", "-", "—", "n/a", "N/A"}


def _skip_name(name: str) -> bool:
    low = name.lower()
    return any(bit in low for bit in SKIP_NAME_BITS)


def parse_protocols(raw: list[dict], now: float | None = None) -> list[LlamaHit]:
    now = now or time.time()
    hits: list[LlamaHit] = []
    for proto in raw:
        if not _is_no_token(proto.get("symbol")):
            continue
        name = (proto.get("name") or "").strip()
        if not name or _skip_name(name):
            continue
        category = proto.get("category") or ""
        if category in SKIP_CATEGORIES:
            continue
        tvl = float(proto.get("tvl") or 0)
        listed = proto.get("listedAt") or None
        age_days = ((now - listed) / 86400) if listed else 9999
        reasons: list[str] = []
        if category in AIRDROP_CATEGORIES and tvl >= 5_000_000:
            reasons.append("no-token protocol with material TVL")
        if listed and age_days <= 14:
            reasons.append(f"listed on DefiLlama {age_days:.0f}d ago")
        change = proto.get("change_7d")
        try:
            change_f = float(change) if change is not None else None
        except (TypeError, ValueError):
            change_f = None
        if change_f is not None and change_f >= 40 and tvl >= 1_000_000:
            reasons.append(f"TVL +{change_f:.0f}% over 7d")
        if not reasons:
            continue
        hits.append(
            LlamaHit(
                slug=proto.get("slug") or name.lower().replace(" ", "-"),
                name=name,
                category=category or "Unknown",
                chain=proto.get("chain") or "",
                chains=list(proto.get("chains") or []),
                url=proto.get("url") or "",
                twitter=(proto.get("twitter") or "").lstrip("@"),
                description=(proto.get("description") or "").strip(),
                tvl_usd=tvl,
                tvl_change_7d=change_f,
                listed_at=int(listed) if listed else None,
                symbol=proto.get("symbol") or "-",
                reasons=reasons,
            )
        )
    hits.sort(key=lambda h: (h.tvl_usd, 0 if h.listed_at else 0), reverse=True)
    return hits


async def fetch_llama_candidates(client: httpx.AsyncClient) -> list[LlamaHit]:
    resp = await client.get(LLAMA_PROTOCOLS, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        return []
    return parse_protocols(data)
