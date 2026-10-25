> **ЗАКРЫТО КАК НЕСООТВЕТСТВУЮЩЕЕ ОБЛАСТИ ПРОЕКТА — 2026-10-25.** Владелец уточнил: **EMBER только для криптовалют; изображения академии — примеры торговой логики, а не источник для восстановления EURUSD/OANDA/SAXO сделок.** Предлагаемый следующий поиск исторических FX свечей, OANDA/SAXO доступов и C53 FX market-golden **ОТМЕНЁН**. Этот документ сохраняется как архив обоснования ограничения данных (никаких сделок и оригинальных FX OHLC нет), но **C53 не принимать за этап рабочей криптостратегии и не включать в текущую активную разработку**. Исходные PNG академии используются как качественные примеры POI/IMB/SNR/RB/OB/реакции/таймфреймов независимо от инструмента. Активный следующий цикл **C54 — проверяемый перенос академической логики на оригинальные Binance USD-M криптовалютные свечи; PAPER ONLY**.

# B1/C53 — восстановление академических FX-источников: проверка поставщика и отсутствие подтверждённого барового эталона

Дата 2026-10-24. Режим **PAPER ONLY / NOT_TRADE_READY**. Это независимая source-only проверка того, можно ли доказать совпадение оригинального учебного EURUSD графика и определённых исходных рыночных свечей. Результат **не выдаёт ордеров, не открывает позиций, не рассчитывает доходность**, имеет ноль author goldens.

## 1. Что было установлено в C52/A122

Исходные 49 PNG автора с Google Drive действительно просмотрены; восемь имеют разборчивые подлинные заголовки TradingView:
- OANDA EURUSD 4H — **3** изображения; 1H — **2**; 15M — **1**. Из них пять опубликованы 2024-05-26, одно 2025-01-20.
- SAXO EURUSD 4H — **2** изображения, опубликованы 2025-01-07.

Даты публикации НЕ времена изображённых свечей, и котировки не являются original Binance USDM криптоданными 2026. Контроль C52/A122 принят независимо: [CI 40100900983](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40100900983) **122/122 SHA SUCCESS 3/3 Python**, tip `5cd047c7ab3afff3b099766d77f4d11bd882c14d6a023361942048afcad4b428`, весь оригинальный 49-объектный метаJSON Git blob `4a06ac1e1ed846f3c23adb4dba7d6f56b6afba67` неизменён.

## 2. Проверены официальные источники OHLC, но настоящие бары без доступа не выдуманы

