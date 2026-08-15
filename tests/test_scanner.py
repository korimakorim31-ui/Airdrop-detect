from airdrop_bot.catalog import curated_airdrops
from airdrop_bot.scanner import find_airdrop, merge, score_airdrop, search_airdrops
from airdrop_bot.sources.defillama import LlamaHit, parse_protocols
from airdrop_bot.sources.news import NewsHit


def test_parse_protocols_keeps_no_token_dex():
    raw = [
        {
            "name": "Fresh Perp",
            "symbol": "-",
            "slug": "fresh-perp",
            "category": "Derivatives",
            "tvl": 25_000_000,
            "change_7d": 12,
            "listedAt": 1_700_000_000,
            "chain": "Arbitrum",
            "chains": ["Arbitrum"],
            "url": "https://example.com",
            "twitter": "freshperp",
            "description": "perps",
        },
        {
            "name": "Binance CEX",
            "symbol": "-",
            "slug": "binance-cex",
            "category": "CEX",
            "tvl": 9_000_000_000,
            "listedAt": 1_600_000_000,
        },
        {
            "name": "Has Token",
            "symbol": "ABC",
            "slug": "has-token",
            "category": "Dexs",
            "tvl": 80_000_000,
        },
    ]
    hits = parse_protocols(raw, now=1_700_000_000 + 86400)
    names = {h.name for h in hits}
    assert "Fresh Perp" in names
    assert "Binance CEX" not in names
    assert "Has Token" not in names


def test_merge_overlays_tvl_and_keeps_catalog():
    llama = [
        LlamaHit(
            slug="polymarket",
            name="Polymarket",
            category="Prediction Market",
            chain="Polygon",
            chains=["Polygon"],
            url="https://polymarket.com",
            twitter="Polymarket",
            description="markets",
            tvl_usd=123_000_000,
            tvl_change_7d=4.2,
            listed_at=1,
            symbol="-",
            reasons=["no-token protocol with material TVL"],
        )
    ]
    news = [NewsHit("Polymarket airdrop timeline slips", "https://example.com/n", "Test", "")]
    items = merge(curated_airdrops(), llama, news)
    poly = find_airdrop(items, "polymarket")
    assert poly is not None
    assert poly.tvl_usd == 123_000_000
    assert poly.investors
    assert any("Polymarket" in h for h in poly.news_hits)
    assert poly.score == score_airdrop(poly)
    assert search_airdrops(items, "intercontinental")


def test_find_by_investor():
    items = curated_airdrops()
    for item in items:
        item.score = score_airdrop(item)
    hit = find_airdrop(items, "founders fund")
    assert hit is not None
    assert hit.slug == "polymarket"
