# EMBER Portfolio-Level OOS WFO

Дата выполнения: 2026-08-03 UTC  
Workflow run: `30847701247`  
Artifact: `8869390031`  
Artifact SHA-256: `eac603f9d2e2677adef0dab60f374cfa9773b0fc52dd9e0b5ae2091b7f2f5803`

## Frozen protocol

- Fixed universe: `PEPEUSDT, FETUSDT, WIFUSDT, SUIUSDT`
- Source datasets: frozen artifact from OOS run `30842493927`
- Interval: `15m`
- Bars per symbol: `15000`
- Profile: `high-vol-block`
- WFO: 4 folds, 30-day lookback, 3-bar embargo
- Existing pass gate:
  - stability score `>= 70%`
  - average PF `>= 1.5`
  - worst DD `< 10%`
  - average return `> 0`
- No symbol was removed after seeing the individual OOS result.

Executed command:

```bash
python scripts/run_fixed_wfo.py \
  --data-dir frozen_oos/data/oos_4alts \
  --out-dir results/oos_portfolio_wfo \
  --symbols PEPEUSDT,FETUSDT,WIFUSDT,SUIUSDT \
  --profiles high-vol-block \
  --interval 15m \
  --bars 15000
```

The implemented CLI uses `--profiles`, not singular `--profile`.

## Result

```text
Status: FAIL
Folds: 4
Zero-trade folds: 2
Average return: +1.6860%
Average PF: inf
Worst DD: 2.4592%
Stability: 50.00%
```

| Fold | Test period | Return | PF | DD | Trades | Positive |
|---:|---|---:|---:|---:|---:|:---:|
| 1 | 2026-03-30 13:30 UTC → 2026-04-24 13:30 UTC | 0.0000% | 0.0000 | 0.0000% | 0 | no |
| 2 | 2026-04-24 13:30 UTC → 2026-05-19 13:30 UTC | 0.0000% | 0.0000 | 0.0000% | 0 | no |
| 3 | 2026-05-19 13:30 UTC → 2026-06-13 13:30 UTC | +0.6424% | 1.2750 | 2.4592% | 4 | yes |
| 4 | 2026-06-13 13:30 UTC → 2026-07-08 13:30 UTC | +6.1017% | `inf` | 0.0000% | 4 | yes |

`PF = inf` in fold 4 means that four completed trades produced no losing trade. With only four trades, it is not statistically strong evidence and does not override the stability failure.

## Trade-density correction

The earlier estimate of `0.14 × 4 = 0.56 trades/day` counted the same four-symbol sample twice.

The full individual OOS test produced **22 trades in total across all four symbols** over approximately `156.24` days:

```text
22 / 156.24 = 0.141 portfolio trades/day
0.141 / 4 = 0.035 average trades/day per symbol
```

A 25-day WFO test fold therefore had an empirical expectation of roughly:

```text
0.141 × 25 = 3.52 portfolio trades per fold
```

Actual fold counts were `0, 0, 4, 4`, not `15–25`.

## Decision

**Portfolio-level OOS WFO: FAIL.**

Reasons:

1. stability was `50%`, below the required `70%`;
2. two of four test folds had zero trades;
3. the two active folds contained only four trades each;
4. fold 3 PF was `1.275`, below the required `1.5`;
5. the formally infinite average PF is dominated by one four-trade fold with no losses and is not reliable evidence of robustness.

The result does **not** support the statement that the strategy is robust at portfolio level on this OOS universe.

PEPEUSDT must not be removed retroactively to improve this OOS result. Removing it after observing its performance would be universe-selection leakage. Excluding PEPE can only be treated as a new research hypothesis, frozen before a later validation on a fresh, non-overlapping period or a new predeclared universe.

```text
Cross-symbol full-period criterion: PASS 3/4
Portfolio OOS WFO: FAIL
Statistical confidence: INSUFFICIENT
PEPE exclusion from current evidence: REJECTED
Paper gate: BLOCKED
Live gate: BLOCKED
```
