# B1/C66 — оригинальные криптосвечи: 4H POI source → 1H context → 15m native IMB/SNR source; разделённые ветки Route A

**UTC:** 25.10.2026. **Repo:** `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`. **CRYPTO ONLY, PAPER ONLY / NOT_TRADE_READY, no real/paper orders.**

## 1. Академический оригинал — важно НЕ подменять этапы

Перечитан пользовательский `2. Entry by IMB & SNR.txt` на Google Drive (ID `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ`). Он требует **разных** алгоритмических веток (не «любой 1H → любой 15m = вход»):

- **4H POI → 1H Trigger → 15M VC [IMB, SNR]**. Сначала обязателен **реальный тест** авторской 4H POI. Триггер 1H: **BSL, SSL или допустимый IMB**. Если IMB на 1H **полностью находится внутри 4H IMB**, его нельзя считать таким триггером. 15M после trigger должна дать настоящее **VC через IMB либо SNR**, а не просто любой 15m FVG; **RB не финальная точка входа**, хотя может быть контекстной POI/VC.
- **4H POI test или 4H liquidity raid → нет 1H Trigger → 1H VC [RB,SNR,IMB] создаёт НОВУЮ 1H POI**, с обязательным **первым настоящим тестом этой 1H POI**, затем 15M служит trigger, а 5m подтверждает VC [IMB,SNR], либо при отсутствии trigger рассматривается 15M VC. Это отдельное состояние от первой ветки, не доказанное просто наличием технической 1H свечной структуры.
- `3. Entry by Inducement [IDM].txt`, Drive ID `19SW5tv2CdeaYeP9jCO6WOCs5bpYSjVrs`: Route B IDM **не ждёт** дополнительного финального подтверждения Route A после ранее установленной родительской VC/StrongHL, и может находиться до/внутри POI. Маршрут B не подменять route A.
- `Order Flow.txt`, Drive ID `1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN`: настоящее подтверждение экстремумов VC POI/BOS должно опираться на работу с liquidity/inefficiency, source pivot/FVG/цена не сертифицированные автором StrongHL.

Это **реальные авторские текстовые правила**, изображения уроков объясняют **логику**: ни один screenshot не является размеченным Binance USD-M `symbol + UTC timestamp + candle original ZIP SHA ID + owner-selected POI + owner-approved VC/StrongHL` positive/negative golden. Их остаётся **0**. Поэтому C66 формирует лишь source-observations, НЕ переводит кандидатов в сделки и НЕ подменяет отсутствующий авторский 1H-branch выбор.

## 2. Изолированная C66 реализация

