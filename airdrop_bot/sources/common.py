from __future__ import annotations

import re
from dataclasses import dataclass, field

# First matching type wins. Keep specific types above generic "airdrop".
TYPE_HINTS: list[tuple[str, tuple[str, ...]]] = [
    (
        "testnet",
        (
            "testnet",
            "test-net",
            "incentivized testnet",
            "public testnet",
            "devnet",
            "testnet season",
            "testnet points",
            "faucet",
            "test ETH",
            "sepolia",
            "holesky",
        ),
    ),
    (
        "bridge",
        (
            "bridge",
            "bridging",
            "cross-chain",
            "cross chain",
            "canonical bridge",
            "stargate",
            "bridge-and-earn",
        ),
    ),
    (
        "trade",
        (
            "trade volume",
            "trading volume",
            "perp volume",
            "spot volume",
            "maker volume",
            "trading competition",
            "trade-to-earn",
            "trade to earn",
            "volume campaign",
            "perps campaign",
            "futures carnival",
            "token buzz",
            "trade to win",
        ),
    ),
    (
        "liquidity",
        (
            "provide liquidity",
            "liquidity mining",
            "lp incentive",
            "lp rewards",
            "dlmm",
            "add liquidity",
        ),
    ),
    (
        "stake",
        (
            "restake",
            "liquid staking",
            "staking season",
            "stake to earn",
            "validator",
        ),
    ),
    (
        "points",
        (
            "points season",
            "points program",
            "xp season",
            "loyalty points",
            "season 2",
            "season 3",
            "season 4",
        ),
    ),
    (
        "cex",
        (
            "hodler airdrop",
            "hodler",
            "launchpool",
            "launch pool",
            "launchpad",
            "megadrop",
            "jumpstart",
            "hodl and earn",
        ),
    ),
    (
        "mainnet",
        (
            "mainnet",
            "main-net",
            "mainnet launch",
            "mainnet alpha",
            "genesis mainnet",
            "onchain activity",
            "on-chain activity",
        ),
    ),
    (
        "airdrop",
        (
            "airdrop",
            "air drop",
            "token generation",
            " tge",
            "tge ",
            "token drop",
            "community allocation",
            "free token",
            "claim window",
            "snapshot",
            "reward pool",
        ),
    ),
]

SKIP_HINTS = (
    "maintenance",
    "tick size",
    "delist",
    "will delist",
    "suspend",
    "wallet maintenance",
    "system upgrade",
)

CATEGORY_TO_TYPE = {
    "Bridge": "bridge",
    "Canonical Bridge": "bridge",
    "Dexs": "trade",
    "Derivatives": "trade",
    "Perps": "trade",
    "Prediction Market": "trade",
    "Liquid Staking": "stake",
    "Liquid Restaking": "stake",
    "Restaking": "stake",
    "Yield": "liquidity",
    "Yield Aggregator": "liquidity",
    "Farm": "liquidity",
    "Chain": "mainnet",
    "Rollup": "mainnet",
    "CEX": "cex",
    "Launchpad": "cex",
}

TYPE_LABEL = {
    "testnet": "TESTNET",
    "mainnet": "MAINNET",
    "trade": "TRADE VOLUME",
    "bridge": "BRIDGE",
    "liquidity": "LIQUIDITY",
    "stake": "STAKE",
    "points": "POINTS",
    "cex": "CEX CAMPAIGN",
    "airdrop": "AIRDROP",
    "other": "CAMPAIGN",
}


def slugify(text: str, limit: int = 48) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (text or "item")[:limit]


def classify_campaign(text: str, category: str = "") -> str:
    blob = (text or "").lower()
    if any(skip in blob for skip in SKIP_HINTS) and "airdrop" not in blob and "testnet" not in blob:
        return ""
    for kind, hints in TYPE_HINTS:
        if any(hint in blob for hint in hints):
            return kind
    if category in CATEGORY_TO_TYPE:
        return CATEGORY_TO_TYPE[category]
    return ""


def looks_like_airdrop(text: str) -> bool:
    """True for any farmable campaign type, not only classic airdrops."""
    return bool(classify_campaign(text))


def looks_like_campaign(text: str, category: str = "") -> bool:
    return bool(classify_campaign(text, category))


def strip_tags(html: str) -> str:
    out: list[str] = []
    skip = False
    for ch in html or "":
        if ch == "<":
            skip = True
            continue
        if ch == ">":
            skip = False
            continue
        if not skip:
            out.append(ch)
    text = "".join(out)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    text = text.replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Detection:
    channel: str
    source_name: str
    title: str
    url: str
    body: str = ""
    published_at: str = ""
    project_guess: str = ""
    extra: dict = field(default_factory=dict)
    campaign_type: str = ""

    def __post_init__(self) -> None:
        if not self.campaign_type:
            self.campaign_type = classify_campaign(self.blob()) or "other"

    def blob(self) -> str:
        return f"{self.title} {self.body} {self.project_guess}"
