# EMBER — единый документ контроля разработки и передачи между чатами

**Создан:** 20 октября 2026 · **Статус:** действующий рабочий документ; продолжать заполнять в КАЖДОМ следующем чате.  
**Репозиторий:** https://github.com/SanChi117/EMBER-Research-Engine  
**Ветка:** `research/academic-engine-recovery-20261015`  
**Режим:** `PAPER ONLY / NOT_TRADE_READY`; реальные ордера, подключение ключей для торговли, расчёт авторских заполнений по 3m OHLC запрещены.

## 1. Три обязательных постоянных источника правды

1. **Этот документ:** `EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md` — читаемая инструкция, актуальный этап, шаги разработки, блокеры и ссылки. **Обновлять ПОСЛЕ КАЖДОГО сделанного шага**, а не только в конце чата. Технические действия, ожидающие тестов, записывать как `[~]`, ошибки как `[!]`, полностью независимо подтверждённые как `[x]`.
2. **Общая карта:** `ACADEMIC_ENGINE_CURRENT_MAP.md` — 40 укрупнённых пунктов, смысл каждого `[x]`/ `[~]` и внешние CI. К моменту C35: **29 завершены, 3 частично, 8 в ожидании**. Это количество пунктов, **не оценка готовности торговой системы**.
3. **Неизменяемый журнал действий:** `research/mtf-element-audit-v1/ЖУРНАЛ_ДЕЙСТВИЙ.jsonl`; **A001–A105 (105/105)** независимо проверены, tip A105 `a2fe39896fea78c95d532e6ff2c0c710f9ee8aabd876f2112c7f390c290247a5`. Каждый `A106+` создавать **строго append-once** с SHA-шестёркой / source hash через `research/mtf-element-audit-v1/tools/auditlog.py record` после независимой CI; старые записи и зарегистрированные доказательства **не изменять**. Проверять `auditlog.py verify` и `tests/test_journal_integrity.py`, затем отдельная независимая CI.

**Никогда не заменять** проверенные исходные данные кодом-имитацией и не называть исследовательские наблюдения `READY`. Ошибка или непрошедший шаг **фиксируются в этом документе** и diagnostics Github, а не скрываются.

## 2. Точка продолжения

**Последний независимо завершённый технический цикл — C35 / A105.** [CI №39476159123](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39476159123) **SUCCESS: 105/105** append-only source SHA records, пять новых source+test+registry+witness+report file hashes, 35 повторных негативных тестов. [Независимая C35 матрица №39475591964](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39475591964) **SUCCESS** — **35/35** тестов на Python **3.10, 3.11 и 3.12**, все четыре CI-jobs успешны. Tip **A105** `a2fe39896fea78c95d532e6ff2c0c710f9ee8aabd876f2112c7f390c290247a5`, финальный independent witness Git blob `c3dab532830083097b53ff5cd9a0f5f18bf27a76`. Рабочая карта обновлена commit `fdf191ff`.

