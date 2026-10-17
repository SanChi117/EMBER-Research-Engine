# B1/C23 — first-intact 3m structure: eliminating previously broken BOS proxies

Date: 2026-10-17. Scope: **original native Binance USD-M Futures 3m 32-day source replay, PAPER ONLY**. No author-approved BOS, position, execution, FTA, SL, PNL or profitable strategy is claimed.

## Why this addresses the largest engineering defect, not the unknowable author labels

The original academy [4. Entry by BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) explicitly requires **HTF liquidity raid, LTF BOS** (typically 1H→3–5m), the structural break must be **below BSL raid for short / above SSL raid for long**, a genuinely wick-only raid and fresh fractal, appropriate prior session/1H target and SL beyond raided liquidity. Entry at price crossing and confirmed/limit entry are alternative execution modes, **not equivalent**. The academy [Fractals / Liquidity](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view) defines a three-candle high/low fractal, only confirmed when the third candle has closed.

**Not in source:** a unique algorithm ranking multiple 3m swings, native 2026 USD-M author-labelled positive/negative BOS cases, tick execution order, confirmed author timezone/DST. The course folder's screenshot is a screen capture of the source lesson and does not independently label Binance Futures price candles. The linked 2023 Notion 1H3m backtest could not be accessed. Historical native3m candles cannot reveal private author subjective pivot choices. None of these gaps may be filled by an assertion of author-equivalent BOS.

## What has now changed, without breaking C21/C22 evidence

The frozen C21B research proxy used **the latest known strict 3m fractal** as if it were a candidate BOS, but the C22B audit found **3,393** potentially eligible swing-level relations spread across 539 original HTF raid-parent edges. That count includes *previously broken and now stale levels*, i.e. a flaw in even a research interpretation of a **first** BOS.

New separate immutable **C23** module `d05/c23_first_intact_pivot_guard.py`:
- starts from every source-native 3m closed candle and first confirmed 1H wick raid already proven by C21A/C21B, checking original ZIP SHA, row ID, UTC 3m grid, complete as-of prefix and no false READY;
- for every candidate 3m swing fully formed before the candidate first close-break bar, replay **ALL earlier closed 3m bars since the swing became known**. Mark as **previously close broken** if an earlier candle **close** already lay strictly beyond that level (directional comparison short/long). Keep equality unbroken; separately record prior **wick** breaches for future market-on-cross models;
- keep only the source confirmed pivots not previously close-broken and identify the levels for which the **current closed 3m candle crosses strictly beyond** with the previous close on the other side;
- classify every original C21B research parent-edge as **one first-closed crossing**, **multiple first-closed crossings (ABSTAIN)** or **none (ABSTAIN)**. This is *engineering source validation*, not evidence of which swing the author would choose. Multiple HTF parent edges on one 3m candle are preserved and cannot be auto-deduplicated into a trade.
- refrain from doing anything to live exchange endpoints. For **all** 539 cases, readiness remains `NOT_TRADE_READY`, author-approved trades and BOS remain **zero**.

The source model intentionally **does not** rewrite frozen C21B/C22B JSONs nor quietly relabel their older candidate counts. It provides a stricter audit and future research-level gate.

## Original independent Binance price result (Sep 1 — Oct 2 2026, 5 USD-M symbols)

| C23 first-intact source observation | Original 3m source result |
|---|---:|
| Previously registered research parent-break edges | **539** |
| Historical source-confirmed eligible 3m swing-level options | **3,393** |
| **Previously close-broken levels** (stale first-break claims) | **1,408** |
| Still close-intact levels | **1,985** |
| Prior wick-breached levels (separate state; overlap with close-broken) | **1,947** |
| Same-bar **first** closed-level crossings (including alternatives) | **904** |
| Parent-edge cases with **exactly one** first-closed level | **285** |
| Parent-edge cases with **multiple** first-closed levels | **242** |
| Parent-edge cases with **no** first-closed level | **12** |
| Cases where legacy C21B latest pivot **was already close-broken** | **13** |
| HTF multiple-parent edge links on common native 3m break bars | **258** |
| Author-labelled USD-M BOS/trades | **0 / 0** |

All counts are **parent-edge relations**, not unique orders or author BOS labels. Note that a single first intact pivot on one parent does **not** mean a unique 3m trade; parent ambiguity may remain. The 1,408 stale options expose exactly why the earlier C22B aggregate 2,854 "rival" options must not all be interpreted as viable first-break structures.

All five original symbols BTC/ETH/SOL/XRP/BCH, original **15 new 3m + 30 original C08 15m/1d ZIPs** independently re-downloaded with paired source `.CHECKSUM` and exact native 5x3m→15m `Decimal` OHLCV; 76,800 original 3m and **15,360/15,360** original source 15m equalities. Independent earlier source-prefix test proves no later-than-as-of 3m data enters a decision. Eight explicit positive/negative synthetic tests include future/unclosed 3m, original source SHA tamper, false READY, strict equality, earlier-wick-not-earlier-close, as-of-prefix equality and unknown 1H raid.

Original source receipt pinned **`evidence/c23/C23_ORIGINAL_FIRST_INTACT_PIVOT_RESULT.json`**, Git blob **`b2fd86941fb1f2fcf11f656d230015577c58b021`**.

Original CI [39063009219](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39063009219) **SUCCESS**. Pinning and repeat independent source CI [39063199392](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39063199392) must be independently accepted before final journal mark.

## Remaining proof gates

**C23 addresses stale first-break pivots. It does NOT establish that the author prefers one particular surviving swing.** Do not promote 285 single first-closed levels to trade READY; require an externally author-annotated goldens and independent validation, proper session freshness and timezone, correct 1H liquidity FTA/TP, SL beyond swept level and real tick data for market-on-cross execution. Existing 242 multiple first-break alternatives and 258 extra parent edges remain **ambiguous**. The correct academic response is to preserve ambiguity and refuse unsupported automatic entry.