- [x] `d05/c66_native15m_route_a_source_event_chain.py` — отдельный источник оригинальных закрытых Binance **native15m** `NativeKline` с проверкой original SHA:timestamp ID, полного OHLCV, временной сетки, постоянного symbol/volume/целостности и `as_of`. Нет данных будущих свечей.
- [x] `15M_CLASSIC_IMB_SOURCE_ONLY`: строгий 3-bar gap **между тенями первой и третьей** 15m, событие возникает **только после закрытия третьей**; не считать автоматически авторской IMB POI/VC, не смешивать iFVG/BPR и другие IMB типы.
- [x] `15M_SNR_LIQUIDITY_SOURCE_ONLY`: две противоположные свечи, затем **третья закрытая свеча подтверждает закрытием за экстремумом пары** (консервативная ADAPTED версия авторского закрепления), был **строго заранее известный неснятый 15m фрактальный источник SSL/BSL**, с фактическим пересечением source pair. Bare 15m fractal НЕ StrongHL. Не путать SNR с RB.
- [x] `15M_SNR_PRIOR_IMB_SOURCE_ONLY`: такая же закрытая пара и закрытие, но фактический пересекающий **ТЕСТ** IMB, который был подтверждён раньше исходной 15m пары. Просто создание новой IMB не является тестом. Если нет liquidity/IMB work, это weaker MB и **НЕ VC**.
- [x] Optimized **preknown 15m liquidity schedule**: один линейный проход по уже закрытым original 15m для каждого из 5 криптоактивов; source unswept pivots подтверждены строго до первого бара пары; не просматривается весь будущий ряд для реанимации ликвидности. Исходный медленный алгоритм первого [CI 40216949092](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40216949092) и оптимизированный [CI 40217165803](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40217165803) дали **одинаковые побайтные original JSON**, без изменения frozen C46…C65. Физически обрезанный `native15m` prefix равен логическому as-of.
- [x] `route_a_15m_source_review` связывает **каждый** C46 native4h technical candidate → его первый C60 original native3m wick контакт → **первое ЛЮБОЕ** C63 closed 1H событие (включая противоположное и двунаправленную неопределённость) → затем **первое ЛЮБОЕ** техническое original15m событие [IMB,SNR] в фиксированном 24h source research окне. Оригинальное направление не подтягивается под «удачный» исход. Никакой технический 1H C63 event автоматически не объявляется **owner trigger** или **owner new VC POI with VALID first test**. Отдельные source-cases 4H opposite и 1H ambiguous исключаются из гипотетической продольной ветки; **ноль author final entries**.
- [x] Все Route B IDM и Route C 3m/5m raid→BOS **не затронуты** и не смешаны с A. Новый код не производит `SL, TP, FTA, order, fill, PnL`. Не изменены V5/QFVG, SMOKE и старые оригинальные C46–C65 code/evidence blobs.
- [x] `d05/test_c66_native15m_route_a_source_event_chain.py`: **33** synthetic adversarial теста × Python 3.10/3.11/3.12, примеры SNR liquidity vs SNR preknown IMB vs MB, wick-gap после только третьей свечи, raw SHA time fraud, original asof == physical source truncate, first ANY opposite 1H/15m, same-time ambiguity, future source, fake owner VC/order, incomplete 24h right censor. [CI 40216715427](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40216715427) SUCCESS 3/3; после оптимизации [CI 40217095249](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40217095249) SUCCESS 3/3; полный independent CI тесты снова ×3.

## 3. Дважды независимая проверка полного оригинального Binance USD-M источника

- [x] `tests/probe_c66_original45zip_4h1h_to_native15m_route_a_source.py` **ПОВТОРНО СКАЧАЛ** original 45 Binance USD-M SHA-checksum ZIP (BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT), 2026-09-01–2026-10-02: **76800** оригинальных закрытых native3m, **15360** оригинальных закрытых native15m, **160** оригинальных native1d, **3840** source-derived закрытых 1H. Каждый из **153** исходных 4H technical parent C46 заново восстановлен с первым C60 3m SHA-ID, C62 1H SNR/RB/IMB и C63 первым ANY, после чего добавлена source 15m хронология; исходные C46/C60/C62/C63 SHA Git blobs проверены неизменными.
- [x] Первоначальный [CI 40216949092](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40216949092) **SUCCESS 5/5** 45 ZIP + 33×3, freeze полного output. Оптимизация preknown schedule не изменяет результатов: [CI 40217165803](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40217165803) **SUCCESS 5/5**. Ещё один полностью независимый fresh signed original45ZIP + **полный BYTE EXACT cmp** [CI 40217312270](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40217312270) **SUCCESS 4/4**, повторный 33×3.
- [x] Заморожен **ПОЛНЫЙ** source event JSON `evidence/c66/C66_ORIGINAL45ZIP_4H1H_TO_NATIVE15M_SOURCE_FIRST_ANY_ROUTE_A.json` — **3 295 302 bytes**, SHA256 `23c6eaac7ebcd3f9cd447f9a3690da023d6fc30e50f03e48f57c5037bff15bd3`, Git blob `c693058cdb28b0e118879d32ddcbbd0d2a66bfc6`. Он содержит все original native15m source events, исходные candle-ID и source parent outcomes, не только агрегатные числа. Independent witness `evidence/c66/C66_INDEPENDENT_45ZIP_4H1H_NATIVE15M_ROUTE_A_WITNESS_20261025.json`.

