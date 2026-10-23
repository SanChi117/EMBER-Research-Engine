# B1/C42 — independently gated prior-obstacle FTA source eligibility (not a target engine)

**Cycle date:** 2026-10-23. Research only: `PAPER ONLY / NOT_TRADE_READY`, **0 orders / 0 trades**. Preserves accepted academic core independently of all ADAPTED route variants. No profit prediction or actual trade backtest.

## 1. Fixed predecessor and precise question

C41/A111 immutable source join [independent CI 39835032870](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39835032870) PASS 111/111 SHA, last chain hash `eab55a801ed454f9266a80f87221e340211fcfc0d92913542f3deeca8df949c4`; frozen full original C41 source Git blob `ac3bb2b2babafdb28af71c4cbaa2b53fce03b06c`. C41's 4 BOS × 3 Reaction × 3 FTA = 36 source streams describe **17,316 correlated event-context copies**, not 17,316 unique orders.

C39's chosen possible FTA uses 1H obstacle source-known before BOS BAR START, **but ranks those candidates against retrospective 3m BOS candle CLOSE**, known only at that candle close. C40 detects prior original native3m wick touches between 1H source-known and the BOS BAR START. This C42 cycle tests what happens if the **same selected C39 obstacle** is considered under three explicit research-only prior-touch policies. These do NOT implement an academic or verified author freshness hierarchy. They are not C39 source mutations.

## 2. Three named and isolated ADAPTED eligibility gates

| Gate | Strict explicit predicate | What it cannot imply |
|---|---|---|
| `ANY_PREKNOWN_RESEARCH_OBSTACLE_V1` | C39 selected any pre-known 1H candidate source; allow even if previously touched/swept | Level freshness or target quality |
| `EXCLUDE_PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL_V1` | Selected candidate exists and C40 did not find prior strict fractal sweep or complete IMB traversal | A boundary-touched level is academically approved |
| `REQUIRE_NO_PRIOR_OBSERVED_TOUCH_V1` | Selected candidate exists and C40 found **no** prior touch in inspected source window | Lifetime untouched level, author selection, executable entry |

`NO_PREKNOWN_FTA_CANDIDATE` is rejected by all gates. Gate sets are nested `ANY >= EXCLUDE_STRICT >= REQUIRE_NONE`; each stored decision is explicitly `known_at = original BOS candle CLOSE`. No re-selection to alternate second-best candidate is performed. Excluding a touched selected obstacle leaves that route gated out instead of inventing a different profit target.

## 3. Independent source experiments, not historical trading performance

C42 implementation `d05/c42_adapted_source_fta_eligibility.py` constructs source-only `SourceEligibilityDecision/Context/Route/Matrix`; checks original C41 data types, symbols, chronological 1H obstacle availability, signed original 3m BOS time, parent source event IDs in joins, no incorrect touch-state/source-ID combinations, no future reaction/touch, no falsely early decision timestamp, never accepts forged READY/orders/author labels.

`d05/test_c42_adapted_source_fta_eligibility.py`: **25** fail-closed synthetic/adverse tests, including all four C40 states and three policy truth tables, no-candidate and illegal future known-at. First independent [CI 39990257408](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39990257408) **SUCCESS 3/3** Python 3.10, 3.11, 3.12; 25 tests per version, no skipped. Full A111 source SHA + all active previous evidence preserved.

`tests/probe_c42_original_fta_eligibility_45zip.py`: independently reads **45 original Binance USD-M SHA/checksum backed ZIP**, **76,800** original closed native3m and **15,360** exact Decimal native15m equalities, matches every original C42 annotated source context to frozen C41 full 36-route source event BOS ID, 1H source-known and original C40 prior contact classification; earlier `as_of` results physically identical with original native3m prefix cut. Original source witness remains 2026-09-01 through 2026-10-02, not an unseen or new OOS sample.

First archived source [CI 39990581621](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39990581621) **SUCCESS**, frozen JSON `evidence/c42/C42_ORIGINAL_SOURCE_FTA_ELIGIBILITY_45ZIP.json`, **40,865,150 bytes**, Git blob **`bddf315c58a906fe58546512bc416c24bd1ce95f`**. Independent [CI 39990993912](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39990993912) **SUCCESS 4/4 jobs**, 25/25 negative tests each Python 3.10, 3.11, 3.12, separate 45 original ZIP re-read and **exact complete 40.9 MB original JSON equality**. Immutable C38–C42 original source blobs individually reverified; 111/111 predecessor SHA evidence intact.

| C42 adapted policy | Correlated original source contexts satisfying predicate |
|---|---:|
| Any preknown research obstacle | **17,289** |
| Exclude prior strict sweep or full IMB traversal | **4,422** |
| Require no prior touch observed | **2,433** |

The same 36 source-route overlays can count a parent market event repeatedly. The policy reductions are **not** a measured edge, win rate, trade frequency or profitability. Across the 17,316 route-occurrences, 27 had no selected candidate; 12,867 selected obstacles had a prior strict sweep/full traversal; 1,989 had a boundary touch without strict sweep; 2,433 had no prior touch **observed in the inspected source window**. These four categories partition *correlated source occurrences*, not unique independent setups or fills.

## 4. Frozen six-file intended SHA journal A112 evidence

1. `d05/c42_adapted_source_fta_eligibility.py`
2. `d05/test_c42_adapted_source_fta_eligibility.py`
3. `tests/probe_c42_original_fta_eligibility_45zip.py`
4. `evidence/c42/C42_ORIGINAL_SOURCE_FTA_ELIGIBILITY_45ZIP.json`
5. `evidence/c42/C42_INDEPENDENT_SOURCE_WITNESS_20261023.json`
6. `cycles/B1_C42_SOURCE_ONLY_FTA_TOUCH_ELIGIBILITY_45ZIP_REPORT.md` (this file)

After proof: append-once `A112` ONLY with six SHA256 evidences and previous A111 source hash unchanged. A separate independent **112/112** SHA and evidence check is required for final source-only cycle acceptance. Never rewrite previous journal lines.

## 5. What is NOT verified and next falsification cycle

- NO independent **2023 instructor-labeled** author FTA / reaction / BOS positive+negative goldens; author terminology and exact source hierarchy may differ.
- Source `NO_PRIOR_SOURCE_TOUCH` does **not** mean lifetime untouched. The source dataset begins 2026-09-01; earlier market touches unknown. Native3m OHLC prior wick cross cannot give tick ordering, limit fills or stop trigger sequence.
- Filtering only the already selected C39 candidate can leave an apparently empty route despite other eligible 1H obstacles. **C43** may separately create source-causal *re-ranking among all candidates*, under distinct ADAPTED hypotheses, with explicit per-candidate raw3m touch history and fail-closed original ID checks. It must NOT silently mutate C39/C40/C42.
- Full algorithmic Route A IMB/SNR, Route B IDM, Route C raid→3m/5m BOS academic parity, MTF 1W/1D→4H POI, structural entry, rejection, stop/TP, order fill, fees/slippage/funding, independent OOS trade backtest and forward PAPER still missing. C42 gate not a fill or take-profit.
- The coarse development map remains **29 of 40** explicitly scoped checkpoints closed, **3 partial**, **8 pending**; not a percent trading readiness. Zero proposed/replayed orders, trades or profit figures. NOT_TRADE_READY.
