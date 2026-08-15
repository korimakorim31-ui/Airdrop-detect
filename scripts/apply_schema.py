"""One-shot: apply supabase/schema.sql. Password from PG_PASSWORD env only."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import psycopg

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "supabase" / "schema.sql").read_text(encoding="utf-8")
HOST = os.environ.get("PGHOST", "db.plwpxcsyjxnntwxsqnfc.supabase.co")
USER = os.environ.get("PGUSER", "postgres")
PASSWORD = os.environ.get("PGPASSWORD", "")


def main() -> int:
    if not PASSWORD:
        print("PGPASSWORD missing")
        return 2
    url = f"postgresql://{USER}:{quote_plus(PASSWORD)}@{HOST}:5432/postgres?sslmode=require"
    try:
        with psycopg.connect(url, connect_timeout=20) as conn:
            with conn.cursor() as cur:
                cur.execute(SQL)
            conn.commit()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select table_name from information_schema.tables
                    where table_schema='public'
                      and table_name in ('airdrops','detections','daily_picks','scans')
                    order by 1
                    """
                )
                print("TABLES", [r[0] for r in cur.fetchall()])
        print("SCHEMA_OK")
        return 0
    except Exception as exc:
        print("SCHEMA_FAIL", type(exc).__name__, str(exc)[:400])
        return 1


if __name__ == "__main__":
    sys.exit(main())
