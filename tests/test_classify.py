from airdrop_bot.catalog import catalog_by_slug
from airdrop_bot.sources.common import classify_campaign, looks_like_airdrop


def test_classifies_each_farm_type():
    assert classify_campaign("Join the incentivized testnet and faucet") == "testnet"
    assert classify_campaign("Bridge ETH via the official canonical bridge") == "bridge"
    assert classify_campaign("Trade volume campaign — trade to earn points") == "trade"
    assert classify_campaign("Provide liquidity in the DLMM pool") == "liquidity"
    assert classify_campaign("Restake ETH this season") == "stake"
    assert classify_campaign("Points season 3 is live") == "points"
    assert classify_campaign("Binance Hodler Airdrop for XYZ") == "cex"
    assert classify_campaign("Mainnet launch — on-chain activity counts") == "mainnet"
    assert classify_campaign("Token airdrop snapshot next week") == "airdrop"


def test_skips_maintenance():
    assert classify_campaign("Updates on Tick Size for Spot Trading Pairs") == ""
    assert not looks_like_airdrop("Wallet maintenance on Sunday")


def test_catalog_types():
    slugs = catalog_by_slug()
    assert slugs["layerzero"].campaign_type == "bridge"
    assert slugs["hyperliquid"].campaign_type == "trade"
    assert slugs["aztec"].campaign_type == "testnet"
    assert slugs["base"].campaign_type == "mainnet"
