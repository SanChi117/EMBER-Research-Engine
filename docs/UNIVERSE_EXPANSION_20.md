# Universe Expansion 20

## Status

```text
Portfolio WFO OOS prerequisite: FAIL
Universe Expansion 20 execution: BLOCKED
Paper mode: BLOCKED
Live trading: BLOCKED
```

The universe-expansion runner and output contract are implemented, but the batch was not executed because the specification permits Task 3 only when the canonical Portfolio WFO OOS result is `PASS`.

The factual prerequisite is recorded in [`PORTFOLIO_WFO_OOS.md`](PORTFOLIO_WFO_OOS.md):

- stability: `50%` versus required `>=70%`;
- completed test trades: `8` versus required `>=20`;
- fold trade counts: `0 / 0 / 4 / 4`;
- final status: `FAIL`.

No 20-symbol list, market result, or tier assignment is fabricated.

## Implemented protocol

The following components are ready for a later valid run:

- `scripts/scan_universe.py` freezes the top 20 eligible Binance USD-M perpetual USDT pairs by 24-hour quote volume before performance testing;
- the predeclared exclusions include the top pairs listed in the specification, the Core 6, and the OOS 4;
- leveraged-token suffixes `UP`, `DOWN`, `BULL`, and `BEAR` are excluded;
- the frozen list is written to `data/universe_20.json`;
- `scripts/run_universe_expansion.py` requires exactly 20 unique USDT symbols;
- the runner checks `docs/PORTFOLIO_WFO_OOS.json` and refuses execution unless its status is `PASS`;
- every symbol is tested on exactly 15000 bars of 15-minute data with the unchanged `high-vol-block` profile;
- outputs are written as Markdown, JSON, and CSV;
- symbol removal after observing results is prohibited.

## Tier rules

| Tier | Requirement |
|---|---|
| Tier 1 | PF > 1.5, return > 0, trades >= 10 |
| Tier 2 | PF > 1.0, return > 0, trades >= 5 |
| Tier 3 | PF <= 1.0, return <= 0, or insufficient trades |

## Tier table

| Symbol | Trades | Return | PF | DD | Win Rate | Tier | Status |
|---|---:|---:|---:|---:|---:|---|---|
| — | — | — | — | — | — | — | BLOCKED |

## Expansion verdict rule

| Tier 1 count | Interpretation |
|---:|---|
| 10–20 | PASS: broader research universe and paper evaluation may proceed |
| 5–9 | PARTIAL: selective research only; separate frozen validation required |
| 0–4 | FAIL: expansion hypothesis rejected for that fixed universe and period |

## Canonical commands

The scanner command must only be used when a valid expansion run is authorized:

```bash
python scripts/scan_universe.py \
  --max-symbols 20 \
  --interval 15m \
  --bars 15000 \
  --universe-output data/universe_20.json \
  --data-dir data/universe_scan \
  --out-dir results/universe_scan
```

The gated batch command is:

```bash
python scripts/run_universe_expansion.py \
  --portfolio-report docs/PORTFOLIO_WFO_OOS.json \
  --universe-file data/universe_20.json \
  --interval 15m \
  --bars 15000 \
  --initial-equity 10000 \
  --data-dir data/universe_expansion_20 \
  --out-dir results/universe_expansion_20 \
  --report-path docs/UNIVERSE_EXPANSION_20.md
```

With the current `FAIL` prerequisite, the second command writes a factual `BLOCKED` report and exits without downloading or backtesting symbols.
