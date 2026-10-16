# D05/F03 — оригинальный Binance USD-M Futures 5m source bridge (BTC, 2026-10-02)

**Дата:** 2026-10-16. **Статус:** SOURCE_5M_ORIGIN_AND_15M_PARITY_VERIFIED_SINGLE_DAY_SINGLE_SYMBOL, **НЕ** академический VC/сетап. PAPER ONLY.

## Исходная причина

Курс TDA требует отдельный **5M VC** в маршрутах GREEN и BLUE, и подтверждённые C08 315/315 архивов содержат **15m и 1d**, но **не 5m**. Делать 5m proxy из 15m нельзя. В отдельном новом F03 создан полный проверяющий 5m источник, **без изменения первоначального SHA-замороженного C08**.

## Сделано: источник→ценовая свеча→тест

- `d05/f03_5m_original_source.py`: отдельный strict allowed 5m archive URL на `data.binance.vision` (только USD-M Futures, пять допустимых монет), original raw ZIP с одним ожидаемым CSV, вся таблица из **288** последовательных 5m, 12 raw полей включая timestamps, trade count, taker volumes, OHLCV, HEX SHA ZIP+CSV, две TLS same-host проверки ZIP+.CHECKSUM. Без получения закрытой третьей 5m свечи classic IMB не появляется; используется существующий неизменённый `confirmed_imb` v05. Выдача **всегда NOT_TRADE_READY**.
- `d05/test_f03_5m_original_source.py`: **23 adversarial unit** сценария: 287/289 свечей, внутренние пропуски, wrong close_time, неправильная OHLC/volume/NaN, ZIP с лишним/неожиданным членом, неверная checksum SHA/filename, Spot/15m/unknown symbol/wrong date/HTTP URL, future as-of, защита от самовольного READY.
- `tests/probe_f03_binance_original_5m_15m.py`: независимо скачаны original BTCUSDT 5m и прежний подтверждённый оригинал C08 15m за **2026-10-02**; **каждые три 5m бара точно совпадают по O/H/L/C/V с одним исходным 15m**, включая open/close UTC time. **96/96 совпадений** без допусков.
- `evidence/f03/F03_BTCUSDT_5M_2026-10-02_ORIGINAL_RECEIPT.json`: впервые извлечённые hash-данные SOURCE 5m закреплены отдельно; CI проверяет фиксированный Git blob **`7e5bc374b4e4cceaf01325b16e42631dad0ec9db`**, а реальный HTTPS 5m ZIP обязан заново совпасть с двумя pinned SHA. **C08 содержимое не модифицировалось**.

## Проверенный реальный источник

- 5m URL: `https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m/BTCUSDT-5m-2026-10-02.zip`
- 5m ZIP SHA256: `2a492563746eba6c3689b90c00a081bfce3ceab86a06493e80f22c4d55e8c7ea`
- 5m raw CSV SHA256: `14dc88dd66d78f44b73daa9243d62e35d539ace64d26adb0ba4b32aefb599c73`
- 15m C08 original ZIP SHA256: `62742a246cee4ec9363e96f2270e00e9f23fd54f137c08ba732113a7a2e284be`
- 288 закрытых 5m, 96 закрытых 15m; **96/96 OHLCV parity**, оригинальный интервал 00:00–24:00 UTC.
- `confirmed_imb` v05 на 5m нашёл **60 классических геометрических IMB-кандидатов** в этом дне, **НЕ 60 торговых сигналов или авторских VC**.

[GitHub Actions 38871920364](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38871920364) — первичный **SUCCESS 23/23 + real ZIP**, [38872110916](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38872110916) — повторный **SUCCESS** уже с криптофиксацией нового F03 receipt и прямой сверкой полученного ZIP/CSV с зарегистрированными SHA.

## Фальсификация и что остаётся не доказано

1. Верификация D04 прежних 315 архивов остаётся **буквально неизменной**. Новый изолированный F03 receipt — **1 день × 1 монета**, не расширение C08 315/315 задним числом.
2. Same-host `.CHECKSUM` + HTTPS/TLS — сильнее офлайн-хеша, **но не цифровая подпись Binance**, не гарантия защиты при взломе исходного сервера.
3. Три бара original 5m воспроизводят original 15m OHLCV, но не гарантируют, что каждый найденный FVG/IMB отвечает правилам Strength, HTF Context, Liquidity, StrongHL и Volume Confirmation курса.
4. Историческая доступность этого 5m источника **не снимает** необходимость проверить авторские входные контракты 5M VC и полноценную multi-TF цепочку. GREEN/BLUE остаются **NOT_TRADE_READY**.
5. Встроенная структура `Verified5m` удостоверяется отдельным HTTPS-прогоном и fixed Git receipt; произвольно созданный объект Python не даёт сам по себе сетевую аутентичность, нельзя доверять claim без pinned archive evidence.
6. История ещё не включает *много дней/все монеты* на 5m. Следующий цикл расширит coverage либо независимо проверит 1H raid→5m BOS на реальных барах, не приписывая авторски одобренные сигналы.

**Не изменены**: source course-v05, D03, C08, EMBER trading core, SMOKE, V5/QFVG, Binance user orders. **Никаких ордеров, PnL или оценок доходности нет.**
