from __future__ import annotations

from .models import Airdrop, FundingRound, Investor, Link, Task

# Curated research snapshot. Figures are publicly reported, not on-chain proofs.
# Status is marked honestly. Rumors stay rumors.


CAMPAIGN_BY_SLUG = {
    "polymarket": "trade",
    "metamask": "mainnet",
    "base": "mainnet",
    "opensea": "airdrop",
    "backpack": "trade",
    "hyperliquid": "trade",
    "layerzero": "bridge",
    "grass": "points",
    "meteora": "liquidity",
    "aztec": "testnet",
    "megaeth": "testnet",
    "edgex": "trade",
    "abstract": "mainnet",
    "n1": "trade",
    "rabby": "mainnet",
}

COST_BY_SLUG = {
    "polymarket": ("mid", "weeks"),
    "metamask": ("low", "weeks"),
    "base": ("low", "weeks"),
    "opensea": ("low", "weeks"),
    "backpack": ("mid", "weeks"),
    "hyperliquid": ("mid", "weeks"),
    "layerzero": ("low", "days"),
    "grass": ("gas", "weeks"),
    "meteora": ("high", "weeks"),
    "aztec": ("gas", "days"),
    "megaeth": ("gas", "days"),
    "edgex": ("mid", "weeks"),
    "abstract": ("low", "weeks"),
    "n1": ("mid", "days"),
    "rabby": ("gas", "weeks"),
}


