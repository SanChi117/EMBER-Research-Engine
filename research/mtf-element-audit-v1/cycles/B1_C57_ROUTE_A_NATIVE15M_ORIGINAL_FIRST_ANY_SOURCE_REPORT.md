# B1/C57 — Route A: source-only first any native15m technical IMB after 4H first contact and later 1H technical source

**Дата:** 25.10.2026 UTC. **Область:** BTC/ETH/SOL/XRP/BCH, оригинальные Binance USD-M Futures 2026-09-01 — 2026-10-02. **PAPER ONLY / NOT_TRADE_READY**.

## Что взяли из академии и что НЕ подменяли

Из **C45 восстановленных уроков владельца** следует: Route A при 4H **действительно типизированном и протестированном POI** предполагает 1H триггер BSL/SSL/IMB, а затем 15m VC типа IMB/SNR. Отсутствие триггера требует **другой ветви**, а не тайной подстановки 15m IMB. Ниже исследуются только **воспроизводимые технические source-кандидаты**, а не курсной POI/1H trigger/15m VC. В C57 **не измерялась академическая VC**, объёмные правила не восстановлены, модель не торгует.

## Стабильная постановка C57

- [x] Не менять A001–A126, источники C46 и C47, ветви Route B и C. C46 классический 4H трёхбарный wick IMB по оригинальным закрытым native3m → **первый** оригинальный 3m wick contact после 4H зоны. C47 первый последующий same-side 1H technical IMB может появиться только после завершения contact3m, но **не считается автоматически 1H авторским триггером**.
- [x] Из отдельного ORIGINAL native15m C08 (не пересэмплированного в тесте из 3m) брать строгие трёхсвечные wick gaps; начало первого 15m source-gap **не ранее полного закрытия 1H source-кандидата**. Рассматривать **первый любой** gap независимо от совпадения направления. Не выбирать постфактум более выгодный same-side.
- [x] Граница окна **6 часов** после 1H known time; это только заранее фиксированная исследовательская граница, **не авторский тайм-аут торгового сигнала**. Если все 6 часов не доступны из-за конца истории, выделять `RIGHT_CENSORED`, а не подменять «не было gap». Коллизия intrabar high/low из OHLC не используется для заявок.
- [x] Сравнивать по каждому parent точные исходные SHA ZIP:bar_start ID, closed-known time, 4H source direction, first contact, later 1H, first any 15m; авторские POI/VC/entry/stop/target всегда **False/0**.

## Действия и source evidence

- [x] Новые независимые файлы `d05/c57_route_a_original15m_first_imb_after_1h_source.py`, `d05/test_c57_route_a_original15m_first_imb_after_1h_source.py`, `tests/probe_c57_original45zip_route_a_4h_1h_native15m_first_imb.py`.
- [x] Протокол исходников перечитал и SHA-проверил **45 настоящих Binance USD-M ZIP + .CHECKSUM**: 30 оригинальных native15m+native1d архивов C08 и 15 оригинальных native3m; **76 800 original3m, 15 360 original15m, 15 360 EXACT Decimal 3m→15m OHLCV parities**, 5 криптовалют; source C47 entire JSON по всем original 4H parents совпадает строго с frozen C47 blob `b2727f081d8a73f522a97a54b4582507ee969244`, C46 `dc03c181912ffbb800bc191fbc16ec0d05c335e0`.
- [x] Реально физически обрезанный original 3m stream до 2026-10-02 00:15 UTC и полный stream с ограничением as-of дали одинаковое C47; native15m исходный префикс дал byte-equivalent C57 результат. Дополнительно unit-тестами отсекаются будущие 15m, неправильные checksum-ID, отсутствие правого подтверждения swing, подмена авторского статуса, выбор более позднего same-side IMB.
- [x] Первичная полная [CI 40200305505](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40200305505) **SUCCESS** с 42 негативными проверками × Python 3.10/3.11/3.12. Frozen JSON: `evidence/c57/C57_ORIGINAL_45ZIP_4H_FIRST_CONTACT_LATER_1H_THEN_FIRST_ANY_NATIVE15M_IMB.json`, **292 187 байт**, SHA256 **3ce556499294bb005f4ecfc57a817488ab6a66ef498c1181ceca2874acff1b95**, Git blob **08f24050d19bb390cf2985a901e2a8f2ea3c0ec3**.
- [x] Вторая полностью независимая **fresh all 45 ZIP** source CI [40200457478](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40200457478) **SUCCESS 4/4**: `cmp -s` всего 292187-byte JSON, точный SHA256, отдельно 42 anti-fraud теста × 3 Python. Witness: `evidence/c57/C57_INDEPENDENT_45ZIP_NATIVE15M_FIRST_ANY_WITNESS_20261025.json`.

