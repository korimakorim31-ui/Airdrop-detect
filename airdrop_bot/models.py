from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal[
    "points_live",
    "token_confirmed",
    "airdrop_confirmed",
    "exploring",
    "delayed",
    "rumored",
    "auto_detected",
    "in_the_news",
    "ended",
]

SOURCE_CATALOG = "catalog"
SOURCE_DEFILLAMA = "defillama"
SOURCE_NEWS = "news"
SOURCE_CEX = "cex"
SOURCE_TELEGRAM = "telegram"
SOURCE_X = "x"
SOURCE_WEBSITE = "website"

Channel = Literal["catalog", "cex", "telegram", "x", "website", "defi", "news"]


@dataclass
class Task:
    title: str
    detail: str
    cost: str = "gas / time"
    official: bool = True


@dataclass
class FundingRound:
    amount: str
    date: str
    round_name: str = ""
    lead: str = ""
    note: str = ""


@dataclass
class Investor:
    name: str
    role: str = "investor"


@dataclass
class Link:
    label: str
    url: str


@dataclass
class Airdrop:
    slug: str
    name: str
    symbol: str
    status: Status
    certainty: str
    category: str
    chains: list[str]
    summary: str
    reward: str
    eligibility: str
    tasks: list[Task]
    funding: list[FundingRound]
    investors: list[Investor]
    links: list[Link]
    sources: list[str]
    risk_notes: list[str] = field(default_factory=list)
    twitter: str = ""
    tvl_usd: float | None = None
    tvl_change_7d: float | None = None
    listed_at: int | None = None
    score: int = 0
    detected_from: list[str] = field(default_factory=list)
    news_hits: list[str] = field(default_factory=list)
    last_verified: str = ""
    channel: Channel = "catalog"
    origin_url: str = ""
    origin_title: str = ""
    published_at: str = ""
    campaign_type: str = "airdrop"
    capital: str = "unknown"
    effort: str = "unknown"
    deadline: str = ""
    playbook: str = ""

    def search_blob(self) -> str:
        bits = [
            self.slug,
            self.name,
            self.symbol,
            self.category,
            self.channel,
            self.campaign_type,
            self.twitter,
            " ".join(self.chains),
            self.summary,
            self.origin_title,
        ]
        bits.extend(inv.name for inv in self.investors)
        bits.extend(self.detected_from)
        return " ".join(bits).lower()

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


STATUS_LABEL = {
    "points_live": "POINTS LIVE",
    "token_confirmed": "TOKEN CONFIRMED",
    "airdrop_confirmed": "AIRDROP CONFIRMED",
    "exploring": "EXPLORING TOKEN",
    "delayed": "DELAYED",
    "rumored": "RUMORED",
    "auto_detected": "AUTO-DETECTED",
    "in_the_news": "IN THE NEWS",
    "ended": "ENDED / TOKEN LIVE",
}

CERTAINTY_RANK = {
    "high": 4,
    "medium-high": 3,
    "medium": 2,
    "medium-low": 1,
    "low": 0,
}


def money(value: float | None) -> str:
    if value is None:
        return "n/a"
    abs_v = abs(value)
    if abs_v >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs_v >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"
