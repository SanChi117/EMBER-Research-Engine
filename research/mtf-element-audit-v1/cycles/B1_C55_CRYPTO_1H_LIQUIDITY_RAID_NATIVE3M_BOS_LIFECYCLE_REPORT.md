# B1/C55 — отдельный жизненный цикл 1H ликвидности → первый Raid → закрытый 3M BOS

**Дата:** 2026-10-25. **CRYPTO ONLY / PAPER ONLY / NOT_TRADE_READY.** Все курсовые рисунки — учебные правила, не price source. Ордера, сделки, PnL, профит и live-входы: 0.

## Важнейшее решение о структуре

C55 **не переписывает** ни 1H-фрактал C20B, ни базовую source-3m геометрию C21B. Вместо создания конкурирующих академических приближений добавлен **слой жизненного цикла** `d05/c55_crypto_1h_liquidity_raid_bos_lifecycle.py`. Он повторно использует оригинальные C20B `HourFractal / FirstWickObservation` и C21B `ThreeSwing / ThreeBreak / observe_native3m_raid_break`. Все действия ограничены исходной `C21Native3mResult` с проверкой original ZIP SHA, raw native3m идентификаторов, original15m exact Decimal и времени закрытия. Никакой Route A или Route B при этом не изменяется, и C54/A123 оригинальные данные остаются замороженными.

## Последовательность, которая должна быть причинно доказана

1. **1H liquidity level**: центр строгого 3×closed-1H фрактала BSL (high выше соседей) или SSL (low ниже соседей); уровень становится известен только после **закрытия правой 1H свечи**. Оригинальные 60 native3m ID трёх 1H свечей сохраняются.
2. **Первое снятие**: только первое касание/пробой границы уровня в закрытом 1H баре после того, как фрактал стал известен. First BODY breach отдельно останавливает этот first-only lifecycle; нельзя объявлять его чистым wick raid.
3. **Wick raid**: тень выше BSL / ниже SSL при теле без закрытия за ликвидностью; следующая полностью закрытая 1H свеча обязана подтвердить 1H фрактал экстремума, иначе событие остаётся неподтверждённым.
4. **3m swing**: исследовательский строгий 3-свечный native3m pivot, становится известен после закрытия правой свечи. Выбранный swing должен быть известен не позже начала свечи вероятного BOS.
5. **3m BOS**: только закрытый original native3m close впервые пересекает подходящий swing в ожидаемом направлении **после подтверждения 1H raid**. Если после подтверждения экстремум рейда снова снят до BOS, базовый C21B прекращает поиск; нельзя использовать результаты последовательности хвостов той же свечи как доказанные сделки.
6. Результат: **ТЕХНИЧЕСКАЯ адаптация**, не instructor verified BOS или full Route C entry, не возможность исполнить SL/TP, нет fill. Сохраняются исходный bar ID и earliest known-time.

Эти правила реализованы без подгонки под прибыль, на source-чтении ранее принятой математики C21B. Это не новое определение авторского BOS; авторские Positive/Negative chart-execution goldens пока отсутствуют.

## Шесть состояний жизненного цикла

| State | Что доказано источником |
|---|---|
| `LEVEL_PREKNOWN_NO_FIRST_BREACH` | Уровень известен, первого breach нет |
| `FIRST_BREACH_BODY_NOT_WICK_RAID` | Первый пробой телом — не wick-only raid |
| `FIRST_WICK_NEEDS_NEXT_CLOSED_1H` | Wick breach, но следующая 1H свеча ещё не закрылась |
| `FIRST_WICK_NONFRACTAL` | Wick breach был, но авторская геометрия 1H фрактала не подтверждена |
| `CONFIRMED_1H_RAID_NO_CLOSED_3M_BREAK` | 1H wick-fractal raid source подтверждён, более поздний строгий 3M close BOS не наблюдался |
| `CONFIRMED_1H_RAID_WITH_ADAPTED_3M_CLOSED_BREAK` | Закрытый источник 3M сделал адаптивный swing-break после 1H raid. **НЕ сигнал сделки** |

## Что конкретно проверено

