# BEHAVIOR02 BACKWARD HISTORICAL CONFIRMATION · locked before old-H4 acquisition

**Date:** 2026-11-01. **Classification:** HISTORICAL BACKWARD HOLDOUT, NOT FORWARD OOS. Older 4h futures candles spanning **2024-02-06 to 2025-06-19** were not used in prior 2025-2026 Behavior02 impulse result. BTC ETH SOL are the core; STRK ZK LDO comparator histories begin at listings. Never treat exchange-delisted missing instruments as absent negative signals.

## No redefinition of event

Use frozen [BEHAVIOR02 rule](./PREREGISTERED_DIRECT_IMPULSE_CONTINUATION_02.md): strong 20-bar breakout, >=1.5x previous ATR14 range, directional body>=60% range, close in outer 25%. Enter reference next bar OPEN, observe whether +0.5 ATR beyond impulse extreme occurs before 50% impulse body retracement over six CLOSED H4 bars; both inside same candle are UNKNOWN. Six-H4-bar signed return net of a hypothetical 0.2% roundtrip cost is a secondary descriptive check. No TP/SL orders or optimized exits.

## Single ex-ante discrimination hypothesis

The candidate **impulse directional body >=2.0 of PRE-impulse H4 ATR14** appeared promising in *later 2026* but less so in earlier 2025-2026 cohorts. That finding is data-mined/post-selected, so **never claim it validated from existing 2025-2026 data**. **Do not alter the 2.0 ATR threshold** on the backward holdout. Compare two categories across BOTH main and comparator universes:

- structural continuation-first ratio among resolvable events;
- mean signed next-open→six-H4-close return under 0.2% hypothetical roundtrip cost;
- event frequency and unconditional cost sensitivity (selection must not annihilate sample size);
- if a core/comparator/time period disagrees, report it, no rescue filters;
- D1 trend, volume >=2x and clearance>=0.5ATR as **secondary diagnostics, not selection rules**.

Backtest on older H4 segment must not borrow future D1 history for event classification: D1 prior closed bars only. Separate read of older 4H H/L/O/C must be source-frozen with file SHA. Avoid using current instrument ranking to pick a winning pool. Neither backward holdout nor post-selected feature is a genuine future forward test.

**Failure rule:** inconsistent directional/cost advantage on the independent older H4 cohort => no evidence this feature separates real and false impulse continuation across cycles. Do not tune. Continue open-source discovery of *another distinct source-family behavior*, not yet another MTF indicator funnel.
