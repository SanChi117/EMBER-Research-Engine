# A204 — RESET отбора после A197–A203: что работает, что проверено и требования к новой готовой стратегии

Дата 2026-10-31. Этот документ — **архитектурная контрольная точка, не бэктест A204 и не новый торговый сигнал**. Все приведённые результаты относятся к независимо записанным GitHub Actions/реальным журналам предыдущих этапов, а не к планам/догадкам.

## Экономический реестр

| Кандидат / цикл | Конечный результат | Сохранить как |
|---|---|---|
| A197 DoubleMA | unstable/OOS failures | отрицательный контроль; causal/market execution tooling |
| A198 SOL Trend Pullback V9 | 12 trades, PF0.60–0.71, loss | не возвращать без новой причины |
| A199 FAdxSma/FReinforced | independent original native futures tests loss/insufficient | baseline Freqtrade2026.4 + crypto futures data |
| A200 bigbear/bigbull original genia | 4 genuine Binance pairs, 5m stop-first, **0/4 BOTH**, baseline stochastic tie lottery | original signal import+5m causal executor+SHA trade receipts |
| A201 original momentum_wick and momentum_rsi | 16 native ZIP, original SL10%/TP2%, **0/4 BOTH**, holds days/weeks | prefix causality test, fee+time gates, SHA verifier |
| A202 original dip_catcher May–Sep2026 | economic PASS3/4, but **98.6% four slots occupied**, 466/466 reentries ≤5m; stop8%; speed/risk FAIL | credible positive market regime observation only; NOT usable short-stop scalping |
| A203 SAME dip_catcher May–Sep2025 independent holdout | **economic FAIL 0/4**, 98.24% four slots, 667/667 <=5m reentry, avg >4 closed/day despite loss | genuine independent yearly falsification, immutable source QA |

A203 report: `A203_INDEPENDENT_2025_ORIGINAL_DIPCATCHER_FAIL_RESULTS_RU.md`. A202 report: `A202_NATIVE_DIPCATCHER_REAL_BINANCE_VERIFIED_RESULTS_RU.md`. Из A202–203 не выбирать только красивые монеты/периоды, сохраняя исходные параметры.

## Доказанные технические возможности, которые НЕ нужно создавать с нуля

1. Pin оригинального Git commit + Git blob SHA и настоящего Freqtrade2026.4 (A199–203).
2. Continuity/audit настоящих Binance USD-M klines5m and 1h mark/funding 2025 and2026, без фальсификации candles и с source ZIP sha256 (A195/A196/A203).
3. Two fee stress levels, per-trade original ZIP SHA and independently reopened `profit_abs` integrity (A199–203).
4. Параллельные отдельные 4-парные wallets without fictional combined PnL.
5. Independent adverse excursion MAE per trade, actual hold duration distribution, utilization occupancy, immediate reentry after previous exit (A202/203).
6. Causal prefix compare against future-appended candles on **original unchanged** signals (A201).
7. Freeze candidate pre-reg BEFORE PnL, fail-closed validation. SUCCESS of Actions means test executed, not economic PASS.

## Новые обязательные требования ДО покупки вычислений

- **Source:** полностью открытый, pinned, рабочий на BTC/ETH/SOL/LINK 5m/15m (BTC research control), native Freqtrade/backtester, no hidden black-box trained model. No `np.gradient` centered on full future frame; no negative shift; when 4h filter is used, only fully closed 4h values may reach child timeframe.
- **Causal entry as an event:** short-lived trigger at a *new* confirmed breakout/retest/sweep/zone reaction, not persistent `signal==True` for a whole market regime. Pretest percentage time in market and per-coin median reentry gap; if 100% of entries occur immediately after previous ROI exit, **reject for discretionary/event-driven A+ setups**.
- **Exit geometry and risk:** actual SHORT and LONG activation; SL behind genuine causal structure with meaningful risk distance, no fake fixed RR that overrides 4h exit zones in EMBER structural core. Reject original SL8–10% prices with TP1–2% if meant for 20–30x. Mandatory liquidation-buffer check BEFORE promoting candidate, own dollar position sizing and worst-case gap. No DCA/averaging down.
- **Honest tempo:** candidate should be able to close 3–5 potentially independent opportunities/day across 4–5 coins **without keeping 4/4 slots busy all day and without p90 holding several days**. Distinguish signal event count, realized closed trades, latent open risk and correlated margin.
- **Profit after expenses:** two fees and one independent adverse slippage scenario; account funding, commission and possible maker nonfill; don't assume live costs match historic tiers.
- **Out-of-sample:** May–Sep2025/2026 have now been mined for decision-making, so they are *no longer pristine future out-of-sample* for any strategy built from lessons. Additional genuinely new market period (2026 October daily Binance Vision available for part of month) and/or forward PAPER must be frozen BEFORE test. If candidate selected solely from Freqle 6k ranked strategies 2022–2024, acknowledge multiple-comparison selection and require fresh holdout.
- **Economic acceptance** at least2/4 symbols base+stress net>0 PF>=1.2 and adequate N, control worst loss, drawdown and top3 concentration. **Execution acceptance is separate**: risk stop/TP, position sizing, 24h p90, low saturation, spot/futures parity, real spread, forward PAPER. An economics PASS alone is never a signal to enable any orders.

## Развилка следующего разумного цикла

**A204 не должен снова выбирать готовый алгоритм только по таблице высокой доходности:** сначала source/risk/causality/continuous exposure screening, потом pin + independent native backtest on paired frozen periods. Происхождение сигналов из готовых исходников допускается; EMA/Bollinger/VWAP/ADX/ATR — инструменты, а не доказательство edge.

Для небольшого депозита наша цель — 1–2% полезного движения цены с **явно ограниченным номинальным риском и заранее проверенными стопами**, а не 20–30× как способ скрыть отсутствие математического ожидания. Если 4h структурный стоп находится за границей ликвидации при заданном плече, такой сетап НЕ ДОПУСКАТЬ, а не переносить SL внутрь структуры ради плеча.

Текущие реальные ордера, SMOKE и пользовательские PAPER-планировщики не менялись.