`d05/test_c55_crypto_1h_liquidity_raid_bos_lifecycle.py`: **43 synthetic/source-negative проверок** × Python 3.10, 3.11, 3.12: future fractal, отсутствие raw bar ID, невалидная liquidity сторона, backdated first touch, отсутствие following 1H confirmation, fabricated premature BOS, swing известный только после BOS, BOS раньше raid, ошибочная цена, противоречивый side, нечестно заявленный author-certified status, попытки исполнения. [CI 40193572232](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40193572232) **SUCCESS 3/3**.

Независимый оригинальный полный источник `tests/probe_c55_original_crypto_1h_raid_3m_bos_45zip.py` повторно читает **45 исходных Binance USDT-M ZIP** из трёх классов 1d/15m/3m, 5 монет. Для C21B ранее независимо принято: **76 800** закрытых native3m; **3 840** закрытых 1H; **642** confirmed first 1H wick-fractal raid и **539** 3M research strict-close break links (это **связи с родительскими уровнями**, не уникальные сделки). Каждый из 5 символов дополнительно обязан подтвердить физически урезанный source-prefix Oct-2 00:09 UTC против полной исходной записи, перезапущенной `as_of` с той же границей. **До независимой проверки источника новые counts state нельзя объявлять принятыми**.

## Ограничения

- Проверенная 1H фрактальная геометрия **не равна** подтверждённому академическому Strong High/Low: выбор структурного ликвидного уровня курса ещё требуется.
- 3m BOS как строгий close-break последнего preknown pivot — **ADAPTED**, не instructor-labelled BOS; реальная академическая семантика рейда/BOS может потребовать дополнительных условий.
- C55 исследует **только native3m ветку** Route C. Исходный 5m вариант маршрута намеренно остаётся самостоятельным и не подменяется 3m баром или ресемплингом.
- Полная связь 4H POI, 1H liquidity / IDM / volume confirmation, structure SL/TP/FTA, комиссии, slippage, OOS и современный терминал ещё не оттестированы.
- **0 сделок, 0 прибыли, 0 авторских торговых goldens.**

Следующая работа: сначала первая независимая original45ZIP full source CI, затем отдельный 45ZIP полного источника побайтный repeat + SHA witness, append-once A124 и независимая 124/124 CI; далее C56 — отдельно 1H Level source selection / lifetime and 5m exact original Route C comparison, без вмешательства в A/B. Не выдавать source-only цикл за завершённую Route C торговую систему.


## Первый полный исходниковый цикл принят в заморозку (до независимой итоговой перепроверки)

[CI 40193694018](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40193694018) **SUCCESS**. Исходные пять символов BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT; все **45 архивов** исходной истории и checksum; новый C55 исходниковый frozen JSON **13 029 668 байт**, Git blob `f26ebde00fff15977e39b4b626fb8625c5fb7341`, SHA256 `63526354af9c450f0e659ab59c793987177a9b023ada69730726e6de10842411`. Сохранены сырые оригинальные ID баров каждого 1H уровня (60 native3m IDs), первого breach, подтверждения следующего 1H, известного 3m swing и закрытого 3m BOS.

| Первичный точный source-only исход | Число |
|---|---:|
| 1H уровень существует, первого снятия не наблюдалось | **131** |
| Первое снятие произошло **телом**, не wick-raid | **772** |
| Первое снятие тенью без подтверждения нужного 1H фрактала | **328** |
| Подтверждён 1H wick-fractal raid, но нет позднего 3m strict break | **103** |
| Подтверждён 1H wick-fractal raid и поздний закрытый 3m adapted swing-break | **539** |
| **Всего 1H уровней исходной крипто истории** | **1 873** |

В полном source-asof на конец периода не осталось уровня в `FIRST_WICK_NEEDS_NEXT_CLOSED_1H`. Для подтверждённых 1H raids: **103+539=642**, совпадает с принятым C21B 60ZIP parent evidence. Никакого академически доказанного BOS/учебной 2023 сделки/ордеров/PnL по-прежнему нет.

Отдельный независимый repeat [CI 40193879074](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40193879074) должен проверить **все 13 029 668 байт** C55 против нового полного source fresh download и 43 source-negative теста × 3 Python. До его успеха A124 не добавлять, прежнюю SHA цепочку не менять.
