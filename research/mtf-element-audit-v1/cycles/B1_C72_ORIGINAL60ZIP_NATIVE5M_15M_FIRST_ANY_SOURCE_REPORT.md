# C72 — оригинальные Binance 5m после возможного 15m Trigger, независимое доказательство 5m/15m

**Дата UTC: 25.10.2026. Репозиторий:** `SanChi117/EMBER-Research-Engine`; ветка `research/academic-engine-recovery-20261015`. **PAPER ONLY / NOT_TRADE_READY / orders=fills=trades=0.**

## 1. Точное правило учебного курса (не выдавать source за author)

Прочитанный ранее и подтверждённый настоящий `2. Entry by IMB & SNR.txt` (Google Drive ID `1hkKKwy60-VIoqEsVYAq12mnPZA7ySXFQ`): при **действительном** тесте 1H POI и наличии **15m Trigger SSL/BSL/допустимой IMB** вход ждёт **5m VC IMB/SNR**. **Если 15m Trigger отсутствует**, ожидается **15m VC IMB/SNR**, а не искусственное 5m подтверждение. Исходная 1H POI должна действительно быть VC реакцией от 4H POI/liquidity, не просто геометрический 1H gap. Авторская `Strong High & Low.txt` (ID `1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t`): только настоящий контакт liquidity **ИЛИ** inefficiency, **ЗАТЕМ** реальный VC POI или BOS. Оригинальные примеры курса являются примерами логики; криптографически зафиксированных `symbol+UTC+ZIP SHA+author positive/negative label` крипто-случаев пока **0**.

## 2. Выполнено

- [x] `d05/c72_original_native5m_source_vc_after15m_gate.py`: новый **настоящий raw original 5m Binance USD-M**; separate valid `https://data.binance.vision/data/futures/um/{monthly|daily}/klines/SYMBOL/5m/SYMBOL-5m-DATE.zip` с очень узким whitelist из 5 проверенных монет и 3 дат, single-host HTTPS redirect, соответствующая **same-host .CHECKSUM**, ZIP SHA256, raw CSV SHA256, ZIP один CSV без path/extra files, 12 исходных Binance столбцов, строгая последовательность 5m timestamps, свеча реально закрыта, точный Decimal OHLCV, отсутствие пропусков, ограничение размера. **Same-host CHECKSUM — не подпись внешнего независимого источника**, не заявлять иначе.
- [x] По каждому символу **3 оригинальные новые 5m архива (September monthly, 1 и 2 October daily)**: 9216 native5m = 3072 уже неизменных source native15m. **Ровно 3 ORIGINAL независимые 5m** должны дать **тот же Decimal O/H/L/C/sum(V)** и реальные SHA:timestamp source IDs как раньше original C08 15m. Не resample из 3m и не имитация native5m.
- [x] Строго source-only 5m IMB: только **3 полностью закрытых реальных original5m свечи с разрывом WICK**, не body gap. 5m SNR: две разнонаправленные свечи, следующая 5m confirmation close, плюс взаимодействие с **ранее** известным локальным liquidity-fractal или старым 5m IMB; голый opposing pair (MB) исключён. Авторское VC и 5m StrongHL **не доказаны** геометрией. Route A `NEW_1H_VC_POI` C71 source branch и **первое** 15m IMB/SNR техническое подтверждение, только затем кандидат FIRST ANY *будущего* полностью закрытого 5m IMB/SNR, чей **весь pattern стартовал после** 15m полного закрытия. Opposite source event первее veto, одновременные kinds/sides ambiguity. Окно 24 часа + right-censor. При истинном авторском отсутствии 15m Trigger нужен 15m VC, а не C72 5m; для этих данных owner Trigger **остаётся UNRESOLVED**, никакого fake branching.
- [x] Отдельные Route B IDM / Route C raid→3m/5m BOS не изменены. Ни одного stop/target/entry/order/fill/trade/profit и ни одного author-positive криптопримера.
- [x] `d05/test_c72_original_native5m_source_vc_after15m_gate.py`: **30 adversarial negative** тестов × Python 3.10, 3.11, 3.12: forged native5m IDs, actual 3m vs 5m source, подмена author 15m Trigger или VC, futures events, first ANY opposite, two sides/kinds ties, technical 5m fractal and IMB as-of, bad ZIP checksum, unknown URLs/symbol/date, no prior 1H POI branch, 15m pattern closing time/5m start, empty source, no trades. [CI 40228372479](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40228372479) **SUCCESS 3/3**.
- [x] `tests/probe_c72_original60zip_native5m_to15m_first_source_vc.py`: **60 оригинальных Binance архивов** в полном прогоне (45 pinned прежних — исходные 3m,15m,1d, **15 реально новых native5m**) × **2 независимых скачивания всех архивов**, отдельные native5m ZIP SHA+CSV SHA для 15 new archives; 5 монет BTC/ETH/SOL/XRP/BCH, 32 дня с **2026-09-01 по 2026-10-02**. **76800 original3m, 46080 original5m, 15360 original15m, 160 original1d, 3840 derived closed1h**. **15360 из 15360** original native15m сверены по исходным 5m 3-to-1 Decimal OHLCV. Все 153 C46 технических parent + неизменённые C60/C62/C63/C66/C67/C68/C69/C70/C71 raw ZIP SHA:timestamps и source OHLCV пересчитаны, без редактирования старых frozen artefacts.
- [x] Первый оригинальный full60 ZIP [CI 40228652375](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40228652375) **SUCCESS 5/5**; второй fresh source60 ZIP independently byte exact [CI 40228845271](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40228845271) **SUCCESS 4/4**. Полный `evidence/c72/C72_ORIGINAL60ZIP_NATIVE5M_15M_PARITY_AFTER_C71_SOURCE_VC.json`: **197266 байт**, SHA256 `3541b5a7f6f8fa9d16dabd28c944343b8e65e1f0055942d3c25b55ee46a22acf`, Git blob `19b7e0357600b70b3f26467339a417e0f99a1302`. Второй independent witness `evidence/c72/C72_INDEPENDENT_ORIGINAL60ZIP_NATIVE5M_SOURCE_WITNESS_20261025.json`.

