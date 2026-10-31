# EMBER — Библиотека потенциально дополнительных компонентов («запчасти»)

**Дата:** 01.11.2026. **Статус:** DOCUMENTATION ONLY / NO IMPORT / NO BACKTEST / NO PAPER CHANGES.  
**Основания:** [реестр R001–R076](STRATEGY_SEARCH_ALL_CANDIDATES_RANKED_20261101.md), [CSV](STRATEGY_SEARCH_ALL_CANDIDATES_RANKED_20261101.csv), [замороженный мандат](RESEARCH_MANDATE_LOCKED.md), [канонический статус](RESEARCH_STATUS_CANONICAL.md) и технический каталог 76 карточек предыдущего этапа (в GitHub пока не публиковался).

## Назначение и границы

Сохранить **неиспользованные или не подтверждённые в наших текущих реализациях** элементы исходных стратегий. **Не создавать ещё одну стратегию**, не включать ничего автоматически и не смешивать этот список с рейтингом прибыльности. Ни один компонент не проверен на совместимость с EMBER/SMOKE; наличие полезной идеи не означает наличие пригодной лицензии/кода, работающей реализации или экономического преимущества.

### Что у нас уже есть — не дублировать как «новое»

- EMBER: OHLCV, EMA/RSI/ATR, swings, частичные FVG/OB/POI, MTF context, ATR SL, cost gate, fixed/opposing-liquidity TP, portfolio, WFO, структурная диагностика, базовый kill switch.
- SMOKE: 1W/1D/4H/15m/5m, dealing range, BOS/CHoCH, FVG/OB, sweep/reclaim, уровни, маршрут к зоне, структурные SL/TP, WebSocket, PAPER исходы (pending/TP/SL/expired) и журнал.
- **Значение статуса «не подтверждено»:** изучены ядро EMBER и README SMOKE, а не исчерпывающе каждая ветка и файл обоих проектов. Похожий компонент может существовать в другом модуле. Перед импортом выполнить read-only сверку конкретных функций.
- Мандат Binance USDT-M Futures не меняется. Spot/OKX/Bybit/Kraken/BloFin оригиналы — только источники идей; их показатели не переносить на Binance.

**Приоритеты:** P0 — достоверность данных, риск и исполнение; P1 — возможные сигнальные/структурные дополнения; P2 — диагностика и исследовательский инструментарий. **Приоритет не является поручением внедрять.**

## Реестр дополнительных компонентов (38)

### Z01 · P0 — Календарная доступность данных и point-in-time join

- **Источники:** R010,R023,R024,R025,R052,R075; X08.
- **Как работает:** Цена, mark, индекс, funding, OI, taker и стакан имеют разные периоды и моменты публикации. Сигнал должен видеть только сведения, которые уже появились к моменту решения.
- **Пересечение с нашим кодом:** EMBER: OHLCV/MTF/свечи; по исследованным core-модулям полноценного события funding/OI/mark нет.
- **Что потенциально добавить:** Единый event-time слой: event_time, published_at, available_at, venue, instrument, source_SHA; as-of join, контроль пропусков и задержек.
- **Ограничение / доказательность:** Без исторических архивов Binance USD-M mark/funding/OI/taker и точных timestamp нельзя признавать сигнал воспроизводимым.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z02 · P0 — Фьючерсная маржа, ликвидации и mark-stop

- **Источники:** R004,R010,R011,R030,R038,R050,R075.
- **Как работает:** Баланс, маржа isolated/cross, maintenance tiers, funding, realised/unrealised PnL, mark-trigger и ликвидация пересчитываются после каждого события/добора.
- **Пересечение с нашим кодом:** EMBER risk_engine считает номинал/маржу приблизительно; README прямо указывает отсутствие модели ликвидаций и funding.
- **Что потенциально добавить:** Изолированный margin/liquidation simulator + сценарии гэпов, cross-collateral, ступени MMR, 2×/5×/20×; остановка до оценок прибыли.
- **Ограничение / доказательность:** Критично для −100% stop у R030, 5× R004, портфеля R011; не переносить риск-модель этих стратегий до проверки.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z03 · P0 — Фактическое исполнение лимиток и L2-микроструктура

- **Источники:** R066,R039,R046,R053; X01,X02.
- **Как работает:** Из bid/ask sizes получают OBI и microprice; очередность заявок, spread, queue position, maker/taker и partial fill определяют реальную цену сделки.
- **Пересечение с нашим кодом:** Есть WebSocket/объём и моделируемая комиссия; полноценная историческая книга L2 и queue replay не подтверждены.
- **Что потенциально добавить:** Отдельный модуль microprice/OBI + реалистичная модель очереди лимитных ордеров; фиксировать data provenance и capacity.
- **Ограничение / доказательность:** OHLCV не восстанавливает историческую очередь; без архивов L2 можно только оценивать диапазон неопределённости, не выдумывать fill.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z04 · P0 — Сверка одного сигнального ядра между research и PAPER

- **Источники:** R036,R045,R052,R057.
- **Как работает:** Сигнал считается одной детерминированной функцией на закрытых входных данных; журнал содержит source version, feature values, signal time, submit/fill time.
- **Пересечение с нашим кодом:** В EMBER и SMOKE есть отдельные backtest/PAPER контуры; точный идентичный сигнал до каждой свечи не подтверждён.
- **Что потенциально добавить:** Signal replay contract: один и тот же модуль, снимок входа, хеш решения и diff на уровне каждого бара между режимами.
- **Ограничение / доказательность:** R036 делает pure-function engine, R045 ведёт артефакты и state; нельзя переносить их результаты Spot/ML напрямую.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z05 · P0 — Портфель двух ног и funding по каждой ноге

