from airdrop_bot.catalog import catalog_by_slug, curated_airdrops


def test_catalog_has_core_names():
    slugs = catalog_by_slug()
    for name in ("polymarket", "metamask", "base", "opensea", "backpack"):
        assert name in slugs


def test_every_entry_has_research_fields():
    for item in curated_airdrops():
        assert item.slug and item.name
        assert item.summary
        assert item.reward
        assert item.eligibility
        assert item.tasks
        assert item.links
        assert item.sources
        assert item.status
        assert all(link.url.startswith("http") for link in item.links)
