# B1/C67 — Route A: отдельный 1H Trigger или 1H VC NEW POI → первый source retest на 15m; вложенная 1H IMB запрещена

Дата UTC: 25 октября 2026. Репозиторий `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`. **Исследование криптосвечей; PAPER ONLY / NOT_TRADE_READY.** Никаких ордеров или статистики прибыли.

## Авторское правило, проверенное по исходнику

Google Drive `2. Entry by IMB & SNR.txt` (ID `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ`) различает:

1. **4H POI actual first test → 1H Trigger** (рейд SSL/BSL или *допустимый* IMB) → **15m VC через IMB/SNR** → возможный вход только при авторском подтверждении.
2. **Отсутствует 1H Trigger** → 1H VC [RB/SNR/IMB], которая образует **NEW 1H POI**. После **реального** теста новой 1H POI следует 15m trigger → 5m VC; если trigger отсутствует, допустимый 15m VC [SNR/IMB]. **Нельзя переходить сразу к 15m входу лишь потому, что появился 1H VC.**
3. **Вложенная 1H IMB, полностью находящаяся в исходной 4H IMB, не считается 1H триггером**. Триггер и новая POI, одновременно интерпретируемые из одной 1H технической IMB без авторской метки, **не выбираются произвольно**.
4. Route B IDM (отдельный файл `3. Entry by Inducement [IDM].txt`) не требует дополнительного VC Route A после родительской авторской VC. Route C raid→BOS 3m/5m — отдельная модель; их код и сигналы не смешиваются с C67.

**Ограничение:** ни скриншоты курса, ни размеченные примеры иных рынков не являются timestamp/price/SHA-ID авторской разметкой по данным Binance. По исходным криптосвечам **ноль** положительных и отрицательных авторских goldens. Здесь только **техническая** геометрия с fail-closed авторскими флагами.

## Сделано в C67

- [x] `d05/c67_route_a_1h_trigger_vs_new_poi_source_fork.py`: новая отдельная state machine, не модифицирующая C46–C66. Читает C46 original4H source classic IMB boundary + первый закрытый native3m wick contact. Различает **1H preknown strict fractal unswept SSL/BSL wick raid** (фактическая тень с открытием и закрытием по другую сторону) как технический кандидат Trigger от **1H VC-структуры RB/SNR/IMB**, не повышая статус.
- [x] Для 1H IMB определяет строго закрытый 3-свечный wick gap, реальные исходные границы и **полное включение** диапазона gap в границы исходной технической 4H IMB; при полном вложении исключает кандидат из ветки 1H Trigger. Возможная контекстная VC-POI технического типа остаётся отдельной веткой и НЕ подтверждает авторский 1H VC. При одновременном источниковом Trigger и VC — `FIRST_ANY_1H_TRIGGER_AND_VC_AMBIGUOUS`; при разных направлениях в одно время — отдельная неопределённость.
- [x] В ветке source new 1H VC POI первое **native15m wick-пересечение технической пары или IMB** учитывается **только после полного закрытия** 1H события. Это не автоматический *первый ВАЛИДНЫЙ* авторский тест POI. Дальше первое ЛЮБОЕ native15m source-event (IMB/SNR): **сохраняются противоположные и одновременные направления**. Если технический IMB требует ещё owner 5m VC/поддержки — ветка только исследовательская, не реальный вход. RB контекстный, MB не VC.
- [x] Блокирует подделку авторского POI, VC, StrongHL, неизвестные raw native15m SHA:UTC, будущие и незакрытые 1H/15m, несовпадающие 1H/15m закрытия. Фиксированное 24h research окно, физический `as_of` из исходных файлов, правоцензура. Всё ещё **0** author test, **0** signals/SL/TP/FTA, **0** orders/fills/trades.
- [x] `d05/test_c67_route_a_1h_trigger_vs_new_poi_source_fork.py`: **35** отдельных позитивных/отрицательных синтетических сценариев × Python 3.10/3.11/3.12, включая первый opposite event, совпадающие стороны, correct nested/non-nested gap, отсутствие истинного 1H retest, 1H new POI source retest только после закрытия, первый opposing native15m после теста и тай-пересечения, ошибочный raw SHA, owner goldens/order spoof, `asof` right-censor. [CI 40218943795](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40218943795) SUCCESS 3/3.
- [x] `tests/probe_c67_original45zip_route_a_fork_retest.py`: заново независимо скачаны **45 оригинальных SHA-checksummed Binance USD-M ZIP** по BTCUSDT/ETHUSDT/SOLUSDT/XRPUSDT/BCHUSDT за 01.09–02.10.2026: **76800** original closed3m, **15360** original closed15m, **160** original daily, **3840** derived closed1h. **Все 153** C46 4H technical parent и C60 native3m contacts, C62 1H SNR/RB/IMB, C63 first-any и **все** frozen original C66 15m source-events заново рассчитаны и сравнены с неизменными Git blobs C46/C60/C62/C63/C66. Оригинальные C64/C65 не менялись.
- [x] Первое полное [CI 40219282645](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40219282645) **SUCCESS 5/5**, независимая вторая исходная 45 ZIP с побайтным сравнением [CI 40219450625](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40219450625) **SUCCESS 4/4**, 35×3 повторно. Полный immutable source JSON `evidence/c67/C67_ORIGINAL45ZIP_ROUTE_A_1H_TRIGGER_NEW_POI_15M_FIRST_RETEST_FORK.json`: **348943 bytes**, SHA256 `f16a8be9e01d9edc3f71d7c091665e32f22cdd66ba0eb7fef466551f482c8c4a`, Git blob `87409101a6fad4897b32e13085c9a0cc13566594`. Отдельный свидетель `evidence/c67/C67_INDEPENDENT_ORIGINAL45ZIP_ROUTE_A_1H_FORK_WITNESS_20261025.json`.

