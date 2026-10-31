# A219 — исходный 4h chart-pattern backtester: VENUE/SOURCE REJECT, без economic backtest

Дата 2026-10-31. Перед созданием новой ветки прочитан неизменный `main/RESEARCH_MANDATE_LOCKED.md`. Оригинал, **не отредактированный**: [juriok/chart-pattern-backtester](https://github.com/juriok/chart-pattern-backtester/tree/2972c880144997ec305dc3dac23d78ee5a831176) commit `2972c880144997ec305dc3dac23d78ee5a831176`; `config.py`, `data/fetcher.py`, `main.py`, `backtest/portfolio.py`.

**Причина интереса:** автор заявляет положительные 2-летние 4h chart-pattern breakout результаты, в том числе long/short и futures. Этот механизм отличался бы от A217 trend pullback и A218 cointegration, *если бы его оригинальная проверка использовала требуемый рынок*.

## Независимый аудит исходного источника

1. `data/fetcher.py` (blob `ce5e3b10752aa9b21ea487520c38662af932e4c9`): функция `_make_exchange()` строит `getattr(ccxt,config.EXCHANGE)({'enableRateLimit':True})` без `options.defaultType='future'`. `config.EXCHANGE='binance'`. По умолчанию CCXT Binance маршрутизирует такие `BTC/USDT` OHLCV на **SPOT**, а не на `BTC/USDT:USDT` USD-M.
2. `top_pairs()` буквально документирована как `Return top-N USDT spot pairs`, выбирает пары `sym.endswith('/USDT')` и `':' not in sym` — это направленно **исключает perpetual futures CCXT symbols**. Авторская выборка 50 монет по **текущему 24h объёму** даёт point-in-time/survivorship leakage для двухлетней истории.
3. `fetch_ohlcv(symbol,...) ` использует именно этот CCXT источник `fetch_ohlcv(symbol, config.TIMEFRAME)` и CSV cache. Для заявленного фьючерсного PnL **нет источника из Binance USD-M Vision**.
4. `config.py` устанавливает `FUNDING_RATE_8H=0.0001` константой, а не историческими settlement cashflows двух направлений; настоящее funding может менять знак, варьировать по монете/дате.
5. `config.py` явно говорит что 4h/ATR/pattern exclusions/concurrency/risk-сайзинг были многократно отобраны на той же 2-летней выборке, которую README называет преимущественно OOS. Без независимой новой выборки эти авторские числа **не доказательство нетронутого OOS**.

## Решение

**`REJECTED_SOURCE_VENUE_MISMATCH`** для данного оригинального backtest. Это не отрицательный PnL-test, а **неподтверждённая futures экономика**. Авторский ROI `$10k->$39.6k` нельзя переводить в список доказанных USD-M кандидатов. Перевод источника на Binance Futures и историческое funding — **уже новый адаптированный алгоритм**, не проверка неизменного оригинала; согласия на это не было. Никакого ретюнинга и никаких настоящих/PAPER ордеров.

**Сохраняем рабочую идею:** chart-pattern breakouts как семейство для поиска *другой готовой futures-native реализации*; не записывать этот репозиторий как подтверждённый edge.

**Отдельно найден [analogdada/perplab](https://github.com/analogdada/perplab/tree/68251be7e1b4c0ade110bd4e097d524c6ce2acbc)** — явно Binance USD-M futures framework с моделированием расходов, но автор прямо пишет `the engine, not the edges`. Это **возможный инструмент тестирования, а не новая якобы прибыльная стратегия**. Не расходовать цикл на 7 исходных textbook templates без гипотезы и экономического доказательства.

Ни одно решение не изменяет immutable mandate, прошлые отрицательные evidence или торговые системы.