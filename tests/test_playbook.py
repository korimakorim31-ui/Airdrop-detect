from airdrop_bot.catalog import catalog_by_slug
from airdrop_bot.playbook import (
    build_plan,
    enrich_item,
    extract_deadline,
    matches_prefs,
    parse_prefs,
    plan_score,
    why_now,
)
from airdrop_bot.scanner import score_airdrop
from airdrop_bot.store import Store


def test_deadline_and_enrich():
    assert extract_deadline("Claim window ends 2026-08-20 on the official site") == "2026-08-20"
    item = catalog_by_slug()["aztec"]
    enrich_item(item)
    assert item.capital == "gas"
    assert item.effort == "days"
    assert item.playbook


def test_plan_skips_done_and_diversifies():
    slugs = catalog_by_slug()
    items = list(slugs.values())
    for item in items:
        enrich_item(item)
        item.score = score_airdrop(item)
    plan = build_plan(items, skip={"polymarket"}, limit=5)
    assert plan
    assert all(p.item.slug != "polymarket" for p in plan)
    types = [p.item.campaign_type for p in plan]
    assert types.count("trade") <= 2


def test_prefs_filter_and_store(tmp_path):
    store = Store(tmp_path / "p.sqlite3")
    store.touch_user(1, "a")
    prefs = store.set_prefs(1, digest=True, min_score=50, types="testnet,cex", chains="base")
    assert prefs.digest
    assert prefs.min_score == 50
    item = catalog_by_slug()["aztec"]
    enrich_item(item)
    item.score = 80
    item.chains = ["Ethereum"]
    assert not matches_prefs(item, prefs)
    item.chains = ["Base"]
    item.campaign_type = "testnet"
    assert matches_prefs(item, parse_prefs(0, 50, "testnet", "base"))
    assert why_now(item)
    assert plan_score(item) >= item.score
