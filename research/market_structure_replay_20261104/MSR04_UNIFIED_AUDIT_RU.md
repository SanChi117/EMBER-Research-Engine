# MSR-04 — frozen accumulation anchor versus later BOS pivot

**Status: RESEARCH_ONLY / CAUSAL_AUDIT / NO_EXPERT_TRUTH / NO_TRADES.**
Date: 2026-11-04. Builds on MSR-01, MSR-02 and MSR-03 without modifying
their original signals or the SMOKE/PAPER automations.

## Input and evidence
- Fixed original cohort: 19 Binance USD-M pairs × 1500 15m bars = 28500.
- Original MSR-01 event log: 10990 events, 1072 accumulation locks,
  639 sweep returns, 374 post-sweep FVG, 234 machine-labelled BOS.
- MSR-01 event artifact: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41857673432/artifacts/13337344184.
- Source event log SHA-256 validated locally:
  `8fcaa7e22cf591c8bef31f99e1017535260311f3333afe90a0fdbaf7e6ad349e`.
- Original Binance Vision ZIP and published CHECKSUM **not independently verified**.
- Current GitHub workflow regenerates the event stream from the pinned source
  CSV fixtures; it does not require access to future prices or live market data.

## Measured mismatches

| Issue | Result |
|---|---:|
| Total original BOS event records | 234 |
| Unique symbol+time+direction | 210 |
| Pivot at sweep is not pivot available at accumulation lock | **206/234 (88.0%)** |
| Pivot **price** at sweep differs from price available at lock | **203/234 (86.8%)** |
| Original pivot was internal to locked accumulation range | 212/234 |
| Used pivot confirmed on the sweep candle | 29/234 |
| Last confirmed 1H swing passed at BOS (MSR-02 proxy) | 65/234 |
| Last confirmed 4H swing passed at BOS (MSR-02 proxy) | 11/234 |
| Blind cases with fewer than 20 visible closed 4H candles | 41/180 |

In the independent event-log audit, the median **absolute** change in reference
price was 0.768 ATR(1H); 154/234 exceeded 0.5 ATR(1H), and 91/234
exceeded 1 ATR(1H).

Example: AAVEUSDT box locked at 2026-08-01T15:00Z used a 91.78
existing high pivot, whereas the later sweep-time high reference was 90.50.
Do **not** infer that the frozen 91.78 level was or was not passed on BOS:
the events.jsonl source does not contain the BOS candle close.

## What the current code FIXES

- Adds a **read-only** historical ledger of both time-stamped references:
  the pivot already known at accumulation lock, and the pivot used at sweep.
- Rejects orphan/chronologically invalid event sequences and mismatched
  sweep/BOS references instead of silently accepting corrupted data.
- Preserves absent anchor as MISSING/UNKNOWN, not an invented negative.
- Reports reselected anchor and actual **price** change separately;
  identical price with a new pivot timestamp still counts as reselection.
- Publishes event and data receipts, duplication counters, independent tests.
- Leaves original MSR-01 recognition unchanged, so previous failures
  are not erased by after-the-fact parameter adjustment.

## Tests and limits

- Local event-log audit code and its own regression set: 11/11 PASS.
- GitHub branch includes `anchor_lock_audit_v04.py`,
  `test_anchor_lock_v04.py` and workflow
  `.github/workflows/msr04_anchor_lock.yml`.
- The workflow asserts original 19/28500/234/210/206/203/212/29 counts
  and exports full `anchor_ledger.csv` for independent inspection.
- **CI status is not asserted until the workflow completes.**
- No independent reviewer labels exist for 180 blind chart cases.
- A local pivot crossing is not identical to verified 1H/4H structure.
- The original trading signal is deliberately **not** replaced yet.
- No tick-level order simulation, fees, funding, profitable edge or real
  orders follow from this audit.

## Still required — and why

1. **Restore BOS closes** from the identical pinned 15m CSV and test whether
   they really crossed the reference frozen **at lock**. Event-only logs
   cannot answer that question. Separately compare 1H/4H pivots frozen at
   lock and sweep.
2. **Blind human review** of candidate and control charts (ideally two
   independent reviewers) before the machine flags are revealed. 41 of 180
   windows need longer past-only 4H context. Only then compute matching
   precision/recall with stratification.
3. **Correct the core event taxonomy** after labels: LOCAL_BOS_15M,
   BOS_1H, BOS_4H, UNKNOWN; do not retroactively rename original outcomes.
4. **Check overlapping episodes** beyond exact same-time duplicate signals.
5. **Reproduce original AMD/FVG/CRT implementations** without substituting
   convenient ATR proxies; freeze source SHA and use independent OOS windows.
6. **Validate original data and execution** using official Vision checksums,
   actual funding, 1m/tick stop/TP ordering and agreed 50% TP1/50% remainder.
   Only after semantic validation should a trading backtest be considered.

**Decision:** meaningful failure of structural-reference parity has been
identified. Accuracy of market reading and positive economic edge are **not**
established. Neither SMOKE, real orders, nor PAPER/Automations were changed.
