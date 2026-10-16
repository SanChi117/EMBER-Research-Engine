# B1/C20B — original 1H fractal wick sweep → 5m close-break diagnostic

**16 October 2026 — PAPER ONLY. Preliminary technical replay, NOT academic acceptance of a trade or author BOS.**

## Source / implementation / test

Source: original author's [Entry by BOS lesson](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view), with intraday 1H raid → 3m/5m BOS, wick-only raid, structure break below BSL or above SSL, fresh previous-session/day fractal, 1H FTA and session rules. The author's *3m example* is distinct from this diagnostic **5m** approximation. The author lesson has no independent timestamp-labelled Binance USD-M golden trade.

- `d05/c20b_hourly_fractal_source_observer.py`: derives fully closed 1H OHLC from twelve original native 5m candles, strict 3-candle 1H fractal high/low, **first** liquidity crossing only, wick-body exclusion, next **closed** 1H bar to establish raid fractal geometry, no guessed session timeout.
- `d05/c20b_five_minute_break_observer.py`: observes a 5m close through an already-known strict 3-candle 5m swing after raid confirmation. For BSL short, swing level below swept 1H level; for SSL long, swing above. A new extreme beyond the raid wick invalidates the candidate; the previous 5m close must have been on the unbroken side. Returns a source-row witness but **not** a certified author's BOS.
- 11 synthetic positive/adversarial tests `d05/test_c20b_closed_1h_5m_source_geometry.py` verify confirmation clocks, next-closed 5m candle, body-vs-wick, extreme invalidation, wrong source row, false ready status and future-prefix invariance.
- `tests/probe_c20b_original_hourly_5m_breaks.py` re-downloads **45 original USD-M ZIPs** and compares exact native 5m→15m→1h price aggregates. The earlier as-of calculation uses a separate C20 source prefix after independent revalidation.
- `evidence/c20/C20B_ORIGINAL_1H_5M_AGGREGATES.json` pins **historical aggregate counts only**; author labels and individual market entries are absent.

## Independent 32-day historical observation

| Symbol | 1H strict fractal levels | First confirmed 1H wick geometry | Subsequent research 5m close-break witnesses |
|---|---:|---:|---:|
| BTCUSDT | 378 | 124 | 101 |
| ETHUSDT | 387 | 156 | 122 |
| SOLUSDT | 374 | 117 | 98 |
| XRPUSDT | 368 | 125 | 97 |
| BCHUSDT | 366 | 120 | 94 |
| **Total** | **1,873** | **642** | **512** |

All 46,080 native 5m rows and 3,840 derived 1H candles were compared against original C08 source; zero author-approved BOS and zero trades. The 512 observations are **not independent signals** and can be temporally stale or ambiguously related to multiple liquidity levels.

Initial independent CI [38953779420](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38953779420) **SUCCESS**: 29 frozen course tests + 296 C10–C20B tests = **325 PASS**, original 45 source ZIP check and 1H reconciliation.

## Falsification / unresolved

- Frozen v05's 2+2 swing and 24h freshness are NOT quietly substituted for author 1+1 fractal and prior session rules.
- Lower-timeframe swing selection here is an **explicit research operationalization**. It lacks author-labelled 5m BOS goldens; cannot prove the right swing, exact intraday session, FTA, SL, TP or crypto pip conversion.
- Aggregate receipt was stored, and source replay has been updated to independently crosscheck it and earlier as-of. **The independent pinned rerun is now confirmed SUCCESS**: [CI 38957040304](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38957040304), with Git SHA `555be0425c68749b27a72e90e3bc2943f7afab64` for the pinned aggregate, 325 tests and 45 original ZIP network replay. The earlier workflow update block remains documented; it was resolved by separately editing the CI path trigger and proof SHA without changing C08/C20A frozen receipts.
- Full macro B1 stays PARTIAL. The current historical diagnostic is **NOT_TRADE_READY**, has no exchange order path and no measured profitability.

**Next needed:** append independent A087 evidence-chain journal proof; source-semantic validation of the correct author BOS structural pivot, prior-session freshness, FTA, stop placement and original 3m variant where claimed. No author approval implied. The 5m pivot choice is still an explicit research operationalization.
