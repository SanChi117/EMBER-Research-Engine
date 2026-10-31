# A247 — prereg: четыре ДРУГИХ ранее мало проверенных исходника на 2024/2025/2026 USD-M

Мандат `main/RESEARCH_MANDATE_LOCKED.md`, issue #9, original source unchanged. No real orders, no PAPER scheduler edits. Эти R014/R015/R031/R032 **не** повторяют Double MA, Risk Stair, TrendFollowing, Winner15m или A245 6 исходников.

| R-id | Original pinned source | Git blob | Native timeframe | Critical condition |
|---|---|---|---|---|
| R014 momentum_wick | `TheoBrigitte/freqtrade@c9def379b1036064d592c3a0518a07811f5a9a76` `strategies/momentum/momentum_wick.py` | `1377a5bbf454252ca835cca3056787ac8ed73c04` | 5m | original stop=-10% price, true shorts & longs, no custom stop |
| R015 momentum_rsi | same repo `strategies/momentum/momentum_rsi.py` | `3f839276f661f242a30e4dd1aa0b739459e7d65b` | 5m | original `['enter_long', 'enter_tag']=(0,...)` DISABLES long! Keep source `SHORT-ONLY`; no silent repair |
| R031 FSupertrendStrategy | `freqtrade/freqtrade-strategies@f3340ce11f5bdf62f598522e64d1f5638eaa13f5` `user_data/strategies/futures/FSupertrendStrategy.py` | `e6ec4c039a7e7759570a4df5176294f7ff19a04f` | 1h | original long-only in futures (no can_short=True), source stop=-26.5%; risk not a net fail |
| R032 FOttStrategy | same repo `user_data/strategies/futures/FOttStrategy.py` | `3961d9b836be4ba0427bb39a23dfe03b70d81728` | 1h | import `from numpy.lib import math` may fail on newer NumPy: record source BLOCKED, do not silently replace the import |

Re-evaluate source economics in **additional history** not present in A201 limited 2026: fixed separate USD-M windows 2024, 2025, 2026 Jan–May, genuine archived Binance BTC/ETH/SOL futures 5m resampled to original timeframe, mark/funding; true SHA receipts, Freqtrade2026.9, userdir isolated, per-window reset $1000 wallet with $100 stake, max3, BASE 0.0005 and STRESS 0.0011 fee each side. For 1h sources --timeframe-detail 5m; 5m original no detail (no smaller verified candles). 4×3×2=24 native executions, two parallel batches. No optimization, no forced protections. This is a **controlled 3-pair screen**, not author exact account; portfolio parity and maintenance-margin/mark-fills/slippage unverified. If source cannot execute unchanged, BLOCKED, not negative PnL or silent code repair. Results from already-seen periods not untouched OOS.
