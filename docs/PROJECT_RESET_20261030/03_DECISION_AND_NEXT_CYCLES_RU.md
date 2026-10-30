# PROJECT RESET — решение, что сохраняем и какой будет следующая попытка

Дата 2026-10-30, версия DECISION D0 (до нового market-feature test).

## 1. Решение по текущему состоянию

**НЕ начинать следующую стратегию на той же сломанной основе.** Не строить C118 как ещё один вариант CHoCH/FVG, чтобы не маскировать ошибку исследования новой оптимизацией.

**Сохранить и консолидировать** (в порядке важности):
1. Один канонический source contract из EMBER C116/C117 native original1m ZIP/CHECKSUM, as-of MTF aggregator, standard UTC/gap/source receipt.
2. Один модуль тестирования причинности и random-clock controlled trials из C114–C117, plus walk-forward/embargo/regime cost sensitivity, immutable SHA evidence.
3. Один симулятор исполнения после reconciled adversarial test EMBER+Terminal: next-open, signal/event/fill separation, STOP-FIRST, maker/taker/funding/spread/no future access.
4. Один управляющий риск/portfolio gate. Базовая безопасная версия не должна иметь регулируемого условия «вернуть убытки»/forced leverage.
5. Один PAPER store/event ledger и одна читаемая веб-оболочка SMOKE. Журнал на Google Drive — отчётный sink, не единственный authoritative accounting store.
6. Отдельный universe/as-of liquidity filter. Весь legacy Smart Money детектор сохранить как research features и визуализацию, **не как доказанный источник сигнала**.

**Что нельзя переносить «включенным»:** зоны как автоматическое право на вход, CHoCH как обязательный фильтр с предполагаемым edge, RR=2 фикс вместо цели, 25–30× как маршрут ускорения, рейтинги A+ до независимого теста, historical red/green windows как новые слепые данные, false positive «планировщик работает значит 24/7 рынок наблюдается».

## 2. Предварительный выбор новой попытки

**Исследовательский трек H1: относительная цена spot/perp + funding cashflow.** Это НЕ обязательное утверждение «будем торговать carry», а первая проверяемая гипотеза, поскольку:
- Расходы и доход имеют экономическое происхождение, а не определяются графическими названиями;
- имеются доступные публичные истории spot/perp/funding для pilot feasibility;
- автономность событийная: меньше зависимости от мгновенного 3m исполнения и постоянного человека у терминала;
- существует качественная академическая база по basis и futures.

Однако **дельта-нейтральный carry потенциально несовместим с прежней целью множества коротких направленных сделок**. Не подменять пожелание: его статус *пилот для проверки принципа*, а не готовое решение по заработку.

**Исследовательский трек H2: forced deleveraging, OI + aggressor flow / liquidation** — отдельная направленная кандидатура, ближе к быстрым торговым сетапам, но **временно SOURCE_FEASIBILITY_HOLD** до доказанного historical OI + liquidation metadata. Нельзя строить детектор по одним свечам и называть его «вынужденным потоком».

**Контроль H0:** price-only trend/time-series/simple long-short drift и random clock matched spot/perp. Нужен, чтобы новый H1/H2 не выглядел уникальным, когда тот же результат даёт случайная торговля или простой carry index.

**Решение между H1 и H2** будет принято только после маленького source feasibility прогона: если spot/perp quotes и settled funding не реконструируются без hindsight, H1 SOURCE_BLOCKED. Если OI/Liq/aggTrades имеют достаточно честную историю, H2 способен выйти на первое исследование; иначе нужны prospective данные и отдельный сборщик.

## 3. Этапы — как не повторить старую ошибку

