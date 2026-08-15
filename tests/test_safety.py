from airdrop_bot.safety import check_text


def test_seed_phrase_is_dangerous():
    report = check_text("Send your seed phrase to claim the airdrop now")
    assert report.score < 40
    assert any("seed" in f.lower() or "phrase" in f.lower() for f in report.flags)


def test_official_domain_is_calmer():
    report = check_text("Read https://polymarket.com and the official docs")
    assert report.score >= 70


def test_fake_claim_host():
    report = check_text("Connect wallet to claim https://airdrop-claim-polymarket.xyz/go")
    assert report.score < 70
