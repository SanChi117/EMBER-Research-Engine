# Portfolio WFO — OOS 4 Alts

## Setup

- Symbols: `PEPEUSDT, FETUSDT, WIFUSDT, SUIUSDT`
- Interval: `15m`
- Bars per symbol: `15000` (~156 days)
- Profile: `high-vol-block`
- Initial equity: `10000.0`
- WFO: `4 folds`, `30-day lookback`, `3-bar embargo`
- Source datasets: frozen artifact from OOS run `30842493927`
- Universe policy: fixed before validation; no symbol removal
- Portfolio mode: all four symbols are passed together to one `WalkForwardValidator`; each fold uses one shared `PortfolioSimulator` and one portfolio equity curve

Canonical command:

```bash
python scripts/run_portfolio_wfo.py \
  --data-dir frozen_oos/data/oos_4alts \
  --symbols PEPEUSDT,FETUSDT,WIFUSDT,SUIUSDT \
  --profile high-vol-block \
  --interval 15m \
  --bars 15000 \
  --initial-equity 10000 \
  --out-dir results/portfolio_wfo_oos \
  --report-path docs/PORTFOLIO_WFO_OOS.md
```

## PASS/FAIL gate

A portfolio PASS requires every condition:

| Metric | PASS requirement |
|---|---:|
| Stability | `>= 70%` |
| Average PF | `>= 1.5` |
| Worst DD | `< 10%` |
| Average return | `> 0%` |
| Total completed test trades | `>= 20` |

## Results

| Fold | Train Start | Train End | Test Start | Test End | Return | PF | DD | Trades |
|---:|---|---|---|---|---:|---:|---:|---:|
| 1 | 2026-02-28 12:45 UTC | 2026-03-30 12:45 UTC | 2026-03-30 13:30 UTC | 2026-04-24 13:30 UTC | 0.0000% | 0.0000 | 0.0000% | 0 |
| 2 | 2026-03-25 12:45 UTC | 2026-04-24 12:45 UTC | 2026-04-24 13:30 UTC | 2026-05-19 13:30 UTC | 0.0000% | 0.0000 | 0.0000% | 0 |
| 3 | 2026-04-19 12:45 UTC | 2026-05-19 12:45 UTC | 2026-05-19 13:30 UTC | 2026-06-13 13:30 UTC | +0.6424% | 1.2750 | 2.4592% | 4 |
| 4 | 2026-05-14 12:45 UTC | 2026-06-13 12:45 UTC | 2026-06-13 13:30 UTC | 2026-07-08 13:30 UTC | +6.1017% | `inf` | 0.0000% | 4 |

## Summary

- Average return: `+1.6860%`
- Average PF: `inf`
- Worst DD: `2.4592%`
- Stability: `50.00%`
- Total completed test trades: `8`
- Zero-trade folds: `2/4`
- Status: **FAIL**

The formal failure is unambiguous:

1. stability is `50%`, below the required `70%`;
2. total completed test trades are `8`, below the required `20`;
3. two folds contain no trades;
4. fold 3 PF is `1.2750`, below `1.5`;
5. fold 4 has only four trades, so `PF = inf` is not strong evidence.

## Interpretation

The fixed four-symbol portfolio does not demonstrate robust OOS walk-forward performance. Positive average return and low drawdown do not override the sparse sample, the two zero-trade folds, or the failed stability gate.

The earlier estimate of `0.14 × 4 = 0.56 trades/day` double-counted the already aggregated four-symbol sample. The full OOS result contained 22 trades across the whole portfolio over about 156 days, or approximately `0.141 portfolio trades/day`; a 25-day fold therefore had an empirical expectation near 3.5 trades, consistent with the observed `0, 0, 4, 4`.

PEPEUSDT cannot be removed retroactively from this result. That would be universe-selection leakage. A PEPE exclusion may only be a new hypothesis frozen before validation on a fresh non-overlapping period or a new predeclared universe.

## Next Step

The specification permits Universe Expansion Test only when Portfolio WFO is PASS. Because this result is FAIL:

```text
Universe Expansion 20: BLOCKED
Paper mode: BLOCKED
Live trading: BLOCKED
```

Preserve this failure, keep the current strategy parameters unchanged, and validate any new universe or symbol-selection hypothesis on untouched data.

## Verification record

- Original portfolio workflow run: `30847701247`
- Original artifact: `8869390031`
- Artifact SHA-256: `eac603f9d2e2677adef0dab60f374cfa9773b0fc52dd9e0b5ae2091b7f2f5803`
- Original checks: Ruff PASS, 22 tests PASS, no-leakage PASS
- Historical equivalent report: `docs/OOS_PORTFOLIO_WFO.md`
