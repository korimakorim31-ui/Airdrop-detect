from __future__ import annotations

import copy
import re
from dataclasses import dataclass

import httpx

from .catalog import curated_airdrops
from .config import DAILY_PICK_LIMIT, HTTP_TIMEOUT
from .daily import DailyPick, daily_best
from .playbook import enrich_item
from .models import (
    CERTAINTY_RANK,
    SOURCE_CATALOG,
    SOURCE_CEX,
    SOURCE_DEFILLAMA,
    SOURCE_NEWS,
    SOURCE_TELEGRAM,
    SOURCE_WEBSITE,
    SOURCE_X,
    Airdrop,
    Link,
    Task,
)
from .sources.cex import fetch_cex_airdrops
from .sources.common import CATEGORY_TO_TYPE, Detection, classify_campaign, slugify
from .sources.defillama import LlamaHit, fetch_llama_candidates
from .sources.news import NewsHit, fetch_airdrop_news
from .sources.telegram import fetch_telegram_airdrops
from .sources.websites import fetch_website_airdrops
from .sources.x_source import fetch_x_airdrops

DEFAULT_TASKS_BY_CATEGORY = {
    "Dexs": [
        Task("Swap on the official app", "Use the project's own domain, not an aggregator ad."),
        Task("Provide liquidity", "Only size you can lose to IL and contract risk."),
        Task("Stay active over weeks", "One-day volume spikes look like Sybil flow."),
    ],
    "Derivatives": [
        Task("Trade on the official venue", "Small, real size. Leverage can wipe the farm."),
        Task("Check for a points season", "Only join a dashboard linked from official X / docs."),
    ],
    "Yield": [
        Task("Deposit only via official UI", "Verify the contract on the project's docs."),
        Task("Leave funds long enough to look organic", "In-and-out same block is a filter signal."),
    ],
    "Prediction Market": [
        Task("Trade real events", "Informed flow beats spam tickets."),
        Task("Make two-sided markets if rewards exist", "Limit orders are often the rewarded action."),
    ],
    "Launchpad": [
        Task("Use the official launchpad only", "Fake launchpads are drainers."),
    ],
    "CEX": [
        Task("Open the venue from the official app", "Binance / Bybit / OKX in-app announcement, not a Telegram forward."),
        Task("Read eligibility", "Hodler / Launchpool / Megadrop rules are written in the announcement."),
        Task("Use the listed product only", "Hold, subscribe, or trade the named pair. Ignore clone tokens."),
    ],
    "testnet": [
        Task("Use the official testnet docs", "Faucet + RPC from the project site, never a paid 'testnet airdrop' Telegram."),
        Task("Do the published flows", "Deploy, transact, bridge, or run a node — whatever the docs ask."),
        Task("Stay across seasons", "One-day faucet spam is the first thing Sybil filters drop."),
    ],
    "mainnet": [
        Task("Use official mainnet apps", "Bridge in, swap, and keep a real history over weeks."),
        Task("Avoid empty loops", "Same-block in-and-out looks like farming, not usage."),
    ],
    "trade": [
        Task("Trade on the official venue", "Real size you can lose. Wash volume is filtered."),
        Task("Track the points / volume season", "Only dashboards linked from official X or docs."),
        Task("Mix spot and perps if both count", "Read the rules — some seasons weight makers or perps only."),
    ],
    "bridge": [
        Task("Bridge via the official UI", "Canonical / Stargate / project bridge — not a random 'bridge airdrop' site."),
        Task("Leave assets on the destination", "Instant bridge-back is a common filter."),
        Task("Use more than one path if the ecosystem has them", "L2 native bridge + a partner app beats a single hop."),
    ],
    "liquidity": [
        Task("LP only size you can lose", "IL and contract risk are real."),
        Task("Pick fee-generating pools", "Idle deposits score worse than productive LP."),
    ],
    "stake": [
        Task("Stake through official docs", "Restaking / LST pages, not clone tokens."),
        Task("Understand unbonding", "Do not stake funds you need this week."),
    ],
    "points": [
        Task("Join the official points season", "Screenshot the official URL from X / docs."),
        Task("Do the listed actions only", "Random social-connect farms are drainers."),
    ],
    "default": [
        Task("Open the official site from X / docs", "Do not Google-ad your way into a clone."),
        Task("Use the product for its real purpose", "2026 drops filter empty checklist wallets."),
        Task("Never sign a 'claim' permit", "No official claim page unless the team posts it."),
    ],
}

