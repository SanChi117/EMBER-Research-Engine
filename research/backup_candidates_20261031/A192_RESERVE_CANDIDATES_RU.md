# A192 — поиск запасных торговых стратегий с открытым кодом, 31.10.2026

## Цель и ограничение
После A188 успешного, но слабостатистического DoubleMA и A191 плохого SingleB ищем несколько альтернатив с другой механикой, преимущественно 4h и полностью открытыми правилами. Статус **НЕ экономический PASS** без независимого воспроизведения, честного OOS и execution stress. Никаких live ордеров, PAPER не меняем. Дата исследования 31.10.2026.

## Сводка приоритетов

### HERMES SuperTrend(10,3), 4H: ПРИОРИТЕТ 1 — источник полностью открыт
- Repo https://github.com/chrysek70/hermes-trading , pinned upstream main **702ee511c669fb521744270e8b3cb9e8964ac998**.
- Продукт: long-only SuperTrend flip DOWN→UP на закрытом 4h, с gate EMA50>EMA200. Вместо старых долгих MTF зон — простой трендовый модуль. Исходники `hermes_trading/signals.py`, `hermes_trading/backtest.py`, `hermes_trading/walk_forward.py`, `state/strategy_supertrend.yaml`, `scripts/run_supertrend_extended.py`; итоговые CSV `results/supertrend_48mo_comparison_20260530_092716.csv` и `results/multiasset_supertrend_rs_comparison_20260530_113106.csv`.
- Авторские 48-месячные 20-fold walk-forward, 4H, комиссия **10 bps ЗА сторону**, slippage **5 bps ЗА сторону**, 6-bar embargo:
  - BTC: N35, +38.661369%, PF2.236525, DD9.63057%, 45.7143% winners, 10/20 positive folds.
  - ETH: N30, +37.864311%, PF2.922881, DD5.30153%, 63.3333% winners, 10/20 positive folds.
  - BTC+ETH multiasset one-at-a-time: N39, +40.9879%, PF2.47991, DD9.607%, 12/20 folds positive.
  - BTC+ETH parallel equal-risk: N65, +39.72%, PF2.50, DD5.54% (author README/research report); five coin portfolio 155 trades PF2.19, **fails author's PF gate 2.24**, do not cherry-pick.
- **Validation scope:** Confirmed cited numbers exist in real author CSV and original code; **NOT yet independent native Freqtrade parity**. Technical flags: `backtest.py` opens position at *same signal candle close* after computing close, with fixed 5bps slippage; current 4h SuperTrend band uses the same bar's high-low/close and stop check uses same bar low, risking path/order artifact. Source signal loop uses causal prior final bands (not future), but same-bar fill and current-bar stop sequencing require **next-bar-open & 1m detail stress** before economic promotion. No actual 2026 post-May OOS verified for ETH yet. N30 thin and 10/20 positive folds. Tested *long only*; do not call this original long/short.
- **Decision:** A rank, **independent replay next**, threshold may be too sparse to fill user's daily trade-frequency goal.

### APEX no-pyramid 4H / 180-day-high: ПРИОРИТЕТ 2 — broad sensitivity robustness
- Repo https://github.com/EstebanSP23/crypto_systematic_research pinned main **5df0c43f6d48b7d8dbb74843d6747e5ddbb6819b**.
- Full logic from `2_strategies/02_apex_no_pyramid/walkforward.py` (blob `52d6851b9356d9e26df860812489369b79ee1032`): 4h close > prev 1080-bar high, SMA50>SMA200 and close>SMA50, volume >1.5x20-bar, ATR2 stop, 2R partial take at 50%, BE after TP1 and 20-bar low trailing, 2% wallet risk, max3 positions, 8 coin universe, 0.10% fee each side, no pyramid, **long-only**.
- Author claims P1 training 2022–23 19 trades +24.17% APY; P2 2024–May2026 47 trades +5.9861% APY, DD −14.1068%, 38.298% win, +0.19678R expectancy. Entire published `sensitivity_apex.csv` pinned blob `ba2b9c788bf46559389a5b9178435941359418bd` independently parsed (pure arithmetic of existing records): **27/27** P2 positive expectancy; **26/27** P2 APY positive. Per-strategy author trade CSV `apex_trades.csv` pinned blob `d91bafb5129c4d896ff4cd260f16c60faa8b80b7` has 19 P1 and 47 P2 records, 11 and 18 positive respectively, gross sum P2 trade-PnL ≈+277.071 USD. **Don't conflate P2 47-trade model with 27 grid variants which are overlapping tests.**
- Limitations: fee model **omits funding**, slippage and detailed 1m fills, sparse ~20 trades/year across 8 coins, 2025 year -$93 (per author), income 5–10% per annum and DD 15–20% expectation; **top3 51% of profit**. This is a potential low-turnover backup, NOT daily setup engine, and not a confirmed futures execution edge.
- **Decision:** B rank, native 4h only with sufficient 180-day warmup and multi-year source; robust prospective structure, low growth rate.

