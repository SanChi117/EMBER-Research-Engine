# B1/C25 — original 1H/3m source: session-timezone uncertainty and 1H FTA/SL research bounds

Date: 2026-10-17. **PAPER ONLY. NOT_TRADE_READY. Zero author-approved trades or orders.**

## Exact author-grounded requirements and source limits

[4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) states: HTF wick-only fresh liquidity fractal raid, normally **1H raid → 3–5m BOS**, for SHORT structural BOS below BSL raid / LONG above SSL raid, liquidity formed **within previous session, at most previous day**, typically TP at first 1H liquidity / previous-session high or low, SL **beyond** raided 1H liquidity, invalidation for nearby FTA or large stop, no entry if no LTF BOS. Author trading clock mentions **09:00 Frankfurt → 17:00 NY Kill Zone**, with intermediate times, but **does not attest a machine-readable timezone/DST or crypto USD-M session calendar** in this supplied text. Forex 15-pip or 1–2-pip limits **must not** be reinterpreted as Binance USD-M price units. [ликвидність.txt](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view) specifies an actual 3-candle fractal, confirmed after adjacent following candle closes, separate EQH/EQL/compression zones.

No source permits treating the trader's local timezone, UTC, London or Kyiv as the author's official time. 09:00–17:00 in any of these timezones is an **explicit sensitivity experiment**, not an academic acceptance criterion. No author-labelled crypto BOS pivot, exact FTA threshold, intrabar market crossing or price buffer for SL has been verified. The linked 2023 Notion 1H/3m backtest was inaccessible through this research interface, and the attached screenshot was a course page rather than a time-labelled 2026 Binance chart.

## Implemented C25, isolated from frozen C21–C24

- `d05/c25_session_freshness_target_source.py` takes authentic original C21A native3m candles with original per-ZIP SHA, exact raw-row ID and closed-prefix proof. It first calls **frozen C24 strict fail-closed research BOS route**, keeps only 165 **research-single-pivot-single-parent** cases across the source period, and joins to the exact original parent raid/break using (fractal center, raid start, break start) plus original native3m raw-row ID. No route can become READY.
- For each C24 candidate, examine the original 1H **fractal center** vs original 1H wick raid time under each of three independently named IANA timezone interpretations: `UTC`, `Europe/Kyiv`, `Europe/London`. Record actual UTC offsets on each specific calendar date, including DST. Evaluate (a) fractal center was on the previous **local calendar day**, (b) previous local calendar day *and* local **09:00–17:00** origin, (c) raid local **09:00–17:00**. This is an **unverified calendar hypothesis**, not claimed author time. No ungrounded Saturday/Sunday trading-day restrictions for 24/7 USD-M.
- For each original C24 candidate, derive historical fully confirmed **opposing 1H fractal** known by the start of its 3m break candle, located strictly in the research trade direction; report **nearest opposing fractal price** as unapproved *geometric target candidate only*. It has **not** been established that this liquidity is unswept / acceptable FTA / first author liquidity / previous-session high/low, and this filter never counts as target approved.
- Report minimum unbuffered **price distance** from native3m observed **close** to original raided 1H wick extreme. Original author demands SL **beyond** the swept liquidity, so the exact buffer, executable fill, stop price, numerical Forex-pip limits and RR are all **unknown and never inferred**. Minimum unbuffered price span is not an order quantity or certified risk limit.

## Source protocol and negative tests

10 adversarial tests: strict previous local calendar day vs previous 09:00–17:00 origin, timezone calendar-date flip, London March DST UTC offset 0→+1, Kyiv DST +2→+3, forged timezone and future fractal refusal, future-confirmed 1H target refusal, wrong direction and equal-price target refused, native3m C24 single can NEVER become author-approved, prefix invariance, fake READY and original source-row forgery rejection. All PASS.

`tests/probe_c25_original3m_session_dst_target.py` downloads from original Binance Futures data **15 source-native 3m + 30 original C08 15m/1d ZIP**, with original paired checksums; independently rebuilds 32-day original candle history for BTC/ETH/SOL/XRP/BCH, original 3m rows and C08 price parity; independently replays identical earlier `as_of_ms` both on full source and on physically truncated verified source; freezes all per-coin timezone differences, 1H geometric target availability, invalid minimum stop price span, and 3 market raw-price witness cases per symbol. It cross-checks original C24 receipt per symbol for exactly 165 research singleton parent-edge links. All 165 remain `NOT_TRADE_READY`.

Independent first original CI: [39066741939](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39066741939) **SUCCESS**. The full receipt `evidence/c25/C25_ORIGINAL_SESSIONS_TARGET_SOURCE.json` Git blob `fe9b23672f97cdf1e50d603e7d214ecdef7a00ad`, frozen after original CI. Subsequent pinned original-source rerun and SHA ledger validation are required before marking this technical C25 [x].

## Actual 32-day research-source counts — DO NOT interpret as trading setups

| Metric across 165 research-only parent-edges | Value |
|---|---:|
| Source C21B parent research links | 539 |
| Source C24 single-pivot/single-1H-parent links | **165** |
| **Previous calendar-day** classification differs across three timezone hypotheses | **50** |
| **Previous calendar-day + 09–17 origin** classification differs | **10** |
| **Raid in local 09–17** classification differs | **44** |
| Historical opposing fully confirmed 1H fractal exists below SHORT / above LONG observed 3m close | **165/165** |
| Missing geometric historical opposing 1H candidate | 0 |
| Nonpositive unbuffered research price span to 1H raid extreme | 0 |
| Confirmed author timezone/session, FTA or structural SL | **0** |
| Author-approved trading signals or order placements | **0** |

Classification counts overlap; don't add the timezone-difference rows. The same original price bars produce **different session-freshness decisions** depending on local-zone interpretation. Previous-day classifications across original parent edges: UTC **42**, London **40**, Kyiv **42**; prior hypothetical 09–17 session origins: UTC **9**, London **7**, Kyiv **7**; raid hypothetical 09–17: UTC **42**, London **47**, Kyiv **50**. These are **experimental scenario counts**, not endorsed trading times, recommendations, source-labelled rules or FX pips for crypto.

## Exact unresolved gates / next source work

1. Timestamp-labelled *author original* positive AND negative BOS goldens that identify the chosen actual 3m structural pivot, real venue, timeframe, source date/time. The current screenshot does not supply this.
2. Source-verified timezone/DST/session boundaries; distinguish previous day/week and previous **trading** session vs a preceding calendar day. All current C25 timezone output is hypothesis only.
3. Source-verified prior-session extreme/1H target; whether nearest opposing fractal is already swept; FTA obstacle before target, RR and structural SL buffer. Only then build C26 **still source-research** verification for unswept 1H liquidity and FTA.
4. Author's 15 Forex pips are **not** USDT. Never auto convert, fabricate tick fill or infer execution from 3m OHLC.

Technical proof [x] only once pinned CI + A095 original-source journal pass. B1 macro remains partial; 29/40 higher-level tasks unchanged.
