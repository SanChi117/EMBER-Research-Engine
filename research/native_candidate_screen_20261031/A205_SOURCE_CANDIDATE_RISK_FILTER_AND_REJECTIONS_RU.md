# A205 — техническое сито 8 открытых стратегий до новых дорогих тестов

Дата 2026-10-31. Все ссылки на внешние рейтинги — вторичный источник; это **НЕ** независимые торговые результаты EMBER. Цель — не переизобретать отрицательные кандидаты; хранить исходники и реестр отказов.

| Исходник | Source class | Что реально есть в коде | Почему допущен / отсечён |
|---|---|---|---|
| `Meszqt/freqtrade-test@7062cdd4` | AggressiveSupportResistanceScalper | закрытая предыдущая 48×5m S/R зона, фитиль отбой, RSI/EMA, 10x (6% equity-risk ≈0.6% price), TP11% маржи, time exit90m, нет DCA | **A205 TEST NOW** на независимых 2025/2026; исходный рейтинг PF1.86, но всего 381/33 пары/3 года, очень редкие входы, и в рейтинге 46h avg hold вопреки 90m exit — сомнение/гейт |
| `win-boom/BTCquant@main` | Winner15m | 15m EMA/MACD/ADX/ROC, stop2.5% price, состояния входа много баров подряд, нет time limit | **REJECT FOR EVENT-ENTRY**: высокая частота исходного рейтинга получена при постоянной готовности повторно входить, исходник без one-shot edge; не считать событием |
| `win-boom/BTCquant@main` | MTF_Hybrid | `ema200_1d` есть `EMA(close,19200)` на 15m, startup500 vs требуются 19200 баров, не настоящая daily informative свеча; PF≈1.08 внешне | **REJECT** ненадёжная warmup/«1D» маркировка, состояние сигнала; не выдавать за true MTF |
| `TheoBrigitte/freqtrade@c9def379` | RsiquiV5 | centered `np.gradient` внутри полного ряда | **REJECT** истинный future dependency на прошлых сигналах; original can't be backtested as causal |
| `jaredrsommer/freqtradestrategies@9d66f71c` | FVGChannel | TF1h, исходный SL10% price, форсированная ширина FVG 23.67% цены | **REJECT** уровень FVG сконструирован эвристически, а не реальная локальная 4H структура |
| `jaredrsommer/freqtradestrategies@9d66f71c` | 2Candle | `class 2Candle` невалидный Python identifier, нет `can_short=True`, комментированный `1% stop` фактически `stoploss=-0.03`, ROI1.5% | **REJECT** source not directly runnable и ложная документация стопа; rewriting changes candidate |
| `cheafi/trading-team@5a8336d6` | A51Strategy | 5m S/R/VWAP, stop0.5% price, TP0.8%, но сам автор в TODO.md приводит 2021–25 backtest −2.94% за пять лет и PF0.60 за 2023–25 | **REJECT** нет основания повторять на уже изученных годах, автор признал отрицательную доходность |
| `IvPalmer/Master-Trader@main` | BearRegimeShortV1 | 1h, short-only BTC bear breakout, stop5% price, 2x, time exit36h | **ARCHIVE** хорошая идея режимного фильтра, но не соответствует короткой 5m/15m частоте/обеим сторонам, можно использовать лишь как контекстный BTC gate |

### Что здесь нельзя делать
- Подменять 1×,10× или 20× при сравнении без явной пересборки и адаптации рисков. Для оригинала A205 6%-risk stop при 10× ≈0.6% PRICE, но комиссия 0.05% PRICE на сторону становится 1% margin roundtrip при10×. Плечо не повышает математическое ожидание, а поднимает чувствительность к издержкам и ликвидации.
- Подгонять параметры задним числом. Если A205 по одному году/fee убыточен или имеет недостаточно сделок — FAIL, даже если отдельный ETH-участок красивый.
- Использовать число закрытых сделок как число **независимых** подтверждённых A+ сетапов; обязательны reentry/occupancy/hold metrics.
- Назвать Freqle OOS; там 2022–24, 33 пары и 10 слотов, а тесты EMBER совсем другой universe/timeframe detail/config.

Результат самого A205 будет только в `A205_SR_ORIGINAL_TWO_YEAR_NATIVE_VERIFIED.json` или в отдельном FAIL/BLOCKED отчёте по подтверждённым логам. Существующие SMOKE, PAPER scheduler и live trades не затронуты.
