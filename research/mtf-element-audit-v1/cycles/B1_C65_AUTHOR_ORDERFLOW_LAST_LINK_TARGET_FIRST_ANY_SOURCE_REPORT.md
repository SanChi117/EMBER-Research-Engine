# B1/C65 — Order Flow: последняя структурная ланка, обязательная работа с liquidity/IMB, HTF target и **ПЕРВАЯ ЛЮБАЯ** инвалидация (крипто-SOURCE ONLY)

**Дата:** 25 октября 2026, UTC. **Проект:** `SanChi117/EMBER-Research-Engine`. **Ветка:** `research/academic-engine-recovery-20261015`. **Статус:** `PAPER ONLY / NOT_TRADE_READY`; нет авторских подтверждённых StrongHL, OF invalidation, ордеров, прибыли.

## 1. Требования именно авторских оригиналов, а не универсальной SMC-эвристики

Повторно перепроверены реальные оригиналы Google Drive:

- **Order Flow.txt**, Drive `1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN`: OF — направленная структура, **обязательно работает с ликвидностью и дисбалансами/POI**. Обязательна осмысленная HTF-цель. После цели OF может ПРОДОЛЖИТЬСЯ — это НЕ автоматическая инвалидация. Инвалидация происходит либо (a) при **закреплении цены за последней истинной структурной OF-ланкой** (BOS), либо (b) при формировании **любой POI в противоположную сторону на том же таймфрейме** после достижения цели. Тень сама по себе не доказывает закреп.
- **Strong High & Low.txt**, Drive `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`: true StrongHL — реальный liquidity/inefficiency contact и **последующий** подтверждённый VC POI или BOS; голый фрактал и произвольная C64 min/max цена НЕ авторски сертифицированы.
- **POI.txt**, Drive `1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R`: сильный POI взаимодействует с SSL/BSL/FVG, но необработанная native1d дневная экстремальная цена ещё не является авторски выбранной POI.
  
**В исходных уроках НЕТ** достаточной подписанной крипто-Binance timestamp/symbol/candle-ID авторской разметки последних реальных OF links, POI/StrongHL, target, first VALID test и последующего BOS. Поэтому C65 — **строгий исследовательский SOURCE-only наблюдатель и отчёт о недоказанных элементах**. Результаты C65 не должны повышать статус готовности к торговле.

## 2. Что реализовано

Новый `d05/c65_of_last_link_target_invalidation_source.py` (отдельно, без изменений C46–C64):

1. [x] Источник только из ранее независимых проверенных C64 price anchor source (должен сохраниться ДО закрытия своего 1H source-события) с явно направленным первым любым C63 событием. Не использовать C64 min/max как последнюю OF-ланку.
2. [x] Свидетельство **снятия/работы с ликвидностью**: source C62 1H SNR/RB with strict preknown unswept fractal raid, той же направленности, известное **до** link, после first source contact. Наличие одного фрактала само по себе НЕ `liquidity work`.
3. [x] **Отдельное** свидетельство ранее известной `IMB work`: source C62 SNR/RB с фактическим тестом ранее закрытого 1H gap в source-геометрии. Просто новая 3-свечная IMB НЕ считается тестом IMB. Доказательства должны быть известны до link на том же source направлении.
4. [x] Ранее подтверждённый и не сметённый strict 3-bar 1H source fractal `SSL` для LONG / `BSL` для SHORT, отдельно от C64 min/max. Если pivot пробит ещё на баре подтверждения — **нельзя задним числом защищать**. Всё равно это только source pivot, НЕ академическая OF-ланка.
5. [x] Source HTF target из **уже закрытой** оригинальной Binance `native1d` свечи, её High для LONG / Low для SHORT; target должен быть ещё впереди на момент появления link. Физически недоступная будущая дневная свеча не может быть источником цели.
6. [x] Достижение такой цели (первый source 1H wick touch), затем — только *после* неё — `FIRST ANY` наблюдаемое событие в фиксированном исследовательском **48h** окне: (a) полностью закрытый original-derived1H close за РАНЕЕ известный отдельный source pivot, либо (b) противоположная 1H source C62 SNR/RB/IMB, чей паттерн **целиком начался после касания HTF цели**. Одновременное возникновение — явный `BOTH`, а не выбор «красивого». Нет события при неполном окне = `right censored`, не успех.
7. [x] Из original source C62 проверяются исходные native15m SHA:bar-start идентификаторы, сторона, время, prefix и совпадение события с raw 1H исходным источником. Все author flags, trade approval, orders, fills, trades = **0**.

