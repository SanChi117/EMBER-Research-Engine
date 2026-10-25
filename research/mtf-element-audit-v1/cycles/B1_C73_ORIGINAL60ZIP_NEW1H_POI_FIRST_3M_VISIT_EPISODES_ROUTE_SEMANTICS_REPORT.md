# C73 — первая физическая 3m-проверка новой 1H POI: отдельные source-визиты и запрет подмены Trigger/VC

**25.10.2026 UTC.** Репозиторий `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`. **PAPER ONLY / NOT_TRADE_READY / trades=0.**

## 1. Оригинальная академия и ограничение интерпретации

Из Google Drive пользователя прочитаны непосредственно:

- `POI.txt`, ID `1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R`: POI — зона support/resistance; сильная POI работает с SSL/BSL или FVG. **Контакт ценой сам по себе не означает правильную авторскую POI или Volume Confirmation.**
- `2. Entry by IMB & SNR.txt`, ID `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ`: `Daily POI or Liquidity → 4H VC [IMB,SNR,RB]`, обязательный тест 4H/1H POI; при наличии 15m Trigger `SSL/BSL/eligible IMB` после теста **1H POI** ждать **5m VC [IMB,SNR]**. При отсутствии 15m Trigger — ждать **15m VC [IMB,SNR]**, а не произвольно переводить 15m source IMB/SNR в триггер.
- `Strong High & Low.txt`, ID `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`: только реальный контакт с liquidity **ИЛИ** inefficiency, **ЗАТЕМ** реальная VC POI/BOS same/lower TF подтверждает StrongHL. Source wick/technical pivot не даёт авторский SL.

**Критическое ограничение:** в найденных материалах отсутствуют author-labelled положительные и отрицательные Binance crypto `symbol+timestamp+source ZIP SHA` first VALID POI tests/VC/BOS/StrongHL. Из course-примеров нельзя получать недоказанную высокую уверенность, винрейт или торговые ордера.

## 2. Реализовано

- [x] Новый независимый `d05/c73_new1h_poi_original3m_visit_episodes_route_split.py` поверх **НЕИЗМЕННЫХ** C67/C69/C70/C71/C72. Для каждого оригинального source candidate он **сам повторно пересчитывает C71** из genuine original3m+original15m+original1h price/raw ID/time и **сам повторно пересчитывает C72** из genuine original5m events. Поддельные 1H POI parent, 3m price, 15m chronology, fake 5m confirmation или ручное включение author flags отвергаются.
- [x] Первое физическое original3m wick-overlap новой 1H POI проверяется по **всем предыдущим original3m raw барам после полного закрытия 1H POI**, а не только по одному выбранному 15m или 3m. Если был более ранний контакт — запись `FIRST` запрещена. Никакой lookahead.
- [x] Истинное техническое повторное посещение — **отдельный непрерывный эпизод**: один/много подряд raw3m candles, чьи тени пересекают POI, = **одно** source-посещение. Чтобы зачесть следующее, между ними должна оказаться **минимум одна полностью закрытая 3m свеча целиком ВНЕ POI**. Повторные свечи внутри зоны не накручивают «тесты».
- [x] Время измерения source visit episodes заканчивается строго **ДО НАЧАЛА** последующего C71 исходного 15m pattern, чтобы не использовать его движение для ретроактивной оценки первого POI-теста. Source continuous/revisit = **факт поведения цены**, но **не авторский valid/invalid POI test**. Если C71 next 15m event opposite, mixed, отсутствует или source POI никогда не достигнута — маршрут на 5m не повышается; Route A 15m Trigger и 15m VC остаются **UNRESOLVED**.
- [x] Source Route B IDM и Route C liquidity raid→3m/5m BOS не изменялись, aucune orders/stop/TP/PnL.
- [x] **30 adversarial negative тестов × Python3.10/3.11/3.12**: first raw contact vs forged first source ID; 1 непрерывный визит vs 2 с полной 3m свечой снаружи; author first valid/15m Trigger/15m VC/5m VC spoof; false child orders, opposite 15m, simultaneous 15m kinds, no new 1h POI/never first3m, incomplete downstream source, 5m raw ID tamper, parent cross-symbol, no trading. [CI 40230696413](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40230696413) **SUCCESS 3/3**.

