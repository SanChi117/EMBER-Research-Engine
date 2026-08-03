# EMBER Out-of-Sample Validation: 4 New Alts

Дата выполнения: 2026-08-03 UTC  
GitHub Actions run: `30842493927`  
Artifact: `8867628034`  
Artifact SHA-256: `c9b34bcf5fb3dd8478bfc4e10c9b2a1fd4125b5494a22709700b80833ec6c5ad`

## Predeclared protocol

- Symbols: `PEPEUSDT, FETUSDT, WIFUSDT, SUIUSDT`
- Interval: `15m`
- Bars per symbol: `15000` (approximately 156.24 days)
- Profile: `high-vol-block`
- `blocked_volatility_regimes=("high_vol",)`
- `min_confidence=43`
- `min_rr=1.8`
- WFO: `4` folds, `30`-day lookback, `3`-bar embargo
- Verdict rule fixed before execution:
  - `PASS`: at least 3 of 4 symbols have positive return and PF > 1.5
  - `PARTIAL`: exactly 2 of 4
  - `FAIL`: 0 or 1 of 4
- No symbol was removed or replaced because of poor performance.

All four datasets contained exactly `15000` rows. There were no timestamp gaps, duplicate timestamps or zero-volume bars.

## Backtest results

| Symbol | Trades | Return | PF | Max DD | Win rate | WFO |
|---|---:|---:|---:|---:|---:|---|
| PEPEUSDT | 2 | -0.7258% | 0.4354 | 1.2731% | 50.00% | FAIL |
| FETUSDT | 5 | +5.0364% | 4.7226 | 1.3356% | 80.00% | PASS_WITH_WARNING |
| WIFUSDT | 7 | +2.5706% | 1.7209 | 2.3623% | 57.14% | FAIL |
| SUIUSDT | 8 | +5.8600% | 2.9848 | 2.8903% | 75.00% | FAIL |

Aggregate:

```text
Total trades: 22
Average return: +3.1853%
Average drawdown: 1.9653%
Worst symbol drawdown: 2.8903%
Qualifying symbols: 3/4
Protocol verdict: PASS
```

## Walk-forward results

| Symbol | WFO status | Stability | Avg return | Avg PF | Worst DD | Zero-trade folds |
|---|---|---:|---:|---:|---:|---:|
| PEPEUSDT | FAIL | 25% | -0.1797% | `inf`* | 1.2731% | 2 |
| FETUSDT | PASS_WITH_WARNING | 75% | +1.5830% | `inf`* | 0.0000% | 1 |
| WIFUSDT | FAIL | 0% | -0.5231% | 0.1629 | 2.3623% | 2 |
| SUIUSDT | FAIL | 50% | +1.1017% | `inf`* | 0.0000% | 2 |

`*` `inf` means that the positive WFO folds had no losing completed trades. It is not proof of unlimited edge and is especially unstable with one or two trades.

Only FETUSDT formally passed WFO, and it contained one zero-trade fold. PEPE, WIF and SUI failed the predeclared WFO gate.

### WFO fold trade counts

| Symbol | Fold 1 | Fold 2 | Fold 3 | Fold 4 |
|---|---:|---:|---:|---:|
| PEPEUSDT | 1 | 0 | 1 | 0 |
| FETUSDT | 1 | 0 | 1 | 2 |
| WIFUSDT | 1 | 0 | 3 | 0 |
| SUIUSDT | 0 | 0 | 1 | 2 |

The WFO evidence is sparse: each symbol produced only 2-8 full-period trades and 0-4 test-fold trades.

## Regime and liquidity diagnostics

| Symbol | High vol | Trend | Range | Low vol | Neutral bias | Mean quote volume / 15m | Gaps |
|---|---:|---:|---:|---:|---:|---:|---:|
| PEPEUSDT | 0.11% | 50.62% | 48.41% | 0.86% | 59.65% | 291,342 USDT | 0 |
| FETUSDT | 1.82% | 52.90% | 44.85% | 0.43% | 47.20% | 140,542 USDT | 0 |
| WIFUSDT | 1.29% | 47.66% | 49.77% | 1.29% | 48.48% | 41,908 USDT | 0 |
| SUIUSDT | 1.18% | 54.26% | 42.63% | 1.93% | 58.44% | 376,501 USDT | 0 |

The poor PEPE result cannot be attributed to missing data or low quoted liquidity. WIF had the lowest liquidity proxy, but still met the full-period return/PF criterion. High-volatility bars were rare in all four datasets, so the `high-vol-block` filter did not remove a large share of the sample.

## Reject diagnostics

| Symbol | Neutral context | Direction reject | Regime reject | No setup | Candidate passed | Executed |
|---|---:|---:|---:|---:|---:|---:|
| PEPEUSDT | 8,912 | 2,636 | 16 | 3,364 | 5 | 2 |
| FETUSDT | 7,051 | 3,249 | 208 | 4,409 | 12 | 5 |
| WIFUSDT | 7,243 | 3,169 | 192 | 4,303 | 15 | 7 |
| SUIUSDT | 8,731 | 2,385 | 176 | 3,630 | 13 | 8 |

The main bottlenecks remained neutral HTF context and absence of a valid setup. There was no evidence that confidence, RR or cost gates were responsible for the low trade count in this run.

## Comparison with core 6

| Universe | Qualifying symbols | Trades | Average return | Worst DD | WFO evidence |
|---|---:|---:|---:|---:|---|
| Core 6, high-vol-block | 6/6 | 73 | +8.7512% | 2.4397% | Portfolio WFO PASS_WITH_WARNING |
| OOS 4, high-vol-block | 3/4 | 22 | +3.1853% | 2.8903% | 1/4 symbol WFO PASS_WITH_WARNING |

The cold-universe test reduced average return and trade density compared with the core six, but the predeclared cross-symbol criterion still passed without parameter changes or symbol removal.

## Verdict and research decision

**Protocol verdict: PASS — 3 of 4 symbols had positive return and PF > 1.5.**

This is evidence against a complete core-six selection-bias failure. It is not yet strong proof of broad robustness because:

1. the total sample contains only 22 completed trades;
2. PEPE failed the full-period criterion;
3. only FET passed per-symbol WFO;
4. seven of sixteen WFO test folds had zero trades;
5. the positive WFO folds often contained only one trade.

Therefore the correct project status is:

```text
Cross-symbol OOS criterion: PASS
Statistical confidence: LOW / INSUFFICIENT
Research universe expansion: ALLOWED with fixed predeclared rules
Paper comparison: ALLOWED in research-only mode
Live gate: BLOCKED
```

No strategy parameter is changed by this result. `high-vol-block` remains a research candidate; baseline remains the control. Live trading remains blocked until the architecture's paper requirements are satisfied.