def curated_airdrops() -> list[Airdrop]:
    items = [
        Airdrop(
            slug="polymarket",
            name="Polymarket",
            symbol="POLY (expected)",
            status="airdrop_confirmed",
            certainty="medium-low",
            category="Prediction Market",
            chains=["Polygon", "Ethereum"],
            summary=(
                "Largest prediction market. CMO Matthew Modabber said in Oct 2025 "
                "there will be a token and an airdrop. No tokenomics, date, or "
                "eligibility rules are published. US relaunch via QCX/CFTC is the "
                "gating item most reports cite."
            ),
            reward=(
                "Token + airdrop publicly confirmed; size unconfirmed. Some reports "
                "floated a large community distribution (treat as unverified). "
                "Live rewards today are USDC market-making / trading incentives, "
                "not the token."
            ),
            eligibility=(
                "No official snapshot rules. History of real trading and competitive "
                "limit-order liquidity is the consensus positioning. Wash volume is "
                "likely to be filtered."
            ),
            tasks=[
                Task("Use official app only", "https://polymarket.com — never a 'claim POLY' popup.", cost="free"),
                Task("Trade real markets", "Place and resolve informed trades. Size and consistency beat one-off spam."),
                Task("Provide liquidity", "Competitive limit orders on active markets. This is the live USDC reward path."),
                Task("Stay over time", "Build months of history. Late mercenary volume is a common Sybil filter."),
                Task("Ignore fake claim sites", "No official claim page exists until the team posts it on official channels."),
            ],
            funding=[
                FundingRound("$1B+", "Oct 2025", "Strategic", "Intercontinental Exchange", "ICE initial direct investment, widely reported at ~$2B total arrangement / ~$9B valuation."),
                FundingRound("$600M", "Mar 2026", "Follow-on", "Intercontinental Exchange", "Completed additional cash investment."),
                FundingRound("earlier rounds", "2020–2024", "Seed / VC", "Founders Fund", "Founders Fund, Blockchain Capital and others in earlier books."),
            ],
            investors=[
                Investor("Intercontinental Exchange (ICE / NYSE parent)", "lead / strategic"),
                Investor("Founders Fund", "early"),
                Investor("Blockchain Capital", "early"),
                Investor("General Catalyst", "reported"),
            ],
            links=[
                Link("Official site", "https://polymarket.com"),
                Link("X / Twitter", "https://x.com/Polymarket"),
                Link("Docs", "https://docs.polymarket.com"),
            ],
            sources=[
                "Polymarket CMO, Degenz Live, Oct 2025",
                "ICE press release, Mar 27 2026",
                "Fortune / ICE $2B arrangement reporting, Oct 2025",
            ],
            risk_notes=[
                "Airdrop confirmed in speech, not in a published token spec.",
                "US regulatory path can slip the timeline.",
                "Fake POLY claim sites will appear the moment a date leaks.",
            ],
            twitter="Polymarket",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="metamask",
            name="MetaMask",
            symbol="MASK (expected)",
            status="token_confirmed",
            certainty="medium",
            category="Wallet",
            chains=["Ethereum", "Linea", "Multi-chain"],
            summary=(
                "Consensys CEO Joseph Lubin confirmed a MetaMask token in Sep 2025 "
                "('sooner than you would expect'). Official Rewards seasons are live "
                "on the official wallet. No airdrop mechanics or date published."
            ),
            reward=(
                "Native $MASK expected. Season 1 Rewards reportedly distributed tens "
                "of millions of USD in partner/token incentives. Season points are "
                "widely treated as the eligibility precursor — not confirmed as the "
                "final airdrop formula."
            ),
            eligibility=(
                "Long-term real wallet use is the conservative thesis: swaps, bridge, "
                "portfolio, staking, Linea, and Rewards points. One-click 'claim' "
                "extensions are scams."
            ),
            tasks=[
                Task("Install only from official store", "https://metamask.io — developer must be Consensys.", cost="free"),
                Task("Join MetaMask Rewards", "Official path: https://metamask.io/rewards"),
                Task("Use native swap / bridge / stake", "In-wallet features, not random dApp claim pages."),
                Task("Use Portfolio and Linea", "Portfolio dashboard + Consensys L2 activity are commonly cited signals."),
                Task("Keep the same wallet", "History length matters more than spinning new seeds."),
            ],
            funding=[
                FundingRound("~$725M cumulative", "through 2022+", "Series D and prior", "Consensys", "Parent company Consensys, not a MetaMask-only round."),
                FundingRound("$450M", "2022", "Series D", "Temasek / Microsoft / SoftBank book", "Widely reported Consensys Series D."),
            ],
            investors=[
                Investor("Microsoft", "Consensys"),
                Investor("SoftBank", "Consensys"),
                Investor("Temasek", "Consensys"),
                Investor("Coinbase Ventures", "Consensys"),
                Investor("HSBC / JPMorgan / Mastercard / UBS", "reported strategic"),
            ],
            links=[
                Link("Official site", "https://metamask.io"),
                Link("Rewards", "https://metamask.io/rewards"),
                Link("X / Twitter", "https://x.com/MetaMask"),
                Link("Consensys", "https://consensys.io"),
            ],
            sources=[
                "The Block interview with Joseph Lubin, Sep 2025",
                "MetaMask official Rewards pages",
                "Public Consensys funding coverage",
            ],
            risk_notes=[
                "Token confirmed; airdrop formula is not.",
                "Never enter a seed into a 'MASK claim' website.",
                "Prediction-market dates are speculation, not a schedule.",
            ],
            twitter="MetaMask",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="base",
            name="Base",
            symbol="unconfirmed",
            status="exploring",
            certainty="medium-low",
            category="Layer 2",
            chains=["Base", "Ethereum"],
            summary=(
                "Coinbase L2. On 15 Sep 2025 Base said it began exploring a network "
                "token with no definitive plan. There is no confirmed airdrop. The "
                "Base app already has in-app rewards (content, USDC holds)."
            ),
            reward=(
                "No official token allocation. If a network token happens, ecosystem "
                "usage is the usual L2 template (bridge, apps, persistence). Do not "
                "treat this as confirmed."
            ),
            eligibility=(
                "Consistent Base-native history. Spam bridging and empty contract "
                "pings were filtered in other L2 drops and should be assumed here too."
            ),
            tasks=[
                Task("Use official portal", "https://base.org and https://www.base.org — not 'base-airdrop.xyz'."),
                Task("Bridge via official bridge", "Official Base bridge / Coinbase onramp."),
                Task("Use Base-native apps", "DEX, perps, social, and savings apps on Base."),
                Task("Base app activity", "In-app posting and USDC holds have live rewards today."),
                Task("Stay consistent", "Months of use beat a weekend of Sybil loops."),
            ],
            funding=[
                FundingRound("Coinbase-backed", "2023–", "Strategic / parent", "Coinbase", "Incubated and operated by Coinbase. Not a typical VC raise for the chain itself."),
            ],
            investors=[
                Investor("Coinbase", "parent / operator"),
                Investor("Optimism Superchain stack", "tech partner"),
            ],
            links=[
                Link("Official site", "https://www.base.org"),
                Link("Blog", "https://blog.base.org"),
                Link("X / Twitter", "https://x.com/base"),
                Link("Bridge", "https://bridge.base.org"),
            ],
            sources=[
                "Base blog: State of Base / Basecamp 2025",
                "Jesse Pollak public comments, Sep 2025",
            ],
            risk_notes=[
                "Exploring ≠ committed. Coinbase could choose not to issue a token.",
                "Any 'claim BASE now' site is a scam today.",
            ],
            twitter="base",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="opensea",
            name="OpenSea",
            symbol="SEA",
            status="delayed",
            certainty="medium",
            category="NFT Marketplace",
            chains=["Ethereum", "Base", "Polygon", "Multi-chain"],
            summary=(
                "SEA token confirmed Feb 2025. Community allocation around 50% of "
                "supply, with more than half of that described as an initial claim. "
                "Q1 2026 target slipped; March 2026 launch was postponed with no new date."
            ),
            reward=(
                "Official SEA token. ~50% of supply to community per team comments. "
                "Historical + recent marketplace activity both flagged as relevant."
            ),
            eligibility=(
                "Real NFT / marketplace history on OpenSea. Wash trading and fresh "
                "wash wallets are the obvious filter."
            ),
            tasks=[
                Task("Use official OpenSea only", "https://opensea.io — never a third-party SEA claim."),
                Task("Keep account history", "Buy/sell/list as a normal user."),
                Task("Recent + old activity", "Team said both historical and recent usage matter."),
                Task("Watch Foundation / official X", "Launch date will come from @opensea / @openseafdn, not Telegram forwards."),
            ],
            funding=[
                FundingRound("$300M", "2022", "Series C", "Paradigm / Coatue", "Reported $13.3B valuation."),
                FundingRound("earlier", "2021", "Series A/B", "a16z", "a16z led earlier growth rounds."),
            ],
            investors=[
                Investor("Andreessen Horowitz (a16z)", "early lead"),
                Investor("Paradigm", "Series C"),
                Investor("Coatue", "Series C"),
                Investor("Coinbase Ventures", "reported"),
            ],
            links=[
                Link("Official site", "https://opensea.io"),
                Link("X / Twitter", "https://x.com/opensea"),
                Link("Foundation", "https://x.com/openseafdn"),
            ],
            sources=[
                "OpenSea Foundation SEA announcement, Feb 2025",
                "CoinDesk Q1 2026 launch confirmation, Oct 2025",
                "Devin Finzer delay post, Mar 2026",
            ],
            risk_notes=[
                "Token is official; the date is not.",
                "SEA ticker scams (same-name tokens on random chains) are common.",
            ],
            twitter="opensea",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="backpack",
            name="Backpack",
            symbol="TGE planned",
            status="points_live",
            certainty="medium-high",
            category="Exchange / Wallet",
            chains=["Solana", "Eclipse"],
            summary=(
                "Wallet + exchange. Team posted a TGE plan (Feb 2026): 25% of supply "
                "to community — 24% to points holders, 1% to Mad Lads. Multi-season "
                "points program (Season 4 started Nov 2025)."
            ),
            reward="25% community (24% points, 1% Mad Lads) per official TGE plan.",
            eligibility="Points seasons on Backpack Exchange + Mad Lads NFT holders for the 1% sleeve.",
            tasks=[
                Task("Official app / exchange", "https://backpack.app — verify the domain."),
                Task("Earn exchange points", "Spot and perps volume during live seasons."),
                Task("Stay through seasons", "Points are seasonal; dropping off resets your rank."),
                Task("Mad Lads (optional)", "1% sleeve is NFT-gated per the TGE plan."),
            ],
            funding=[
                FundingRound("$17M", "2023", "Series A", "Placeholder / Multicoin", "Widely reported wallet/exchange raise."),
                FundingRound("later book ~$37M cited", "2024–2025", "follow-on / reported", "", "Secondary reporting; confirm on official posts."),
            ],
            investors=[
                Investor("Placeholder", "lead / early"),
                Investor("Multicoin Capital", "lead / early"),
                Investor("Anatoly Yakovenko", "angel, reported"),
            ],
            links=[
                Link("Official site", "https://backpack.app"),
                Link("X / Twitter", "https://x.com/Backpack"),
            ],
            sources=[
                "Backpack TGE plan post, Feb 9 2026",
                "CoinGecko upcoming airdrops note, 2026",
            ],
            risk_notes=["Exchange risk and custody risk if you deposit. Prefer withdrawable funds only."],
            twitter="Backpack",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="hyperliquid",
            name="Hyperliquid",
            symbol="HYPE",
            status="points_live",
            certainty="medium-high",
            category="Perp DEX",
            chains=["Hyperliquid", "Arbitrum"],
            summary=(
                "Largest onchain perp DEX. Genesis airdrop already happened. Tokenomics "
                "reserve ~38.88% of supply for future emissions, so later community "
                "distributions remain the thesis — not a first-time drop."
            ),
            reward=(
                "HYPE is live. Future emissions / assistance funds are the remaining "
                "upside. No published next-airdrop checklist."
            ),
            eligibility="Active trading, staking HYPE, vaults / LP, long-term use.",
            tasks=[
                Task("Official app", "https://app.hyperliquid.xyz"),
                Task("Trade perps", "Real flow, not wash volume."),
                Task("Stake HYPE", "If you already received or bought HYPE."),
                Task("Vaults / LP", "Provide inventory where you understand the risk."),
            ],
            funding=[
                FundingRound("self-funded / no traditional VC book", "—", "n/a", "", "Commonly cited as not VC-backed in the usual sense."),
            ],
            investors=[
                Investor("No classic lead VC", "community / team"),
            ],
            links=[
                Link("Official app", "https://app.hyperliquid.xyz"),
                Link("X / Twitter", "https://x.com/HyperliquidX"),
            ],
            sources=["Hyperliquid tokenomics", "DefiLlama TVL"],
            risk_notes=["Perp trading can lose the farm capital. Size down."],
            twitter="HyperliquidX",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="layerzero",
            name="LayerZero",
            symbol="ZRO",
            status="points_live",
            certainty="medium-high",
            category="Interop / Infra",
            chains=["Multi-chain"],
            summary=(
                "ZRO is live. Foundation says 38.3% of supply is community; 15.3% is "
                "reserved for future initiatives / later snapshots. Feb 2026: Zero L1 "
                "plus Tether investment; CEO said no new token — ZRO stays the asset."
            ),
            reward="Possible future ZRO snapshots from the reserved community sleeve.",
            eligibility="Real cross-chain usage via Stargate and partner apps. Spam bridges were slashed in round 1.",
            tasks=[
                Task("Official portal", "https://layerzero.network"),
                Task("Stargate", "https://stargate.finance — real transfers."),
                Task("Partner apps", "Use apps that actually settle via LayerZero."),
                Task("Spread over time", "One-day Sybil loops were filtered before."),
            ],
            funding=[
                FundingRound("$120M+", "2022–2023", "Series A/B", "a16z / Sequoia / others", "Widely reported growth rounds."),
                FundingRound("strategic", "2026", "Strategic", "Tether", "Tether investment; Citadel Securities and Ark as advisors."),
            ],
            investors=[
                Investor("a16z", "lead"),
                Investor("Sequoia", "lead"),
                Investor("Circle", "strategic"),
                Investor("Tether", "2026 strategic"),
                Investor("Citadel Securities", "advisor"),
                Investor("ARK Invest / Cathie Wood", "advisor"),
            ],
            links=[
                Link("Official site", "https://layerzero.network"),
                Link("Foundation", "https://layerzero.foundation"),
                Link("X / Twitter", "https://x.com/LayerZero_Labs"),
            ],
            sources=["LayerZero Foundation ZRO post", "LayerZero Core Feb 2026 Zero L1 post"],
            risk_notes=["Round 1 already happened. Future rounds are reserved, not promised on a date."],
            twitter="LayerZero_Labs",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="grass",
            name="Grass",
            symbol="GRASS",
            status="points_live",
            certainty="medium",
            category="DePIN / Bandwidth",
            chains=["Solana"],
            summary=(
                "Share unused bandwidth. First airdrop was 28 Oct 2024. Foundation "
                "describes later interval airdrops tied to points / uptime. This is "
                "a continuing program, not a first claim."
            ),
            reward="Periodic GRASS distributions via Grass Foundation; points from uptime and network usage.",
            eligibility="Install official app, stay online, accumulate Uptime / Network points.",
            tasks=[
                Task("Official app only", "https://www.grass.io"),
                Task("Keep it running", "Uptime is the product."),
                Task("Stable connection", "Residential-quality links score better than flaky VPS stories."),
                Task("Referrals optional", "Referrals can add points; bought referral farms get filtered."),
            ],
            funding=[
                FundingRound("reported VC book", "2024", "Seed / Series", "Polychain / Tribe (reported)", "Confirm on official fundraising posts."),
            ],
            investors=[
                Investor("Polychain Capital", "reported"),
                Investor("Tribe Capital", "reported"),
            ],
            links=[
                Link("Official site", "https://www.grass.io"),
                Link("X / Twitter", "https://x.com/grass"),
            ],
            sources=["grass.io", "Grass Foundation first airdrop, Oct 2024"],
            risk_notes=["Only install the official desktop/browser node. Fake 'Grass miners' are malware."],
            twitter="grass",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="meteora",
            name="Meteora",
            symbol="MET",
            status="ended",
            certainty="high",
            category="DEX / Liquidity",
            chains=["Solana"],
            summary=(
                "Solana DLMM. MET is live. Season 2 claim was announced through "
                "23 Apr 2026. Further seasons are possible; treat new 'claim' links "
                "as hostile until posted by @MeteoraAG."
            ),
            reward="MET already distributed across seasons. Watch official channels for later seasons.",
            eligibility="Productive LP (fee-generating DLMM positions), not idle one-deposit farming.",
            tasks=[
                Task("Official app", "https://app.meteora.ag"),
                Task("Provide fee-generating LP", "DLMM in pools that actually trade."),
                Task("Follow season rules", "Past seasons had claim-page + optional NFT distributor paths."),
            ],
            funding=[
                FundingRound("Jupiter / Solana ecosystem", "—", "ecosystem", "Jupiter alignment", "Tight Jupiter ecosystem relationship."),
            ],
            investors=[
                Investor("Jupiter ecosystem", "alignment"),
            ],
            links=[
                Link("Official app", "https://app.meteora.ag"),
                Link("X / Twitter", "https://x.com/MeteoraAG"),
            ],
            sources=["Meteora Season 2 claim posts, 2026", "DefiLlama"],
            risk_notes=["IL and smart-contract risk on LP. Token is already live — no mystery claim page."],
            twitter="MeteoraAG",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="aztec",
            name="Aztec",
            symbol="AZTEC (expected)",
            status="rumored",
            certainty="medium-low",
            category="ZK / Privacy L2",
            chains=["Ethereum", "Aztec"],
            summary=(
                "Privacy ZK network. Large historical raises. Community expects a "
                "token for operators / testers / network users. Treat any current "
                "claim page as fake unless it is posted on aztec.network."
            ),
            reward="Unconfirmed. Testnet / operator / privacy-app usage is the usual thesis.",
            eligibility="Testnet participation, node / operator work, and real private-tx usage if mainnet is open.",
            tasks=[
                Task("Official site", "https://aztec.network"),
                Task("Docs + testnet", "Follow official testnet / operator guides only."),
                Task("No social-connect claim farms", "Discord 'support' claim bots are drainers."),
            ],
            funding=[
                FundingRound("$100M", "2022", "Series B", "a16z", "Widely reported."),
                FundingRound("later book ~$17M cited", "2025", "reported", "", "Secondary 2025/26 coverage; verify on official posts."),
            ],
            investors=[
                Investor("a16z", "lead"),
                Investor("Paradigm", "reported"),
            ],
            links=[
                Link("Official site", "https://aztec.network"),
                Link("X / Twitter", "https://x.com/aztecnetwork"),
            ],
            sources=["Public Series B coverage", "2026 airdrop-roundup articles (rumor-grade)"],
            risk_notes=["Still rumor-grade on the token itself. Do not sign 'AZTEC airdrop' permits."],
            twitter="aztecnetwork",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="megaeth",
            name="MegaETH",
            symbol="MEGA (expected)",
            status="rumored",
            certainty="medium-low",
            category="High-perf L2",
            chains=["MegaETH", "Ethereum"],
            summary=(
                "Realtime Ethereum L2 with a large 2025 raise and public testnet. "
                "Token launch has been a prediction-market topic through 2026. "
                "Confirm current TGE status on official channels before doing anything."
            ),
            reward="Unconfirmed community allocation. Testnet / ecosystem usage is the usual positioning.",
            eligibility="Official testnet, apps on MegaETH, and any published points program only.",
            tasks=[
                Task("Official site", "https://megaeth.com"),
                Task("Official testnet / apps", "Only links from megaeth.com or the official X."),
                Task("Ignore TG 'claim MEGA' bots", "Standard drainer pattern."),
            ],
            funding=[
                FundingRound("$20M seed + later book", "2024–2025", "Seed / reported", "Dragonfly / angels", "Vitalik cited as angel in multiple reports; later ~$100M figures circulated — treat as reported."),
            ],
            investors=[
                Investor("Dragonfly", "reported lead"),
                Investor("Vitalik Buterin", "angel, reported"),
                Investor("Robot Ventures", "reported"),
                Investor("Figment Capital", "reported"),
            ],
            links=[
                Link("Official site", "https://megaeth.com"),
                Link("X / Twitter", "https://x.com/megaeth"),
            ],
            sources=["Public 2024–25 raise coverage", "Polymarket token-launch markets 2026"],
            risk_notes=["Status moves fast. Re-check official X before interacting."],
            twitter="megaeth",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="edgex",
            name="edgeX",
            symbol="EDGE (rumored)",
            status="rumored",
            certainty="low",
            category="Perp DEX",
            chains=["Multi-chain"],
            summary=(
                "Perp DEX frequently listed on 2026 airdrop roundups. Points-style "
                "trading programs are the usual path. Verify any points dashboard "
                "against the official domain only."
            ),
            reward="Unconfirmed. Trading-points → token is the rumor template.",
            eligibility="Real perp volume on the official venue. Wash volume is toxic.",
            tasks=[
                Task("Find official domain from X", "Start at the verified @edgeX_exchange (or current official handle) — do not Google Ads."),
                Task("Trade small, real size", "Do not over-farm with leverage you cannot lose."),
            ],
            funding=[
                FundingRound("undisclosed / verify", "—", "", "", "Do not trust random 'raised $XXm' cards without a primary source."),
            ],
            investors=[],
            links=[
                Link("Research starting point", "https://x.com/search?q=edgeX%20official"),
            ],
            sources=["2026 airdrop roundup lists (low-certainty)"],
            risk_notes=["Low-certainty name. Domain impersonation risk is high."],
            twitter="",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="abstract",
            name="Abstract",
            symbol="check official",
            status="rumored",
            certainty="medium-low",
            category="Consumer L2",
            chains=["Abstract", "Ethereum"],
            summary=(
                "Igloo / Pudgy-adjacent consumer chain. Often bundled with NFT and "
                "consumer-app airdrop theses. Confirm whether a points season or "
                "token is actually live before spending gas."
            ),
            reward="Unconfirmed / check official. Consumer-app and NFT ecosystem usage is the thesis.",
            eligibility="Official portal activity, ecosystem apps, and NFT history if a season is published.",
            tasks=[
                Task("Official site", "https://abs.xyz"),
                Task("Ecosystem apps only", "Links from abs.xyz or the official X."),
            ],
            funding=[
                FundingRound("Igloo / Pudgy ecosystem", "—", "ecosystem", "Igloo Inc.", "Consumer-brand backing rather than a classic L2 raise card."),
            ],
            investors=[
                Investor("Igloo Inc. / Pudgy Penguins", "ecosystem"),
            ],
            links=[
                Link("Official site", "https://abs.xyz"),
                Link("X / Twitter", "https://x.com/AbstractChain"),
            ],
            sources=["Public Abstract / Igloo coverage", "2026 airdrop lists"],
            risk_notes=["Brand confusion with fake 'Abstract airdrop' tokens on other chains."],
            twitter="AbstractChain",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="n1",
            name="N1",
            symbol="unconfirmed",
            status="rumored",
            certainty="low",
            category="Exchange / Infra",
            chains=["N1"],
            summary=(
                "Appears on 2026 'biggest upcoming airdrop' lists and has a live "
                "DefiLlama bridge listing. Treat as research-only until the team "
                "publishes a points or token post."
            ),
            reward="Unconfirmed.",
            eligibility="Official app usage only. No published checklist.",
            tasks=[
                Task("Official app", "https://app.n1.xyz/ — confirm domain against official X."),
                Task("Do not sign mystery permits", "No official claim flow is assumed."),
            ],
            funding=[],
            investors=[],
            links=[
                Link("App", "https://app.n1.xyz/"),
            ],
            sources=["2026 airdrop listicles", "DefiLlama N1 Exchange Bridge"],
            risk_notes=["Low primary-source coverage. High impersonation risk."],
            twitter="",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
        Airdrop(
            slug="rabby",
            name="Rabby Wallet",
            symbol="unconfirmed",
            status="rumored",
            certainty="low",
            category="Wallet",
            chains=["Multi-chain"],
            summary=(
                "DeBank-built wallet. Recurring airdrop rumor because DeBank had a "
                "points culture. No official token announcement should be assumed."
            ),
            reward="Unconfirmed. Do not pay for 'Rabby airdrop' access.",
            eligibility="Organic wallet use if a program is ever announced.",
            tasks=[
                Task("Official download", "https://rabby.io only."),
                Task("Use as a daily wallet", "Swaps / dapp connect via Rabby if you already need a wallet."),
            ],
            funding=[
                FundingRound("DeBank / Rabby book", "historical", "", "Coinbase Ventures (DeBank, reported)", "Parent DeBank raise, not a Rabby token sale."),
            ],
            investors=[
                Investor("Coinbase Ventures", "DeBank, reported"),
            ],
            links=[
                Link("Official site", "https://rabby.io"),
                Link("X / Twitter", "https://x.com/Rabby_io"),
            ],
            sources=["Public DeBank/Rabby coverage"],
            risk_notes=["Pure rumor. Fake Rabby extensions exist — only the official store."],
            twitter="Rabby_io",
            last_verified="2026-08-15",
            detected_from=["catalog"],
        ),
    ]
    for item in items:
        item.campaign_type = CAMPAIGN_BY_SLUG.get(item.slug, item.campaign_type)
        if item.slug in COST_BY_SLUG:
            item.capital, item.effort = COST_BY_SLUG[item.slug]
    return items


def catalog_by_slug() -> dict[str, Airdrop]:
    return {item.slug: item for item in curated_airdrops()}
