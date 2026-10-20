# EMBER — единый документ контроля разработки и передачи между чатами

**Создан:** 20 октября 2026 · **Статус:** действующий рабочий документ; продолжать заполнять в КАЖДОМ следующем чате.  
**Репозиторий:** https://github.com/SanChi117/EMBER-Research-Engine  
**Ветка:** `research/academic-engine-recovery-20261015`  
**Режим:** `PAPER ONLY / NOT_TRADE_READY`; реальные ордера, подключение ключей для торговли, расчёт авторских заполнений по 3m OHLC запрещены.

## 1. Три обязательных постоянных источника правды

1. **Этот документ:** `EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md` — читаемая инструкция, актуальный этап, шаги разработки, блокеры и ссылки. **Обновлять ПОСЛЕ КАЖДОГО сделанного шага**, а не только в конце чата. Технические действия, ожидающие тестов, записывать как `[~]`, ошибки как `[!]`, полностью независимо подтверждённые как `[x]`.
2. **Общая карта:** `ACADEMIC_ENGINE_CURRENT_MAP.md` — 40 укрупнённых пунктов, смысл каждого `[x]`/ `[~]` и внешние CI. К моменту C34: **29 завершены, 3 частично, 8 в ожидании**. Это количество пунктов, **не оценка готовности торговой системы**.
3. **Неизменяемый журнал действий:** `research/mtf-element-audit-v1/ЖУРНАЛ_ДЕЙСТВИЙ.jsonl`; **A001–A104 (104/104)** независимо проверены, tip A104 `741e2ef71ec6f7095001d5161e6d59801af41cb86e42eccd109618a34045f5b4`. Каждый `A105+` создавать **строго append-once** с SHA-шестёркой / source hash через `research/mtf-element-audit-v1/tools/auditlog.py record` после независимой CI; старые записи и зарегистрированные доказательства **не изменять**. Проверять `auditlog.py verify` и `tests/test_journal_integrity.py`, затем отдельная независимая CI.

**Никогда не заменять** проверенные исходные данные кодом-имитацией и не называть исследовательские наблюдения `READY`. Ошибка или непрошедший шаг **фиксируются в этом документе** и diagnostics Github, а не скрываются.

## 2. Точка продолжения

**Последний завершённый исследовательский цикл — C34 / A104:** [Независимая CI №39459245566](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39459245566) **SUCCESS**, **104/104 SHA**, четыре новых source-evidence byte hashes и **38** source-negative BOS тестов. [Независимая Python 3.10/3.11/3.12 CI №39458705426](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39458705426) SUCCESS по **38 тестов на каждую версию**. Каноническая запись A104 SHA `741e2ef71ec6f7095001d5161e6d59801af41cb86e42eccd109618a34045f5b4`, финальный witness Git blob `fd9c406712eea68ad49372a1822b80fac3645c9b`.

**Что C34 действительно завершил:** первичный реестр источников (уроки BOS/IMB-SNR/IDM/liquidity/context и screenshots), строгие исходные отрицательные условия — BOS должен быть ниже BSL рейда или выше SSL, настоящий wick рейд, наличие 3m BOS/адекватной цели, первая FTA не должна нарушать RR, SL за ликвидностью. Модуль `d05/c34_author_bos_text_negative_gate.py` моделирует только условные **отказы**, а не обнаружение рыночных сигналов; все сценарии `NOT_TRADE_READY`, **0 одобренных сделок и 0 ордеров**. 15 FX pips, IANA timezone, tick fill, точная цена лимитки и авторский 3m pivot НЕ выдуманы.

**Главная блокировка сохраняется:** original [Notion 1H/3m BackTest 2023](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21) недоступен; в Drive и скриншотах нет пары *авторский выбранный 3m swing → символ, дата, уровень, подтверждение*. C33 original 45 ZIP source показывает **539/539** технически неоднозначных BOS / **5285** доступных заранее 3m swing links. Полный исходный C33 Git blob `fa17524a942d8227e8ec33e3d1e2c93c860669df` **НЕ ИЗМЕНЁН** в C34, новых ZIP или рыночных бэктестов C34 не запускал.

**Текущий пункт карты:** B1 [~], D05 [~], всего **29/40 крупных пунктов**. C34 [x] **только как проверка негативных правил курса**, НЕ завершённая академическая система. **Следующий C35 [~]:** либо обнаружить настоящий source-labelled BOS pivot на доступном первоисточнике и построить source-to-case золотой протокол, либо документально сохранить блокер `NEEDS_AUTHOR_BOS_GOLDENS` и заняться другими независимыми PAPER-компонентами без изобретения алгоритма выбора свинга.

**Предыдущий C33 / A103:** независимая [CI 39455752782](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39455752782) SUCCESS: 103/103 SHA, 45 USD-M ZIP, 539 cases/5285 candidate swing relationships, no author selection. **C32 / A102:** два source-only пути BOS first-wick vs close-then-unknown-limit, 0 ордеров.

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
| **C35 [~]** | source gap авторского 3m swing + связка reaction/FTA/SL без самовольной эвристики | `NEEDS_AUTHOR_BOS_GOLDENS`; другой независимый PAPER-компонент возможен |

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