**Что реально сделал C35:** повторно искал [оригинальный BackTest 1H/3M январь–июль 2023](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21) в интернете и подключённом Google Drive, но получил только ссылку из [курса 4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view). Авторские размеченные случаи, тикер, chart time-zone, дата и точный выбранный 3m swing НЕ получены. Проверено, что **только по заголовку** авторский период 2023-01—2023-07, а **доказанные исходные архивы C33** по Binance USD-M относятся к `2026-09-01 00:00 UTC — 2026-10-03 00:00 UTC` и эти периоды не пересекаются. C35 реализует **строгий metadata-only запрет** соединить чужие исторические случаи и выдавать произвольно заполненные поля за одобренный автором BOS. [Исходный реестр](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/evidence/c35/C35_SOURCE_ACCESS_GAP_REGISTRY.json) и `d05/c35_author_case_source_join_guard.py` сохранены; оригинальный C33 JSON Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df` **не менялся**. C35 **не запускал нового рыночного ZIP-бэктеста**, не создавал сделок и не нашёл авторский BOS.

**Главный блокер:** `NEEDS_AUTHOR_BOS_GOLDENS` — из C33 известны **539/539** исследовательских BOS с несколькими preknown pivot, 5 285 source swing relations, но **0 авторских размеченных положительных/отрицательных кейсов**. Восстановить точную механику выбора 3m BOS, SL/FTA и лимитку ПОКА НЕВОЗМОЖНО. `PAPER ONLY · NOT_TRADE_READY`.

**Текущая карта:** B1 [~], D05 [~], всего **29/40 крупных контрольных пунктов** без повышения. **Следующий C36 [~]** — исследовать следующий независимый академический элемент, который можно аттестовать по доступному исходному уроку без авторской разметки BOS (например, first trouble area, source-only FTA geometry), при обязательной первичной документации и негативных тестах. Если оригинальный авторский 2023 BackTest появится, вместо этого начать работу над отдельно подтверждённой **историей ТОГО ЖЕ инструмента и периода**, не сопоставлять с исходными свечами 2026.

**Предыдущие принятые этапы:** C34 / A104 — 38 strict BOS source-text negative checks и 104/104 SHA; C33 / A103 — оригинальные 45 ZIP, 539 research BOS, 5 285 source-known competing swings, 103/103 SHA. Ни один этап не получил `READY`.

## 3. Последовательность разработки, не менять произвольно

`Академические первоисточники → собственная формальная семантика каждого элемента → отрицательные тесты и тесты ас-of → воспроизводимые оригинальные USD-M ZIP → независимая CI и полное JSON-совпадение → append-only SHA-журнал → карта → этот документ → следующий цикл`.

**Ключевая блокировка:** авторский [BackTest 1H/3M Jan–Jul 2023](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21) недоступен пользователю и поиску; положительные/отрицательные размеченные примеры выбора *именно авторского* BOS swing, лимитного входа/FTA и SL не получены. **Нельзя** подставлять в качестве ground truth внешние ICT Silver Bullet / MSS / FVG модели, чужие скриншоты или выбранный моделью “правильный” pivot.

Стабильные исходники: Binance USD-M Futures **45 SHA-checked ZIP** по **BCH, BTC, ETH, SOL, XRP**; оригинальные 3m закрытые **76 800**; исходные Decimal-сверки 15m **15 360**; прежние C21B original research parents **539**, C24 singles **165**. Исследование **не означает бэктест сделок** и не позволяет выводить win rate, SL/TP.

## 4. Контрольная история уже принятых циклов

| Цикл | Что ДЕЙСТВИТЕЛЬНО подтверждено | Проверка/ограничение |
|---|---|---|
| C20–C25 | строгие исходные 1H и 3m источники, геометрия, parent/child и 165 research singleton | авторский BOS/FTA не присвоен |
| C26 / A096 | source technical first trouble area — предварительные 1H уровни | авторская FTA-приоритизация неизвестна |
| C27 / A097 | 1H EQ и session-source наблюдения | author timezone/DST и отбор не доказаны |
| C28 / A098 | 1H classic 3-candle IMB source | [CI 39124290984](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39124290984) 98/98 |
| C29 / A099 | RB и SNR *нельзя* доказать цветовой парой; 1 989 пар | [CI 39126166544](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39126166544) 99/99 |
| C30 / A100 | ранее известные 1H fractal wick raids/IMB wick-first tests | [CI 39164335165](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39164335165) 100/100 |
| C31 / A101 | 122/539 ранних wick reach до close, семантика отличается | [CI 39175901614](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39175901614) 101/101 |
| **C32 / A102** | **две типизированные ветви BOS**, ни одна не создаёт заявку | [CI 39300966067](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39300966067) 102/102 |
| **C33 / A103 [x]** | source-наблюдение всех допустимых заранее swing: 539/539 случаев с неоднозначностью, 5 285 связей | [CI 39455752782](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455752782) 103/103 SHA; НЕ авторский BOS |\n| **C34 / A104 [x]** | source-text BOS отрицательные правила и первичные Drive источники, но без авторского выбранного BOS pivot | [CI 39459245566](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39459245566) PASS 104/104; 38 synthetic negative tests×3 Python |
| **C35 / A105 [x]** | 2023 авторский источник vs 2026 USD-M: правила метаданных и запрет ложного сопоставления кейсов | [CI 39475591964](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39475591964) 35×3 PASS; [A105 CI 39476159123](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39476159123) 105/105 SHA; авторского BOS нет |
| **C36 [~]** | следующий независимый академический PAPER-элемент; без подмены авторских BOS goldens | не начинался, отдельная приёмка |

## 5. Журнал работ C33 и всех следующих шагов — ЗАПОЛНЯТЬ ПО ХОДУ

Формат каждой записи **один шаг = одна запись**:

`STEP ID / дата UTC / [ ] [~] [x] [!] / задача → реальное действие → изменённый файл+Git commit → выполненные тесты+CI → возражения/ошибки и их исход → степень доказанности → дальнейшее действие`.

Запись `[x]` допустима **только** при наличии конкретного независимого CI, immutable source и (где цикл завершён) SHA-журнала. Если есть только push кода или черновик, `[~]`, даже если код выглядит верным. Если тест провален, `[!]` до успешного повторного теста; запись об ошибке НЕ удалять.

### C33 — подтверждённые действия 20 октября 2026

- **C33-S00 [x]** — Создан единый живой документ для передачи между чатами, commit `26aec6d0`. Он дополняет карту и append-only SHA-журнал, не заменяет их.
- **C33-S01 [x]** — Исследован C21 `latest preknown 3m 1+1 swing` и сформулирован контролируемый вопрос: единственен ли этот swing. Исходные авторские примеры недоступны, правило latest нельзя утверждать как авторское.
- **C33-S02 [x]** — Создан `d05/c33_preknown_competing_bos_swings.py`, валидация первых 3m свечей источника и правой подтверждающей свечи. Коммиты `2ac6b213`, `c66ef2ee`. 27 adversarial тестов, в том числе future lookahead и оригинальные SHA.
- **C33-S02a [!] → [x]** — Первоначальная [CI 39454193235](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39454193235) упала на синтаксисе тестового Python: буквальное `\\n` в строке. Исправлен только тестовый исходник commit `64244cdd`. Повтор [CI 39454279240](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39454279240) **PASS 27/27**. Исходный FAIL оставлен в истории.
- **C33-S03 [x]** — `tests/probe_c33_original_competing_bos.py` (commit `a95ff1f0`) и оригинальная CI `mtf-c33-original-competing-45zip.yml` (commit `aea3be57`) подтвердили **539 research BOS / 5 285 swing links / 0 уникальных pivot событий** на 45 оригинальных SHA USD-M ZIP; зафиксирован полный JSON source `evidence/c33/C33_ORIGINAL_COMPETING_BOS_PIVOTS_SOURCE.json` Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df`. Никаких ордеров.
- **C33-S04 [x]** — Независимо перечитан полный 45 ZIP source и все 539 событий с **точным полным JSON равенством** и 27 тестами × Python 3.10/3.11/3.12; [CI 39455216429](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455216429) **SUCCESS**, witness Git blob `7c432fd16a554dfadd0536590aafa7c17610231d`.
- **C33-S05 [x]** — Append-only A103 (canonical SHA `a6df5a8510402c832454653b409abb2ce9d89d04b0d3b35dbf6026e3803bc1d8`), независимая [CI 39455752782](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455752782) **PASS 103/103 SHA**, шесть source evidence byte hashes, 45 original ZIP full JSON. Карта обновлена commit `b51c3756`, документ обновлён. **C33 [x] только как исходная исследовательская проверка**.

