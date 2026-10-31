> **⚠️ АРХИВНОЕ / НЕ ТЕКУЩЕЕ — `ARCHIVE_SNAPSHOT_SUPERSEDED`.** Прежние shortlist, исходный скрининг и попытки паритета могут использовать неправильный TF/пары/капитал. Показатели не равны подтверждённому авторскому futures account. Ошибочно трактованные или устаревшие выводы ассистента исправляются только через [единую актуальную сводку](RESEARCH_STATUS_CANONICAL.md). Исходный текст ниже сохранён для аудита; не считать экономический или PAPER PASS доказанным.

---

# Проверка методики: A228–A229 НЕ являются полной корректной репликацией оригиналов

Дата 2026-10-31. Без изменения LOCKED мандата. Проверка по фактическому runner коду `research/a228_five_original/a228_run_original_freqtrade_five.py`, пяти original source SHAs, Freqtrade 2026.9 docs и журналам A228/A229.

## Подтверждённые существенные недостатки

1. **Защитные механизмы выключены**: оригиналы DualTrend, TrendFollowing, BearRegime определяют `protections` (CooldownPeriod/StoplossGuard/MaxDrawdown). A228/A229 backtesting CLI не содержит обязательного `--enable-protections`; Freqtrade документирует, что без флага они НЕ применяются. Это не полный авторский риск-режим. Документ: https://www.freqtrade.io/en/stable/backtesting/
2. **Движение внутри старшей свечи не уточнялось 5m**: оригиналы на 15m, 1h, 4h запускались без `--timeframe-detail 5m`, несмотря на уже подготовленные настоящие 5m USD-M. Фактические STOP/ROI/custom_stoploss могут существенно отличаться. Документ: https://www.freqtrade.io/en/stable/backtesting/
3. **Оригинальный исходник DualTrend использует будущее**: в `wangc-joker/ft_userdata` SHA `6833cb9b4bc5bfb01c3f5829ff11cc02b0814fd9`, файл `user_data/strategies/DualTrendCompressionRestartShortV1Strategy.py`, строки 170–178 `_merge_btc_context` выполняют `pd.merge_asof` без сдвига 4H BTC свечи до 4H CLOSE. Строки 273–277 — полученные данные текущего незавершённого 4h BTC для ETH/SOL, строки 300–313 — фильтр используется прямо для входа. Свеча BTC 08–12 UTC, подписанная 08 UTC, переносится в 1h сигнал с 08 UTC вместо 12 UTC. Это **causal lookahead**, не вопрос комиссии. Freqtrade предупреждает о небезопасном прямом merge старшего TF. https://docs.freqtrade.io/en/stable/strategy-customization/
4. **BearRegime startup length** `startup_candle_count=250` на 1h, но `mom20d = pct_change(20*24)` использует 480 1h баров. Первые сигналы у границ теста могут быть потеряны/не прогреты; требует recursive warmup паритета.
5. **Нельзя сравнивать с Freqle 33-pair прямо**: наши три BTC/ETH/SOL, 3 open trades, wallet1000/stake100, тогда как внешний Freqle 33 пар/10 слотов/другие настройки. Результаты это *другой эксперимент*, не опровержение автора в его условиях.
6. **Costs/fills**: fee BASE=0.05%, STRESS=0.11% на сторону; повышенные fees НЕ моделируют реальные ордербук-проскальзывания, maker queue, intrabar margin liquidation. Для идентификации контрактов использован официальный Binance FUTURES TESTNET exchangeInfo из-за mainnet HTTP451 на CI; реальные OHLCV/mark/funding из USD-M mainnet архивов. Liquidation-tier parity, paid funding per trade, stop execution и lookahead-analysis/recursive-analysis должны быть отдельно проверены.
7. **2026 incomplete**: июнь 2026 official 8h mark missing 3 свечи, official 1h mark missing 24 свечи; результаты на 2026 Jan–May, НЕ полный 2026 и не полностью независимый prospective OOS. У Bear за Jan-May2026 только 4 трейда.

## Что верно

Пять оригинальных текстов авторов действительно SHA закреплены без изменений; реальные Binance USD-M 5m и 8h mark/funding ZIP с receipts загружены, Freqtrade действительно выполнил backtest native Freqtrade, рассчитал результаты 2024/2025/Jan-May2026 *для конкретной неверной/ограниченной настройки*.

## Статус

**REQUIRES_CORRECTED_PARITY_REPLAY / NOT VERIFIED**. Старые таблицы A228/A229 нельзя использовать как окончательный verdict. Исправление runner без изменения оригинала — ветка `research/a230-five-original-freqtrade-parity-protections-5m-20261031`, CI https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41236167218 . Сильная lookahead ошибка **в самом** DualTrend не будет исправлена включением protections/timeframe-detail; до её независимого устранения прежние положительные результаты DualTrend нельзя интерпретировать как genuine edge.

Нет реальных или PAPER ордеров. Никакой новой торговой системы.