* [OANDA REST v20 Instruments Candles](https://developer.oanda.com/rest-live-v20/instrument-ep/) / [Pricing API](https://developer.oanda.com/rest-live-v20/pricing-ep/) — авторизованный endpoint для `EUR_USD`, granularity M15/H1/H4, `from` / `to`, `price=M/B/A`, `complete`; есть `dailyAlignment` и `alignmentTimezone`. OANDA сама предупреждает, что historical base price group может **отличаться от live chart/account pricing**. Нельзя предполагать, что MID, BID и ASK взаимозаменяемы, а H4 обязательно начинается в каждый час UTC с индексом 00,04,08,12.
* [Saxo OpenAPI /chart/v3/charts](https://developer.saxobank.com/openapi/referencedocs/chart/v3/charts/get__chart) — получение исторических chart bar OHLC по UIC/AssetType/Horizon/Time/Count; Forex содержит **Bid/Ask**, для получения нужны права доступа. Не копировать OANDA-скриншот на Saxo цену и не заменять котировки Dukascopy/Binance.

**В этом исследовательском цикле отсутствуют авторизованные оригинальные рыночные EURUSD-свечи ровно из TradingView OANDA/SAXO снимков.** Не выдавать guessed OHLC, ticker, UIC, price side, chart bar UTC-time за полученную настоящую историю.

## 3. Что реализовано технически

`d05/c53_fx_provider_original_source_attestation_gate.py`: отдельный строгий data receipt gate, 8 source figures из C52. Принимает источниковой бар ТОЛЬКО как исследовательскую запись `SourceBarReceipt`, с обязательными: OANDA/SAXO original provider, EURUSD, TF, выбранная ценовая компонента MID/BID/ASK, аутентичный provider-host HTTPS, оригинальный byte digest и ID свечи, Decimal OHLC, вменяемый коридор forex, `fully_closed`, причинная граница `start→close`, отсутствие будущего. Специально **не** навязывается ошибочная привязка 4H к `UTC % 4H = 0`: H4 у OANDA допускает broker daily alignment; требуются только надёжные часовые границы и правильная фактическая длительность.

Важнейшее временное ограничение: **подлинная исходная рыночная свеча должна завершиться не ПОСЛЕ timestamp публикации изображения**. И наоборот, дата публикации не присваивается свечам как их фактическое время.

Даже если валидный provider-only receipt когда-либо появится, gate возвращает `PROVIDER_ONLY_SOURCE_RECEIVED_CHART_CANDLE_UNALIGNED`, то есть **НЕ готовый авторский POSITIVE**; требуется визуально доказанное выравнивание графика к raw source candle/price component и авторская семантика POI→test→trigger/VC→StrongHL/FTA. Никакой live order code.

`d05/test_c53_fx_provider_original_source_attestation_gate.py`: **43** independent cases × Python 3.10, 3.11, 3.12. Включены отрицательные проверки: чужой провайдер и TF, поддельный адрес источника (даже если содержит слово 'oanda'), MID/BID/ASK несовпадение, форженная сделка и авторский golden, пустой digest, source-bar rawID, future после публикации изображения 2024 или 2025, NaN/невалидная FX OHLC, H4 time alignment и правильный 15M. [CI 40101543442](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40101543442) **SUCCESS 3/3 Python**, 43/43 на каждой версии.

`tests/probe_c53_all8_owner_course_fx_original_vendor_gate.py`: источник из C52 маркирует **все 8 оригинальных FX изображений** как `SOURCE_NOT_RETRIEVED` (ни один historical raw candle не сопоставлен), записывает потребность в OANDA M15/H1/H4 и SAXO H4, 6 академических author-label blockers и обязательное неопознание MID/BID/ASK. Frozen report `evidence/c53/C53_EIGHT_ORIGINAL_FX_ACADEMIC_CHART_SOURCE_PROVIDER_PREFLIGHT.json`, **11 871 байт**, Git blob `c38da1ec093bc37006942f7206018288e8884240`, SHA256 `01464f1a7b92f1185137b024d730a9bd7fbd39457c787935e46b65f8b7c7a61a`. Первый complete manifest [CI 40101699823](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40101699823) **SUCCESS**.

## 4. Что не доказано и не замещается моделированием

- 8/8 original FX market OHLC sets **NOT RETRIEVED** (не выдумывать source raw).
- 0 author chart 2023 actual positive/negative goldens; изображения опубликованы в 2024/2025, сами рыночные события требуют отдельного timestamp source reconciliation.
- 0 verifiable actual 4H academic typed POI first test, 1H contextual VC/trigger, 15M entry VC, структурных оригинальных SL/TP, реальных fill, PnL и held-out OOS.
- Нет разрешения на торговлю, paper-only исследования без исполнимых сигналов.

## 5. Независимая приёмка и следующий этап

Только после независимой CI полного C53 source-only manifest byte-to-byte, 43×3 negative, A123 append-once SHA и независимой 123/123 ledger проверки эта часть gate принимается как **[x] этап контроля качества данных, НЕ [x] реконструкция исходной академической сделки**.

Далее требуется законный точный оригинальный провайдер EURUSD M15/H1/H4 в исторические интервалы, сначала OANDA 2024 и Saxo 2025. Сохранить price side / feed group / alignment / chart source provenance; если authenticated raw bars недоступны, C54 должен иметь статус **UNKNOWN + отсутствие авторских эталонов**, а не использовать чужие котировки ради «совпадения». PAPER ONLY / NOT_TRADE_READY.


## 6. Независимая проверка первой заморозки завершена

[CI 40101894607](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40101894607) **SUCCESS 4/4**: отдельный source replay **побайтно** повторил весь 11 871-байтный C53 JSON, Git blob `c38da1ec093bc37006942f7206018288e8884240`, SHA256 `01464f1a7b92f1185137b024d730a9bd7fbd39457c787935e46b65f8b7c7a61a`. Три независимых матричных Python 3.10, 3.11, 3.12 jobs повторно прошли все **43/43** negative anti-forged market/candle/author tests, проверили неизменную предыдущую цепочку A122 (122/122) и шесть C52 SHA доказательств. Свидетельство `evidence/c53/C53_INDEPENDENT_FX_VENDOR_SOURCE_GATE_WITNESS_20261024.json` фиксирует неизвлечённые 0 original FX OHLC, 0 авторских goldens и отсутствие API-токенов.

Для принятия *source preflight / missing-vendor-feed gate*, но **не** полностью воспроизведённой академической торговой системы, требуется append-once A123 и независимый 123/123 SHA CI.
