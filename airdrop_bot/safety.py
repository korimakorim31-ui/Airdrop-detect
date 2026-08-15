from __future__ import annotations

import re
from dataclasses import dataclass

SEED_RE = re.compile(
    r"\b(seed phrase|secret phrase|recovery phrase|mnemonic|private key|keystore password)\b",
    re.I,
)
CLAIM_RE = re.compile(
    r"\b(claim now|connect wallet to claim|airdrop is live|you have been selected)\b",
    re.I,
)
URL_RE = re.compile(r"https?://[^\s<>\"]+", re.I)

SUSPECT_HOST_BITS = (
    "airdrop-claim",
    "claim-airdrop",
    "free-token",
    "connect-wallet",
    "double-your",
    "walletconnect-verify",
    "secure-drop",
)

KNOWN_GOOD_HOSTS = {
    "polymarket.com",
    "metamask.io",
    "consensys.io",
    "base.org",
    "www.base.org",
    "bridge.base.org",
    "blog.base.org",
    "opensea.io",
    "backpack.app",
    "app.hyperliquid.xyz",
    "hyperliquid.xyz",
    "layerzero.network",
    "layerzero.foundation",
    "stargate.finance",
    "www.grass.io",
    "grass.io",
    "app.meteora.ag",
    "meteora.ag",
    "aztec.network",
    "megaeth.com",
    "www.megaeth.com",
    "abs.xyz",
    "app.n1.xyz",
    "rabby.io",
    "defillama.com",
    "x.com",
    "twitter.com",
    "docs.polymarket.com",
}


@dataclass
class SafetyReport:
    score: int
    verdict: str
    flags: list[str]


def host_of(url: str) -> str:
    url = url.strip()
    if "://" in url:
        rest = url.split("://", 1)[1]
    else:
        rest = url
    return rest.split("/")[0].split(":")[0].lower()


def check_text(text: str) -> SafetyReport:
    flags: list[str] = []
    score = 80
    if SEED_RE.search(text):
        flags.append("Asks for a seed phrase, mnemonic, or private key. Real airdrops never do this.")
        score -= 80
    if CLAIM_RE.search(text) and "official" not in text.lower():
        flags.append("Urgent claim language. Verify the domain on the project's official X, not a forwarded link.")
        score -= 20
    for url in URL_RE.findall(text):
        host = host_of(url)
        if any(bit in host for bit in SUSPECT_HOST_BITS):
            flags.append(f"Suspicious host pattern: {host}")
            score -= 30
        elif host not in KNOWN_GOOD_HOSTS and host.startswith("www.") and host[4:] not in KNOWN_GOOD_HOSTS:
            flags.append(f"Unknown host {host}. Open the official site first, then navigate from there.")
            score -= 10
        elif host not in KNOWN_GOOD_HOSTS and not host.startswith("www."):
            flags.append(f"Unknown host {host}. Open the official site first, then navigate from there.")
            score -= 10
    score = max(0, min(100, score))
    if score >= 70:
        verdict = "Looks like research text, not an obvious drain attempt."
    elif score >= 40:
        verdict = "Caution. Verify every URL on official channels before connecting a wallet."
    else:
        verdict = "Dangerous pattern. Do not connect a wallet or paste a seed."
    if not flags:
        flags.append("No obvious drain phrases detected. Still use a burner wallet for any farming.")
    return SafetyReport(score=score, verdict=verdict, flags=flags)


DISCLAIMER = (
    "Research only. Not financial advice. Never paste a seed phrase. "
    "This bot does not claim tokens, sign transactions, or ask for a wallet."
)