- **Источники:** R046,R049,R067; X08.
- **Как работает:** Pair spread/cointegration или carry требует двух синхронных legs: цены, hedge ratio, funding по каждой, fees, недоисполнение одной ноги.
- **Пересечение с нашим кодом:** EMBER portfolio отслеживает сделки, но атомарную/частично заполненную пару в просмотренных модулях не обнаружено.
- **Что потенциально добавить:** Multi-leg portfolio ledger, partial-hedge exposure, hedge rebalance, transfer/venue risk и фиксирование legs.
- **Ограничение / доказательность:** Не считать арбитраж без риска: basis, borrow, leg slippage, ликвидация и рыночная нейтральность требуют отдельных проверок.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z06 · P0 — Частичные выходы, доборы и денежный журнал

- **Источники:** R010,R037,R038,R057,R060.
- **Как работает:** TP1/TP2/TP3, частичные закрытия, перенос стопа, пирамидинг/усреднение, финансирование и комиссии по каждой ноге должны менять оставшийся риск и капитал.
- **Пересечение с нашим кодом:** SMOKE имеет планы ENTRY/SL/TP и PAPER outcome; полный cash-event ledger для частичных fill/scale-in не подтверждён.
- **Что потенциально добавить:** Событийный ledger: fill_id, parent_trade, qty, fee, funding, margin, average_entry, remaining_stop_risk; invariants суммы.
- **Ограничение / доказательность:** R038 содержит funding на доливе; R057 state-machine TP; нельзя вписать фиксированное RR вместо авторской модели.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z07 · P0 — Общий риск нескольких разных движков

- **Источники:** R011,R040,R060,R074; X18.
- **Как работает:** Независимые стратегии создают коррелированные позиции; общий RiskGuard ограничивает суммарный DD, gross/notional, overlap и stop exposure.
- **Пересечение с нашим кодом:** EMBER имеет портфельный kill switch; риск по нескольким отдельным стратегиям и корреляциям не подтверждён.
- **Что потенциально добавить:** Portfolio-level multi-strategy budget, конфликт сигналов и correlation netting; раздельный PnL/воздействие.
- **Ограничение / доказательность:** R060 ZENITH/GEM общий RiskGuard; закрытые модели R074 не переносить.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z08 · P0 — Персистентное состояние защит и восстановление после рестарта

- **Источники:** R008,R019,R050,R053.
- **Как работает:** Daily/weekly loss breaker и cooldown хранятся между сессиями; рестарт не должен сбрасывать запрещение входа; состояние сверяют с журналом/биржей.
- **Пересечение с нашим кодом:** В EMBER kill switches есть, но сохранение/восстановление после restart в изученных core-модулях не подтверждено.
- **Что потенциально добавить:** Persistent RiskState + restart/reconcile test, idempotent transition и запрет silent reset.
- **Ограничение / доказательность:** TSMOM меняет экономику при штатном breaker: без сверки нельзя объявлять исходный плюс валидным.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z09 · P0 — Тайминг очередности касаний и неопределённость intrabar

- **Источники:** R016,R017,R018,R020,R021,R070.
- **Как работает:** В одной OHLC-свече TP и SL могут быть достигнуты в разном порядке; надо использовать 1m/tick, если есть, иначе диапазон лучшего/худшего исхода.
- **Пересечение с нашим кодом:** SMOKE разрешает спорные свечи SL-first; EMBER имеет баровую модель, но авторские fill-семантики могут отличаться.
- **Что потенциально добавить:** Необратимый dual-touch diagnostic; диапазон неопределённости, отдельные цены open/gap, TTL лимиток.
- **Ограничение / доказательность:** BIGBEAR/BIGBULL исходно использовали случайный выбор 50/50 при двойном касании: такой тест не подтверждает реалистичную прибыль.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z10 · P0 — Срок жизни ордера, missed fills и stale-data контроль

- **Источники:** R018,R022,R053,R059,R061.
- **Как работает:** Сигнал, размещение, TTL, отмена, частичное исполнение, повторная заявка и stale candle — отдельные состояния.
- **Пересечение с нашим кодом:** SMOKE имеет pending/expired, но queue/missed_fill и время отправки на реальную площадку не доказаны.
- **Что потенциально добавить:** Order state-machine с timestamp→execution, missed fills, TTL, reject/retry и fee/latency sensitivity.
- **Ограничение / доказательность:** Не подменять limit entry гарантированным исполнением по свечному high/low.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z11 · P1 — Жизненный цикл структурных зон и качество волн

- **Источники:** R033,R034,R035.
- **Как работает:** Swings образуют волны; зона имеет born/active/touched/broken/retest/flip, wick bounds, score качества и конечную доступность в времени.
- **Пересечение с нашим кодом:** SMOKE имеет зоны/реакции; EMBER FVG/POI частично приближены, не доказана идентичность сложного zone-lifecycle.
- **Что потенциально добавить:** Сравнительный модуль market_structure: causal wave registry, per-zone provenance, quality и lifecycle.
- **Ограничение / доказательность:** Внешняя библиотека есть (MIT); оригинального класса MsSupportResistanceV1 нет. Нельзя приписывать ему прибыль 404 сделок после импорта только библиотеки.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z12 · P1 — Причинный перенос HTF на LTF с временем доступности

- **Источники:** R002,R033,R034,R052,R056.
- **Как работает:** 4H индикатор, сформированный при закрытии 4H, доступен 1H/15m только после закрытия/публикации; shift/merge и warmup обязательны.
- **Пересечение с нашим кодом:** В EMBER и SMOKE MTF есть, но детальная parity-инвариантность для всех новостей/структур не доказана.
- **Что потенциально добавить:** Единый as-of resampler со строгим closed-bar timestamp, тестами HTF shift и first-available LTF.
- **Ограничение / доказательность:** Референс: fortunato/mtf.py с HTF shift(1); не делать сдвиг дважды и не отменять необходимый.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z13 · P1 — Декларативные правила Price Action