**31 unit/adversarial test** на Python 3.10/3.11/3.12 (`d05/test_c65_of_last_link_target_invalidation_source.py`): отсутствие liquidity/IMB, искусственный MB вместо liquid, будущая IMB ссылка, last-link pivot not C64 anchor, незакрытая 1D, target behind, ПОСЛЕДУЮЩЕЕ достижение цели без разворота, противоположная POI строго после цели, ложная POI с паттерном до цели, несовпадение timeframe/candle-ID, target first vs favorable BOS, оба условия в одну закрытую свечу, ложные авторские flags/ордера, правосторонняя цензура.

- [!] Сначала [CI 40214646246](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40214646246) был **FAIL 3** — три синтетических теста по ошибке задавали противоположную 3-свечную POI до фактического достижения цели, а тестовая дневная target high ещё находилась впереди цены. Исправлены ожидания и именно **синтетические** цены/порядок, не упрощалась производственная проверка.
- [x] После исправления [CI 40214720404](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40214720404) **SUCCESS 3/3**, и после усиления SHA provenance, same-direction 1H work + 48h window [CI 40214855551](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40214855551) **SUCCESS 3/3**.

## 3. Полная оригинальная криптоистория и независимый cross-join

Новый `tests/probe_c65_original45zip_of_last_link_target_invalidation.py`: дважды С НУЛЯ скачаны **45 подписанных ZIP + оригинальные checksum** с Binance USD-M Futures (BTC, ETH, SOL, XRP, BCH, 2026-09-01–2026-10-02). **76800** native3m, **160** native1d, **15360** exact native15m Decimal OHLCV паритетов и **3840** закрытых source-derived1H.

Все **153** 4H technical source-пары по одинаковым original source SHA:time сверены непосредственно с immutable C46 `dc03c181912ffbb800bc191fbc16ec0d05c335e0`, C60 `899373e4a1dc1999d1485ac8c1f790d39071aebd`, C62 `8428bf7d6cd3bc26f617cfc32a34c91a27c813b2`, C63 `fdc77c7ec942f03b4efae83b935d994c8435a24f`, C64 `f70b0493a0c4964c618c09c75fee900dd65f5c05`; **C64 source-anchor снова воссоздан с нативными 3m ценами**, не доверено одной записи в отчёте.

- [x] Первоначальный полный original45ZIP и 31×3 [CI 40215080339](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40215080339) **SUCCESS**, JSON **237284 bytes**, SHA256 `0865735c653925230e29ee978df2f59090a3711243d93db09cdf11994990b07b`, Git blob `791f20fcf0a8d6c4697f02fd7247b45cfd4b6de5`, путь `evidence/c65/C65_ORIGINAL45ZIP_OF_SOURCE_LAST_LINK_HTF_TARGET_FIRST_ANY_INVALIDATION.json`.
- [x] Второй полностью НОВЫЙ independent original45ZIP [CI 40215245033](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40215245033) **SUCCESS 4/4**, все **237284 bytes** исходного JSON совпали побайтно; SHA256 и 31×3 теста повторно. Evidence-witness `evidence/c65/C65_INDEPENDENT_ORIGINAL45ZIP_SOURCE_OF_LAST_LINK_WITNESS_20261025.json`.

## 4. Результат C65: система пока НЕ имеет права признать ни одной авторской OF-ланки

| Исходный STATUS для 153 source 4H контекстов | Сколько |
|---|---:|
| Источник C64 не дал технический anchor, остававшийся известным к моменту 1H подтверждения | **83** |
| Источник C64 подошёл, но **не доказана предыдущая работа с ликвидностью на 1H по строгим условиям** | **69** |
| Evidence по ликвидности нашёлся, но **нет отдельно доказанного preknown IMB work** | **1** |
| Полный strict source 1H комплект evidence последней OF-ланки + HTF target + возможные инвалидации | **0** |
| **ВСЕГО** исходных correlated 4H technical contexts | **153** |