### C34 — 20 октября 2026, контроль каждого шага

- **C34-S00 [x]** — Исследованы исходные Google Drive уроки `4. Entry By BOS.txt`, IMB/SNR, IDM, liquidity, RB, TDA/context; просмотрены три сохранённых изображения 2102, 2092, 2093 и папки Entry Model Logic/BOS. Доказаны **источники негативных BOS-правил**, но не найдены timestamp+symbol+price метки авторского BOS swing. Оригинал Notion 2023 недоступен, не подменять другими ICT. Указано в `cycles/B1_C34_AUTHOR_BOS_PRIMARY_SOURCE_NEGATIVE_RULE_AUDIT.md`.
- **C34-S01 [x]** — Созданы `d05/c34_author_bos_text_negative_gate.py` (commit `2ebc6214`) и `d05/test_c34_author_bos_text_negative_gate.py` (commit `ea053838`), **38 негативных synthetic source-rule проверок** с запретом авторского READY и любых ордеров. Это НЕ проверка сигналов в market data.
- **C34-S02 [!] → [x]** — Первая [CI 39458131235](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39458131235) **FAIL ДО тестов**: `git rev-parse HEAD:` использовал неверный относительный путь, тесты `SKIPPED`. Диагностика `evidence/c34/diagnostics/C34_AUTHOR_BOS_NEGATIVES.json` сохранена. Путь исправлен commit `68f3d56b`; повторная независимая [CI 39458705426](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39458705426) **PASS 38/38 × Python 3.10/3.11/3.12**, все 4 jobs successful. История первичного FAIL не удалена.
- **C34-S03 [x]** — Выполнена академическая матрица проверенных источников `cycles/B1_C34_AUTHOR_BOS_PRIMARY_SOURCE_NEGATIVE_RULE_AUDIT.md` (commits `1f5fd4b5`, `aedc772e`); положительные goldens **0**, точный выбор авторского pivot не восстановлен.
- **C34-S04 [x]** — Зафиксирован независимый witness `evidence/c34/C34_INDEPENDENT_SOURCE_NEGATIVE_WITNESS.json` Git blob `f56fe16d514b0f9caeb03b483d8a905bf719fb90`, CI `39458705426`. Предыдущее A103 103/103 и original C33 market source blob `fa17524a942d8227e8ec33e3d1e2c93c860669df` проверены неизменными; в C34 **0 новых 45 ZIP market rereads**.
- **C34-S05 [x]** — Добавлена единственная append-only запись **A104** с 4 source evidence SHA, tip `741e2ef71ec6f7095001d5161e6d59801af41cb86e42eccd109618a34045f5b4`. [CI 39459245566](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39459245566) **SUCCESS 104/104**, bytes validated. Карта обновлена commit `69146941`. НИКАКОЙ авторский BOS pivot, тик-entry, лимитка, RR, SL или доходность не выведены.
- **C34-S06 [x]** — Текущий единый документ передачи обновлён; основной B1, D05 остаются [~], 29/40 неизменно. Следующий чат продолжать с C35.

