# Airdrop Intel Bot

Telegram + CLI research bot that **detects airdrops from every public channel it can reach**, ranks a **daily best-10**, and **saves the full card to Supabase** (or local SQLite).

Each card includes tasks, reward notes, funding, investors, official links, and scam warnings.

This is a **research desk**, not a farmer. It does not connect a wallet, claim tokens, solve social tasks, or ask for a seed phrase.

## What it detects

| Channel | Command | Live source |
| --- | --- | --- |
| CEX | `/cex` | Binance CMS, Bybit v5 announcements, OKX support API (Launchpool / Hodler / Jumpstart / reward copy) |
| Telegram | `/tg` | Official `t.me/s/` announcement channels (Binance, Bybit, OKX, Bitget, KuCoin, Gate, CMC) |
| X | `/x` | Google News RSS filtered to x.com / twitter.com |
| Websites | `/web` | Cointelegraph, Decrypt, Google News |
| On-chain / project | `/hot` | DefiLlama no-token protocols + curated 2026 catalog (tasks, fund, investors) |

The bot **scans by itself every 5 minutes**. After `/start`, new **airdrop, testnet, mainnet, trade-volume, bridge, LP, stake, points, and CEX** campaigns are **pushed to your chat automatically**. You do not need to `/scan`. `/mute` pauses pings; `/unmute` turns them back on.

`/daily` (alias `/best`) is the ranked board for today. Every scan upserts:

- `airdrops` — full research card
- `detections` — raw CEX / TG / X / web hits
- `daily_picks` — today's best 10 + reason
- `scans` — run log

## Telegram commands

After `/start` a keyboard stays under the chat and you get **`/plan`** — today's 5 best actions by cost, type, and what you already marked done.

Push is filterable: `/digest on` (one daily packet), `/filter testnet,cex`, `/minscore 60`, `/chain base`. `/why name` explains rank + cheapest path. `/export` sends a CSV.

`/` in Telegram lists every command. `/menu` prints the same list grouped.

| Group | Commands |
| --- | --- |
| Core | `/start` `/help` `/menu` `/about` |
| Discover | `/daily` `/best` `/hot` `/top` `/new` `/confirmed` `/rumored` `/search` |
| Type | `/testnet` `/mainnet` `/trade` `/bridge` `/points` `/stake` `/lp` |
| Details | `/airdrop` `/tasks` `/fund` `/investors` `/reward` `/links` `/compare a vs b` |
| Channel | `/cex` `/tg` `/x` `/web` `/news` |
| My list | `/track` `/my` `/done` `/skip` `/watch` `/unwatch` `/watches` |
| Alerts | `/mute` `/unmute` `/recent` |
| System | `/scan` `/status` `/stats` `/check` `/ask` `/safety` `/sources` `/id` |

Type a project name as plain text to open its card. Tap **Track** on a card to save it to `/my`.

## Setup

Python 3.11+ (3.12 / 3.14 are fine).

```powershell
cd C:\Users\DELL\airdrop-intel-bot
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
```

1. Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → paste the token into `TELEGRAM_BOT_TOKEN`.
2. Optional: put your numeric Telegram id in `ALLOWED_USER_IDS`.
3. Optional: xAI key at https://console.x.ai → `XAI_API_KEY` for `/ask`.
4. **Supabase (recommended)**
   - Create a project at https://supabase.com
   - SQL editor → paste `supabase/schema.sql` → run
   - Settings → API → project URL into `SUPABASE_URL`
   - Settings → API → `service_role` key into `SUPABASE_SERVICE_KEY`
   - The service role is for this server bot only. Do not put it in a browser app.

If Supabase env vars are empty, the bot still saves to `data/intel.sqlite3`.

```powershell
.\.venv\Scripts\python.exe run.py
```

Then open the bot in Telegram and send `/start`.

## CLI (no Telegram token needed)

```powershell
.\.venv\Scripts\python.exe run.py --once
.\.venv\Scripts\python.exe run.py --daily
.\.venv\Scripts\python.exe run.py --card polymarket
.\.venv\Scripts\python.exe run.py --search "founders fund"
```

`--once` and `--daily` both persist the scan to SQLite and to Supabase when configured.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Safety

- Never paste a seed, private key, or wallet-connect session into Telegram.
- Official CEX announcements live **inside the exchange app**. Telegram / X replies with "claim" links are drains.
- Use a burner wallet if you later farm anything yourself.
- Auto-detected names are **hints**, not confirmed drops.

Not financial advice. Allocations, dates, and eligibility change without notice.