- **Источники:** R058,R068,R070.
- **Как работает:** Выражение уровня, failed breakout, retest, consolidation и последовательного триггера как проверяемых правил в on_bar-контексте.
- **Пересечение с нашим кодом:** BOS/sweep/retest имеются, но отдельный проверяемый DSL для сравнения реализаций не подтверждён.
- **Что потенциально добавить:** Набор независимых распознавателей с event_time и единой семантикой «образован/подтверждён/исполнен».
- **Ограничение / доказательность:** stolgo даёт библиотеку/примеры, а не доказанный edge; формат bracket нужно тестировать.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z14 · P1 — Состояния compression→breakout→failed return→restart

- **Источники:** R002,R029,R058.
- **Как работает:** Сжатие диапазона по ATR/ширине, выход, неудачный возврат, повторный импульс, reclaim, cooldown. Каждая фаза на известной свече.
- **Пересечение с нашим кодом:** SMOKE умеет продолжение/retest; отдельный накопительный автомат сжатия и рестарта не подтверждён.
- **Что потенциально добавить:** Finite-state detector + журнал переходов и требований volume/HTF.
- **Ограничение / доказательность:** R029 исходный код long-only (несмотря на противоречивый README); не переносить предполагаемые shorts.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z15 · P1 — Независимые детекторы геометрических фигур

- **Источники:** R014,R015,R044,R047,R070.
- **Как работает:** Четырёхчасовые фигуры: флаг, треугольник, двойная вершина/дно, голова-плечи; 5m wick/candle sequences; сигнал после фактического подтверждения пивота.
- **Пересечение с нашим кодом:** Есть swings и структуры BOS; полный набор детекторов фигур не подтверждён.
- **Что потенциально добавить:** Отдельные причинные функции с паттерн-id, временем подтверждения, статистикой по каждому.
- **Ограничение / доказательность:** Сохранить как диагностические признаки; авторские результаты основаны на других venue/universe и могли иметь survivorship bias.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z16 · P1 — Непрерывный FVG-channel как альтернатива одиночным зонам

- **Источники:** R028.
- **Как работает:** Bull/bear FVG агрегируются в сглаженные верх/низ/mid канала; вход по пересечению границ, а не факту одной незакрытой зоны.
- **Пересечение с нашим кодом:** FVG и POI есть, но агрегированный динамический FVG channel не подтверждён.
- **Что потенциально добавить:** Вычислитель channel upper/lower/mid, упругость/возраст зоны, signal provenance.
- **Ограничение / доказательность:** Контрольный USD-M стресс R028 отрицательный 2024–2026; модуль изучать как feature, не готовую стратегию.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z17 · P1 — Распознавание ложного пробоя и ранний выход

- **Источники:** R020,R044,R058,R061,R062.
- **Как работает:** Свеча пробивает уровень, не удерживает его, возвращается или подтверждается последующей свечой; separately failure-exit и invalidation.
- **Пересечение с нашим кодом:** SMOKE имеет sweep-reclaim, но нет подтверждения полного семейства failed-break/early-exit.
- **Что потенциально добавить:** Сравнить независимые версии failed_break с trigger-on-close/next-open и early invalidation.
- **Ограничение / доказательность:** R020 исходный same-close тест некорректен, нельзя переиспользовать результаты.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z18 · P1 — Переключатель regime и устойчивость режима

- **Источники:** R003,R036,R043,R051,R062.
- **Как работает:** ADX/EMA/volatility, наблюдение persistence 30m/1h, выбор trend/breakout/range-reversion с явным neutral state.
- **Пересечение с нашим кодом:** Режимы есть; нет доказательства точного persistence/route per strategy.
- **Что потенциально добавить:** Протокол состояния режима с минимальной длительностью, гистерезисом, исключением nan/warmup.
- **Ограничение / доказательность:** Не переносить авторские «прибыльные regime switches» без A/B и OOS.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z19 · P1 — SuperTrend, OTT и HMA-коридор как альтернативные признаки

- **Источники:** R006,R007,R031,R032,R036,R071.
- **Как работает:** ATR/SuperTrend direction flip, OTT адаптивная линия, Hull MA corridor, EWO и многоскоростные RSI; отдельные признаки для независимого сравнения.
- **Пересечение с нашим кодом:** EMA/ATR/RSI уже есть; эти формулы/варианты не подтверждены отдельными feature modules.
- **Что потенциально добавить:** Оригинальные функции признаков с версионированными параметрами; не заменять ими существующие EMA по умолчанию.
- **Ограничение / доказательность:** R032 оригинал runtime blocked; R031 стоп −26.5%; R007 98% exposure; это не кандидаты для прямого переноса risk.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z20 · P1 — Funding extremum, z-score и OU half-life

- **Источники:** R023,R049,R065; X08.
- **Как работает:** Funding rate как событие 8h, z-score исторической ставки, оценка OU mean reversion/half-life; сигнал отдельно от денежного funding PnL.
- **Пересечение с нашим кодом:** В основном EMBER funding не моделируется; быстрые макросрезы не равны историческому событийному слою.
- **Что потенциально добавить:** Фичи funding_level, lagged_z, OU half-life и cash-flow; valid-only if point-in-time.
- **Ограничение / доказательность:** R023 публичный CSV не содержит рекламируемого XRP; R065 OOS отрицателен; Z-score — не доказательство edge.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z21 · P1 — Четыре режима price×Open Interest

- **Источники:** R024.
- **Как работает:** Рост/падение цены × рост/падение OI: вход новых позиций либо закрытие старых; taker ratio уточняет подтверждение.
- **Пересечение с нашим кодом:** Есть price direction и объём; полноценный point-in-time OI classification не выявлен.
- **Что потенциально добавить:** Четырёхквадрантный классификатор с lag, taker confirm и regime label.
- **Ограничение / доказательность:** Авторский DD до −97.5% на SUI; использовать как исследовательский признак, не автономный сигнал.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z22 · P1 — Агрессивный поток покупок/продаж (taker buy ratio)