## Что показали фактические криптоисходники

| Технический source-статус (каждый parent один раз) | Количество |
|---|---:|
| 4H source зона не была впервые затронута | **21** |
| Первое 1H source-событие в противоположную сторону | **42** |
| Первое 1H source-событие двунаправленное | **11** |
| Одновременные source 1H Trigger и VC — ветка неоднозначна | **18** |
| Source 1H Trigger-first → первое 15m IMB/SNR в той же стороне | **13** |
| Source 1H Trigger-first → первое 15m IMB/SNR в противоположной стороне | **13** |
| Source NEW 1H VC POI wick-test → первое 15m opposite | **21** |
| Source NEW 1H VC POI wick-test → 15m IMB candidate, 5m VC не подтверждено | **6** |
| Source NEW 1H VC POI wick-test → 15m SNR technical source | **6** |
| Source NEW 1H VC POI wick-test → 15m одновременно две стороны | **1** |
| Source NEW 1H VC POI wick-test → нет последующего 15m события | **1** |
| **Всего 4H source parent contexts** | **153** |

**187 source-совпадений полной вложенности 1H IMB в 4H IMB** запрещены в trigger-ветке. **Это повторяющиеся наблюдения через пересекающиеся исходные 4H parent contexts, не 187 независимых зон/сделок**. Для source RB/SNR зоны использованы консервативные границы двух свечей; авторский выбор RB/SNR POI и действительность первого теста этими границами не доказаны.

Никакой строки таблицы нельзя считать торговым сетапом, выигрышем или сигналом по академии: **сам 4H parent ещё не owner-selected POI; первая 3m тень ещё не owner VALID test; 1H/15m source события ещё не владеют author-approved VC; 5m VC ещё не собран**. Эти технические кандидаты не могут быть подменены стратегией Route B IDM или Route C.

## Ошибки, исправленные и оставленные в CI-истории

- [CI 40218779842](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40218779842) красный: некорректные синтетические свечи 1H gap: open ниже low. Исправлены **тестовые** OHLC, рынок не редактировали, [40218943795](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40218943795) 35×3 зелёный.
- [CI 40219112041](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40219112041) и [40219214487](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40219214487): C67 full probe ошибочно сравнивал старый C66 **числовой счётчик** native15m source events с перечнем `all_native15m_original_source_events`. Заменён только ключ-идентификатор frozen source, цены и классификация не менялись. [40219282645](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40219282645) и [40219450625](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40219450625) полные исходники SUCCESS.

## Следующий этап C68 и входные блокеры

**C67 закончен как SOURCE RESEARCH, не как готовый академический маршрут.** C68: истинная семантика подтверждённого 1H Trigger/NEW POI, first VALID 1H POI retest, правильная связь с StrongHL/Volume Confirmation 15m и 5m, структурными FTA/SL/TP с истинными исходными свечами. Без положительных/отрицательных авторски размеченных Binance crypto goldens по `symbol + timestamp + OHLCV source SHA + 4H POI label + Trigger/VC branch + first valid test` **author fidelity не доказана**. Отдельно OOS PAPER и комиссионная проверка до интеграции в SMOKE, никаких live orders.

## Приёмка A137

Принимать **ровно шесть** новых immutable SHA evidence paths: C67 module; C67 35 tests; C67 original45 ZIP probe; full 348943-byte source JSON; second independent witness; **этот** report. Previous 136/136 ledger tip `03f5277ae06bc2249e90b92669ca9dc222d73eb5ebf047ae3406eebd082bafea`. Независимый final 137/137 SHA × Python3.10/3.11/3.12 и 35×3, все предыдущие архивы и source unchanged. После A137 **НЕ редактировать ни один из шести файлов**, вести новые уточнения только в постоянной передаче проекта.

**CRYPTO ONLY | PAPER ONLY | NOT_TRADE_READY | orders=0, fills=0, trades=0.**
