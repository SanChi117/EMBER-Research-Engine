# EMBER SOURCE/PARITY · P07 / P10 · EXECUTION-LEDGER AUDIT (2026-11-01)

**Status:** evidence only, **0 VERIFIED_FUTURES_CANDIDATE**. Tested original pinned strategy/engine on real Binance USDT-M OHLCV via independent executor. **NOT** an economically validated strategy, **NOT** OOS, **NOT** order-fill parity with Binance, **NO** live/PAPER orders or changes to existing systems.

## Reproducible evidence

- Branch: `research/source-parity-native-traces-20261101`.
- Original source commits P07 `68251be7e1b4c0ade110bd4e097d524c6ce2acbc`, strategy blob `4b04c1834bbf0a3e69d9e67542aea204718550c8`; P10 `65cf4284e7a397673d1ac8c982f0d113027ed27b`, signal blob `7568c60cbef2157065d2d1b8944ca5a4c965f39b`.
- Frozen Binance USD-M futures data `binance_usdtm_closed_20261101.csv`, SHA256 `b885da6dc7e80ea81c7bfb97ec1fb3da615e31824af48625f81cdd376d9a7ee7`. 3 symbols BTC/ETH/SOL, 1499 **closed 1h** candles each (plus 999 D1 each for other project's signal checks). Roughly 30 August–31 October 2026: **insufficient for multi-regime/OOS proof**.
- Real signed funding history (not spot, not synthetic): `binance_usdtm_funding_20261101.csv`, SHA256 `845a467c297cfc9fbe62f6b2616f961a023687a3c85c1e5164db427acab21ec3`, 190 historical funding settlements per asset; 570 rows. All intervals within 20 ms of 8h; observed timestamps may jitter milliseconds. Positive/negative periods BTC 170/20; ETH 162/28; SOL 138/52.
- Auditor code: `replay_execution.py`; test: `tests/test_execution_replay_20261101.py`; **original source checked out and Git SHA verified before running**, no original source file modified.
- [Original CI event parity](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41260634761) successful on Python 3.10/3.11/3.12. [Summary CI](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41260774114) includes comparative figures and explicit source/independent checks.

## 1. P07 Pullback Retest

Native original class `PullbackRetest` + native `perplab.engine.simulator.Simulator`, compared against *separate independently implemented* event/cash ledger. **134/134 trade event tuples** match: BTC 53, ETH 39, SOL 42; exact symbol, side, entry time/price, exit time/price and reason. This is `NATIVE_EVENT_LEDGER_PARITY_OK`, **not** real Binance execution.

**Source integrity issues, all preserved and not repaired in the original:**

1. In `simulator.py`: equity credits `trade.net_pnl - trade.costs` although `net_pnl` already deducts closing cost; exact duplicate exit-fee overcharges on separate diagnostic wallets are BTC $21.00702, ETH $15.57792, SOL $16.93559 (**$53.52053 across THREE wallets, not a combined portfolio**).
2. On the final candle the original source may tag a close-price execution with its **opening timestamp**. The independent parity mode reproduces this *timestamp mistake* for matching tuples; funding calculation uses the final bar's actual close boundary, and the result is explicitly marked `ENDPOINT_CLOCK_WARNING`.
3. P07 original strategy default has **no hard stop or take-profit**; native model has `stop_loss_pct=None`/`take_profit_pct=None`. The simulator's optional stop trigger can miss gap-through bars if `stop_price` lies outside the bar range; this risk is **not actually sampled under no-stop defaults**. Its `exit_signal_vectorized` checks breakouts on *either* side, not just opposite; this may cause early exits and needs original-intent audit.

**Independent corrected accounting, with genuine signed funding and P07's source default commissions/spread/slippage, no stops (original defaults), 3 independent initial $10,000 diagnostic accounts:**

| Asset/account | Trades | Signed funding drag (+ cost, − receipt), $ | Cash net after modeled costs, $ |
|---|---:|---:|---:|
| BTC | 53 | +0.469145 | **−145.128357** |
| ETH | 39 | −0.127539 | **+8.588015** |
| SOL | 42 | +1.083686 | **+148.705144** |

These are *one short 1h sample*, not three capital-managed strategy sleeves; commissions/slippage are assumptions from source model, not measured trades. No mark-based liquidation, bar gap fill model, available size, shared portfolio correlation, OOS or validation by regime. ETH and SOL positive results **do not imply edge**; BTC is negative in this sample.

**Why any price gross PnL arises:** post-breakout/retest/re-breakout entry and exit on subsequent channel breakout; not proven incremental to trend beta/buy-hold/random-entry control. Signed funding is expense/credit only, not signal.

## 2. P10 rgg81 BB Squeeze

Pinned original `BbSqueezeStrategy` and original `backtest.run_backtest` with only an in-memory input adapter replacing data-file loading (no change to strategy or original engine logic). Independently rebuilt execution event loop using source rules. **54/54 completed trades exactly match** by instrument, side, entry/exit clock, prices and exit reasons: `NATIVE_EVENT_LEDGER_PARITY_OK` on **1h research profile**.

**Critical qualifier:** author's README CLI default interval is **15m**, while this closed-candle research audit used **1h**. Thus this is native-code reproduction on a *nondefault timeframe*, **NOT** a successful native-default strategy validation. Source README defaults otherwise: 2% stop, 3% target, 120-min timeout, $1,000 max trade amount, 0.1% **round-trip** fee; BB signal weight 80 means ~$800 per trade. Source engine enters on the *same signal candle's already-known close*.

| P10 54-trade diagnostic accounting | Same-close source execution | Causal next-open transfer | Next-open + 10 bps extra total trade friction |
|---|---:|---:|---:|
| Gross price contribution, USD | +16.000748 | +16.024647 | +16.024647 |
| Author modeled round-trip fee, USD | −43.200000 | −43.200000 | −43.200000 |
| Historical signed funding cost, USD | −0.509896 | −0.445000 | −0.445000 |
| Extra friction, USD | 0 | 0 | −43.200000 |
| **Net, USD** | **−27.709148** | **−27.620353** | **−70.820353** |

The next-open causal transfer has 54 closed events, but entry timing changes by 1 ms and price changes on 20 aligned events. These values are **sum of hypothetical fixed $800 independent trade-level returns**, not a realistic shared compounded equity curve. Commissions and added 10 bps friction are *assumed scenarios*, not actual order receipts, and actual signed funding is accrued using approximate held notional. Same-bar SL/TP order is conservatively resolved; mark-price liquidation, genuine spread/impact and detailed fill order are not proven.

**Mechanism of price gain/loss:** volatility/volume expansion after low Bollinger Band bandwidth, betting on continuation. On this limited sample the **gross +$16 is dwarfed by modeled $43.20 round-trip commissions**, before funding and adverse execution. This is `COST_DOMINATED_ON_RESEARCH_SAMPLE`, **not `FAIL_ALL_REGIMES`**.

## Qualification decisions

- **P07**: source event trace now reproducible; `ACCOUNTING_INTEGRITY_WARNING`, `ENDPOINT_CLOCK_WARNING`, `EXIT_SEMANTICS_WARNING`; `OOS_NOT_DONE`, `PRODUCTION_BLOCKED`. Preserve original as-is. A separate labeled correction is required for future economic testing.
- **P10**: source event trace reproducible for 1h; `COST_DOMINATED_ON_SAMPLE`, `DEFAULT_15M_NOT_YET_TESTED`, `ACTUAL_EXECUTION_UNVERIFIED`. No tuning on this observed window; next original default 15m/expanded period or independent regimes first.
- **VERIFIED_FUTURES_CANDIDATE = 0**. No capital deployment recommendation, no change to `main`/mandate, EMBER/SMOKE/PAPER or connected trading accounts.

## Next independent work

Reproduce author-default P10 on 15m historical futures data and run source-parity full Freqtrade P06 with authentic TA-Lib (not dependency shims). Parallel P04 is still Bybit-native and Binance transfer must not be mistaken for Bybit parity. All full performance screening should have ex-ante universe, regimes, OOS and benchmark attribution with funding/fees/slippage, and independent trade ledger reconstruction.
