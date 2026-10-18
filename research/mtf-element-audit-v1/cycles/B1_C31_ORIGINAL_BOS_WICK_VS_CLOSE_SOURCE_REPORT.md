# B1/C31 — 539 original source 3m BOS: first wick touch vs later closed break

**Scope:** research-only PRICE TIMING COMPARISON, not a new entry strategy, not author-approved BOS/FTA/TP, **PAPER ONLY / NOT_TRADE_READY**. First 45 original source receipt obtained; independent full JSON/three Python-version matrix and A101 chain check pending.

## Primary academic course

[Author's 4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): intraday 1H fractal wick raid -> 3m/5m structure break, BOS must be below BSL raid / above SSL, stop beyond swept extreme, target opposing 1H liquidity avoiding intervening FTA. **Two distinct entry methods are listed:** direct market on price crossing BOS, **or** after candle confirmation then limit. Which actual candle swing/pivot author selects, intrabar order of stops/fills, FTA first obstacle priority and author session zone remain UNKNOWN.

[Author linked BackTest 1H/3M 2023.01–2023.07](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21) is not retrievable by user or public search; **this is a missing-source blocker**, not evidence that the source never existed.

External 2026 comparisons in [PUBLIC_BOS_EXAMPLES_SOURCE_PROVENANCE.md](B1_C31_PUBLIC_BOS_EXAMPLES_SOURCE_PROVENANCE.md) are explicitly **NON-author** analogs, especially Secuora's strict same-candle versus relaxed multi-event BTC/ETH Silver Bullet contrast and separately dated June 2026 FVG-retest example. No author pivot/entry/FTA taken from them. In particular, 2025–26 public BTC spot, gold and Nasdaq rules are NOT an original Jan–Jul 2023 instructor backtest and cannot certify 2026-09→10 Binance Futures 3m goldens.

## C31 exact source code and negative testing

`d05/c31_bos_entry_semantic_disagreement.py` reads ONLY original SHA-checked C21 USD-M native3m closed candles and C25 research-only parent cases; it **does not modify C20–C30**. For every frozen strict C21B 3m close-BOS candidate, separately records:

- The C21-selected **1+1 3m swing** center, known-after-right-3m close, its Decimal level, selected 3m research close and exact original Binance SHA bar identity.
- The first **earlier 3m wick cross** of that SAME retrospectively selected level since both the raid's 1H full confirmation and 3m swing's right-bar full confirmation, **before** technical C21 BOS bar starts. No current break bar is counted as an earlier observation.
- Distinct numbers for (a) earlier strict wick cross WITHOUT close, and (b) earlier CLOSED 3m price beyond swing; no false assumption that an intrabar price tick filled an order.
- Selected proxy BOS 3m break relative to HTF raided 1H fractal; elapsed time between completed 1H raid confirmation and start of technical break; alternative previous-calendar-day hypotheses UTC, Europe/Kyiv, Europe/London (NEVER author's certified IANA timezone/DST).
- Immutable source as-of physical prefix, source original SHA, linked C25 165 research singletons and 539 original C21 parent edges. All outputs `AUTHOR_SELECTED_BOS_PIVOT_UNKNOWN`, `MARKET_CROSS_VS_CLOSE_OR_LIMIT_UNKNOWN`, `AUTHOR_FTA_TP_PRIORITY_UNKNOWN`, 0 author-approved trades.

**17 adversarial guards** in `d05/test_c31_bos_entry_semantic_disagreement.py` passed first [C31 source negative CI 39175168906](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39175168906) **SUCCESS**: source time, pivot-right-close, wrong BSL/SSL side and swing type, wrong break bar, falsified price/source SHA, nonfinite prices, earlier wick-only vs earlier closed break as distinct outcomes, no inferred fill, and forged READY.

## Original 45 USD-M ZIP first source findings — pinned NOT author trades

Pinned `evidence/c31/C31_ORIGINAL_BOS_CROSS_VS_CLOSE_SOURCE.json`, immutable Git blob `38276d6d8a77942101a041d3605d72f69a7845d1`. 45 original Binance Futures 3m/15m/1d ZIP across BCH/BTC/ETH/SOL/XRP; 76,800 closed native3m bars, 15,360 exact native15m Decimal OHLCV parity. Retained **539** original strict closed-3m research parent edges and **165** surviving source-only singletons from the unchanged C21/C25 records.

| Asset | Research C21B 3m closed BOS | Earlier SAME selected swing wick crosses | Earlier close beyond SAME selected swing |
|---|---:|---:|---:|
| BCHUSDT | 99 | 22 | 0 |
| BTCUSDT | 104 | 23 | 0 |
| ETHUSDT | 129 | 30 | 0 |
| SOLUSDT | 103 | 31 | 0 |
| XRPUSDT | 104 | 16 | 0 |
| **TOTAL** | **539** | **122** | **0** |

**122/539 (22.6%)** C21 RESEARCH proxy events had an earlier original CLOSED 3m bar whose **wick** strictly crossed the retrospectively selected local swing but whose **close** failed to settle beyond it. **142 total earlier wick observations**, since multiple bars can test one event. NO prior close beyond the same selected swing in this scoped window — consistent with delayed selected-swing close-BOS logic. **83/539** C21 technical breaks start exactly at the following 1H raid-confirmation time; **2/539** begin more than 180 minutes after. These are historical SOURCE RELATIONS, **not 122 fillable earlier entries**. We lack actual tick order, order book, selected author BOS pivot, author current raid window/FTA and fill policy. Market crossing can occur before later bar close *if* the swing is actually the instructor's chosen one; we cannot infer any trade from this.

Alternate previous-calendar-day counts differ under UTC, Kyiv, London and do not establish course timezone. Do not import public ICT fixed 10:00 New York killzone as academy's 09:00–17:00 IANA time.

**Admission gate:** first source receipt and negative tests complete. Before C31 source-only [x], require independent re-download 45 original ZIP and complete JSON equality, Python 3.10/3.11/3.12 17 test matrix, append-only seven-file A101 SHA, independently verified 101/101 journal, map update. **Main trade readiness STILL BLOCKED by author BOS/FTA goldens and source Notion.**
