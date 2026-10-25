# B1/C64 — исходный кандидат защищённого экстремума: 4H POI → первый native3m контакт → первое 1H событие → запрет ранней активации → наблюдение инвалидации

**UTC:** 25 октября 2026. **Репозиторий:** `SanChi117/EMBER-Research-Engine`, ветка `research/academic-engine-recovery-20261015`. **CRYPTO ONLY — Binance USD-M Futures; PAPER ONLY / NOT_TRADE_READY, 0 сделок.**

## 1. Что строго написано в авторской академии

Перечитаны реальные Google Drive оригиналы, используемые также в C59/C61:

- **Strong High & Low.txt**, ID `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`: сильный High/Low возникает от **контакта с ликвидностью либо неэффективностью** и *последующего* подтверждения движения через **Volume Confirmation POI или BOS**. Голый экстремум/пивот **не является StrongHL**. Подтверждённый Strong High может служить логическим структурным стопом, но не source proxy из C64.
- **Order Flow.txt**, ID `1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN`: OF = структура + работа с liquidity и IMB/POI. Инвалидация OF наступает при **закреплении за последней ланкой OF (BOS)** или формировании противоположной POI в контексте отработки цели. **Обычный прокол тенью любого технического минимума/максимума ещё не OF invalidation.**
- **POI.txt**, ID `1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R`: сильная POI работает с liquidity SSL/BSL или FVG, но исходная трёхсвечная 4H wick IMB **без авторского выбора** не становится академической POI.
- Примеры на старых схемах, в том числе Forex, являются **примерами логики**, не датированными crypto raw-bar золотыми тестами. Оригиналы не содержат воспроизводимой Binance USD-M авторской разметки `symbol/timestamp/source_ID/true selected POI/StrongHL/OF target`.

**Поэтому цель C64 — наблюдаемый технический PRICE SOURCE-кандидат экстремума, а НЕ автоматическая StrongHL-сертификация или готовый стоп/вход.**

## 2. Разработанный полноценный source lifecycle

- [x] Новый независимый модуль `d05/c64_original3m_source_protected_extreme_invalidation.py`: входы — C63 **первое ЛЮБОЕ**, а не выгодное, закрытое source-1H событие, оригинальный исходный SHA:timestamp первого native3m касания parent 4H-кандидата и исходные полные native3m/derived1h свечи, физически отсечённые на `as_of_ms`.
- [x] Направления не выбираются задним числом: при **двух направлениях с одинаковым первым временем** source extreme **не формируется**; при отсутствии контакта/закрытого события тоже не формируется. Если first ANY был *против* исходной 4H зоны, технический anchor строится в направлении **реального first-any**, а не в желательном LONG/SHORT.
- [x] Условный source anchor price = **минимум original native3m low** для первого LONG либо **максимум original native3m high** для первого SHORT от первого оригинального 3m contact bar (включительно) до старта будущего 1H source-паттерна (не включая его). Для него записан реальный raw original3m SHA:bar_start witness и время возникновения. **Anchor защищённым техническим кандидатом может стать только после полного закрытия first-any 1H события**, а не в прошлом и не как академический `StrongHL`.
- [x] Если во время *формирования* 1H-подтверждения, до закрытия последней свечи паттерна, native3m price уже нарушил anchor тенью — `SOURCE_ANCHOR_BREACHED_BEFORE_EVENT_CONFIRMATION`: такой anchor отклонён. Не перерисовывать его задним числом на более удачный. Ранний sweep до появления подтверждения НЕ превращать в будущий защищённый уровень.
- [x] После фактического знания 1H source-подтверждения раздельно наблюдать (только source/research) первое: **(a)** native3m high/low wick crossing, **(b)** оригинальное 3m *закрытие* строго за anchor, **(c)** source derived1h *закрытие* строго за anchor. Никакая из этих отметок сама не означает реальный академический BOS/OF invalidation, поскольку не доказано, что anchor есть авторская последняя структурная ланка OF.
- [x] Фиксированное окно post-confirmation = **24h** с явной правосторонней цензурой при конце исходной истории. Если подтверждение появилось, но истории меньше 24h, число фактически наблюдавшихся нарушений не объявляется «полной выживаемостью».
- [x] `d05/test_c64_original3m_source_protected_extreme_invalidation.py`: **28** adversarial negative/positive synthetic checks × Python 3.10/3.11/3.12. Случаи fake source 3m SHA/HOHLCV, незакрытый 1H, non-NaN, ложные авторские StrongHL и ордера, preconfirmation sweep, wick-only без 3m close, отдельно 1h close, противоположное first-any, ambiguous и source-asof с физически обрезанным префиксом. [CI 40213111462](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40213111462) SUCCESS 3/3.

## 3. Полная проверка на оригинальных криптосвечах, два независимых прохода

