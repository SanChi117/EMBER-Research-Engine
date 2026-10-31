# A199 — независимый отбор реально исполнимых коротких FUTURES стратегий (протокол до результата)

31.10.2026. Исходный механизм EMBER и провалившиеся A195–A198 не реанимировать. Бумажное исследование **без каких-либо торговых или виртуальных ордеров**.

Источник: официальный публичный `freqtrade/freqtrade-strategies` (реестр **примеров**, не прибыльных готовых систем), pinned commit `f3340ce11f5bdf62f598522e64d1f5638eaa13f5` 08.09.2026. Frozen exact git blobs:
- `user_data/strategies/futures/FReinforcedStrategy.py` blob `11bfdde9fcecf772a2d223c88b9ee62bfd8737d3`. Оригинал 5m, **LONG и SHORT**, EMA-cross 8/21, фильтр тренда 1h resampled SMA50, ADX exit, 5% стоп, исходная ROI time-map (5/10/7.5%). No alteration.
- `user_data/strategies/futures/FAdxSmaStrategy.py` blob `3bb13caf079e8360a959c3ad4dd2b2507f3045c0`. Оригинал 1h, **LONG и SHORT**, ADX>30 + crossover SMA12/48, ADX exit, 5% стоп, исходная ROI time-map. No alteration.
- `FSampleStrategy` 1h example reserved as negative-control only if first two results warrant; it is not preselected as profitable.

## Готовая гипотеза и одна тестовая матрица

- **Actual native Freqtrade==2026.4**, unmodified source code classes, same actual static offline Binance USD-M futures **exchange market metadata** + genuine Binance Vision OHLCV, mark-price candles, hourly actual settled funding. Native engine's own limited OHLC based fills. Do NOT label as real orderbook proof. This is NOT a synthetic imitation of source strategy entries or exits.
- 4 original liquid pairs, no exclusion after inspecting results: **BTCUSDT, ETHUSDT, SOLUSDT, LINKUSDT**.
- History warmup of 1h from 2026-03-15 (A195) and genuine 5m from May01 (A196); fixed evaluation **[2026-05-13,2026-10-01) UTC** 141 days. Futures Binance genuine mark 1h and funding settlements (A195). For 5m strategy use real original 5m data May–Sep. For 1h FAdxSma enable `--timeframe-detail 5m` with identical original sources. Data and source ZIP SHA from previous source-quality verified scripts (A195,A196).
- Simulated **separate $1000 wallet per pair**, **fixed $100 isolated stake**, original strategies **default native 1x leverage** (no user 20–30x), **at most one position per pair**. Do not present sum of wallet returns as one combined live multi-pair portfolio. A fixed $100 notional and -5% native stop yield intended roughly **$5 + fees per position** (0.5% wallet), but actual gaps can exceed this.
- Fees per fill: 0.05% per side in BASE, 0.125% per side STRESS; no extra slippage added; **native approximate limit order fills**, NO orderbook queue, bid/ask, latency or realized exchange fills. Stress commission increase does not fully cover slippage.
- Original source parameters, no retuning, no disabling shorts, no forcing RR or setting targets from EMBER.
- **Predeclared gate for *initial* candidate only**: at least **2 of 4 pairs** with **N>=35**, **positive net**, **PF>=1.20**, **wallet DD <15%** at **both fee scenarios**; combined trades of the four pair-account isolated scenarios **>=141** over 141 days (~1/day across four; still short of user goal 3–5/day); top 3 winning trades share **<60% of all gross positive trade PnL** for each qualifying pair; portfolio-level risk and correlations NOT tested. Results from Binance 2026 historical May-Sep used repeatedly in past and are therefore a **screening** window not pristine untouched OOS.
- If baseline results reject, do not optimize on same period. If any pass, require a new untouched time window (Oct 2026 genuine daily data or future forward) + native 5m detail, Freqtrade official lookahead and recursive audit, explicit fees/slippage+mark/liquidation before *PAPER monitoring* (not auto orders).
- Important real-user requirement: do not conflate high trade *frequency* with expectancy. No 20x/30x and no implausible rapid capital multiplication promises.
- Source date is newer than data tested; author had 2026 data available, so test may be in-sample of original published example. No live, no SMOKE, no scheduler changes.

Results and audit ledger A199 to be appended **only after actual CI receipt outputs and independent verification**. No placeholders counted as completed.
