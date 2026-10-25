# B1/C55 — Оригинальные криптовалютные 1H BSL/SSL рейды и следующий закрытый 3m BOS: независимый SOURCE-only перенос Route C

**Дата:** 2026-10-25. `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`. **PAPER ONLY / NOT_TRADE_READY**. Ни одной исполненной сделки, никаких сигналов к торговле или PnL.

## Основная задача

Продолжение C54/A123 с учётом прямого правила владельца: академические изображения — **иллюстрация логики**, проект целиком для **криптовалют**. C54 фальсифицировал попытку брать 4H технический IMB за 1H уровень ликвидности Route C. C55 использует **реальные 1H источниковые BSL/SSL фракталы и first wick raid + подтверждение соседним закрытым часом**, уже исследованные в original native3m C37 (и C20B), и сохраняет независимые 3M и 5M Route C из оригинального C45 учебного текста.

**Важно:** C37 содержит четыре АДАПТИРОВАННЫХ способа выбора 3m Swing/BOS; он **НЕ содержит авторских размеченных правильных сделок**. Отдельный 5m Route C нельзя считать выполненным по 3m оригинальным барам; далее нужен отдельный original native5m causal scan (ранее 5m источники C20 доступны, но C55 не сопоставлял их по этому маршруту).

## Реализованное ядро контроля

`d05/c55_crypto_1h_liquidity_raid_3m_bos_route_c_guard.py` проверяет исходный frozen C37 типизированный `AdaptedClosedBreak` и **временную последовательность**:

1. 1H фрактал BSL/SSL из центра должен быть подтверждён следующим полностью закрытым 1H баром — известен после `center + 2H`. ПЕРВОЕ строгое пробитие уровня рейдом не может предшествовать известности pivot.
2. Рейд по теням BSL/SSL `raid_first_breach_ms` известен только после его **следующего 1H подтверждения** `raid_confirmed_ms = raid_start + 2H`. Нельзя использовать незакрытый час или объявлять wick-событие исполненным ордером.
3. SHORT только после BSL, LONG только после SSL. Для BSL техническая геометрия: `wick extreme > liquidity level > bearish swing level > break close`; для SSL зеркально.
4. Структурный **исследовательский** Swing на оригинальных закрытых 3m имеет центр+следующий бар; `swing_confirmed_ms=center+2×3m`, и весь swing подтверждён **до START BOS 3m свечи**. Сам 3m breakout можно узнать только в **CLOSE BOS bar**, исходный `sha256:raw3m_start_ms` сохраняется точно.
5. Источник original3m raw-ID **может менять ZIP SHA на архивных границах** (исправление C54); не вводить ложное правило «каждый исходный 3m с одним ZIP sha». ID+timestamp и изначально pinned C37 защищены вместе.
6. Два разных course route состояния: `C_1H_RAID_3M_BOS` — `ADAPTED_1H_WICK_RAID_TO_CLOSED_3M_BREAK_NOT_AUTHOR_BOS`, а `C_1H_RAID_5M_BOS` — `NATIVE5M_SOURCE_MUST_BE_EVALUATED_SEPARATELY_NOT_BORROWED_FROM_3M`. **0 author-approved** для обоих. В исходный C45 курс не вносить правок.

`d05/test_c55_crypto_1h_liquidity_raid_3m_bos_route_c_guard.py` — **31/31** независимых отрицательных и source-корректных тестов × Python 3.10, 3.11, 3.12; проверяет направление BSL/SSL, подделки биржи, версионного source, незакрытые 1H/3m, swing-confirmed после BOS начала, фиктивные 5m ордера, forged author BOS, FX URL и неизвестные raw3m IDs. [CI 40193471942](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40193471942) PASS 3/3.

## Перенос на оригинальные 45 архивов криптовалют

C55 `tests/probe_c55_original_crypto_route_c_1h_raid_3m_bos_from_c37.py` независимо читает **замороженный полный оригинальный C37** `evidence/c37/C37_ORIGINAL_FOUR_ADAPTED_NATIVE3M_BOS_EVENTS.json`, Git blob `e4b702e8c6cdc34f1c2475df73ef44ae1631fe56` (2 310 174 байта), исходные Binance USD-M 45ZIP, 76 800 original closed 3m, 15 360 Decimal-exact 15m. Для каждого исходного C37 события проверяется строгая причинная хронология 1H BSL/SSL → original3m selected Swing known → first closed original3m break. Второй route 5M маркируется не проверенным. Аналитические четыре C37 адаптации содержат:

| Отдельная гипотеза выбора Swing | Research source events |
|---|---:|
| `LATEST_CONFIRMED_V1` | **539** |
| `EARLIEST_CONFIRMED_V1` | **462** |
| `DEEP_RAID_SIDE_V1` | **412** |
| `NEAREST_RAID_SIDE_V1` | **511** |
| **Всего коррелированных альтернатив, НЕ независимых сделок** | **1 924** |

BSL source raids **866**, SSL source raids **1058**. Суммы считаются по четырём вариантам одной и той же истории; это **не четыре портфеля, не частота успешных сделок, не win rate**. Повторно использовать один и тот же original3m BOS бар для нескольких raid contexts допустимо только в SOURCE счётчике, не в независимых трейдах. **Ноль** author BOS/academic liquidity validity/StrongHL/SL-TP/filled orders, PnL.

Первое original source freeze: [CI 40193558668](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40193558668) **SUCCESS**, весь C55 source JSON `evidence/c55/C55_ORIGINAL_45ZIP_ROUTE_C_1H_RAID_3M_BOS_4ADAPTED_SOURCE.json` **2 045 882 байта**, Git blob `2b4f944ddbdff0871a7fd553de2ab9955d220b91`, SHA256 `9f9939603a3d4b4e9b7cb8569727a6013aaa06ee94d9f151a6c4d7acbb95924b`.

## Независимая оригинальная перепроверка и критерии окончательной приёмки

[CI 40193652733](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40193652733) запущен отдельный **полный re-download всех 45 original Binance USD-M ZIP** с replay прежнего C37 2 310 174-байтного JSON, сравнением всего исходного C37 побайтно, затем полным независимым повтором всех 1 924 C55 событий и сравнением **всех 2 045 882 байт** C55 JSON. Три независимых Python jobs заново проверяют A123 123/123 и 31 тест × 3 версии. Только после SUCCESS сохранить independent witness, append-once A124 шести SHA evidence, независимый 124/124 журнал. Если оригинальный source replay провалится, C55 оставить [~] и рассмотреть ошибку как новое возможное опровержение.

**Следующий C56:** построить независимый Route C native5m из ОРИГИНАЛЬНЫХ crypto 5m свечей (не переклеить 3m), исходный 1H liquidity BSL/SSL, только закрытые свечи, C20/C09 source 5m фрактал и swing, структурное совпадение/различие BOS 3m/5m по одним родительским 1H raids; отдельно Route B IDM и Route A 15m VC. Сохранить все оригинальные 2026 BTC ETH SOL XRP BCH crypto source архивы и отсутствие lookahead.
