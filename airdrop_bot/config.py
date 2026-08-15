from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "intel.sqlite3"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1").strip()
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4.6").strip() or "grok-4.6"

SCAN_INTERVAL_MINUTES = max(2, int(os.getenv("SCAN_INTERVAL_MINUTES", "5")))
ALERT_NEW_LIMIT = max(1, int(os.getenv("ALERT_NEW_LIMIT", "5")))
AUTO_PUSH = os.getenv("AUTO_PUSH", "true").strip().lower() not in {"0", "false", "no", "off"}
FIRST_SCAN_SECONDS = max(15, int(os.getenv("FIRST_SCAN_SECONDS", "45")))
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "25"))
DAILY_PICK_LIMIT = max(3, int(os.getenv("DAILY_PICK_LIMIT", "10")))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    or os.getenv("SUPABASE_KEY", "").strip()
)


def supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _parse_ids(raw: str) -> set[int]:
    out: set[int] = set()
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk.lstrip("-").isdigit():
            out.add(int(chunk))
    return out


ALLOWED_USER_IDS: set[int] = _parse_ids(os.getenv("ALLOWED_USER_IDS", ""))


def config_problems(require_telegram: bool = True) -> list[str]:
    problems: list[str] = []
    if require_telegram and not TELEGRAM_BOT_TOKEN:
        problems.append("TELEGRAM_BOT_TOKEN is missing from .env")
    return problems