**Существенное ограничение:** эта проверка **1H ONLY + post-first-contact + совпадение направления + preknown C62 source-level**. Академия допускает VC/POI на том же TF **или ниже**, HTF контексты тоже не заменяются механическим 1H. Поэтому `0` не доказывает отсутствие реального OF в BTC/ETH/SOL/XRP/BCH и не является оценкой winrate, «работоспособности рынка» или прибыльности торговли. Оно показывает **недостаточность доказательств по указанной source-модели**. Искусственно расширять совпадения или убрать liquidity/IMB условие, чтобы получить сделки, запрещено.

## 5. Где блокер и следующий логический C66

**C65 инженерно завершает зафиксированный строгий 1H evidence-gate**, а не настоящий торговый Order Flow. Отсутствует авторами размеченный OHLCV price/candle-ID true last OF link, last liquidity sweep, IMB test, POI, target и Strong High/Low. НЕТ author crypto chart goldens, подтверждённого SL/TP/FTA, трех работающих связок A/B/C, OOS с исполнением.

**C66 далее:** без изменения замороженной C65 воспроизвести **4H/1H→15m (и 5m только там, где допускает исходный маршрут) source context**, отдельные закрытые native15m real liquidity/IMB work, подтверждение 1H/15m VC POI/BOS и last OF link. Взять исходные схемы как evidence *логики*, не придумывать им crypto timestamps; при отсутствии авторского goldens сохранять ADAPTED/NOT_TRADE_READY. Лишь после доказательства структуры соединять независимые Route A/B/C, structural SL/TP/FTA и независимый PAPER OOS. Ни один source candidate не даёт ордер.

## 6. Приёмка A135 и immutable evidence

Append-once **A135** только после двух независимых 45 original ZIP C65, 31×3 CI: ровно шесть SHA файлов (source module, negative tests, original45 ZIP replay probe, frozen 237284-byte JSON, independent witness, этот report). Старые A001–A134 и frozen C46–C64 SHA обязаны остаться идентичны; independent CI 135/135 SHA на Python 3.10/3.11/3.12, нет lookahead и приказов.

**Результат:** `0 author_OF_links, 0 author_StrongHL, 0 orders/fills/trades/PnL`. Строго `PAPER ONLY / NOT_TRADE_READY`.


## 7. Дополнительная независимая реализация полного 45ZIP source replay

Кроме основного `tests/probe_c65_original45zip_of_last_link_target_invalidation.py` была отдельно реализована `tests/probe_c65_original45zip_of_last_link_target_first_invalidation.py`. Она самостоятельно заново пересчитывает все 153 C46 parents, оригинальные C60 contacts, все исходные C62 случаи, C63 first ANY, C64 native3m anchor и C65 1H-контекст, после чего сравнивает исходные frozen C46/C60/C62/C63/C64 price/ID и присваивает тот же строго fail-closed C65 status.

- Первое независимое полное выполнение [CI 40215224187](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40215224187) **SUCCESS**. Второе повторное независимое скачивание всех 45 оригинальных подписанных ZIP и побайтное сравнение [CI 40215392901](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40215392901) **SUCCESS 4/4**; ещё **31×3** теста. `evidence/c65/C65_ORIGINAL45ZIP_LAST_STRUCTURAL_OF_LINK_FIRST_TARGET_INVALIDATION_SOURCE.json` — **222052 bytes**, SHA256 `a178de99d78cb5bbf1f75c5dfa61c7750705c9f7b500c9712a6bdab3f672ae08`, Git blob `be6052b0e94ba93c2575712d8873051af37a46e5`. Схема дополнительного JSON отличается от основного, но **все 153 C65 source states идентичны: 83/69/1/0**. Второй независимый witness `evidence/c65/C65_INDEPENDENT_ORIGINAL45ZIP_LAST_OF_LINK_NO_OVERPROMOTION_WITNESS_20261025.json`.
- Сохранён промежуточный [CI 40215106379](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40215106379) FAIL из-за опечатки в функции подсчёта по всем символам (`tot` вместо `totals`). Исправлена именно опечатка без подгонки OHLCV или статусов. После этого оба полных replay **SUCCESS**.

Таким образом принята не одна запущенная реализация, а **две независимо написанные последовательности сверки оригинальных исходников**. Нулевой подтверждённый OF по прежнему означает недостаточность технической source-модели на этих данных, не отсутствие авторской рыночной структуры.
