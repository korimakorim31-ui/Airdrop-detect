from __future__ import annotations

import logging
from functools import wraps

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import ai, alerts, commands, config, formatter
from .persist import persist_scan
from .playbook import build_plan, export_csv, matches_prefs, normalize_chain, why_now
from .scanner import ScanResult, find_airdrop, run_scan, search_airdrops
from .safety import DISCLAIMER, check_text
from .store import Store

log = logging.getLogger("airdrop-intel")

WATCH_ALL = "*"


def allowed(update: Update) -> bool:
    if not config.ALLOWED_USER_IDS:
        return True
    user = update.effective_user
    return bool(user and user.id in config.ALLOWED_USER_IDS)


async def deny(update: Update) -> None:
    uid = update.effective_user.id if update.effective_user else "unknown"
    if update.callback_query:
        await update.callback_query.answer("Not on the allow list.", show_alert=True)
        return
    if update.effective_message:
        await update.effective_message.reply_text(
            f"Private bot. Your Telegram id ({uid}) is not on ALLOWED_USER_IDS."
        )


def guard(fn):
    @wraps(fn)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not allowed(update):
            await deny(update)
            return
        store: Store = ctx.application.bot_data["store"]
        user = update.effective_user
        if user:
            store.touch_user(user.id, user.username)
        try:
            if update.effective_chat:
                await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
            return await fn(update, ctx)
        except Exception:
            log.exception("handler %s failed", fn.__name__)
            if update.callback_query:
                await update.callback_query.answer("Something broke. Check logs.", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text("Something broke on my side. Check the console log.")

    return wrapper


async def send_html(
    update: Update,
    text: str,
    reply_markup=None,
    edit: bool = False,
) -> None:
    parts = formatter.chunk(text)
    if edit and update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(
            parts[0],
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
        for extra in parts[1:]:
            await update.callback_query.message.reply_html(extra, disable_web_page_preview=True)
        return
    msg = update.effective_message
    if not msg:
        return
    await msg.reply_html(parts[0], disable_web_page_preview=True, reply_markup=reply_markup)
    for extra in parts[1:]:
        await msg.reply_html(extra, disable_web_page_preview=True)


def cache(ctx: ContextTypes.DEFAULT_TYPE) -> ScanResult:
    result = ctx.application.bot_data.get("scan")
    if result is None:
        raise RuntimeError("scan cache empty")
    return result


async def persist_result(ctx: ContextTypes.DEFAULT_TYPE, result: ScanResult) -> None:
    store: Store = ctx.application.bot_data["store"]
    import time

    persist_scan(store, result.airdrops, result.detections, result.daily, result.errors, time.time())


async def ensure_scan(ctx: ContextTypes.DEFAULT_TYPE, force: bool = False) -> ScanResult:
    if force or "scan" not in ctx.application.bot_data:
        result = await run_scan()
        ctx.application.bot_data["scan"] = result
        await persist_result(ctx, result)
    return cache(ctx)


def arg(ctx: ContextTypes.DEFAULT_TYPE) -> str:
    return " ".join(ctx.args or []).strip()


def recipients(store: Store) -> list[int]:
    ids = store.subscribers()
    if config.ALLOWED_USER_IDS:
        ids = [i for i in ids if i in config.ALLOWED_USER_IDS]
    return ids


@guard
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if user:
        store.set_alerts(user.id, True)
    await ensure_scan(ctx)
    result = cache(ctx)
    await send_html(
        update,
        formatter.start_text(),
        reply_markup=formatter.main_keyboard(),
    )
    await cmd_plan(update, ctx)


@guard
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await send_html(update, formatter.menu_text(), reply_markup=formatter.main_keyboard())


@guard
async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await send_html(update, formatter.menu_text(), reply_markup=formatter.main_keyboard())


@guard
async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await send_html(update, formatter.about_text(), reply_markup=formatter.main_keyboard())


@guard
async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    uid = user.id if user else "?"
    await send_html(
        update,
        f"Your Telegram id is <code>{uid}</code>\n"
        "Put it in ALLOWED_USER_IDS if you want a private bot.",
    )


def _skip_slugs(store: Store, user_id: int | None) -> set[str]:
    if not user_id:
        return set()
    return {row["slug"] for row in store.tracks_for(user_id) if row["state"] in {"done", "skip"}}


@guard
async def cmd_plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    result = await ensure_scan(ctx)
    user = update.effective_user
    plan = build_plan(result.airdrops, skip=_skip_slugs(store, user.id if user else None), limit=5)
    await send_html(
        update,
        formatter.plan_card(plan),
        reply_markup=formatter.list_keyboard([p.item for p in plan]),
    )


@guard
async def cmd_why(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /why polymarket")
        return
    result = await ensure_scan(ctx)
    item = find_airdrop(result.airdrops, query)
    if not item:
        await send_html(update, f"No match for <code>{formatter.h(query)}</code>.")
        return
    await send_html(
        update,
        formatter.why_card(item, why_now(item)),
        reply_markup=formatter.item_keyboard(item.slug),
    )


@guard
async def cmd_prefs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    await send_html(update, formatter.prefs_card(store.get_prefs(user.id)))


@guard
async def cmd_digest(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    raw = arg(ctx).lower()
    on = raw not in {"off", "0", "false", "no"}
    prefs = store.set_prefs(user.id, digest=on)
    await send_html(update, formatter.prefs_card(prefs))


@guard
async def cmd_instant(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    prefs = store.set_prefs(user.id, digest=False)
    await send_html(update, formatter.prefs_card(prefs))


@guard
async def cmd_filter(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    raw = arg(ctx).lower() or "*"
    prefs = store.set_prefs(user.id, types=raw.replace(" ", ""))
    await send_html(update, formatter.prefs_card(prefs))


@guard
async def cmd_minscore(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    raw = arg(ctx)
    try:
        score = max(0, min(100, int(raw)))
    except ValueError:
        await send_html(update, "Usage: /minscore 60")
        return
    prefs = store.set_prefs(user.id, min_score=score)
    await send_html(update, formatter.prefs_card(prefs))


@guard
async def cmd_chain(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    raw = arg(ctx) or "*"
    parts = [normalize_chain(p) for p in raw.replace(" ", ",").split(",") if p]
    prefs = store.set_prefs(user.id, chains=",".join(parts) if parts else "*")
    await send_html(update, formatter.prefs_card(prefs))


async def _browse_chain(update: Update, ctx: ContextTypes.DEFAULT_TYPE, chain: str) -> None:
    result = await ensure_scan(ctx)
    key = normalize_chain(chain)
    hits = [
        i
        for i in result.airdrops
        if key in {normalize_chain(c) for c in i.chains} or key in normalize_chain(" ".join(i.chains))
    ][:12]
    await send_html(
        update,
        formatter.list_card(hits, f"Chain: {key}", "Browse only. /chain to lock auto-push to this chain."),
        reply_markup=formatter.list_keyboard(hits),
    )


@guard
async def cmd_base(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _browse_chain(update, ctx, "base")


@guard
async def cmd_solana(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _browse_chain(update, ctx, "solana")


@guard
async def cmd_eth(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _browse_chain(update, ctx, "ethereum")


@guard
async def cmd_hyperliquid_chain(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _browse_chain(update, ctx, "hyperliquid")


@guard
async def cmd_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    items = [p.item for p in result.daily] or result.airdrops[:15]
    name, data = export_csv(items, "airdrop-daily")
    if not update.effective_chat:
        return
    from io import BytesIO

    bio = BytesIO(data)
    bio.name = name
    await ctx.bot.send_document(
        update.effective_chat.id,
        document=bio,
        filename=name,
        caption="Today's board as CSV. Research only.",
    )


@guard
async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    items = [p.item for p in result.daily]
    await send_html(
        update,
        formatter.daily_card(result.daily),
        reply_markup=formatter.list_keyboard(items),
    )


@guard
async def cmd_hot(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    top = result.airdrops[:8]
    await send_html(
        update,
        formatter.list_card(top, "Hot airdrops", "Catalog + live DefiLlama no-token detections."),
        reply_markup=formatter.list_keyboard(top),
    )


@guard
async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    top = result.airdrops[:15]
    await send_html(
        update,
        formatter.list_card(top, "Top 15", "Highest score right now."),
        reply_markup=formatter.list_keyboard(top),
    )


@guard
async def cmd_confirmed(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    hits = [i for i in result.airdrops if i.status in {"airdrop_confirmed", "token_confirmed", "points_live"}][:12]
    await send_html(
        update,
        formatter.list_card(hits, "Confirmed / points live"),
        reply_markup=formatter.list_keyboard(hits),
    )


@guard
async def cmd_rumored(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    hits = [i for i in result.airdrops if i.status in {"rumored", "exploring", "delayed"}][:12]
    await send_html(
        update,
        formatter.list_card(hits, "Rumored / exploring / delayed"),
        reply_markup=formatter.list_keyboard(hits),
    )


@guard
async def cmd_new(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    fresh = [i for i in result.airdrops if i.status in {"auto_detected", "in_the_news"}][:8]
    if not fresh:
        fresh = [i for i in result.airdrops if "defillama" in i.detected_from][:8]
    text = formatter.list_card(fresh, "Live detections", "New or no-token protocols + news overlap.")
    text += "\n\n" + formatter.news_card(result.news[:8], "Headlines")
    await send_html(update, text, reply_markup=formatter.list_keyboard(fresh))


@guard
async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /search polymarket")
        return
    result = await ensure_scan(ctx)
    hits = search_airdrops(result.airdrops, query, limit=8)
    if not hits:
        await send_html(update, f"No match for <code>{formatter.h(query)}</code>.")
        return
    await send_html(
        update,
        formatter.list_card(hits, f"Search: {query}"),
        reply_markup=formatter.list_keyboard(hits),
    )


async def show_section(update: Update, ctx: ContextTypes.DEFAULT_TYPE, section: str, query: str) -> None:
    result = await ensure_scan(ctx)
    item = find_airdrop(result.airdrops, query)
    if not item:
        await send_html(update, f"No match for <code>{formatter.h(query)}</code>. Try /hot or /search.")
        return
    card = {
        "d": formatter.detail_card,
        "t": formatter.tasks_card,
        "f": formatter.fund_card,
        "i": formatter.investors_card,
        "r": formatter.reward_card,
        "l": formatter.links_card,
    }[section](item)
    await send_html(update, card, reply_markup=formatter.item_keyboard(item.slug), edit=bool(update.callback_query))


@guard
async def cmd_airdrop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /airdrop metamask")
        return
    await show_section(update, ctx, "d", query)


@guard
async def cmd_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /tasks base")
        return
    await show_section(update, ctx, "t", query)


@guard
async def cmd_fund(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /fund polymarket")
        return
    await show_section(update, ctx, "f", query)


@guard
async def cmd_investors(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /investors opensea")
        return
    await show_section(update, ctx, "i", query)


@guard
async def cmd_reward(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /reward backpack")
        return
    await show_section(update, ctx, "r", query)


@guard
async def cmd_links(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = arg(ctx)
    if not query:
        await send_html(update, "Usage: /links metamask")
        return
    await show_section(update, ctx, "l", query)


@guard
async def cmd_compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    import re

    raw = arg(ctx)
    if not raw:
        await send_html(update, "Usage: /compare polymarket vs metamask")
        return
    if re.search(r"\s+vs\s+", raw, re.I):
        left, right = re.split(r"\s+vs\s+", raw, maxsplit=1, flags=re.I)
    else:
        bits = raw.split()
        if len(bits) < 2:
            await send_html(update, "Usage: /compare polymarket vs metamask")
            return
        left, right = bits[0], bits[1]
    result = await ensure_scan(ctx)
    a = find_airdrop(result.airdrops, left.strip())
    b = find_airdrop(result.airdrops, right.strip())
    if not a or not b:
        await send_html(update, "Need two known names. Try /hot then /compare a vs b")
        return
    await send_html(update, formatter.compare_card(a, b), reply_markup=formatter.list_keyboard([a, b]))


@guard
async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    await send_html(update, formatter.news_card(result.news, "Headlines"))


@guard
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    await send_html(update, formatter.stats_card(result.airdrops, result.detections, result.counts))


@guard
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    from datetime import datetime, timezone

    store: Store = ctx.application.bot_data["store"]
    result = await ensure_scan(ctx)
    user = update.effective_user
    row = store.last_scan()
    last = ""
    if row:
        last = datetime.fromtimestamp(row["finished"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    await send_html(
        update,
        formatter.status_card(
            alerts_on=bool(user and store.alerts_on(user.id)),
            interval_min=config.SCAN_INTERVAL_MINUTES,
            counts=result.counts,
            errors=result.errors,
            last_finished=last,
            subscribers=len(store.subscribers()),
        ),
    )


@guard
async def cmd_recent(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    rows = store.recent_alerts(12)
    if not rows:
        await send_html(update, "No auto-pushed alerts yet. I only ping on <b>new</b> hits after startup.")
        return
    lines = ["<b>Recent auto-pushes</b>", ""]
    for row in rows:
        lines.append(f"• [{formatter.h(row['kind'])}] {formatter.h(row['message'])} — <code>{formatter.h(row['slug'])}</code>")
    await send_html(update, "\n".join(lines))


async def _set_track(update: Update, ctx: ContextTypes.DEFAULT_TYPE, state: str) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    query = arg(ctx)
    if not user or not query:
        await send_html(update, f"Usage: /{state} polymarket")
        return
    result = await ensure_scan(ctx)
    item = find_airdrop(result.airdrops, query)
    note = ""
    if not item:
        first, *rest = query.split(maxsplit=1)
        item = find_airdrop(result.airdrops, first)
        note = rest[0] if rest else ""
    if not item:
        await send_html(update, f"No match for <code>{formatter.h(query)}</code>.")
        return
    store.set_track(user.id, item.slug, state, note)
    await send_html(update, f"Saved <b>{formatter.h(item.name)}</b> as <code>{state}</code>. /my to see the list.")


@guard
async def cmd_track(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _set_track(update, ctx, "doing")


@guard
async def cmd_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _set_track(update, ctx, "done")


@guard
async def cmd_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _set_track(update, ctx, "skip")


@guard
async def cmd_my(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    rows = store.tracks_for(user.id)
    result = await ensure_scan(ctx)
    names = {i.slug: i.name for i in result.airdrops}
    items = [find_airdrop(result.airdrops, r["slug"]) for r in rows]
    items = [i for i in items if i]
    await send_html(
        update,
        formatter.tracker_card(rows, names),
        reply_markup=formatter.list_keyboard(items) if items else formatter.main_keyboard(),
    )


@guard
async def cmd_mute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    store.set_alerts(user.id, False)
    await send_html(update, "Auto-push is off. I still scan in the background. /unmute to get pings again.")


@guard
async def cmd_unmute(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    store.set_alerts(user.id, True)
    await send_html(update, "Auto-push is on. New airdrops and CEX campaigns will land here.")


@guard
async def cmd_watch(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    query = arg(ctx).lower()
    user = update.effective_user
    if not user:
        return
    if query in {"", "all", "*"}:
        store.watch(user.id, WATCH_ALL)
        await send_html(update, "Watching <b>all new detections</b>. /unwatch to stop.")
        return
    result = await ensure_scan(ctx)
    item = find_airdrop(result.airdrops, query)
    if not item:
        await send_html(update, f"No match for <code>{formatter.h(query)}</code>.")
        return
    store.watch(user.id, item.slug)
    await send_html(update, f"Watching <b>{formatter.h(item.name)}</b>.")


@guard
async def cmd_unwatch(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    query = arg(ctx)
    if not query:
        n = store.unwatch(user.id)
        await send_html(update, f"Cleared {n} watch(es).")
        return
    result = await ensure_scan(ctx)
    item = find_airdrop(result.airdrops, query)
    slug = item.slug if item else query
    n = store.unwatch(user.id, slug)
    await send_html(update, f"Removed {n} watch(es).")


@guard
async def cmd_watches(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if not user:
        return
    slugs = store.watches_for(user.id)
    if not slugs:
        await send_html(update, "No watches. /watch all or /watch polymarket")
        return
    await send_html(update, "Watching:\n" + "\n".join(f"• <code>{formatter.h(s)}</code>" for s in slugs))


def _channel_dets(result: ScanResult, channel: str):
    return [d for d in result.detections if d.channel == channel]


async def _cmd_campaign_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE, ctype: str, title: str) -> None:
    result = await ensure_scan(ctx)
    items = [i for i in result.airdrops if i.campaign_type == ctype][:12]
    dets = [d for d in result.detections if d.campaign_type == ctype]
    text = formatter.list_card(items, title, f"{len(items)} live matches · type={ctype}")
    if dets:
        text += "\n\n" + formatter.detections_card(dets, f"{title} — raw hits")
    await send_html(update, text, reply_markup=formatter.list_keyboard(items))


@guard
async def cmd_testnet(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "testnet", "Testnet campaigns")


@guard
async def cmd_mainnet(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "mainnet", "Mainnet campaigns")


@guard
async def cmd_trade(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "trade", "Trade-volume campaigns")


@guard
async def cmd_bridge(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "bridge", "Bridge campaigns")


@guard
async def cmd_points(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "points", "Points seasons")


@guard
async def cmd_stake(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "stake", "Stake / restake")


@guard
async def cmd_lp(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_campaign_type(update, ctx, "liquidity", "Liquidity / LP")


@guard
async def cmd_cex(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    items = [i for i in result.airdrops if i.channel == "cex" or "cex" in i.detected_from][:10]
    text = formatter.detections_card(_channel_dets(result, "cex"), "CEX airdrops / launchpools")
    if items:
        text = formatter.list_card(items, "CEX campaigns") + "\n\n" + text
    await send_html(update, text, reply_markup=formatter.list_keyboard(items))


@guard
async def cmd_tg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    await send_html(
        update,
        formatter.detections_card(_channel_dets(result, "telegram"), "Telegram announcement channels"),
    )


@guard
async def cmd_x(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    await send_html(
        update,
        formatter.detections_card(_channel_dets(result, "x"), "X / Twitter airdrop chatter"),
    )


@guard
async def cmd_web(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx)
    await send_html(
        update,
        formatter.detections_card(_channel_dets(result, "website"), "Website / news airdrops"),
    )


@guard
async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await ensure_scan(ctx, force=True)
    c = result.counts
    err = f"\nErrors: {', '.join(result.errors[:6])}" if result.errors else ""
    await send_html(
        update,
        "Scan complete.\n"
        f"Records {c.get('airdrops', 0)} · CEX {c.get('cex', 0)} · TG {c.get('telegram', 0)} · "
        f"X {c.get('x', 0)} · web {c.get('website', 0)} · daily {c.get('daily', 0)}.{err}",
    )
    await cmd_daily(update, ctx)


@guard
async def cmd_safety(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await send_html(update, formatter.safety_help())


@guard
async def cmd_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await send_html(
        update,
        "<b>Sources</b>\n"
        "• CEX: Binance CMS, Bybit v5 announcements, OKX support API\n"
        "• Telegram: official t.me/s/ announcement channels\n"
        "• X: Google News RSS filtered to x.com / twitter.com\n"
        "• Websites: Cointelegraph, Decrypt, Google News\n"
        "• DefiLlama no-token protocols + curated 2026 catalog\n"
        "• Daily best 10 saved to Supabase (or local SQLite)\n"
        "• Optional SpaceXAI brief via XAI_API_KEY\n\n"
        f"<i>{formatter.h(DISCLAIMER)}</i>",
    )


@guard
async def cmd_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = arg(ctx) or (update.effective_message.text if update.effective_message else "")
    text = text.replace("/check", "", 1).strip()
    if not text:
        await send_html(update, "Usage: /check https://totally-legit-claim.xyz")
        return
    report = check_text(text)
    flags = "\n".join(f"• {formatter.h(f)}" for f in report.flags)
    await send_html(
        update,
        f"<b>Safety score {report.score}/100</b>\n{formatter.h(report.verdict)}\n\n{flags}",
    )


@guard
async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    question = arg(ctx)
    if not question:
        await send_html(update, "Usage: /ask which airdrops have confirmed tokens?")
        return
    result = await ensure_scan(ctx)
    try:
        answer = ai.brief(question, result.airdrops)
    except Exception as exc:
        await send_html(update, f"AI brief failed: {formatter.h(str(exc))}")
        return
    await send_html(update, formatter.h(answer))


BUTTON_HANDLERS = {
    "plan": cmd_plan,
    "today": cmd_plan,
    "daily": cmd_daily,
    "hot": cmd_hot,
    "new": cmd_new,
    "testnet": cmd_testnet,
    "mainnet": cmd_mainnet,
    "trade": cmd_trade,
    "bridge": cmd_bridge,
    "points": cmd_points,
    "stake": cmd_stake,
    "lp": cmd_lp,
    "cex": cmd_cex,
    "tg": cmd_tg,
    "x": cmd_x,
    "web": cmd_web,
    "menu": cmd_menu,
    "status": cmd_status,
    "my": cmd_my,
    "safety": cmd_safety,
    "mute": cmd_mute,
    "unmute": cmd_unmute,
    "stats": cmd_stats,
    "top": cmd_top,
    "news": cmd_news,
    "confirmed": cmd_confirmed,
    "rumored": cmd_rumored,
    "prefs": cmd_prefs,
}


@guard
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text or text.startswith("/"):
        return
    mapped = BUTTON_HANDLERS.get(text.lower())
    if mapped:
        await mapped(update, ctx)
        return
    if text.lower().startswith("http") or "claim" in text.lower():
        report = check_text(text)
        if report.score < 70:
            flags = "\n".join(f"• {formatter.h(f)}" for f in report.flags)
            await send_html(
                update,
                f"<b>Safety score {report.score}/100</b>\n{formatter.h(report.verdict)}\n\n{flags}",
            )
            return
    result = await ensure_scan(ctx)
    item = find_airdrop(result.airdrops, text)
    if item:
        await send_html(
            update,
            formatter.detail_card(item),
            reply_markup=formatter.item_keyboard(item.slug),
        )
        return
    hits = search_airdrops(result.airdrops, text, limit=6)
    if hits:
        await send_html(
            update,
            formatter.list_card(hits, f"Matches for {text}"),
            reply_markup=formatter.list_keyboard(hits),
        )
        return
    await send_html(update, "No match. Try /hot or /search layerzero")


@guard
async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    data = query.data
    if data == "menu:hot":
        await cmd_hot(update, ctx)
        return
    if data == "menu:new":
        await cmd_new(update, ctx)
        return
    if data == "menu:daily":
        await cmd_daily(update, ctx)
        return
    if data == "menu:plan":
        await cmd_plan(update, ctx)
        return
    if data == "menu:cex":
        await cmd_cex(update, ctx)
        return
    if data == "menu:tg":
        await cmd_tg(update, ctx)
        return
    if data == "menu:x":
        await cmd_x(update, ctx)
        return
    if data == "menu:web":
        await cmd_web(update, ctx)
        return
    if data == "menu:safety":
        await cmd_safety(update, ctx)
        return
    if data == "menu:testnet":
        await cmd_testnet(update, ctx)
        return
    if data == "menu:trade":
        await cmd_trade(update, ctx)
        return
    if data == "menu:bridge":
        await cmd_bridge(update, ctx)
        return
    if data == "menu:my":
        await cmd_my(update, ctx)
        return
    if ":" not in data:
        return
    kind, slug = data.split(":", 1)
    store: Store = ctx.application.bot_data["store"]
    user = update.effective_user
    if kind == "w" and user:
        store.watch(user.id, slug)
        await query.answer(f"Watching {slug}", show_alert=False)
        return
    if kind == "u" and user:
        store.unwatch(user.id, slug)
        await query.answer(f"Unwatched {slug}", show_alert=False)
        return
    if kind == "p" and user:
        store.set_track(user.id, slug, "doing")
        await query.answer(f"Tracked {slug}", show_alert=False)
        return
    if kind == "o" and user:
        store.set_track(user.id, slug, "done")
        await query.answer(f"Marked {slug} done", show_alert=False)
        return
    if kind == "y":
        result = await ensure_scan(ctx)
        item = find_airdrop(result.airdrops, slug)
        if item:
            await send_html(
                update,
                formatter.why_card(item, why_now(item)),
                reply_markup=formatter.item_keyboard(item.slug),
                edit=True,
            )
        return
    if kind in {"d", "t", "f", "i", "r", "l"}:
        await show_section(update, ctx, kind, slug)


async def push_alerts(ctx: ContextTypes.DEFAULT_TYPE, result: ScanResult) -> int:
    if not config.AUTO_PUSH:
        return 0
    store: Store = ctx.application.bot_data["store"]
    user_ids = recipients(store)
    if not user_ids:
        # Still claim keys so a later /start does not get a backlog flood.
        alerts.collect_push_alerts(result.airdrops, result.detections, store)
        return 0
    fresh = alerts.collect_push_alerts(result.airdrops, result.detections, store)
    sent = 0
    instant: list[tuple[int, object]] = []
    digest_users: list[tuple[int, object]] = []
    for uid in user_ids:
        prefs = store.get_prefs(uid)
        if prefs.digest:
            digest_users.append((uid, prefs))
        else:
            instant.append((uid, prefs))

    limit = config.ALERT_NEW_LIMIT
    for uid, prefs in instant:
        mine = [a for a in fresh if matches_prefs(a.item, prefs)]
        if not mine:
            continue
        if len(mine) > limit:
            text = formatter.digest_card(mine[:limit], extra=len(mine) - limit)
            markup = formatter.list_keyboard([a.item for a in mine[:limit]])
            try:
                await ctx.bot.send_message(
                    uid, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=markup
                )
                sent += 1
            except Exception:
                log.exception("digest failed user=%s", uid)
        else:
            for alert in mine:
                store.log_alert(alert.item.slug, alert.kind, alert.item.name)
                try:
                    await ctx.bot.send_message(
                        uid,
                        formatter.alert_card(alert.item, alert.kind),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=formatter.item_keyboard(alert.item.slug),
                    )
                    sent += 1
                except Exception:
                    log.exception("alert failed user=%s slug=%s", uid, alert.item.slug)

    from datetime import datetime, timezone

    day_key = f"daily:{datetime.now(timezone.utc).date().isoformat()}"
    if store.mark_alerted(day_key):
        for uid, prefs in instant:
            if not result.daily:
                continue
            try:
                await ctx.bot.send_message(
                    uid,
                    formatter.daily_card(result.daily),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=formatter.list_keyboard([p.item for p in result.daily]),
                )
            except Exception:
                log.exception("daily push failed user=%s", uid)
        for uid, prefs in digest_users:
            skip = _skip_slugs(store, uid)
            plan = build_plan(result.airdrops, skip=skip, limit=5)
            mine = [a for a in fresh if matches_prefs(a.item, prefs)]
            try:
                await ctx.bot.send_message(
                    uid,
                    formatter.plan_card(plan),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=formatter.list_keyboard([p.item for p in plan]),
                )
                if mine:
                    await ctx.bot.send_message(
                        uid,
                        formatter.digest_card(mine[:limit], extra=max(0, len(mine) - limit)),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )
                sent += 1
            except Exception:
                log.exception("digest daily failed user=%s", uid)
    log.info("auto-push %s new item(s) to %s user(s)", len(fresh), len(user_ids))
    return sent


async def scan_job(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    result = await run_scan()
    ctx.application.bot_data["scan"] = result
    await persist_result(ctx, result)
    await push_alerts(ctx, result)


async def post_init(app: Application) -> None:
    app.bot_data["store"] = Store()
    try:
        app.bot_data["scan"] = await run_scan()
        log.info("initial scan: %s airdrops", len(app.bot_data["scan"].airdrops))
    except Exception:
        log.exception("initial scan failed")
        from .catalog import curated_airdrops
        from .scanner import ScanResult

        items = curated_airdrops()
        for item in items:
            from .scanner import score_airdrop

            item.score = score_airdrop(item)
        from .daily import daily_best

        picks = daily_best(items, limit=config.DAILY_PICK_LIMIT)
        app.bot_data["scan"] = ScanResult(
            airdrops=items,
            news=[],
            detections=[],
            daily=picks,
            new_slugs=[],
            errors=["initial live scan failed"],
            counts={"airdrops": len(items), "daily": len(picks)},
        )
    try:
        import time

        persist_scan(
            app.bot_data["store"],
            app.bot_data["scan"].airdrops,
            app.bot_data["scan"].detections,
            app.bot_data["scan"].daily,
            app.bot_data["scan"].errors,
            time.time(),
        )
    except Exception:
        log.exception("initial persist failed")
    try:
        from datetime import datetime, timezone

        store: Store = app.bot_data["store"]
        scan: ScanResult = app.bot_data["scan"]
        store.baseline_alerted(alerts.baseline_keys(scan.airdrops, scan.detections))
        store.mark_alerted(f"daily:{datetime.now(timezone.utc).date().isoformat()}")
        log.info("alert baseline locked — only new CEX/airdrops will be pushed")
    except Exception:
        log.exception("alert baseline failed")
    await app.bot.set_my_commands(commands.telegram_bot_commands())


def build_app() -> Application:
    problems = config.config_problems(require_telegram=True)
    if problems:
        raise SystemExit("\n".join(problems))
    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .rate_limiter(AIORateLimiter())
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("commands", cmd_menu))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("today", cmd_plan))
    app.add_handler(CommandHandler("daily", cmd_daily))
    app.add_handler(CommandHandler("best", cmd_daily))
    app.add_handler(CommandHandler("hot", cmd_hot))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("confirmed", cmd_confirmed))
    app.add_handler(CommandHandler("rumored", cmd_rumored))
    app.add_handler(CommandHandler("testnet", cmd_testnet))
    app.add_handler(CommandHandler("mainnet", cmd_mainnet))
    app.add_handler(CommandHandler("trade", cmd_trade))
    app.add_handler(CommandHandler("volume", cmd_trade))
    app.add_handler(CommandHandler("bridge", cmd_bridge))
    app.add_handler(CommandHandler("points", cmd_points))
    app.add_handler(CommandHandler("stake", cmd_stake))
    app.add_handler(CommandHandler("lp", cmd_lp))
    app.add_handler(CommandHandler("liquidity", cmd_lp))
    app.add_handler(CommandHandler("cex", cmd_cex))
    app.add_handler(CommandHandler("tg", cmd_tg))
    app.add_handler(CommandHandler("telegram", cmd_tg))
    app.add_handler(CommandHandler("x", cmd_x))
    app.add_handler(CommandHandler("twitter", cmd_x))
    app.add_handler(CommandHandler("web", cmd_web))
    app.add_handler(CommandHandler("website", cmd_web))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("airdrop", cmd_airdrop))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("fund", cmd_fund))
    app.add_handler(CommandHandler("investors", cmd_investors))
    app.add_handler(CommandHandler("reward", cmd_reward))
    app.add_handler(CommandHandler("links", cmd_links))
    app.add_handler(CommandHandler("compare", cmd_compare))
    app.add_handler(CommandHandler("why", cmd_why))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("prefs", cmd_prefs))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("instant", cmd_instant))
    app.add_handler(CommandHandler("filter", cmd_filter))
    app.add_handler(CommandHandler("minscore", cmd_minscore))
    app.add_handler(CommandHandler("chain", cmd_chain))
    app.add_handler(CommandHandler("base", cmd_base))
    app.add_handler(CommandHandler("solana", cmd_solana))
    app.add_handler(CommandHandler("eth", cmd_eth))
    app.add_handler(CommandHandler("ethereum", cmd_eth))
    app.add_handler(CommandHandler("hyperliquid", cmd_hyperliquid_chain))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("recent", cmd_recent))
    app.add_handler(CommandHandler("track", cmd_track))
    app.add_handler(CommandHandler("my", cmd_my))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("skip", cmd_skip))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("watch", cmd_watch))
    app.add_handler(CommandHandler("unwatch", cmd_unwatch))
    app.add_handler(CommandHandler("watches", cmd_watches))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("safety", cmd_safety))
    app.add_handler(CommandHandler("sources", cmd_sources))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    if app.job_queue:
        app.job_queue.run_repeating(
            scan_job,
            interval=config.SCAN_INTERVAL_MINUTES * 60,
            first=config.FIRST_SCAN_SECONDS,
            name="airdrop-scan",
        )
        log.info(
            "auto-watch every %sm (first run in %ss)",
            config.SCAN_INTERVAL_MINUTES,
            config.FIRST_SCAN_SECONDS,
        )
    return app


def run_polling() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    build_app().run_polling(allowed_updates=Update.ALL_TYPES)
