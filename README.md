# EMBER Research Engine 0.2.0

EMBER is a **research-only** cryptocurrency strategy engine implementing the HYBRID v2 architecture from `docs/EMBER_ARCHITECTURE_SPEC.md`.

It does not place live orders, does not accept exchange API keys, and does not contain a live execution adapter.

## Current validation status

The persistent validation history is stored in:

[`docs/VALIDATION_LOG.md`](docs/VALIDATION_LOG.md)

The latest six-symbol, 15000-bar study is stored separately with all per-symbol metrics, aggregate results, decisions and WFO warnings:

[`docs/CORE_VALIDATION_15000.md`](docs/CORE_VALIDATION_15000.md)

Current research status:

```text
Six-symbol baseline backtest: PASS
Baseline WFO: PASS with one zero-trade fold warning
High-vol-block backtest: PASS
High-vol-block WFO: PASS with one zero-trade fold warning
Structure-bias replacement: FAIL
Opposite-liquidity clean fixed-universe WFO: PENDING
Paper gate: BLOCKED
Live gate: BLOCKED
```

A `PASS` applies only to the named validation stage. It does not authorize live trading.

## Non-negotiable research rules

1. **Zero Look-Ahead** - entry features, MTF context and setup detection only use bars at or before `entry_time`.
2. **Regime First** - setup direction is filtered by HTF bias and market regime.
3. **MTF hierarchy** - 1D/4H context, 15m trigger, optional 5m confirmation field.
4. **Cost aware** - fees and slippage are mandatory in the risk gate and PnL.
5. **Completed trades only** - structure learning requires `exit_time < entry_time`.
6. **No placeholder results** - incomplete future data invalidates the simulated trade.
7. **Purged WFO** - train and test are separated by an embargo.
8. **Kill switch first** - daily -2%, weekly -5%, or 3 consecutive losses halt the portfolio.

## Architecture

```text
Binance Public API / local lazy CSV
  -> ember.core.data_engine
  -> ember.core.features
  -> ember.core.context_builder
  -> ember.strategy.setups
  -> ember.strategy.risk_engine
  -> ember.strategy.exit_simulator
  -> ember.filters.quality_gate
  -> ember.filters.structure_gate
  -> ember.simulation.portfolio
  -> ember.simulation.walk_forward
  -> ember.research.report_engine
  -> ember.server.paper_server
```

The local CSV schema is:

```text
symbol,time,open,high,low,close,volume
```

## Installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/SanChi117/EMBER-Research-Engine.git
cd EMBER-Research-Engine
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Required checks

```bash
ruff check ember/ tests/ scripts/
pytest tests/ -v
pytest tests/test_no_leakage.py -v
```

`tests/test_no_leakage.py` covers future-price isolation, future-only exits, completed-trade-only learning, no placeholder results, uncapped PF and OHLC validation.

## Mixed-regime synthetic sanity demo

```bash
python scripts/run_demo.py --demo --bars 5000 --wfo --out-dir results/demo
```

The generator is deterministic and includes `trend_up`, `trend_down`, `range` and `high_vol` segments. It also includes adverse reversals so a perfect win rate is not assumed.

Outputs:

```text
results/demo/backtest_report.md
results/demo/backtest_trades.csv
results/demo/backtest_trades.parquet
results/demo/wfo_report.md
results/demo/reject_diagnostics.json
```

Synthetic results test pipeline behavior only. They are not evidence of live profitability.

## Backtest a local CSV

```bash
python scripts/run_backtest.py \
  data/candles.csv \
  --out-dir results/backtest \
  --equity 10000
```

The CSV is read through `polars.scan_csv`, so a large file is not loaded into RAM at once.

### Reject diagnostics

```bash
python scripts/run_backtest.py \
  data/DOGEUSDT_15m_5000.csv \
  --profile baseline \
  --diagnostics \
  --out-dir results/doge_baseline
```

Available profiles:

```text
baseline             specification EMA20 +/-2% and down-only context
both-directions      EMA20 +/-2% with bull and bear context
ema-tight            EMA20 +/-0.5% with bull and bear context
ema50                EMA50 +/-2% with bull and bear context
structure-bias       swing-structure bias with bull and bear context
high-vol-block       baseline plus blocked high_vol regime
opposite-liquidity   baseline plus opposite HTF liquidity target
wide                 diagnostic-only relaxed confidence/volume/RR/ATR values
```

`baseline` remains the production research default. The other profiles are controlled experiments and do not silently change the architecture contract.

The backtester reports exactly where bars and candidates are rejected: context, direction, regime, setup, confidence, volume, risk, RR, costs, quality, structure, missing future data, portfolio overlap and kill switches.