## 3. Результат оригинальных криптосвечей — 153 source контекста 4H

| Первое native5m событие **после** source C71 15m pattern полного закрытия | Source count |
|---|---:|
| Нет единственной подходящей source 1H NEW POI → 15m ветви C71 | **141** |
| Первый source 5m IMB совпал по направлению, **не author VC** | **3** |
| Первый source 5m SNR совпал по направлению, **не author VC** | **1** |
| Первый future source 5m event оказался **противоположным** | **5** |
| Первые 5m source событий имели разные kinds одновременно, выбрать нельзя | **3** |
| **Всего** | **153** |

Из **12** условных C71 source 15m NEW 1H POI cases только **4** имеют следующее совпадающее техническое 5m наблюдение, **5** имеют первоочередное противоположное, **3** ambiguous. Эти counts **НЕ** независимые trade setups, не author 5m VC, не winrate, не profitability. Авторский валидный первый тест 1H POI, 15m Trigger, true volume confirmation, StrongHL, FTA/SL/TP по-прежнему **не сертифицированы**.

## 4. Контрпроверка / сбои

Первый полный 60 ZIP [CI 40228571926](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40228571926) корректно остановился: старый `strict_vision_d04.parse_url` жёстко поддерживал архивы более ранних 3m/15m/1d и **отвергал новую 5m URL**. Реализован отдельный source5m *строго валидирующий* downloader с тем же restricted host/redirect; старый whitelist и frozen original ZIP не ослаблены. Последующие **два** 60 ZIP прогонa 3:1 parity и полное JSON byte equality успешны. Нельзя путать собственную source SHA проверку с независимой подписью Binance.

## 5. Следующий C73 — не выполнен

**Главный незакрытый академический gap:** валидная 1H POI selection и настоящий **first VALID** тест на авторски размеченных crypto candles, distinction 15m Trigger vs 15m VC, независимая проверка 5m VC с первичными `author positive/negative` кейсами. Далее настоящая StrongHL подтверждённая после реальной реакции, правильный structural SL/FTA/TP, OOS PAPER only (комиссии, проскальзывание, стоп первым при одном баре), без lookahead, затем интеграция в SMOKE. Данные C72 подготовлены, но **не подтверждают** вход в криптосделки.

## 6. Приёмка SHA A142

**6 SHA evidence receipts:** `d05/c72_original_native5m_source_vc_after15m_gate.py`, `d05/test_c72_original_native5m_source_vc_after15m_gate.py`, `tests/probe_c72_original60zip_native5m_to15m_first_source_vc.py`, frozen full 197266-byte original source JSON, independent witness и **этот report**. После второй независимой 60 ZIP/30×3 append A142 only once, проверка 142 SHA Python3.10/3.11/3.12, frozen C46–C71 unchanged. Previous A141/141 SHA tip `9f6e2a7bb92e9b105e446be0f0e0c6c0397359a74f25071ada0297cb099e6a9f`. После записи A142 никогда не редактировать ни один из шести SHA-evidence, только handoff/map.

**CRYPTO ONLY / PAPER ONLY / NOT_TRADE_READY / orders=0 / fills=0 / trades=0.**
