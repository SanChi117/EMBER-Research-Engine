# A193 — поиск адекватной стратегии для ускоренного роста малого депозита (31.10.2026)

**Цель пользователя:** найти **готовую, работоспособную, проверяемую** стратегию для сравнительно частых коротких направленных движений криптовалюты с ограничением потери депозита. В качестве исходной гипотезы рассматриваются лонг/шорт 5m–15m, цена 1–3% движения, 3–5 setups/day across 5+ highly liquid pairs, автоматический PAPER. Вышеуказанные величины — исследовательские пожелания, **не доказанное свойство доступных систем**. Открытие реальных позиций запрещено. Рост малого депозита кратно за 40–60 дней нельзя обосновывать одним удачным backtest.

## A193 — первая точная проверка претендента «для маленького депозита»

**Источник:** https://github.com/jiangkaili/binance-trader-bot
- Author strategy: RSI(7) Wilder, 5m, ADX(14) <25, RSI20/80 triggers, SL 1.5% from price, TP 3.0% price, cooldown 12 bars, 5x, 16 USDT *изолированный модельный торговый капитал*, both long and short; Git original pinned commit `39f7187ce21b021441fb4a55188b95831df7b5b1`.
- Оригинальный код `scripts/sweep_timeframe.py` git blob `d4e5ed465c0c520a0f1496c984f020259904969c`; точный источник RSI/ADX `gridtrader/quant/indicators.py` git blob `28c6a8cd437384565ffc8b9586f27b535207a1cf`.
- Автор декларирует `v8` исторический +12.88 USDT на BTC за 3 календарных окна, средний PF1.18, 42% WR, 5x. **Независимость этих трёх окон нарушена пересечением интервалов**: Mar29–May18, Apr18–Jun17, May28–Jun27 2026. На них перебирались варианты, поэтому цифры нельзя считать полноценным независимым walk-forward.
- **Наша проверка:** реальный непрерывный Binance Vision Binance USD-M ETHUSDT 5m, [2026-08-01,2026-10-01) UTC, **17568** свечей; другое направление/актив относительно BTC, но код frozen 31.10.2026 => **не заведомо постпубликационный автором untouched OOS**; это внешняя cross-pair историческая проверка. Прогон через оригинальную функцию автора **без изменения торговых правил** и инструментированную копию, различающуюся ровно одним возвращённым полем `ending_cash`; все авторские показатели `pnl,n,wr,pf,max_dd` совпадают 1:1 для обеих комиссий.
- **Наш исходный успешный GitHub Actions CI:** [run 41144777094](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41144777094) source receipts [artifact 13019448889](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41144777094/artifacts/13019448889), sha256 `78bb56e79b8159cb33b68f870e2bbd7e51806817d0f3e1a98d4dbd5968dd44a0`; повторный [run 41144927577](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41144927577) **SUCCESS** с проверкой точного Git blob RSI/ADX, [новый архив #13020399145](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41144927577/artifacts/13020399145), sha256 `468b5798021e7ae72f962203710878788bbd8ebc8a12095fdd592994ecddde79`. Вся арифметика совпала с первым прогоном.
- **Важная бухгалтерская находка:** автор `simulate()` вычитает комиссию входа непосредственно из `cash`, но `returned['pnl']=sum(trade['pnl'])` включает **только комиссии закрытия**, тем самым его `pnl` **завышает** баланс относительно фактического `cash - margin`. В отчёте основным считаем счёт по наличным `ending_cash - 16`. Исходные сделки и рынок не изменялись, только извлекаемый баланс.

| Тест оригинальной системы (ETH 5m) | Комиссия 6 bps за сторону | Комиссия 12.5 bps за сторону |
|---|---:|---:|
| Закрытых сделок | 43 | 43 |
| Win rate | 27.907% | 27.907% |
| Авторский PF (выходные net rows) | 0.53967 | 0.48553 |
| Авторский суммарный PnL (без учёта entry fees) | −9.543757 USDT | −10.016553 USDT |
| **Реальный cash accounting PnL** | **−10.578430 USDT** | **−11.939526 USDT** |
| **Остаток из тестовых 16 USDT** | **5.421570** | **4.060474** |
| Упущенные авторским return entry fees | 1.034673 USDT | 1.922973 USDT |
| Max DD авторской модели | −72.77% | −77.37% |

**Уточнение:** −66.1%/−74.6% потери относятся к **изолированному тестовому капиталу 16 USDT**, которым авторская функция многократно оперирует с плечом 5x, а не к целому депозиту 100 USDT, если оставшиеся 84 USDT остаются нетронутыми. Модель не ограничивает общий портфель и не моделирует ликвидации/рыночный стакан.

**Вердикт:** `REJECT_FAST_RSI_5M`, `NO_LIVE`, `ECONOMIC_FAIL_ON_ETH_CROSSPAIR`. Данных недостаточно, чтобы объявлять стратегию неизменно убыточной на BTC или всех активах, но нет основания рекомендовать её для агрессивного малого счёта. Усложнения типа funding-заграждения у v9 автором ещё не проверены.

## Другие найденные источники, сравнительный отсев
| Источник | Код | Факты / ситуация | Статус |
|---|---|---|---|
| `kboranyldz/sol-trading-research` | Есть полный SOL Pullback V9 `src/sol_pullback_core_v9.py` (~2600 строк) | 1h вход, SOL+BTC 4h режим, 4/5 подтверждений, SL 1.75ATR, TP1=1.5R(40%), TP2=2.5R, long+short. Автор сообщает положительные development 2023-25, 2022 около BE, 2026 выше 0 при небольшом N. *Default target stop risk 6% account* и 1–3x — чрезмерен. Исследовательские скрипты частично зависят от неопубликованных backtest components, нет свежей independent parity. | **PRIORITY_1_FOR_REDUCED-RISK-REPLAY** (1% account risk cap, НЕ якобы проверенная доходность). Низкая частота, не гарантирует 3–5 сетапов/день |
| `nateemma/strategies` | Исходники NN/ML и много результатов | 15m/1h mean reversion gbb автору удавалось получать плюс OOS; около 70% сделок/почти весь PnL на ZEC с ликвидностью хуже BTC/ETH/SOL. У другого 15m/hourly momentum basket +114% в 2024–26, но 52–64% drawdown, 69% итогового эффекта ZEC. | **REJECT_SMALL-CAPITAL-LIQUIDITY/TARGET** |
| `Gotodataru/binance-futures-backtest` | Реальный Python код и отдельный Binance USD-M walk-forward OOS CSV | 5m taker momentum отрицательный net на SUI/SOL/ETH/BTC (PF соответственно 0.8285/0.75/0.5159/<1), в OI+price 15m ETH +7.4% но PF1.023 и высокий DD; SUI доходный с DD около 97.5%. | **REJECT_FOR_SMALL_DEPOSIT** |
| `Superior-Trade/superior-skills` | Шаблоны/API под Hyperliquid, неполноценная копия авторского исполняемого движка | Автор 4h Bollinger Reverter 84 trades +8.77% /162d, max DD18.5%; 6-trade Donchian +6.69% /162d. Результаты есть на одной истории; речь про чужую платформу и не про Binance 5m. | **REFERENCE_REGIME_MODULE_ONLY** |
| `jiangkaili/binance-trader-bot` | Полный авторский RSI 5m | Статическая проверка неточности entry-fee и наш 43-trade offpair сильный минус, авторские три BTC окна перекрываются. | **FAIL** |
| `PatrickSebastine/ema-momentum-bot` | Python bot, 5m/15m | Декларирует максимум 20% «риска» на сделку и 30% дневного DD, авторские 55–65% WR без независимых trade receipts/надежного OOS. | **REJECT_RISK_PROFILES** |
| `grinay/geektrade-strategies` | TradingView setup описание | ETH Momentum 2h PF3.08 авторский, 12 сделок/год, не быстрый компаундинг, полного Python-native эквивалента тут нет. 5m DumpReversal нет аудируемых trade receipts. | **REFERENCE_ONLY** |
| `francisx1999/crypto-trading-bot-postmortem` | Отрицательная бухгалтерия 7 стратегий/24mo | Среди тестов стратегия с ~93% WR потеряла ~95% equity из-за широкой сетки/открытых убытков. | **METHODOLOGY WARNING** |
| `knacker65/v5-crypto-scalper` | Открытая торговая среда, опубликованы 30+ тестов | На liquid majors 5m/1h gross-edge почти ≈ комиссии и проскальзывание, стратегия после costs отрицательная. | **RESEARCH_MATERIAL_ONLY** |

## Вывод для пользователя
**На момент A193 мы НЕ нашли ни одной готовой high-frequency long/short стратегии на ликвидных фьючерсах с полноценным независимым положительным OOS и допустимой просадкой, которая обоснованно поддерживала бы x5–x20 малого депозита за 40–60 дней.**

Лучший **механический источник для следующей независимой проверки**, а не обещание результата: `SOL Pullback V9` с неизменными правилами входа и выхода, но лимитом риска **не более 1% полного счета** (вместо исходных 6%) при масштабировании 1–3x, 1h+4h. Если нужна более высокая частота, отдельная новая 15m гипотеза (trend-continuation pullback/impulse) должна пройти **отдельный новый preregistered тест** без механического переноса 1h параметров на 15m.

### План проверок
1. A194: frozen complete `SOL Pullback V9` original code audit + verify code/backtest dependency availability. Reconstruct independent engine if original historical runner missing, label as independent implementation. Use Binance Vision SOL/BTC 1h+4h and 1m detail, fixed 2024–Oct2026 periods, 10/25bps roundtrip + slippage+funding, error test zero lookahead. Compare size/risk 1% to original 6%, no retuning.
2. A195: after identifying robust 1h setup, *separate* 15m continuation engine on fixed 5–8 highly liquid pairs with 4h-only context and 5m entry; no tuning of setups on OOS. Require at least 200 truly independent trades, PF ≥1.3 after full costs and a high-fee stress, effective DD within bounded threshold, 1m fills, no one-coin/outlier dependence. Candidate without evidence remains `RESEARCH_ONLY`, not PAPER order generator.
3. Release criteria: production scripts source-pin, original-vs-independent trade parity, CPCV/embargo and frozen test window, randomized fee/cost pressure, honest journal. Loss of 1% full account on SL includes fees and slippage; leverage is sizing instrument **not edge**. No forcing 3–5 trades/day and no suggestion 20–30x merely to mimic telegram trader.

## Sources
- https://github.com/jiangkaili/binance-trader-bot
- https://github.com/kboranyldz/sol-trading-research
- https://github.com/Gotodataru/binance-futures-backtest
- https://github.com/nateemma/strategies/blob/master/us_spot_market_study.md
- https://github.com/Superior-Trade/superior-skills
- https://github.com/francisx1999/crypto-trading-bot-postmortem
- https://github.com/knacker65/v5-crypto-scalper

No real trades executed; SMOKE and old PAPER automations unchanged.
