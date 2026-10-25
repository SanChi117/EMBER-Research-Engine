# B1/C58 — Route B preknown 1H liquidity inside a 4H technical source zone (NOT academic IDM)

**Дата:** 2026-10-25 (UTC). **Scope:** CRYPTO ONLY, Binance USD-M BTC/ETH/SOL/XRP/BCH 01.09–02.10.2026. **PAPER ONLY / NOT_TRADE_READY**, ноль заявок/сделок.

## Курсная семантика и научное разделение

Исходный C45 lesson `3. Entry by Inducement [IDM]` указывает: Route B требует контекстный POI / VC и нижний IDM из BSL/SSL ликвидности **внутри либо перед** родительским POI; Strong High/Low, без финального Route A VC. Однако нет исходно подтверждённого автором механического определения **ahead** и оригинальных timestamp/symbol/price меток авторских IDM и StrongHL. Поэтому C58 ограничен только объективной **INSIDE 4H source gap** и не делает выводов «это IDM», «это трейд» или «всё прошло академию».

## Сделано

- [x] Прочитаны C45 текстовый контракт Route B, ранние независимые C46/C55 исходники, воспроизведён C46 original 4H technical classic 3-candle wick imbalance. Frozen C46 SHA blob `dc03c181912ffbb800bc191fbc16ec0d05c335e0` неизменён; ранее accepted A127 tip `f7f82c55dd87db0bc881ef977e9e9b0db1c91495f827d47f86701934e05c9005`.
- [x] Написаны самостоятельные `d05/c58_route_b_preknown_original1h_liquidity_inside_4h_source.py`, `d05/test_c58_route_b_preknown_original1h_liquidity_inside_4h_source.py`, `tests/probe_c58_original45zip_route_b_preknown_unswept_1h_inside_4h.py`. Отдельно от Route A и C, не меняют торговую механику V5/QFVG или SMOKE.
- [x] Каждому оригинальному source 4H gap сопоставляется **первый** оригинальный wick contact native3m, только после момента знания всех трёх 4H баров. На момент **начала** этого 3m contact source bar берутся ВСЕ source 1H строгие трёхчасовые fractal BSL/SSL, полностью известные после 4H зоны и до самого contact bar. На price axis уровни обязаны лежать внутри technical gap [bottom,top]. Никакой nearest/best/winner swing по последующим свечам не выбирается.
- [x] Каждый такой source 1H pivot дополнительно сканируется по ВСЕМ подлинным **закрытым** original3m барам после времени, когда pivot стал известен, но **строго до начала первого контакта**. Strict BSL breach high выше уровня, SSL breach low ниже. Уже сломанный уровень нельзя объявить «раньше непробитым». Приоритет A/B/C не перемешивается, single-source-ID SHA сохраняется.
- [x] Re-download **45 оригинальных Binance USD-M ZIP + SHA .CHECKSUM**: 30 оригинальных native15m/1d и 15 оригинальных native3m; 76 800 оригинальных closed3m, 15 360 exact Decimal OHLCV native15m равенств; 3 840 derived full1H. Вся исходная C46 source JSON строго совпала с frozen C46, физически укороченный 3m prefix совпадает с as-of результатом.
- [x] 28 source-only adversarial тестов × Python 3.10/3.11/3.12. [Первичная original45ZIP CI 40201560854](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40201560854) **SUCCESS**. Заморожен полный JSON `evidence/c58/C58_ORIGINAL_45ZIP_PREKNOWN_UNSWEPT_1H_FRACTAL_INSIDE_4H_FIRST_CONTACT.json`: **193 355 байт**, SHA256 **405a34b939845357412ab4ec2d055d71885e3f6a1b22f55bc25c87c60272808e**, Git blob **06f2ff7decd2aa9660381947d3cf43f6b722cd8e**.
- [x] Второй независимо повторённый полный original **45ZIP** + byte exact `cmp -s` по всем **193355 bytes**, SHA256 и 28×3 тестам [CI 40201692307](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40201692307) **SUCCESS 4/4**, witness `evidence/c58/C58_INDEPENDENT_ORIGINAL45ZIP_PREKNOWN_1H_INSIDE_WITNESS_20261025.json`.

## Цифры — только source parent research

| Состояние исходных 4H технических зон | BCH | BTC | ETH | SOL | XRP | Всего |
|---|---:|---:|---:|---:|---:|---:|
| Первый original3m contact не наблюдался | 3 | 5 | 5 | 5 | 3 | **21** |
| До контакта нет подходящего известного 1H уровня ВНУТРИ gap | 23 | 20 | 17 | 20 | 23 | **103** |
| Есть ранее известный непробитый 1H уровень ВНУТРИ gap | 6 | 5 | 9 | 6 | 3 | **29** |
| **Итого** | **32** | **30** | **31** | **31** | **29** | **153** |

29 source links: **18 BSL**, **11 SSL**; все строго не пробиты до начала first native3m contact в доступном source-префиксе. Категория `ONLY_PRIOR_SWEPT_1H_FRACTAL_LEVELS_INSIDE_4H_GAP` оказалась 0 для этого набора, но **существует** и протестирована. Ни 29, ни 18/11 не являются количеством сделок, IDM-входов, таймингом entry или вероятностью прибыльной сделки.

## Критика и сохранение исторических красных тестов

- [!] Первая негативная [CI 40201363229](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40201363229) **FAIL**: поддельный отрицательный 1H pivot level сначала отфильтровывался как outside 4H gap и не отклонялся. Это важный fail-closed дефект.
- [x] Исправлено commit `f36e188aefa98b760cbe94c64699bbb009b2dd2d`: **каждый** 1H source pivot полностью валидируется (Decimal finite price positive, known time, source raw ID, kind) ДО any temporal/price candidate selection. Затем 28×3 negative matrix [CI 40201503417](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40201503417) SUCCESS и два полных независимых original45ZIP replay успешны.

## Строгие ограничения

Нет авторского typed POI, tested POI, Strong High/Low, достоверного IDM, «ahead» классификатора, структурной SL/TP/FTA/entry-логики, авторски размеченных positive/negative 2023 кейсов, tick/fills, fees/slippage/OOS, реальных либо PAPER сделок. **Не разрешать торговлю из C58**, допускать эти 29 случаев только как гипотезы для дальнейшей source/semantic проверки. Любые 1H fractal BSL/SSL как Proxy не должны ошибочно стать Course Author IDM. Crypto only, академические EURUSD рисунки только логические примеры.

## Audit ledger

После этого отчёта можно **отдельно** append-once **A128**: шесть новых frozen files — module, 28 negatives, original45ZIP probe, полный original source JSON, независимый CI witness и этот report. Ранее A001–A127 SHA и source не изменять. Далее independent 128/128 SHA × Python 3.10/3.11/3.12, старый C46/C47/C55/C56/C57 exact frozen source blobs. Счёт укрупнённых вех 29 completed, 3 partial, 8 pending из 40 не повышать от source исследования.

**Следующий этап C59:** отдельное авторское Strong High/Low semantic precondition и подтверждение первой действительно подходящей 4H POI (не proxy). Потом 1H/15m подтверждение, Route B direct IDM without final Route A VC, перебирать ADAPTED версии только по независимым тестовым периодам, без подгонки и заявок.
