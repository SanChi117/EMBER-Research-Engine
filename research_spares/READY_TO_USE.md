# EMBER SPARES v0.3 — подключаемая библиотека вычислений

**Что готово:** 37 именованных компонентных точек (`Z01–Z38`, кроме уже реализованной `Z12`), 5 дополнительных алгоритмов, единый вызов по ID, чтение Binance USDT-M OHLCV/funding/OI/bookTicker, подключение кадров EMBER (Polars LazyFrame/DataFrame), pandas или массива словарей, консольная команда, запускаемые примеры и тесты.

**Что не следует выдавать за готовое:** никакая из внешних 76 стратегий не стала 1:1 source-parity-реализацией; нет реального биржевого execution/funding history downloader/ликвидационного движка. Модули готовы к вызову **с предоставленными данными**; обязательные исторические записи не создаются из воздуха. Никаких денег, API-ключей, торгового Gateway, новых автоматизаций и PAPER изменений.

## Установка единожды

Из корня EMBER на ветке библиотеки:

```bash
python -m pip install -e ./research_spares
python -m unittest discover -s research_spares/tests -v
python -m ember_spares.examples
```

Или установить независимо, без переноса/встраивания файлов в EMBER:

```bash
python -m pip install 'git+https://github.com/SanChi117/EMBER-Research-Engine.git@research/spares-library-core-20261101#subdirectory=research_spares'
```

## Подключить любую деталь без ручного адаптера

```python
from ember_spares import invoke

# Z22 — давление агрессивных покупателей по закрытым свечам
value = invoke('Z22', {'buy_volume':[50,80], 'total_volume':[100,100]})
assert value == .65

# Z09 — если OHLC содержит и SL, и TP, не выдумываем последовательность
bar = {'open_time':0,'close_time':60,'available_at':60,
       'open':100,'high':105,'low':95,'close':102,'volume':1000}
out = invoke('Z09', {'bar':bar,'side':'long','stop':96,'target':104}, decision_at=60)
assert out == 'AMBIGUOUS'
```

`invoke()` сам создаёт типизированные объекты, проверяет параметры и возвращает JSON-сериализуемый результат. `decision_at` ограничивает историческую доступность свечей. При ошибке входа отказ, а не фиктивный торговый сигнал. Все ID покрыты исполнимыми тестовыми примерами (`python -m ember_spares.examples`).

## Вход из реального EMBER Polars

```python
from ember_spares.bridge import run_on_candles

# Обычные строки из EMBER DataEngine: symbol,time,open,high,low,close,volume.
# `lf` может быть pl.LazyFrame. Не вызывать на полном будущем наборе
# без `decision_at` — функция остановится на будущих свечах.
result = run_on_candles(
    'Z16', lf, symbol='SOLUSDT', timeframe_seconds=3600,
    decision_at=1761955200, lookback=30
)
```

Данные одной монеты не смешиваются с другой: при нескольких символах без `symbol=` вызов отклоняется. Для неточной/неподтверждённой даты в dataframe вызывающий обязан указать `time_is='open'|'close'` и длительность свечи.

## Оригинальные Binance public records — чтение без сетевых запросов

```python
from ember_spares.binance import parse_kline, parse_funding, parse_oi, parse_book_ticker
from dataclasses import asdict
from ember_spares import invoke

bar = parse_kline(binance_usdtm_rest_kline_row)  # закрытая свеча
result = invoke('Z09', {'bar':asdict(bar), 'side':'long', 'stop':96., 'target':104.}, decision_at=bar.available_at)

# Публикационная задержка финансирования/OI должна быть задана явно.
funding = parse_funding(historical_funding_record, publication_lag_ms=1000)
oi = parse_oi(historical_open_interest_record, publication_lag_ms=1000)
```

У `parse_kline` timestamps в миллисекундах конвертируются в UTC секундные границы; незакрытая WebSocket-свеча отклоняется.

## Консольный интерфейс

```bash
ember-spares list
printf '{"buy_volume":[50,80],"total_volume":[100,100]}' | ember-spares Z22 -
```

Вывод — структурированный JSON `{ok, component, result}`. Неправильный вход = код завершения `2`, никакого открытия сделок.

## Дополнительные готовые функции

| Группа | Имя | Обозначение |
|---|---|---|
| Z15 | `Z15.patterns` | причинно подтверждённые double/triple top/bottom, H&S и треугольники |
| Z19 | `Z19.ott` | OTT семейство (собственная прозрачная реализация, не оригинал Freqtrade) |
| Z19 | `Z19.var` | переменная EMA, CMO-модификация |
| Z27 | `Z27.predict_linear` | проверка хэша JSON-модели и безопасный logistic inference |
| Z30 | `Z30.holdout_gate` | не допускать пересечения обучающей и тестовой истории |

Все эти расширения доступны через `invoke()` и отдельные чистые функции `ember_spares.extra`.

## Границы пригодности

- **Готово немедленно для расчётов:** доступные OHLCV, цены, объёмы, стоп-геометрия, cash-ledger, сигнальные признаки, портфельные ограничения, портфельные отчёты.
- **Нужны реальные записи:** funding/OI/mark/L2 и другие события. Вызовы уже работают; для точного исторического вывода требуются корректные внешние ряды и их публикационные задержки.
- **Не готово без дальнейшей независимой работы:** точные биржевые ликвидации, заполнение очереди лимиток, права на импорт чужого кода, исходный торговый алгоритм и авторские backtest fills, реальный gateway.

`READY_FOR_OFFLINE_USE` **не равен** `VALIDATED_BINSANCE_USDTM_STRATEGY`. Включение в EMBER стратегию остаётся явным решением автора проекта. Неизменный мандат `RESEARCH_MANDATE_LOCKED.md` соблюдается.


## Новое в v0.3: прямое подключение

- `ember_spares.ready.run_binance_usdm` — одна функция Binance USD-M REST -> OHLCV/mark/funding/OI/taker -> Z01/Z03/Z14/Z15/Z16/Z19/Z20/Z21/Z22/Z26. Не требует собственного адаптера истории.
- `ember_spares.binance_feed.BinanceUSDMPublic` — read-only historical HTTP client с пагинацией; по 451 возвращает блокировку и никогда не подменяет фьючерсы Spot.
- `ember_spares.operations.SQLiteResearchLedger` — SQLite журнал событий + risk latch, защита от дублей и случайных снятий HALT, повторное открытие из другого процесса.
- `ember_spares.adapters.parity_from_exports` — конвертирование оригинальных экспортированных сигналов Freqtrade/Pine/других рантаймов в общий trace с настройкой имён колонок; без исходного export нельзя подтвердить эквивалентность.
- `ember_spares.advanced` и `invoke('Zxx.function', {...})` — расчёты маржинальных ступеней, многоногих cashflow, комбинаций индикаторов и сегментной статистики.
- `python -m pytest research_spares/tests -q` — проверяет результат на стандартных синтетических и формате фиктивных ответов Binance (HTTP не был доступен из рабочего контейнера).

**Дата и время:** данные должны быть точными, с UTC и явно зафиксированной задержкой публикации. Арбитраж/фандинг, книга L2 и стопы не являются «готовой прибыльной стратегией» лишь потому, что их вычислитель импортируется.
