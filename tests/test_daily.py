from airdrop_bot.catalog import curated_airdrops
from airdrop_bot.daily import daily_best, pick_reason
from airdrop_bot.scanner import score_airdrop
from airdrop_bot.sources.common import Detection, looks_like_airdrop
from airdrop_bot.scanner import merge


def test_daily_best_prefers_live_and_ranks():
    items = curated_airdrops()
    for item in items:
        item.score = score_airdrop(item)
    picks = daily_best(items, limit=5)
    assert len(picks) == 5
    assert [p.rank for p in picks] == [1, 2, 3, 4, 5]
    assert all(p.item.status != "ended" for p in picks)
    assert picks[0].score >= picks[-1].score
    assert pick_reason(picks[0].item)


def test_detection_merges_onto_catalog():
    dets = [
        Detection(
            channel="cex",
            source_name="Binance",
            title="Binance lists Polymarket related reward campaign",
            url="https://www.binance.com/en/support/announcement/x",
            body="airdrop",
        )
    ]
    items = merge(curated_airdrops(), [], [], dets)
    poly = next(i for i in items if i.slug == "polymarket")
    assert "cex" in poly.detected_from
    assert any("Binance" in h for h in poly.news_hits)


def test_looks_like_airdrop():
    assert looks_like_airdrop("Launchpool for NEWTOKEN")
    assert not looks_like_airdrop("Tick size update for BTCUSDT")
