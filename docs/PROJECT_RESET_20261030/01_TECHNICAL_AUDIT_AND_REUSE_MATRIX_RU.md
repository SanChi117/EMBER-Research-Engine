# PROJECT RESET — технический аудит активов и матрица повторного использования (2026-10-30)

**Статус:** первичный полный **Git tree** census четырёх репозиториев на зафиксированных SHA; **выборочный содержательный** аудит основных модулей, собственных отчётов, автотестов, Google Drive Atlas/документа V2.2/анализа CryptoX и read-only AppDeploy. **НЕ** ручной code-review всех 2189 файлов и не подтверждение успешности каждого теста. Никаких новых торговых правил/ордеров, не изменены прежние репозитории или развёрнутая среда.

## 0. Принципы

**Раздельные вердикты:** TECH_PASS = проверка заданного программного контракта; SOURCE_PASS = проверка часов, источников, непрерывности; ECONOMIC_PASS = достаточный положительный чистый результат вне выборки, с контролями; DEPLOY_PASS = фактический доступ и сохранение состояний; LIVE_ALLOWED = отдельное решение, которого **нет**. Один PASS **не** влечёт остальных.

**Ярлыки:** **A/REUSE** — ясно изолированный повторно применимый компонент, но перед включением нужен regression/adversarial contract; **B/REPAIR** — полезный компонент с известным дефектом или существенным недоказанным свойством; **C/REFERENCE** — исследовательский/аналитический справочник, но нельзя использовать как сигнал; **X/ARCHIVE** — не переносить торговое решение в новую стратегию; **?/REVERIFY** — существование подтверждено, функциональный статус не подтверждён.

## 1. Проверенная карта имущества

Источник: машинный полный Git-path/Git-blob hash/size каталог `00_MACHINE_INVENTORY_GIT_TREES.json`, создался без скачивания исходных секретов, получен из непорезанных `recursive=1` деревьев.

