# EMBER B1/C37 — Native 3m Forward-in-Time Adapted BOS Routes

**Date:** 2026-10-20. **Scope:** full bar-by-bar historical causally-ordered original 3m scan following 1H wick raids for FOUR ADAPTED-only hypotheses. **Never an instructor-certified 2023 BOS, executable entry, paper/real order, profit/backtest or win rate.** PAPER ONLY · NOT_TRADE_READY.

## Why C37 is substantially different from C36

C36 compared which *level* four selectors would have chosen at a candle already selected as BOS by frozen C21. Other pivots at that candle may not have broken at all. C37 now scans **every successive original native 3m bar** after full 1h wick raid confirmation and independently tracks each variant's **first genuine price CLOSE beyond its currently selected, prior-confirmed swing**. Pivot selection strictly precedes the bar open; the closed-break event becomes known at bar close, not retroactively at its start. A new swing may change the candidate level only after the right-hand 3m pivot confirmation bar has closed. The per-raid scan stops if the original 3m OHLC high/low exceeds the raided 1h wick extreme, conservatively refusing to assume favorable within-bar trade ordering.

Source code: `d05/c37_native_adapted_bos_event_scanner.py`; controls: `d05/test_c37_native_adapted_bos_event_scanner.py` (**27 distinct negative and causal tests**), complete original ZIP source: `tests/probe_c37_original_adapted_45zip_event_scan.py`.

Original academic core, C21/C33 original 45 SHA ZIP source receipts, C36 adaptation selectors and append-only historical journal are unmodified.

## First full original 45 ZIP research result, independently verified

Original Binance USD-M Futures symbols: BCH, BTC, ETH, SOL, XRP. Native 3m: **76,800 source-closed bars**, independently original 15m Decimal parity **15,360**, 45 SHA-checksummed USD-M ZIP (3m/15m/1d). 1 September – 2 October 2026 UTC. No original teacher 2023 market-basis relation; author 1H/3m annotated examples remain inaccessible.

| Independent ADAPTED selector | 1H raid research contexts with a first 3m closed-break | Distinct original3m break bars | Additional reused-bar contexts |
|---|---:|---:|---:|
| LATEST_CONFIRMED_V1 (C21 research baseline) | **539** | **390** | **149** |
| EARLIEST_CONFIRMED_V1 | **462** | **326** | **136** |
| DEEP_RAID_SIDE_V1 | **412** | **298** | **114** |
| NEAREST_RAID_SIDE_V1 | **511** | **371** | **140** |

The LATEST variant **exactly reproduces** all source-native C21 539 research parent events, including original candle/timestamp, raid parent and swing center/level. That is a regression to an **existing research proxy**, not independent correctness of an author entry.

Events per original instrument:

| Market | LATEST | EARLIEST | DEEP | NEAREST |
|---|---:|---:|---:|---:|
| BCHUSDT | 99 | 91 | 80 | 94 |
| BTCUSDT | 104 | 83 | 74 | 93 |
| ETHUSDT | 129 | 109 | 98 | 126 |
| SOLUSDT | 103 | 88 | 76 | 100 |
| XRPUSDT | 104 | 91 | 84 | 98 |

**The variants produce genuinely different event times**, not only a different price level at the frozen C21 bar. Cross-variant comparisons on the same source raid:

| Against LATEST | EARLIEST | DEEP | NEAREST |
|---|---:|---:|---:|
| Both routes yield an event for same raid | 446 | 410 | 492 |
| Only adapted variant has an event | 16 | 2 | 19 |
| Only original LATEST has an event | 93 | 129 | 47 |
| On exactly same original 3m bar | 72 | 135 | 174 |
| Adapted event closes EARLIER | 86 | 10 | 114 |
| Adapted event closes LATER | 288 | 265 | 204 |

Every common-raid case is assigned once to earlier/same/later; correlation of events through shared 3m bars makes these **NOT independent trades**.

Chronological partitions are descriptive structural audits, not a pristine holdout for returns. Source-specific 3m market execution/spread/slippage/funding unavailable in these archives; even a closed price BOS is **not** a realized fill. No optimizer fitting, profit or win-rate conclusions.

## Falsification / tests

- Unit tests: **27** negative controls. Frozen original C21 latest regression; raid known only after full following 1h bar; same-bar break invalidated by new raid wick extreme; different as-of and physical prefix equality; closed 3m bar known_ms vs event start; strict confirmed 3m swing right-bar; no future or fake native3m SHA; body breach of raided liquidity not classified clean wick; no author `READY`/signal/order/trade; four alternative swing ranking outcomes.
- [First 27/27 source test CI 39491091920](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39491091920) SUCCESS.
- [First complete original 45 ZIP 4-route CI 39491400022](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39491400022) reported source reconstruction SUCCESS and committed first original `C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json` Git blob `e4b702e8c6cdc34f1c2475df73ef44ae1631fe56`.
- [Independent C37 CI 39492075525](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39492075525) **SUCCESS all five jobs**: full original 45 ZIP reread and complete per-event JSON equality across 539/462/412/511 research event routes, original 76,800 native3m bars and 15,360 native15m Decimal parity, plus **27 negative controls each** on Python 3.10/3.11/3.12. Immutable independent witness `evidence/c37/C37_INDEPENDENT_SOURCE_WITNESS.json` Git blob `d11147727df89e598b69ae7c80a5e01b6dbc7bb3`. The first independent [CI 39491774466](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39491774466) **FAILED** after source reread and 3×27 tests PASS because immutable JSON contains empty arrays while intermediate Python dataclass `asdict` contains empty tuples; canonical JSON serialize-then-parse comparison repaired without changing original source scan or frozen data, commit `77cd44c8`. Original failed run remains in audit trail. Source C37 narrow research evidence acceptance awaits canonical append A107 and independently verified 107/107 SHA.

## Integration is NOT yet complete

C37 now provides four independently-found *research* BOS closed-break timelines and original3m bar IDs. It still lacks a verified local `REACTION` after 1H raid, a prioritized `FIRST_TROUBLE_AREA` compatible with price sequence, independent `STOP_TARGET`, actual `ENTRY` execution or fill, fees, funding, risk and valid out-of-sample forward results. Those modules remain **DISABLED** in C36 six-slot assembly. No autonomous order code and no live API keys.

**Next C38:** independent source-native Reaction concept trial with academically documented source vs separately labeled ADAPTED criteria (e.g. range displacement, rejection wick, confirmed local swing; freeze definitions before testing). No fitting to return metrics and no crypto order execution. Integrate only when each element and causal order passes source and adverse tests. Avoid presenting hypothetical replacement as original instructor method.

Frozen immutable: A106 SHA tip (see central journal), C33 source original Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df`, C36 original comparison `d086e00def1f84dafd32fc370ab249ec15956075`. C37 author BOS certified 0; orders 0; trades 0.
