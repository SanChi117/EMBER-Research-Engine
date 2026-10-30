# C115 — SOURCE_BLOCKED (cross-archive OHLC disagrees), no economic claim

**2026-10-30; C114 A177 source-blocked retained.** C115 prereg was a source-only format reconciliation: treat volume mismatches as diagnostic while demanding absolutely identical original Binance daily native3m/native5m reconstructed 15m OHLC, times and provider SHA/CHECKSUM. Historical two windows, same entry/SL/TP/matching/bootstraps as C114. No economic parameters tuned.

CI: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41109660961

The 8 C115 source contract tests and 23 C114 adverse tests PASSED on Python 3.10/3.11/3.12 (plus regressions). The full 2025-01 archive sourcing then failed at the PRICE strictness gate, **before any signal or PnL computation**:

- Symbol: XLMUSDT (second in the fixed universe after BNBUSDT; first failure in that symbol).
- UTC original native3m native5m reconciling 15m bucket index 2694 (2025-01-29 01:30–01:45 UTC).
- Both series price/timestamp 15m: open **0.39616**, high **0.39730**, close **0.39656** identical.
- **LOW mismatch: 3m=0.39478, 5m=0.39467**. Difference **0.00011 XLMUSDT** (roughly **2.78 basis points**).
- This divergence can change a stop/target first passage as the strategy is price and OHLC based. Therefore C115 SOURCE_BLOCKED is mandatory. No changing source trust policy to pretend tests passed.

Independent original 3m and 5m Binance Vision ZIP individually passed official checksum and 12-column CSV clock checks. Passing provider SHA proves that they were unaltered, not that the time aggregations agree with each other.

The previous C114 source mismatch, BNBUSDT 15m bucket 1302, volume 24700.27 vs 31675.04 (~22.02%), is not the same as this XLM low-price mismatch.

**Verdict: SOURCE_BLOCKED / NO_TRADE / NO_PNL / LIVE_BLOCKED.** Not an economic rejection of the 4H-zone/5m-CHoCH premise and not a green economic experiment either. Keep original C114/C115 evidence and CI failed jobs. No sample change/coin exclusion/favorable low correction/posthoc smoothing allowed. Future independent research needs canonical single-source (e.g. original Binance native1m) aggregation into consistent 3m and 5m, with precise labelling that these are derived and NOT independent originals; precommit first, then any new data. Existing C114/C115 profitability gates must remain untouched.
