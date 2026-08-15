from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .config import DB_PATH


class Store:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(exist_ok=True)
        self._init()
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS seen (
                    slug TEXT PRIMARY KEY,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS watches (
                    user_id INTEGER NOT NULL,
                    slug TEXT NOT NULL,
                    created REAL NOT NULL,
                    PRIMARY KEY (user_id, slug)
                );
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_seen REAL NOT NULL,
                    alerts_enabled INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS alerted (
                    key TEXT PRIMARY KEY,
                    created REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created REAL NOT NULL,
                    slug TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS airdrops (
                    slug TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    symbol TEXT,
                    status TEXT,
                    certainty TEXT,
                    category TEXT,
                    channel TEXT,
                    payload TEXT NOT NULL,
                    score INTEGER,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    source_name TEXT,
                    title TEXT,
                    url TEXT,
                    body TEXT,
                    published_at TEXT,
                    seen_at REAL NOT NULL,
                    UNIQUE(channel, url, title)
                );
                CREATE TABLE IF NOT EXISTS daily_picks (
                    pick_date TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    slug TEXT NOT NULL,
                    score INTEGER,
                    reason TEXT,
                    payload TEXT,
                    created REAL NOT NULL,
                    PRIMARY KEY (pick_date, rank)
                );
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started REAL,
                    finished REAL NOT NULL,
                    counts TEXT,
                    errors TEXT
                );
                CREATE TABLE IF NOT EXISTS tracks (
                    user_id INTEGER NOT NULL,
                    slug TEXT NOT NULL,
                    state TEXT NOT NULL,
                    note TEXT,
                    updated REAL NOT NULL,
                    PRIMARY KEY (user_id, slug)
                );
                CREATE TABLE IF NOT EXISTS prefs (
                    user_id INTEGER PRIMARY KEY,
                    digest INTEGER NOT NULL DEFAULT 0,
                    min_score INTEGER NOT NULL DEFAULT 0,
                    types TEXT NOT NULL DEFAULT '*',
                    chains TEXT NOT NULL DEFAULT '*'
                );
                """
            )

    def _migrate(self) -> None:
        with self._connect() as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
            if "alerts_enabled" not in cols:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN alerts_enabled INTEGER NOT NULL DEFAULT 1"
                )

    def touch_user(self, user_id: int, username: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_seen, alerts_enabled)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
                """,
                (user_id, username or "", time.time()),
            )

    def upsert_seen(self, slug: str, payload: dict) -> bool:
        """Return True if this slug is brand new."""
        now = time.time()
        blob = json.dumps(payload, default=str)
        with self._connect() as conn:
            row = conn.execute("SELECT slug FROM seen WHERE slug=?", (slug,)).fetchone()
            if row:
                conn.execute(
                    "UPDATE seen SET last_seen=?, payload=? WHERE slug=?",
                    (now, blob, slug),
                )
                return False
            conn.execute(
                "INSERT INTO seen (slug, first_seen, last_seen, payload) VALUES (?,?,?,?)",
                (slug, now, now, blob),
            )
            return True

    def watch(self, user_id: int, slug: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO watches (user_id, slug, created)
                VALUES (?, ?, ?)
                """,
                (user_id, slug, time.time()),
            )

    def unwatch(self, user_id: int, slug: str | None = None) -> int:
        with self._connect() as conn:
            if slug:
                cur = conn.execute(
                    "DELETE FROM watches WHERE user_id=? AND slug=?",
                    (user_id, slug),
                )
            else:
                cur = conn.execute("DELETE FROM watches WHERE user_id=?", (user_id,))
            return cur.rowcount

    def watches_for(self, user_id: int) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT slug FROM watches WHERE user_id=? ORDER BY created",
                (user_id,),
            ).fetchall()
        return [r["slug"] for r in rows]

    def watchers(self, slug: str) -> list[int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT user_id FROM watches WHERE slug=? OR slug='*'",
                (slug,),
            ).fetchall()
        return [int(r["user_id"]) for r in rows]

    def all_global_watchers(self) -> list[int]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT user_id FROM watches WHERE slug='*'").fetchall()
        return [int(r["user_id"]) for r in rows]

    def log_alert(self, slug: str, kind: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO alerts (created, slug, kind, message) VALUES (?,?,?,?)",
                (time.time(), slug, kind, message),
            )

    def recent_alerts(self, limit: int = 10) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM alerts ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def upsert_airdrop(self, slug: str, name: str, payload: dict, score: int, channel: str) -> None:
        now = time.time()
        blob = json.dumps(payload, default=str)
        with self._connect() as conn:
            row = conn.execute("SELECT slug FROM airdrops WHERE slug=?", (slug,)).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE airdrops
                    SET name=?, symbol=?, status=?, certainty=?, category=?, channel=?,
                        payload=?, score=?, last_seen=?
                    WHERE slug=?
                    """,
                    (
                        name,
                        payload.get("symbol"),
                        payload.get("status"),
                        payload.get("certainty"),
                        payload.get("category"),
                        channel,
                        blob,
                        score,
                        now,
                        slug,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO airdrops
                    (slug, name, symbol, status, certainty, category, channel, payload, score, first_seen, last_seen)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        slug,
                        name,
                        payload.get("symbol"),
                        payload.get("status"),
                        payload.get("certainty"),
                        payload.get("category"),
                        channel,
                        blob,
                        score,
                        now,
                        now,
                    ),
                )

    def insert_detection(self, channel: str, source_name: str, title: str, url: str, body: str, published_at: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO detections
                (channel, source_name, title, url, body, published_at, seen_at)
                VALUES (?,?,?,?,?,?,?)
                """,
                (channel, source_name, title, url, body, published_at, time.time()),
            )
            return cur.rowcount > 0

    def set_alerts(self, user_id: int, enabled: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET alerts_enabled=? WHERE user_id=?",
                (1 if enabled else 0, user_id),
            )

    def alerts_on(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT alerts_enabled FROM users WHERE user_id=?",
                (user_id,),
            ).fetchone()
        return bool(row and row["alerts_enabled"])

    def subscribers(self) -> list[int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT user_id FROM users WHERE COALESCE(alerts_enabled, 1) = 1"
            ).fetchall()
        return [int(r["user_id"]) for r in rows]

    def mark_alerted(self, key: str) -> bool:
        """Return True if this key has never been pushed."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO alerted (key, created) VALUES (?, ?)",
                (key, time.time()),
            )
            return cur.rowcount > 0

    def baseline_alerted(self, keys: list[str]) -> int:
        now = time.time()
        count = 0
        with self._connect() as conn:
            for key in keys:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO alerted (key, created) VALUES (?, ?)",
                    (key, now),
                )
                count += cur.rowcount
        return count

    def replace_daily_picks(self, pick_date: str, rows: list[dict]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM daily_picks WHERE pick_date=?", (pick_date,))
            for row in rows:
                conn.execute(
                    """
                    INSERT INTO daily_picks
                    (pick_date, rank, slug, score, reason, payload, created)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        pick_date,
                        row["rank"],
                        row["slug"],
                        row.get("score") or 0,
                        row.get("reason") or "",
                        json.dumps(row.get("payload") or {}, default=str),
                        time.time(),
                    ),
                )

    def daily_picks(self, pick_date: str) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM daily_picks WHERE pick_date=? ORDER BY rank",
                (pick_date,),
            ).fetchall()

    def log_scan(self, counts: dict, errors: list[str], started: float) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO scans (started, finished, counts, errors) VALUES (?,?,?,?)",
                (started, time.time(), json.dumps(counts), json.dumps(errors)),
            )

    def last_scan(self) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 1").fetchone()

    def set_track(self, user_id: int, slug: str, state: str, note: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tracks (user_id, slug, state, note, updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, slug) DO UPDATE SET
                    state=excluded.state,
                    note=excluded.note,
                    updated=excluded.updated
                """,
                (user_id, slug, state, note, time.time()),
            )

    def tracks_for(self, user_id: int) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM tracks WHERE user_id=? ORDER BY updated DESC",
                (user_id,),
            ).fetchall()

    def get_prefs(self, user_id: int):
        from .playbook import parse_prefs

        with self._connect() as conn:
            row = conn.execute("SELECT * FROM prefs WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return parse_prefs()
        return parse_prefs(row["digest"], row["min_score"], row["types"], row["chains"])

    def set_prefs(
        self,
        user_id: int,
        *,
        digest: bool | None = None,
        min_score: int | None = None,
        types: str | None = None,
        chains: str | None = None,
    ):
        current = self.get_prefs(user_id)
        next_digest = current.digest if digest is None else digest
        next_score = current.min_score if min_score is None else min_score
        next_types = ",".join(current.types) if types is None else types
        next_chains = ",".join(current.chains) if chains is None else chains
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO prefs (user_id, digest, min_score, types, chains)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    digest=excluded.digest,
                    min_score=excluded.min_score,
                    types=excluded.types,
                    chains=excluded.chains
                """,
                (user_id, 1 if next_digest else 0, next_score, next_types, next_chains),
            )
        return self.get_prefs(user_id)

    def untrack(self, user_id: int, slug: str | None = None) -> int:
        with self._connect() as conn:
            if slug:
                cur = conn.execute(
                    "DELETE FROM tracks WHERE user_id=? AND slug=?",
                    (user_id, slug),
                )
            else:
                cur = conn.execute("DELETE FROM tracks WHERE user_id=?", (user_id,))
            return cur.rowcount
