# B1/C44 — causal source FTA boundedness, original 45 ZIP (ADAPTED research only)

Date 2026-10-23. **PAPER ONLY / NOT_TRADE_READY. Zero orders, zero fills, zero trades.** C44 does NOT certify original course 4H/1D POI, author FIRST TROUBLE AREA, or any profitable execution strategy. Source parameters are independent explicit research alternatives, not hyperparameters fitted to past returns.

## 1. Predecessor preserved and precise test hypothesis

Historical C43/A113 independently source-accepted SHA ledger tip `f8a397096e2199133ded9d08dc81f8112f5ea27b3b1675851c26c008568354f8`, [independent CI 40001101592](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40001101592) **113/113 PASS** and **entire 168,774,218 byte C43 canonical JSON SHA `92956d189574d2a13a0f8aa3f5aa9f99ddd4cc33dcb128c3fbb2b9b8fc30e791`**, original C43 manifest pinned Git blob `c1db4afec81cb240f981e6e0ef2211044c75e372`. Original C41/C42 sources unchanged.

C43 could select any earlier 1H candidate from unbounded original Sep–Oct source history. Almost every repeated research context gained a candidate even under untouched restrictions (17,262/17,316 correlated route overlays). **C44 falsification question:** does a source-only **finite age and forward price-distance** constraint restrict availability, and what further happens if the chosen potential candidate is required to lie inside the previous closed 4H or previous closed 1D **OHLC range**? No assumed academic POI semantics are smuggled in.

## 2. Four separate ADAPTED bounded candidate filters

Every candidate is independently reconstructed from original 1H fractal source or classic 1H three-bar imbalance, proven by the original 1H source-known time and original native3m source row IDs; prior touch/sweep independently checked on original native3m bars **fully closed after obstacle was known and strictly before BOS candle starts**.

| Policy ID (ADAPTED) | Rule |
|---|---|
| `NT_SOURCE_MAX_24H_MAX_1PCT_ADAPTED_V1` | C43 `NO_PRIOR_SOURCE_TOUCH`, source age at BOS bar **START** <=24 hours, source price strictly ahead of retrospective BOS close, distance <=1% |
| `NT_SOURCE_MAX_72H_MAX_3PCT_ADAPTED_V1` | Same no-touch, age <=72 hours, source distance <=3% |
| `NT_72H_3PCT_PREV_CLOSED_4H_RANGE_PROXY_V1` | Same 72h/3%, plus candidate original 1H level lies between previous **fully closed** native-original-3m aggregated 4H candle LOW–HIGH |
| `NT_72H_3PCT_PREV_CLOSED_1D_RANGE_PROXY_V1` | Same 72h/3%, plus candidate original 1H level lies between previous **fully closed** native-original-3m aggregated 1D candle LOW–HIGH |

4H/1D benchmark windows close before BOS bar start (no partial current 4H/1D bar). If no completed 4H/1D range exists, that benchmark filter fails closed. Explicit `source.age`, `distance_pct`, `previous_closed_4h_start`, `previous_closed_1d_start`, parent C43 unbounded untouched selected candidate ID, C44 selected original row provenance, retrospective decision-known-at BOS **CLOSE**, 36 research routes and all 4 individual source policy decisions are retained for each context. No orders/targets/returns. **This is not an academic POI or SNR replacement.**

Thresholds 24/72h and 1%/3% were declared before running the 45 original ZIP archive, *not* selected against profitability; source availability on reused historical data does not establish predictive performance or author parity. The three C39 FTA family ranking variants still apply independently. C44 uses the C43 all-candidate audited source rather than C42's first-only candidate; past C43 results used as original raw-id regression oracle.

## 3. Adversarial CI and implementation corrections (unhidden)

