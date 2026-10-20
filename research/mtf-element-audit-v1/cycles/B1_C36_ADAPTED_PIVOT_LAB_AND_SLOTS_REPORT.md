# B1/C36 — ADAPTED BOS Pivot Lab + Academic Core Slot Isolation

**Date:** 20 Oct 2026 · **Source:** frozen C33 2026 original Binance USD-M Futures 45 ZIP research parent receipt · **Mode:** PAPER ONLY / NOT_TRADE_READY. This experiment DOES NOT restore the author-selected 2023 BOS or deploy order execution. Only C36 code/evidence may change; old C20–C35 academic source and A001–A105 append-only SHA remain intact.

## Architecture and why it addresses the main blocker

Instead of repeatedly demanding inaccessible author Notion positive/negative 2023 goldens, C36 introduces a distinct **ADAPTED pivot research namespace**. Academic original constraints continue unchanged; substitute variants are explicitly `ADAPTED`, not fictional original author rules. Source-validated means source OHLC geometry, NOT academically original pivot choice.

`d05/c36_adapted_pivot_hypotheses.py` implements four reproducible and genuinely different source-known choices on the SAME previously frozen C33 research options:

| Hypothesis ID | Rule | Role |
|---|---|---|
| `LATEST_CONFIRMED_V1` | most recent confirmed strict 1+1 3m swing at C21 break bar START | Existing frozen C21 research baseline, **not author-golden** |
| `EARLIEST_CONFIRMED_V1` | earliest source-confirmed eligible 1+1 swing since 1H raid | Alternative — not a trade trigger |
| `DEEP_RAID_SIDE_V1` | on BSL→SHORT select the minimum eligible LOW beyond raid; on SSL→LONG select maximum HIGH | Alternative — not a target or author level |
| `NEAREST_RAID_SIDE_V1` | on BSL→SHORT maximum LOW still strictly below swept level; on SSL→LONG minimum HIGH still strictly above | Alternative — not a target or author level |

All variants explicitly require source SHA-linked original three 3m bars, candidate-list SHA, true prior 1H fractal raid direction, 3m swing right-hand candle known `<= research BOS bar START`, C33 frozen selected C21 baseline, Decimal finite prices and original3m closed bar SHA. Evaluation at other as-of time is rejected; no future 3m confirmation may be used. **No route says it has a confirmed BOS break at the alternative pivot.**

`d05/c36_adapted_slot_registry.py` adds a typed *research assembly*, not a working full strategy. Academic core (source-only verified fragments) is pinned by stable digest and C33 source blob. `RAID_1H` and `ENTRY` are not silently replaceable; `REACTION`, `FIRST_TROUBLE_AREA` and `STOP_TARGET` are **unresolved slots**, and untested adapted variants cannot be registered. Current `BOS_PIVOT` variant proposals are the only selectable adapted slot. Four assemblies are `NOT_TRADE_READY` and have **zero** trades/orders/PnL, both PAPER and REAL order placement disabled.

## Complete C33 sample comparison — not return/performance

Source `evidence/c36/C36_ORIGINAL_539_CASE_ADAPTED_PIVOT_COMPARISON.json`: **539 frozen C21-conditioned 1H-raid→3m BOS research contexts**, **5,285 source-preknown swing relations**, across BCH, BTC, ETH, SOL and XRP. Hypothesis agreement versus frozen C21 choice:

| Adapted hypothesis | Same selected swing as C21 | Different selected swing | What it does NOT prove |
|---|---:|---:|---|
| Latest confirmed baseline | **539 / 539** | 0 | This is **not** independent strategy accuracy; baseline replicates its selection |
| Earliest confirmed | **0 / 539** | 539 | Different selected pivot may not be a BOS at the frozen event |
| Deep raid-side extreme | **54 / 539** | 485 | Disagreement != greater returns |
| Nearest raid-side | **52 / 539** | 487 | Disagreement != safer stop or valid author BOS |

**Critical independent-sample falsification:** 539 research *raid contexts* map to only **390 distinct original 3m closed-break candle rows**. **149 additional 1H raid contexts reuse a previously observed original3m candle**. These research rows are correlated contexts, **not 539 independent executable trades**. Initial [first-gate CI 39479714861](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39479714861) failed due an overly strict one-bar-one-context uniqueness assumption; corrected source identity to include associated raid pivot + raid start + selected swing, and separately count 390 unique price bars. Original C33 frozen original JSON unchanged.

Chronological description-only partitions by C21 break-bar timestamp:
- `DEVELOPMENT`: **270** raid contexts
- `VALIDATION`: **131** raid contexts
- `HOLDOUT`: **138** raid contexts

