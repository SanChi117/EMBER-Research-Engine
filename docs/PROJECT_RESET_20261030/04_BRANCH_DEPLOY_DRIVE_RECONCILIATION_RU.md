# RESET-04 — приоритетные ветки, независимый AppDeploy и актуальный Google Drive

Время первичной проверки: 2026-10-30 UTC. **Это содержательная проверка выбранных веток и файлов; не утверждение, что прочитано всё содержимое 143 веток.** Режим только чтение чужих проектов, ни один deployed snapshot, секрет, торговый журнал, расписание и прежние исходники не изменялись.

## Git — точные сравнения, позволяющие не потерять лучшие версии

- `smoke-trading-terminal/main`: **326 Git blob файлов**.
- `smoke-trading-terminal/fix/paper-minute-monitor-and-strategy-slot-20261013`: **386 файлов**. Из 326 общих с main **318 SHA полностью идентичны**, **8 отличаются**, **60 добавлены**. Из ключевых отличий в `core/paper/`: `paper-pilot-state.ts`, `paper-receipt.ts`. Последняя исследовательская ветка содержит намного больше готового: `portable-paper-runtime.ts`, `portable-cycle-runner.ts`, `postgres-paper-store.ts`, Postgres/PAPER recovery и integration tests. **Это приоритетный кандидат для PAPER слоя**, а не `main`.
- Branch latest `PROJECT_STATUS.md` в fix содержит P11/P12: воспроизведённый real disposable PostgreSQL `pg_dump/pg_restore`, проверки CAS/once-only, negative financial corruption tests. Указаны успешные CI [38805670747](https://github.com/SanChi117/smoke-trading-terminal/actions/runs/38805670747) и [38806065551](https://github.com/SanChi117/smoke-trading-terminal/actions/runs/38806065551). Это **историческая QA конкретных коммитов и синтетической БД**, не доказательство корректного deployed database backup или market-executable fills.
- `Smoke-strategy/main`: 160 файлов; `Smoke-strategy/agent/smoke-core-candidate-2-research`: **1294 файла** — гораздо более богатая research ветка. `research/SMOKE_CORE_CANDIDATE_2_RESEARCH_SPEC_V1.md` фиксирует жизненный цикл причинного распознавания, P1–P8 заморозку, восстановление после Candidate1 и отделение долгосрочной цели от торговой прибыли. Этот текст **называется SPEC, не prereg прибыльности**. `research/SMOKE_RESEARCH_LADDER_FINAL_CONCLUSION_V1.md` (18.07.2026) имеет статус **EXHAUSTED_WITHOUT_ROBUST_EDGE**: лучший SMC_POI_VC_CHAIN 47 сделок, PF1.2023, 5 из 10 прибыльных folds, меньше предзаданного порога 60 сделок и 6 положительных folds. Не использовать наблюдавшееся short PF2.0195 как новый фильтр: posthoc.
- `EMBER/research/academic-engine-recovery-20261015` и `EMBER/research/c117-random-time-4h-zone-counterfactual-20261030` имеют соответственно **1388** и **1455** файлов; последняя версия дополняет старую by strict C116 canonical1m и A181 corrected C117 evidence. Для источника данных и нулевых контролей выбирать C117/A181; старые первоисточники в академической ветке сохранять как semantic reference.

## AppDeploy: snapshot не равен GitHub branch

Прочитаны AppDeploy `get_apps`, `get_app_versions`, `src_glob`, `src_read`, `get_app_status`. Проект `smoke-trading-terminal-0kl792`, deployed Vite snapshot **v52 `1792085859614`**, 15.10.2026, в каталоге **52 сохранённые версии v1-v52**. `src_glob` последнего snapshot отдал **94 файла** (содержимое пока прочитано выборочно), включая frontend `src/App.tsx`, backend `backend/index.ts` и `services/orchestrator/observe-cycle.ts`, отдельный runtime от GitHub Next/Vinext.

**Побайтовая сверка `src_read` v52 versus GitHub Terminal fix** (нет ссылок на секреты):
- `core/paper/paper-lifecycle.ts` — EXACT, 9582 символа; Git blob `ba922dafef4524957ccd50418374da535b151ad2`.
- `core/paper/paper-receipt.ts` — EXACT, 4395 символов; blob `e226cea762470f9d432d0baeb4babbdf4d552804`.
- `core/market/klines-parity.ts` — EXACT, 2455 символов; blob `a3785ae2ab0aa3400510d235948ef5984295fc01`.
- `app/lib/binance-public-transport.ts` — **DIVERGENT**; AppDeploy 3511 символов, GitHub 2024; первая строка AppDeploy импортирует `@appdeploy/client`; **запрещён слепой merge**. В AppDeploy transport отдельно предусмотрен публичный путь REST и source-labelled browser proxy, но HTTP 451 может возвращаться даже при READY.
- `services/orchestrator/observe-cycle.ts` в AppDeploy присутствует; по точному пути GitHub Terminal fix `NOT_FOUND`. Разработку нельзя переносить «всё совпадает».
- `get_app_status`: snapshot READY, frontend QA warnings; фактические historical frontend errors содержат aborted REST и Binance HTTP451. READY **не** означает, что рыночные источники поставляют целые свечи сейчас.

**Вывод:** проверены три одинаковых компонента, один diverged, один AppDeploy-only. **Полный независимый побайтовый AppDeploy snapshot backup ещё не сделан**: никакого разрешения перезаписать деплой. Перенос разрешается только после baseline export/source diff+rollback.

## Google Drive (только подключённые пользователю материалы)

- 30.10.2026 запрошена новая общая `Google Drive.search(query="",topn=100)`: возвращены **100 объектов**, но этого недостаточно назвать полным новым каталогом (снимок ограничен 100 без гарантий покрытия остальных). Старый `ПОЛНЫЙ АТЛАС` 12.10 сообщает **149 объектов** (50 папок/99 файлов), сам оговаривает отсутствие побайтовой копии архивов.
- В новой выборке обнаружены по метаданным: виртуальный журнал автономного механизма с последним обновлением 30.10, буфер исходных рыночных данных 30.10, 2 research/monitoring Google Sheets, документ V2.2, CryptoX 20 screenshots, атлас, архивные handoff-версии. Не смешивать исходные торговые транзакции и шаблоны из разных эпох.
- Отдельный live source-of-truth PAPER ledger пока **не установлен**. Хранить закрытые события, сигналы, факты исполнимости и шаблоны отдельно; Google Docs можно оставить отчётным представлением. Приватное содержимое таблиц и имена пользователей **не копируются в GitHub**.
- Задача полного поиска всех веток Drive/спецификаций остаётся открытой. Не вносить фиктивные значения из частичных поисков и не удалять существующие данные.

## Новый реальный инженерный шаг R01

Создан отдельно от старых стратегий минимальный **strategy-neutral** пакет `research/platform/`:
- `market_contract.py`: `ClosedBar` with explicit UTC ms, known-at/ingested-at, spot/perp, mandatory SHA provenance, fail-closed gaps/duplicates/staleness/source mix, explicit *historical assumed close* when adapting C116 Original1m. Не превращает backtest в подтверждённый live feed.
- `paper_execution.py`: консервативный симулятор PAPER на quote bid/ask, next full closed 1m, structural SL/TP, STOP-first, adverse gap, long/short, double fee and slippage, halted on missing future time coverage. No exchange orders API.
- `sha_ledger.py`: deterministic SHA256 event chain, duplicate rejection, payload tamper detection; **in-memory**, not yet transactional Postgres and without внешней гарантирующей подписи.
- `tests/test_reboot_platform.py`: 22 tests including negative cases; CI Python 3.10/3.11/3.12 [R01 run 41132022060](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41132022060) SUCCESS for pure isolated tests, before main CI import runner correction.

**Не заявлять** production-equivalence нового Python paper simulator to TS AppDeploy: Python is **independent specification prototype**, needs exact shared golden fixtures and cross-language comparison before migration. Funding/two-leg/basis, mark/liq and live collection not yet implemented. Не включать старые CHoCH как signal в новый пакет.

## План до завершения объединения

1. По branch heads выбрать по одному эталонному модулю (фикс CI/источника), подтвердить SHA; не менять источник ради более прибыльного результата.
2. Сверить Python PAPER и TS PAPER на одних числовых GOLDEN fixtures (entry+full 1m+gap+fees+cancel+no coverage). При расхождении маркировать `PARITY_FAIL`, не утверждать универсальную синхронизацию.
3. Согласовать `known_at`/timestamp policy между Binance archived1m, spot/perp, funding settlements и live OI.
4. Реальный source-feasibility пилот H1 отдельно до всякого backtest; при отсутствии quote schedule = SOURCE_BLOCKED.
5. Independent risk/accounting journal, negative falsification, WFO, no live.

## Ограничение по среде

Ни AppDeploy v52, ни Terminal fix, ни Telegram/старые стратегии не запускали реальное исполнение в текущем цикле. Сделаны read-only comparisons, добавлена новая отдельная исследовательская библиотека и её unit CI. Самостоятельное прибыльное торговое преимущество не заявлено.