### Compare diagnostic profiles

```bash
python scripts/run_diagnostics.py \
  data/DOGEUSDT_15m_5000.csv \
  --out-dir results/doge_diagnostics
```

This writes separate reports for each profile and a combined `summary.json`.

## Six-symbol 15000-bar validation

Download and test approximately 156 days for every core symbol:

```bash
python scripts/run_core_validation.py \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,structure-bias,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000 \
  --data-dir data/core_validation \
  --out-dir results/core_validation
```

The runner writes:

```text
results/core_validation/summary.csv
results/core_validation/summary.json
results/core_validation/summary.md
results/core_validation/reports/<symbol>/<profile>/...
```

Run WFO on one fixed, predeclared universe without selecting symbols from full-period performance:

```bash
python scripts/run_fixed_wfo.py \
  --data-dir data/core_validation \
  --out-dir results/fixed_wfo \
  --symbols INJUSDT,TONUSDT,DOGEUSDT,ARBUSDT,NEARUSDT,OPUSDT \
  --profiles baseline,high-vol-block,opposite-liquidity \
  --interval 15m \
  --bars 15000
```

## Public Binance data

For one API page, use `DataEngine.fetch_binance`:

```python
from ember.core.data_engine import DataEngine

candles = DataEngine.fetch_binance(
    symbols=["DOGEUSDT"],
    interval="15m",
    limit=1000,
)
```

For longer histories, use the paginated public downloader:

```bash
python scripts/fetch_binance.py \
  --symbols DOGEUSDT \
  --interval 15m \
  --limit 5000 \
  --out-dir data
```

Multiple symbols are comma-separated. No API keys are accepted or required. The downloader paginates with `endTime`, retries failed requests, prefers Binance Vision and falls back to Futures `fapi`.

## Purged walk-forward

```bash
python scripts/run_wfo.py data/candles.csv --out-dir results/wfo --test-days 7
```

WFO passes only when all specification thresholds are met:

```text
stability_score >= 70%
avg_pf >= 1.5
worst_dd < 10%
avg_return > 0
```

Zero-trade folds are reported separately. A formal threshold pass with a zero-trade fold is recorded as a warning and is not sufficient for live readiness.

## Virtual-only paper server

```bash
python scripts/run_paper_server.py --host 127.0.0.1 --port 8095 --db paper_trades.db
```

Endpoints:

```text
GET  /health
GET  /status
GET  /trades?limit=20
GET  /export/trades.csv
POST /paper-webhook
```

Open a virtual trade:

```bash
curl -X POST http://127.0.0.1:8095/paper-webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "action":"open",
    "symbol":"DOGEUSDT",
    "side":"short",
    "setup_type":"pullback",
    "entry_time":"2024-01-01T00:00:00+00:00",
    "entry_price":100,
    "stop_price":101,
    "target_price":98.2
  }'
```

No exchange keys or secrets are used by the paper server.

## Configuration

Defaults are defined in `ember/config.py` and mirrored in `config/ember.example.json`.

The specification default `allowed_direction_contexts=("down",)` and EMA20 +/-2% bias are preserved. Alternative direction, threshold, EMA-period, structure-bias, volatility-block and TP modes are tested through named research profiles.

The configuration supports:

```text
htf_bias_mode: ema | structure
htf_ema_period: positive integer
htf_ema_threshold_pct: positive percentage
blocked_volatility_regimes: tuple of runtime regime names
tp_mode: fixed_rr | opposite_htf_liquidity
```

`ContextBuilder` emits the volatility regime name `high_vol`; a block list intended to reject it must therefore contain `high_vol`, not `high`.

## Scope and known limitations

The document itself identifies several research TODOs. Version 0.2.0 keeps them explicit rather than pretending they are solved:

- FVG mitigation uses latest-zone tracking, not a full multi-zone ledger.
- HTF POI activity is an approximation based on recent unmitigated FVG/OB events.
- resampling assumes the input timeframe is complete and regularly spaced.
- Binance Vision provides spot klines; Futures `fapi` is the fallback.
- leverage is a research sizing model and does not model liquidation or funding.
- profile selection on one historical sample creates meta-selection risk.
- a positive result from a small number of trades is not statistically sufficient.

## Live gate

Live trading remains prohibited until all conditions are met:

- at least 100 completed paper trades;
- at least 30 calendar days of paper observation;
- paper metrics within +/-10% of backtest expectations;
- WFO result is `PASS`;
- all leakage tests pass.

See `docs/LIVE_GATE.md`.