## 3. Полная исходная крипто-сверка без подгонки

- [x] `tests/probe_c73_original60zip_new1h_poi_3m_visits_semantic_split.py`: **60 подлинных Binance USD-M ZIP × 2 независимых ПОЛНЫХ скачивания**, 5 монет BTC/ETH/SOL/XRP/BCH, 2026-09-01—2026-10-02: **76800 original3m, 46080 original5m, 15360 original15m, 160 original1d, 3840 derived1h**. Every **3 original5m = original15m Decimal OHLCV, 15360/15360**. Все 153 frozen C46 original 4H technical parents, C60 C62 C63 C66 C67 C68 C69 C70 C71 C72 source prices/timestamps/SHA идентификаторы независимо пересчитаны и совпали. Binance `*.CHECKSUM` выдаётся **тем же сайтом**, это **не внешняя независимая криптографическая подпись**.
- [x] Первый full original60 [CI 40230881038](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40230881038) **SUCCESS 5/5**; второй заново скачал все оригинальные 60 ZIP и сравнил целиком исходный JSON **побайтно** [CI 40231128409](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40231128409) **SUCCESS 4/4**.
- [x] Замороженный source `evidence/c73/C73_ORIGINAL60ZIP_FIRST_SOURCE_1H_POI_NATIVE3M_VISIT_EPISODES_ROUTE_SPLIT.json`: **303327 байт**, SHA256 `c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b`, Git blob `65db9aeaddaa58612bb4c743227cc9d28894cc31`. Отдельный witness `evidence/c73/C73_INDEPENDENT_ORIGINAL60ZIP_FIRST_NEW1H_POI_VISIT_WITNESS_20261025.json`.

### Результаты из 153 исходных технических 4H source-контекстов

| Классификация по ценам оригинальных 3m и последующей 15m-цепочке | Случаев |
|---|---:|
| Не ветка новой 1H POI | **47** |
| Техническая новая 1H POI без первого original3m касания | **71** |
| Было source-касание, но нет однозначной C71 15m-цепочки | **23** |
| C71 15m technical pattern, до него лишь **1 непрерывный source-визит** | **9** |
| C71 15m technical pattern, до него уже **повторный отдельный source-визит** | **3** |
| **Всего** | **153** |

**12** случаев технической 15m-цепочки после новой 1H POI: **9 один визит, 3 повторных**; это **не** 12 независимых входов и не 12 авторски подтверждённых 1H first VALID POI tests. Взгляд на исходные real3m price wick показал разницу между `FIRST source visit` и `additional technical return`; эти source status **НЕ** дают знания, какая свеча правильная для академического теста, SL, Trigger, VC или 5m входа. Все owner-valid flags **false**, ордера ноль, PnL отсутствует.

## 4. Что осталось после C73

Главная семантическая неопределённость **не решается перебором свечей**: 1H POI должна быть реальной VC после родительской 4H POI, которую преподаватель счёл действительной. Нужны настоящие положительные/отрицательные авторские примеры по крипте для определения valid/invalid first POI test, что такое 15m SSL/BSL/eligible IMB Trigger именно в этом контексте, что такое 15m VC без Trigger, когда есть настоящая 5m VC. Ранее найденные 4 source-паттерна 5m C72 не стали торговыми сигналами. После семантических goldens: правильные StrongHL и структурные SL/FTA/TP, независимый OOS PAPER с комиссиями/проскальзыванием/SL first/no-lookahead и затем SMOKE.

## 5. Журнал A143 приёмка

Добавить append-only A143 **строго после двух полных независимых original60 replay и 30×3**. 6 SHA evidence: C73 source module, 30 tests, original60 probe, frozen full 303327 byte source JSON, independent witness, этот report. Previous immutable A142/142 SHA tip `347507f363d03a3bde2008a5690976ec3110925cc0ac514c1a6434299848059f`. Затем независимо проверить 143/143 SHA × Python3.10/3.11/3.12, все frozen original C46–C72 SHA git blobs прежние, обновлять только map и handoff. Никакие шесть файлов A143 после записи не менять.

**CRYPTO ONLY / PAPER ONLY / NOT_TRADE_READY.**
