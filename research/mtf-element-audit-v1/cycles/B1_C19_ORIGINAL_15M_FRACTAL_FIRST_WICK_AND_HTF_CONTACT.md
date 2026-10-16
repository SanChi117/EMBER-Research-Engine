# B1/C19 — original native 15m fractal liquidity / first clean wick breach vs HTF contact

Date: 2026-10-16. Independent source observations only. **PAPER ONLY; not a signal engine, no order placement**.

## Academic primary texts and what they actually say

1. **Liquidity / Fractals / Raid** ([direct Google Drive text](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view)): a fractal high has two neighboring candles with strictly lower highs; similarly fractal low neighbors have higher lows. BSL and SSL are such fractal levels. A raid is a liquidity removal and reaction; a **clean raid uses a wick**, and its raid formation must also be fractal. A body breach may display a reaction but is not a clean wick raid. This is the basis of geometric 15m observations; the source does not label any replayed Binance USD-M bars.
2. **StrongHL** ([direct source](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view)): contact with liquidity or inefficiency followed by **VC POI OR BOS** as movement confirmation, on same/lower timeframe. A geometrically observed raid alone does not fulfill this full condition.
3. **4. Entry by BOS** ([direct source](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view)): common intraday execution **1H Raid → 3m/5m BOS**, with additional fresh liquidity, wick raid, BOS spatial relation, session, TP, FTA, SL and timing requirements. Therefore **C19 never treats a 15m close/break as a source-certified BOS**; complete native original 3m/5m 32-day Futures archive not established. Pips/session concepts in that teaching context are not numerically imported into crypto.
4. Frozen D05/C14 qualitative controls remain separate from replayed raw USD-M Futures. Original screens are examples of price reactions, not author-annotated timestamp/OHLCV golden cases.

## Implementation + counterfactual checks

- `d05/c19_fractal_wick_raid_source_witness.py`: validates caller through C16→C18 native 15m/1d/1h/4h source checks, constructs confirmed strict three-bar 15m fractal pivots with original row SHA witness, and examines **first** price level breach after the pivot is known. Classifies body breach, wick breach whose raid candle is not a fractal, pending next 15m close, accepted geometric fractal wick breach, or no breach. A possible geometric raid is only known **after the bar following the wick breach closes**, not from future intra-bar data.
- Join is now **exact first HTF zone-contact native-15m candle == clean first wick fractal-breach candle**. No unbounded later raid joins allowed, no closest candidate or directional winner selected. Multiple fractal pivots in one HTF contact are kept. Potential IMB geometric gaps on lower TF are listed only after the raid confirmation is known, but **their mere later existence does not confer VC/POI or causal parenthood**.
- `d05/test_c19_fractal_wick_raid_source_witness.py`: 21 synthetic positive/adversarial tests (3-bar pivot timing, body-vs-wick, first breach only, post-raid fractal closing time, same-candle association, synthetic source/aggregation corruption, future as-of and suffix invariance, refusal of author READY/BOS).
- `tests/probe_c19_original_fractal_raid_contacts.py`: independently fetches frozen C08 raw 30 15m/1d ZIP and .CHECKSUM, rechecks 15,360 native 15m candles and 160 native 1d matches; compares early as-of full stream to replayed independent source prefix and immutable receipt. Frozen C08/C14/C16/C17/C18 objects unchanged.
- `evidence/c19/C19_ORIGINAL_NATIVE15M_FRACTAL_WICK_RESULT.json`: exact per-symbol source-backed counts, 0 approvals / 0 trades.

## Exact 32-day original Binance USD-M Futures counts, five symbols

| Coin | Native closed fractal BSL + SSL | First clean fractal wick geometry | First strict body breach (not clean) | First wick breach, no fractal confirmation | Exact first HTF-zone-contact / clean wick co-observation | Different HTF parents co-observed |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1401 | 461 | 655 | 233 | 26 | 12 |
| ETHUSDT | 1419 | 503 | 653 | 218 | 22 | 11 |
| SOLUSDT | 1375 | 483 | 583 | 249 | 17 | 10 |
| XRPUSDT | 1343 | 441 | 603 | 252 | 25 | 9 |
| BCHUSDT | 1436 | 462 | 654 | 260 | 19 | 11 |
| **Total** | **6974** | **2350** | **3148** | **1212** | **109** | **53** |

Additional 264 original-source closed fractal pivot levels were **not breached** by the end of the 32-day window; 0 had an unconfirmed first wick remaining in this exact end-of-window sample. 109 co-observation *links* involve **104 distinct fractal pivot levels** across instruments (some can share an HTF contact candle); 53 unique HTF parents have ≥1 such link. These totals are not independent trades. All 109 have later geometric candidate IMB on 15m/1h when looking to the end of the source window, but this is **unbounded future availability**, NOT verified causal reaction, direction, author VC or profitable model. The additional lower-TF pattern counts are not promoted.

## Verification and retained negative evidence

- First workflow [38948199390](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38948199390) FAILED 11 tests due to invalid **synthetic** fixture attempting to assign index 48 of a 48-bar Python list; no original source or detector code modified. Fixture was extended before assignment.
- Independent 30-ZIP source-run [38948302715](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38948302715) SUCCESS: 29 original v05 + 262 C10-C19 regression tests (**291 PASS**), full original C08 source proof, strict as-of suffix invariance.
- Frozen C19 quantitative result pinned in Git blob `dbbd11a15cc5442644fd6c4339615fa1fa37362f`. A new workflow update unintentionally corrupted its OWN regex/YAML when replacing text with a string containing dollar sign; fixed and retained failure; no historical data/source changes.
- Final independent pinned receipt CI: see GitHub Actions `mtf-b1-c19-fractal-native15m-source.yml` and A085 journal proof once accepted.

## Scientific negative result / limitations

- The detection finds observational price geometry, **not** market maker behaviour, dominance, author StrongHL, author POI, BOS, or validated liquidity-induced entries.
- C19 15m fractal raid is a diagnostic lower-TF example; **not** a replacement for the author's typical 1H raid→3m/5m BOS execution route.
- No indiscriminate nearest-child attribution; no retrospective live order, profits, returns or win-rate.
- 32-day C08 case is too short for long-run statistics and has no independent author-labelled Futures goldens. Original 3m/5m 32-day source parity remains unverified. READINESS: `AUTHOR_GOLDEN_SOURCE_UNAVAILABLE`, `NOT_TRADE_READY`.
- Next research C20: investigate original 1H raid plus separately source-attested 5m/3m BOS and author-defined spatial/temporal rules. Do not assume crypto pips, session, or thresholds from external educational context.

This limited **C19 source-witness diagnostic** can be DONE independently, while B1 overall remains PARTIAL (29/40 macro), author-qualified route remains blocked.
