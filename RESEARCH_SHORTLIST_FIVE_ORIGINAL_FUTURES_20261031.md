> **⚠️ АРХИВНОЕ / НЕ ТЕКУЩЕЕ — `ARCHIVE_SNAPSHOT_SUPERSEDED`.** Прежние shortlist, исходный скрининг и попытки паритета могут использовать неправильный TF/пары/капитал. Показатели не равны подтверждённому авторскому futures account. Ошибочно трактованные или устаревшие выводы ассистента исправляются только через [единую актуальную сводку](RESEARCH_STATUS_CANONICAL.md). Исходный текст ниже сохранён для аудита; не считать экономический или PAPER PASS доказанным.

---

# ПЯТЬ ОРИГИНАЛЬНЫХ КАНДИДАТОВ — предварительный список (31 октября 2026)

**Назначение:** только подбор пяти реальных источников по прямому поручению пользователя. **НЕ анализ прибыльности EMBER, НЕ одобрение к торговле, НЕ создание новой стратегии**, никакой ретюнинг. Зафиксирован главный мандат `RESEARCH_MANDATE_LOCKED.md` и `RESEARCH_USER_VETO_A220.md`; пользователь отклонённые три A220 источника здесь отсутствуют.

**Метод отбора**: широкий публичный поиск Exa/Web по GitHub, Freqle, FMZ, TradingView, открытым исследованиям и backtest-платформам. Сильнее всего сопоставимые готовые исходники с *внешним* общим стандартом Freqle: 33 пары, Binance-style Freqtrade futures sandbox, fee **0.05% за сторону**, 10 одновременных слотов, $1000 кошелёк, 2022-01…2024-12. Это НЕ самостоятельное подтверждение реального Binance USDT-M исполнения и не реальное mark/funding/liquidation/forward. Все результаты ниже — **опубликованные Freqle результаты**, НЕ наши результаты EMBER. Неправдоподобный Spot, DCA без лимита, явные leak-сигналы и фальшивые рекорды отброшены.

## Ровно пять — четыре новые плюс один ранее выбранный

