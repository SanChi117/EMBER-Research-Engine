# Configuration and Frequency Validation — 15000 Synthetic Bars

## Purpose

This experiment tested the proposed default change:

```python
allowed_direction_contexts = ("bull", "bear")
blocked_volatility_regimes = ("high_vol",)
```

The change was evaluated as a research hypothesis, not assumed safe. The same fixed mixed-regime synthetic sample was used for four isolated configurations so direction and volatility effects could be attributed separately.

## Protocol

- Dataset: `mixed_regime_synthetic_data`
- Bars: `15000` 15-minute bars
- Approximate duration: `156.25 days`
- Seed: `42`
- Strategy thresholds unchanged:
  - `min_confidence = 43.0`
  - `min_volume_ratio = 0.70`
  - `min_rr = 1.8`
  - `max_positions = 1`
- No setup detector or quality threshold changes
- No symbol removal
- Synthetic performance is diagnostic only and cannot authorize paper or live trading

Canonical command:

```bash
python scripts/run_frequency_diagnostics.py \
  --bars 15000 \
  --seed 42 \
  --out-dir results/frequency_diagnostics
```

## Frequency and performance

| Profile | Directions | High-vol blocked | Trades | Trades/day | Estimated trades/25d fold | Return | PF | DD |
|---|---|---|---:|---:|---:|---:|---:|---:|
| legacy-baseline | down | no | 30 | 0.1920 | 4.80 | +19.2842% | 2.3873 | 2.6167% |
| both-directions | bull, bear | no | 3 | 0.0192 | 0.48 | -3.9040% | 0.0000 | 3.9040% |
| high-vol-block | down | yes | 30 | 0.1920 | 4.80 | +19.2842% | 2.3873 | 2.6167% |
| bidirectional-high-vol-block | bull, bear | yes | 3 | 0.0192 | 0.48 | -3.9040% | 0.0000 | 3.9040% |

## Reject diagnostics

| Reject reason | legacy-baseline | both-directions | high-vol-block | bidirectional-high-vol-block |
|---|---:|---:|---:|---:|
| bars_seen | 14940 | 14940 | 14940 | 14940 |
| neutral_context | 3424 | 3424 | 3424 | 3424 |
| direction_reject | 3924 | 0 | 3028 | 0 |
| regime_reject | 0 | 0 | 1728 | 1728 |
| no_setup | 7116 | 10724 | 6287 | 9012 |
| volume_low | 7 | 11 | 6 | 6 |
| candidate_passed | 469 | 781 | 467 | 770 |
| quality_reject | 32 | 46 | 32 | 46 |
| structure_reject | 36 | 86 | 36 | 86 |
| overlap_reject | 23 | 1 | 23 | 1 |
| halted | 1 | 1 | 1 | 1 |
| executed | 30 | 3 | 30 | 3 |

The remaining recorded reject counters were zero for all four profiles: `setup_blocked`, `confidence_low`, `risk_none`, `rr_low`, `cost_gate`, `no_future`, and `portfolio_reject`.

## Findings

1. Blocking `high_vol` did not change the completed-trade count or synthetic performance in the down-only control. It moved 1728 bars into `regime_reject`, but the final result remained 30 trades, PF 2.3873.
2. Allowing both directions increased `candidate_passed` from 469 to 781, but completed trades collapsed from 30 to 3.
3. The bidirectional variants hit three consecutive losses and produced `-3.9040%`, PF `0.0`. The kill switch then halted the run.
4. `min_confidence`, `min_rr`, costs, and volume were not the principal bottlenecks in this sample. Their reject counters were zero or negligible.

## Decision

```text
Proposed bidirectional default: REJECTED
High-vol block as isolated profile: RETAINED FOR RESEARCH
Historical EmberConfig default: PRESERVED
Step 3 extended-history WFO: REQUIRED AND COMPLETED
Step 4 filter relaxation: NOT AUTHORIZED ON THIS VIEWED PERIOD
Universe Expansion 20: BLOCKED
Paper: BLOCKED
Live: BLOCKED
```

The proposed configuration was still tested on the requested 30000-bar real-data extension. That result is recorded in [`PORTFOLIO_WFO_EXTENDED_30000.md`](PORTFOLIO_WFO_EXTENDED_30000.md).

## Verification

- Workflow run: `30913719737`
- Job: `92006464215`
- Artifact: `8894548471`
- Artifact SHA-256: `23448a87f1a5afd5f01466e43eeb4368f77136ab98a09e484c24d12ee6986f46`
- Static checks: PASS
- Tests: `38 passed`, one dependency deprecation warning
- Leakage tests: `7 passed`
