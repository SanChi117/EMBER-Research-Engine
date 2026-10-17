# B1 / C26 — Original USD-M 1H unswept target and FTA forensic source

**Scope:** existing 1H-raid -> 3m technical first-intact singleton C24/C25 candidates, NOT original-author-approved BOS. PAPER ONLY / NOT_TRADE_READY. No changes to 45 initial academics, C21–C25, receipts, or SMOKE.

## Falsifiable hypothesis and reproducible causal contract

C25 reported 165/165 previously known geometric opposing 1H fractals but did NOT establish target liveness. C26 asks whether the closest *historical* opposing 1H 1+1 confirmed fractal on the research trade side remained unswept **as of break bar start**. A 1H fractal is preknown only when its right candle has closed (`known_ms <= break_start_ms`); after that, only original 3m bars with `known_ms <= break_start_ms` may invalidate it. A strict prior wick cross or close through proves already-crossed; strict price equality is segregated as unresolved, never assumed a crossing. The BOS 3m bar itself is excluded. A second farther un-crossed candidate remains `alternative hypothesis`, never silently replaces a swept first choice. Preknown intervening 1H levels are FTA *candidates*, not author-attested FTA. No arbitrary RR cutoff, trading session clock, fill price, stop buffer, or 3m within-bar tick order is inferred.

## First original-source receipt (45 ZIP)

- Frozen Git blob: `11edbf5ddf8e89e513fc3893e807903bbf8933eb`; location `evidence/c26/C26_UNSWEPT_1H_FTA_ORIGINAL_SOURCE.json` (full per-case original 3m row lineage and timestamps).
- 45 native original Binance USD-M Futures ZIP from the 32 UTC days 2026-09-01—2026-10-02, including 3m, 15m, 1d. 76,800 original native3m bars, 15,360 independent native15m Decimal OHLCV equalities across five symbols. C24 parent count unchanged: 539 parent edges; C24 singleton research count unchanged: 165.
- **Historical nearest target already crossed before BOS:** 137; **no earlier strict cross observed:** 28; **equality-only unknown:** 0; **no candidate:** 0. **Known intermediary 1H obstacle(s) before nearest:** 74. **Farther intact hypothetical alternatives found:** 164 (this includes cases whose original nearest is itself intact; NOT 164 approved alternate TP). **Same research-BOS bar marked dual endpoint reach:** 0 (this does not prove any tick ordering outside that bar).
- Symbol breakdown: BCHUSDT 45 cases, 36 crossed, 9 intact, 22 with obstacles; BTCUSDT 30/26/4/16; ETHUSDT 23/21/2/9; SOLUSDT 30/25/5/9; XRPUSDT 37/29/8/18. Crossed includes WICK_CROSS and BODY_CLOSE_THROUGH.

Independent source examples from full pinned receipt:
1. **Earlier close-through (negative target liveness):** BCHUSDT break `1788430500000`, original 3m row `c3192a1d7cd70d5dc19c80514eea7c3add87931378b89c6f43c1a85ae944ea92:1788430500000`. Price `248.66`, nearest geometric `246.70`, 1H target known `1788336000000`, first earlier strict wick `1788336180000`, earlier body close beyond `1788337260000`; two intermediary 1H level witnesses. `REJECT_ALREADY_SWEPT_TARGET`.
2. **Earlier wick-only cross (negative target liveness):** BTCUSDT break `1788518160000`, original source row suffix `:1788518160000`. Research close `81045.10`, nearest historical target `81267.60`, preknown at `1788501600000`, wick first crossed `1788513300000`, no earlier close beyond. `REJECT_ALREADY_SWEPT_TARGET`.
3. **No earlier cross (positive *technical* liveness only):** BTCUSDT break `1788312420000`, research price `77120.00`, 1H historical candidate `76883.60`, pivot known `1788303600000`, no earlier original3m wick/body crossing within causal interval. `NO_CROSS_OBSERVED` still leaves `FTA_THRESHOLD_AUTHOR_UNKNOWN`, `UNKNOWN_AUTHOR_SL_BUFFER`, and `UNKNOWN_AUTHOR_SESSION_DST`.

## Adversarial controls and admission

Separate new read-only files: `d05/c26_unswept_1h_fta_source.py`, `d05/test_c26_unswept_1h_fta_source.py` (18 tests), `tests/probe_c26_original3m_unswept_fta.py`, and independent source/CI workflows. Negative tests include prior wick, prior body close, equality, wrong-side, future/unconfirmed 1H fractal, multiple intervening levels, missing target, SHA and source-row tampering, false READY, physically truncated prefix, and impossible within-bar order claims. C25 timezone sensitivity (50/10/44 across UTC/London/Kyiv hypothetical scenes) has not been author-resolved.

**Verification status:** first source CI produced the frozen complete JSON above; the separate independent pinned 45-ZIP replay is required before A096 may mark C26 DONE. Do not treat code/receipt presence as independent end-to-end certification. After pinned success: log full evidence SHA256, append A096 to append-only journal, independently verify 96/96 and update map. B1 macro remains partial and 29/40 macro count unchanged.

## Limits, falsification and next research dependencies

The historic closest 1H fractal is a price-geometry candidate, not the author's TP; FTA obstacles here cover preknown 1H fractal levels and deliberately do NOT exhaust SNR, IMB, POI or prior-session structures. Source-native 3m OHLC cannot establish intrabar executable prices or SL/TP ordering. Author-labelled positive and negative Futures goldens (including exact selected 3m BOS pivot), author timezone/DST, prior-session policy, FTA threshold, SL buffer and independent frozen OOS backtest are still missing. No paper/live order or win-rate claim is permitted from these 165 dependent research links.
