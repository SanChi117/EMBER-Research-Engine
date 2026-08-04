# Portfolio WFO — Extended History 30000

## Evidence classification

```text
Classification: extended_overlapping_history
Fresh independent OOS: NO
Configuration hypothesis: bidirectional-high-vol-block
Strategy verdict: FAIL
```

The 30000-bar sample includes the earlier 15000-bar OOS period and extends backward. It is useful for trade-density and robustness diagnosis, but it is not a new untouched OOS proof.

## Setup

- Symbols: `PEPEUSDT, FETUSDT, WIFUSDT, SUIUSDT`
- Interval: `15m`
- Bars per symbol: `30000`
- Date range: `2025-09-26 01:45 UTC` through `2026-08-04 13:30 UTC`
- Profile: `bidirectional-high-vol-block`
- Initial equity: `10000.0`
- WFO: `4 folds`, `30-day lookback`, `3-bar embargo`
- Portfolio mode: one shared portfolio state and equity curve per fold
- Universe: all four symbols retained; PEPE was not removed

Configuration:

```text
allowed_direction_contexts: bull, bear
blocked_volatility_regimes: high_vol
min_confidence: 43.0
min_volume_ratio: 0.70
min_rr: 1.8
max_positions: 1
```

Canonical command:

```bash
python scripts/run_portfolio_wfo.py \
  --data-dir data/oos_4alts_30000 \
  --out-dir results/portfolio_wfo_extended_30000 \
  --report-path results/portfolio_wfo_extended_30000/PORTFOLIO_WFO_EXTENDED_30000.md \
  --report-title "Portfolio WFO — Extended History 30000" \
  --evidence-class extended_overlapping_history \
  --symbols PEPEUSDT,FETUSDT,WIFUSDT,SUIUSDT \
  --profile bidirectional-high-vol-block \
  --interval 15m \
  --bars 30000 \
  --initial-equity 10000
```

## PASS gate

Every condition is required:

| Metric | Requirement |
|---|---:|
| Stability | `>=70%` |
| Average PF | `>=1.5` |
| Worst DD | `<10%` |
| Average return | `>0%` |
| Completed test trades | `>=20` |

## Fold results

| Fold | Test period | Return | PF | DD | Trades | Positive |
|---:|---|---:|---:|---:|---:|---|
| 1 | 2025-10-26 02:30 → 2025-12-21 02:30 UTC | -2.1411% | 0.4293 | 3.4456% | 5 | no |
| 2 | 2025-12-21 02:30 → 2026-02-15 02:30 UTC | +0.0127% | 1.0150 | 3.7361% | 17 | yes |
| 3 | 2026-02-15 02:30 → 2026-04-12 02:30 UTC | -3.0534% | 0.6211 | 4.1456% | 10 | no |
| 4 | 2026-04-12 02:30 → 2026-06-07 02:30 UTC | +2.2396% | 1.2899 | 3.1406% | 14 | yes |

## Summary

```text
Average return: -0.7355%
Average PF: 0.8388
Worst DD: 4.1456%
Stability: 50.00%
Total completed test trades: 46
Zero-trade folds: 0
Status: FAIL
```

Increasing history solved only the sample-size problem:

- trades increased from `8` in the frozen 15000-bar portfolio WFO to `46`;
- every fold received trades;
- stability remained `50%`;
- average return became negative;
- average PF remained below `1.0`, far below the required `1.5`.

The expected improvement to roughly 7–14 trades per fold was broadly achieved (`5/17/10/14`), but the larger sample rejected the strategy configuration on performance and stability rather than frequency.

## Data manifest

| Symbol | Rows | Start UTC | End UTC | SHA-256 |
|---|---:|---|---|---|
| PEPEUSDT | 30000 | 2025-09-26 01:45 | 2026-08-04 13:30 | `ab951df979c99e697f0308244485a31f1f8571b7a4e5981433cbd4aea3d2c53e` |
| FETUSDT | 30000 | 2025-09-26 01:45 | 2026-08-04 13:30 | `859da03ecebe30a6c562ce358e950912ffe339e0da577276101292da410a3ede` |
| WIFUSDT | 30000 | 2025-09-26 01:45 | 2026-08-04 13:30 | `0257122569d738d2edc20f6cf2d36f6be041eeba8ae1c18998eac6e2224e0902` |
| SUIUSDT | 30000 | 2025-09-26 01:45 | 2026-08-04 13:30 | `6ddaba31910294ff99874e0f441d33725860b4751c339024352f1faa7e1ef20c` |

## Decision

```text
Bidirectional high-vol-block default: REJECTED
Historical default configuration: PRESERVED
Filter relaxation on the viewed period: PROHIBITED
Universe Expansion 20: BLOCKED
Paper mode: BLOCKED
Live trading: BLOCKED
```

The next proposed change, `min_volume_ratio 0.70 → 0.55`, may only be registered as a separate hypothesis and evaluated on a genuinely fresh non-overlapping period. The current 30000-bar sample has now been inspected and cannot serve as fresh evidence for filter selection.

## Verification

- Workflow run: `30913719737`
- Job: `92006464215`
- Artifact: `8894548471`
- Artifact SHA-256: `23448a87f1a5afd5f01466e43eeb4368f77136ab98a09e484c24d12ee6986f46`
- Static checks: PASS
- Tests: `38 passed`, one dependency deprecation warning
- Leakage tests: `7 passed`
- Data download: four files × exactly `30000` rows
- Substantive WFO execution: PASS
- Strategy verdict: **FAIL**
