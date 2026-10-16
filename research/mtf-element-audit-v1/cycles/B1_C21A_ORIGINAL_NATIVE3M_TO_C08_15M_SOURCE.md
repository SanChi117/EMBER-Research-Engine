# B1/C21A — original 32-day native 3m Futures source proof against frozen C08 15m

Date: 2026-10-17. Research-only **PAPER ONLY**. This acceptance applies to **historical source data**; NOT author-approved BOS, entry, exit, order, PNL or signal.

## What the original academic author actually requires

[Entry by BOS — direct course original](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): typical intraday execution involves a **1H fractal wick liquidity raid** and a BOS on **3–5m**. The author illustrates a specific **1H→3m** example and explicitly disqualifies the illustrated model without **3m BOS**, even if the raid and target look correct. BOS must be spatially below swept BSL (short) / above swept SSL (long). Separate author requirements: fresh raided fractal from prior session, not older than previous day; session-based timing, FTA/correct target, structural SL. Timezone of this course's workday 09–17 and crypto-equivalent pip conversion are **not verified**. Those missing semantics are not filled from generic trading conventions.

[Liquidity / Fractals / Raid](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): a strict 3-candle fractal is only confirmed after its next candle closes; a clean liquidity raid is by wick. A source 3m candle set does not itself establish an authorized BOS.

## Engineering: verify NEW 3m prices without mutating frozen source

- New module `d05/c21_native3m_source_bridge.py`, distinct `Original3mRow`, `Original3mArchive`, `C21Native3mResult`, 180000-ms native closed grid and original raw-row SHA references, all market prices exact Python `Decimal`, independent strict Futures USD-M **HTTPS only** path and authorized 5 C08 symbols.
- Original files: Binance USD-M original September **monthly 3m** + Oct 1 and 2 **daily 3m**, 3 new original archive ZIPs per symbol = **15 entirely NEW 3m source ZIP**. Every original ZIP binary SHA256 is matched to its paired **same-host** original `.CHECKSUM`; CSV byte SHA256 separately pinned. This is integrity+same-host check, **not an independently signed oracle**.
- No waiver of previous D04/C08 15m/1d allowed source set. Original C08 source [previously frozen](../evidence/c08/C08_315_AGGREGATE.json) is independently re-downloaded unchanged using its existing receipts. Total network source 15 new 3m plus 30 previously frozen 15m/1d archives = 45 ZIP.
- All 76,800 original closed 3m candles (15,360/symbol) must reconstruct **all 15,360 native independently sourced 15m original OHLCV** (3,072/symbol), via five consecutive 3m bars each: O = first, H=max, L=min, C=last, V=exact Decimal sum; UTC start/last end close aligned. Frozen C16 also verifies 160 original native1d parities (32/symbol).
- `tests/probe_c21_native3m_futures_32day.py` never trusts file names without HTTPS/recomputed ZIP SHA/.CHECKSUM, performs full replay and verified earlier as-of 2026-10-02 00:03 prefix **14,881 3m bars/symbol**, never looks into later bars. Pins every new archive and original raw CSV SHA individually.
- `d05/test_c21_native3m_source_bridge.py` contains **15 synthetic adversarial/positive tests** for original period/time/12 CSV columns, host, checksum, extra ZIP members, gaps, nonfinite OHLCV, tampered 3m input, incomplete original source, false author READY and original 15m Decimal reconstruction. Synthetic ZIP `zipfile` headers are *not* treated as immutable academic price goldens.

## Result (original Binance USD-M Futures, 2026-09-01 to 2026-10-02 UTC)

| Symbol | New 3m original ZIP | Native 3m closed | Exact native 15m matches | Native 1d source matches |
|---|---:|---:|---:|---:|
| BTCUSDT | 3 | 15,360 | 3,072 | 32 |
| ETHUSDT | 3 | 15,360 | 3,072 | 32 |
| SOLUSDT | 3 | 15,360 | 3,072 | 32 |
| XRPUSDT | 3 | 15,360 | 3,072 | 32 |
| BCHUSDT | 3 | 15,360 | 3,072 | 32 |
| **Total** | **15** | **76,800** | **15,360 / 15,360** | **160 / 160** |

Independent original source/15 synthetic test CI [38968923699](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38968923699): **SUCCESS**. All fifteen archive binary SHA and CSV SHA pinned in `evidence/c21/C21A_NATIVE3M_C08_PARITY_RECEIPT.json`. The newer source CI is explicitly pinned to the receipt Git blob `02949d457e63bb367bbb99ae087e3306d1e68557`.

### Retain failed attempt as evidence

A first workflow edit [38969092408](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38969092408) FAILED workflow YAML after JS replacement accidentally interpolated literal `$` in the test regex and duplicated part of the workflow. The *new workflow itself* was repaired by exact substring boundaries and not by changing Binance price source, course rules or frozen historical C08. Both attempts remain in Actions history.

## Explicit boundary / next C21B

**C21A proves price-source parity ONLY.** It does not certify a structural 3m BOS, distinguish market crossing vs candle close at a trigger, select the correct author-annotated swing, qualify earlier session freshness or RR/FTA or exchange entry. The original author labels with Binance USD-M timestamps **do not exist here**, so there are **0 approved trades**, **0 certified BOS** and `NOT_TRADE_READY`.

C21B must compare 1H raid → actual native **3m** potential structures to the existing 5m research operationalization, **retain ALL parent ambiguity and timing states** and explicitly falsify any ungrounded 3m=5m equivalence. Then author context and source-labelled positive+negative examples are still needed. No real Binance connections or orders.