### C35 — подтверждённые действия 20 октября 2026

- **C35-S00 [x] (только доступность источника)** — Повторный поиск Drive по `BackTest 1H`, `2023.01`, `2023.07`, `1H3M`, `BOS 2023` и попытка открыть Notion: выявлена лишь ссылка в первичном уроке BOS, оригинальный 2023 positive/negative кейс НЕ найден. Код доступа/разметка не выдумывались.
- **C35-S01 [x]** — Точное техническое расхождение: заголовок курса `2023 Jan–Jul`, проверенный C33 `2026-09-01..2026-10-03 UTC`. Реестр `evidence/c35/C35_SOURCE_ACCESS_GAP_REGISTRY.json` (commit `fad3ace4`) перечисляет `SOURCE_NOT_SHOWN`: авторский ярлык/тикер/провайдер/часовой пояс, 1H raid и выбранный 3m swing/FTA/SL. Отчёт `cycles/B1_C35_2023_AUTHOR_VS_2026_C33_SOURCE_JOIN_REPORT.md` (commit `fec3ba01`, окончательно pinned blob `ccf9ae39a770c402df1c621ee91d7d73a5914c16`).
- **C35-S02 [!] → [x]** — Изначально **два Python-файла** были случайно созданы на default вместо ветки research из-за неуказанного `branch`: module commit `b0e7a3fc`, test commit `845763c2`. Оба восстановлены в research коммитами `e8b1cb65` и `dea39bcc`; обе случайные записи на default отменены коммитами `592f0b8b` и `31926f9e`. [Первый CI 39474797141](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39474797141) **FAIL**: `ModuleNotFoundError` до тестов. Историю неудачи сохранить.
- **C35-S03 [!] → [x]** — [Второй CI 39475425258](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39475425258): все 35 тестов выполнились, но 2 FAIL по регистру диагностического имени поля `C35_INVALID_...`. Исправлен **только формат ошибки**, без ослабления проверки, commit `109ef7c1`. Третий [CI 39475591964](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39475591964) **SUCCESS 35/35 × Python 3.10/3.11/3.12**. Frozen independent witness Git blob `4f793de037978f73bd2e4b61cae858a4757ea04a`.
- **C35-S04 [x]** — Неизменяемый append-only журнал получил запись **A105**, canonical SHA `a2fe39896fea78c95d532e6ff2c0c710f9ee8aabd876f2112c7f390c290247a5`, **пять новых SHA доказательных файлов**. [Независимая CI 39476159123](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39476159123) **SUCCESS**: 105/105 SHA, 5/5 bytes, 35 tests; final witness blob `c3dab532830083097b53ff5cd9a0f5f18bf27a76`.
- **C35-S05 [x]** — Карта обновлена commit `fdf191ff`, этот контрольный документ обновлён. Нет новых original ZIP, 0 author goldens, 0 ордеров, 0 сделок. C35 `[x]` **ТОЛЬКО** в области gate происхождения, NOT_TRADE_READY.

