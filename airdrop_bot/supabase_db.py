from __future__ import annotations

import logging

from .config import SUPABASE_KEY, SUPABASE_URL, supabase_enabled

log = logging.getLogger("airdrop-intel")
_client = None


def get_client():
    global _client
    if not supabase_enabled():
        return None
    if _client is not None:
        return _client
    from supabase import create_client

    _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    log.info("supabase client ready")
    return _client