| Репозиторий, снимок | Файлов Git | Скрипты кода (ориентировочно) | Тест-файлы (эвристика имени) | Важная характеристика |
|---|---:|---:|---:|---|
| [EMBER-Research-Engine](https://github.com/SanChi117/EMBER-Research-Engine) branch `research/c117-random-time-4h-zone-counterfactual-20261030` SHA `041eaf9fe8275c8c66047efc489b6b72b818a04d` | 1455 | 458 | 163 | академическая семантика C08–C117, canonical original native1m ZIP, воспроизводимый paper replay, append-only A181 audit, 430 workflow-файлов (НЕ 430 независимо пройденных экспериментов) |
| [Smoke-strategy](https://github.com/SanChi117/Smoke-strategy) `main` | 160 | 106 | 16 | исследовательские сборщики, MTF, выбор universe, генератор, Paper, WFO, batch; main PROJECT_STATUS.md описывает *устаревшее раннее состояние*, не итог всех branches |
| [smoke-trading-terminal](https://github.com/SanChi117/smoke-trading-terminal) `main` | 326 | 236 | 45 | UI, TV Pine, V5, chart, paper lifecycle, adapter, Python strategy_lab. **Main не равен AppDeploy deployment и не равен** `fix/paper-minute-monitor-and-strategy-slot-20261013` |
| [telegram-signal-bot](https://github.com/SanChi117/telegram-signal-bot) `main` | 248 | 48 | 188 | исторический Telegram scanner, experimental backtests, workflows; наличие файлов не означает исправный сигнал |
| **Всего** | **2189** | **848** | **412** | Инвентаризация каталога. Эти счётчики НЕ измерение качества кода и НЕ число пройденных тестов |

**Дедупликация:** из 160 файлов Smoke-strategy vs Terminal main обнаружены **126 одинаковых путей**, **121 совпадает по Git blob SHA**, **5 отличаются**: `PROJECT_STATUS.md`, `README.md`, `pyproject.toml`, `scripts/fetch_binance_candles.py`, `scripts/run_paper_mode.py`. Поэтому переносить `strategy_lab` «ещё раз» в новую систему не нужно — в значительной части это уже зеркала. Установить единый владелец исходного модуля (не создавать 3 независимых копии).

**Хранилища помимо Git:** [Google Drive Atlas 12.10](https://docs.google.com/document/d/1zobqNAuGRjgOt7-cPW6GQR2HSzsxYGRQAPpMfrpk0OA/edit), документ V2.2, журналы, отдельные Google Docs и Sheets, академические материалы, исходные Pine, AppDeploy — **частично каталогизированы**. Атлас от 12.10 перечисляет 149 объектов (50 папок / 99 файлов), сам предупреждает, что это не byte-for-byte копия. Новые Drive-файлы после 12.10 требуют свежей полной инвентаризации. Не путать «атлас есть» с «полностью проверены все материалы».

**Реальный деплой:** AppDeploy `smoke-trading-terminal-0kl792`, прочитано `get_apps` и `get_app_status` 30.10.2026, snapshot `1792085859614`, status **ready**, frontend_url https://smoke-trading-terminal-0kl792.v2.appdeploy.ai/ . **Однако** логи содержат HTTP 451 Binance USD-M `fapi/v1/klines` и прерванные REST-запросы OP/XRP; GUI QA ready ≠ reliable market feed, ≠ live data, ≠ online scan proof. Никакого деплоя/секретов/ордера здесь не меняли.

## 2. Матрица по компонентам, а не по именам стратегий

| Модуль | Конкретная опора | Категория | Почему и как применять |
|---|---|---|---|
| **Канонический исторический OHLCV** | EMBER `d05/c116_canonical_original_native1m_source.py`; original Binance USD-M ZIP/CHECKSUM → 1m→3m/5m | **A/REUSE** | Формат, UTC, непрерывность, SHA, fully closed; C116/C117 1344 ZIP и 1 935 360 1m. Переносить как независимый `DataContract`, с явно описанной областью применимости. Не утверждать независимую биржевую OHLCV-истину: original native3m/5m иногда противоречили друг другу (C114/C115). |
| **Live REST/WS парсер, нормализация 1m/5m** | Terminal `core/market/klines-parity.ts`, market adapters, browser candle chart | **B/REPAIR** | Есть типовые тесты, но серверный Binance HTTP451 и abort. Не считать «ready» устойчивостью; нужен альтернативный легитимный provider, fail-closed freshness, gap detection, UTC clock, as-of/source receipts, повторяемое сравнение provider. |
| **Синхронизация старших TF, causal alignment** | EMBER `ember/core/context_builder.py`, `d05/c96_canonical_history_warmup_invariance.py` и агрегация в C114/C116 | **A/REUSE** | C96 проверял повторяемость same history prefix и требовал 7d/достаточно 1W; нужен parity-протокол и для новой фичи OI/funding: именно known-at, не timestamp появления в будущей БД. |
| **Pivot/FVG/OB/IDM/StrongHL/CHoCH** | EMBER `research/mtf-element-audit-v1/d05`, C08–C117; LuxAlgo source | **C/REFERENCE** | Детекторы технически полезны для отображения и диагностики условий, **не переносить как mandatory alpha filter**. Семантика неоднородна и часть source-only академических тонкостей не подтверждена. |
| **4H far edge SL и closest unswept FTA** | EMBER `d05/c105_parent4h_structural_geometry.py` | **B/REPAIR (utility)** | C114/C117 строго проверяли происхождение 4H SL/TP. Сохраняем только **конструктор риск-плана/расчёта препятствия**, не считаем наилучшей экономической геометрией. Результат этой конкретной геометрии NEGATIVE. |
| **Симуляция исполнения, STOP-FIRST/GAP/NEXT-OPEN** | EMBER `d05/c105_parent4h_structural_geometry.py::simulate`, Terminal `core/paper/paper-lifecycle.ts`, `core/paper/entry-minute-audit.ts` | **A/REUSE + B/REPAIR** | Положительное инженерное наследие: stop-first, разделение события и fill, затраты, source gaps. Прежде чем выбирать эталон — reconcile два симулятора на единой матрице золотых кейсов: spread, maker/taker, latency, stop-gap, funding, mark/index, size, multiple legs, missing bars. |
| **Costs / portfolio / drawdown / paper equity** | EMBER `ember/simulation/portfolio.py`, `d05/c113_final_execution_geometry_research.py`; Terminal `core/risk` и `strategy_lab/portfolio_simulator.py` | **B/REPAIR** | Исторические R и портфельный maxDD не являются фактическим доходом биржи. Есть рабочие risk contracts; дополнить funding, basis, ликвидационную маржу, partial fills, slippage distributions, correlated BTC shock, volatility exposure. |
| **WFO, split/embargo, negative controls, placebo** | EMBER `ember/simulation/walk_forward.py`; C96–C117; Smoke-strategy `strategy_lab/walk_forward.py` | **A/REUSE** | Один из главных активов. В C117 был настоящий conditional random-clock control с сохранёнными несостоятельными первыми отчётами и исправлением A181. В новой гипотезе предрегистрация и untouched OOS обязательны. |
| **Тесты + append-only SHA-журнал** | EMBER `ЖУРНАЛ_ДЕЙСТВИЙ.jsonl` A181/181, `tools/auditlog.py`, CI [41124106697](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41124106697) | **A/REUSE** | Проверяет целостность цепочки и факт эксперимента. Ветку аудита не чистить и не объединять без provenance. Исторический CI успешный на конкретной ветке/коммите не доказывает иную ветку. |
| **Universe / sector strength/selection** | Smoke-strategy `rolling_symbol_strength.py`, `universe_selector.py` и `universe`; Terminal duplicate | **B/REPAIR** | Полезно отсеивать delisted/illiquid/высокий spread; **не** подбирать тикеры по результатам полных test windows. As-of universe listing & missing delisted records, liquidity/fees benchmark. |
| **Market regime context** | EMBER `context_builder.py`; Terminal V5 LOCATION/REVERSAL/CONTINUATION | **C/REFERENCE** | Рыночную фазу хранить как объясняющую **фичу** для эксперимента; C111 фильтр режимов не спас экономику. Не включать BTC «вниз» по posthoc подглядыванию. |
| **Scoring (A+, quality, structure)** | Smoke-strategy `trade_quality_score.py`, `structure_learning.py` | **B/REPAIR** | Есть программная инфраструктура, но баллы не калиброваны как вероятность доходного исхода и initial sample trades synthetic. В новой системе оценка только после пререгистрации чистой выборки, иначе декоративная A+. |
| **PAPER ledger / immutable fills** | Terminal `core/paper/paper-receipt.ts`, `paper-lifecycle.ts`, `paper-journal`; AppDeploy deployment; Google Docs [журнал автономного механизма](https://docs.google.com/document/d/1wHIXGhzTsdEJZRg8DkDV3L2GX_rcb8O4VnyA9-c5Orw/edit) | **B/REPAIR** | Требует выбрать **один первичный журнал событий**, readback exact orders, posted vs executed vs cancelled, восстановление состояния и дедупликация. Google Docs — человекочитаемый экспорт, не единственный transactional source of truth. |
| **Webhooks/TV Pine 3.6.3** | Terminal `research/tradingview/Strategy_V2_2_Radar_LuxAlgo_v363_webhook.pine`, `core/contracts/tv-v22-candidate.mjs` | **C/REFERENCE** | Contract парсинга и алертов полезен, но нет доказательства установленного текущего Pine/потока боевых алертов. Для нового исследования предпочтителен прямой data collector, не обязателен TV premium. |
| **Frontend SMOKE / графики** | Terminal `app`, AppDeploy URL, `PROJECT_STATUS.md` | **A/REUSE UI; B/REPAIR data** | Сохранять готовую оболочку, не переписывать до выбора гипотезы и feed; раздельный runtime GitHub Next/Vinext и AppDeploy Vite/React — **не overwrite** без backup и source diff. |
| **Telegram signal bot** | `telegram-signal-bot/bot`, `strategy_research` | **?/REVERIFY** | Reusable message layer при условии separate regression. Последние найденные GitHub Actions июня 2026 **failure**, значит нельзя считать инфраструктуру исправной без retest. Не переносить старую стратегию или ключи. |
| **Виртуальный планировщик и журналы Drive** | Проверенный по метаданным актуальный журнал, предсбор/срезы в ChatGPT | **B/REPAIR** | Keep source freshness, timestamp and no false entries. Автоматизация ≠ continuous execution; пока не достоверный store market microstructure. Не модифицировать существующие расписания без запроса. |

## 3. Закрытые торговые семейства и почему не переносить

**Архивировать правила, сохранить их в исследованиях:**
- EMBER C93–C108: сценарии BOS/IDM/POI, отличающиеся TF/parent/warmup; QA улучшилась, но экономическая устойчивость не доказана; C98 новые рыночные данные A/B/C **все нет-прибыль** при 25bps.
- C109–C113: 4H FVG first touch, структурные SL/FTA, stop/entry geometry modifications → не обеспечили profit robustness. C111 отдельный режимный фильтр FAIL, C112 «зона→зона» как доходная модель FAIL.
- C114/C115: независимые native3m/native5m original источники обнаружили существенную несогласованность истории (volume drift и price mismatch). SOURCE_BLOCKED, не экономическая победа/поражение.
- C116: **canonical original native1m engineering PASS; economic NO_POWER** (строго совпавшие C114 T/C пары 4/1).
- C117/A181: два новых 56d окна, source integrity и full cohort; corrected T-only netR25 **−16.104518R, PF0.488377** и **−5.864886R, PF0.731755**; в обоих статистика **ECONOMIC FAIL**. Исходная ошибочная публикация T-биллинга оставлена, A181 исправила 100/93 неверно включённых control fills. Отрицательный случай фиксируется в `B1_C117_A181_CORRECTED_FINAL_RANDOM_CLOCK_CHoCH_RU.md`, [CI](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41124106697).
- Terminal V5: PROJECT_STATUS/README прямо указывают **RESEARCH_ONLY_REGIME_INSTABILITY**, прежние сильные validation/test не перевесили отрицательную calibration/малое N; не возвращать готовый сигнал V5.
- Smoke-strategy FULL_BALANCED/FULL_STRICT sample results: `PROJECT_STATUS.md` прямо предупреждает, что pipeline тогда начинался с **готовых sample trade CSV**, не полностью real-market executable signal+fill. Прибыли из synthetic/sample отчётов не являются edge.
- Telegram/TradingView old turbo/RSI/EMA strategies: оставить справочником и историей failure, пока не найдена независимая воспроизводимая экономическая опора.

**Важно:** C117 не доказывает, что все возможные стратегии на основе зон бессмысленны, только отвергает торговую пригодность проверенной конфигурации и данных. Любая новая модель требует собственной пререгистрации. НЕ спасать старое семейство cherry-picking направления, RR, периода, тикера и слippage.

## 4. Очередь быстрой инженерной доработки (без торговых обещаний)

**P0 — зафиксировать версии и убрать повторы:** branch C117 A181 + Git tree snapshot 4 repos + текущее AppDeploy; сравнить 121 SHA-identical files, назначить единую библиотеку, не менять deployment, сделать source ownership map.

**P1 — один `MarketObservation` contract:** символ, exchange, asset_type=spot/perp, interval, [open,close], data-observed-at, event-time, available-at, source URL/provider receipt, checksum, latency/gap mask, crossed-market sanity. Original1m canonical — исторический базис; Binance/Bybit USD-M live feed — отдельные адаптеры. Провал свежести => `DATA_UNTRUSTED`, НЕ trade.

**P2 — один `ExecutionResearchSimulator`:** frozen costs 14/25/40bps + maker/taker, funding flows, two-leg spot/perp, latency, bid/ask, stop-first, mark gap/liquidation, capacity, multi-symbol cross-exposure; golden tests из EMBER и Terminal; отсутствие исходных данных означает отказ.

**P3 — единый proof journal:** compare GitHub algorithm state, source snapshots, PAPER recorded signal, execution receipt; regression suite охватывает lookahead, early competing, portfolio DD, WFO, OS time, incomplete archives, control contamination.

**P4 — минимальный DataCollector OI/funding/basis:** только **после** подтверждения timestamp/истории и источника, начиная с маленького BTC/ETH/SOL; проверить, сохраняется ли фактическое наблюдение и нет ли API 451, не запускать бессмысленную непрерывную нагрузку.

**Порядок приёмки:** код + negative CI → verified original source 1m+metadata+OI/funding → baseline signals and random control → untouched OOS across regimes → paper 30d/100 trades if frequency appropriate → only then independent decision; live OFF.

## 5. Что ещё **не** сделано и нельзя скрывать

1. Не проведён ручной построчный audit всех **2189** файлов / **91** ветки Terminal; только полный Git census и выборочный code/doc read. Ветки и deployed source нужно отдельно сверять, иначе риск утраты более позднего исправления.
2. Не проведена полная актуальная после 12.10 инвентаризация всех Google Drive папок, бинарных курсов и скриншотов. Атлас изучен как каталог, а не полный байтовый архив.
3. Не выгружен AppDeploy Vite/React snapshot для сравнения содержимого с GitHub; status READY и error logs прочитаны read-only.
4. Не гонялись локально все три чужих репозитория и нет real-time сверки маркет-фида.
5. Не реализован новый алгоритм, не проверена новая торговая гипотеза и не получен новый positive economic result.
6. Нет подтверждения независимых исторических OI/forced liquidation **за 2025-2026**, API Binance 30-day limitation делает часть исследования SOURCE_BLOCKED без иного licensed archive.

**Первый итог:** сохранить 1m source+causal tester+cost simulator+journal+terminal UI; не переносить CHoCH как alpha, скопированные модули не клонировать, market-feed/reconciliation приоритетнее распознавания новых фигур.