- C44 `d05/c44_adapted_bounded_source_fta.py`, `d05/test_c44_adapted_bounded_source_fta.py`: **31** tests of exact Decimal 24h/72h and 1%/3% boundaries, zero/future source, source-available and 4H/1D native fully closed windows, C43 parent IDs, nested filter relationships, no invented author POI/orders. Initial GitHub workflow [40007987234](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40007987234) failed YAML job naming and did not execute tests; fixed. Next [40008062183](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40008062183) failed setup because test code referenced nonexistent `ReRankContext.original_bos_closed_ms`; fixed. Next [40008146520](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40008146520) failed setup due parent renamed fields; fixed. Finally independent [CI 40008214776](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40008214776) **SUCCESS 3/3** × Python 3.10/3.11/3.12, **31/31 each** (93 passes), 113/113 predecessor SHA verified.
- Original complete 45 ZIP replay `tests/probe_c44_original_bounded_source_45zip.py`. Source bridge reads original Binance USD-M ZIP with SHA/CHECKSUM C08, **76,800 original 3m** closed bars, **15,360 exact Decimal native15m**; each new bounded context checked against original C43 five-market source Git SHA manifest, same raw 3m BOS ID, original 1H raid center, BOS start/close, reaction status, no-touch selected source ID; early-as-of source prefix results match physically cut input exactly.
- First original 45ZIP [CI 40008446069](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40008446069) **SUCCESS**, froze **97,764,435 byte** full original JSON `evidence/c44/C44_ORIGINAL_BOUNDED_FTA_SOURCE_45ZIP.json`, immutable Git blob `0f8cd79824af85569ffef87bfbec808a8a2b89b3`. Original source repeated contexts 17,316, 36 4×3×3 routes, 4 new bounded policies; no author source golden, trade or order. 
- **Independent second [CI 40008979006](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40008979006) SUCCESS 4/4 jobs**: all original 45 ZIP freshly downloaded and processed again; complete archived JSON **exactly byte-equal for all 97,764,435 bytes** (not summary only); SHA-256 `62a8ef144a045733e2cdc35592056417916c9ab6db41e2dc8ffb9ea0c41f4892`; three other independent Python 3.10/3.11/3.12 jobs each revalidated previous A113 113/113 SHA and **31/31** C44 negative tests, no skips. New witness `evidence/c44/C44_INDEPENDENT_ORIGINAL_SOURCE_WITNESS_20261023.json` frozen. **A114 still requires separate append-once and independent 114/114 CI before final acceptance.**

## 4. First archived research result — not performance

| C44 selected source criterion | 36-route correlated context occurrences with an eligible research obstacle |
|---|---:|
| 24h / 1% untouched | **11,106** |
| 72h / 3% untouched | **16,578** |
| 72h / 3% plus previous closed 4H range proxy | **11,466** |
| 72h / 3% plus previous closed 1D range proxy | **14,211** |

C43 unlimited untouched policy selected an obstacle in **17,262** correlated route copies. Restricting a candidate source by age and distance changes how often a *potential source candidate* exists, **not the accuracy of a signal, FTA reached, stop distance, RR, win rate or profit**. The same parent BOS repeats for three reactions × three FTA family hypotheses, and some shared source candidate sets yield near-duplicated contexts. Period is historical only; a large untested market regime and original 2023 course labels are missing. The native original3m OHLC low/high cannot prove intrabar sequencing of any order.

## 5. A114 intended SHA evidence and next stage

With independent 45ZIP PASS and frozen witness, append-once A114 with SHA256 of **six files**: new C44 module, 31-test suite, complete 45ZIP replay probe, full 97,764,435 byte original C44 JSON, independent witness, this report. Separate 114/114 independent chain/evidence check on Python 3.10/3.11/3.12 remains mandatory before source-only closure. Keep C39–C43 entirely immutable.

After source-only C44 closure, continue toward real academic semantic fidelity: original course 4H/1D POI and IDM/IMB/SNR/BOS author-labeled examples; C45 must NOT silently replace true POI with previous candle range proxy. Do not introduce retrospective parameter optimization on same source period. Need separately held-out source to test any thesis before live/paper fills. Academic Route A/B/C, structural SL/TP, fees/slippage/funding and end-to-end paper trade execution not validated; `PAPER ONLY / NOT_TRADE_READY`. Coarse development map count **29/40 [x], 3 [~], 8 pending unchanged**, not system completion %.
