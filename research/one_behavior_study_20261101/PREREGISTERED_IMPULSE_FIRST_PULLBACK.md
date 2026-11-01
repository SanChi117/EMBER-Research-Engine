# EMBER · PREREGISTERED BEHAVIOR-01 (2026-11-01)

**Статус:** hypothesis/protocol, NOT source-native complete trading strategy, NOT verified profitable, NOT orders.

## Question

Can one specific **impulse → first closed-bar pullback → continuation** price behavior recur across assets/timeframes/regimes, and can observable **pre-entry** evidence distinguish successful instances from lookalike failures? The idea is inspired by *source-read* P07/P06/P10 and directional P01/P04/P05; no claim of original six-way mechanism.

## Fixed event definition, frozen BEFORE outcomes

Use actual UTC *closed* Binance USDT-M Futures OHLCV. Each asset independently on 1h, 4h and 1d. No mandatory lower-TF confirmation.

1. **Impulse bar i**: close exceeds previous 20 full bars' highest high (long) or lowest low (short); impulse true range >= **1.50× ATR14 from bars ending at i−1**; directional candle body / full range >= **0.60**; close in directional outer 25% of range. No lookahead.
2. **First close-based pullback**: among the first 6 subsequently CLOSED bars, first bar j whose CLOSE reverses at least **0.35× the pre-impulse ATR14** from impulse close, and no more than **1.50× that ATR**, while still closing outside the previous-20 breakout boundary. Before such j: no fresh high beyond original impulse high (long) / low (short), and no close back inside the previous breakout range. Any failure becomes separately counted *impulse without qualifying first pullback*. Use wick excursion on qualifying pullback bar as preknown structural invalidation marker, NOT a validated SL.
3. **Event signal** at the close of j. **Observed entry reference** next full bar OPEN, not known at j signal time and not asserted executable. Do not exploit next open to choose events.
4. **Structural outcome** on the first 12 bars after j: initial impulse high/low retraced and exceeded in impulse direction **before** pullback bar opposite wick extreme is broken = continuation-first. Opposite wick extreme hit first = invalidation-first. Both in same bar = ambiguous. Neither within 12 bars = time-censored. Signal's own wick is NOT a post-signal failure.
5. **Independent economic diagnostics**: directional close-to-open returns over 3, 6, 12 subsequent bars; MFE/MAE to 12 bars in price or ATR units; hypothetical 0.10/0.20/0.40 percent roundtrip friction sensitivity. These are not actual orders or proof of expectancy after market-specific slippage/funding; no TP/SL/BE selected.

No feature-gated event suppression in this first trial. Any follow-up confirmation must be frozen on TRAIN-only and tested on untouched OOS, with rejected-event recall and costs disclosed.

## Ex-ante features for lookalike comparison (not optimized)

Prior 20-range width / ATR; prior volatility ATR% and past quote turnover; impulse body / ATR, volume multiple vs prior 20, prior 20-bar signed return / ATR, pullback retrace ATR, pullback penetration of broken boundary by wick, signal-side close clearance / ATR, elapsed bars to pullback, day-level regime as-of signal and BTC 1D context when available. NO outcome information as feature.

## Timeframe and comparator groups

**Liquid reference:** BTCUSDT / ETHUSDT / SOLUSDT. **Comparator-only exploratory alts:** STRKUSDT / ZKUSDT / LDOUSDT (do not claim all are objectively illiquid; categorize by *historical* median quote volume, launch age and spread data available). This group helps decide **future tradable universe**, not establish universal edge. Do not delete weak/failed assets after seeing results.

1h 1499 hours per symbol (Aug 30–Nov 1, 2026); 4h 3000 bars per symbol (Jun 19, 2025–Oct 31, 2026); 1d 999 days for liquid reference and variable available histories for alts (2024–2026). **Different time windows** -> never compare raw TF win rates as if samples came from the same distribution. Additional equal-calendar sensitivity and conditional calendar regime counts must accompany results.

## Falsification and quality

Event rarity and ambiguous within-bar path are valid negative results. Report all: impulse bars, qualifying first pullbacks, rejected pre-pullback impulses, both breakout directions, structural success/failure/ambiguous/censored, by asset and TF, not cherry-picked winners. Mark any missing realistic fees, funding, mark-price SL, crossing spread, delisted symbols, independent future OOS as **NOT VERIFIED**. No tuning thresholds in this cycle. Do not modify existing main, PAPER, or trading instructions.

**Next only after results:** decide whether behavioral family is viable; if yes, test pre-signal distinguishing features and out-of-sample across regimes before any real entry/SL/TP engineering.
