# A228/A229: РЕАЛЬНАЯ НЕЗАВИСИМАЯ ПРОВЕРКА ПЯТИ ГОТОВЫХ ОРИГИНАЛОВ

Дата: 2026-10-31. В отличие от опубликованных на Freqle результатов 2022–2024, это **собственные нативные Freqtrade тесты пяти НЕИЗМЕНЁННЫХ готовых original** на SHA-проверенных Binance MAINNET USDT-M OHLCV, mark/funding BTC ETH SOL. Binance TESTNET использовался **только для справочника market metadata** из-за HTTP451 на GitHub CI. Исключён июнь 2026: отсутствуют 3 официальные 8h mark candles / 24 1h mark candles. Комиссии BASE 0.05%/side, STRESS 0.11%/side; STRESS — замена более дорогими fee, НЕ реалистичный orderbook slippage; 5x liquidation/margin tiers не аудированы, без forward. No live/PAPER orders.

### Главное: ни один не выдержал проверку устойчивого положительного STRESS PnL в 2024, 2025, Jan–May 2026

| Оригинал | 2024 STRESS | 2025 STRESS | Jan–May2026 STRESS | Статус |
|---|---:|---:|---:|---|
| DualTrendCompressionRestartShortV1Strategy | **−2.80%** (21) | +5.74% (49) | +6.05% (18) | отрицательный 2024 / мало сделок |
| TrendFollowing | — | **−71.41%** (1828) | — | экономический отказ и катастрофическая просадка |
| NASOSv7LongShort | — | **−5.85%** (57) | — | экономический отказ |
| BearRegimeShortV1 | +2.56% (12) | +3.27% (40) | **−0.72%** (4) | слабая/редкая выборка, 2026 отрицательный |
| Risk_Stair_S5 | +0.93% (76) | +19.14% (59) | **−11.01%** (26) | отрицательный 2026, 5x liquidation risk |

Числа в скобках — закрытые сделки. 2024/2026 для TrendFollowing и NASOS **не тестировали**, потому что их 2025 отрицателен в независимом stress test, а не «0%».

Полный отчет, версии исходников, проценты BASE, funding/fee assumptions, все CI URL, журнал и source receipts: [A228_A229_COMPLETE_FIVE_NATIVE_ORIGINALS_RU.md](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/a229-three-native-originals-cross-regime-20261031/research/a229_cross_regime/A228_A229_COMPLETE_FIVE_NATIVE_ORIGINALS_RU.md).

**Исследование доказало только отрицательный/недостаточный результат для ЗАДАННОГО Binance USD-M BTC ETH SOL рынка, периодов, размера капитала, исходных параметров и модели OHLCV исполнения.** Не выдавать пятёрку за VERIFIED, не переподбирать параметры на раскрытых годах. Не менять locked mandate, veto A220, действующие PAPER и реальные счета. 0 VERIFIED.