### Quattro Donchian 4H 4 pyramids: MARGINAL/high-risk research, not promoted
- Same EstebanSP23 repo `2_strategies/01_quattro_donchian/backtest.py`; 20-bar breakout + rising daily EMA200, up to 4 units; per-unit 2% acct risk, 5% wallet hard stop, exit 10bar lower low, only BTC long.
- Author historical 2022–May2026 +1107%, 94 grouped trades, PF not enough here, drawdown **37.5%**, projected future DD35–50%, many rare large winners, 26.6% win, funding omitted; live BloFin deployment reported by author but not independently verified; production code not published, research source is.
- **Decision:** DO NOT PROMOTE as usable reserve given DD, pyramiding and small account.

### FailureToReturn (FTR) 1H: exact native ETH OOS zero signals — POWER FAIL
- Repo `hrodrig/freqhub-strategies` pinned commit `210952246ae457a5f6d5e089ddea8b4960a71775` code blob `6e80c0b96754c21744726120b6904f940621ec01`, source `FailureToReturnStrategy.py`; pattern impulse>prior high, bounded retest, continuation signal, intended forex, timeframe1h, hard SL −8%, can_short=False despite short code, uses current EMA200 + ATR.
- **Our real native Freqtrade 2026.4** Binance ETH USDM 1h with real Binance candles / settled funding / mark, static offline exchange metadata, 2026-08-01..2026-09-30, 5000 USD/500 stake, fees 0.05% and 0.125% side, **zero trades both scenarios**, 0% PNL and PF=0 (undefined/zero trades, NOT evidence of unprofitability). Real workflow [#41143948231](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41143948231) SUCCESS and [artifact #13020268202](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41143948231/artifacts/13020268202), zip SHA256 `c5c596390a5d425401dd396011949ea74e9467259cad5ddb45e96ed4bb4da5f5`.
- **Decision:** NOT RESERVE, `NO_POWER_NO_TRADES`. Not enough evidence for real trading; could work with FX in other windows, not proven crypto.

## Дополнительный отрицательный отбор
- `jamniol/freqtrade-setup/strategies/DivergenceStrategy.py` source Git blob `50b686793d88161e8571e178e9e310f71f43bb85`: source uses `scipy.signal.argrelextrema(...,order=swing_order)` on entire DataFrame then sets divergence at pivot index when next `order` bars needed to confirm the extremum. This is a **suspected static lookahead** not causally known at its timestamp and not usable OOS without patch and parity; do not accept catalog ranking as proof.
- `hrodrig/freqhub-strategies/strategies/FreqHub.Strategy.MandelbrotFibonacci/MandelbrotFibonacciStrategy.py` Git blob `ea54ee26dac523fa6ce0e173b75453a6ad5087fc`: `high.shift(-1), shift(-2)` etc in fractal detection and immediate signal attribution; **clear future-bar dependency**, reject unless causal delay added (then becomes a different strategy).
- `Danson77/Freqtrade_AIO_UI/.../DS_BNC_EV1E_5m.py`: spot only, fallback hard stoploss -99%, `use_custom_stoploss=True` requires independent safe-tail review; not a prudent futures reserve; catalog's score is not proof.
- `davidzr/freqtrade-strategies/NFI5MOHO_WIP.py`: 1189 lines, `INTERFACE_VERSION=2`, -99% SL fallback, many parameters; not a simple reproducible / maintainable reserve.
- `AKzar1el/walk-forward-crypto`: author advertises +144.5% in 2024–2026 paper but `docs/REDACTION_REPORT.md` confirms **full source and 24-config pool proprietary / private**; exclude original reproduction, not a real open-source candidate.
- Research methods: `gitittttf/trading-ai-research` declares 17 preregistered variants none reached live gates, corroborates cost sensitivity; `rajdeep7878/marketmind-open` rejects many apparently winning strategies after real retail costs. Useful audit methodology but not deployable edge.
- Freqle rank https://freqle.org/ranking community strategy sorting has survivorship bias, lookahead/stops/fees differ. Rankings alone do not validate our use case.

## Prioritized next checks
1. **A193** isolate Hermes SuperTrend full `signals.py` + same author backtest and create **causal next-bar-open / same-bar-stop stress** on unchanged timeframes and parameters; inspect closed trade-level receipts, validate 20 folds independent dates, then ETH Aug-Oct2026 and BTC/ETH multi-year Freqtrade/original parity. `A193` branch isolated from old SMOKE.
2. **A194** Apex no-pyramid: 4h 180-day warmup, 8-asset fixed universe, transaction costs incl funding, 1m fill, compare original custom engine, walk-forward no training on OOS; high 2025 drawdown and only 5.99% APY base caution.
3. **A195** further look for crypto 1h/15m full-source long+short with >200 independent post-release OOS trades, PF net 1.3+, controlled 1m execution, none currently verified. Do not force candidate adoption or alter trading rules to manufacture trades.

**Verdict A192:** RESEARCH_SHORTLIST_FOUND, **NO NEW INDEPENDENT ECONOMIC PASS**. All author metrics marked as third-party estimates, independently verified only CSV arithmetic and source availability. No live orders, SMOKE unchanged.
