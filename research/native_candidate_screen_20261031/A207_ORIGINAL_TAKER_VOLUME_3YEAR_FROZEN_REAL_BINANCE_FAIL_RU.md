# A207 — реальная проверка taker buy/sell pressure 5m: FAIL 0/4 во всех 2024–2026 годах

Дата 2026-10-31. GitHub Actions прошёл техническую проверку реальных источников. Это **не** native Freqtrade, а независимый фиксированный replay точных оригинальных source signals. Prereg источник: `A207_TAKER_PRESSURE_5M_FROZEN_SOURCE_PREREG_RU.md`, записан ДО PnL. Реальный файл: `A207_GENUINE_2024_2025_2026_FIXED_ORIGINAL_TAKER_VERIFIED.json`.

## Исходник и данные
- `Gotodataru/binance-futures-backtest@5ed0d6e39d8a3e951bea40c66e2638c213012e1b`, исходный `strategy_2_taker_momentum/signals.py` blob `b8a2840618c4fb02a2d90120deed5771b34bdbd6`.
- Оригинальный taker-buy/base-volume / total-volume, EMA не является заменой этой информации. Original `generate_signals` вызывается byte-unchanged: lookback15, confirmation3, high0.62/low0.38, ATR14 with 0.8×MA50 threshold.
- Независимый исполнитель: следующий open 5m, hard SL1% цены, TP2% цены, max hold16 bars/80min, candle SL-first, no DCA, 1x, isolated model, $100 nominal and four independent $1000 wallets. Fees BASE0.05%/side + 0.01% slippage/side; STRESS0.125%/side +0.03% slippage/side; financing actual signed settled Binance monthly funding events.
- 2024,2025,2026 May13–Sep30 on BTC/ETH/SOL/LINK; 120 genuine Binance ZIP+CSV SHA receipts, 24 original-source-signal replay trade ledgers with individual SHA256, causal prefix invariance. No fabricated historical candles or performance metrics.
- 2024 was new to EMBER before prereg; 2025 and 2026 previously used for other strategies; not true forward out-of-sample. Additional unknown orderbook/fees models.

## Outcome (wallet returns vs $1000 per individual symbol; base cost model)

| Year | BTC N/net%/PF | ETH N/net%/PF | SOL N/net%/PF | LINK N/net%/PF | Trades total |
|---|---|---|---|---|---:|
| 2024 | 8 / -0.102520% / 0.4531 | 5 / -0.039313% / 0.6143 | 2 / -0.057951% / 0.0 | 9 / -0.143246% / 0.3946 | **24** |
| 2025 | 38 / -0.733337% / 0.1300 | 2 / -0.057261% / 0.0 | 7 / -0.188054% / 0.3558 | 6 / -0.111736% / 0.4818 | **53** |
| 2026 | 24 / -0.332560% / 0.2574 | 5 / -0.146033% / 0.0 | 23 / -0.246947% / 0.5225 | 49 / -0.720298% / 0.5776 | **101** |

**Все 12 BASE year×coin результатов отрицательны, все STRESS ещё хуже.** При более дорогих исполнениях каждый исходный set N сохранился (независимая fixed bracket модель).

## Почему
- Всего 178 исходных завершённых сделок (сумма across 12 отдельных model wallets across 3 years). Из них исходы: **166 timeout 80m, 10 SL, всего 2 TP**. 2024: 24 timeout/24, TP0; 2025:50 timeout+3 SL, TP0; 2026:92 timeout+7 SL+2 TP. Отсутствует достаточно быстрый **направленный price displacement** после входного taker-buy перевеса.
- 2024 raw pressure signal bars всего52 (28 onset), 2025 109 (60 onset), 2026 226 (121 onset). Пользовательский темп 3–5 independent closed setups/day недостижим: 24/141=0.17/day, 53/141=0.38/day, 101/141=0.72/day.
- Входы нерегулярны, но не насыщают 4 рынка и не имеют постоянного instant re-entry. Исторический edge отсутствует даже до усиления расходов (negative after BASE).
- Финансирование в 2024 +0.018965USDT, 2025 -0.016046USDT, 2026 -0.004774USDT на 4 счета суммарно — **не причина** убытков. Сумма BASE fees по 4 моделям: 2024 $2.400921, 2025 $5.299426, 2026 $10.100639, плюс slippage, издержки имеют значение. Прогноз без расходов не тестировался и не объявляется.
- Current bar ATR in signals uses known after bar-close OHLC at signal timestamp, but execution is on **next** bar open: temporal ordering correct. 2024 signal prefix test passes. Точная latency, maker fill, order book не имитируются.

## Вывод
**A207 — ECONOMIC FAIL 0/4 and TEMPO FAIL**, strategy rejected intact; no modifications of parameters on the 2024–26 data allowed. Достоинство эксперимента — настоящий buy/sell aggressor flow, архивные SHA и три года. Сам по себе taker ratio нельзя использовать как готовый A+ entry trigger.

Сохранить source replay как отдельный независимый плагин для будущей стратегии, но **не выдавать это за готовую положительную систему**. Планировщики и торговые позиции пользователя не менялись.
