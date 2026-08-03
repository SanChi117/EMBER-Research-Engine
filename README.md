# EMBER Research Engine 0.2.0

EMBER is a **research-only** cryptocurrency strategy engine implementing the HYBRID v2 architecture from `docs/EMBER_ARCHITECTURE_SPEC.md`.

It does not place live orders, does not accept exchange API keys, and does not contain a live execution adapter.

## Current validation status

All completed checks, commands, datasets, metrics, discovered bugs, fixes and next steps are recorded in:

[`docs/VALIDATION_LOG.md`](docs/VALIDATION_LOG.md)

The validation log is the project’s persistent source of truth. New research steps must be appended there with their actual results and a `PASS`, `FAIL` or `BLOCKED` verdict.

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

## Synthetic sanity demo

```bash
python scripts/run_demo.py --out-dir results/demo --bars 1000
```

Outputs:

```text
results/demo/backtest_report.md
results/demo/backtest_trades.csv
results/demo/backtest_trades.parquet
results/demo/wfo_report.md
```

A positive synthetic PF is only a deterministic sanity check. It is not evidence of live profitability.

## Backtest a local CSV

```bash
python scripts/run_backtest.py data/candles.csv --out-dir results/backtest --equity 10000
```

The CSV is read through `polars.scan_csv`, so a 22GB file is not loaded into RAM at once.

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

## Public Binance data

```python
from ember.core.data_engine import DataEngine

candles = DataEngine.fetch_binance(
    symbols=["DOGEUSDT"],
    interval="15m",
    limit=1000,
)
```

The loader uses public endpoints only, retries three times with 1/2/4-second backoff, rate-limits requests, prefers Binance Vision, and falls back to Futures `fapi`.

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

The specification default `allowed_direction_contexts=("down",)` is preserved. The detector maps `down` to bearish context and also accepts explicit `bull`/`bear` aliases.

## Scope and known limitations

The document itself identifies several research TODOs. Version 0.2.0 keeps them explicit rather than pretending they are solved:

- FVG mitigation uses latest-zone tracking, not a full multi-zone ledger.
- HTF POI activity is an approximation based on recent unmitigated FVG/OB events.
- resampling assumes the input timeframe is complete and regularly spaced.
- Binance Vision provides spot klines; Futures `fapi` is the fallback.
- leverage is a research sizing model and does not model liquidation or funding.

## Live gate

Live trading remains prohibited until all conditions are met:

- at least 100 completed paper trades;
- at least 30 calendar days of paper observation;
- paper metrics within +/-10% of backtest expectations;
- WFO result is `PASS`.

See `docs/LIVE_GATE.md`.
