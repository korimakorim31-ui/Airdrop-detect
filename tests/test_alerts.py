from airdrop_bot.alerts import (
    collect_push_alerts,
    detection_key,
    is_push_worthy_detection,
    is_push_worthy_item,
)
from airdrop_bot.catalog import catalog_by_slug
from airdrop_bot.scanner import score_airdrop
from airdrop_bot.sources.common import Detection
from airdrop_bot.store import Store


def test_cex_detection_is_push_worthy():
    det = Detection("cex", "Binance", "Hodler Airdrop for ABC", "https://www.binance.com/a", "airdrop")
    assert is_push_worthy_detection(det)
    skip = Detection("cex", "Binance", "source-errors", "", "")
    assert not is_push_worthy_detection(skip)


def test_catalog_only_is_not_auto_pushed():
    item = catalog_by_slug()["polymarket"]
    item.score = score_airdrop(item)
    assert item.channel == "catalog"
    assert not is_push_worthy_item(item)


def test_collect_pushes_new_cex_once(tmp_path):
    store = Store(tmp_path / "intel.sqlite3")
    det = Detection(
        channel="cex",
        source_name="Binance",
        title="Binance Hodler Airdrops: TOKEN",
        url="https://www.binance.com/en/support/announcement/tok",
        body="hodler airdrop",
    )
    first = collect_push_alerts([], [det], store)
    assert len(first) == 1
    assert first[0].kind == "cex"
    assert "Hodler" in first[0].item.name or "Hodler" in first[0].item.origin_title
    second = collect_push_alerts([], [det], store)
    assert second == []
    assert detection_key(det).startswith("det:cex:")


def test_subscribers_mute(tmp_path):
    store = Store(tmp_path / "intel.sqlite3")
    store.touch_user(1, "a")
    store.touch_user(2, "b")
    assert set(store.subscribers()) == {1, 2}
    store.set_alerts(2, False)
    assert store.subscribers() == [1]
    assert store.alerts_on(1)
    assert not store.alerts_on(2)
