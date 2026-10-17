# B1/C22B — 3m BOS pivot alternatives, primary-source annotation remains unavailable

Date: 2026-10-17. **PAPER ONLY**. This cycle does NOT approve a trade, an academic BOS, FTA, entry, target, SL or profit.

## Source-first limits

The directly fetched academic lesson [4. Entry by BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) says HTF liquidity is raided and LTF BOS follows (often 1H→3–5m); for short BOS is below BSL; for long above SSL; crossing at market and entry after price confirms are both discussed; lack of **3m BOS** explicitly invalidates the illustrated 1H/3m case. It requires prior-session fresh fractal, a meaningful nearby 1H/previous-session take profit and SL beyond swept liquidity. **It does NOT specify an independently timestamp-labelled Binance USD-M Futures 3m BOS structural pivot or a universal rule to select one of several qualifying 3m structure levels.** A course diagram is not a Binance 2026 price golden.

Direct Drive folder `4. Entry By BOS` holds the author text and `Снимок экрана (2102).png`, with no independently verified Binance Futures instrument/candle/author-selected pivot annotation. Text links to 2023-01→07 Notion backtest, but that page was inaccessible to the present research tool; its 2023-era examples are not interchangeable with our independent Binance Futures 2026-09→10 dataset. These evidence blockers are recorded in `evidence/c22/C22B_AUTHOR_BOS_LABEL_PROVENANCE_GATE.json`.

## Audited engineering rule, not author rule

The preexisting frozen C21B author-*unapproved* proxy selects the **latest** strict 3-candle native3m swing which was fully confirmed before the observed break, formed after the first 1H wick raid, and lies spatially below BSL / above SSL. C22B neither modifies the frozen code nor pretends this pivot choice is author intent.

`d05/c22b_source_inventory.py` rebuilds the immutable C21B native3m source bars, recomputes each of the **539** C21B parent-edge crossings and enumerates **ALL other confirmed eligible swings** known by the same bar. The raw original Binance row ID, no future timestamps, source 1H raid parent, raid-relative structural region, and strict close-cross equality are checked. It separately counts (1) eligible previously confirmed pivots and (2) alternative pivots **also crossed on that same 3m bar**. It does not automatically label trades, choose a nearest/most recent author BOS, or merge multiple HTF parent edges.

`d05/test_c22b_source_inventory.py` verifies eight synthetic source positive/negative examples including two rival swings crossed on same bar, an unbroken alternate swing, no signal before next 1H confirmation, no future 3m candle, SHA-invalid native bar, false READY and historical prefix independence. Synthetic is NOT author golden.

`tests/probe_c22b_native3m_pivot_alternatives.py` independently re-downloads **45 original Binance USD-M ZIP** (15 native3m Sept monthly + Oct1/2 daily, 30 frozen native15m/1d), checks paired original .CHECKSUM and exact 5x3m-to-original15m Decimal OHLCV for **76,800** source3m and **15,360** independently native15m, verifies source original C21B per-symbol counts sum to 539, checks earlier independent as-of 2026-10-02 prefix stability, and compares pinned `evidence/c22/C22B_ORIGINAL_PIVOT_ALTERNATIVES.json` byte-equivalent JSON. The new source evidence Git blob is `87bc70ed12cf77bf444a019cb48ef38d907ac5f3`.

## Original source counts — not independent trades

| Market | 3m break parent edges | Edges with multiple eligible pivots | Edges crossing additional pivots on same bar | Other eligible pivots |
|---|---:|---:|---:|---:|
| BCHUSDT | 99 | 99 | 52 | 523 |
| BTCUSDT | 104 | 104 | 66 | 598 |
| ETHUSDT | 129 | 129 | 85 | 693 |
| SOLUSDT | 103 | 103 | 60 | 527 |
| XRPUSDT | 104 | 104 | 63 | 513 |
| **TOTAL** | **539** | **539** | **326** | **2,854** |

Across these 539 edge-wise observations, 3,393 total eligible native3m pivot options existed, including the algorithm's 539 chosen pivots. In 326 edges the same closing 3m candle also crossed at least one alternate previously known structural pivot, with 626 such extra simultaneous level-crossing *relations*. Counts of pivot choices/relations are not distinct OHLC bars, independent author BOS, tradable opportunities or profitable trades.

## Proof and forced uncertainty

First original-source CI [39058701833](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39058701833) **SUCCESS** (8 new C22B adversarial tests + 24 earlier C21B/C22A, original source tests and first 45ZIP replay). Later pinned receipt replay and A092 SHA journal must pass independently before checking this technical cycle [x]. If a legitimate author's positive/negative BOS timestamped case appears, compare original chart's stated venue/date/time and explicitly selected structural pivot to this research candidate set. **Without it, the correct author 3m swing remains UNKNOWN, no trade approval, NOT_TRADE_READY.**

Next C22C: original author session timezone and previous-session fresh fractal, auditable LTF structure alternatives, 1H target/FTA/structural SL and genuine author goldens. Do not interpret FX 15 pips as Binance USD-M point value. No real-time trading, orders, PNL or fees are evaluated here.