| Шаг | Действие | Объективный результат для отметки |
|---|---|---|
| **RESET-00** | Complete 4-repo Git tree census + SHA overlap; data/document/runtime overview | **DONE**: `00_MACHINE_INVENTORY_GIT_TREES.json` с 2189 path/blob records, 121 SHA-identical пересечением |
| **RESET-01** | Выборочный технический аудит компонентов, статусов, «что брать/не брать», причины отказов | **DONE for initial scope**: `01_TECHNICAL_AUDIT_AND_REUSE_MATRIX_RU.md`; `NOT FULL CODE AUDIT` |
| **RESET-02** | Обзор литературы/API и ранжирование гипотез по данным, сложности и автономии | **DONE for shortlist**: `02_EXTERNAL_RESEARCH_HYPOTHESES_AND_DATA_FEASIBILITY_RU.md`; `NOT FULL LITERATURE SYSTEMATIC REVIEW` |
| **RESET-03** | Доказуемость manifest и SHA, invariant tests and CI | **IN PROGRESS**, не считать DONE до green CI |
| **RESET-04** | Полная branch-level экспертиза EMBER 30/Terminal 91/Smoke 19 и актуальная независимая Drive inventory, AppDeploy source snapshot | **OPEN**; данный Census — только по выбранным refs, а не всему branch DAG |
| **RESET-05** | Объединить source + simulator + immutable PAPER journal в минимальный package; contract tests | **OPEN**, дедупликация не означает перенос/рефактор уже сделан |
| **RESET-06** | Профилировать реальные открытые API: historical funding, matched spot/perp, Bybit historical OI earliest 2025-2026, optional liquidation provider; source timestamps | **OPEN**. Any 451/forbidden/gap/no quote => SOURCE_BLOCKED |
| **RESET-07** | Пререгистрировать **одну** гипотезу H1 или H2, два untouched OOS окна и matched random/no-trade benchmarks | **OPEN**. Создаётся до просмотра цены и PnL на новых периодах |
| **RESET-08** | Tiny canonical economic backtest of hypothesis, adversarial controls, 14/25/40 bps, confidence, drawdown | **OPEN**. FAIL закрыть быстро, не оптимизировать |
| **RESET-09** | Only if robust positive OOS, separate real-time PAPER data logging ≥30d and sample-size test | **BLOCKED** пока 07/08 не PASS |
| **RESET-10** | После достаточной независимой доказательной базы принимать отдельное решение о real execution | **LIVE BLOCKED** |

## 4. Протокол «плохая идея умирает быстро»

**Сначала вопрос, потом данные, потом код.** Новая гипотеза обязана содержать:
1. механизм market participant cash/forced flow, наблюдаемый причинный признак и earliest known timestamp;
2. короткий event definition, один горизонт и one-sided falsification threshold; without later «настроить красиво»;
3. существующий signed no-trade/random/price baseline, полная реалистичная стоимость ввода/вывода позиции;
4. power/sample, DD cap, regime robustness, securities & venues availability;
5. exact code SHA, original source checksum, append-only journal, owner-readable summary;
6. отдельный запрет на перенос прошлых проигравших фильтров как «необходимую академическую основу».

**Если по окончании SOURCE_QA невозможно реконструировать историю**, не писать стратегию и не рисовать положительный бэктест. Если получен negative net result на untouched OOS, **архивировать идею немедленно**. Если positive, НЕ запускать сразу live и не обещать скорость роста капитала.

## 5. Ownership архитектуры на следующий этап

`research/platform/` (предлагаемое будущее, пока не реализовано):
- `market_data/`: Binance 1m ZIP, futures aggTrades, funding, Bybit OI; immutable receipts/available_at;
- `features/`: independent causal source-known price and venue flow features; no hidden execution;
- `hypotheses/`: one H1, one H2 separated by `hypothesis_id` and precommit ID;
- `execution/`: single simulator, stop-first, two-leg, funding and capital;
- `evaluation/`: random/no-trade, bootstrap cluster, untouched OOS, stress/portfolio;
- `evidence/`: source manifest, trades, DD trace, hypothesis decisions and failure reason;
- `interfaces/`: read-only SMOKE, PAPER event log, notifier.

Do NOT merge `Smoke-strategy` into SMOKE terminal by overwriting the source. 121 files overlap exactly; migrate only verified missing functionality. AppDeploy requires snapshot and content reconciliation first.

## 6. Рабочее правило для следующих чатов

Не начинать архитектуру «с нуля». Открыть `00…json`, `01…md`, `02…md`, `03…md`; затем read branch SHA and only relevant original code/CI to avoid repeating previous hundreds of iterations. Все части read-only до окончания source/legality audit. Чётко отчитываться по статусам DONE/OPEN/BLOCKED; не обещать фоновой работы и не трактовать красный торговый результат как технический FAILURE, а ошибочную математическую модель как CI PASS.

## 7. Ограничение этого решения

Сейчас НЕ было живого проверенного отчёта по H1 или H2, никакой статистики прибыли, полного code-review всей истории branches/Drive, ни импортированного единого ядра. Это технически и исследовательски **основанный стартовый план**, но ещё не готовый новый alpha и не обещание заработка.