## Результаты только в единицах коррелированных SOURCE CONTEXTS

| Crypto | 15m first any same-side | 15m first any opposite-side | 4h no contact | contact no 1h source | 15m no gap before source end, censored |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 12 | 17 | 3 | 0 | 0 |
| BTCUSDT | 9 | 13 | 5 | 0 | 3 |
| ETHUSDT | 14 | 10 | 5 | 2 | 0 |
| SOLUSDT | 11 | 13 | 5 | 0 | 2 |
| XRPUSDT | 13 | 12 | 3 | 0 | 1 |
| **Итого** | **59** | **65** | **21** | **2** | **6** |

153 technical 4H IMB zones; 132 первого оригинального 3m contact; 130 с технической следующей 1H same-side IMB, но не подтверждённым автором. У 124 из них в заданном окне появился first-any 15m wick-gap, у 6 окно right-censored. Нельзя считать 59 или 65 торговой вероятностью/винрейтом: события коррелированы, нет авторского POI, сильного High/Low, валидной VC, входа, комиссии, проскальзывания, tick fill, RR, SL/TP или OOS.

## Не скрывать неудачи

- [!] Первоначальная CI 40199972533 упала на одной **ожидаемой строке отказа** теста (`UNVERIFIED_C47` вместо фактического fail-closed `MISSING_FIRST_1H_CANDIDATE`). Исправлено только точное ожидание теста; CI 40200076524 PASS.
- [!] Первоначальная full45ZIP CI 40200264623 упала до оригинального replay: код ошибочно обращался к несуществующему полю frozen C47 (`author_course_poi_vc_goldens`). Исправлено на **реальные два существующие** source-поля: `academic_author_4h_poi_verified`, `academic_author_1h_volume_confirmation_verified`. Исходные события не менялись, успешный повтор 40200305505; независимый повтор 40200457478.
- [x] Доработка против неверных выводов: `RIGHT_CENSORED` статус отдельно от отсутствия gap при полностью просмотренных 6 часах, строгие source row ID в 3m и 15m.

## Принципиально не принято как авторская академическая семантика

4H classic wick gap **не равен** авторскому выбранному POI; первый source native3m wick контакт **не равен** разрешённому первому POI-тесту; C47 1H технический IMB **не равен** полноценному контекстному trigger; C57 15m technical IMB **не равен** документированному 15m VC. В отсутствие настоящего Volume Confirmation, SNR, Strong HL, FTA и исходно размеченных авторских кейсов стратегия не готова ни к автоматическому, ни к PAPER размещению заявок. Все flags авторского статуса, executions, orders, trades, PnL остаются нулевыми.

## Приёмочная граница

Этот отчёт + C57 code, negative tests, full original JSON, независимый witness + исходный replay всего **6 evidence файлов** для новой **A127**. В SHA-журнал A127 записывать только после independent CI, не изменяя A001–A126. Последняя принятая точка перед C57: A126 126/126 tip `f47e459f6fda6bed5fc89d61a172b120eceee0702596cfd9de21f3382ec23dba`. После записи нужна отдельная 127/127 CI по 3 Python, с SHA каждого из 6 evidence файлов и старых frozen C46/C47/C55/C56. Общая coarse карта **29/40 done, 3 partial, 8 pending** пока неизменна; эти числа не готовность к торговле.

**Дальше:** C58 — отдельно курсная Route B IDM семантика preknown BSL/SSL liquidity inside/ahead POI, с запрещением fake pivot-based IDM, без смешения с Route A VC. Начинать исходные crypto исследования только как ADAPTED until author sample proven.