- **Источники:** R023,R024,R025.
- **Как работает:** Rolling taker_buy_volume / total_volume отличает агрессора от обычного свечного объёма; сигнал при устойчивости нескольких баров.
- **Пересечение с нашим кодом:** Обычный volume_ratio есть; taker-side сделки и лаг публикации не подтверждены.
- **Что потенциально добавить:** Фича taker_pressure, rolling persistence, trade timestamp; compare above candle-only baseline.
- **Ограничение / доказательность:** У R025 большинство авторских рынков имеют отрицательный PF; отдельно от прибыли стратегии.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z23 · P1 — BTC→alt lead–lag событийная задержка

- **Источники:** R067.
- **Как работает:** При резком движении BTC в разные режимы проверяется delayed reaction по конкретным альтам на секундном/минутном горизонте.
- **Пересечение с нашим кодом:** BTC macro gate уже есть; синхронизированный event-trigger latency estimator не подтверждён.
- **Что потенциально добавить:** Event-study с задержкой, лаг-распределением, историческими одновременными feed snapshots.
- **Ограничение / доказательность:** Kraken Futures оригинал и авторская гипотеза; перенос latency на Binance не гарантирован.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z24 · P1 — Cross-sectional momentum и динамический ranking

- **Источники:** R011,R040,R053.
- **Как работает:** Монеты ранжируют по доходности за 14/21/90d, ATR/волатильности, volume/tradability; портфель периодически ротируется.
- **Пересечение с нашим кодом:** Scanner и фиксированный universe есть, однако полноценного point-in-time rank/basket/turnover учета не выявлено.
- **Что потенциально добавить:** Исторически воспроизводимый universe, rank snapshots, rebalance/rejected/turnover/capacity ledger.
- **Ограничение / доказательность:** Нельзя выбирать top winners по полному периоду; R040 spot и концентрация ZEC, R053 timestamp flaw.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z25 · P1 — Relative-value / spread z-score двух активов

- **Источники:** R046,R076.
- **Как работает:** Для двух контрактов рассчитывается spread, hedge ratio, rolling z-score, вход в отклонение и закрытие при нормализации.
- **Пересечение с нашим кодом:** Парной статистической торговой модели как самостоятельного модуля не подтверждено.
- **Что потенциально добавить:** Pair signal и portfolio legs отдельно; cointegration gate, rebalance, IC/execution costs.
- **Ограничение / доказательность:** Не подменять Kraken Spot-stat-arb R076 несуществующей авторами futures-реализацией.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z26 · P1 — Относительное отклонение от SMA и медленный decay

- **Источники:** R041,R039.
- **Как работает:** RSI<30 + сильное отклонение от длительной SMA, удержание 48–96h, равномерные небольшие позиции; отдельно от cross-sectional rank.
- **Пересечение с нашим кодом:** RSI и pullback есть, но dislocation/decay function + liquidity caps не подтверждены.
- **Что потенциально добавить:** Детектор dislocation и decay curve; capacity stress, долгий time-stop, stop risk.
- **Ограничение / доказательность:** Оригинальный OversoldReversion Spot и stop −99%: нельзя переносить его risk/экономику.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z27 · P1 — Качественные признаки ML и контракт модели

- **Источники:** R045,R064.
- **Как работает:** Feature registry и версии ML weights, history-only train/validation, inference thresholds, model drift; offline и online должны давать одинаковые сигналы.
- **Пересечение с нашим кодом:** EMBER есть feature builder и WFO, но версии внешних ML-моделей/артефактов в core не подтверждены.
- **Что потенциально добавить:** ModelCard+feature SHA + training cutoff + causal inference adapter; только research.
- **Ограничение / доказательность:** R045 model training/model artifacts не восстановлены; R064 dry-run −$93.98/139 trades. Не использовать прогноз как прибыльный.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z28 · P1 — Deep Fibonacci retracement и раздельные входы

- **Источники:** R060.
- **Как работает:** После импульса определяются leg endpoints, 79% retracement, ATR-стоп за экстремумом, два уровня entry, SMC confluence.
- **Пересечение с нашим кодом:** У EMBER/SMOKE structural zone есть; специализированного GEM dual-entry 79% нет.
- **Что потенциально добавить:** Изолированный fib-leg detector + E1/E2 geometry + independent state trace.
- **Ограничение / доказательность:** Источник BloFin; SMC часть дублирует существующие механизмы, риск и плечо автора не заимствовать.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z29 · P2 — A/B ablation элементов без подмены входов

- **Источники:** R034,R035,R036,R043; X09.
- **Как работает:** Один сигнал и один портфель, включение/выключение единственного фильтра без изменения данных и других параметров.
- **Пересечение с нашим кодом:** WFO/диагностика есть; воспроизводимого single-component matched-trade attribution для всех механизмов не доказано.
- **Что потенциально добавить:** Framework paired-run с дельтой trades/fees/PnL/DD, исходным signal timeline и строгим OOS.
- **Ограничение / доказательность:** MsFilter и NoMs — одна семья, не два независимых прибыльных кандидата.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z30 · P2 — Оценка IC, deflated Sharpe и множественных попыток

- **Источники:** R039,R045,R064,R076; X07.
- **Как работает:** Информационный коэффициент, null/baselines, permutation или bootstrap со структурой времени, deflated Sharpe и поправка на число испытанных вариантов.
- **Пересечение с нашим кодом:** EMBER считает PF/DD/WFO, но IC/multiple-hypothesis correction не выявлены.
- **Что потенциально добавить:** Статистический отчёт: periods, tried variants, confidence intervals, family count, OOS untouched.
- **Ограничение / доказательность:** R076 Spot среднее преимущество после расходов отрицательное; применима методика, не заявленный рынок.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z31 · P2 — Атрибуция результата по активам, режимам и сигналам

- **Источники:** R022,R039,R040,R047,R048.
- **Как работает:** Каждому сигналу/паттерну назначить ID; отдельно PnL по символам, долю топ-3 сделок, концентрацию, leave-one-asset-out, trade tags.
- **Пересечение с нашим кодом:** Отчёты по сделкам/quality gate есть, но устойчивый leave-one-out/концентрация не подтверждены.
- **Что потенциально добавить:** Attribution dashboard: by module/signal/symbol/regime, 3-trade concentration и per-family portfolio effects.
- **Ограничение / доказательность:** Нельзя принимать R034 с 96.2% прибыли от 3 сделок за устойчивый механизм.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z32 · P2 — Диагностика lookahead/warmup/двойного shift

