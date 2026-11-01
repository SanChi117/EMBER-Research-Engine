# R030 original VolatilitySystem — PRE-REGISTERED new FUTURES holdout

**Registered 2026-11-01 before reading any June–October 2026 VolatilitySystem outcomes.**
Only original source, no signal tuning or added stops.

- Candidate: R030 original **freqtrade/freqtrade-strategies @ f3340ce11f5bdf62f598522e64d1f5638eaa13f5**, source \`user_data/strategies/futures/VolatilitySystem.py\`, Git blob \`15ce2473f3f60bd33c4a67b0b8b228e379850f19\`.
- Source 1H, 3H resampled ATR and close momentum, original long/short and exits, 2× leverage, max 2 fills (initial 50% stake then DCA), source stoploss −100% **preserved**. No aftermarket stop invention.
- New holdout: **2026-06-01 UTC through 2026-10-31 UTC (exclusive 2026-11-01)**, unseen by original prior A245 tests (ending 2026-05-31). Source warmup **2026-05 full calendar month**. If missing data, fail closed. Do not change months based on outcome.
- Source markets: **ONLY BTCUSDT, ETHUSDT, SOLUSDT perpetual USDT-M**, published monthly original Binance Vision **5m OHLCV, 8h mark and funding**, archive ZIP SHA256 receipts. 2026-05–2026-10 inclusive. Any genuine 8h mark month with gaps can be reconstructed only from complete original **1h mark ZIP**, retaining receipts; otherwise BLOCKED.
- Native engine \`freqtrade==2026.9\`, original unmodified source hash, 1H source candles assembled from **complete 5m** bars, native 5m detail. Isolated margin, starting wallet USDT1000, controlled stake USDT100 and max 3 trades; this is the **same controlled screen configuration as A245**, NOT published author wallet. BASE fee 0.05% each side, STRESS fee 0.11% each side; fixed before seeing results. No hyperopt.
- Record complete original trade histories incl. entries/additional fills, maximum adverse prices and future path, mark/funding, account DD, fees, rejected signals, trade concentration, drawdown. Critically verify liquidation and margin assumptions rather than trusting profitable backtest. If official Binance tier/maintenance/funding/mark cannot be accurately reconstructed, status BLOCKED/PROVISIONAL; never VERIFIED.
- Acceptance: genuine independent 2026 new-period after-fee native results >0 across fixed scenarios and no unacceptable liquidation/fill/margin modeling uncertainties; if fails, preserve FAIL. The old 2024/25/Jan-May2026 windows were examined and are **not new OOS**.
- This runs only in research branch; no modification to original Pine/EMBER, any PAPER/live orders, running automations, or user accounts.

**Source insight:** original \`stoploss = -1\` means no protective price-based SL until liquidation/other exit, even though entry/exits can profit in backtest. Stop-loss safety veto remains irrespective of attractive ROI.
