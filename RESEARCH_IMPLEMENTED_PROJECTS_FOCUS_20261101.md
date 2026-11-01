# EMBER — готовые проекты с оригинальным кодом под выбранные направления 1/2/3/4 (+6)

**Дата 2026-11-01 | Цикл CODE_SEARCH_SELECTED-01 | Режим ПОИСК/АУДИТ ИСХОДНИКОВ; без новых бэктестов и исполнения.**

**Команда пользователя:** только направления 1 (диверсифицированный тренд/CTA), 2 (TSMOM), 3 (FailureToReturn/retest), 4 (пробой/волатильность); **6 — необязательное** сжатие→пробой. Направления 5 funding mean-reversion и 7 OI-based signal **исключены из отбора**. Funding как расчёт расходов по существующим Binance USDT-M контрактам остается обязательным в будущих финансовых тестах, но **не является здесь торговым сигналом**. Не переключать основную торговую площадку с Binance USDT-M.

**Мандат:** [RESEARCH_MANDATE_LOCKED.md](RESEARCH_MANDATE_LOCKED.md); [канонический статус](RESEARCH_STATUS_CANONICAL.md). Ноль независимых `VERIFIED_FUTURES_CANDIDATE`. Пользователь разрешил новый **ПОИСК**, а не кодовое внедрение, бэктест или PAPER.

## Что означает «готовый проект» в этой выдаче

- `A`: конкретный исходный код сигнала + рабочая инфраструктура backtest/runner или полноценный класс Freqtrade, доступен для проверки; **не доказательство прибыльности**.
- `B`: код есть, но не тот venue/исполнитель, неизвестная лицензия/интеграция либо важная недостающая проверка.
- `C`: обнаружено значимое несоответствие данных, отчёта или архитектуры; только вспомогательный источник.

Проверка: открыты **фактические исходные файлы**, а не только README; сохранены Git blob SHA. Формулировка `LICENSE-файл не подтверждён` означает, что GitHub-root `LICENSE` не найден в данной проверке, **это не юридическое заключение и не разрешение копировать код**.

## 1. Перекрёстная карта по выбранным направлениям

| Направление | Доступные проекты | Первичный вывод |
|---|---|---|
| **1 — Портфельный тренд / CTA** | P01, P02, P03 | P01 — оригинальный Binance CTA research; P02 — модульный отдельный тренд+портфель; P03 — Hyperliquid, требует переноса venue и фильтров |
| **2 — TSMOM** | P04, P05, P03 | P04 — полная TSMOM research/live логика (Bybit); P05 — Binance-based long-only исследовательский сигнал; P03 — дополнительная независимая Hyperliquid конструкция |
| **3 — Failure-to-Return / ретест** | P06, P07, P08 | P06 — полноценный Freqtrade LONG-only; P07 — LONG/SHORT ретест-автомат; P08 — MA cluster/continuation, не считать независимым без сверки |
| **4 — Всплеск/пробой** | P07, P09, P10, P02, P11, P12, P14 | P07 — 2 разные breakout-реализации; P10 — momentum и inside-bar; P09 — Binance native bot; P11/P14 — обнаруженные проблемы, только резерв |
| **6 — Сжатие → пробой (резерв)** | P07, P10, P08, P13 | P07 Bollinger/Keltner, P10 BB-width+volume, P08 DoubleMA cluster, P13 FMZ BB/Keltner |

## 2. Реестр 14 проверенных проектов (сначала код, затем рассказы о прибыли)

