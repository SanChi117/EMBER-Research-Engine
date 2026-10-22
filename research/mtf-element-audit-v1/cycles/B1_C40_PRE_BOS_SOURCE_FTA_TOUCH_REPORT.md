# B1/C40 — native3m PRIOR-touch states for C39 potential 1H FTA

**Freeze date:** 2026-10-22. **Scope:** 1H source obstacle interaction before BOS original native3m break BAR START. Source-only research, NOT instructor-certified FTA, NOT trading backtest. **PAPER ONLY · NOT_TRADE_READY**, 0 orders and 0 trades.

## Immutable parent / causal intent

C39 `d05/c39_adapted_preknown_fta_source.py` selects three expressly ADAPTED potential obstacle families against four independently timed C37 source BOS variants. Candidate 1H levels are confirmed by their final original native3m row and have `source_known_ms <= break_bar_start_ms`; C39 ranks candidate using **retrospective BOS 3m CLOSE**. This is not an actionable entry/target price known at BOS bar START.

C40 adds `d05/c40_pre_bos_fta_touch_state.py` with its own original3m source verification. It reconstructs 1H source tuples from 20 original 3m bars/hour, validates corresponding exact 1H confirmed fractal or 3-candle classic IMB original source row IDs, and scans only **closed native3m bars** whose `known_ms > selected.source_known_ms` and `known_ms <= BOS.break_bar_start_ms`. It never counts a 3m bar from within or after the BOS candle as prior touch.

For a directional fractal, touching the boundary and strict sweep have different classifications. For an IMB, any interval overlap and full interval traversal are separate. The **first** touch and **first** full traversal are original bar open timestamp + row ID when applicable; wick OHLC does not determine intra-candle sequencing or execution fills.

## Four states and interpretation

- `NO_PREKNOWN_FTA_CANDIDATE` — no eligible C39 source family ahead of retrospective BOS close.
- `NO_PRIOR_SOURCE_TOUCH` — no prior interaction **within inspected source window**, not proof of lifetime freshness.
- `PRIOR_BOUNDARY_TOUCH` — original native3m wick meets level/zone, no strict sweep/full interval traversal in the pre-BOS source window.
- `PRIOR_STRICT_SWEEP_OR_FULL_TRAVERSAL` — original native3m evidence strictly breaches fractal or completely traverses the IMB zone before BOS.

These are state observations, **not independent events or trades**. Some events may share BOS bars and original raid parents. C40 does **not** retroactively disqualify already-touched obstacles from C39; such filtering is a future explicitly separate ADAPTED eligibility hypothesis, requiring independent tests. Academic source does not certify author FTA freshness/priority, structural entry/SL/TP, execution or expectancy.

## Independent source reread + falsification

**Source artifacts (all are repository paths):**

1. `d05/c40_pre_bos_fta_touch_state.py` — exact source time/ID and four state classifications.
2. `d05/test_c40_pre_bos_fta_touch_state.py` — 19 adverse controls: future 1H obstacle refusal, forged author approval / orders refusal, original native3m SHA mismatch rejection, source-prefix equality, unsupported levels/families, bad Decimal values, and no PnL assertions.
3. `tests/probe_c40_original_fta_prior_touch_45zip.py` — re-fetch original Binance Futures USD-M 15m, 1d, 3m archives; validate pinned receipts and source names; build 1H and exact Decimal 15m reconciliations; recompute all 12 source streams; check exact entire JSON against frozen original.
4. `evidence/c40/C40_ORIGINAL_PRE_BOS_PRIOR_FTA_TOUCH_STATES.json` — frozen original full 45ZIP result, Git blob **`718ce971dd781b2046c530992b4c9743225ef5b7`** (immutable).
5. `evidence/c40/C40_INDEPENDENT_SOURCE_WITNESS_20261022.json` — independently observed runner status/limits and immutable SHA IDs, NOT a new author label or new source data.
6. This report.

**Earlier independent runner:** [CI 39516049254](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39516049254), head `daddd1d90a2e29e86648b22eb3f6d17ea84ffea9`, 4 successful jobs: 19 C40 tests for each Python 3.10/3.11/3.12 + original 45ZIP entire JSON equality.

**Independent successor runner:** [CI 39831134857](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39831134857), source-checker commit `212a05ffa3b433098aa7d2193459ad47658a020e`, **SUCCESS 4/4**: three Python versions each independently verify A001–A108 ledger + all active evidence, run **33 C39 + 19 C40** negative tests; separate 3.11 job downloads source ZIP for C39 then C40 and matches *entire* frozen original source JSON exactly. Pinned Git blobs C37, C38, C39, C40 and prior C39 witness are individually compared against Git. Original 45 ZIP, **76,800** original closed3m, **15,360** native15m precise Decimal parities; 4 BOS × 3 FTA = **12** correlated source streams.

**Negative correction record:** the first successor CI [39830996018](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39830996018) did not pass overall because successor checker incorrectly reused C40's evidence field names for C39. Fixed checker in `212a05ffa3b433098aa7d2193459ad47658a020e`; successfully reran independent entire source. No original/academic module changes from correction.

C40 example source classification for `LATEST_CONFIRMED_V1::CLOSEST_PRIOR_1H_OBSTACLE_V1`: no candidate **2**, no previous touch **78**, boundary touch **58**, strict sweep or full gap traversal **401**, totaling **539** correlated research BOS contexts, not fills. All C40 12-route source observations preserve source IDs; author FTA-freshness confirmed **0**, orders **0**, trades **0**, `NOT_TRADE_READY`.

## Source boundary and adversarial conclusion

Static code audit and tests demonstrate C40's prior-touch history is restricted to source level fully-known through BOS original3m BAR START and excludes suffix/forward 3m candles in tested paths. They do **not** constitute a proof about all possible unseen bugs, source provider independence (Binance checksum is same-host), nonobserved history before 2026-09-01, author priority, cross-route uniqueness, actual limit fills, PnL or chronology inside a wick bar.

C39 final previous ledger A109 confirmed `32d1759424b2659cc7350a0c78e1b61b9b428f4542a499a20fa27ae816f6b84e` and [independent 109/109 CI 39832081581](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39832081581) SUCCESS across three Python versions.

**C40 final acceptance gate:** append A110 exactly ONCE after A109, freeze this report and all 6 C40 evidence SHA256, then new independent full **110/110** ledger+evidence verification. Until that check completes, C40 cycle remains [~] though preceding research replay tests passed.

## Next cycle C41 — DO NOT call source combinations trades

Only after A110 independently passes, integrate **4 BOS × 3 Reaction × 3 FTA = 36 correlated source-only routes** with all parent IDs, 1H known-as-of, source-prior-touch states and 3m pre-BOS reaction timing. Explicitly mark otherwise unknown academic parts. No order creation, PnL, stops, take-profits or claim of instructor reproduction. Future separately tested execution model must use closed bars, stop-first ambiguity, fees, slippage, funding and held-out data.
