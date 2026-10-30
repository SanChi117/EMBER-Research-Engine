# Что проверять после 0/2 отрицательных ценовых тестов (2026-10-31)

**Это shortlist исходного кода и опубликованных результатов; это НЕ наша проверенная прибыльность.** Уход от перебора параметров у проигравших версий обязателен.

## Приоритет 1 — публичный Freqtrade с заранее закончившимся отчётным периодом

[MirrorNew/2026DoubleMaFuturesStrategy](https://github.com/MirrorNew/2026DoubleMaFuturesStrategy). GitHub repository created **2026-05-11**, last source push **2026-05-12** (по GitHub API на момент проверки). Исходный класс `user_data/strategies/VideoDoubleMaFuturesStrategy.py`, SHA Git blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`. Авторский файл большой (~60 KB), много параметров, 1h entry, 4h context, dynamic structural custom stop, Freqtrade 2× exposure.

**Авторские (не наши) результаты:** 2021-05-11–2025-01-01 215 сделок PF1.345 +100.84%, 2025-01-01–2026-05-11 76 сделок PF1.591 +53.04%, полный 291 сделка PF1.404 +154.24%. Это backtests из [авторского отчёта](https://github.com/MirrorNew/2026DoubleMaFuturesStrategy/blob/main/reports/futures_backtests/ETH_2X_FALSE_BREAKOUT_REFINEMENT.md); нет независимой проверки, что корректно учитываются funding, quotes, частичные fills, lookahead и prepublication optimization. Автор сам пишет, что не на 100% уверен в ready/live.

**Лучший независимый тест:** source SHA frozen на 12.05.2026, **последующий период [2026-05-12, 2026-10-30) UTC**, которого не было в опубликованных результатах. Native Freqtrade 2026.x, exact class/config, Binance USDM original ETH 1h/4h/mark/funding, ≥4h multi-week warmup BEFORE May12, no unearned future 4h bar, realistic cost & funding. Verification must include in-memory safe isolated engine, no secrets or real orders. **NOT YET RUN**. Не подменять этот кандидат «похожей стратегией» или собственным индикатором.

## Приоритет 2 — live PAPER с документированными отрицательными результатами

[darkvolg/Trading](https://github.com/darkvolg/Trading), public TrendRider 1h, live PAPER since Apr1 2026. Changelog 28.09.2026: v2.16 935 trades **PF0.92**, v2.17 628 trades **PF1.05** in publication's 2025-2026 combined tests; 2025 remains negative, 2026 positive. Авторская история исправлений включает тяжёлый bug: live в течение 2 месяцев использовал неверно разрешённую копию класса, обходя bear gate. **Не приоритетный кандидат для платной/реальной интеграции**, но полезен для regression тестов идентификации стратегии, version/provenance и честных PAPER журналов.

## Приоритет 3 — условные только после exact original engine проверки
- [freqtrade/Freqtrade-strategies Supertrend](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/Supertrend.py), 1h с тремя индикаторами, но сам исходный файл сообщает, что индикатор не валидирован по первоначальной научной публикации. Не считать валидным source alpha до TA-Lib parity и независимой истории.
- [HolyFot/VulcanTrader DonchianBreakout](https://github.com/HolyFot/VulcanTrader/blob/main/user_data/strategies/DonchianBreakout.py), 15m source, требует особого Rust bridge, ATR stop/trailing и 15m свечей. Нельзя тестировать по одним 1h вместо исходного 15m, писать на Python имитацию Rust без parity.
- [possm/freqtrader WolfBreakout_donchian](https://github.com/possm/freqtrader/blob/main/user_data/strategies/WolfBreakout_donchian.py), 15m LONG, BTC/EUR (!) на 1h как regime gate, кастомный ATR trailing, 7-day time exit; наш BTC/USDT не тождественен BTC/EUR, данные требуют отдельной валидации. Нельзя заявлять native equivalence в 1h proxy.
- Более простые готовые `VolatilitySystem` и `FOttStrategy` из freqtrade-strategies на 1h содержат динамическое увеличение позиции/нестандартный resample и циклы накопления внутри индикатора; слишком высок риск неточного суррогата. Приоритет после native.

**Рекомендация:** не перебирать ещё десятки 1h параметров на тех же A/B данных. Следующее экономическое исследование отдать native `VideoDoubleMaFuturesStrategy` на настоящей пост-публикационной истории с cross-check исходных и funding данных. При отрицательном результате закрыть быстро, при положительном в нескольких невиденных фазах — только PAPER и дальнейшая независимая проверка.
