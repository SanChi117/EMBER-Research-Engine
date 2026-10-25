# B1/C63 — исходный 4H POI-контекст → первый native3m контакт → ПЕРВОЕ ЛЮБОЕ 1H техническое подтверждение или BOS-прокси

**UTC:** 25.10.2026. **Рынок:** BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT — Binance USD-M original 45 signed ZIP, 01.09–02.10.2026. **PAPER ONLY / NOT_TRADE_READY — ноль ордеров.**

## Задача цикла и принцип честной статистики

Предшествующие C46, C60, C61 и C62 раздельно знали:
- оригинальную **техническую** classic 4H IMB-зону, момент её образования и первое истинное касание её границ по native3m source wick (C46);
- последовательность первого / повторных отдельных контактов (C60);
- тайм-контекст исходного 1D, отделение реального авторского POI и первого валидного теста от source wick геометрии (C61);
- разные технические 1H классы source SNR, RB, слабый MB и классический 3-свечный IMB (C62).

C63 **связывает** эти факты в проверяемую хронологию. На каждом 4H source-кандидате выбирается **ПЕРВОЕ ЛЮБОЕ** событие 1H, целиком сформированное *ПОСЛЕ первого закрытого native3m контакта*, в фиксированном исследовательском окне **24 часа**. Учитывается и противоположная реакция, и одновременные события двух направлений. Нельзя выбирать первое благоприятное, игнорируя более раннее противоположное. Если окно не полностью наблюдалось, оно явно **RIGHT_CENSORED**, а не победа/поражение.

## Реализовано

- [x] `d05/c63_closed_4h_source_contact_to_first_any_1h_reaction.py`:
  - на входе уже зафиксированный оригинальный parent 4H source, SHA:timestamp оригинального first native3m contact и список original closed source 1H событий;
  - типы технических событий **1H SNR**, **1H RB**, **1H classic IMB**, **1H close-breach ранее известного strict3bar fractal**. Последний — **BOS proxy**, не авторский BOS. RB — контекстный source, не Route A final entry; слабый MB и голая пара свечей не становятся VC;
  - строгое правило `first_pattern_bar_start_ms >= first_contact_known_ms`; закрытие последней свечи 1H не даёт права использовать 2 часа раннего события, начавшегося до source-контакта;
  - источник каждого события — точный исходный native15m SHA:bar_start; для каждого event тип фиксирует длительность паттерна и `fully_known_ms`. Подделанные авторский VC/BOS/StrongHL, price-ID, будущие и неполные события вызывают исключение;
  - `first any` на одинаковом времени **обе стороны** = `AMBIGUOUS`, не выбирается приятная сторона; по истечении полного окна без событий = `FULL_WINDOW_NO_SOURCE_EVENT`, при неполном без событий = `RIGHT_CENSORED_NO_SOURCE_EVENT`;
  - author goldens, first **валидный** POI test, Strong High/Low, SL/TP, FTA, PnL, orders/fills/trades остаются нулевыми.
- [x] `d05/test_c63_closed_4h_source_contact_to_first_any_1h_reaction.py`: **29** сценариев (Python 3.10/3.11/3.12), включают более раннее противоположное событие, два направления в одно время, right-censor, full-window, нет контакта, forged SHA-ID, future event, forged author StrongHL, short pattern и сравнение `physically truncated source` с `as-of filtered`. [CI 40211660771](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40211660771) SUCCESS 3/3.

## Настоящие Binance криптоисходники

