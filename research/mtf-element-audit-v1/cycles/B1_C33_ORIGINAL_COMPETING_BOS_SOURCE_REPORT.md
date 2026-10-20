# B1/C33 — original 3m BOS swing competition, C21 proxy vs author ambiguity

**Scope:** source-only C33 original 45 Binance USD-M Futures ZIP **first pinned receipt obtained**, 27/27 adversarial tests [CI 39454279240](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39454279240) PASS. Independent full JSON replay of 45 original ZIP and Python 3.10/3.11/3.12 27-negative matrix **PASSED** [CI 39455216429](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455216429); independent witness frozen Git blob `7c432fd16a554dfadd0536590aafa7c17610231d`. Append-only A103 / final independent 103/103 SHA still pending. **NOT author 3m BOS, FTA, trade, TP, SL; PAPER ONLY · NOT_TRADE_READY.**

## Primary academy and exact unknown

Author's [4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) requires higher TF 1H wick liquidity raid + 3m/5m structure BOS **on the correct side** of swept BSL/SSL. Original source distinguishes market at price crossing from confirmation then limit. The course does **not** define an algorithm choosing the exact author 3m BOS pivot from multiple qualifying native price swings.

The original [Notion BackTest 1H/3M Jan–Jul 2023](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21) remains unavailable; no positive/negative case charts label author BOS swing. External ICT analogs are not a source of instructor labeling. The C21 frozen 1+1 strict **last-preknown** swing heuristic is only an unapproved research proxy.

## Mechanism built

`d05/c33_preknown_competing_bos_swings.py` **isolates** 1H raid → 3m pivot candidate enumeration, with NO new arbitrarily chosen pivot ranking.

For every frozen C21 original 3m BOS technical parent, enumerate **all** source-confirmed strict 1-left/1-right native3m LOW/HIGH swings whose (a) center was after 1H raid began, (b) original right-hand 3m bar CLOSED and pivot became known before source BOS candle START, (c) price is on correct side of raid BSL/SSL level, and (d) original three raw SHA-linked 3m candles satisfy strict center LOW/HIGH geometry. All selected 3m pivots, competing pivots, source IDs and source time known-at are preserved.

For each candidate record first strict OHLC wick price reach at/after the later of the previous 1H raid full confirmation or candidate's 3m swing confirmation, strictly before or during C21 selected technical close-break candle; never infer intra-bar tick ordering/fills. The original C21 selected LAST-confirmed research proxy is tagged explicitly; when other source pivots exist, **AUTHOR_BOS_PIVOT_AMBIGUOUS**, but no subjective selection, 0 author-approved goldens, 0 orders.

`d05/test_c33_preknown_competing_bos_swings.py`: 27 negative and causal integrity checks (strict future right candle, 1H raid time, wrong BSL/SSL, fabricated Decimal swing, original three row SHA, center pivot correct price, physical source as-of, forged `READY`, missing selected source, duplicate candidates). Initial [CI 39454193235](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39454193235) failed before running tests because authored Python unit test contained a literal escaped newline. Fixed only test-file spelling; [CI 39454279240](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39454279240) 27/27 PASS. Error remains documented in cross-chat handoff.

## First exact original 45 ZIP SOURCE result (awaiting independent rerun)

Original full case receipt `evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json`, Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df` (5.8 MB complete JSON). 45 SHA-pinned original 3m, 15m, 1d Binance USD-M ZIP across BCH/BTC/ETH/SOL/XRP, 76,800 native3m closed rows, 15,360 exact original 15m Decimal parity, 539 unchanged C21 research close BOS parent observations / 165 C24 singleton cases.

| Pair | Research BOS events | Multiple strict preknown 3m swing options | Original source swing relations | Most per event |
|---|---:|---:|---:|---:|
| BCHUSDT | 99 | 99 | 984 | 16 |
| BTCUSDT | 104 | 104 | 1,058 | 18 |
| ETHUSDT | 129 | 129 | 1,301 | 17 |
| SOLUSDT | 103 | 103 | 970 | 18 |
| XRPUSDT | 104 | 104 | 972 | 15 |
| **TOTAL** | **539** | **539** | **5,285** | **18** |

All 539 research source events had **2 or more** strictly eligible local native3m technical pivot witnesses at the same source break instant; exactly one pivot among those was C21's last preknown strict 1+1 heuristic. **ZERO** events had unique available pivot given these broad C21 source rules. This is a strong falsification of *'the source data themselves uniquely determine the instructor's BOS level'*. But it does **not** mean all 5,285 alternatives are author-valid or simultaneous actionable trades; missing author filters, session, first FTA and liquidity context may invalidate them.

**No author pivot confidence score, BOS target price or trade selected**. All observations `NEEDS_AUTHOR_1H_3M_POSITIVE_NEGATIVE_GOLDENS` and `NOT_TRADE_READY`. The original as-of physical prefix was independently checked against source truncation within the first experiment, but independent second 45 ZIP replay and 103/103 journal pending.

## Why this matters for future work

The blocker is not search speed, use of another generic MSS detector, or 'add more filters': it is missing the author's operational instruction for selecting ONE of multiple structurally eligible source swings, and what qualifies as local BOS after specific raid reaction. Thus the next meaningful research must focus on obtaining instructor's **annotated source case** (or authored precise text identifying selected 3m swing) and comparing author label vs ALL 5,285 source candidates.

Success of CI will close only technical C33 ambiguity enumeration; it cannot make the larger B1 author entry engine READY. Original full frozen JSON was independently replayed exactly, negative tests PASSED on three Python versions, witness pinned. Before C33 source-only final [x]: append-once A103 with six-source SHA and 103/103 independent full original ZIP replay; then update map and cross-chat handoff.