- **Источники:** R002,R027,R052,R054,R055,R056,R061.
- **Как работает:** Centered gradient, отрицательный shift, pivot с правыми барами, EMA19200 при startup500, same-close fill — все требуют момента доступности.
- **Пересечение с нашим кодом:** EMBER имеет 7 leakage tests, но проверка произвольного внешнего pipeline требует отдельного контрактного аудита.
- **Что потенциально добавить:** Data availability tracer по каждому индикатору и automatic reject на NaN/insufficient warmup.
- **Ограничение / доказательность:** Не «исправлять» и одновременно приписывать результат оригиналу: исправленный вариант тестировать отдельным ID.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z33 · P2 — Сверка исходного портфеля и независимого контрольного теста

- **Источники:** R001,R009,R011,R026,R036,R075.
- **Как работает:** Авторский общий счёт, пары, плечо, max positions, repeat entries, wallet/stake и timeframe должны быть восстановлены отдельно от 3-парного стандартизированного экрана.
- **Пересечение с нашим кодом:** Бэктест есть, но старые A233/A240 ошибочно сравнивали раздельные и общий кошелёк.
- **Что потенциально добавить:** Frozen author parity ledger, canonical hashes, per-trade diffs, separate controlled 3-pair benchmark.
- **Ограничение / доказательность:** Никакого verdict у ETH-only R009 за 10-coin OKX; R075 mirrored shorts не равны авторскому short edge.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z34 · P2 — Лимит ликвидности и проскальзывание на входе/выходе

- **Источники:** R039,R040,R041,R047,R066; X02.
- **Как работает:** Лимит объёма исполнения как доля quote volume свечи, spread sensitivity, очередь для maker и forced exit; отдельные оценки цены разных размеров.
- **Пересечение с нашим кодом:** Fee/slippage модель есть, но полные participation caps и market impact не подтверждены.
- **Что потенциально добавить:** Fill envelope при capacity scenarios и стресс на ZEC/малых альтах; показать то, чего свечи не позволяют доказать.
- **Ограничение / доказательность:** Не переносить результат, если большая часть прибыли только в малоликвидном активе.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z35 · P2 — Сезонность/сессии и режимная ошибка селекции

- **Источники:** R016,R037,R059.
- **Как работает:** Анализ времени суток, сезона и weekly/daily resets, без отбора лучшего окна на всей истории.
- **Пересечение с нашим кодом:** Периодические WFO есть; фиксированная методика session ablation не выделена.
- **Что потенциально добавить:** Проверка заранее заданных окон на независимых режимах и stable sessions.
- **Ограничение / доказательность:** BIGBEAR авторский session-filter мог подбираться на той же истории — нужна поправка на поиск.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z36 · P2 — Анализ повторных входов и постоянной экспозиции

- **Источники:** R007,R029,R053.
- **Как работает:** Счётчик re-entry, free capital, time-in-market, sequential open на следующем баре, hidden overlap.
- **Пересечение с нашим кодом:** В SMOKE есть cooldown, EMBER ограничивает max positions; отдельного exposure audit по каждому оригиналу не подтверждено.
- **Что потенциально добавить:** Exposure timeline + repeat-entry attribution, alerts when slots permanently occupied.
- **Ограничение / доказательность:** R007 98.24% времени 4/4 слотов занято: частота 4.76/day не доказывает независимость 4.76 сетапов.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z37 · P2 — Ступенчатый риск и DCA-risk budget как объект исследования

- **Источники:** R004,R030,R038,R064,R074.
- **Как работает:** Risk staircase по состоянию капитала, per-trade volatility scaling, total stop exposure с доборами, DD-scaler.
- **Пересечение с нашим кодом:** Risk_engine имеет общий размер риска, но лестница/квадратичная DD модель в core не подтверждена.
- **Что потенциально добавить:** Отдельная симуляция риска без изменения торговых сигналов; единый maximum loss и margin.
- **Ограничение / доказательность:** При source stop −100% или неизвестной марже не использовать увеличение размера в PAPER.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

### Z38 · P2 — Отдельная инфраструктура для аудита альтернативных исполнителей

- **Источники:** R018,R026,R032,R057,R073; X06,X09,X12,X18.
- **Как работает:** Сравнить Freqtrade/Pine/пользовательский Python по одним входным данным, отделить runtime error, несовместимость, неисполненные заявки и отрицательный PnL.
- **Пересечение с нашим кодом:** Собственные тесты и CI есть, но сравнительная дифференциальная модель неодинаковых исполнителей не собрана.
- **Что потенциально добавить:** Replay-adapter boundary; измерять source/runtime/market/fill discrepancy по каждому test id.
- **Ограничение / доказательность:** Закрытые исходники R073/R074 и неисправный R032 не считать экономическим FAIL.
- **Статус:** `SPARE_UNVERIFIED` — не встроен, не протестирован.

## Полнота охвата R001–R076

Отсутствие отдельного уникального элемента в источнике — не экономический FAIL стратегии. Некоторые карточки ведут к нескольким компонентам. Перечень ниже не исключает кандидата из исходного реестра.

