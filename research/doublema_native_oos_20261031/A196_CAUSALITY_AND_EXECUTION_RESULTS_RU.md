# A196 — контроль причинности и более реалистичного исполнения Double MA

Дата 31 октября 2026. PAPER research only.

## Часть 1. Оригинальный исходник, временная доступность индикаторов/сигналов — ГОТОВО

**Оригинал без изменений:** `MirrorNew/2026DoubleMaFuturesStrategy` May12 commit `40af5c7c1c44253766428cfb06babf22f9817aa4`; `VideoDoubleMaFuturesStrategy.py` Git blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`, `freqtrade==2026.4`.

**Реальный Freqtrade source computation, без переписанной модели индикаторов:** запуск исходных `populate_indicators` и `populate_entry_trend` на полной истории и на 40 отдельно обрезанных префиксах, максимально доступных к закрытию 1h свечи, с 4h информативными свечами только после их закрытия. Точки May15–Sep27 2026 (10 дат × 4 пары BTC, ETH, SOL, LINK), 20 оригинальных проверенных колонок на каждой точке: `enter_long/short/tag`, first pullback, stops, cluster zones, ATR, 4h HTF flags, pivots, MA directions, MA band. **40 × 20 = 800 проверок: 0 несовпадений.**

Реальная проверка CI: [run 41148182095](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41148182095), **SUCCESS**, [artifact 13021044804](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41148182095/artifacts/13021044804), SHA256 `1fea6180ff6047470e1f083c8ddcb305fdfea6aedb54075a24f1ef5791553f61`.

Ограничение: это **40 выбранных контрольных моментов**, не весь массив и не полный `freqtrade lookahead-analysis`, не `recursive-analysis`, не полная проверка `custom_stoploss/custom_exit`. Называть исходную стратегию «полностью без lookahead» **нельзя**. A188 только локально подтвердил, что одно изменение границы callback не изменило 27 ETH сделок, и не доказал полную безопасность.

## Часть 2. Нативное Freqtrade 1h против 5m детального исполнения — проверка в процессе

Зафиксированный до анализа план: [A196_5M_EXECUTION_PREREGISTERED_PROTOCOL_RU.md](A196_5M_EXECUTION_PREREGISTERED_PROTOCOL_RU.md). Оригинальные исходники и параметры 1h + 4h не изменяются. Используется `--timeframe-detail 5m` с настоящими 5m OHLCV Binance Vision May–Sep2026; сравнение против фактических 8 ZIP сделок A195 на BTC, ETH, SOL, LINK и двух комиссиях. Отделить несоответствие fill path от отсутствия прямой проверки bidder-ask и точной временной очереди лимиток.

**Статус:** до появления проверенных исходных receipt не писать экономическую оценку результата. Контроль `original 5m source SHA` + `full native trades` — обязателен.

## Важный вывод

Сами **наблюдаемые** индикаторы при дополнении будущей истории не изменились на выбранных 40 моментах. **Прибыльность не доказана**: как показал A195, даже +34.8% ETH, +17.3% SOL, +36.5% LINK в исходном 1h backtest могут зависеть от топ-3 сделки и исполнения лимитных заявок. Любой возможный Paper запуск запрещён до независимой проверки исполнения и более длительного периода.

Никаких реальных ордеров, изменений PAPER-планировщиков и SMOKE.