- [x] `tests/probe_c63_original45zip_first_any_1h_after_original3m_contact.py`: заново скачаны **45 SHA-checked signed original Binance USD-M ZIP** (15 × native3m, 15 × native15m, 15 × native1d) на каждой из **двух независимых** проверок; исходные 76800 native3m, 160 original native1d, 15360 exact Decimal native15m OHLCV, 3840 полностью закрытых derived1h. Исходные **153 C46 4H source parents** сверены полностью с frozen Git blob `dc03c181912ffbb800bc191fbc16ec0d05c335e0`; C62 по каждому crypto оригиналу заново сформирован и сравнен с frozen Git blob `8428bf7d6cd3bc26f617cfc32a34c91a27c813b2`; frozen C60 `899373e4a1dc1999d1485ac8c1f790d39071aebd` сверяется с каждым parent ID/contact.
- [!] Первоначальный [CI 40211860750](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40211860750) красный: в оперативном объекте `asdict` оставались Python tuple исходных candle-ID и пустых orders, тогда как соответствующий frozen JSON содержал массивы. **Исходная цена не изменилась**; исправлена канонизация `json.loads(json.dumps(...))` перед сравнением. Красный исторический запуск сохранён.
- [x] После исправления полная первичная исходная [CI 40211919023](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40211919023) **SUCCESS**: original45ZIP, 29×3 tests, frozen source `evidence/c63/C63_ORIGINAL45ZIP_FIRST_ANY_CLOSED1H_SOURCE_AFTER_4H_FIRST_NATIVE3M_CONTACT.json`, **302827 bytes**, SHA256 `a681e2941d45b9658ab02c98c5dd06e4bfd85388982537241d8a5bd0708c31be`, Git blob `fdc77c7ec942f03b4efae83b935d994c8435a24f`.
- [x] Полная независимая вторая оригинальная 45ZIP [CI 40212064161](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40212064161) **SUCCESS 4/4**: все **302827** исходных JSON-байта совпали; повторно 29×3 отрицательных тестов.

## Результаты — НЕ прибыль и НЕ сделки

| Состояние source-контекста 4H → first ANY 1H | Число |
|---|---:|
| Нет исходного первого 3m контакта | **21** |
| Первое следующее source-событие **в первоначальном направлении** | **64** |
| Первое следующее source-событие **в противоположном направлении** | **61** |
| Первое следующее событие **двух направлений одновременно** | **7** |
| Полное 24h окно без 1H события | **0** |
| Неполное 24h окно без 1H события (right-censored) | **0** |
| **Всего original 4H технических source-кандидатов** | **153** |

Это **результат технического событийного фильтра**, не результаты торгов, не winrate, не вероятность движения в будущем. Даже события направления **64/132** нельзя называть выигрышем: нет author-selected POI, действительного StrongHL, FTA/SL/TP, конкретного ордера, спреда и проскальзывания. Родительские 4H source IMB-контексты могут пересекаться по свечам и статистически зависимы. Отсутствие right-censor в этой выборке не отменяет механизм и его тесты.

## Что по-прежнему БЛОКИРУЕТ торговый механизм

**Academic StrongHL НЕ готов**: для реального Strong High/Low по уроку `Strong High & Low.txt` нужен авторский контакт с ликвидностью/inefficiency, затем **фактический подтверждённый** VC POI/BOS. C63 показывает проверяемую source-последовательность, но `1H fractal close break` остаётся адаптацией, `SNR/RB/IMB` остаются техническими исходными геометрическими кандидатами; ни один сам по себе **не академический сигнал**. Не делать snapshot/label StrongHL задним числом. Не смешивать с Route B IDM и Route C native3m/5m BOS, не изменять SMOKE, V5, QFVG, не торговать.

**Следующий реальный шаг C64:** отделить protected source extreme в момент закрытого contact/reaction, подтверждённую source invalidation и её хронологию, получить положительные и отрицательные **авторски размеченные** crypto chart goldens с timestamp и raw candle-ID, затем отдельно 4H/1H typed POI → Route A/B/C final entry, FTA, SL/TP, OOS backtest. Не использовать FX скриншот как цену Binance.

## Принятие A133

Append-only **A133** возможен только по шести отдельным frozen evidence paths: модуль C63, 29 unit tests, full original45ZIP source script, полный immutable 302827 bytes JSON, second-independent witness, этот report. Приёмка — `python tools/auditlog.py verify`, строго неизменные A001–A132 и старые SHA C46/C47/C55/C56/C57/C58/C59/C60/C61/C62, независимый 133/133 SHA × Python 3.10/3.11/3.12. Previous tip A132 `7b6f58a0007783307b25d8876cc3f2332dddd5a0935c2ac9d677b34be4b2c4ab`.