| Кандидат | Источник | Связанные «запчасти» или причина отсутствия новой | 
|---|---|---|
| R030 VolatilitySystem | `freqtrade/freqtrade-strategies` | Z02, Z37 |
| R004 Risk_Stair_S5 | `linhuang1212-coder/crypto-quant-trading` | Z02, Z37 |
| R011 Octopus multi-perp CTA | `OctopusTakopi/crypto-trend-following` | Z02, Z07, Z24, Z33 |
| R029 FailureToReturnStrategy | `hrodrig/freqhub-strategies` | Z14, Z36 |
| R033 MsSupportResistanceV1 | `fortunato/pymarket-structure` | Z11, Z12 |
| R009 SingleB_FixedRR | `liu57liu456/backtest-autopsy` | Z33 |
| R008 TSMOM | `yongzhe2160cs/trading-engine` | Z08 |
| R002 DualTrendCompressionRestartShortV1 | `wangc-joker/ft_userdata` | Z12, Z14, Z32 |
| R022 Acekiller MTF scanner | `Acekiller88/crypto-signal-scanner` | Z10, Z31 |
| R023 XRP funding mean reversion | `Gotodataru/binance-futures-backtest` | Z01, Z20, Z22 |
| R034 MsFilterV6 | `fortunato/pymarket-structure` | Z11, Z12, Z29 |
| R035 MsFilterV6NoMs | `fortunato/pymarket-structure` | Z11, Z29 |
| R016 BIGBEAR | `genia503/mean-reversion-backtester` | Z09, Z35 |
| R017 BIGBULL | `genia503/mean-reversion-backtester` | Z09 |
| R039 nateemma gbb/reversion | `nateemma/strategies` | Z03, Z26, Z30, Z31, Z34 |
| R045 LightGBM Jansen | `djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen` | Z04, Z27, Z30 |
| R042 RSI/ADX scalper | `jiangkaili/binance-trader-bot` | Новая самостоятельная функция пока не доказана; RSI/ADX уже есть; самодельный fee gate не переносить без исправления |
| R046 Pair Trading NEDL | `djienne/pair_trading_NEDL` | Z03, Z05, Z25 |
| R075 V5 Crypto Scalper — perp Momentum theoretical | `knacker65/v5-crypto-scalper` | Z01, Z02, Z33 |
| R057 gmchun breakout | `gmchun83/binancefuturebot` | Z04, Z06, Z38 |
| R014 momentum_wick | `TheoBrigitte/freqtrade` | Z15 |
| R015 momentum_rsi | `TheoBrigitte/freqtrade` | Z15 |
| R019 TrendRider | `darkvolg/Trading` | Z08 |
| R031 FSupertrendStrategy | `freqtrade/freqtrade-strategies` | Z19 |
| R032 FOttStrategy | `freqtrade/freqtrade-strategies` | Z19, Z38 |
| R043 Bollinger Reverter / Donchian | `Superior-Trade/superior-skills` | Z18, Z29 |
| R044 ETH Momentum 2h / DumpReversal | `grinay/geektrade-strategies` | Z15, Z17 |
| R051 AdaptiveRegime / AdaptiveRegimeLong | `Kureshi25/cryptobot` | Z18 |
| R058 stolgo PA variants | `stockalgo/stolgo` | Z13, Z14, Z17 |
| R060 Zenith / GEM | `traderhydr/krpticz` | Z06, Z07, Z28 |
| R066 Orderbook imbalance | `tsuithomas/crypto_research_order_book_imbalance` | Z03, Z34 |
| R067 Lead-lag trader | `mamipour/lead-lag-trader` | Z05, Z23 |
| R068 FMZ SR breakout | `fmzquant/strategies` | Z13 |
| R048 NostalgiaForInfinity X8 | `iterativv/NostalgiaForInfinity` | Z31 |
| R020 Revelio sweep→BOS V1 | `hroussel18/Revelio_Improved_Strategy` | Z09, Z17 |
| R010 SOL Trend Pullback V9 | `kboranyldz/sol-trading-research` | Z01, Z02, Z06 |
| R024 OI momentum/divergence | `Gotodataru/binance-futures-backtest` | Z01, Z21, Z22 |
| R025 Taker momentum | `Gotodataru/binance-futures-backtest` | Z01, Z22 |
| R012 FAdxSmaStrategy | `freqtrade/freqtrade-strategies` | Новая самостоятельная функция пока не доказана; ADX/SMA пересечения уже есть; возможен лишь сравнимый эталонный тест |
| R013 FReinforcedStrategy | `freqtrade/freqtrade-strategies` | Новая самостоятельная функция пока не доказана; основной механизм перекрывается имеющимися, источник/реализацию сверять отдельно |
| R026 Winner15m | `win-boom/BTCquant` | Z33, Z38 |
| R001 Double MA | `MirrorNew/2026DoubleMaFuturesStrategy` | Z33 |
| R003 BearRegimeShortV1 | `IvPalmer/Master-Trader` | Z18 |
| R005 TrendFollowing | `krantikaridev/freqtrade` | Новая самостоятельная функция пока не доказана; обычный тренд/EMA и protections уже представлены, новых компонентов без полного аудита не доказано |
| R006 NASOSv7LongShort | `remiotore/ccxt-freqtrade` | Z19 |
| R028 FVGChannel | `jaredrsommer/freqtradestrategies` | Z16 |
| R027 MTF_Hybrid | `win-boom/BTCquant` | Z32 |
| R007 dip_catcher | `viktors1982/trading` | Z19, Z36 |
| R018 AggressiveSupportResistanceScalper | `Meszqt/freqtrade-test` | Z09, Z10, Z38 |
| R021 Pranay FVG/OB | `pranay123-stack/Algorithmic-Trading-Projects` | Z09 |
| R036 HERMES SuperTrend | `chrysek70/hermes-trading` | Z04, Z18, Z19, Z29, Z33 |
| R037 APEX no-pyramid | `EstebanSP23/crypto_systematic_research` | Z06, Z35 |
| R038 Quattro Donchian | `EstebanSP23/crypto_systematic_research` | Z02, Z06, Z37 |
| R040 MomentumRegimeBasket15mFast | `nateemma/strategies` | Z07, Z24, Z31, Z34 |
| R041 OversoldReversion | `nateemma/strategies` | Z26, Z34 |
| R047 Chart-pattern backtester | `juriok/chart-pattern-backtester` | Z15, Z31, Z34 |
| R049 Funding Carry OU | `aayanvatsa04/btc-perpetual-funding-arbitrage` | Z05, Z20 |
| R050 TrendFutures | `Kureshi25/cryptobot` | Z02, Z08 |
| R052 Den­niskid research / production | `denniskid2520/btcusdt-research-archive` | Z01, Z04, Z12, Z32 |
| R053 Dynamic gainers | `kiattisakph/crypto-scalp-bot` | Z03, Z08, Z10, Z24, Z36 |
| R055 DivergenceStrategy | `jamniol/freqtrade-setup` | Z32 |
| R056 MandelbrotFibonacciStrategy | `hrodrig/freqhub-strategies` | Z12, Z32 |
| R059 SC4RECOIN breakout | `SC4RECOIN/simple-crypto-breakout-strategy` | Z10, Z35 |
| R061 Milton BTC breakout | `MiltonTulli/trading-bot` | Z10, Z17, Z32 |
| R062 BinHV45 v3 / v4 | `zevrichards/freqtrade-strategies` | Z17, Z18 |
| R071 DS_BNC_EV1E_5m | `Danson77/Freqtrade_AIO_UI` | Z19 |
| R054 RsiquiV5 | `TheoBrigitte/freqtrade` | Z32 |
| R063 GeneticEngineV1 | `ceyhanmolla` | Новая самостоятельная функция пока не доказана; исходный код и SHA не восстановлены — нечего импортировать |
| R064 Ultimate Alpha v16 | `OfficialGIGA/freqtrade-ml-strategy` | Z27, Z30, Z37 |
| R065 Funding zscore | `Adeline117/Strategy-project` | Z20 |
| R069 FMZ retest 482873 | `https://www.fmz.com/strategy/482873` | Новая самостоятельная функция пока не доказана; venue/timeframe mismatch, до исправления нет технически подтверждённого компонента |
| R070 2Candle | `jaredrsommer/freqtradestrategies` | Z09, Z13, Z15 |
| R072 NFI5MOHO_WIP | `davidzr/freqtrade-strategies` | Новая самостоятельная функция пока не доказана; старая API/семейство NFI; независимый модуль не выделен |
| R073 AKzar walk-forward | `AKzar1el/walk-forward-crypto` | Z38 |
| R074 DevAntsa models | `DevAntsa/DevAntsa-Algo-Public` | Z07, Z37 |
| R076 Crypto Stat Arb — spot mean reversion gross edge | `billybraith17/crypto-stat-arb` | Z25, Z30 |