TIER_INVESTOR_WORDS = (
    "a16z",
    "andreessen",
    "paradigm",
    "sequoia",
    "dragonfly",
    "polychain",
    "coinbase",
    "founders fund",
    "placeholder",
    "multicoin",
    "temasek",
    "softbank",
    "tether",
    "intercontinental",
)


@dataclass
class ScanResult:
    airdrops: list[Airdrop]
    news: list[NewsHit]
    detections: list[Detection]
    daily: list[DailyPick]
    new_slugs: list[str]
    errors: list[str]
    counts: dict[str, int]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def score_airdrop(item: Airdrop) -> int:
    score = 20
    score += CERTAINTY_RANK.get(item.certainty, 0) * 8
    score += {
        "airdrop_confirmed": 28,
        "token_confirmed": 22,
        "points_live": 18,
        "delayed": 12,
        "exploring": 10,
        "ended": 6,
        "rumored": 4,
        "auto_detected": 8,
        "in_the_news": 6,
    }.get(item.status, 0)
    if item.funding:
        score += min(20, 6 * len(item.funding))
    if any(any(w in inv.name.lower() for w in TIER_INVESTOR_WORDS) for inv in item.investors):
        score += 14
    if item.tvl_usd:
        if item.tvl_usd >= 100_000_000:
            score += 16
        elif item.tvl_usd >= 10_000_000:
            score += 10
        elif item.tvl_usd >= 1_000_000:
            score += 5
    if item.news_hits:
        score += min(10, 3 * len(item.news_hits))
    if SOURCE_DEFILLAMA in item.detected_from and SOURCE_CATALOG not in item.detected_from:
        score += 4
    if item.channel == "cex" or SOURCE_CEX in item.detected_from:
        score += 16
    if SOURCE_TELEGRAM in item.detected_from:
        score += 6
    if SOURCE_X in item.detected_from:
        score += 5
    if SOURCE_WEBSITE in item.detected_from:
        score += 4
    extra_channels = {c for c in item.detected_from if c not in {SOURCE_CATALOG}}
    if len(extra_channels) >= 2:
        score += 8
    return min(100, score)


def _match_catalog(hit_name: str, catalog: list[Airdrop]) -> Airdrop | None:
    needle = _norm(hit_name)
    if not needle:
        return None
    for item in catalog:
        if needle == _norm(item.name) or needle == _norm(item.slug):
            return item
        if needle in _norm(item.name) or _norm(item.name) in needle:
            return item
    return None


def _tasks_for(category: str, campaign_type: str = "") -> list[Task]:
    if campaign_type and campaign_type in DEFAULT_TASKS_BY_CATEGORY:
        return list(DEFAULT_TASKS_BY_CATEGORY[campaign_type])
    return list(DEFAULT_TASKS_BY_CATEGORY.get(category, DEFAULT_TASKS_BY_CATEGORY["default"]))


def campaign_for(item_text: str, category: str = "") -> str:
    return classify_campaign(item_text, category) or CATEGORY_TO_TYPE.get(category, "airdrop") or "other"


def llama_to_airdrop(hit: LlamaHit) -> Airdrop:
    links = []
    if hit.url:
        links.append(Link("Project site", hit.url))
    if hit.twitter:
        links.append(Link("X / Twitter", f"https://x.com/{hit.twitter}"))
    links.append(Link("DefiLlama", f"https://defillama.com/protocol/{hit.slug}"))
    summary = hit.description or "No-token protocol picked up by the live DefiLlama detector."
    reason = "; ".join(hit.reasons)
    return Airdrop(
        slug=f"llama-{hit.slug}"[:60],
        name=hit.name,
        symbol=hit.symbol or "-",
        status="auto_detected",
        certainty="low",
        category=hit.category,
        chains=hit.chains or ([hit.chain] if hit.chain else []),
        summary=f"{summary} Detector: {reason}. No token on DefiLlama — possible future drop, not a promise.",
        reward="Unknown. No-token + TVL / new listing is only a hint.",
        eligibility="Use the real product if you already want it. Do not farm empty wallets.",
        tasks=_tasks_for(hit.category, campaign_for(f"{hit.name} {hit.category} {hit.description}", hit.category)),
        funding=[],
        investors=[],
        links=links,
        sources=["DefiLlama protocols API"],
        risk_notes=[
            "Auto-detected. Funding and investors are unknown until you verify primary sources.",
            "New listings include junk. Confirm the domain on official socials.",
        ],
        twitter=hit.twitter,
        tvl_usd=hit.tvl_usd,
        tvl_change_7d=hit.tvl_change_7d,
        listed_at=hit.listed_at,
        detected_from=[SOURCE_DEFILLAMA],
        last_verified="live scan",
        channel="defi",
        campaign_type=campaign_for(f"{hit.name} {hit.category} {hit.description}", hit.category),
    )


