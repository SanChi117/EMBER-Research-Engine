# Live Gate

EMBER 0.2.0 is intentionally research-only.

Live execution must not be added until all conditions below are true:

1. 100 or more completed paper trades.
2. 30 or more calendar days of paper observation.
3. Paper metrics are within +/-10% of backtest expectations.
4. Purged walk-forward validation is `PASS`.
5. No look-ahead test is failing.
6. Kill-switch behavior is verified independently.

A future Phase 4 may add a separate exchange adapter, partial-fill/slippage execution model, liquidation/funding model and a capital-limited rollout. None of those components exists in this project.
