#!/usr/bin/env python3
"""Airdrop Intel Bot.

  python run.py                 # Telegram polling
  python run.py --once          # one live scan to stdout (saves to DB)
  python run.py --daily         # print today's best 10
  python run.py --card NAME     # print one full card
  python run.py --search Q      # search the live set
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from html.parser import HTMLParser


class _Strip(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []

    def handle_data(self, data: str) -> None:
        self.out.append(data)

    def text(self) -> str:
        return "".join(self.out)


def html_to_text(raw: str) -> str:
    parser = _Strip()
    parser.feed(raw)
    parser.close()
    return parser.text()


async def cli_once(query: str | None, search: str | None, daily: bool = False) -> int:
    import time

    from airdrop_bot.formatter import (
        daily_card,
        detections_card,
        detail_card,
        fund_card,
        investors_card,
        list_card,
        news_card,
        reward_card,
        tasks_card,
    )
    from airdrop_bot.persist import persist_scan
    from airdrop_bot.scanner import find_airdrop, run_scan, search_airdrops
    from airdrop_bot.store import Store

    print("Scanning CEX + Telegram + X + websites + DefiLlama…")
    result = await run_scan()
    counts = persist_scan(
        Store(),
        result.airdrops,
        result.detections,
        result.daily,
        result.errors,
        time.time(),
    )
    print("Saved:", counts)
    if result.errors:
        print("Source errors:", "; ".join(result.errors[:8]), file=sys.stderr)
    if daily or (not query and not search):
        print(html_to_text(daily_card(result.daily)))
        print()
    if search:
        hits = search_airdrops(result.airdrops, search, limit=12)
        print(html_to_text(list_card(hits, f"Search: {search}")))
        return 0 if hits else 1
    if query:
        item = find_airdrop(result.airdrops, query)
        if not item:
            print(f"No match for {query!r}")
            return 1
        for fn in (detail_card, tasks_card, fund_card, investors_card, reward_card):
            print(html_to_text(fn(item)))
            print("-" * 60)
        return 0
    if daily:
        return 0
    print(html_to_text(list_card(result.airdrops[:12], "Hot airdrops", f"{len(result.airdrops)} records")))
    print()
    print(html_to_text(detections_card([d for d in result.detections if d.channel == "cex"][:8], "CEX")))
    print()
    print(html_to_text(news_card(result.news[:8])))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Airdrop Intel Bot")
    parser.add_argument("--once", action="store_true", help="run one scan and exit")
    parser.add_argument("--daily", action="store_true", help="print today's best 10")
    parser.add_argument("--card", metavar="NAME", help="print one project's full cards")
    parser.add_argument("--search", metavar="Q", help="search names / investors")
    args = parser.parse_args()
    if args.once or args.card or args.search or args.daily:
        return asyncio.run(cli_once(args.card, args.search, args.daily))
    from airdrop_bot.bot import run_polling

    run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
