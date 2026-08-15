from airdrop_bot.store import Store


def test_watch_and_seen(tmp_path):
    store = Store(tmp_path / "intel.sqlite3")
    store.touch_user(42, "alice")
    assert store.upsert_seen("polymarket", {"name": "Polymarket"}) is True
    assert store.upsert_seen("polymarket", {"name": "Polymarket"}) is False
    store.watch(42, "*")
    store.watch(42, "metamask")
    assert store.watches_for(42) == ["*", "metamask"]
    assert 42 in store.watchers("anything-new")
    assert store.unwatch(42, "metamask") == 1
    assert store.unwatch(42) == 1
    store.upsert_airdrop("polymarket", "Polymarket", {"symbol": "POLY", "status": "airdrop_confirmed", "certainty": "medium", "category": "Prediction"}, 88, "catalog")
    store.insert_detection("cex", "Binance", "Hodler Airdrop", "https://example.com/a", "body", "2026-08-15")
    store.replace_daily_picks(
        "2026-08-15",
        [{"rank": 1, "slug": "polymarket", "score": 88, "reason": "confirmed", "payload": {"name": "Polymarket"}}],
    )
    picks = store.daily_picks("2026-08-15")
    assert len(picks) == 1
    assert picks[0]["slug"] == "polymarket"
