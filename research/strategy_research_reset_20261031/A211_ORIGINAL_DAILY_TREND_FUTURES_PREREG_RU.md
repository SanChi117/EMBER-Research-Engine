# A211 — ПРЕРЕГИСТРАЦИЯ до PnL: оригинальный дневной Donchian TrendFutures 1×

Дата: 2026-10-31. Первое исследование по A209 EDGE-FIRST. PAPER/RESEARCH ONLY. **Не подключать к существующим SMOKE/PAPER-планировщикам и не выставлять ордера.**

## Чётко определённый объект теста

Оригинальный `Kureshi25/cryptobot@c8ffbaabee9f63630e179c698c53df4916b93f8e`, `user_data/strategies/TrendFutures.py`, git-blob `2e6b83ba128373655090ca4827d8c7954ffaedfd`. Класс `TrendFutures`, default `entry_lookback=20`, `exit_lookback=10`, `atr_stop_mult=3.0`, `lev=1` без гипероптимизации. 1d native Freqtrade2026.4, can_short=True, 20d Donchian/200d EMA, 10d exit and author's custom 3ATR stop. Original hard fallback -35% цены и `stoploss_on_exchange=False` требуют дополнительного risk gate. `entry/exit=market`, no DCA, signal available after complete daily candle.

**Никакие параметры источника не меняются, никакая адаптация после PnL не может носить название оригинального теста.**

## Исторический план заранее

- Четыре пары BTC,ETH,SOL,LINK USD-M Binance perpetual.
- Ежедневная price history **2023-01-01–2026-09-30** (достаточно 365 начальных свечей для EMA200, test starts 2024-01-01). Два полных календарных года 2024, 2025 и 2026 до 30 сентября (2026 неполный календарный год). 3 отдельных независимых по времени validation windows: `20240101-20250101`, `20250101-20260101`, `20260101-20261001`, с непрерывной предысторией через общий folder. **Внимание: данные 2024–2026 уже затронуты EMBER-A197..A208, не pristine future OOS.**
- Источники по каждому символу/месяцу: Binance Vision monthly USD-M `klines/1d`, `markPriceKlines/1h`, `fundingRate`. Каждый ZIP и CSV SHA256, ровно 1d open timestamps; каждую пропущенную 1h mark свечу дополнять только по отдельному genuine Binance daily `markPriceKlines/1h`, с индивидуальным SHA и строгой проверкой совпадающих свечей. **Никаких синтетических цен, no backfill from futures OHLC**, ZERO for periods between genuine funding settlements.
- Все источники для 2023–2026 must exist; otherwise BLOCKED. Exact date interval and 2026 October 1 exclusive.
- Trading engine `freqtrade==2026.4` actual native, no exchange keys/network orders, Freqtrade offline static metadata as A199; `dry_run_wallet=1000 USDT`, nominal `stake_amount=100 USDT`, separate isolated 1× account **per pair × period**, max 1 simultaneous position per pair. *This is not one integrated portfolio*. If wishing to compare an equally weighted 4-account portfolio, explicitly model 4×$1000 separately, never add summed percentages without capital denominator.
- Costs two cases `--fee 0.0005` and `--fee 0.00125` per fill, no invented maker benefit; **no additional intrabar slippage** simulated, therefore this is research not an executable order book forecast. Original market orders may suffer additional slippage. Funding taken from actual USD-M settlement source in Freqtrade native.
- 4 coins × 3 periods × 2 costs = **24 native original ZIP trade receipts**. Validate source SHA, date boundaries, 1×, total profit by sum trade PnL, PF, DD, win rate, max loss, hold, directional mix; zero trades allowed and must be preserved honestly; mark-to-market drawdown must not be confused with realized-trade DD.
- Baselines: cash USDT 0%; 1× buy-and-hold futures *price* return for each coin/test period (no funding/fees, clearly distinguished from executable spot); same gross USDT allocation and spot buyhold separately only if genuine spot quote price is added later. Report market-relative return explicitly, not 'beats hold' from different capital.
- No mandatory number of trades, no mandatory timeframe, no obligatory short signals each year. Slow profitable strategy can be investigated, but 2 trades on one year → INSUFFICIENT_EVIDENCE, not instant PASS.
- **Research decision** from verified 24 ZIP: multi-year net results + fee sensitivity + drawdown + market-relative performance + cash; a single good year is insufficient. Suggested PROVISIONAL only if overall diversified (4 equal subaccounts) net positive under BOTH cost models, PF>=1.2 on aggregate (when enough losing samples), absence of liquidation, worst individual year/account deterioration not catastrophic, and >0 net result in at least 2 of 3 periods (gross equal-account portfolio). If test rejects, report RESEARCH_NEGATIVE / INSUFFICIENT_EVIDENCE; no tuning on same market windows.
- **Separate forward PAPER validation mandatory** before any trade-signal usage. A successful CI run is ONLY code/data success, not economic PASS.

## Предварительные отрицательные риски

У автора в README уже указан отрицательный full-sample `TrendFutures` (-66.5% при 156 сделках), с частично позитивным walk-forward. Избранный инструмент не рекламируется как вероятно прибыльный; его проверяем как **честный длинный трендовый baseline** и заменяем ложную оптимизацию настоящей воспроизводимой проверкой. Если подтверждается убыточность — не перебирать сроки Donchian на той же истории.

## Второе независимое направление

Исторический spot-perp delta-neutral funding carry исследуется **отдельно** и требует двух реальных ног, spot/perp prices, total four-leg roundtrip fees, basis returns and margin. Не считать чистое funding положительной стратегией. Продвигать независимо от того, положителен или отрицателен A211.
