# A232 — результаты переоценки оригинальной Double MA: все 4 пары, оба периода, обе комиссии

31 октября 2026. **A232 = ретроспективная forensic-арифметика первоначальных исходных торговых журналов. НЕ новый независимый forward/OOS тест, НЕ новый алгоритм.** Отдельно сохраняются ВСЕ отрицательные сделки и убыточные пары.

**Исходник:** `MirrorNew/2026DoubleMaFuturesStrategy` commit `40af5c7c1c44253766428cfb06babf22f9817aa4`; авторский Git blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`; настоящие Binance USD-M OHLCV/funding/mark, native Freqtrade 2026.4, `--timeframe-detail 5m`, оригинальные 2x и $10k отдельный wallet/pair, оригинальные структурные stops, комиссии на сторону `0.05%` и `0.125%`. Никаких правок к источнику, сигналам, параметрам или поиску лучших монет.

**Независимый повторный анализ всех 16 оригинальных Freqtrade ZIP:** [CI success 41237610006](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41237610006), artifact `a232-original-doublema-all-four-assets-two-regimes-genuine-pnl`, id `13055982327`, SHA256 `7b58010ad24fdff45bddda3ce4164e11ec577adcd14bd94aa9aabd3c514d9c4a`. CI взял **ровно 8 оригинальных** ZIP A197 за 2025 [run 41149728068](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41149728068) и **8 оригинальных** ZIP A196 за 2026 [run 41148069316](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41148069316); независимо извлёк `strategy[VideoDoubleMaFuturesStrategy].profit_total_abs`, число закрытых сделок и DD по каждой монете. Равная раздельная капитализация `4 x $10k`; средняя portfolio-sleeve доходность = total profit_abs / 40000.

| Исходная 4-составная корзина BTC ETH SOL LINK | BASE return | STRESS return | Native completed trades |
|---|---:|---:|---:|
| Apr–Dec 2025 | **+18.502687%** | **+7.149636%** | 164 |
| May–Sep 2026 | **+12.400401%** | **+5.576630%** | 101 |

При STRESS результаты *включают* отрицательные пары: 2025 BTC +26.50%, ETH +19.47%, SOL −2.69%, LINK −14.68%; 2026 BTC −22.69%, ETH +12.70%, SOL +14.54%, LINK +17.75%. Не удалять проигравших. Значения округлены для таблицы; полные float значения в JSON артефакте.

**Значение:** отрицательный gate на отдельных монетах **не доказывал отрицательный combined net**. Double MA заслуживает дальнейшей проверки в полноформатном USDT-M портфеле, если нет скрытых общих margin/fill/liq проблем. Но накопленная доходность двух периодов **не даёт** статистического подтверждения стабильного преимущества: периоды разной длины, 2025 до публикации исходника, автор мог видеть данные, 2026 не является ещё не увиденным рынком, а агрегирование четырёх sleeves — ретроспективный diagnostic после прежних результатов. **Нет одной моделируемой общей equity curve и истинной correlated max drawdown; 2x, большие stakes, лимитки и отсутствие реального orderbook/mark stop trigger не допускают сейчас PAPER-подключения.**

Техническое уточнение старых тестов: оригинальные A196/A197 **уже включали** `--timeframe-detail 5m`; класс автора **не определяет** `protections`, так что проблема A230 «пропущен --enable-protections» к нему напрямую не относится. Источник `startup_candle_count=499` и использует дополнительные 4h/1d context; полный recursive/causality callback с риском 2x и реальным orderbook всё ещё требует верификации.

Статус: `REOPEN_PRIORITY_ONE / HISTORICAL_FOUR_SLEEVE_POSITIVE / NOT_VERIFIED`. Не переподбирать валюты, пороги, source params, плечо на известных 2025/26. Следующее обязательное событие для решения — *проспективный* вневыборочный PAPER после строгого теста shared capital, original config, official mark/liquidation, realistic order fills; текущие планы пользователя не менять.

No trading orders. No modifications to registered negative results or locked mandate.
