# EMBER V3 — independent hypothesis / cross-symbol synchronization audit

**Date:** 2026-11-01. **Status:** DIAGNOSTIC_ONLY / NOT PORTFOLIO / NO VERIFIED EDGE.

- Base research dataset: 50 Binance USDT-M contracts, 17 archived CSV batches; V3 report and receipt SHAs in `research/mtf_v3_universe/REPORT.md`.
- New audit source: `scripts/audit_mtf_v3_independence.py` and `tests/test_audit_mtf_v3_independence.py`.
- Successful GitHub Actions run: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41308520655
- Evidence ZIP: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41308520655/artifacts/13084615902
- Added `independence_audit.json` to the complete evidence artifact, alongside the unchanged V3 price/transfer replay.

## Hypothesis and method

A large coin universe increases event observations, **not** statistical independence. Independently rescore the V3 original completed trade hypotheses without modifying the recognition, entries, stops, targets, taker filter or source 0.35% notional round-trip cost proxy.

For each execution variant separately:
1. Preserve every completed original simulated event.
2. Sort by known entry time; on a same-timestamp tie select order-block before swing before FVG, then known contact timestamp, then event ID. **Never sort by realized profit or exit.**
3. Keep at most one open hypothesis per `symbol`; discard same-symbol overlaps until previous exit. This is a diagnostic policy, not a promised live order manager.
4. Report event count, nominal mean, win rate, stop share, distinct entry days, equal-weight daily-mean nominal proxy, and UTC-day/hour clustering of symbols.

## Results from successful 50-contract CI replay

| Cohort | Original events | Original mean per notional | Nonoverlap events | Nonoverlap mean per notional | Discarded overlapping |
|---|---:|---:|---:|---:|---:|
| PRICE_ONLY | 450 | -0.574237% | 371 | -0.502709% | 79 (17.56%) |
| TAKER_CONFIRMED | 311 | -0.539099% | 261 | -0.480131% | 50 (16.08%) |

Taker-confirmed nonoverlap: 261 entries, 50 contracts, 55 distinct UTC entry days; 32.567% positive; 62.835% stop exits; nominal day-equal-weight mean -0.277082%. **42 of 55 days** had signals in at least 3 distinct contracts; maximum **15 distinct contracts** on a single UTC day; **21 UTC entry hours** had signals on 3+ contracts.

Price-only nonoverlap: 371 entries, 50 contracts, 57 distinct entry days; 31.806% positive; 63.881% stop exits; nominal day-equal-weight mean -0.276004%. **50 of 57 days** had 3+ active contract signals; max **20 contracts** on one day; **30 entry hours** had 3+ distinct symbols.

## Interpretation

The original 450/311 event counts were inflated by **79/50 same-contract overlapping trade hypotheses**, respectively. The 261 taker-confirmed nonoverlapping events still have negative average nominal outcome **after the unchanged hypothetical 0.35% round-trip cost**. In fact, even before that assumed cost the 311-event original mean was -0.189099% per notional. This sample shows no net edge, and overlapping signals cannot explain it away.

Cross-asset signals concentrate in common calendar times, so multiplying contract count cannot be treated as increasing effective independent sample size linearly. Day-equal-weight statistics are not a portfolio return.

## Strict caveats

- `independence_audit.json` is calculated on the original simulated **unfinanced** V3 ledger, not on actual Binance fills.
- The test does not calculate shared wallet margin, risk parity, equity compounded return, trade size, leverage, funding, mark-price liquidation, observed spread or quote depth.
- No pre-registered OOS regime, no live or autonomous paper evidence, no native source-fidelity proof. **ZERO VERIFIED FUTURES CANDIDATES.**
- Results are based on one short 2026 sample. The original negative evidence remains unchanged.
- The original SMOKE native 4H POI scoring, inactive-dedup and lifecycle parity remains unresolved; `source_receipt` is not `native_parity`.

## Next research priorities (do not tune to this sample)

1. Compare each SMOKE source-native 4H POI snapshot vs V3 at identical as-of UTC closes, reporting missing/extra levels by family, activity and source dedup ordering.
2. Separate impulse failure vs sustained control using **preknown** features, freeze definitions on a development period; confirm incremental predictive value on untouched regimes and symbols.
3. If source fidelity and OOS pass, test 15m execution, actual funding/mark, liquidation and shared-capital risk. Until then, **no strategy promotion or integration to PAPER**.

The locked `RESEARCH_MANDATE_LOCKED.md` is unchanged: V3 is a separate auxiliary mechanism study, not an original-source Futures strategy verification or change to primary EMBER objective.
