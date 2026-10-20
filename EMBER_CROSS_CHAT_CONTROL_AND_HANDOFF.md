# EMBER — единый документ контроля разработки и передачи между чатами

**Создан:** 20 октября 2026 · **Статус:** действующий рабочий документ; продолжать заполнять в КАЖДОМ следующем чате.  
**Репозиторий:** https://github.com/SanChi117/EMBER-Research-Engine  
**Ветка:** `research/academic-engine-recovery-20261015`  
**Режим:** `PAPER ONLY / NOT_TRADE_READY`; реальные ордера, подключение ключей для торговли, расчёт авторских заполнений по 3m OHLC запрещены.

## 1. Три обязательных постоянных источника правды

1. **Этот документ:** `EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md` — читаемая инструкция, актуальный этап, шаги разработки, блокеры и ссылки. **Обновлять ПОСЛЕ КАЖДОГО сделанного шага**, а не только в конце чата. Технические действия, ожидающие тестов, записывать как `[~]`, ошибки как `[!]`, полностью независимо подтверждённые как `[x]`.
2. **Общая карта:** `ACADEMIC_ENGINE_CURRENT_MAP.md` — 40 укрупнённых пунктов, смысл каждого `[x]`/ `[~]` и внешние CI. К моменту C32: **29 завершены, 3 частично, 8 в ожидании**. Это количество пунктов, **не оценка готовности торговой системы**.
3. **Неизменяемый журнал действий:** `research/mtf-element-audit-v1/ЖУРНАЛ_ДЕЙСТВИЙ.jsonl`; **A001–A103 (103/103)** независимо проверены, tip A103 `a6df5a8510402c832454653b409abb2ce9d89d04b0d3b35dbf6026e3803bc1d8`. Каждый `A104+` создавать **строго append-once** с SHA-шестёркой / source hash через `research/mtf-element-audit-v1/tools/auditlog.py record` после независимой CI; старые записи и зарегистрированные доказательства **не изменять**. Проверять `auditlog.py verify` и `tests/test_journal_integrity.py`, затем отдельная независимая CI.

**Никогда не заменять** проверенные исходные данные кодом-имитацией и не называть исследовательские наблюдения `READY`. Ошибка или непрошедший шаг **фиксируются в этом документе** и diagnostics Github, а не скрываются.

## 2. Точка продолжения

