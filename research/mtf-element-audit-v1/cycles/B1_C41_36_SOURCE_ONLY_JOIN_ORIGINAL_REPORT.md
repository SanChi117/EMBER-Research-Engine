# B1/C41 — Four BOS × Three Reaction × Three Potential FTA: original-source-only 36-route join

**Date:** 2026-10-22. **Scope:** chronological source-event JOIN, no author-approved setup, entry/TP/SL or returns. **PAPER ONLY · NOT_TRADE_READY**, orders 0, trades 0.

## 1. Dependence: immutable accepted C37–C40

C41 runs only after C39/A109 independent [109/109 CI 39832081581](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39832081581), C40/A110 independent [110/110 CI 39832669364](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39832669364). Last journal tip A110 `26a833aa16042c29826c510ddf3fb28f511de32478b81aad216de5c452b8cc4f`; neither academic core nor prior source evidence changed.

Frozen parent source Git blobs:
- C38 original 4 BOS × 3 reactions `a69d69de29d4b52a9ee68ccdf0dbcb20222a6440`.
- C39 original 4 BOS × 3 possible FTA `15dacbe47ba2b6e133d8b97d970a96d6242cd80f`.
- C40 original source prior touch `718ce971dd781b2046c530992b4c9743225ef5b7`.

## 2. Actual implementation

`d05/c41_source_only_bos_reaction_fta_join.py` introduces `C41SourceContext`, `C41SourceRoute`, `C41SourceMatrix`, `join_c41_source_records`, `scan_original_c41_source_matrix`. Four C37 distinct BOS streams are joined separately with C38 three adapted post-raid reactions, C39 three adapted selected historical 1H obstacle rankings, C40 prior source-touch states: **4 × 3 × 3 = 36 logical source routes**.

Selection join is keyed and cross-checked by **source symbol, as-of, academic core ID, 1H raid fractal center ID, original 3m BOS row ID, 3m BOS bar START and original BOS CLOSED known-at time**, *not* by fabricated execution or inferred OHLC fill. It rejects incomplete/duplicate/unknown routes, changed raw source candles, forged author approvals, forged READY, asset/as-of mismatch, missing parent counts, wrong reaction source row ID, future 3m reaction close, future known 1H potential obstacle, prior touch after BOS or before selected obstacle was known, and source lifecycle disagreement. It preserves the no-candidate/no-prior-touch/boundary/full-traversal state distinction.

The per-event C38 **reaction can only be confirmed between complete 1H raid confirmation and the original BOS 3m break candle START**. C39 potential FTA is already known before the BOS candle START, but its *selection by retrospective break candle CLOSE* is only a research comparison known after BOS closes. C40 prior touch can only use closed original 3m candles after source obstacle known and no later than BOS candle START. No order, stop, slippage, funding, tick sequencing, author freshness or win-rate inferred.

## 3. Tests, mistakes and independent falsification

- `d05/test_c41_source_only_bos_reaction_fta_join.py`: **19** source join and adverse cases. Initially independent [negative CI 39833392790](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39833392790) **FAILED** due to an invalid unit-test fixture assumption: a synthetic 220-bar sample contained no *positive* adapted reaction, but one negative test required it. Corrected test to forge a future reaction on the BOS candle deterministically and check rejection; original algorithm **not modified**. Independent [CI 39833541683](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39833541683) then **SUCCESS 19/19 × Python 3.10, 3.11, 3.12** (no skips).
- `tests/probe_c41_original_36route_source_45zip.py`: loads source fresh from **45** original Binance USD-M archives with old C08 receipt SHA and same-host Binance CHECKSUM, reconstructs **76,800** closed original3m and **15,360** exact Decimal native15m parities. Verifies source physically cut prefix at earlier `as_of` equals full-source earlier `as_of`. Recomputes all **36** original source joins for five markets.
- The probe individually compares **every C41 source observation in route order** to frozen C38 original reaction witness, C39 original selected potential source and C40 prior-touch classification, with exact same original BOS native3m raw ID, not only totals.
- First full original 45ZIP [CI 39833872654](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39833872654) SUCCESS, source data frozen at `evidence/c41/C41_ORIGINAL_36_SOURCE_JOIN_MATRIX.json`, **Git blob `ac3bb2b2babafdb28af71c4cbaa2b53fce03b06c`**.
- Independent [CI 39834278704](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39834278704) SUCCESS: 3 Python versions each independently verified A001–A110 active evidence and **19/19 C41 negative source tests**; separate job reloaded all original 45 ZIP, recomputed entire C41 original JSON and required exact full JSON equality to frozen Git blob. Independently verified pinned C38 C39 C40 C41 source blobs. Source counts: 45 ZIP, 76,800 original3m, 15,360 native15m Decimal, 36 routes, **17,316 correlated** source observations, author goldens 0, orders 0, trades 0.

Six source evidence files intended for append-once C41/A111:
1. `d05/c41_source_only_bos_reaction_fta_join.py`
2. `d05/test_c41_source_only_bos_reaction_fta_join.py`
3. `tests/probe_c41_original_36route_source_45zip.py`
4. `evidence/c41/C41_ORIGINAL_36_SOURCE_JOIN_MATRIX.json`
5. `evidence/c41/C41_INDEPENDENT_SOURCE_WITNESS_20261022.json`
6. `cycles/B1_C41_36_SOURCE_ONLY_JOIN_ORIGINAL_REPORT.md` (this document)

## 4. Interpretation and limitations

**36 combinatorial routes are not 36 independent executed trades.** There are 17,316 deliberately repeated/correlated BOS contexts across 5 markets/9 adapted child combinations for each BOS route. No academic 2023 author BOS/Reaction/FTA goldens. No genuine entry trigger acceptance, SL/TP, broker order acknowledgement, fills, funding, trading costs, realistic RR, profitability, independently unseen future dataset, or author course semantic parity. Same-host ZIP CHECKSUM plus frozen receipt is not an independent digital signature of market provenance.

C41 is research-engine integrated **source geometry only**, and cannot be promoted to PAPER trade validator. The coarse checklist remains **29/40 completed, 3 partial, 8 pending**. B1 [~], E semantic fidelity pending, Routes A/B/C pending, backtest F/G pending, H SMOKE integration pending.

## 5. Acceptance and next steps

C41 **[~] until A111**. Append once with the six files above after verifying independent 45ZIP results, then independent chain **111/111 SHA** across Python 3.10/3.11/3.12, checking each of six immutable evidence file bytes. No edits to accepted C37/C38/C39/C40 data.

After that, next C42 must address **source-only obstacle eligibility** and eventual validation of full route chronology against independent labelled source cases, and separately plan causal execution/exit simulator: prior 1H context, 4H POI, original BOS/Reaction ID, entry availability after closed BOS, first FTA source obstacle, structural SL, TP, stop-first in OHLC collision, fees, slippage and funding. Those features remain **unimplemented**; avoid creating retrospective trading claims from C41.
