from __future__ import annotations

import json

from .config import XAI_API_KEY, XAI_BASE_URL, XAI_MODEL
from .models import Airdrop

SYSTEM = (
    "You are an airdrop research desk inside a Telegram bot. "
    "Be precise. Mark rumors as rumors. Never invent a claim URL, airdrop date, "
    "or investor. Never ask for a seed phrase or wallet. If data is missing, say so. "
    "Keep answers under 280 words. Use short bullets."
)


def available() -> bool:
    return bool(XAI_API_KEY)


def _client():
    from openai import OpenAI

    return OpenAI(api_key=XAI_API_KEY, base_url=XAI_BASE_URL)


def _compact(item: Airdrop) -> dict:
    return {
        "name": item.name,
        "symbol": item.symbol,
        "status": item.status,
        "certainty": item.certainty,
        "score": item.score,
        "category": item.category,
        "chains": item.chains,
        "summary": item.summary,
        "reward": item.reward,
        "eligibility": item.eligibility,
        "tasks": [{"title": t.title, "detail": t.detail} for t in item.tasks],
        "funding": [
            {"amount": f.amount, "date": f.date, "round": f.round_name, "lead": f.lead}
            for f in item.funding
        ],
        "investors": [f"{i.name} ({i.role})" for i in item.investors],
        "links": [f"{l.label}: {l.url}" for l in item.links],
        "risk": item.risk_notes,
        "news": item.news_hits[:4],
        "tvl_usd": item.tvl_usd,
    }


def brief(question: str, items: list[Airdrop]) -> str:
    if not available():
        return (
            "AI brief is off. Add XAI_API_KEY from https://console.x.ai to .env "
            "and restart. Until then use /hot /search /airdrop."
        )
    payload = [_compact(i) for i in items[:12]]
    client = _client()
    resp = client.responses.create(
        model=XAI_MODEL,
        input=[
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Research snapshot (JSON):\n{json.dumps(payload, default=str)}"
                ),
            },
        ],
    )
    text = getattr(resp, "output_text", None)
    if text:
        return text.strip()
    return "The model returned an empty brief."