**Завершено и независимо подтверждено — C33 / A103:** [CI №39455752782](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455752782) **SUCCESS**, **103/103 SHA**, шесть новых доказательных файлов, полный повтор **45 оригинальных** USD-M ZIP и всего JSON по 539 исследовательским BOS. Дополнительная [C33 CI №39455216429](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455216429) **SUCCESS** — 27 негативных тестов на каждой из Python 3.10/3.11/3.12 + равенство полного JSON. Исходный C33 source Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df`, independent witness `7c432fd16a554dfadd0536590aafa7c17610231d`, canonical A103 SHA `a6df5a8510402c832454653b409abb2ce9d89d04b0d3b35dbf6026e3803bc1d8`.

**Доказанный технический результат:** все **539/539** оригинальных C21 research BOS имели **более одного** заранее подтверждённого строгого 1+1 3m swing; **5 285** связей BOS↔технически доступный swing; максимум **18**. **Ни один** из них автором не размечен как выбранный BOS. Алгоритм C21 `latest preknown strict swing` восстановлен технически, но НЕ доказан как требование академии. **0 сделок, 0 ордеров, PAPER ONLY · NOT_TRADE_READY**.

**Следующий этап — C34 [~] / источник авторского выбора BOS:** найти точные positive/negative примеры и условия выбора swing именно у автора, начиная с доступных оригинальных Drive-уроков, и составить таблицу `авторское доказательство → выбранный swing → время закрытия 3m → FTA/SL`. Недоступную Notion-страницу `BackTest 1H/3M 2023` НЕ подменять внешними ICT-правилами. Если нужных примеров нет, честно фиксировать `NEEDS_AUTHOR_BOS_GOLDENS`, не назначать случайный BOS.

**Предыдущее C32 / A102:** 102/102 SHA, два изолированных source-only маршрута: MARKET_AT_BOS_CROSS и CLOSE_THEN_LIMIT, оба **без исполняемых заявок**. Из 539 C21 proxy events 122 ранние свечные тени достигали BOS до следующего закрытия; tick/order book/fill не восстановлены по 3m OHLC.

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
| **C33 / A103 [x]** | source-наблюдение всех допустимых заранее swing: 539/539 случаев с неоднозначностью, 5 285 связей | [CI 39455752782](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455752782) 103/103 SHA; НЕ авторский BOS |\n| **C34 [~]** | поиск авторских положительных/отрицательных BOS goldens и точных FTA/SL | источник не найден; нельзя подменять сторонней моделью |

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

### C34 — дальнейшая работа

- **C34-S00 [~]** — Инвентаризация оставшейся первичной академической разметки BOS, FTA, SL. Notion 2023 original недоступен; в доступных Drive-уроках нужно искать конкретную инструкцию выбора pivot, а не строить новые неназванные модели.
- **C34-S00a [~]** — 2026-10-20: выполнен повторный поиск Google Drive по `BOS`, `Entry`, `Fractal`, `BackTest`, `Break Of Structure`, `рейд`. Прочитаны оригинальные `4. Entry By BOS.txt`, `2. Entry by IMB & SNR.txt`, `3. Entry by Inducement [IDM].txt`, `ликвидность.txt`, `3. Rejection Block.txt`, context/TDA. Осмотрены архивные папки `4. Entry By BOS` и `Entry Model Logic`, изображения `Снимок экрана (2102).png`, `(2092).png`, `(2093).png`. BOS-скриншот показывает текст академии, остальные — примеры другого входа IMB/SNR: они НЕ содержат проверяемого `symbol/date/price` выбранного BOS 3m. Исходный Notion BackTest 2023 по-прежнему недоступен. **Вывод `[~]`:** имеются авторские отрицательные правила (нет рейда, BOS, нормальной цели, неверная сторона BOS); алгоритма выбора pivot и author-positive labels нет. Начать отдельную негативную source gate без выдумывания авторских входов.
- **C34-S01 [ ]** — Source-to-author-golden таблица с примерами выбранного swing и явно отрицательными кейсами; если исходников нет, задокументировать блокер `NEEDS_AUTHOR_BOS_GOLDENS`.
- **C34-S01a [~]** — 2026-10-20: созданы отдельные чистые функции `d05/c34_author_bos_text_negative_gate.py` (commit `2ebc6214`) и `d05/test_c34_author_bos_text_negative_gate.py` (commit `ea053838`): **38** source-negatives из прямого урока `4. Entry By BOS.txt` — отсутствие wick-рейда, отсутствующий 3M BOS/цель, FTA с неудовлетворительным RR, неверная сторона BOS относительно 1H SSL/BSL, SL не за снятой ликвидностью. Все синтетические посылки не являются наблюдениями рынка и **не допускают** author-positive, market/limit fill, READY. Перенос правила 15 pips на криптовалюту запрещён. Тестовая CI пока не завершена, шаг `[~]`.
- **C34-S01b [!] → [~]** — Первый CI [39458131235](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39458131235) **FAIL до тестов**: SHA Git source проверялся по `HEAD:evidence/...` вместо полного пути от корня. Старые 103/103 проверены, тесты были `SKIPPED`. Ошибка сохранена в `evidence/c34/diagnostics/C34_AUTHOR_BOS_NEGATIVES.json`, Git SHA workflow исправлен commit `68f3d56b`, первоначальный FAIL не скрывать.
- **C34-S01c [~]** — Создан академический source-review `cycles/B1_C34_AUTHOR_BOS_PRIMARY_SOURCE_NEGATIVE_RULE_AUDIT.md` (commit `1f5fd4b5`) и независимая 38-test×Python 3.10/3.11/3.12 CI `.github/workflows/mtf-c34-independent-source-negatives.yml` (commit `50d8ec6c`), без нового 45-ZIP replay, поскольку рыночные сигналы C34 не создаёт. Результат ожидается.
- **C34-S02 [ ]** — Только после найденных авторских case labels: сравнить их с 5 285 доступными исходными technical swing и разделить авторский выбор/предположение.
- **C34-S03 [ ]** — Никакого A104, READY, TP/SL или ордеров до тестов и доказательств.

## 6. Правила перехода в следующий чат

Новый чат должен **без вводных гаданий**:
1. Прочитать этот документ по **ссылке ветки GitHub**, затем карту, затем последние записи `ЖУРНАЛ_ДЕЙСТВИЙ.jsonl`, последнее CI и Git branch HEAD.
2. Не начинать проект с нуля, не менять старые доказательства, не переписывать историю; восстанавливать точную точку C34-Sxx и продолжать незакрытый шаг C34.
3. Каждое реальное действие и неудачную проверку **сразу после выполнения** добавлять в раздел шагов этого документа, ставить правильный статус; **нет записи — действие для контроля чатов не засчитано**.
4. После каждого полного цикла опровергать собственные результаты с независимыми входами, проверять все SHA и физически усечённый source as-of.
5. В каждом ответе кратко показывать изменённые шаги `[x]/[~]/[!]`, CI и главную проблему, без неподтверждённых `READY`, “доходности” и реальных сделок.

## 7. Ссылки и управление версиями

- [Этот документ — текущая версия](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md).
- [Скачать текущий Markdown](https://raw.githubusercontent.com/SanChi117/EMBER-Research-Engine/research/academic-engine-recovery-20261015/EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md).
- [Общая карта работ](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/ACADEMIC_ENGINE_CURRENT_MAP.md).
- [Неизменяемый JSONL журнал](https://raw.githubusercontent.com/SanChi117/EMBER-Research-Engine/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/%D0%96%D0%A3%D0%A0%D0%9D%D0%90%D0%9B_%D0%94%D0%95%D0%99%D0%A1%D0%A2%D0%92%D0%98%D0%99.jsonl).
- [ТЗ C33](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/cycles/B1_C33_COMPETING_PREKNOWN_3M_BOS_SWING_SOURCE_DRAFT.md).

**Безопасность и граница проекта:** исследовательские данные и академическая корректность НЕ доказывают доходность, надёжность сигналов или готовность к торговле. `PAPER ONLY · NOT_TRADE_READY`.
