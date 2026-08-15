from airdrop_bot.catalog import catalog_by_slug
from airdrop_bot.commands import COMMANDS, telegram_bot_commands
from airdrop_bot.formatter import compare_card, menu_text, stats_card
from airdrop_bot.scanner import score_airdrop
from airdrop_bot.store import Store


def test_every_command_is_registered_for_telegram():
    names = [c.command for c in telegram_bot_commands()]
    assert "start" in names
    assert "menu" in names
    assert "testnet" in names
    assert "compare" in names
    assert "track" in names
    assert "status" in names
    assert len(names) == len(COMMANDS)
    assert len(names) == len(set(names))


def test_menu_lists_commands():
    text = menu_text()
    assert "/daily" in text
    assert "/track" in text
    assert "/compare" in text


def test_compare_and_stats():
    slugs = catalog_by_slug()
    a = slugs["polymarket"]
    b = slugs["metamask"]
    a.score = score_airdrop(a)
    b.score = score_airdrop(b)
    card = compare_card(a, b)
    assert "Polymarket" in card and "MetaMask" in card
    stats = stats_card([a, b], [])
    assert "trade" in stats.lower() or "TRADE" in stats


def test_personal_tracker(tmp_path):
    store = Store(tmp_path / "t.sqlite3")
    store.touch_user(7, "bob")
    store.set_track(7, "polymarket", "doing", "trade daily")
    store.set_track(7, "polymarket", "done")
    rows = store.tracks_for(7)
    assert len(rows) == 1
    assert rows[0]["state"] == "done"
    assert store.untrack(7, "polymarket") == 1
