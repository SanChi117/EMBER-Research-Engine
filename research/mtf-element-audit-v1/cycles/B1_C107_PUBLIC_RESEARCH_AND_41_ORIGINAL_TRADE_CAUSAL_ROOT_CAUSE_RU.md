# EMBER C107 — ГЛУБОКОЕ РАССЛЕДОВАНИЕ: почему технически корректные 4H-сетапы не имеют устойчивого преимущества
**Дата:** 2026-10-30. **Статус:** доказанная семантическая несогласованность + проверенные рыночные аномалии; **это НЕ доказанная прибыльная стратегия и НЕ live-ready**. PAPER ONLY. Пользователь просил изучить GitHub, форумы, интернет и учебные правила, не добавляя ненужных чужих элементов.

## 0. Способ отличать факты от гипотез
- **КОД-ДОКАЗАНО:** воспроизведено по исходным строкам EMBER C105/C91, зафиксированным SHA, негативными синтетическими тестами.
- **ОРИГИНАЛЬНЫЕ ДАННЫЕ-ДОКАЗАНО:** повторно считаны **640 оригинальных Binance USD-M daily native3m ZIP**, каждый CHECKSUM, ZIP SHA+CSV SHA; **307200** свечей исходных 20 coin×32d 26.09–27.10.2026; форензика **41/41** старых PAPER сделок на их исходных трассах, без каких-либо новых сигналов.
- **ВНЕШНИЙ ЭТАЛОН:** сравнение с иной реализацией SMC, исходным LuxAlgo 848 строк, первичной документацией TradingView и Backtrader, с указанием, что SMC не имеет одной всеми утверждённой реализации.
- **ГИПОТЕЗА/НЕ ДОКАЗАНО:** что конкретное исправление даст лучшую устойчивую доходность. Никаких попыток подогнать параметры на 41 уже увиденной сделке; всё только исследовательская диагностика.

## 1. Итог по реальным исходным 41 сделкам — НЕ выдуманные метрики

| Доказательство | C105 /25 | C106 /16 | Всего /41 |
|---|---:|---:|---:|
| Стоп на native3m wick/gap | 15 | 10 | **25** |
| **Из стопов: 4H candle CLOSED, но 4H FVG ещё валидна** по исходному C105 close rule | **7/15** | **5/10** | **12/25 =48%** |
| Из стопов: 4H parent действительно инвалидирован 4H закрытием | 8/15 | 5/10 | 13/25 |
| Исходный 4H TP был впоследствии достигнут после реального стопа в первоначальные 48h (посмертное наблюдение, НЕ результат сделки) | 2/15 | 6/10 | **8/25 =32%** |
| 15m VC "SNR" (закрытие за high/low непосредственно предыдущей 15m свечи, **не structural BOS**) | 22/25 | 14/16 | **36/41 =87.8%** |
| 15m VC "IMB" | 3/25 | 2/16 | 5/41 |
| 1H rejection закрылась **внутри** родительской 4H FVG (вместо гарантированного ухода за всю зону) | 9/25 | 6/16 | **15/41 =36.6%** |
| Native3m entry оказался **за ближним краем** родительской 4H зоны, уже вне POI | 16/25 | 10/16 | **26/41 =63.4%** |
| 4H FVG middle candle неправильной стороны среди принятых trades | 0 | 0 | **0/41** |

**Важное отрицательное доказательство:** упрощённая C105 _fvg действительно может синтетически принять gap с неправильным направлением центральной свечи, но **в этих 41 состоявшихся сделках такого нет**. Не называть причиной наблюдаемых убытков отсутствие middle-direction gate; нельзя задним числом заявлять «исправление FVG импульсом улучшит 41 сделку» без нового неподсмотренного теста.

**H1 (12/25)** показывает расхождение *критериев*: C105 жизненный цикл считает 4H POI сломанной только если **CLOSE целой 4H свечи** пересекает дальний край, а paper-stop ставится 0.15×ATR4H за этим краем и срабатывает на **любой 3m LOW/HIGH**. 12 оригинальных 4H свечей с этим стопом потом **закрылись обратно на валидной стороне**. Это *не значит*, что стоп нужно держать до закрытия 4H! По 4H close alone риск станет немоделируемым/возможно гораздо больше, особенно на криптофьючерсах. Нужно выбрать согласованные структурную инвалидизацию, допустимую глубину excursion и реальный защитный стоп как **одну заранее протестированную политику**, а не бесконечно держать стоп. Любая гипотеза более дальнего стопа обязана пересчитывать размер, ликвидацию и реальный 3m max adverse.

