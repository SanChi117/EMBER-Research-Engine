# C114 / PRECOMMIT — новое независимое семейство: имеет ли подтверждение 5m самостоятельную ценность после 4H POI?

Дата 2026-10-30. **Это не C109-фильтр и не попытка спасения C109.** Историческая разработка только PAPER; LIVE запрещён. Предыдущая C113 закрыта с отрицательным экономическим результатом и A176 SHA-журналом. Этот документ фиксируется **до доступа к двум новым периодам C114**.

## Исследуемая гипотеза (проверяемая, не аксиома)

Общая гипотеза пользователя: движение между значимыми 4H-зонами после подтверждённой реакции. Нужно отдельно проверить:
1. Есть ли вообще добавочная предсказательная ценность **подлинного 5m структурного CHoCH после first touch 4H POI**, если сравнить с сопоставимыми первым касанием той же структуры БЕЗ CHoCH?
2. Не объясняется ли наблюдаемая разница выбором уже успешных/выживших событий, направлением 1D или расстоянием от цены до 4H target?
3. Увеличивается ли **экономический** netR после издержек 25/40bps, если и подтверждённые, и контрольные события исполняются с одинаковой геометрией 4H?

Финальное решение зависит от двух заранее скрытых периодов. Результаты C109–C113 использовать только как *запрет на переподбор*, не как параметры данной модели.

## Causal source contracts

- **1D**: отчёт о подтверждённой 2L2R swing structure/HH-HL/LH-LL, known only after right-side confirmation; **не gating**, поскольку конкретный импульсный фильтр C111 уже провалился. В дальнейшем можно сформулировать отдельную гипотезу, но не на данных C114.
- **4H**: первичная семейная POI = три закрытые 4H свечи, подлинная FVG (такой source-contract есть в EMBER). Только **первое** физическое касание по оригинальным 3m low/high, не более 48h после формирования, точное появление и родительский ID. Dealing Range от **двух уже подтверждённых 4H противоположных swing extremes 2L2R**; Premium/Discount относительно середины диапазона = заранее известные стратификационные признаки, **не отбор выигрышных сделок**. Если актуальной подтверждённой пары swing нет, категория NO_RANGE и не подставлять произвольный high/low.
- **OB/SNR/Liquidity Pools**: пока не включать в C114. Для них нужны собственные семантические source-contract, as-of, lifecycle и негативные тесты. Запрет выдавать произвольную свечу за OB или pivot за зону.
- **5m**: использовать **ORIGINAL native5m Binance ZIP, независимый от original native3m**. Нельзя пересобирать 5m свечи из 3m с округлением: разбиение не кратно. CHoCH LONG только когда до first touch наблюдалась локальная подтверждённая 5m понижательная структура (две подтверждённые 2L2R pivot-вершины и две впадины в последовательности LH/LL), а затем **полностью закрытая 5m candle CLOSE выше последней известной swing high**, при бычьем теле; SHORT зеркально. Pivot должен иметь confirmed_timestamp **строго до close пробойной 5m**. Последовательность после first-touch, окно максимум 6h. Нет подтверждённой предшествующей структуры => NO_CHoCH_STRUCTURAL_SOURCE, не превращать каждый wick в CHoCH.
- **15m**: в C114 stage-1 не придумывать 15m OB/FVG после наблюдения outcomes. Роль 15m execution требует отдельной регистрации **после** проверки независимого значения CHoCH. Stage-1 entry в обеих группах совпадает по времени, чтобы убрать временную фору от ожидания подтверждения.

## Общий LANDMARK, чтобы убрать immortal-time / postselection bias

Для каждого 4H first-touch событие зарегистрировать заранее t0. Общий LANDMARK = t0+6h для BOTH groups (строго close-aligned 3m).
- Treatment (T): CHoCH, закрытый по описанным правилам в [t0,t0+6h].
- Control (C): к этому общему timestamp нет подобного CHoCH; никогда не использовать будущие свечи, чтобы объявить контроль.
- Любой stop/TP/4H invalidation до landmark = **EARLY_COMPETING_EVENT**, событие остаётся в intention-to-treat denominator; нельзя выбросить не дожившие до подтверждения.
- Основное сравнение future-first-passage делается на выживших **в обеих** группах **только от одинакового 6h landmark** и обязано сопровождаться полным исходным ITT outcome, числом early failures, source-not-known и количественным анализом selection bias.
- Никакого утверждения причинности из одной корреляции: CHoCH не рандомизирован; control matching только снижает смешение наблюдаемых факторов.

## Paired controls and price geometry

До наблюдения будущих исходов каждая T matched к C той же монеты, того же календарного месяца, того же направления POI и категории известного на t0 Premium/Discount/NO_RANGE; матчи с известной на landmark ценой относительно 4H SL/TP и 4H ATR risk bins: [0.2%,1%), [1%,3%), [3%,10%]. Matching **without replacement**, tie break earliest timestamp, then stable parent-ID. Если matches нет => UNMATCHED (учесть в denominator). Никаких моделей propensity fit на новых outcomes.

Common execution diagnostic for both T/C: next original 3m open at landmark (только после закрытия всех 5m подтверждений); physical 4H parent far-edge SL +/-0.15 already closed ATR14 H4, TP прежний ближайший fully preconfirmed unswept 4H FTA pivot +/-0.15ATR. На t=landmark проверять same-side and derived RR>=1.25, risk 0.2–10%; неадмиссимый исход = 0R на ITT уровне, не исключать только контроль. Горизонт 48h, stop-first ambiguous native3m, fees+slip14/25/40bps. Fixed-RR TP не используется.

