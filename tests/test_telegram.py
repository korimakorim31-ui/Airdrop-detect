from airdrop_bot.sources.telegram import parse_tg_html


HTML = """
<div class="tgme_widget_message_wrap">
  <div class="tgme_widget_message" data-post="binance_announcements/99">
    <div class="tgme_widget_message_text js-message_text">Binance Hodler Airdrops for TOKEN start tomorrow</div>
    <a href="https://t.me/binance_announcements/99"><time datetime="2026-08-15T10:00:00+00:00"></time></a>
  </div>
</div>
<div class="tgme_widget_message_wrap">
  <div class="tgme_widget_message" data-post="binance_announcements/100">
    <div class="tgme_widget_message_text">Futures will apply last price protection on ONEUSDT</div>
    <a href="https://t.me/binance_announcements/100"></a>
  </div>
</div>
"""


def test_telegram_filters_to_airdrop_posts():
    hits = parse_tg_html(HTML, "binance_announcements")
    assert len(hits) == 1
    assert hits[0].channel == "telegram"
    assert "Hodler" in hits[0].title
    assert "t.me/binance_announcements/99" in hits[0].url