**H2 (36/41)**: frozen `c91._vc()` возвращает `SNR`, когда текущий 15m CLOSE > HIGH **ровно предыдущей 15m свечи** в LONG (SHORT зеркально). В функции **нет** подтверждённого swing high/low, нет истинного BOS/CHoCH price protected structure, нет liquidity raid, нет reclaim или displacement contract. Большая часть входов образуется на **таком слабом SNR**. Число не устанавливает, что именно 36 SNR «плохие» (поскольку и в winning есть SNR); но называть это market structural BOS недостоверно.

**H3 (15/41)**: frozen `p4.rejection()` требует touch 4H zone и H1 CLOSE > FVG midpoint и close>open (LONG), но фактически в 15 сделках H1 CLOSE находилось ещё **внутри** 4H gap. Это отражает работу по median, а не доказанный выход из родителя. По ICT CE midway может быть полезной линией; не всякое закрытие внутри зоны означает false setup, но **метка «1H подтвердил отбой» сильнее фактически проверяемого условия**.

**H4 (26/41)**: delayed 1H +15m -> next 3m OPEN зачастую уже **вне родительской FVG**. Это вход на продолжении отскока, не лимитка на тест parent POI. Близость к входу в 4H и соотношение стоп/TP существенно меняются, но пока не показано, сколько «поздних» входов объективно убыточны. Запрещена post hoc фильтрация по расстоянию на этом наборе.

**H5 (0/41 неправильных средних свечей)**: независимый GitHub Python `joshyattridge/smart-money-concepts/smc.py` требует middle bullish/bearish для трехбарного FVG; LuxAlgo позволяет авто-порог gap body strength/displacement. C105 `_fvg` только gap geometry. Это семантический пробел у кандидатов, но для принятых 41 **не исходная выявленная причина**.

**H6 Режим/экономика:** C105 25 сделок +5.544304R PF1.29141 при 25bps, C106 на других 10 тикерах за те же 32 суток 16 сделок **+0.024034R PF1.00201**; early C105 -6.186858R/13, early C106 -6.77985R/6, поздние отрезки лучше. Указание на зависимость от режима, **не обязательно техническая ошибка детектора**. Исторический coin-transfer ≠ future true OOS. 25bps и 40bps способны уничтожить маленькое торговое преимущество.

## 2. Что нашли в **материалах владельца** (выше по приоритету, чем случайный форум)

Исходный `research/mtf-element-audit-v1/d05/c83_owner_course_text_crosswalk.py` сохраняет конкретные текстовые требования:
- **POI_STRENGTH**: «Сильна POI - це та, яка працювала з ліквідністю [SSL, BSL] або FVG». C105 считает **все** разрешённые 4H FVG родительскими зонами при упрощённом W/D контексте, не устанавливая связь с целевым SSL/BSL работой.
- **1H_PARENT**: «1H POI завжди має бути створена в контексті тесту та реакції від 4H POI». В C105 есть H1 candle rejection, но нет полноценного 1H дочернего POI с own creation, first test and chronology. Следовательно, **проверка реакции H1 не равна выполнению авторского 1H_PARENT**.
- **1H_FIRST_TEST**: «Щоб ввійти в позицію у нас обовʼязково має бути ТЕСТ цього 1H POI». C105 не создаёт 1H POI, поэтому не может проверять её **первое** тестирование.
- **NO_TRIGGER_DIRECT_15M_VC**: «При відсутності 15M Trigger → очікується на 15M VC [IMB, SNR]». C105 `_vc` смешивает контекст и VC без проверки полного parent/child trigger source.
- **RB_RAID_OR_IMB**: «RB обоʼязково має знімати ліквідність, або перекривати POI у вигляді IMB». C105 1H rejection не проверяет raid либо IMB/RB.
- `ACADEMIC_SOURCE_TO_CODE_TO_TEST.md` ещё раньше честно отмечал «NO DIRECT COURSE-LABELED TEST», «NOT_ACADEMICALLY_APPROVED» по ключевым semantic predicates и отсутствие золотых авторских свечных отметок.

**Это главное: наш C105 является причинно корректной упрощённой 4H→1H→15m цепочкой, но НЕ реализацией необходимых авторских formation semantics.** Была заменена часть реальных переходов (родитель→дочерняя POI→первый тест→правильный VC/raid) простыми пересечениями/свечами. Техническая корректность timestamp или 2070 зелёных тестов доказывает, что **неверная адаптация стабильно повторяется**, а не что формации адекватны реальному рынку.