**Not an untouched trading holdout.** Every split's selector agreement is now visible; no adapted hypothesis was tuned for profit, but these data MUST NOT be claimed as pristine future forward profit validation. Future true validation requires completely new untouched periods, purge/embargo around overlapping raids, source-matched 3m signal event replay, actual fill model, fees/slippage/funding and preferably real paper forward observations.

## Negative-first tests and no false claims

- 35 source-only pivot negatives: candidate right-hand future, wrong 1H raid direction, invalid Decimal, fake native SHA row IDs, tampered C33 original candidate-list SHA, duplicate same-side pivot center, missing C21 baseline, false author READY, spoofed source trade, unknown hypothesis. One originally skipped multi-baseline synthetic test was corrected to use an actual pinned multi-pivot case. **35/35 should run with zero skip.**
- 23 architecture negatives: frozen academic core hash and C33 source lock, disallowed modification of author raid/entry, forbidden FTA/SL/Reaction placeholders, disallowed unregistered variant and real trading, explicit `holdout not pristine` marker.
- Complete original 539-case comparison through `tests/probe_c36_adapted_pivot_comparison.py`; every original case and its four source selections preserved. `tests/probe_c36_adapted_slot_registry.py` freezes four typed assembly states without orders.

The first C36 source-only [CI 39480206950](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39480206950) **SUCCESS** after correcting distinct raid context keys, yielding first source-comparison Git blob `d086e00def1f84dafd32fc370ab249ec15956075`. Independent complete full-source JSON and **35 pivot + 23 registry tests on EACH Python 3.10, 3.11, 3.12** confirmed by [CI 39481487246](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39481487246) **SUCCESS, five jobs**. Full C36 first receipt frozen Git blob `d086e00def1f84dafd32fc370ab249ec15956075`; research slot manifest Git blob `a77454dd66d39855878519ba83b61df95cdc7c0f`; independent CI witness Git blob `36fbb68bb0f76f35065bd8ec5be69a2a4a87ec90`. A106 append-only journal and independent 106/106 SHA acceptance remain pending.

## Precise next practical implementation (C37), NOT solved by C36

A full adapted BOS *event* is not a static choice from cases that C21 already selected as BOS. C37 must rebuild the chronological event scanner **from independent original 3m/1H bars**, performing each hypothesis's choice **BEFORE each new bar begins**; then detect its *own* actual later wick-cross and closed-break events, without conditioning on C21's chosen break time. Verify each variant produces different event timestamps, unique original bars and invalidation semantics, without future leakage.

Only after this route is stable integrate local `Reaction`, then `FTA`, and `SL/TP` slots, with independent price-source geometry and no assumption of fill from 3m OHLC. Evaluate whole strategies against **new** untouched holdout periods and forward PAPER observations; no profitable strategy, author fidelity, Sharpe/ROI or win rate can be claimed at C36.

**Immutable baseline:** Original source C33 Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df`, A105 SHA tip `a2fe39896fea78c95d532e6ff2c0c710f9ee8aabd876f2112c7f390c290247a5`. Development remains **PAPER ONLY · NOT_TRADE_READY**.


## CI falsification and repair history — preserve all failed checks

- [CI 39479714861](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39479714861) FAIL — source scanner falsely asserted each C21 research parent must use a unique original 3m break candle. Actual source had 539 different 1H raid contexts but only 390 unique 3m bars. Fixed to keep both counts and an explicit correlation warning, not to drop contexts.
- [CI 39480803299](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39480803299) FAIL after all three Python 58-test matrices passed — manifest probe compared Python `asdict` tuple with JSON list as though same type. Fixed first equality to empty-collection nontruthiness, with no changes to event logic.
- [CI 39481307923](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39481307923) FAIL only in final freeze job after full source and 58×3 negatives PASS — wrote tuple-structured Python object and reread JSON-structured object without canonical reserialization. Fixed canonical JSON comparison in probe, with original source + slot registry unchanged.
- [CI 39481487246](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39481487246) all five jobs SUCCESS. No 32/32 skipped tests disguised as passing: now 35/35 pivot and 23/23 architecture checks each Python.

**Source scope:** frozen original C33 ZIP receipt reused — C36 did **not** re-download the 45 ZIP; it independently reevaluated frozen C33 complete JSON with pinned SHA. The old independent C33 45 ZIP replay remains earlier evidence, NOT a new C36 source reread. Author goldens 0, confirmed adapted trading triggers 0, orders 0, trades 0.
