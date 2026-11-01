# BEHAVIOR-02 · Hypothesis preregistration · Direct impulse continuation · 2026-11-01

**Flag:** SECONDARY_EXPLORATORY / POST_BEHAVIOR01_SELECTION. This hypothesis arose after seeing failure counts of behavior01 on the very same data. It is therefore exploratory and **cannot** be called independent out-of-sample, even if rules are frozen before THIS calculation. No profitable claim.

**Question:** after an unusually large confirmed 20-bar price breakout, is the *initial continuation before deep 50%-body retrace* common and exploitable, unlike the delayed first-close pullback studied in Behavior01?

## Fixed objective rule (do not tune this test)

1. Use the **same** source impulse definition as Behavior01: prior 20 full bars breakout in close direction, bar true-range at least 1.5× ATR14 computed on preceding bars, directional body at least 60% of range, close within outer 25% of impulse bar. Binance USD-M closed 1h/4h/1d, six fixed symbols. **All** 894 recognized impulse seeds included, not just those whose future favorable continuation is known.
2. **Signal** at close of impulse bar; **diagnostic entry reference** next bar open, never used to identify signal.
3. **Continuation** = future wick extends **strictly beyond** impulse's high (LONG) / low (SHORT) by 0.5× the preregistered prior ATR14, within next SIX bars. **Failure** = wick reaches or crosses 50% of impulse candle body from close towards open **before** extension is achieved. If both in one candle, ambiguous. If neither, censored at six bars; RIGHT_CENSORED if too few full subsequent bars.
4. Record 3/6/12-bar gross signed next-open→later close outcomes, hypothetical 0.1/0.2/0.4% roundtrip friction; 12-bar MFE/MAE in ATR. Midpoint is a descriptive retracement marker, **not an actionable validated stop**.
5. Prior 1D as-of EMA20/EMA50 regime, relative impulse-volume, ATR%, impulse close over its previous channel and quote volume = pre-entry descriptors, **not gates**. Report failures and ambiguous outcomes.
6. BTC/ETH/SOL primary; STRK/ZK/LDO comparator-only. Same-period TF comparison separately because historic windows differ (H1 ~62d, H4 ~500d, D1 ~867–999d). Both bull/bear/transitional regime grouping. No claims that any market-cycle claim is proven without future/OOS full-regime tests.

**Anti-overfit:** Any positive descriptive average on this reused history is exploratory only. No filter tuning, switching TF after seeing profit, or selecting only nice coins. Real execution costs, live spread, slippage, funding, positions and actual stop/TP/BE remain **UNKNOWN**. Retain all failed observations and do not change original source strategies.
