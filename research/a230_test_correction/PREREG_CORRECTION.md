# A230 pre-registered test correction (2026-10-31)

A228/A229 tested five pinned original Freqtrade strategies with genuine Binance USD-M candles, marks and funding; however two execution assumptions were incomplete:

1. Source-defined protections of DualTrend, TrendFollowing and BearRegime were not enabled. Freqtrade requires explicit `--enable-protections` in backtesting. This can change trade selection and drawdown.
2. No `--timeframe-detail 5m` was supplied for original strategies with 15m, 1h and 4h main timeframes. Native 5m data already exists; detailed candle evaluation can change intrabar stops, ROI and callbacks. Original NASOS is itself 5m.

Freeze the same original classes, pinned source SHA and unchanged strategy parameters, original 3-market dataset, capital and fee scenarios. Change ONLY the backtesting CLI to enable protections and finer fill/exit resolution. Corrected independent tests: all five originals during 2025; 2024 and Jan-May 2026 for three prior positive 2025 families, with both fee scenarios. Do not infer profit from runs failing to execute. Keep A228/A229 results as legacy-config evidence, not decisive performance. Do not tune source logic or execute actual/paper orders.

Remaining limitations: testnet public metadata due to Binance mainnet HTTP451, 3 pairs rather than Freqle's 33, fixed $100 stake and $1000 starting wallet vs author's precise deployment, 5m OHLC fill not full orderbook, margin/liquidation unaudited, OOS not prospective, 2026 June mark missing genuine archive day. Still require lookahead and recursive analysis before any positive candidate receives verified status.
