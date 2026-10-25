# B1/C61 — комплексная академическая цепь 1D/4H → typed POI → первый допустимый тест → VC/BOS → Strong High/Low (RESEARCH ONLY)

**Дата:** 25.10.2026 UTC. **Криптовалюты:** BTC, ETH, SOL, XRP, BCH (USDT-M Futures). **Выполнение заявок: ЗАПРЕЩЕНО / PAPER ONLY / NOT_TRADE_READY**. C61 завершает этап восстановления текстовых предусловий и независимой проверки *исходного* криптоконтекста, но **НЕ утверждает** готовность академических авторских POI/StrongHL/входов.

## 1. Источники — первичные уроки, заново прочитанные на Google Диске

| Название | Drive ID | Подтверждённая семантика |
|---|---|---|
| POI.txt | `1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R` | Зоны спроса/предложения. Сильная POI работала с BSL/SSL либо FVG. |
| 3. Rejection Block.txt | `1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT` | RB — реакция двух противоположных свечей с обязательным снятием ликвидности или перекрытием IMB, с нюансом теней и закрепления. Пара свечей сама по себе **не** author RB. |
| Order Flow.txt | `1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN` | OF = структура + ликвидность + работа с POI/IMB. Для StrongHL нужна работа с ликвидностью и подтверждение движения. |
| Strong High & Low.txt | `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t` | Контакт с ликвидностью либо неэффективностью, затем подтверждение движения через VC POI либо BOS. Bare pivot недостаточен. |
| Fair Value Gap Imbalance.txt | `1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN` | Настоящий первый тест POI выделяется отдельно, повторы могут формировать пул ликвидности. |
| 2. Entry by IMB & SNR.txt | `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ` | Контекст Daily POI/Liquidity → 4H VC, 4H тест → 1H trigger → 15m VC, IMB внутри 4H IMB не становится 1H IMB trigger. |
| 3. Entry by Inducement [IDM].txt | `19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs` | Route B лимит на IDM может выставляться **без последующего теста POI**, но родительский VC и StrongHL должны уже существовать к моменту планирования лимита. |
| PDPWPM High&Low. Session Liquidity.txt | `1HqGlqYUZptdNvOVLBHftx03XYASvo9MZ` | PDH/PDL/PWH/PWL и прочие прошлые high/low = ликвидность/возможные цели, **не автоматически selected POI**. |

**Граница источников:** В текстах отсутствуют полностью машиночитаемые **криптовалютные** author-labelled кейсы с символом, timestamp, raw candle-ID, выбранным POI, подтверждённым StrongHL/SL/TP/FTA и исходом. Не подменяли их рисунками EURUSD, одиночными техническими свечами или постфактум выгодными источниками.

## 2. Комплексная конструкция C61

- [x] `d05/c61_academic_poi_context_first_valid_stronghl_contract.py`: независимый академический предикат `academic_poi_lifecycle_contract`, типы POI: IMB/SNR/RB/Liquidity; источник HTF, first valid test, контакт ликвидности/неэффективности, ПОСЛЕДУЮЩИЙ closed VC POI/BOS, StrongHL. Авторское присвоение и исполнение запрещены. Положительный **синтетический** text-case никогда не даёт approved entry.
- [x] Отдельные 5 типов маршрутных текстовых контекстов для Route A 4H Trigger→15M VC, Route A без триггера→1H VC, Route B 4H VC→1H IDM, Route B 1H VC→15M IDM, Route C Raid→BOS. Эти проверки **не смешивают** конечный Route A VC с Route B прямым IDM. C61 не заменяет специализированные исходные механизмы Route C/B и не меняет SMOKE/V5/QFVG.
- [x] Дополнительный fail-closed порядок: даже прямой Route B IDM LIMIT нельзя планировать **до полного знания родительского VC**. В Route A/C подтверждение после контакта не может предшествовать первому контакту исходного контекста. Отдельный тест не допускает, чтобы последующие посещения ретроактивно изменяли статус исторического первого теста.
- [x] `last_closed_original_day_before_zone`: **подлинные** Binance USDT-M native1d SHA:row_start; берётся последняя **уже закрытая** дневная свеча строго не позже момента возникновения исходного 4H source POI. Отдельно проверено, что *физически урезанный до исходного 4H времени* 1D-префикс даёт **тот же** предыдущий закрытый бар и PDH/PDL, что и полный поток с ограничением as-of. В первую неполную доступную дату prior 1D = **MISSING**, не «догадка» и не будущая свеча.
- [x] `join_source_poi_context`: 153 исходных 4H source-кандидата склеиваются **по точным original Binance row-ID**, направлению, времени и границам сразу из **C46** (4H технический IMB/первое native3m касание), **C47** (последующий технический 1H IMB), **C59** (inside 1H-vs-4H veto), **C60** (первое/повторное посещение). Результат содержит контекстный prior original 1D, тип *технического* 4H кандидата, количество исходных визитов, 1H chronological source и полный перечень блокеров авторской семантики. Он НИКОГДА не повышает авторские статусы.
- [x] `d05/test_c61_academic_poi_context_first_valid_stronghl_contract.py` — **51** unit/negative test × Python 3.10/3.11/3.12, 153/153 SHA parent links проверены повторным исходным replay. Тесты false goldens/поддельные сделки, незакрытый native1d, NaN/неконсистентная 1D свеча, fake first contact, неверный parent, преждевременный BOS/VC и преждевременный IDM, RB без обязательной liquidity/IMB работы.