## 4. Реальные числа — не сигналы

**Original native15m technical events, всего 4 771** на пяти монетах в указанных 32 днях (классы могут относиться к коррелирующим/перекрывающимся свечам):

| Технический SOURCE вид | Исходных наблюдений |
|---|---:|
| 3 fully closed native15m classic 3-wick IMB | **3048** |
| 3 closed native15m source SNR + previously known liquidity source test | **514** |
| 3 closed native15m source SNR + previously known IMB source test | **1209** |

**153 original 4H-кандидата** от C46, после восстановленной цепочки C60 → C63 → native15m:

| Истинный source outcome | Количество |
|---|---:|
| Отсутствует первое original3m касание технической 4H зоны | **21** |
| Первое последующее 1H source событие в ПРОТИВОПОЛОЖНОМ направлении | **61** |
| Первое последующее 1H source событие одновременно двух направлений | **7** |
| Есть source 1H событие в исходном направлении и **первое** 15m событие в том же направлении | **29** |
| Есть source 1H событие в исходном направлении и **первое** 15m событие ПРОТИВОПОЛОЖНО | **35** |
| В полной выборке другие source classes right censor/no 1H/no LTF | **0** |
| **Итого original технических 4H source parents** | **153** |

**ЭТО НЕ 29 А+ сетапов, НЕ 4771 сделок, НЕ winrate, НЕ готовые лимитки.** Классификация 1H source техническая и не определяет, где реально был авторский 1H Trigger и где новая VC POI с первым VALID retest; без этого owner Route A entry не подтверждён. 1H opposite/ambiguous не «исправлены» выбором другого направления; 15m opposite-first не фильтруется. Route B IDM не запускался.

## 5. Открытые семантические блокеры и C67 NEXT

**C66 source-only native15m timing/IMB/SNR работоспособен. Однако у нас 0 проверенных авторских crypto goldens** (OHLCV symbol+time+author POI label), 0 подтверждённых first VALID 4H/1H POI tests, 0 verified 1H BSL/SSL/IMB Trigger, 0 настоящих 1H VC new POI и последующего retest, 0 valid 15m VC, 0 StrongHL, 0 Route A/B/C конечных order signals, 0 FTA/SL/TP или бумажного PnL/OOS. **Нельзя засчитать это как торговую готовность.**

**C67 NEXT:** source + visual academic differentiation: `4H original POI test → 1H BSL/SSL/IMB trigger → 15M VC` **versus** `4H context / raid → 1H VC NEW POI → first VALID native3m/n15m 1H POI TEST → 15M trigger → 5m VC or 15M VC`. Preserve 1H IMB fully inside 4H IMB veto, correct RB/SNR/IMB and source liquidity raid preknown levels. Original course FX images examples cannot invent cryptocurrency candle labels; if author crypto case missing, keep **ADAPTED** / **NOT_TRADE_READY**. Route B IDM remains separate; route C raid→BOS remains separate. Then C68: true academic StrongHL and structural FTA/SL/TP before OOS PAPER and SMOKE integration.

## 6. SHA acceptance A136

Only after both independent original45ZIP and 33×3 negative tests: append **A136** with exactly six SHA evidence paths (C66 module; C66 33 tests; C66 fresh full original 45 ZIP script; full 3.295MB original crypto JSON; independent witness; THIS immutable report). Previous A135/135 tip `76014ca82efd4ddb4d40da272fd54b514310d370fce90a8ccb22064b9a6b6787`; keep A001–A135 and original frozen C46–C65 byte-for-byte. Independent CI final 136/136 SHA × Python3.10/3.11/3.12 and 33×3, no skip.

**CRYPTO ONLY | PAPER ONLY | NOT_TRADE_READY | orders=fills=trades=0.**
