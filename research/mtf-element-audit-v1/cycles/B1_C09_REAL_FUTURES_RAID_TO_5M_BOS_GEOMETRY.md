# B1/C09 — первичные 5m Futures свечи → закрытые 1H фракталы → Raid → 5m BOS

**Дата:** 2026-10-16. **Область приёмки:** `SOURCE_BOUND_V05_LIQUIDITY_RAID_TO_LTF_BOS_GEOMETRY`, исследовательские кандидаты и реальный источник, **не** академический торговый сигнал. **PAPER ONLY**.

## Источниковое основание

- Исходный урок [Order Flow.txt](https://drive.google.com/file/d/1r6sH0XjEoK4Jwq4EVLz8vqPSWVh9qerN/view): по структуре движение OF опирается на ликвидность и IMB; после снятия ликвидности ожидается младший BOS для дальнейшего рассмотрения входа. Достижение цели само по себе не переключает OF.
- [Entry By BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): отдельный маршрут 1H raid → 3m/5m BOS.
- Используются **неизменённые primitives** `confirmed_pivots`, `confirmed_hourly_raids`, `bos_after_raid` из `research/mtf-course-v05/src/course_primitives_v05.py` (Git blob `45cec7fd66d0ec156bc0a38225ee282c6d3ee71b`).
- Реальный 5m Binance USD-M Futures BTCUSDT 2026-10-02 проходит независимую F03-квитанцию, Git blob `7e5bc374b4e4cceaf01325b16e42631dad0ec9db`, ZIP SHA `2a492563746eba6c3689b90c00a081bfce3ceab86a06493e80f22c4d55e8c7ea`; B1/C09 всегда использует закрытые 5m бары и формирует 1H только после **12 закрытых 5m**, начиная UTC-полночью.

## Фактически сделано

- `d05/c09_source_5m_raid_bos_geometry.py`: read-only `inspect_source_raid_bos_5m(Verified5m,as_of)` получает 288 исходных свечей, отрезает будущую часть в `as_of`, агрегирует 12×5m в 1H, строит уже существующие закрытые фракталы, замечает 1H wick-sweep с возвратом закрытия, проверяет закрытый 5m BOS **только после известности родительского 1H RAID**. Каждый BOS связан с конкретным raw original 5m row source ID.
- `d05/test_c09_source_5m_raid_bos_geometry.py`: **18** тестов с позитивной синтетической последовательностью, отсутствием raid, wick without reclaim, BOS по тени без close, новый выход за extreme raid, отсутствие подтверждения до закрытия 1H / 5m, смена future suffix, неполный исходник, gap и frozen `NOT_TRADE_READY`.
- `tests/probe_c09_actual_price_raids_bos.py`: online заново получает оригинальный Binance 5m + .CHECKSUM и сверяет ZIP/CSV SHA с F03; прогоняет **все 288 raw 5m**, плюс префикс по 08:00 UTC, через этот новый геометрический мост.

## Проверенная реальная выборка

[GitHub Actions B1/C09 — SUCCESS, 38872807582](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38872807582):

- Исходные Futures 5m: **288**, построенные закрытые 1H: **24**;
- Кандидаты 1H фракталов: **5**;
- Кандидаты 1H wick raid: **1**;
- Кандидаты 5m фракталов: **76**;
- Связанные source-backed 1H raid → закрытый 5m BOS: **1** (в этой дневной выборке, при текущих v05 инженерных параметрах);
- Цена BOS взята из оригинального 5m клайна с open time `1790949300000` = 2026-10-02 **13:55 UTC**; запись привязана к ZIP-SHA и raw CSV row timestamp. **Это не точка входа и не результат прибыльной сделки.**
- **29** исходных v05 + **23** F03 proof/negative tests + **18** новых C09 = **70/70 PASS**.

## Опровержение и ошибки предыдущей попытки

Первый [CI run 38872747699](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38872747699) дал **1 FAIL в 41** новых тестах: тест сравнивал полный `original_5m_member_id` между двумя *синтетическими* ZIP, в одном из которых изменена будущая часть. Это ошибочная приёмка: SHA исходного целого архива при любом изменении обязан быть другим, значит raw IDs законно отличаются. Пересмотрен **только тест**, теперь старый prefix сравнивается по времени/geometric event-ID и ценовому событию, а разные source hash не замалчиваются. Второй запуск — **SUCCESS**. Старый FAIL оставлен в истории.

**Важные нерешённые источниковые вопросы:**
1. Original v05 `confirmed_hourly_raids` использует **24h freshness** как явно признанную приближённую инженерную оценку, а не прошедшее авторскую подпись правило каждой сессии.
2. Original v05 `confirmed_pivots` использует 2 слева/2 справа; без независимого course-labelled графика нельзя выдавать всякий такой pivot за авторский fractal SSL/BSL.
3. Реальные **1** raid и **1** BOS — результаты механики исследования, не сертифицированные академические labels: нет соответствующего подтверждённого StrongHL, HTF/from-to, source POI, целевого FTA, инвалидации, проверки рыночных режимов и заполненного trade graph.
4. Для авторского StrongHL необходимо независимое **подтверждение объёма** `VC_IMB/VC_SNR/VC_RB` или BOS с причинной ценовой геометрией и обязательным контекстом; факт распознанного BOS не разрешает автоматически объявить StrongHL или выставить заявку.
5. Source range — 1 день BTC. Историю 5m на все дни/монеты нельзя автоматически считать аттестованной; альтернативная дневная выборка может дать другое число кандидатов.

**Приёмка:** `READ_ONLY_GEOMETRY_PASS`, `ACADEMIC_ENTRY_READY=0`, `ORDERS_CREATED=0`, `PnL_NOT_ESTIMATED`. Оригинальная торговая инфраструктура EMBER/SMOKE/V5/QFVG не менялась.