| ID | Исходный проект | № направлений | Venue | Готовность | Исполнитель/исходник |
|---|---|---|---|---|---|
| P01 | [Octopus CTA — Binance Perpetual Trend Following](https://github.com/OctopusTakopi/crypto-trend-following) | 1;2 | Binance USDT-M — исследовательский портфель | **A** | [Открыть исходник](https://github.com/OctopusTakopi/crypto-trend-following/blob/main/engine.py) |
| P02 | [WhiteCat Binance Strategies — TrendEma/BreakoutATR](https://github.com/WhiteCatNa/binance-strategy) | 1;4 | Binance USDT-M — Python backtester | **B** | [Открыть исходник](https://github.com/WhiteCatNa/binance-strategy/blob/main/src/binance_futures_strategy/strategies.py) |
| P03 | [Gajesh TSMOM — Hyperliquid Momentum](https://github.com/Gajesh2007/momentum-trading) | 1;2 | Hyperliquid Perpetuals, НЕ Binance | **B** | [Открыть исходник](https://github.com/Gajesh2007/momentum-trading/blob/main/momentum_trading/signals/engine.py) |
| P04 | [Trading Engine TSMOM — yongzhe2160cs](https://github.com/yongzhe2160cs/trading-engine) | 2 | Bybit USDT perps, НЕ Binance | **A** | [Открыть исходник](https://github.com/yongzhe2160cs/trading-engine/blob/main/strategy/tsmom.py) |
| P05 | [Binance USD-M TSMOM (long-only) — adokav](https://github.com/adokav/signal-bot) | 2 | Binance USD-M data; research-only | **A** | [Открыть исходник](https://github.com/adokav/signal-bot/blob/main/trading/strategies/tsmom.py) |
| P06 | [FailureToReturnStrategy — FreqHub](https://github.com/hrodrig/freqhub-strategies) | 3 | Freqtrade, 1H (Binance futures требует проверенной конфигурации) | **A** | [Открыть исходник](https://github.com/hrodrig/freqhub-strategies/blob/main/strategies/FreqHub.Strategy.FailureToReturn/FailureToReturnStrategy.py) |
| P07 | [PerpLab — Pullback Retest + 3 Breakouts](https://github.com/analogdada/perplab) | 3;4;6 | Binance USDT-M perpetual research/backtest | **A** | [Открыть исходник](https://github.com/analogdada/perplab/blob/main/src/perplab/strategy/library/pullback_retest.py) |
| P08 | [Video DoubleMA Futures / Compression — MirrorNew](https://github.com/MirrorNew/2026DoubleMaFuturesStrategy) | 3;6 | Freqtrade futures 1H + 4H/1D | **B** | [Открыть исходник](https://github.com/MirrorNew/2026DoubleMaFuturesStrategy/blob/main/user_data/strategies/VideoDoubleMaFuturesStrategy.py) |
| P09 | [gmchun Binance Future Breakout Bot](https://github.com/gmchun83/binancefuturebot) | 4 | Binance USDT-M live-oriented code | **B** | [Открыть исходник](https://github.com/gmchun83/binancefuturebot/blob/main/binancefuturebot.py) |
| P10 | [crypto-trade — 8 signal strategies](https://github.com/rgg81/crypto-trade) | 4;6 | Binance Futures (Python + CSV) | **A** | [Открыть исходник](https://github.com/rgg81/crypto-trade/blob/main/src/crypto_trade/strategies/indicator/bb_squeeze.py) |
| P11 | [BTC Breakout — MiltonTulli](https://github.com/MiltonTulli/trading-bot) | 4 | Live futures orders, однако сигнальный OHLCV Spot API | **C** | [Открыть исходник](https://github.com/MiltonTulli/trading-bot/blob/main/src/breakout-engine.ts) |
| P12 | [Binance Futures Trading Bot — conor19w](https://github.com/conor19w/Binance-Futures-Trading-Bot) | 4 | Binance Futures, Windows-first | **C** | [Открыть исходник](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py) |
| P13 | [FMZ BB–Keltner Squeeze Futures](https://github.com/fmzquant/strategies) | 6 | FMZ Pine strategy, backtest Futures_Binance | **B** | [Открыть исходник](https://github.com/fmzquant/strategies/blob/main/BB-Keltner-Squeeze%E4%BA%A4%E6%98%93%E7%AD%96%E7%95%A5BB-Keltner-Squeeze-Trading-Strategy.md) |
| P14 | [MTF Breakout Bot — MAKSAT](https://github.com/MAKSAT-DEL/mtf-breakout-bot) | 4 | CSV research + live_bot.py, venue needs verification | **C** | [Открыть исходник](https://github.com/MAKSAT-DEL/mtf-breakout-bot/blob/main/main.py) |

### Детальные карточки и риск несоответствия оригиналу

#### P01 — Octopus CTA — Binance Perpetual Trend Following | A | 1;2

- **Исходник:** [OctopusTakopi/crypto-trend-following/engine.py](https://github.com/OctopusTakopi/crypto-trend-following/blob/main/engine.py), Git blob `99885dd8f3995b53dbd1a53e725e13fe99be9a29`; `READY_ORIGINAL_BACKTEST`.
- **Рыночный механизм:** Разноскоростные сигналы MA от log price; нормализация волатильности; sector/risk targeting; портфельный rebalance и turnover buffer.
- **Состояние и venue:** Binance USDT-M — исследовательский портфель.
- **Главное ограничение:** Нет полноценного биржевого исполнителя и моделирования ликвидаций; 788 контрактов в данных и ~145 одновременных позиций по авторскому отчёту — маленький счёт не повторяет этот результат; некоторые funding-пробелы считаются нулевыми.
- **Лицензия:** MIT подтверждена. **Новый ли относительно архива:** из старого реестра.

#### P02 — WhiteCat Binance Strategies — TrendEma/BreakoutATR | B | 1;4

- **Исходник:** [WhiteCatNa/binance-strategy/src/binance_futures_strategy/strategies.py](https://github.com/WhiteCatNa/binance-strategy/blob/main/src/binance_futures_strategy/strategies.py), Git blob `8353f3bfa7150de6be3a2c800603774a6f549cd3`; `READY_OHLC_ONLY_SUBSTRATEGIES`.
- **Рыночный механизм:** Отдельные TrendEmaStrategy (EMA направление), BreakoutAtrStrategy (диапазон/ATR) и VolumeMomentumStrategy (доходность+объём); отдельные классы, портфельный backtest.
- **Состояние и venue:** Binance USDT-M — Python backtester.
- **Главное ограничение:** Брать только OHLCV-классы. В собственной проверке автора 1095 дней OI содержали лишь ~20 дней настоящих данных: комбинированную OI-модель и default multicfactor НЕ использовать.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** дополнительный источник.

#### P03 — Gajesh TSMOM — Hyperliquid Momentum | B | 1;2

- **Исходник:** [Gajesh2007/momentum-trading/momentum_trading/signals/engine.py](https://github.com/Gajesh2007/momentum-trading/blob/main/momentum_trading/signals/engine.py), Git blob `7a1becea5ebca35dafc663ccf0a1360dcd293cd6`; `FULL_NON_BINANCE_RUNTIME`.
- **Рыночный механизм:** 10/30/90-дневная momentum сила → z-score → общий сигнал; risk/engine.py выравнивает волатильность и вес портфеля; order router и main существуют.
- **Состояние и venue:** Hyperliquid Perpetuals, НЕ Binance.
- **Главное ограничение:** Для Binance нужен перевод входов/ордеров/позиции. В исходной версии funding влияет на сигнал, OI может влиять на риск: если исключать эти метрики, получится отдельная модификация, не «оригинал».
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** новое дополнение.

#### P04 — Trading Engine TSMOM — yongzhe2160cs | A | 2

- **Исходник:** [yongzhe2160cs/trading-engine/strategy/tsmom.py](https://github.com/yongzhe2160cs/trading-engine/blob/main/strategy/tsmom.py), Git blob `af7d999ff114a872df6bfe65fb5376577451021b`; `FULL_SOURCE_RESEARCH_AND_LIVE`.
- **Рыночный механизм:** Знак доходности за lookback × обратно пропорциональная волатильность; дневная перебалансировка; backtest/engine.py и live/tsmom_trader.py; одновременно BTC/ETH/SOL.
- **Состояние и venue:** Bybit USDT perps, НЕ Binance.
- **Главное ограничение:** Старая проверка EMBER выявляла существенную зависимость экономики от штатного защитного breaker и restart. Нельзя просто выключать защиту или переносить Bybit результат на Binance.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** из старого реестра.

#### P05 — Binance USD-M TSMOM (long-only) — adokav | A | 2

- **Исходник:** [adokav/signal-bot/trading/strategies/tsmom.py](https://github.com/adokav/signal-bot/blob/main/trading/strategies/tsmom.py), Git blob `1448abe29f47ef343ec72f779be4abb675c7714e`; `PURE_SIGNAL_AND_RESEARCH_BACKTEST`.
- **Рыночный механизм:** Sign past daily return; vol-target sizing; long-only, плохой тренд → NO_TRADE. ExitPlan включает ATR-stop, частичные TP и time stop; исследовательский бэктестер отдельно.
- **Состояние и venue:** Binance USD-M data; research-only.
- **Главное ограничение:** Не запущенная Freqtrade стратегия и не live executor; файл прямо запрещает can_authorize_trade. Служит конкретным независимым авторским исходником для исследований, без OI как сигнала.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** новое дополнение.

#### P06 — FailureToReturnStrategy — FreqHub | A | 3

- **Исходник:** [hrodrig/freqhub-strategies/strategies/FreqHub.Strategy.FailureToReturn/FailureToReturnStrategy.py](https://github.com/hrodrig/freqhub-strategies/blob/main/strategies/FreqHub.Strategy.FailureToReturn/FailureToReturnStrategy.py), Git blob `6e80c0b96754c21744726120b6904f940621ec01`; `COMPLETE_FREQTRADE_STRATEGY`.
- **Рыночный механизм:** После пробоя swing-level цена откатывается, держит ключевую границу и подтверждает восстановление направления; EMA/ATR/volume и session guards.
- **Состояние и venue:** Freqtrade, 1H (Binance futures требует проверенной конфигурации).
- **Главное ограничение:** Фактически can_short=False — только LONG. Daily profit guard и session участвуют в исходном поведении. Плюс ~0.4% в прежних стресс-экранах и 6–24 сделки недостаточны для доказанного edge.
- **Лицензия:** GPLv3 подтверждена. **Новый ли относительно архива:** из старого реестра.

#### P07 — PerpLab — Pullback Retest + 3 Breakouts | A | 3;4;6

- **Исходник:** [analogdada/perplab/src/perplab/strategy/library/pullback_retest.py](https://github.com/analogdada/perplab/blob/main/src/perplab/strategy/library/pullback_retest.py), Git blob `4b04c1834bbf0a3e69d9e67542aea204718550c8`; `FOUR_COMPLETE_STRATEGY_CLASSES`.
- **Рыночный механизм:** PullbackRetest: breakout → зона ретеста за M баров → повторный проход, LONG/SHORT. DonchianBreakout — N-bar канал. VolatilityBreakout — прошлое close ± k×прошлый диапазон. BollingerSqueeze — BB внутри Keltner, выход из squeeze.
- **Состояние и venue:** Binance USDT-M perpetual research/backtest.
- **Главное ограничение:** Все четыре стратегии реализованы, но автор прямо пишет 'zero edges'; параметры учебные, прибыльность не доказана; backtest без live исполнителя. Лицензия AGPL-3.0-or-later, не копировать без учёта условий.
- **Лицензия:** AGPL-3.0-or-later подтверждена. **Новый ли относительно архива:** старый инфраструктурный источник, новые проверенные исходные классы.

#### P08 — Video DoubleMA Futures / Compression — MirrorNew | B | 3;6

- **Исходник:** [MirrorNew/2026DoubleMaFuturesStrategy/user_data/strategies/VideoDoubleMaFuturesStrategy.py](https://github.com/MirrorNew/2026DoubleMaFuturesStrategy/blob/main/user_data/strategies/VideoDoubleMaFuturesStrategy.py), Git blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`; `FULL_STRATEGY_WITH_COMPLEX_CALLBACKS`.
- **Рыночный механизм:** Сжатие кластера EMA 5/10/30, сильные/слабые пробои, трендовый откат/зона, структурные стопы, custom exit/stop, LONG/SHORT.
- **Состояние и venue:** Freqtrade futures 1H + 4H/1D.
- **Главное ограничение:** Уже исследовалось ранее как Double MA; не считать новым независимым семейством или проверенным прибыльным. Риски большого числа порогов/настроек, репликации исходных сигналов и overfit.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** старый кандидат.

#### P09 — gmchun Binance Future Breakout Bot | B | 4

- **Исходник:** [gmchun83/binancefuturebot/binancefuturebot.py](https://github.com/gmchun83/binancefuturebot/blob/main/binancefuturebot.py), Git blob `3dc57f074e1fb066c1cc32b9f4f0cb292411f775`; `SIGNAL_AND_FUTURES_BROKER_CODE`.
- **Рыночный механизм:** get_breakout_signal(): breakout recent range с ATR-фильтром, направление BUY/SELL; TP1/TP2/TP3 и сопровождение, стоп рассчитывается от ATR.
- **Состояние и venue:** Binance USDT-M live-oriented code.
- **Главное ограничение:** Код по умолчанию signal interval=1m, несмотря на рекомендации README для 15m/1h; нет независимо проверенных результатов, нужен аудит количества исполнений/сбоев. Не запускать live.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** из старого реестра.

#### P10 — crypto-trade — 8 signal strategies | A | 4;6

- **Исходник:** [rgg81/crypto-trade/src/crypto_trade/strategies/indicator/bb_squeeze.py](https://github.com/rgg81/crypto-trade/blob/main/src/crypto_trade/strategies/indicator/bb_squeeze.py), Git blob `7568c60cbef2157065d2d1b8944ca5a4c965f39b`; `RUNNABLE_MULTI_STRATEGY_RESEARCH`.
- **Рыночный механизм:** BB squeeze: low relative bandwidth → expanding BB + volume → LONG/SHORT; momentum: N подряд направленных свечей; inside-bar breakout: пробой материнской свечи. Есть единый backtest CLI.
- **Состояние и venue:** Binance Futures (Python + CSV).
- **Главное ограничение:** Это в основном краткосрочное продолжение, НЕ академический TSMOM и НЕ доказанный стабильный edge. Сверять backtest/live parity и каждое закрытие; большие отчёты по многим версиям не являются независимым OOS.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** новое дополнение.

#### P11 — BTC Breakout — MiltonTulli | C | 4

- **Исходник:** [MiltonTulli/trading-bot/src/breakout-engine.ts](https://github.com/MiltonTulli/trading-bot/blob/main/src/breakout-engine.ts), Git blob `dd67586ca51942753db9c08f5a3fba6c2d032f1b`; `EXECUTOR_SOURCE_BUT_MARKET_MISMATCH`.
- **Рыночный механизм:** 10-барный BTC Donchian breakout + объём >2x → вход; SL3%, TP6%, 5x, порог частоты; TS Bun и файловый журнал.
- **Состояние и venue:** Live futures orders, однако сигнальный OHLCV Spot API.
- **Главное ограничение:** Сигнал fetchCandles() запрашивает api.binance.com/api/v3/klines (SPOT), а отправка ордеров идёт на fapi.binance.com (FUTURES). Отдельный src/backtest.ts имеет параметр fees=0.001, но в runTrades PnL не обнаружено списания этих комиссий. Заявленные проценты считать НЕПОДТВЕРЖДЁННЫМИ.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** новое дополнение, низкий приоритет.

#### P12 — Binance Futures Trading Bot — conor19w | C | 4

- **Исходник:** [conor19w/Binance-Futures-Trading-Bot/TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py), Git blob `b5bdc3e6f6d11ac33caea9268901660088b806fc`; `LEGACY_STRATEGY_FUNCTIONS_WITH_BROKER`.
- **Рыночный механизм:** В TradingStrats.py множество отдельных функций, включая breakout, ATR, EMA, wick, custom TP/SL; есть back_testing и live_trading.
- **Состояние и venue:** Binance Futures, Windows-first.
- **Главное ограничение:** Устаревшие подходы/Windows-only; README указывает на неработающий check_close_pos. Для research не приоритет до аудита закрытий и совместимости API.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** новое дополнение, низкий приоритет.

#### P13 — FMZ BB–Keltner Squeeze Futures | B | 6

- **Исходник:** [fmzquant/strategies/BB-Keltner-Squeeze交易策略BB-Keltner-Squeeze-Trading-Strategy.md](https://github.com/fmzquant/strategies/blob/main/BB-Keltner-Squeeze%E4%BA%A4%E6%98%93%E7%AD%96%E7%95%A5BB-Keltner-Squeeze-Trading-Strategy.md), Git blob `e5d4f901a5d607e8ae6e0b81e2c5324ce6913536`; `COMPLETE_EMBEDDED_PINE_STRATEGY`.
- **Рыночный механизм:** BB/Keltner геометрия сжатия → пробой полосы в сторону фильтра → LONG/SHORT, закрытие при изменении направления.
- **Состояние и venue:** FMZ Pine strategy, backtest Futures_Binance.
- **Главное ограничение:** Это embedded Pine, не Python-класс; другой backtest-провайдер, точный режим исполнения/комиссий и лицензия не сверены. Наличие Futures_Binance в заголовке не гарантирует прибыль.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** дополнительный открытый исходник.

#### P14 — MTF Breakout Bot — MAKSAT | C | 4

- **Исходник:** [MAKSAT-DEL/mtf-breakout-bot/main.py](https://github.com/MAKSAT-DEL/mtf-breakout-bot/blob/main/main.py), Git blob `0459984dc5a5a577117c930ac35a867ae36c3bea`; `HTF_TIME_ACCESS_WARNING`.
- **Рыночный механизм:** 1H входы с EMA 4H/1D, ATR стоп, ADX/volume фильтр, next-open backtest.
- **Состояние и venue:** CSV research + live_bot.py, venue needs verification.
- **Главное ограничение:** В add_indicators() 4H/1D resample вычисляет текущие HTF EMA и ffill на 1H без задержки на закрытие HTF; вероятен lookahead внутри HTF периода. Не использовать авторский плюс до причинной сверки.
- **Лицензия:** LICENSE-файл не подтверждён. **Новый ли относительно архива:** новое дополнение, низкий приоритет.

## 3. Дополнительные исходные файлы внутри уже найденных проектов

- `P07` PerpLab: [volatility_breakout.py](https://github.com/analogdada/perplab/blob/main/src/perplab/strategy/library/volatility_breakout.py) — Git blob `4abbea4fd602dba1814a04e29671bde55939a3cb`; **не** читать это как Donchian+ATR: в коде триггер по previous_close ± k × previous_range.
- `P07` PerpLab: [donchian_breakout.py](https://github.com/analogdada/perplab/blob/main/src/perplab/strategy/library/donchian_breakout.py) — Git blob `402bceb628cd46c7ab0bf239ab606f5a49cb336b`.
- `P07` PerpLab: [bollinger_squeeze.py](https://github.com/analogdada/perplab/blob/main/src/perplab/strategy/library/bollinger_squeeze.py) — Git blob `05105bc9877fddd0ae0ece7408131af403ecd6ab`.
- `P04` yongzhe: [live/tsmom_trader.py](https://github.com/yongzhe2160cs/trading-engine/blob/main/live/tsmom_trader.py) — Git blob `c64d0600b9853e99d0b82919cd193941494c6384`; [backtest/engine.py](https://github.com/yongzhe2160cs/trading-engine/blob/main/backtest/engine.py) — Git blob `4575bb98efdc5e7d7f158a41f21cba02a73fd0c0`. ВНИМАНИЕ: `core/strategy.py` — legacy VATFMR, **не** валидированная TSMOM.
- `P03` Gajesh: [risk/engine.py](https://github.com/Gajesh2007/momentum-trading/blob/main/momentum_trading/risk/engine.py) — Git blob `087c6eb05bdb311da9cdd2a6502f0b130de40866`; [main.py](https://github.com/Gajesh2007/momentum-trading/blob/main/momentum_trading/main.py) — `14447ac0b7da5a3f50904e2393ecdbbff20125d5`.
- `P10` rgg81: [momentum.py](https://github.com/rgg81/crypto-trade/blob/main/src/crypto_trade/strategies/price_action/momentum.py) — `33a54384daa6e592db702995237941b37855e71f`; [inside_bar.py](https://github.com/rgg81/crypto-trade/blob/main/src/crypto_trade/strategies/price_action/inside_bar.py) — `3aeb73bc79cd4435ee2407dafe667e1a13c9ce7e`. Это **свечной краткосрочный momentum**, не TSMOM.
- `P11` Milton: [src/backtest.ts](https://github.com/MiltonTulli/trading-bot/blob/main/src/backtest.ts) — `7bf8550e35f5c6104d0d41a0dfd030384d4ee859`; локальный `fees=0.001` в params не учтён в `runTrades` при `balance += pnl` — это исходно разные модели и не подтверждение net-результата.
- `P02` WhiteCat: [результаты аудита факторов](https://github.com/WhiteCatNa/binance-strategy/blob/main/docs/candidate_factor_test_results.md) — `04b52e64591125047ba00c345b97f9a046fb6f6f`, выявленная самим автором плохая OI history; не переносить в основной отбор.

## 4. Что НЕ засчитывается готовым оригиналом под Binance USDT-M

| Источник | Причина исключения из shortlist |
|---|---|
| [jicheolha/crypto-trading-bot](https://github.com/jicheolha/crypto-trading-bot) | Squeeze для Coinbase derivatives; автор сообщает, что `diagnostics.py`, `download_data.py`, `run_backtest.py`, `run_live_multi_asset.py` скрыты. Красивый Sharpe не заменить отсутствующие исходники. |
| [Shafqat388/quant-trading-bot](https://github.com/Shafqat388/quant-trading-bot) | Наличие breakout/squeeze в коде подтверждено, но стратегии **long-only SPOT**, не futures short. Spot не подменяет пользовательский рынок. |
| [engineerinvestor/systematic-trend-following-with-managed-futures](https://github.com/engineerinvestor/systematic-trend-following-with-managed-futures) | Есть настоящий TSMOM код и crypto research, но `configs/crypto/tsmom_1_3_12.yaml` по умолчанию `prefer: synthetic`, а `CRYPTO_SPEC.md` исключает perpetual funding/liquidation execution. Полезная **методика**, не готовый Binance USD-M оригинал. |
| [zionhann/open-binancian-futures](https://github.com/zionhann/open-binancian-futures) | Реальный Binance USD-M framework/backtesting, но это **движок**, не раскрытая конкретная прибыльная стратегия; не считать ещё одной независимой моделью. |
| [BYTEX-TRADE/bytex](https://github.com/BYTEX-TRADE/bytex) | `examples/reference/breakout-retest.json` существует, но использует синтетические 3000 баров (seed=7): учебный example, не рыночный futures edge. |
| [adensvaz/Sentinal_Hyperliquid](https://github.com/adensvaz/Sentinal_Hyperliquid) | Поиск нашёл упоминание, но GitHub content API не вернул дерево кода: неподтверждённый доступ, НЕ включать как проверенный. |

## 5. Короткий рабочий shortlist по нашей задаче (не команда на следующий этап)

| Направление | Лучшие исходники по полноте | Почему |
|---|---|---|
| **1. CTA** | P01 Octopus; P02 TrendEma-only | Binance фьючерсный портфельный оригинал и отдельный лёгкий OHLC-only контроль |
| **2. TSMOM** | P04 yongzhe; P05 adokav | Полный Bybit research/live + независимый Binance long-only research, оба TSMOM, а не EMA-cross |
| **3. Failure-to-return** | P06 FreqHub; P07 PerpLab PullbackRetest | Два независимых полностью описанных кода с разной логикой подтверждения |
| **4. Breakout** | P07 PerpLab Donchian/Vol; P10 rgg81; P09 gmchun | Binance-native исследовательский код и отдельный Binance bot; три разных варианта по таймфрейму/триггеру |
| **6. Опционально squeeze** | P07 PerpLab; P10 rgg81; P13 FMZ | BB/Keltner, BB bandwidth+volume, Pine фьючерсный пример; не путать squeeze со статистическим доказательством дохода |

## 6. Дисциплина данных и авторских результатов

- `PROJECT_SOURCE_AVAILABLE` ≠ `ORIGINAL_PARITY` ≠ `NET_PROFIT_VERIFIED`. **Ни один** из P01–P14 не получает статус VERIFIED на этапе поиска.
- Авторские Sharpe/ROI (Octopus, Milton, старые FTR/DoubleMA) не переносить в результаты нового независимого теста. Если backtest сбой или missing source — `BLOCKED`, не экономический FAIL.
- Не копировать код из проектов без подтверждённых лицензий. Даже MIT/GPL/AGPL требуют соблюдения условий.
- Стоимость направления 1 может быть неприемлема при небольшом счёте: диверсификация по 145 контрактам и min-notional требуют отдельного расчёта, но этот экран **не пересчитывает и не адаптирует** портфель.
- История GitHub, PAPER, стратегия на счёте, файлы risk engine, канонический реестр R001–R076, открытые задачи и расписания **НЕ изменены**. Этот документ — только каталог найденных реализаций.