### C36 — следующая точка (не выполнена)

- **C36-S00 [~]** — Перейти от заблокированного авторского BOS к отдельному source-attested академическому элементу (например, first trouble area), предварительно прочитать исходный урок и не импортировать самостоятельно выбранные схемы.
- **C36-S01 [ ]** — Проверить возможность автора описать positive/negative определение элемента по первоисточнику; прочитать старые C26/C28 источники для отсутствия дубликата, найти новую непротестированную часть.
- **C36-S02 [ ]** — Негативные проверки/исходные данные и только после независимой CI записать A106, проверить 106/106 SHA. Без одобрения торговых сделок.
- **C36-S03 [ ]** — Если появится исходный 2023 Notion, провести отдельную верификацию instrument/provider/timezone/2023 actual data и выбранного автором swing; 2026 C33 — не тот же backtest.

## 6. Правила перехода в следующий чат

Новый чат должен **без вводных гаданий**:
1. Прочитать этот документ по **ссылке ветки GitHub**, затем карту, затем последние записи `ЖУРНАЛ_ДЕЙСТВИЙ.jsonl`, последнее CI и Git branch HEAD.
2. Не начинать проект с нуля, не менять старые доказательства, не переписывать историю; восстанавливать точную точку C36-Sxx и продолжать незакрытый шаг C36.
3. Каждое реальное действие и неудачную проверку **сразу после выполнения** добавлять в раздел шагов этого документа, ставить правильный статус; **нет записи — действие для контроля чатов не засчитано**.
4. После каждого полного цикла опровергать собственные результаты с независимыми входами, проверять все SHA и физически усечённый source as-of.
5. В каждом ответе кратко показывать изменённые шаги `[x]/[~]/[!]`, CI и главную проблему, без неподтверждённых `READY`, “доходности” и реальных сделок.

## 7. Ссылки и управление версиями

- [Этот документ — текущая версия](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md).
- [Скачать текущий Markdown](https://raw.githubusercontent.com/SanChi117/EMBER-Research-Engine/research/academic-engine-recovery-20261015/EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md).
- [Общая карта работ](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/ACADEMIC_ENGINE_CURRENT_MAP.md).
- [Неизменяемый JSONL журнал](https://raw.githubusercontent.com/SanChi117/EMBER-Research-Engine/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/%D0%96%D0%A3%D0%A0%D0%9D%D0%90%D0%9B_%D0%94%D0%95%D0%99%D0%A1%D0%A2%D0%92%D0%98%D0%99.jsonl).
- [Отчёт C35 по источникам и несовпадающим периодам](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/cycles/B1_C35_2023_AUTHOR_VS_2026_C33_SOURCE_JOIN_REPORT.md).

**Безопасность и граница проекта:** исследовательские данные и академическая корректность НЕ доказывают доходность, надёжность сигналов или готовность к торговле. `PAPER ONLY · NOT_TRADE_READY`.
