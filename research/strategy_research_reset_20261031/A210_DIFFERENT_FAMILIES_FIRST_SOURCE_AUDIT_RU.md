# A210 — первая очередь кандидатов после отмены искусственных ограничений

Статус: **source-screen only, без новых PnL-результатов**. Продолжение регламента `A209_EDGE_FIRST_RESEARCH_CHARTER_RU.md`. Дата 2026-10-31.

## 1. Первый экономический цикл: дневной тренд, допускается long-only / long-short

Публичный источник: [`Kureshi25/cryptobot`](https://github.com/Kureshi25/cryptobot), pinned ***original files***:
- `user_data/strategies/TrendFutures.py`, Git blob `2e6b83ba128373655090ca4827d8c7954ffaedfd`; класс `TrendFutures`, `timeframe=1d`, `can_short=True`, Donchian 20-day breakout against preceding rolling highs/lows, EMA200 context, channel10 exit, ATR stop, original default 1×, market entry/exit. Stoploss disaster fallback -35% price, dynamic ATR stopper; **проверять именно реализацию стопа, не считать автоматически «защитным -3%»**.
- `user_data/strategies/TrendBreakout.py`, Git blob `48884fdee7a0e3c1eb1a0cbdbdd438e35b91ddd0`; класс `TrendBreakout`, 1d `can_short=False`, similar Donchian20/10 + EMA200, 1× spot-native LIMIT entry/exit. Это long-only **контроль того же механизма, не независимая торговая гипотеза**, так как вход и источник почти одинаковы.
- `user_data/strategies/AdaptiveRegime.py`, Git blob `7b0f5fbe2157d45ef52e4ee48155c06f3f057628`; `AdaptiveRegimeLong.py`, Git blob `306d34f7f9acffdc3f57a105fd7738b3283c65ce`; 1d trend/range classifier with Kaufman efficiency. **Больше параметров и потенциальная post-hoc подгонка** — оставить как отдельный challenger после строгого source check.
- Авторская README признаёт: `TrendFutures` на полном своём sample 1× `$1000->$335` (−66.5% при 156 trades), несмотря на walk-forward mean +4.2% OOS и 2/4 положительных окна (CI от −29.7% до +38.0%). Это НЕ перспективный «проверенный победитель», а честный **нулевой/отрицательный контроль** trend-following. Снова перебирать его hyperopt ради зелёной истории запрещено. Исследование нужно лишь для причинных сравнений с простым ETF/спотом/кэшем на новых данных. Утверждения автора не заменяют наших trade ZIP.

**Техническая предварительная проверка:** нужна genuine Binance дневная USD-M OHLCV и mark/funding за достаточно длинный непрерывный период: EMA200 + startup220 дней требует минимум 220 предшествующих 1d свечей; A195/A196 5m May–Sep **не годятся** без полноценной 1d предыстории. Для 2024–26 понадобится год или более warmup, timestamp 1d candle known only at UTC close. Не разрешать lookahead по `crossed above` из незакрытого дня. Во Freqtrade custom_stoploss проверить `after_fill`, confidence in next-day stops, exit timing and fees. **Не запускать без пререгистрации и данных.**

## 2. Второй принципиально иной экономический цикл: delta-neutral spot/perp funding carry

Публичный **сканер**, а не готовая торговая стратегия: `Kureshi25/cryptobot:funding_scan.py` blob `606081f5e361d2b73fe52ee908be8c691d58498f`; `selectivity_test.py` blob `aa055677a2ae7cbc22d3c2ec1bb7027609dee248`.
- Идея: long spot + short matching perpetual на одну и ту же базовую монету, collecting positive net funding, вдобавок считать residual basis и 4 legs fees; long-short hedge должен быть одновременно исполнимым.
- Документ `funding_scan.py` проверяет реально существующую ликвидную spot-leg и процентное funding в отдельных venues. Это **source-only**, а не подтверждённый торговый PnL.
- Стратегия не market-directional, зато новый failure mode: negative funding flips, divergent basis, price difference between exchanges, execution one-leg-first, settlement/counterparty risk, liquidation margin. При капитале малой величины возможен NO-GO из-за min notional/hedge collateral даже при положительном theoretical yield.
- Пререгистрация: источник point-in-time spot+perp prices same exchange/venue, historical funding settlement, historical spread or conservative proxy; roundtrip both legs all taker by default, opportunity costs and both collateral legs. Сравнить buy-and-hold spot, cash USDT, carry exposure-rebalance, reality of min positions. **Не считать историческую сумму funding без хеджа доказательством PnL**.
- `selectivity_test.py` моделирует funding-only and one RT fee and assumes fixed capital multiplier 1.5, но не ведёт mark-to-market basis/hedge/maintenance margin or pair legs; это гипотеза и отдельный negative-control engine, НЕ финальная модель.
- Для этого типа неуместны требования количества сделок и TP/SL=1:2.

## 3. Третий независимый кандидат: 1h long-only momentum/pullback

Публичный source `darkvolg/Trading:FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py`, blob `b7d013a802b45d2dd1cb0b91d4083fb247efac75`.
- 1h, long only, 1×, no DCA, 6% price stop, trailing 3% after +5%, 4h and 1d informative context, EMA/RSI/ADX/volume/MACD, optional market neutral FNG placeholders hardcoded (50).
- В коде `use_custom_stoploss=False` — не заявлять стоп ATR, несмотря на комментарий `ATR-based custom stoploss overrides`: активен hard -6% plus trailing. Информативные 1D EMA200 требуют не менее 200 суток предыстории. 1D контекст должен быть сдвинут, сигнал не должен видеть незакрытый день.
- Авторский исторический отчёт о +55% за 110d относится к публичному source comment `v2.12.0`, не нашему backtest. Вход многосигнальный, модель легко переобучить; **все параметры оригинала заморозить**. Указывать замены внешних FNG/OI neutral defaults. Никакой рекламы прибыльности.

## Решение по дальнейшей последовательности

- **Приоритет 1:** независимый baseline + исходный `TrendFutures` и `TrendBreakout` 1d при корректной истории (контроль того, что происходит при длинном таймфрейме, даже если отрицательные results автора повторятся). Не перенастраивать.
- **Приоритет 2:** funding basis carry, но только после проверки наличия ровных исторических spot+perp источников и воспроизводимого **двухногого** исполнения — иначе BLOCKED, а не «доходность funding».
- **Приоритет 3:** публичный `TrendRider` 1h как самостоятельный swing challenger после source audit и строгой истории 1d informative.
- Если эти источники снова отрицательные, не тратить ресурсы на hyperopt каждого; переходить к другой математической гипотезе и/или денежному портфельному базису.
- Не торговать ни один из источников на реальном счёте или на действующих PAPER scheduler без новой отдельной команды.

**Статус A210:** кандидаты найдены, исходники и технические риски указаны; **не запущен economic backtest** и **нет обещания доходности**. Это осознанное отличие preflight от результата.
