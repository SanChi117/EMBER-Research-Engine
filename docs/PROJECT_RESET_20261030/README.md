# PROJECT RESET 2026-10-30 — индекс переиспользуемых инструментов и исследовательских гипотез

**Назначение:** уйти от бесконечных вариаций уже опровергнутой системы к инвентаризации, консолидации и быстрым дешёвым тестам независимых рыночных гипотез. Репозиторий исходного C117/A181 и все прошлые отрицательные результаты сохранены. **Никаких реальных ордеров, без новых сигналов.**

## Что прочитать и в какой последовательности

1. [00_MACHINE_INVENTORY_GIT_TREES.json](00_MACHINE_INVENTORY_GIT_TREES.json) — 2 189 исходных Git blob/file записи в **четырёх репозиториях**, с Git SHA, размером, путём, exact source SHA; 126 пересекающихся путей Smoke-strategy/Terminal, 121 identical Git SHA. Это снимок **конкретного commit/ref каждого репозитория**, не diff всех branches.
2. [00B_MACHINE_BRANCH_HEADS.json](00B_MACHINE_BRANCH_HEADS.json) — **143 обнаруженных Git branch heads** (EMBER 31, Smoke-strategy 20, Terminal 91, Telegram bot 1); SHA каждой ветки и явное `has_verified_every_branch_content:false`.
3. [01_TECHNICAL_AUDIT_AND_REUSE_MATRIX_RU.md](01_TECHNICAL_AUDIT_AND_REUSE_MATRIX_RU.md) — модули A/REUSE, B/REPAIR, C/REFERENCE, X/ARCHIVE, ?/REVERIFY, сильные инженерные контракты, причины неудач C93–C117, подтверждённые различия GitHub/AppDeploy, что нельзя использовать как live signal.
4. [02_EXTERNAL_RESEARCH_HYPOTHESES_AND_DATA_FEASIBILITY_RU.md](02_EXTERNAL_RESEARCH_HYPOTHESES_AND_DATA_FEASIBILITY_RU.md) — исследование публикаций 2014–2026, официальных API Binance/Bybit и исторического data coverage, 7 кандидатов со сравнением и falsifiable H1/H2.
5. [03_DECISION_AND_NEXT_CYCLES_RU.md](03_DECISION_AND_NEXT_CYCLES_RU.md) — управленческое решение, H1 funding/basis первым **исследовательским** пилотом, H2 forced-flow после проверки OI истории, конкретная очередь RESET-00 … RESET-10, критерии быстрых STOP и цена ошибки.
6. [../../scripts/reboot_inventory_contract_test.py](../../scripts/reboot_inventory_contract_test.py) — 10 тестов источников инвентаризации (не тестов торговых правил), Python3.10/3.11/3.12.
7. [../../.github/workflows/ember-reset-4repo-inventory-ci.yml](../../.github/workflows/ember-reset-4repo-inventory-ci.yml) — автоматическая проверка источников реестра, неизменности A181 audit chain, тестов и наличия отчётов.

## Откуда брали факты

- Точный GitHub деревьев на 2026-10-30, branch/commit SHA закреплены в машинном JSON, включая альтернативные ветки в отдельном JSON.
- Содержимое корневых README/PROJECT_STATUS каждого репозитория, EMBER C117 corrected A181 full report, исходные `c105`, `c114`, `c116`, `c117` и `auditlog.py`.
- Read-only AppDeploy app/status: `smoke-trading-terminal-0kl792` snapshot `1792085859614`, QA ready, а также HTTP 451 / aborted market fetch в фактических logs. **Ready != reliable OHLCV.**
- Google Drive [старый полный атлас 12.10.2026](https://docs.google.com/document/d/1zobqNAuGRjgOt7-cPW6GQR2HSzsxYGRQAPpMfrpk0OA/edit), [V2.2 analysis](https://docs.google.com/document/d/1oXYpyiSXsLmgbgzDb9EMI0FsyUD8V46-4sb-OPMwOJ8/edit), [CryptoX screenshots study](https://docs.google.com/document/d/1HGuHlnTYsy7kOIcD2jTeBUi-iIp1TWp2wvfit4ZcVCg/edit) и метаданные текущего PAPER журнала. **Не** прочитано полное содержимое всех возможных файлов Drive; старый атлас неполный для даты 30.10.
- Внешние доступные официальные source docs, научные journal abstracts и 2026 working papers с явным различением гипотез и доказанной собственной прибыльности.

## Фактический статус работы

- `RESET-00` — **DONE** Git 4-repo full file manifest, 143 branch HEAD pointers.
- `RESET-01` — **DONE первичный сравнительный/выборочный аудит**, **не DONE** полная экспертиза 143 веток, всех 2189 файлов, AppDeploy snapshot или Drive.
- `RESET-02` — **DONE выборка проверяемых гипотез и источников**, НЕ systematic literature review и НЕ data-availability test за 2025 у Bybit.
- `RESET-03` — **критерий DONE только после green regression CI**, 10 тестов × Python3.10/3.11/3.12.
- `RESET-04 … RESET-10` — **OPEN/BLOCKED**: разработка общей платформы и новая реальная alpha **не** выполнены.
- LIVE trading and irreversible writes: **BLOCKED**.

**Приёмка:** никакой следующий чат не должен писать «всё проверено», не показав точные SHA проверенных веток и CI; не должен показывать H1/H2 как доходные без настоящего OOS + placebo. Возможность использовать код отдельно от profit evidence есть, но это не одно и то же.
