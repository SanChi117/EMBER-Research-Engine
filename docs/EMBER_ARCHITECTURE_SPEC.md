# EMBER Research Engine - Architecture Specification 0.2.0

This file preserves the implementation contract supplied for the project.

## Purpose

Build a research-only engine that follows the path Research -> Paper -> Live, with live execution blocked behind an explicit gate.

## Mandatory principles

- Zero Look-Ahead.
- Regime First.
- MTF hierarchy: 1D/4H -> 1H location/POI -> 15m trigger -> optional 5m confirmation.
- Mandatory fee and slippage cost gate.
- Completed-trade-only structure learning.
- No placeholder trade results.
- Purged walk-forward validation with embargo.
- Kill switches: daily -2%, weekly -5%, three consecutive losses.

## Required modules

```text
core.data_engine
core.features
core.context_builder
strategy.setups
strategy.risk_engine
strategy.exit_simulator
filters.quality_gate
filters.structure_gate
simulation.portfolio
simulation.walk_forward
research.report_engine
server.paper_server
```

## Baseline setups

Only `pullback` and `ignition` are enabled. `breakout`, `range_rotation`, `liquidity_reclaim` and `watch` are blocked.

## Validation thresholds

WFO is `PASS` only when:

- stability score >= 70%;
- average PF >= 1.5;
- worst drawdown < 10%;
- average return > 0.

## Paper server

Port 8095, FastAPI and SQLite, virtual trades only. Required endpoints:

```text
GET /health
GET /status
GET /trades?limit=20
GET /export/trades.csv
POST /paper-webhook
```

## Live gate

Live execution remains blocked until at least 100 completed paper trades, 30 observation days, paper metrics within +/-10% of backtest, and WFO `PASS`.
