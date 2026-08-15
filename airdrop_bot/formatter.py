from __future__ import annotations

from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from .models import STATUS_LABEL, Airdrop, money
from .playbook import CAPITAL_LABEL, EFFORT_LABEL
from .safety import DISCLAIMER
from .sources.common import TYPE_LABEL


def h(text: str | None) -> str:
    return escape(text or "", quote=False)


def chunk(text: str, limit: int = 3900) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    for line in text.split("\n"):
        extra = len(line) + 1
        if buf and size + extra > limit:
            parts.append("\n".join(buf))
            buf = [line]
            size = extra
        else:
            buf.append(line)
            size += extra
    if buf:
        parts.append("\n".join(buf))
    return parts


def status_line(item: Airdrop) -> str:
    label = STATUS_LABEL.get(item.status, item.status.upper())
    return f"{label} · certainty {item.certainty} · score {item.score}/100"


def list_card(items: list[Airdrop], title: str, note: str = "") -> str:
    lines = [f"<b>{h(title)}</b>"]
    if note:
        lines.append(h(note))
    lines.append("")
    for i, item in enumerate(items, 1):
        tvl = f" · TVL {money(item.tvl_usd)}" if item.tvl_usd else ""
        ch = f" · {item.channel}" if item.channel and item.channel != "catalog" else ""
        kind = TYPE_LABEL.get(item.campaign_type, item.campaign_type or "")
        kind_bit = f" · {kind}" if kind else ""
        cost = CAPITAL_LABEL.get(item.capital, item.capital)
        lines.append(
            f"{i}. <b>{h(item.name)}</b> [{h(item.symbol)}] — {h(status_line(item))}{tvl}"
        )
        lines.append(
            f"    {h(item.category)}{h(ch)}{h(kind_bit)} · {h(cost)} · {h(', '.join(item.chains[:3]) or 'n/a')}"
        )
    lines.append("")
    lines.append(f"<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def detail_card(item: Airdrop) -> str:
    chains = ", ".join(item.chains) or "n/a"
    sources = ", ".join(item.detected_from) or "catalog"
    lines = [
        f"<b>{h(item.name)}</b> · {h(item.symbol)}",
        h(status_line(item)),
        f"{h(item.category)} · {h(TYPE_LABEL.get(item.campaign_type, item.campaign_type))} · {h(chains)}",
        f"Sources: {h(sources)} · verified {h(item.last_verified or 'n/a')}",
        (
            f"Cost: {h(CAPITAL_LABEL.get(item.capital, item.capital))} · "
            f"time: {h(EFFORT_LABEL.get(item.effort, item.effort))}"
            + (f" · date: {h(item.deadline)}" if item.deadline else "")
        ),
    ]
    if item.playbook:
        lines.append(f"Do this: {h(item.playbook)}")
    if item.tvl_usd is not None:
        chg = ""
        if item.tvl_change_7d is not None:
            chg = f" ({item.tvl_change_7d:+.1f}% 7d)"
        lines.append(f"TVL: {money(item.tvl_usd)}{h(chg)}")
    lines += ["", h(item.summary), "", f"<b>Reward</b>\n{h(item.reward)}"]
    lines.append(f"\n<b>Eligibility</b>\n{h(item.eligibility)}")
    if item.funding:
        lines.append("\n<b>Funding</b>")
        for rnd in item.funding:
            lead = f" · lead {rnd.lead}" if rnd.lead else ""
            extra = f" — {rnd.note}" if rnd.note else ""
            lines.append(f"• {h(rnd.amount)} ({h(rnd.date)} {h(rnd.round_name)}{h(lead)}){h(extra)}")
    if item.investors:
        names = ", ".join(f"{inv.name}" + (f" [{inv.role}]" if inv.role else "") for inv in item.investors)
        lines.append(f"\n<b>Investors</b>\n{h(names)}")
    if item.links:
        lines.append("\n<b>Official / research links</b>")
        for link in item.links:
            lines.append(f'• <a href="{escape(link.url, quote=True)}">{h(link.label)}</a>')
    if item.news_hits:
        lines.append("\n<b>Recent headlines</b>")
        for hit in item.news_hits[:4]:
            lines.append(f"• {h(hit)}")
    if item.risk_notes:
        lines.append("\n<b>Risk</b>")
        for note in item.risk_notes:
            lines.append(f"• {h(note)}")
    if item.sources:
        lines.append("\n<i>Refs: " + h("; ".join(item.sources[:4])) + "</i>")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def tasks_card(item: Airdrop) -> str:
    lines = [f"<b>Tasks — {h(item.name)}</b>", ""]
    for i, task in enumerate(item.tasks, 1):
        off = "official-path" if task.official else "unverified"
        lines.append(f"{i}. <b>{h(task.title)}</b> [{h(off)} · {h(task.cost)}]")
        lines.append(f"    {h(task.detail)}")
    if not item.tasks:
        lines.append("No published checklist. Use the product only if you already want it.")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def fund_card(item: Airdrop) -> str:
    lines = [f"<b>Funding — {h(item.name)}</b>", ""]
    if not item.funding:
        lines.append("No verified raise card in the catalog. Check the official blog / DefiLlama Raises.")
    for rnd in item.funding:
        lines.append(f"<b>{h(rnd.amount)}</b> · {h(rnd.date)} · {h(rnd.round_name or 'round')}")
        if rnd.lead:
            lines.append(f"Lead: {h(rnd.lead)}")
        if rnd.note:
            lines.append(h(rnd.note))
        lines.append("")
    lines.append(f"<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def investors_card(item: Airdrop) -> str:
    lines = [f"<b>Investors — {h(item.name)}</b>", ""]
    if not item.investors:
        lines.append("Investor book unknown on this record. Do not trust random 'backed by a16z' banners.")
    for inv in item.investors:
        role = f" — {inv.role}" if inv.role else ""
        lines.append(f"• {h(inv.name)}{h(role)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def reward_card(item: Airdrop) -> str:
    return "\n".join(
        [
            f"<b>Reward — {h(item.name)}</b>",
            h(status_line(item)),
            "",
            h(item.reward),
            "",
            f"<b>Eligibility</b>\n{h(item.eligibility)}",
            f"\n<i>{h(DISCLAIMER)}</i>",
        ]
    )


def news_card(rows: list, title: str = "Airdrop headlines") -> str:
    lines = [f"<b>{h(title)}</b>", ""]
    if not rows:
        lines.append("No airdrop headlines pulled this scan.")
    for i, hit in enumerate(rows[:12], 1):
        lines.append(f'{i}. <a href="{escape(hit.url, quote=True)}">{h(hit.title)}</a>')
        extra = " · ".join(x for x in (hit.source, hit.published) if x)
        if extra:
            lines.append(f"    {h(extra)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def daily_card(picks, title: str = "Best airdrops today") -> str:
    lines = [
        f"<b>{h(title)}</b>",
        "Ranked from CEX + Telegram + X + websites + DefiLlama + catalog.",
        "",
    ]
    if not picks:
        lines.append("No daily board yet. Run /scan.")
    for pick in picks:
        item = pick.item
        lines.append(
            f"{pick.rank}. <b>{h(item.name)}</b> — {item.score}/100 · {h(item.channel)}"
        )
        lines.append(f"    {h(pick.reason)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def detections_card(rows, title: str) -> str:
    lines = [f"<b>{h(title)}</b>", ""]
    if not rows:
        lines.append("Nothing matched airdrop keywords on this channel this scan.")
    for i, det in enumerate(rows[:12], 1):
        label = det.title[:140]
        if det.url:
            lines.append(f'{i}. <a href="{escape(det.url, quote=True)}">{h(label)}</a>')
        else:
            lines.append(f"{i}. {h(label)}")
        lines.append(f"    {h(det.source_name)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def safety_help() -> str:
    return (
        "<b>Airdrop safety</b>\n\n"
        "1. Real drops never ask for a seed phrase or private key.\n"
        "2. Open the official site from the project's X / docs. Do not click claim ads.\n"
        "3. Use a burner wallet. Never approve unlimited spends for a 'claim'.\n"
        "4. If a stranger DMs 'you are selected', it is a drain.\n"
        "5. This bot is research. It does not connect to your wallet.\n\n"
        "Paste any suspicious text or URL here with /check\n"
        f"<i>{h(DISCLAIMER)}</i>"
    )


KIND_BADGE = {
    "cex": "🏦 NEW CEX CAMPAIGN",
    "telegram": "📣 NEW TELEGRAM CAMPAIGN",
    "x": "𝕏 NEW X CAMPAIGN",
    "website": "🌐 NEW WEBSITE CAMPAIGN",
    "airdrop": "🪂 NEW AIRDROP",
    "testnet": "🧪 NEW TESTNET",
    "mainnet": "🟩 NEW MAINNET",
    "trade": "📈 NEW TRADE-VOLUME CAMPAIGN",
    "bridge": "🌉 NEW BRIDGE CAMPAIGN",
    "liquidity": "💧 NEW LP / LIQUIDITY",
    "stake": "🔒 NEW STAKE / RESTAKING",
    "points": "⭐ NEW POINTS SEASON",
    "daily": "⭐ DAILY BEST",
}


def alert_card(item: Airdrop, kind: str) -> str:
    badge = KIND_BADGE.get(kind, "🔔 NEW DETECTION")
    return f"<b>{h(badge)}</b>\n\n" + detail_card(item)


def digest_card(alerts, extra: int = 0) -> str:
    lines = [
        "<b>🔔 New airdrops / CEX campaigns</b>",
        "Pushed automatically — you do not need to /scan.",
        "",
    ]
    for i, alert in enumerate(alerts, 1):
        item = alert.item
        badge = KIND_BADGE.get(alert.kind, alert.kind)
        lines.append(f"{i}. <b>{h(item.name)}</b> · {h(badge)}")
        if item.origin_title and item.origin_title != item.name:
            lines.append(f"    {h(item.origin_title[:140])}")
        elif item.summary:
            lines.append(f"    {h(item.summary[:140])}")
    if extra:
        lines.append(f"\n…and {extra} more this round. Open /new or /daily.")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def plan_card(plan) -> str:
    lines = [
        "<b>Today's plan</b>",
        "Best cheap, live, diversified actions. Skips /done and /skip.",
        "",
    ]
    if not plan:
        lines.append("Nothing actionable. /hot or /scan.")
    for step in plan:
        item = step.item
        lines.append(
            f"{step.rank}. <b>{h(item.name)}</b> · {h(TYPE_LABEL.get(item.campaign_type, item.campaign_type))} · "
            f"{h(CAPITAL_LABEL.get(item.capital, item.capital))}"
        )
        lines.append(f"    {h(step.action)}")
        lines.append(f"    {h(step.why)}")
    lines.append("\n/why name · /track name · /done name")
    lines.append(f"<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def why_card(item: Airdrop, bullets: list[str]) -> str:
    lines = [f"<b>Why {h(item.name)}</b>", h(status_line(item)), ""]
    for bullet in bullets:
        lines.append(f"• {h(bullet)}")
    if item.playbook:
        lines.append(f"\n<b>Cheapest path</b>\n{h(item.playbook)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def prefs_card(prefs) -> str:
    types = ", ".join(prefs.types)
    chains = ", ".join(prefs.chains)
    mode = "digest (one daily packet)" if prefs.digest else "instant (push as found)"
    return (
        "<b>Your filters</b>\n"
        f"Mode: {h(mode)}\n"
        f"Min score: {prefs.min_score}\n"
        f"Types: <code>{h(types)}</code>\n"
        f"Chains: <code>{h(chains)}</code>\n\n"
        "/digest on · /instant\n"
        "/filter testnet,cex,trade\n"
        "/minscore 60\n"
        "/chain base\n"
        f"<i>{h(DISCLAIMER)}</i>"
    )


def menu_text() -> str:
    from .commands import COMMANDS, GROUP_TITLE

    lines = ["<b>All commands</b>", "Tap / or use the keyboard under the chat.", ""]
    current = ""
    for cmd in COMMANDS:
        if cmd.group != current:
            current = cmd.group
            lines.append(f"\n<b>{GROUP_TITLE.get(current, current)}</b>")
        lines.append(f"/{cmd.name} — {h(cmd.desc)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def compare_card(a, b) -> str:
    def row(label: str, left: str, right: str) -> str:
        return f"<b>{h(label)}</b>\n{h(left)}\nvs\n{h(right)}\n"

    return "\n".join(
        [
            f"<b>Compare</b> {h(a.name)} vs {h(b.name)}",
            "",
            row("Type", f"{a.campaign_type} / {a.status}", f"{b.campaign_type} / {b.status}"),
            row("Score", f"{a.score}/100 · {a.certainty}", f"{b.score}/100 · {b.certainty}"),
            row("Reward", a.reward[:240], b.reward[:240]),
            row("Funding", a.funding[0].amount if a.funding else "unknown", b.funding[0].amount if b.funding else "unknown"),
            row(
                "Investors",
                ", ".join(i.name for i in a.investors[:4]) or "unknown",
                ", ".join(i.name for i in b.investors[:4]) or "unknown",
            ),
            row("Eligibility", a.eligibility[:200], b.eligibility[:200]),
            f"<i>{h(DISCLAIMER)}</i>",
        ]
    )


def stats_card(items, detections, counts: dict | None = None) -> str:
    by_type: dict[str, int] = {}
    by_ch: dict[str, int] = {}
    for item in items:
        by_type[item.campaign_type or "other"] = by_type.get(item.campaign_type or "other", 0) + 1
        by_ch[item.channel or "?"] = by_ch.get(item.channel or "?", 0) + 1
    det_ch: dict[str, int] = {}
    for det in detections:
        det_ch[det.channel] = det_ch.get(det.channel, 0) + 1
    lines = ["<b>Live snapshot</b>", f"Projects: {len(items)} · raw hits: {len(detections)}", ""]
    if counts:
        lines.append(
            f"Last scan mix: CEX {counts.get('cex', 0)} · TG {counts.get('telegram', 0)} · "
            f"X {counts.get('x', 0)} · web {counts.get('website', 0)}"
        )
        lines.append("")
    lines.append("<b>By campaign type</b>")
    for key, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        lines.append(f"• {h(TYPE_LABEL.get(key, key))}: {n}")
    lines.append("\n<b>By source channel</b>")
    for key, n in sorted(by_ch.items(), key=lambda kv: -kv[1]):
        lines.append(f"• {h(key)}: {n}")
    if det_ch:
        lines.append("\n<b>Raw detections</b>")
        for key, n in sorted(det_ch.items(), key=lambda kv: -kv[1]):
            lines.append(f"• {h(key)}: {n}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def status_card(
    *,
    alerts_on: bool,
    interval_min: int,
    counts: dict,
    errors: list[str],
    last_finished: str,
    subscribers: int,
) -> str:
    lines = [
        "<b>Watcher status</b>",
        f"Auto-push: {'ON' if alerts_on else 'OFF'} · scan every {interval_min} min",
        f"Subscribers: {subscribers}",
        f"Last scan: {h(last_finished or 'n/a')}",
        f"Records {counts.get('airdrops', 0)} · detections {counts.get('detections', 0)} · daily {counts.get('daily', 0)}",
        f"CEX {counts.get('cex', 0)} · TG {counts.get('telegram', 0)} · X {counts.get('x', 0)} · web {counts.get('website', 0)}",
    ]
    if errors:
        lines.append("\n<b>Source errors</b>")
        for err in errors[:6]:
            lines.append(f"• {h(err)}")
    lines.append("\nI keep scanning in the background. /mute pauses pings only.")
    lines.append(f"<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def tracker_card(rows, names: dict[str, str]) -> str:
    lines = ["<b>My campaigns</b>", ""]
    if not rows:
        lines.append("Empty. /track polymarket to save one.")
    for row in rows:
        slug = row["slug"]
        name = names.get(slug, slug)
        note = f" — {row['note']}" if row["note"] else ""
        lines.append(f"• <b>{h(name)}</b> [{h(row['state'])}]{h(note)}")
        lines.append(f"    /airdrop {h(slug)} · /done {h(slug)} · /skip {h(slug)}")
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def links_card(item) -> str:
    lines = [f"<b>Links — {h(item.name)}</b>", ""]
    if not item.links:
        lines.append("No official links on this record.")
    for link in item.links:
        lines.append(f'• <a href="{escape(link.url, quote=True)}">{h(link.label)}</a>')
    lines.append(f"\n<i>{h(DISCLAIMER)}</i>")
    return "\n".join(lines)


def about_text() -> str:
    return (
        "<b>Airdrop Intel Bot</b>\n"
        "Research desk for airdrop, testnet, mainnet, trade-volume, bridge, LP, "
        "stake, points, and CEX campaigns.\n\n"
        "It watches sources in the background and pushes new hits here. "
        "It never asks for a seed, never connects a wallet, never claims tokens.\n\n"
        "Tap the keyboard or /menu for every command.\n"
        f"<i>{h(DISCLAIMER)}</i>"
    )


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Plan"), KeyboardButton("Daily"), KeyboardButton("Hot")],
            [KeyboardButton("Testnet"), KeyboardButton("Trade"), KeyboardButton("Bridge")],
            [KeyboardButton("CEX"), KeyboardButton("TG"), KeyboardButton("X")],
            [KeyboardButton("My"), KeyboardButton("Menu"), KeyboardButton("Status")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def start_text() -> str:
    return (
        "<b>Airdrop Intel Bot</b>\n"
        "I watch CEX, Telegram, X, websites, and on-chain projects in the background.\n"
        "<b>New airdrop, testnet, mainnet, trade-volume, bridge, LP, stake, and CEX campaigns "
        "are pushed here automatically.</b> You do not need to /scan.\n\n"
        "Alerts are ON. /mute to pause · /unmute to resume.\n\n"
        "Use the buttons under the chat, or /menu for every command.\n"
        "/plan is the daily action list. /digest on stops spam.\n"
        "/why name · /filter testnet,cex · /export\n\n"
        f"<i>{h(DISCLAIMER)}</i>"
    )


def item_keyboard(slug: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Details", callback_data=f"d:{slug}"),
                InlineKeyboardButton("Tasks", callback_data=f"t:{slug}"),
            ],
            [
                InlineKeyboardButton("Fund", callback_data=f"f:{slug}"),
                InlineKeyboardButton("Investors", callback_data=f"i:{slug}"),
                InlineKeyboardButton("Reward", callback_data=f"r:{slug}"),
            ],
            [
                InlineKeyboardButton("Watch", callback_data=f"w:{slug}"),
                InlineKeyboardButton("Why", callback_data=f"y:{slug}"),
                InlineKeyboardButton("Track", callback_data=f"p:{slug}"),
                InlineKeyboardButton("Done", callback_data=f"o:{slug}"),
            ],
        ]
    )


def list_keyboard(items: list[Airdrop]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for item in items[:10]:
        row.append(InlineKeyboardButton(item.name[:28], callback_data=f"d:{item.slug}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton("Plan", callback_data="menu:plan"),
            InlineKeyboardButton("Daily", callback_data="menu:daily"),
            InlineKeyboardButton("Hot", callback_data="menu:hot"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton("CEX", callback_data="menu:cex"),
            InlineKeyboardButton("TG", callback_data="menu:tg"),
            InlineKeyboardButton("X", callback_data="menu:x"),
            InlineKeyboardButton("Web", callback_data="menu:web"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton("Testnet", callback_data="menu:testnet"),
            InlineKeyboardButton("Trade", callback_data="menu:trade"),
            InlineKeyboardButton("Bridge", callback_data="menu:bridge"),
            InlineKeyboardButton("My", callback_data="menu:my"),
        ]
    )
    return InlineKeyboardMarkup(rows)