| № | Оригинальная готовая стратегия / семейство | Зафиксированный файл оригинала GitHub | Отчёт внешнего backtest Freqle | Freqle net total 2022-24 | MaxDD | Trades | PF | Три года положительные? |
|---|---|---|---|---:|---:|---:|---:|---|
| 1 (ранее) | DualTrendCompressionRestartShortV1Strategy, 1h/4h, SHORT trend/pullback-compression | [wangc-joker/ft_userdata](https://github.com/wangc-joker/ft_userdata/blob/6833cb9b4bc5bfb01c3f5829ff11cc02b0814fd9/user_data/strategies/DualTrendCompressionRestartShortV1Strategy.py), commit `6833cb9`, file blob `36cfb029cd7dc871160b037548db2c57de852969` | https://freqle.org/strategy/5be7d77a47ba4321 | **+28.51%** | −13.18% | 292 | 1.20 | 2022 +13.1; 2023 +6.7; 2024 +7.1 |
| 2 NEW | TrendFollowing, 4h, EMA/ADX trend continuation, long+short | [krantikaridev/freqtrade](https://github.com/krantikaridev/freqtrade/blob/11d7d66c60cf49a148cb61619b8061dc40d2510c/strategies/TrendFollowing.py), commit `11d7d66`, file blob `ee2293e19f3cdecb082525f6d55a166249f74eb2` | https://freqle.org/strategy/483b6e3a8af858a6 | **+97.31%** | −13.25% | 2181 | 1.30 | 2022 +54.99; 2023 +19.14; 2024 +23.21 |
| 3 NEW | NASOSv7LongShort, 5m, EMA/EWO/RSI mean reversion long+short | [remiotore/ccxt-freqtrade](https://github.com/remiotore/ccxt-freqtrade/blob/44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03/strategies/NASOSv7_FuturesC.py), commit `44beaeb`, file blob `172fd2b5e76cb1b14d4c9547b6046bff7f19ba7a` | https://freqle.org/strategy/ec3bb293ac111096 | **+95.08%** | −7.60% | 3-year summary (use exact Freqle row before independent check) | Freqle page | 2022 +13.84; 2023 +38.20; 2024 +43.21 in 5-year version; Freqle 3-year run summarized +95.08 |
| 4 NEW | BearRegimeShortV1, 1h, bearish market short-only regime | [IvPalmer/Master-Trader](https://github.com/IvPalmer/Master-Trader/blob/8e29d170982c36a502de2c6ed14a80c6510c4921/ft_userdata/user_data/strategies/BearRegimeShortV1.py), commit `8e29d17`, file blob `a6c62639e60a28b050a462f646241e7a2ba9076c` | https://freqle.org/strategy/8af3cbbe7dc54a2d | **+13.11%** | −10.24% | 333 | 1.20 | 2022 +6.14; 2023 +0.15; 2024 +6.82 |
| 5 NEW | Risk_Stair_S5, 15m + 4h, trend breakout, dynamic stair/time exit, long+short | [linhuang1212-coder/crypto-quant-trading](https://github.com/linhuang1212-coder/crypto-quant-trading/blob/63c012a0329a280f99fe57896456d4b9363c9c71/user_data/strategies/risk_exp/Risk_Stair_S5.py), commit `63c012a`, file blob `9b6ba1f5466727da1e9446f4e283b1c555fca59b` | https://freqle.org/strategy/19f9d9a5e87fc648 | **+215.64%** | −32.90% | 3014 | 1.12 | 2022 +31.66; 2023 +135.97; 2024 +48.02 |

### Риски, зафиксированные без начала детального анализа

1. **DualTrend** — Freqle собственная оценка `FRAGILE`, p≈0.1294, не статистически подтверждённый edge, нельзя считать победителем. При разном запуске Freqle сумма менялась; нужен frozen original next-open parity.
2. **TrendFollowing** — Freqle static trust *no lookahead patterns*, но неполный 200-EMA startup, trailing и stop-on-exchange vs OHLC backtest; отдельные detail прогоны включают отрицательный результат. Обязательная проверка.
3. **NASOSv7** — Freqle static trust *no lookahead patterns*, но `custom_stoploss` в исходнике **НЕ вызывается** (`use_custom_stoploss=False`); фактический стоп 15% и trailing 5m; `position_adjustment_enable=True`, но `max_entry_position_adjustment=0`, поэтому не считать рекламный DCA рабочим. 5-летний отчёт отдельно включает 2025 +2.45%, но это **другой интервал запуска**, не суммировать 2022–24 с ним.
4. **BearRegimeShortV1** — весь edge 2023 всего **+0.15%**, похоже на флуктуацию рядом с нулём; 1h short-only, слабая диверсификация против №1 до проверки корреляции сделок.
5. **Risk_Stair_S5** — **5× leverage**, MaxDD −32.9% на 2022–24 и −35.49% в отдельном пятилетнем запуске, fee drag высокий, long трендовое семейство частично похоже на №2. Freqle static trust no lookahead patterns, но 4h trailing и warmup/stop fill parity требуют доаудита.

### Что сознательно НЕ включено

- `AggressiveSupportResistanceScalper` демонстрировал +55.82%, MaxDD −4.51%, но Freqle trust обнаружил явные `whole_series_reduction: .min()/.max()` по всей истории. Пока не независима воспроизводимость, это **не кандидат**.
- Spot-only стратегии, очевидная DCA без ограничения, маркетинговые стратегии и научные гипотезы без ready-to-run исходного кода.
- Три явно исключённых пользователем A220 и все ранее отрицательные оригинальные A188–A227.

**Дальнейшие действия строго по отдельной команде пользователя:** независимо переисполнить все **ПЯТЬ оригиналов без модификации параметров** с источниковым provenance и честными Binance USD-M mark/funding/fees/slippage/liq 2024,2025,Jan–Sep2026, раздельным оцениванием и проверкой причинности, risk stress и OOS, отдельно сравнить корреляцию и пригодность для небольшого депозита. Пока пользователь сказал только СОБРАТЬ 5, **не делать независимые тесты**. Никаких реальных/виртуальных ордеров.