from __future__ import annotations

from dataclasses import dataclass

from telegram import BotCommand


@dataclass(frozen=True)
class Cmd:
    name: str
    desc: str
    group: str


# One registry so /menu, BotFather, and the keyboard stay in sync.
COMMANDS: tuple[Cmd, ...] = (
    Cmd("start", "Start bot and turn on auto-push", "core"),
    Cmd("help", "Full help", "core"),
    Cmd("menu", "All commands by group", "core"),
    Cmd("plan", "Best actions for today", "discover"),
    Cmd("today", "Alias of /plan", "discover"),
    Cmd("daily", "Today's best 10", "discover"),
    Cmd("best", "Alias of /daily", "discover"),
    Cmd("hot", "Highest-scored names", "discover"),
    Cmd("top", "Top 15 by score", "discover"),
    Cmd("new", "Newest live detections", "discover"),
    Cmd("confirmed", "Confirmed / points-live only", "discover"),
    Cmd("rumored", "Rumors and exploring", "discover"),
    Cmd("search", "Search name, type, or investor", "discover"),
    Cmd("testnet", "Testnet campaigns", "type"),
    Cmd("mainnet", "Mainnet campaigns", "type"),
    Cmd("trade", "Trade-volume campaigns", "type"),
    Cmd("volume", "Alias of /trade", "type"),
    Cmd("bridge", "Bridge campaigns", "type"),
    Cmd("points", "Points seasons", "type"),
    Cmd("stake", "Stake / restake", "type"),
    Cmd("lp", "Liquidity / LP", "type"),
    Cmd("liquidity", "Alias of /lp", "type"),
    Cmd("airdrop", "Full project card", "detail"),
    Cmd("tasks", "Task checklist", "detail"),
    Cmd("fund", "Funding rounds", "detail"),
    Cmd("investors", "Investor book", "detail"),
    Cmd("reward", "Reward / allocation", "detail"),
    Cmd("links", "Official links only", "detail"),
    Cmd("compare", "Compare two projects", "detail"),
    Cmd("why", "Why this ranks + cheapest path", "detail"),
    Cmd("export", "CSV of today's board", "detail"),
    Cmd("cex", "CEX launchpool / hodler", "channel"),
    Cmd("tg", "Telegram announcements", "channel"),
    Cmd("telegram", "Alias of /tg", "channel"),
    Cmd("x", "X / Twitter hits", "channel"),
    Cmd("twitter", "Alias of /x", "channel"),
    Cmd("web", "Website / news hits", "channel"),
    Cmd("website", "Alias of /web", "channel"),
    Cmd("news", "Headlines only", "channel"),
    Cmd("track", "Save a project to My list", "tracker"),
    Cmd("my", "My tracked campaigns", "tracker"),
    Cmd("done", "Mark a project done", "tracker"),
    Cmd("skip", "Skip a project", "tracker"),
    Cmd("watch", "Watch one name or all", "tracker"),
    Cmd("unwatch", "Stop watching", "tracker"),
    Cmd("watches", "List watches", "tracker"),
    Cmd("mute", "Stop auto-push", "alerts"),
    Cmd("unmute", "Resume auto-push", "alerts"),
    Cmd("digest", "One daily packet instead of spam", "alerts"),
    Cmd("instant", "Push each new hit live", "alerts"),
    Cmd("filter", "Only these types: testnet,cex", "alerts"),
    Cmd("minscore", "Ignore hits below this score", "alerts"),
    Cmd("chain", "Only these chains: base,solana", "alerts"),
    Cmd("base", "Browse Base campaigns", "type"),
    Cmd("solana", "Browse Solana campaigns", "type"),
    Cmd("eth", "Browse Ethereum campaigns", "type"),
    Cmd("hyperliquid", "Browse Hyperliquid campaigns", "type"),
    Cmd("prefs", "Show your filters", "alerts"),
    Cmd("recent", "Last auto-pushed alerts", "alerts"),
    Cmd("scan", "Force a live refresh", "system"),
    Cmd("status", "Watcher / last-scan status", "system"),
    Cmd("stats", "Counts by type and channel", "system"),
    Cmd("check", "Scam-sniff a link", "system"),
    Cmd("ask", "AI brief", "system"),
    Cmd("safety", "How not to get drained", "system"),
    Cmd("sources", "Where data comes from", "system"),
    Cmd("id", "Your Telegram user id", "system"),
    Cmd("about", "What this bot is", "system"),
)

GROUP_TITLE = {
    "core": "Core",
    "discover": "Discover",
    "type": "Campaign type",
    "detail": "Project details",
    "channel": "Source channel",
    "tracker": "My list",
    "alerts": "Auto-push",
    "system": "System",
}


def telegram_bot_commands() -> list[BotCommand]:
    return [BotCommand(c.name, c.desc[:256]) for c in COMMANDS]
