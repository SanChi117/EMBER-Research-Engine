# Быстрый отсев открытых стратегий, предварительная регистрация 2026-10-31

Цель: не доказать доходность, а быстро отбраковать три *готовые* Freqtrade логики до полноценного переноса.

## Открытые исходные стратегии
- AdxSmas — freqtrade/freqtrade-strategies user_data/strategies/berlinguyinca/AdxSmas.py, blob 5bc99c1c1e32b8c1dc12c265176b511f44cbc242. LONG: ADX14>25 и SMA3 пересекает SMA6 вверх; выход ADX14<25 и SMA6 пересекает SMA3 вверх. 1h, ROI10%, SL25%.
- BbandRsi — freqtrade/freqtrade-strategies user_data/strategies/berlinguyinca/BbandRsi.py, blob addc87268affc2f3b1b00549f1ca8b119e41e655. LONG: RSI14<30 и close < BB lower typical price20/2std; выход RSI14>70; ROI10%, SL25%, 1h.
- FAdxSmaStrategy — freqtrade/freqtrade-strategies user_data/strategies/futures/FAdxSmaStrategy.py, blob 3bb13caf079e8360a959c3ad4dd2b2507f3045c0. LONG/SHORT ADX14>30 плюс SMA12/48 cross; exit when ADX14<30; SL5%, original ROI time-based {0:5%,30min:10%,60min:7.5%}. **Proxy uses fixed ROI5%, not exact original Freqtrade ROI.**

## Замороженная выборка и стоимость
- 6 Binance USD-M BTCUSDT/ETHUSDT/SOLUSDT original public API 1h records in data/{A,B}_{symbol}.json, 840 consecutive hours each; Git blob version source.
- A: [2025-02-01, 2025-03-08) UTC; B: [2026-07-01, 2026-08-05) UTC. No tuning on either.
- Decisions after closed 1h, fills at next open, stop first if stop and target both touched, signal exits at next bar open; mandatory end-window marked-to-market close.
- 120 warmup closed bars before first signal. Independent Wilder ADX14/RSI14 and population Bollinger typical price20. TA-Lib indicator parity and original Freqtrade full engine are NOT proven.
- 7/12.5/20 basis points adverse pricing **per side** (approximately 14/25/40bps two-side costs); risk presented as percent of 1x notional, **not account equity**. No actual bid/ask, maker fills, funding, liquidation, cross-symbol wallet or latency model. Therefore strictly FIRST SCREEN, not a valid production-quality Freqtrade backtest.
- Progress gate for *spending time on original Freqtrade reproduction*: >=30 trades aggregate, PF>1.2 at 25bps IN EACH of A,B, positive aggregate net at 40bps IN EACH A,B. Not a live authorization. No parameter changing after observing the results.
- All failed original strategies remain available for archival, but no immediate optimization to rescue results. Zero trades is NO_POWER, not evidence of zero profitability.