- [x] `tests/probe_c64_original45zip_3m_extreme_protected_invalidations.py` **ДВАЖДЫ С НУЛЯ скачал** 45 original Binance USD-M SHA+CHECKSUM ZIP на BTC, ETH, SOL, XRP, BCH: 15 original native3m, 15 native15m, 15 native1d за 1 сентября – 2 октября 2026. Верифицированы **76800** original closed native3m, **160** native1d, **15360** exact Decimal original15m OHLCV equalities, **3840** закрытых derived1h.
- [x] Каждый из **153** технических parent4H C46 source заново вычислен и полностью сравнен с неизменным frozen C46 blob `dc03c181912ffbb800bc191fbc16ec0d05c335e0`; C60 first contact/blob `899373e4a1dc1999d1485ac8c1f790d39071aebd`, C62 SNR/RB/IMB original JSON/blob `8428bf7d6cd3bc26f617cfc32a34c91a27c813b2` и C63 earliest ANY original chain/blob `fdc77c7ec942f03b4efae83b935d994c8435a24f` связаны по одному parent ID с original native3m/1h.
- [x] Первичный полный source & 28×3 negative [CI 40213320619](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40213320619) **SUCCESS**, evidence frozen `evidence/c64/C64_ORIGINAL45ZIP_STRICT_SOURCE_EXTREME_PRECONFIRM_POST_WICK_CLOSE_INVALIDATION.json`, **238920 bytes**, SHA256 `a921947a70a330cad76f63c0d3faa95069941e8793d24816291df87766cb729e`, Git blob `f70b0493a0c4964c618c09c75fee900dd65f5c05`.
- [x] Второй независимый fresh original Binance45 ZIP, полное **побайтное** сравнение `cmp -s` и SHA256, 28×3 negative [CI 40213466284](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40213466284) **SUCCESS 4/4**, full frozen **238920 bytes exact**. Witness `evidence/c64/C64_INDEPENDENT_ORIGINAL45ZIP_PROTECTED_SOURCE_EXTREME_WITNESS_20261025.json`.

## 4. Неподогнанная статистика ИСХОДНЫХ технических кандидатов — не сделки

| Source-статус на 153 parent 4H | Число |
|---|---:|
| Нет первого original native3m контакта | **21** |
| Первое source 1H событие было одновременно в двух направлениях | **7** |
| Anchor **нарушен во время формирования** 1H source-подтверждения | **55** |
| Anchor **не нарушен до фактического закрытия** source-1H события | **70** |
| **Всего source 4H геометрических кандидатов** | **153** |

Дополнительные наблюдения **только среди source anchor, не отклонённых до подтверждения**:

| После закрытия события, ограничено 24h | Количество |
|---|---:|
| Есть полностью наблюдённое 24h source-окно | **61** из 70 |
| Есть неполное / правосторонне цензурированное 24h окно | **9** из 70 |
| Хотя бы раз произошло пересечение source anchor **тенью 3m** | **35** |
| Наблюдалось оригинальное **закрытие 3m** строго за anchor | **31** |
| Наблюдалось **полностью закрытое 1H** строго за anchor | **28** |

35, 31 и 28 — **вложенные/пересекающиеся группы**, не складывать. Сильно коррелирующие 4H зоны могут давать общий диапазон/свечи, не считать отдельными сделками. Без авторского StrongHL и настоящего SL/TP некорректно называть 70 «выжившими стопами», а 28 — «стопами, которые выбило». Никакой прибыльности/вероятности здесь нет.

## 5. Границы и новая практическая задача C65

**C64 source chronology + protected candidate price + preactivation veto + native3m vs 1h closed breach ВЫПОЛНЕНЫ.**
**НЕТ** ни одного author positive golden по genuine StrongHL/OF invalidation, выбранному Daily/4H/1H POI, first VALID test, 15m VC, Route A entry, Route B IDM, Route C native3m/5m BOS, FTA, structural SL/TP, OOS. Никаких ордеров. Не путать `1h close beyond arbitrary C64 technical anchor` с академическим `BOS beyond last link of OF`, особенно в контексте target liquidity и OF continuation.

**C65 (ещё не выполнялся/не принят):** восстановить *саму* авторскую «последнюю ланку OF» с документируемой структурой, обязательной работой с liquidity/IMB и HTF target; последующее **закрытие** за ней или противоположная авторская POI после цели — только тогда рассматривается OF invalidation. Сверить с авторскими настоящими примерами, не переписывая 4H source anchors и C63 first ANY, затем PAPER отыгрыш всех трёх независимых маршрутов с корректным SL/TP/FTA и OOS.

## 6. Приёмка A134

Принять C64 **ровно шестью новыми** source SHA paths после двух независимых 45ZIP CI: модуль, 28 тестов, original45ZIP full probe, original 238920-byte JSON, independent witness, этот отчёт. `python tools/auditlog.py verify` обязателен; предыдущая A133/133 tip `3c222f47db62f0c2477f1c6d487444bcd46645770d0e545b31be1e8102a1b4ac`, все предыдущие оригиналы C46–C63 immutable. Затем независимый 134/134 SHA на Python3.10/3.11/3.12 и 28×3 negative tests. Отсутствие записи A134 означает **НЕПРИНЯТЫЙ** цикл.

**CRYPTO ONLY, PAPER ONLY, NOT_TRADE_READY, 0 orders/fills/trades/PnL.**
