# B1/C17 — original C08 32-day 1D/4H geometric IMB and reaction diagnostics

**Scope:** 2026-09-01—2026-10-02 UTC, Binance USD-M Futures, BTC/ETH/SOL/XRP/BCH; research-only, never trading authorization.

## Source → algorithm → code

- Original course v05 frozen `src/course_primitives_v05.py`: `confirmed_imb` permits the classic 3-CLOSED-wick-bar LONG gap (third low > first high), SHORT gap (third high < first low), and does not gate on second-bar candle color. **This is a geometric IMB diagnostic, not an automatically author-validated POI/StrongHL or route.**
- The separately frozen author StrongHL qualitative corpus C14 requires liquidity/inefficiency contact and **later** VC POI OR BOS with suitable timeframe; it also records the still-unresolved SNR resistance candle-order contradiction. Its examples are qualitative figures, not timestamped Binance USD-M author labels.
- Original 30 USD-M ZIPs: C08 native 15m monthly Sep2026 and daily Oct1/2; independently native 1D from identical 32 days; all 30 verified against previously frozen C08 HTTPS+same-host checksum+ZIP/CSV SHA and original C08 receipts. 15,360 original 15m → 3,840 derived 1h; 960 derived closed 4h; 160 native 1D matched exactly. C16 receipt Git blob `bdaa008ce719254507ea95231cdc630bfa85cd67`.
- New `d05/c17_htf_imb_reaction_diagnostics.py`: read-only strict closed 1D/4H source, dimensional/time-order/SHA metadata guard and as-of cut. Detect 3-bar geometric gap **only at the close of third candle**. Analyze subsequent price-zone overlap as contact, first versus repeated, and subsequent bar close relative to zone (above / inside / below). **None** of the closing locations is auto-labelled author rejection, bounce, invalidation, entry, target, or profitability. No nearest/first IMB parent linkage is invented.
- New `d05/test_c17_htf_imb_reaction_diagnostics.py`: 31 synthetic engineering positive/negative tests (never asserted to be original Futures or independent author examples). Includes lookahead, incomplete/overlapping TF, fake SHA/lineage, modified OHLC, caller-forged APPROVED/READY, ambiguous overlapping gaps, first/repeat contact, actual counterexamples without contact, adverse close and 1D/4H separation.
- New `tests/probe_c17_original_htf_geometry.py` reloads the 30 independent original C08 archives, compares native 1D with derived 15m through frozen C16, performs full prefix and independent cutoff-prefix replay, asserts prefix invariance and matches new pinned C17 result receipt.
- New `evidence/c17/C17_ORIGINAL_C08_1D_4H_CANDIDATE_RESULT.json`, Git blob `d7fffbe4712bc5a188b2e9065527b86c2987846f`: source-derived quantitative outcomes pinned without author labelling.

## Independently observed geometric candidates (not trades)

| USD-M Futures | 1D 3-bar IMB | 1D later contact | 4H 3-bar IMB | 4H later contact |
|---|---:|---:|---:|---:|
| BTCUSDT | 4 | 4 | 30 | 25 |
| ETHUSDT | 7 | 6 | 31 | 26 |
| SOLUSDT | 5 | 4 | 31 | 26 |
| XRPUSDT | 4 | 4 | 29 | 26 |
| BCHUSDT | 6 | 4 | 32 | 29 |
| **Total** | **26** | **22** | **153** | **132** |

Of the 179 geometric IMB candidates, 154 have at least one subsequently observed closed-bar zone overlap; 25 did not. These are candidate counts, not author-validated POI, independent trade setups, nor statistical performance claims. All outputs remain `AUTHOR_GOLDEN_SOURCE_UNAVAILABLE` and `NOT_TRADE_READY`.

## Independent CI and recorded counterchecks

- [Initial C17 workflow 38941888523](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38941888523): **FAIL**, pre-test pin guard typo for C14 frozen SHA (old source unchanged).
- [Diagnostic pin workflow 38942009952](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38942009952): **FAIL**, same incorrect C14 expected literal; actual Git SHA printed.
- [Explicit Python pin diagnostic 38942119196](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38942119196): **FAIL**, precisely identified one-character copy error in expected C14 SHA. Corrected workflow string, NOT frozen academic file.
- [Actual 30-original-archive source run 38942172431](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38942172431): **SUCCESS**, 29 original course-v05 + 216 C10–C17 regressions (**245 PASS**), 30 original C08 USD-M native archive ZIP/CSV SHA, 160 native 1D exact matches, 960 derived closed 4H, full and earlier cutoff as-of agreement. Run artifact includes source logs and per-symbol quantitative record.
- Pinned-receipt repeat CI: [38942501259](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38942501259). This repeat must be SUCCESS independently before an append-only DONE action is written.

## Limitations / hypothesis counterchecks

1. The academic figures show *possible price reactions at levels*, not dated Binance USD-M candles annotated and approved by the original author. Both an observed contact and a subsequent adverse close remain observations only. The C14 positive concept is **not** a true Futures golden, and C14 negative is a **text-derived** counterexample, not an independently labelled market no-signal.
2. The C17 candidate detector inherits C16 32-day C08 raw-source validation; C17 result alone is not cryptographic independent issuer identity. Binance Vision .CHECKSUM is same-host, not a publisher-separated signature.
3. v05's original three-candle wick-gap geometry is reused rather than modified. No assumption has been added requiring gap fill, close reaction, automatic author StrongHL, first parent, POI inheritance, SNR candle sequence, volume threshold, BOS condition or trade trigger.
4. The 32-day route **does not** independently authenticate 32-day original 5m; 4H/1H remain derived from original 15m and are never called native 4H/1H. No five-level automated entry mechanism or ROI/PnL validation follows from this cycle.
5. Precise source-author labelled 1D/4H POI and StrongHL scenarios, full parent→child attribution, downstream 5m source alignment, execution and FTA/SL rules remain unfinished.

**Next research cycle:** document source-specific classification of 1D/4H level candidates and parent/child 1H/15m as-of associations, retain all ambiguous parents, obtain independent author-golden annotated Futures examples rather than fabricating certification. PAPER ONLY.