**Но** не копировать все академические элементы вслепую: пользователь просил стабильный самостоятельный криптомеханизм, не точную реконструкцию курса. Только необходимое, с отдельной доказываемой полезностью и реальным bounded OOS.

## 3. Проверенные внешние источники, релевантные именно дефекту

**Первоисточники и открытые механизмы (higher confidence):**
1. [LuxAlgo Smart Money Concepts — оригинальный публичный TradingView индикатор](https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/) — структурные swing/internal BOS/CHoCH, mitigation, order blocks, ликвидность; авторы **не гарантируют** подтверждённую институциональную ликвидность/статистическую валидность. Пользовательский Pine 848 строк имеет `getCurrentStructure` (409–457), `displayStructure` (551–612), `drawFairValueGaps` (634–649), `deleteFairValueGaps` (625–630). **Права CC BY-NC-SA 4.0**, код не переносился.
2. [GitHub joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts) и [точный smc.py](https://github.com/joshyattridge/smart-money-concepts/blob/master/smartmoneyconcepts/smc.py) — FVG требует 3-bar wick gap **+ middle direction**, есть разные `join_consecutive`, mitigation index; swing highs/lows имеют explicit window, BOS/CHoCH != break of immediately preceding single bar; `close_break` distinguishes close vs high/low break. Известный риск Python batch implementation: использование `shift(-1)` / pivot context без `available_at` может дать визуальную метку на прошлом баре, если не построить отдельное execution-time clock.
3. [TradingView official repainting](https://www.tradingview.com/pine-script-docs/concepts/repainting/) и [TradingView confirmed MTF docs](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) — `security(HTF, high[0]/low[0], lookahead_on)` can leak future historical prices; require fully closed HTF values or [1]+lookahead_on. Наш C105 собственной агрегацией по original 3m **этой конкретной Pine ошибки не наследует**. Нельзя смешивать недостаток чужого LuxAlgo с найденным дефектом EMBER.
4. [TradingView Bar Magnifier official](https://www.tradingview.com/support/solutions/43000669285-what-is-bar-magnifier-backtesting-mode/) и [Backtrader execution documentation](https://www.backtrader.com/docu/order-creation-execution/order-creation-execution/) — OHLC alone doesn't reveal intrabar order, next-open after bar-close needed; native3m лучше H4-only, но отсутствие tick orderbook/bid-ask всё ещё препятствует реальной проверке fills, stop slippage/liquidations.

**Практики / обучающие базы (меньший уровень доказательства):**
5. [ICT FVG context and first presented gap](https://quartersequence.com/the-study/ict-fair-value-gap/) — различать 3-wick gap, displacement, liquidity sweep context, partial/full mitigation, не каждая FVG обязательна к торговле.
6. [FVG CE and body vs wick invalidation](https://www.thedtterminal.com/academy/ict-fair-value-gaps) — CE 50%, body beyond far edge as failure; интерпретация школы ICT, **не universal law**.
7. [GitHub ICT knowledge library FVG mitigation](https://github.com/SrsBlack/ict-knowledge-library/blob/master/concepts/06-fair-value-gaps/fvg-mitigation.md) — "fresh/partial/mitigated" разные состояния; правило порога должно быть однозначным и предзадекларированным.
8. [Reddit practitioner CE discussion (31 Jan 2026)](https://www.reddit.com/r/InnerCircleTraders/comments/1qrqbtm/i_have_question_fvg_validity/) — мнения, не доказательство вероятности; реальное несогласие авторов об уровне wick/CE/body invalidation.
9. [Academic Zarrabi — 7650 technical FX rules & false discovery/rolling OOS](https://repository.essex.ac.uk/18805/1/1-s2.0-S1057521916301958-main.pdf) — technical edge can occur temporarily but not persist when OOS/cost and multiple testing considered; **не исследование EMBER/crypto**, используется только как methodological warning.
10. [Hudson & Urquhart — Technical Trading and Cryptocurrencies](https://centaur.reading.ac.uk/85715/8/Hudson-Urquhart2019_Article_TechnicalTradingAndCryptocurre.pdf) — evidence out-of-sample effects can diverge across crypto; **not proof of SMC**.
11. [GitHub independent TS SMC implementation](https://github.com/gabrielkoerich/smart-money-concepts) — множество фильтров, включая fresh OB, COSD, volume, classification; **не переносить** их в EMBER без конкретной причинной необходимости. Complexity increases data snooping.

## 4. РАНЖИРОВАННЫЙ ВЕРДИКТ

**№1 — подтверждённая СЕМАНТИЧЕСКАЯ ПОДМЕНА:** «4H FVG к любому 1H H1 midpoint rejection к 15m close выше предыдущей свечи» не равно полной требуемой «4H POI + подтверждённая реакция/ликвидность + дочерняя 1H POI first test + релевантная 15m VC»; это явный пропуск/упрощение, а не точная реализация. **36/41 входов через weak previous-bar SNR**. Причину экономической разницы нельзя свести к одной цифре без более длинного frozen OOS.
**№2 — доказанная ВНУТРЕННЯЯ НЕСОГЛАСОВАННОСТЬ РИСКА:** **12/25** реальных native3m стопов при сохранении C105 4H parent на close того же 4H бара. Stop may still be legitimate protective exit; нельзя механически заменить на 4H close.
**№3 — НЕПОЛНОТА СЕМАНТИКИ ЗОНЫ и ИДЕНТИЧНОСТИ ЦЕЛИ:** C105 рассчитывает TP по nearest unswept 4H pivot, но не доказывает, что он относится к тому же 4H dealing range/parent structure; SL за дальним FVG краем не обязательно соответствует защищённому StrongHL 4H. Оба источника *4H по timeframe*, но не обязательно *структурная одна идея*. Это пока code-level conceptual deficiency, не количественно подтверждённая причина.
**№4 — 1H reaction/entry chase:** 15/41 inside gap after H1, 26/41 already outside gap at entry. Из контекста ликвидности не следует автоматически продолжение.
**№5 — рыночный режим и транзакционные издержки:** только 32 дня, n41, early/late разошлись, PF40 у C106<1, в целом edge пока не доказан.
**Опровергнутая гипотеза именно для 41 сделок:** middle 4H FVG direction wrong — 0/41.

## 5. ТЕХНИЧЕСКИ ОБОСНОВАННЫЙ следующий этап, БЕЗ наворотов
**C108: не добавлять индикаторы; восстановить единый контракт всего сетапа на языке уже известных формаций.**
- Определить явное 4H parent POI: **созданная, ещё действующая, на правильной стороне 1D/1W/4H структуры**, со state `created/first_test/invalidated` и `reason`.
- На существующем 1H уровне проверить **реакцию на эту 4H POI** и минимальную *не фиктивную* структуру (protected H/L; требуемый first test H1 child если он часть выбранной модели). Не называть простой candle midpoint «подтверждённым разворотом»; если научно обоснованная проверка отсутствует, пометить `UNVERIFIED`.
- Разделить 15m genuine swing BOS/VC от простого prev-candle-high SNR **только в рамках требований существующего 15m VC**, не добавлять весь LuxAlgo BOS + OB + EQH zoo.
- Привязать **SL к 4H структурной отмене**, TP к **4H уровню того же dealing range/противоположной стороне структуры**. Защитный stop должен быть executable intrabar, а валидность зоны — отдельное правило; сразу определить, где `setup invalidated` и где `risk stop`, с отдельными последствиями. Запретивать расширение SL post-entry.
- До запуска C108 экономического сравнения preregister new chronological future post-Oct27 data/window + missing fees and 40bps + guardrail; не выбирать лучшую по уже вскрытым 41.
- Сохранить original C105/C106 unchanged witnesses и не активировать live. Никаких обещаний стабильного профита.

## 6. Артефакты аудита
- Precommit `cycles/B1_C107_PRECOMMIT_CAUSAL_ROOT_CAUSE_FORENSIC_RU.md`
- Source-only script `d05/c107_original_p4_false_signal_forensics.py` и 20 independent negative tests `d05/test_c107_rootcause_original_source_semantics.py`
- **640 provider SHA+CSV archive evidence** `evidence/c107/C107_ORIGINAL_NATIVE3M_20COIN_STRUCTURE_RECLAIM_DIAGNOSTIC.json` (**308924 bytes, SHA256 98adf5a7497f8a08feb7c035b12b9fb3a0ea23921cc7d0164b39fc8406bc4334**)
- Independent original 640 sources and 20 new +690 prior ×3 Python =2130 PASS [GitHub CI 40979878731](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40979878731) SUCCESS4/4. Technical workflow covers 25/41 stop1st, exact 4H-reclaim source and no new trade rules.
