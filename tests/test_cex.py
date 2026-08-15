from airdrop_bot.sources.cex import parse_binance, parse_bybit, parse_okx


def test_binance_keeps_airdrop_skips_maintenance():
    payload = {
        "data": {
            "catalogs": [
                {
                    "catalogName": "Latest Binance News",
                    "articles": [
                        {"title": "Binance Hodler Airdrops: Claim XYZ", "code": "abc", "releaseDate": 1700000000000},
                        {"title": "Updates on Tick Size for Spot Trading Pairs", "code": "def"},
                    ],
                }
            ]
        }
    }
    hits = parse_binance(payload)
    assert len(hits) == 1
    assert "Hodler" in hits[0].title
    assert hits[0].channel == "cex"
    assert hits[0].source_name == "Binance"


def test_bybit_activities_and_okx_rewards():
    bybit = {
        "result": {
            "list": [
                {
                    "title": "Trade MOONSHOT. Win $100,000",
                    "description": "reward pool",
                    "type": {"key": "latest_activities"},
                    "url": "https://announcements.bybit.com/x",
                },
                {
                    "title": "New listing FOO",
                    "description": "spot listing",
                    "type": {"key": "new_crypto"},
                    "url": "https://announcements.bybit.com/y",
                },
            ]
        }
    }
    hits = parse_bybit(bybit)
    assert any("MOONSHOT" in h.title for h in hits)
    assert not any("FOO" in h.title for h in hits)

    okx = {
        "data": [
            {
                "details": [
                    {"title": "OKX Jumpstart airdrop for ABC", "url": "https://www.okx.com/help/x", "pTime": "1700000000000"},
                    {"title": "OKX to list AVNTUSD X-Perps", "url": "https://www.okx.com/help/y", "pTime": "1700000000000"},
                ]
            }
        ]
    }
    ohits = parse_okx(okx, "announcements-latest-activities")
    assert len(ohits) == 1
    assert "Jumpstart" in ohits[0].title
