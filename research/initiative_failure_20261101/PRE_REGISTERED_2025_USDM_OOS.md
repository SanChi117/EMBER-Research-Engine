# PRE-REGISTERED OOS: 2025 Binance USD-M reassertion check

**FROZEN BEFORE DOWNLOADING OUTCOMES** · 2026-11-01 · exploratory out-of-sample diagnostic, NOT trade authorization.

## Fixed question / sample

Re-run exact V3 contact registry, V3 transfer replay, nonoverlap selection and frozen 3-hour old-side reassertion diagnostic on earlier 2025 Binance USD-M futures prices. No new trading strategy and no parameter optimization.

**12 predetermined instruments, no profitability-based substitutions:** BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, LINKUSDT, AVAXUSDT, ADAUSDT, OPUSDT, ARBUSDT, LDOUSDT, NEARUSDT. If one is unavailable, report DATA_BLOCKED rather than silently replacing it. These were not independently selected as representative or historically liquid: explicit limitations apply.

**Source and dates:**
- Binance Vision official public historical USD-M monthly klines ZIP + published companion SHA256 CHECKSUM.
- 4H: 2025-01 through 2025-08 inclusive to supply structure history.
- 1H: 2025-06 through 2025-08 inclusive to supply 1H attempt/entry/outcome history.
- Strict UTC millis, closed bars, taker-buy base volume, no SPOT or synthetic candles. Validate daily/monthly contiguity and 1H→4H OHLCV parity; reject anomalies and missing contract history.
- Archive each original ZIP SHA256, published checksum, converted raw CSV SHA and Git revision.

## Frozen old original vs same-clock diagnosis

1. Original unchanged V3 PRICE_ONLY and TAKER_CONFIRMED recognition and execution. 4H structural stop +0.15 ATR4 buffer, nearest opposite 4H structural target, RR>=1.25, next 1H open entry, 24h stop-first, cost proxy 0.35% notional.
2. Original V3 trades de-overlapped per symbol using existing deterministic code.
3. EXACT 3 full closed 1H bars after original transfer. Reassertion attempts to regain original known contact_close. OLD_SIDE_REASSERTION_FAILED means attempt low/high challenged reference, candle closed on new-control side and all following observation closes held that side. SAME delayed open time and SAME precheck exclusion rules for all groups.
4. Retain all cases stopped or already targeted before delayed decision; report RR-invalid cases. Compare failed reassertion to NO_REASSERTION at SAME delayed entry clock, by-group N/mean/stop share/day-bootstrap, and prior earlier 2026 diagnostics.
5. Do not alter threshold, source selection, times, symbols, stop, target, fill order or fee after observing output. A positive isolated cohort is a hypothesis, not a verified edge; negative is accepted.
6. Output error/blocker honestly if sources fail, or LOW_POWER if few cases. No Mark, funding, liquidation, real fills, or financially shared-portfolio evidence.

This 2025 window was not previously tested by the 2026 V3 initiative pipeline but may have been examined by other EMBER candidates. Twelve predeclared symbols are an incomplete futures universe (delisting survivorship). This is a useful **new period check only**, not proof of a stable cross-cycle trading advantage.

The original existing-user LOCKED strategy-search mandate and USER_PAUSED ready-made-source track are not changed. PAPER and exchange accounts untouched.
