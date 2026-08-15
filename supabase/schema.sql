-- Run this in the Supabase SQL editor once.
-- Project: Airdrop Intel Bot

create table if not exists airdrops (
  slug text primary key,
  name text not null,
  symbol text,
  status text,
  certainty text,
  category text,
  channel text,
  chains jsonb default '[]'::jsonb,
  summary text,
  reward text,
  eligibility text,
  tasks jsonb default '[]'::jsonb,
  funding jsonb default '[]'::jsonb,
  investors jsonb default '[]'::jsonb,
  links jsonb default '[]'::jsonb,
  sources jsonb default '[]'::jsonb,
  risk_notes jsonb default '[]'::jsonb,
  twitter text,
  tvl_usd numeric,
  score int,
  detected_from jsonb default '[]'::jsonb,
  news_hits jsonb default '[]'::jsonb,
  origin_url text,
  origin_title text,
  published_at timestamptz,
  first_seen timestamptz default now(),
  last_seen timestamptz default now()
);

create table if not exists detections (
  id bigint generated always as identity primary key,
  channel text not null,
  source_name text,
  title text not null,
  url text not null default '',
  body text,
  published_at timestamptz,
  seen_at timestamptz default now(),
  unique (channel, url, title)
);

create table if not exists daily_picks (
  pick_date date not null,
  rank int not null,
  slug text not null,
  score int,
  reason text,
  snapshot jsonb,
  created_at timestamptz default now(),
  primary key (pick_date, rank)
);

create table if not exists scans (
  id bigint generated always as identity primary key,
  started_at timestamptz,
  finished_at timestamptz default now(),
  counts jsonb,
  errors jsonb
);

create index if not exists airdrops_score_idx on airdrops (score desc);
create index if not exists airdrops_channel_idx on airdrops (channel);
create index if not exists detections_channel_idx on detections (channel, seen_at desc);
create index if not exists daily_picks_date_idx on daily_picks (pick_date desc);

alter table airdrops enable row level security;
alter table detections enable row level security;
alter table daily_picks enable row level security;
alter table scans enable row level security;

-- Service-role key used by the bot bypasses RLS.
-- Optional read-only access for a dashboard using the anon key:
do $$
begin
  if not exists (
    select 1 from pg_policies where tablename = 'airdrops' and policyname = 'public read airdrops'
  ) then
    create policy "public read airdrops" on airdrops for select using (true);
  end if;
  if not exists (
    select 1 from pg_policies where tablename = 'daily_picks' and policyname = 'public read daily_picks'
  ) then
    create policy "public read daily_picks" on daily_picks for select using (true);
  end if;
  if not exists (
    select 1 from pg_policies where tablename = 'detections' and policyname = 'public read detections'
  ) then
    create policy "public read detections" on detections for select using (true);
  end if;
end $$;