Основной outcome: первая физическая реализация 4H TP-before-4H SL за 48h после common landmark плюс netR25/40 и PF. Вторичный outcome: сырое касание preknown nearest opposing 4H FVG near edge (только наблюдение, не приравнивать к fill). Report independently ITT, survivors, matched, unmatched, per symbol, first vs second 28day fold, time to event.

## НОВЫЕ источниковые интервалы — ещё не были доступны C109–C113

56 полных дней на каждое окно, одинаковые 12 USDT монет из C109:
- WIN_A: 2025-01-01T00:00:00Z .. 2025-02-26T00:00:00Z exclusive.
- WIN_B: 2026-02-01T00:00:00Z .. 2026-03-29T00:00:00Z exclusive.

При фиксированном списке 12 монет: **1344 оригинальных дневных ZIP native3m (645120 строк)** и **1344 оригинальных дневных ZIP native5m (387072 строки)**. Всего 2688 ZIP с индивидуальной provider .CHECKSUM и SHA ZIP/CSV; original 5m 288 свечей/день. Контроль хронологии: обе серии без пропусков/дублей, согласованы только по реальным UTC timestamp. 7 дней warmup, terminal 48h embargo для доступности полного 48h post-landmark horizon (+6h), stage 1 endpoints. При отсутствии хотя бы одного исходника SOURCE_BLOCKED, никаких подмен, сдвигов периода и fake OK.

## Predeclared gate: строго два окна, binary PASS/FAIL/NO_POWER

Каждое окно должно иметь минимум 40 matched T/C пар, минимум по 10 matched пар в каждой половине (time-fold), а также опубликованные доли T/C/early/unmatched. В обеих независимых выборках:
- T netR25 >0, PF25>1.2 и PF40>1.1.
- T minus matched C average netR25 **строго больше нуля**; нижняя граница 95% интервала block-bootstrap по symbol-week **выше 0**; bootstrap seeds/partition frozen before quote reading.
- вероятность TP-before-SL у T выше C, с тем же направлением эффекта в ранней/поздней половинах обеих выборок.
- 1% starting-equity risk per fill conservative multi-symbol portfolio DD under 10% и funding/latency gaps explicitly reported.
- Экономическое улучшение нельзя обосновать только выкидыванием пропущенных T или C / matched pair survivor cohort.

Если мало matched pair => NO_POWER, **не ослаблять** CHoCH, не переходить на любой 5m wick ради n. При отрицательном эффекте/провале условия => FAIL, не допускать к PAPER автоматизированному отбору. Даже при полном историческом PASS — только независимый prospective forward PAPER и отдельно проверка 15m execution, LIVE по умолчанию запрещён.

## Неизменяемые технические решения до начала чтения C114-источников

- Block bootstrap: 2000 replicates, deterministic RNG seed 11420261030, whole matched-pair symbol+ISO-week blocks, 2.5% percentile lower bound; one resample unit is all paired observations grouped by the treatment pair's symbol-week, not an individual trade.
- t0 is close/known_ms of the first native3m candle whose wick first intersects the previously fully closed 4H FVG. It is UTC 3m aligned, and t0+6h is also exact 3m open. Native5m is read only at close_ms <= t0+6h. No 5m construction from 3m.
- Treatment's local pre-touch bearish/bullish regime requires the two most recently **confirmed** 5m highs and lows (2L2R each) as of t0, strictly descending for LONG or ascending for SHORT. Freeze the most recent confirmed opposite swing price as the breach level at t0; do not relabel mid-window. CHoCH must occur after t0 and be a first directional close crossing that frozen swing.
- early competing geometry is a frozen stop and nearest preconfirmed 4H FTA calculated from the first touch **at t0**, not future geometry. A lacking t0 preconfirmed FTA is marked EARLY_TARGET_UNKNOWN (not a fabricated hit).
- Matching ratio-to-FTA bins are frozen as [1.25R,2R), [2R,4R), [4R,infinity); they are an additional as-of landmark matching key alongside frozen risk bins. They are not additional entry gates and are NOT tuned to observed outcomes.
- A 5m candle starting before a t0 close on a 3m boundary is not a fully post-touch CHoCH candle. Qualifying 5m breach must have original open_ms >= t0 AND known close_ms <= t0+6h, without 3m->5m synthesis.
- Matching risk bins and price relative to stop/target are computed on post-landmark known 3m opening price, while matching and evaluation use zero future outcomes.
- t0 before first-week warmup excluded only by frozen time gate. Common landmark must leave a full 48h future horizon before window end. No market data may be used to reduce these windows.
- C114 trial will be marked **NOT_GENUINE_UNSEEN** if period overlap with any earlier accessed C109–C113 test inputs is established, even though period dates were fixed before this cycle.

## Очередь реализации

1. C114-A: source-contract tests: native5m cannot be derived from native3m, fully closed H4/P5 pivots, negative lookahead, timestamp alignment, no false CHoCH and no immortal-time/postselection.
2. C114-B: causal POI/5m event ledger + matched 6h landmark risk geometry, 14/25/40bps and portfolio control.
3. C114-C: frozen CI original 2688 provider ZIP + attribution, paired source SHA manifests and blind binary decision.
4. C114-D: append A177 journal with countercheck ONLY after genuine execution, not this precommit.

Результат **пока не получен**. Этот документ — строгая программа нового независимого эксперимента, а не доказательство прибыльности.