def detection_to_airdrop(det: Detection) -> Airdrop:
    name = (det.project_guess or det.title).strip()[:80] or det.source_name
    channel = det.channel if det.channel in {"cex", "telegram", "x", "website"} else "news"
    category = {
        "cex": "CEX",
        "telegram": "Telegram",
        "x": "X",
        "website": "Website",
    }.get(channel, "News")
    ctype = det.campaign_type or campaign_for(det.blob(), category)
    tasks = _tasks_for(category if channel == "cex" else ctype, ctype)
    return Airdrop(
        slug=f"{channel}-{slugify(det.source_name + '-' + det.title)}"[:60],
        name=name,
        symbol="-",
        status="auto_detected" if channel != "cex" else "points_live",
        certainty="medium" if channel == "cex" else "low",
        category=category,
        chains=["CEX"] if channel == "cex" else [],
        summary=det.body or det.title,
        reward="See official announcement. Size is only confirmed in the venue post.",
        eligibility="Follow the official rules for this campaign type (testnet, mainnet, trade, bridge, CEX, points).",
        tasks=tasks,
        funding=[],
        investors=[],
        links=[Link(det.source_name, det.url)] if det.url else [],
        sources=[det.source_name],
        risk_notes=[
            "Verify the announcement inside the official app.",
            "Telegram / X forwards are the #1 drain vector. Do not tap claim links in replies.",
        ],
        detected_from=[channel],
        last_verified="live scan",
        channel=channel,  # type: ignore[arg-type]
        origin_url=det.url,
        origin_title=det.title,
        published_at=det.published_at,
        campaign_type=ctype,
    )


def attach_detections(items: list[Airdrop], detections: list[Detection]) -> list[Airdrop]:
    extras: list[Airdrop] = []
    for det in detections:
        matched = _match_catalog(det.title, items) or _match_catalog(det.project_guess, items)
        if matched:
            line = f"{det.source_name}: {det.title}"
            if line not in matched.news_hits:
                matched.news_hits.append(line)
            if det.channel not in matched.detected_from:
                matched.detected_from.append(det.channel)
            if det.url and not any(l.url == det.url for l in matched.links):
                matched.links.append(Link(det.source_name, det.url))
            if det.campaign_type and det.campaign_type != "other":
                matched.campaign_type = det.campaign_type
            continue
        extras.append(detection_to_airdrop(det))
    return extras


def attach_news(items: list[Airdrop], news: list[NewsHit]) -> None:
    for item in items:
        blob_names = [_norm(item.name), _norm(item.slug), _norm(item.symbol)]
        for hit in news:
            title_n = _norm(hit.title)
            if any(n and n in title_n for n in blob_names if len(n) >= 4):
                line = f"{hit.title} ({hit.source})"
                if line not in item.news_hits:
                    item.news_hits.append(line)
                if SOURCE_NEWS not in item.detected_from:
                    item.detected_from.append(SOURCE_NEWS)