## Дополнительные 18 источников — что сохранять

| ID | Источник | Роль |
|---|---|---|
| X01 | xujaan/futurabot | OBI/CVD/VPIN и поток, проверить конкретные реализации (Z03,Z21,Z22) |
| X02 | DylanSiegel/GO-Microstructures | Hawkes/aggTrades/микроструктура и event-time (Z01,Z03,Z34) |
| X03 | HodlHook/momentum-breakout-postmortem | Отрицательный OOS как контроль методики, не компонент edge |
| X04 | MG-Trading-Terminal/trading-strategy | Позиционирование/OI, нет полного исполнителя |
| X05 | Mykola-Quant/retail-crypto-alpha | Отрицательный futures OOS, архив evidence |
| X06 | PVinh-Quant/Kairos-v2 | Research инфраструктура (Z38) |
| X07 | SebastianBoehler/MarketTensor | ML baseline и слабое преимущество (Z30) |
| X08 | Superjojo74/nautilus-perp-funding | Funding settlement layer, НЕ сигнал (Z01,Z05,Z20) |
| X09 | analogdada/perplab | Тестовый движок/parity/ablation (Z29,Z38) |
| X10 | behlulgoker/price-action-engine | Spot API; только абстрактные PA-правила, без копирования venue |
| X11 | bockuden/crypto-cointegration-research | отрицательная после расходов экономика pair/basis; evidence (Z25) |
| X12 | chiragbitoni/binance-paper-trading-lab | PAPER инфраструктура, не фьючерсный edge (Z38) |
| X13 | francisx1999/crypto-trading-bot-postmortem | отрицательный Kraken/Coinbase OOS, не Binance verdict |
| X14 | joseph280/crypto-backtest-lab | синтетический sanity, не рыночный результат |
| X15 | spagnola-analytics/intraday-strategies | другой рынок, не импортировать сигналы |
| X16 | ycchew/CQ_breakout_strategy | equity/Yahoo, не Binance USD-M |
| X17 | younghwan91/quantbox-engine | недоступный оригинал, SOURCE_BLOCK |
| X18 | zabor-crypto/zaBor | инфраструктура риск-контроля (Z07,Z08) |

## Прямое вето пользователя

`AbdullaE100/perp-quant-lab`, `OctopusTakopi/funding-rate-alpha`, `agarwalchirag535-lab/smallcap-pump-reversal` — `USER_VETO / DO_NOT_REQUEUE`. Важно: Octopus CTA R011 — **другой** репозиторий, не под запретом.

## Проверенные исходные файлы (примеры, SHA относятся к просмотренным файлам, не доказательству работы всего проекта)