### C35 — следующая точка

- **C35-S00 [~]** — Проблема: C21 `latest preknown strict 3m pivot` — только техническая эвристика. По 539 cases источник допускает 5285 swing relations; первичный авторский selected swing отсутствует. Продолжить поиск **конкретных** author-positive/negative 1H/3m cases, не применять публичные аналоги как goldens.
- **C35-S00a [~]** — Проверена доступность встроенной в авторский урок BOS картинки: внешняя S3-ссылка на иллюстрацию 3M BOS не открылась; пиксели этой диаграммы и авторские метки уровня не прочитаны. **Критический контроль периода:** авторский недоступный BackTest датирован январём–июлем **2023**, тогда как ранее проверенные C33 45 ZIP/Binance USD-M и 5 285 связей swing относятся к сентябрю–октябрю **2026**. Нельзя сопоставлять авторский пример 2023 напрямую с ценовыми событиями 2026. Если удастся получить авторский кейс, сначала определить реальный инструмент/рынок/провайдера/часовой пояс и только потом искать соответствующую **2023** историю. Никакого нового A105 или изменения старой проверки в этом шаге.
- **C35-S01a [~]** — 2026-10-20: повторён поиск Google Drive по `BackTest 1H`, `2023.01`, `2023.07`, `BOS 2023`, `1H3M`, `1H 3M`: ссылка на авторский 2023 Notion BackTest найдена только в курсовом `4. Entry By BOS.txt`; самостоятельный размеченный dataset не обнаружен. Прямая веб-страница Notion не доступна публичному чтению. Уточнены UTC окна: frozen C33 `2026-09-01..2026-10-03` (`d05/c16_c08_monthly_daily_htf_lineage.py`), название авторского курса `2023-01..2023-07`; **эти окна не пересекаются**. Создан `d05/c35_author_case_source_join_guard.py`, commit `b0e7a3fc`: проверяет источник и поля авторского примера, запрещает подставлять данные 2026 к примеру 2023 или выдавать анкетную строку за авторскую сделку. Пока только код **[~]**, тесты и CI ожидаются; старый A104 не изменён.
- **C35-S01 [ ]** — Сформировать строгую таблицу `ссылка / авторское изображение / тикер / год-месяц-число / timezone / 1H raid / 3m selected BOS / первый FTA / stop`; отсутствие полей явно `SOURCE_NOT_SHOWN`.
- **C35-S02 [ ]** — При отсутствии источника не выдавать очередной непроверенный «лучший» swing; развивать только отдельно аттестуемые элементы PAPER или искать формализованный авторский материал.
- **C35-S03 [ ]** — Следующий A105 только после отдельного полного теста/CI и независимой 105/105 SHA, никаких реальных заявок.

## 6. Правила перехода в следующий чат

Новый чат должен **без вводных гаданий**:
1. Прочитать этот документ по **ссылке ветки GitHub**, затем карту, затем последние записи `ЖУРНАЛ_ДЕЙСТВИЙ.jsonl`, последнее CI и Git branch HEAD.
2. Не начинать проект с нуля, не менять старые доказательства, не переписывать историю; восстанавливать точную точку C35-Sxx и продолжать незакрытый шаг C35.
3. Каждое реальное действие и неудачную проверку **сразу после выполнения** добавлять в раздел шагов этого документа, ставить правильный статус; **нет записи — действие для контроля чатов не засчитано**.
4. После каждого полного цикла опровергать собственные результаты с независимыми входами, проверять все SHA и физически усечённый source as-of.
5. В каждом ответе кратко показывать изменённые шаги `[x]/[~]/[!]`, CI и главную проблему, без неподтверждённых `READY`, “доходности” и реальных сделок.

## 7. Ссылки и управление версиями

- [Этот документ — текущая версия](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md).
- [Скачать текущий Markdown](https://raw.githubusercontent.com/SanChi117/EMBER-Research-Engine/research/academic-engine-recovery-20261015/EMBER_CROSS_CHAT_CONTROL_AND_HANDOFF.md).
- [Общая карта работ](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/ACADEMIC_ENGINE_CURRENT_MAP.md).
- [Неизменяемый JSONL журнал](https://raw.githubusercontent.com/SanChi117/EMBER-Research-Engine/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/%D0%96%D0%A3%D0%A0%D0%9D%D0%90%D0%9B_%D0%94%D0%95%D0%99%D0%A1%D0%A2%D0%92%D0%98%D0%99.jsonl).
- [Отчёт C34 с прямыми первоисточниками](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/academic-engine-recovery-20261015/research/mtf-element-audit-v1/cycles/B1_C34_AUTHOR_BOS_PRIMARY_SOURCE_NEGATIVE_RULE_AUDIT.md).

**Безопасность и граница проекта:** исследовательские данные и академическая корректность НЕ доказывают доходность, надёжность сигналов или готовность к торговле. `PAPER ONLY · NOT_TRADE_READY`.
