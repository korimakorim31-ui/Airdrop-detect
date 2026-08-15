from airdrop_bot.catalog import catalog_by_slug
from airdrop_bot.formatter import (
    detail_card,
    fund_card,
    investors_card,
    list_card,
    reward_card,
    tasks_card,
)
from airdrop_bot.scanner import score_airdrop


def test_cards_escape_and_include_sections():
    item = catalog_by_slug()["polymarket"]
    item.score = score_airdrop(item)
    detail = detail_card(item)
    assert "Polymarket" in detail
    assert "Funding" in detail
    assert "Investors" in detail
    assert "<script>" not in detail
    assert "Research only" in detail
    assert "Tasks" in tasks_card(item)
    assert "$1B" in fund_card(item) or "1B" in fund_card(item)
    assert "ICE" in investors_card(item) or "Intercontinental" in investors_card(item)
    assert "USDC" in reward_card(item) or "token" in reward_card(item).lower()
    listing = list_card([item], "Hot")
    assert "Hot" in listing