| Зачем | Репозиторий/файл | Git blob SHA |
|---|---|---|
| Z11/Z12 | [fortunato/pymarket-structure/src/market_structure/freqtrade.py](https://github.com/fortunato/pymarket-structure/blob/main/src/market_structure/freqtrade.py) | `556f95bdff71aa78c99ab35da5962684600e6984` |
| Z12 | [fortunato/pymarket-structure/src/market_structure/mtf.py](https://github.com/fortunato/pymarket-structure/blob/main/src/market_structure/mtf.py) | `b628a8edf5530bafaa582d81c1b7a2f64bece175` |
| Z04/Z19 | [chrysek70/hermes-trading/hermes_trading/signals.py](https://github.com/chrysek70/hermes-trading/blob/main/hermes_trading/signals.py) | `ac6794eda99cc83e50a097b19e7bb30f9e9bdc89` |
| Z13 | [stockalgo/stolgo/examples/pa/failed_break.py](https://github.com/stockalgo/stolgo/blob/main/examples/pa/failed_break.py) | `2754b3a11465029be55783bb4510ab32b12401db` |
| Z21 | [Gotodataru/binance-futures-backtest/strategy_3_oi_divergence/signals.py](https://github.com/Gotodataru/binance-futures-backtest/blob/main/strategy_3_oi_divergence/signals.py) | `be177d2b24a740bc3ac46115326780c48582ec3e` |
| Z20 | [Gotodataru/binance-futures-backtest/strategy_1_funding_mr/signals.py](https://github.com/Gotodataru/binance-futures-backtest/blob/main/strategy_1_funding_mr/signals.py) | `7528f737eddd459b8505972c01fef60d263715e1` |
| Z20 | [aayanvatsa04/btc-perpetual-funding-arbitrage/funding_arb/models/ou_model.py](https://github.com/aayanvatsa04/btc-perpetual-funding-arbitrage/blob/main/funding_arb/models/ou_model.py) | `d4aaeb1f11d20c9a0e7214e501d022cafa851362` |
| Z06/Z34 | [EstebanSP23/crypto_systematic_research/2_strategies/01_quattro_donchian/backtest_quattro_v2_costs.py](https://github.com/EstebanSP23/crypto_systematic_research/blob/main/2_strategies/01_quattro_donchian/backtest_quattro_v2_costs.py) | `638a29dfac2430809b50154c7b046d75f402d12a` |
| Z27 | [djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen/freqtrade_live/user_data/strategies/LightGBMStrategy.py](https://github.com/djienne/ML_Trading_Strategy_Crypto_BTC_LightGBM_Jansen/blob/main/freqtrade_live/user_data/strategies/LightGBMStrategy.py) | `8c4c66f14f0001f9ad959d149b4e7571b869a02e` |
| Z28 | [traderhydr/krpticz/gem_strategy.py](https://github.com/traderhydr/krpticz/blob/main/gem_strategy.py) | `12d5b0f9309aaf9f3697236610b219c2ef969642` |
| Z07/Z28 | [traderhydr/krpticz/strategy.py](https://github.com/traderhydr/krpticz/blob/main/strategy.py) | `84aa0da94f9d79acb53a0ad574b5102a0ff3ca24` |
| Z09 | [jaredrsommer/freqtradestrategies/2Candle.py](https://github.com/jaredrsommer/freqtradestrategies/blob/main/2Candle.py) | `10f0259053eb5fbd5dd4167006fd22a68c8db223` |
| Z17 | [zevrichards/freqtrade-strategies/BinHV45_Regime_5m_v4.py](https://github.com/zevrichards/freqtrade-strategies/blob/main/BinHV45_Regime_5m_v4.py) | `f133f37902fc19343ec3cff5d9108d825413b002` |
| Z32 | [hrodrig/freqhub-strategies/strategies/FreqHub.Strategy.MandelbrotFibonacci/MandelbrotFibonacciStrategy.py](https://github.com/hrodrig/freqhub-strategies/blob/main/strategies/FreqHub.Strategy.MandelbrotFibonacci/MandelbrotFibonacciStrategy.py) | `ea54ee26dac523fa6ce0e173b75453a6ad5087fc` |
| Z27 | [OfficialGIGA/freqtrade-ml-strategy/README.md](https://github.com/OfficialGIGA/freqtrade-ml-strategy/blob/main/README.md) | `79471eb459b83a5b4811acf990e722617887a497` |

## С чем сверялась текущая реализация EMBER/SMOKE

- [EMBER core/features.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/features.py) — `a7323ff1ce25e3c6def59a8b8d5bf7150681f5cb`.
- [EMBER core/context_builder.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/core/context_builder.py) — `e075d95b54c505d6dcf30def5967899a2cd3e0f8`.
- [EMBER strategy/risk_engine.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/strategy/risk_engine.py) — `b4972edff2807e391ecaf5c62705dbe2c72015cb`.
- [EMBER strategy/exit_simulator.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/strategy/exit_simulator.py) — `23c450858b9c938b9b41bd56b58434f381045490`.
- [EMBER simulation/portfolio.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/portfolio.py) — `a0f689a14301c8cb4b7381801303191845cd9f1e`.
- [EMBER simulation/walk_forward.py](https://github.com/SanChi117/EMBER-Research-Engine/blob/main/ember/simulation/walk_forward.py) — `7c3c346e366e8ca4f0367f2ec7ffe9bf9b6c619f`.
- [SMOKE README](https://github.com/SanChi117/smoke-trading-terminal/blob/main/README.md) — `reviewed 2026-11-01`.

## Правило возможного переноса, только после отдельного разрешения

1. Проверить, действительно ли функция отсутствует, указав сравниваемые функции/версии/поведение (не только совпадение терминов).
2. Проверить лицензию внешнего источника; GPLv3, MIT и отсутствие лицензии не эквивалентны. Не копировать код без подходящих прав.
3. Отделить исходный алгоритм от его авторского бэктестера, торгового счёта и предположений об исполнении; не наследовать небезопасные SL/плечи.
4. Составить contract-in/out, causal timestamp, unit/property tests и независимые данные. Никакой silent repair под видом оригинала.
5. Добавлять в отдельный выключенный исследовательский модуль; сравнивать baseline с/без компонента только на заранее закреплённой выборке и нетронутом holdout.
6. **Никаких действий сейчас:** этот файл не запускает исследования, не меняет стратегию, код, ветки A-серии, PAPER-планировщики, Binance или live.

## Не путать статусы

- `SPARE_UNVERIFIED`: потенциально новая функция, без импортной/экономической проверки.
- `ALREADY_PRESENT`: после точной code-parity проверки выяснилось, что функция уже реализована.
- `SOURCE_BLOCKED`: не найден оригинал, лицензия либо данные — НЕ отрицательная экономика.
- `NO_ECONOMIC_CLAIM`: ни один модуль здесь не считается источником доказанной прибыли.