def merge(
    catalog: list[Airdrop],
    llama: list[LlamaHit],
    news: list[NewsHit],
    detections: list[Detection] | None = None,
) -> list[Airdrop]:
    items = [copy.deepcopy(x) for x in catalog]
    for item in items:
        if SOURCE_CATALOG not in item.detected_from:
            item.detected_from.insert(0, SOURCE_CATALOG)

    by_name = {_norm(i.name): i for i in items}
    extras: list[Airdrop] = []
    for hit in llama:
        existing = _match_catalog(hit.name, items) or by_name.get(_norm(hit.name))
        if existing:
            existing.tvl_usd = hit.tvl_usd
            existing.tvl_change_7d = hit.tvl_change_7d
            existing.listed_at = hit.listed_at or existing.listed_at
            if hit.twitter and not existing.twitter:
                existing.twitter = hit.twitter
            if SOURCE_DEFILLAMA not in existing.detected_from:
                existing.detected_from.append(SOURCE_DEFILLAMA)
            if existing.channel == "catalog":
                existing.channel = "defi"
            continue
        extras.append(llama_to_airdrop(hit))

    extras.sort(key=lambda x: x.tvl_usd or 0, reverse=True)
    items.extend(extras[:40])
    attach_news(items, news)
    extra_dets = attach_detections(items, detections or [])
    seen_titles: set[str] = set()
    unique_extra: list[Airdrop] = []
    for extra in extra_dets:
        key = _norm(extra.origin_title or extra.name)[:80]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        unique_extra.append(extra)
    items.extend(unique_extra[:80])

    for item in items:
        enrich_item(item)
        item.score = score_airdrop(item)
    items.sort(key=lambda x: (x.score, x.tvl_usd or 0), reverse=True)
    return items


async def run_scan() -> ScanResult:
    errors: list[str] = []
    llama: list[LlamaHit] = []
    news: list[NewsHit] = []
    detections: list[Detection] = []
    headers = {"User-Agent": "AirdropIntelBot/1.0 (+research)"}
    async with httpx.AsyncClient(headers=headers, timeout=HTTP_TIMEOUT) as client:
        try:
            llama = await fetch_llama_candidates(client)
        except Exception as exc:
            errors.append(f"DefiLlama: {exc}")
        try:
            news = await fetch_airdrop_news(client)
        except Exception as exc:
            errors.append(f"News: {exc}")
        try:
            cex_hits, cex_err = await fetch_cex_airdrops(client)
            detections.extend(cex_hits)
            errors.extend(cex_err)
        except Exception as exc:
            errors.append(f"CEX: {exc}")
        try:
            tg_hits, tg_err = await fetch_telegram_airdrops(client)
            detections.extend(tg_hits)
            errors.extend(tg_err)
        except Exception as exc:
            errors.append(f"Telegram: {exc}")
        try:
            x_hits, x_err = await fetch_x_airdrops(client)
            detections.extend(x_hits)
            errors.extend(x_err)
        except Exception as exc:
            errors.append(f"X: {exc}")
        try:
            web_hits, web_err = await fetch_website_airdrops(client)
            detections.extend(web_hits)
            errors.extend(web_err)
        except Exception as exc:
            errors.append(f"Website: {exc}")
    items = merge(curated_airdrops(), llama, news, detections)
    picks = daily_best(items, limit=DAILY_PICK_LIMIT)
    counts = {
        "airdrops": len(items),
        "llama": len(llama),
        "news": len(news),
        "detections": len(detections),
        "cex": sum(1 for d in detections if d.channel == "cex"),
        "telegram": sum(1 for d in detections if d.channel == "telegram"),
        "x": sum(1 for d in detections if d.channel == "x"),
        "website": sum(1 for d in detections if d.channel == "website"),
        "daily": len(picks),
    }
    return ScanResult(
        airdrops=items,
        news=news,
        detections=detections,
        daily=picks,
        new_slugs=[],
        errors=errors,
        counts=counts,
    )


def find_airdrop(items: list[Airdrop], query: str) -> Airdrop | None:
    q = (query or "").strip().lower()
    if not q:
        return None
    qn = _norm(q)
    exact = [i for i in items if i.slug == q or i.name.lower() == q or _norm(i.symbol) == qn]
    if exact:
        return exact[0]
    scored: list[tuple[int, Airdrop]] = []
    for item in items:
        blob = item.search_blob()
        if q in blob or qn in _norm(blob):
            scored.append((item.score, item))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def search_airdrops(items: list[Airdrop], query: str, limit: int = 10) -> list[Airdrop]:
    q = (query or "").strip().lower()
    if not q:
        return items[:limit]
    hits = [i for i in items if q in i.search_blob()]
    return hits[:limit]
