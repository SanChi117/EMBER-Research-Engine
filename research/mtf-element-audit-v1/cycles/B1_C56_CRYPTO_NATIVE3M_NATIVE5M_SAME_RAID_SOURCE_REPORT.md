# B1/C56 — original crypto native3m vs native5m on same 1H raid

**Дата:** 25.10.2026 UTC. **Scope:** CRYPTO ONLY, Binance USD-M BTC/ETH/SOL/XRP/BCH. **PAPER ONLY / NOT_TRADE_READY.** Академические графики — только примеры логики, не OANDA/SAXO или EURUSD исторические сделки.

## Гипотеза до скана

Route C_1H_RAID_3M_BOS и отдельный C_1H_RAID_5M_BOS не должны сливаться: сравниваем только истинный один и тот же 1H parent (symbol, BSL/SSL, fractal pivot center, first 1H breach start, fully confirmed next 1H close). 3m baseline — только заранее frozen LATEST_CONFIRMED_V1 из C37; запрещено ретроспективно выбирать среди EARLIEST/DEEP/NEAREST. 5m — только самостоятельный оригинальный Binance native5m C20B. Регистрировать время получения знания после ЗАКРЫТИЯ свечи, исходные raw SHA:bar_start, причину отсутствия события.

## Сделано [x]

- [x] Сверен HEAD 25.10.2026 e670fd9eb059ea06c47c331b32f20c83fac49c82, prior accepted A124, его SHA tip 90ff52f751ef4628288c78a64e350a307f1007206b8cbc465e930207e6b011fd, 6 frozen proofs, CI 40194511479 с 26 тестами по Python 3.10/3.11/3.12.
- [x] Написан новый tests/probe_c56_original_crypto_native5m_3m_same_raid_60zip.py; переиспользованы проверенные C08/C20/C20B/C21/C37 pipelines, старые исходные evidence не изменялись.
- [x] Заново скачано и проверено 60 оригинальных Binance USD-M .zip и .CHECKSUM: 30 native15m/1d, 15 native3m, 15 native5m. 76 800 оригинальных 3m, 46 080 оригинальных 5m, 15 360 exact native15m Decimal OHLCV равенств на каждом LTF, 3840 общих полностью закрытых 1H OHLC равенств.
- [x] Физический as-of crop на 2026-10-02 00:15 UTC сравнён с запущенным на полном оригинальном источнике ас-of сканом. Соблюдены preknown 1H fractal, первый 1H breach wick, подтверждение следующим закрытым 1H, known swing до начала 3m/5m BOS свечи, BOS только на CLOSE; исходные 3m и 5m ZIP SHA+row IDs различны.
- [x] Все 539 оригинальных native3m LATEST исходных событий равны frozen C37 source по целому каноническому JSON, все 512 native5m source событий получены отдельно. parent join только по точному 1H ключу.
- [x] Первичная source CI 40197404808 SUCCESS, 26 негативных тестов x Python 3.10/3.11/3.12 + все 60 ZIP. Frozen complete C56: evidence/c56/C56_ORIGINAL_60ZIP_SAME_1H_PARENT_3M_NATIVE5M_COMPLETE_SOURCE.json, **971017 bytes**, SHA256 **24db86b20e0454d6ac5abd1e4506f092f23d9c448d77c1862c3c777c40b7af07**, Git blob **98f087a731d30c2191dc443038c371751456f316**.
- [x] Независимый *второй* fresh re-download всех 60 source ZIP, byte-identical cmp -s / 971017 bytes / SHA256, Python 3.10/3.11/3.12 ×26 source negatives: **CI 40197616359 SUCCESS 4/4**. Сохранён evidence/c56/C56_INDEPENDENT_ORIGINAL_60ZIP_NATIVE3M_NATIVE5M_WITNESS_20261025.json.

## Наблюдения (только SOURCE CONTEXTS, не сделки)

| Символ | 3m | 5m | 3m раньше | 5m раньше | одинаковое close | только 3m | только 5m |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 99 | 94 | 70 | 17 | 6 | 6 | 1 |
| BTCUSDT | 104 | 101 | 75 | 19 | 6 | 4 | 1 |
| ETHUSDT | 129 | 122 | 94 | 16 | 11 | 8 | 1 |
| SOLUSDT | 103 | 98 | 68 | 25 | 5 | 5 | 0 |
| XRPUSDT | 104 | 97 | 78 | 14 | 5 | 7 | 0 |
| **Итого** | **539** | **512** | **385** | **91** | **33** | **30** | **3** |

509 общих исходных 1H родителей, 542 уникальных объединённых 1H родителей. В одном контексте может использоваться price-bar нескольких parents; коррелированные события нельзя объявлять независимыми торговыми возможностями или винрейтом.

## Опровергнуто и исправлено

- [!] Первая CI 40197312055 FAIL на сравнении Python tuple defaults в dataclass с JSON list в frozen C37. Ни один C37 event не заменён и C56 файл при FAIL не заморожен.
- [x] Исправлено commit a5cefb82dcb31bed891f57eb81be57daa60b1a11: сравнение полного JSON после его канонической сериализации/декодирования, без изменения цен, timestamps, исходных ID. Полный повтор 40197404808 и независимый 40197616359 PASS. Красная CI сохранена в истории.

## Непроверено [~]

НЕТ авторских размеченных 1H liquidity / 3m или 5m BOS swing goldens, Strong High/Low, оригинального корректного 4H POI, первого допустимого POI касания, VC, FTA, SL/TP, OOS, реальных fills, комиссий и проскальзывания. 32 дня / 5 crypto инструментов не доказывают качество торговли. Author-approved entries = 0; orders = 0; trades = 0; PnL отсутствует. Crypto-only, PAPER ONLY / NOT_TRADE_READY.

Дополнительный 13MB C55 lifecycle source и его независимая CI успешны, но это НЕ одна из шести evidence A124 и НЕ часть данного C56 A125; не записывать A124 задним числом, сохранить для отдельной будущей приёмки.

## Ledger / следующий этап

Выбранная область единственного нового A125: C56 source-only 60ZIP parent-matched replay, 26 ×3 negatives, независимая 4/4 byte-exact CI. Append once только по выбранным 6 frozen файлам после этого отчёта и witness. Отдельный финальный контроль 125/125 SHA обязателен, до него статуса accepted A125 нет. В карте разработки укрупнённые 29 [x] / 3 [~] / 8 [ ] из 40 не изменяются.

После A125 — самостоятельное отдельное доказательство C55 extra lifecycle, затем академические Route A IMB/SNR, B IDM и genuine 1W/1D → 4H typed POI → 1H → 15m, отдельный 1H → 15m → 5m VC, no-lookahead, без подгонки, PAPER only.