## 3. Реальные криптоданные / независимое повторение

- [x] Целиком ДВАЖДЫ скачаны **45 Binance USD-M ZIP + .CHECKSUM** (15 original native3m, 15 original native15m, 15 original native1d) по 5 символам за период 01.09–02.10.2026; позднее выполнены ещё два повторных replay с усиленными native1d physical-asof и chronology guards.
- [x] **76800** исходных native3m candle; **160** исходных закрытых native1d; **15360** exact Decimal native15m OHLCV паритетов. Каждый C46 original source parent повторно сравнен с замороженным C46 JSON полностью; C47/C59/C60 immutable Git blobs проверены неизменными.
- [x] Первый полный source [CI 40205429138](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40205429138) **SUCCESS**: 45 оригинальных Binance ZIP + 48×3 прежних negative tests, файл evidence/c61 заморожен.
- [x] Второй **независимый** original45 ZIP full JSON [CI 40205560855](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40205560855) **SUCCESS 4/4**, `cmp -s` всего исходного JSON и SHA256.
- [x] Усиленный third original45 ZIP [CI 40205832842](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40205832842) **SUCCESS**: physical native1d asof prefix и **51×3** тест, exact frozen JSON.
- [x] Усиленный fourth **независимый** original45 ZIP full-byte [CI 40205841182](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40205841182) **SUCCESS 4/4**, **51 тест × Python 3.10/3.11/3.12**, с полным совпадением **260561 bytes** SHA256 **00a99d9d31f551ed18fedc850fbd0da7fb2c50db6feedba41f920224f9857426**, Git blob **305624e592f55bd699e94e45f4316e4efabdb726**.
- [!] Промежуточная отрицательная CI **40205819439** FAIL: устаревшее ожидание `Ran 48 tests` после добавления 3 новых chronological adversarial тестов. CI обновлена на `Ran 51 tests` и повтор 40205826270 SUCCESS 3/3. Нельзя скрывать первый красный прогон.

## 4. Статистика — только source research, НЕ торговые сетапы

| Показатель | Значение |
|---|---:|
| Source 4H classic IMB кандидатов | **153** |
| Есть уже закрытая нативная 1D свеча к моменту 4H zone | **150** |
| Предыдущая дневная свеча ещё не была доступна | **3** |
| Original3m первый wick contact | **132** |
| После контакта technical 1H same-side IMB source | **130** |
| Только один observed source-visit | **5** |
| Повторные раздельные native3m wick-visits | **127** |
| Контекст first source отсутствует | **21** |
| Полностью внутри parent4H IMB: последующий 1H IMB Route A veto | **21** |
| Partial overlap: unresolved 1H source | **12** |
| 1H source вне 4H IMB (НЕ авторский триггер) | **97** |
| Оригинальных авторски подтверждённых first-valid tests, StrongHL, выполненных сделок | **0** |

Строки относятся к **разным измерениям тех же 153 зон**, не суммируются как независимые сделки и не дают вероятности успеха. PDH/PDL = информационные исходные high/low предыдущего дня, не реальные авторские Daily POI. Source «первый wick contact» не означает признанный автором first-valid test. Поздний 1H IMB без полного контекста **не** означает Volume Confirmation. Bare pivot не может стать StrongHL или стопом.

## 5. Финальная граница C61 и следующая работа

**Завершено:** академические предикаты и их защита от lookahead/ложной разметки, достоверный original 1D→4H→1H source-проход, хронология native3m first/revisit, сохранение A/B/C независимыми, тестовая 51×3 матрица, double independent original45ZIP, immutable evidence.

**Не выдавать за завершённое:** авторская распознавалка всех IMB/SNR/RB/Liquidity POI с авторски размеченными позитивными и негативными криптокейсами, StrongHL сертификация price-level, FTA/structural SL/TP, execution, OOS эффективность. Нужен отдельный механический и визуальный audit авторских timestamped примеров, иначе систематический ADAPTED статус обязателен.

После документального evidence freeze — append-once **A131**: ровно шесть evidence (module, 51 tests, original45ZIP probe, full C61 JSON, independent witness, current report). Проверить отдельной финальной CI **131/131 SHA × Python 3.10/3.11/3.12** и неизменные frozen C46/C47/C55/C56/C57/C58/C59/C60. Текущий accepted до A131 — **A130 tip `e649e975970f9e940e3bdc87b7c65a8ce363d2d5241226b2876e0c07dd788810`**.

**Следующий C62:** изолированно реализовать распознаватели BTC/ETH/SOL/XRP/BCH POI по полному курсу (SNR/RB/IMB + liquidity work), BOS contact→reaction with strict closed TF and strong extreme invalidation, валидацию маркированных рисунков/кейсов без домыслов. Только потом PAPER бэктест с fees/slippage, а не подгонка 32 дней. **NO ORDERS / NOT_TRADE_READY**.
