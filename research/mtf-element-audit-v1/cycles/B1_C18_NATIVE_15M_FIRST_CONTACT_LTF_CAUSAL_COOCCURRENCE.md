# B1/C18 — независимая 1D/4H → native 15m → 1h/15m диагностика

**Date:** 2026-10-16. **Scope:** source-backed read-only engineering, PAPER ONLY, never live orders, no author-approved trade entry.

## Source → code

- Original author [Strong High & Low](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view): StrongHL contact with liquidity or inefficiency, later VC **POI OR BOS**, POI may be same/lower TF. This does not identify which particular later IMB belongs to a particular parent.
- Original author [Imbalance](https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view): classic three-candle unfilled wick-gap; no candle-color gate. First test matters, later contacts can form liquidity. There are also distinct BPR/iFVG concepts, **not implemented** by this candidate detector. Illustrations depict possible price reactions, not guaranteed outcomes.
- Original author [POI](https://drive.google.com/file/d/1C5sAzdOON4iMxLVdrBD5XMXUj3bVcZ-R/view): support and resistance can offer a reaction and stronger examples interact with liquidity/FVG. No source-exact automatic nearest-child-parent rule or author-labelled Binance USD-M Futures OHLCV case available.
- Frozen `course-v05` `confirmed_imb`, C14 13 source-concept controls and C16/C17 SHA proofs reused without modifications.
- C08 original native monthly Sep2026 and daily Oct1–2 15m and 1d, five symbols; 30 ZIP + SHA, HTTPS and same-host .CHECKSUM; 15,360 native 15m, 3,840 derived closed 1h and 160 independent native 1d equalities. C16 original source receipt Git blob `bdaa008ce719254507ea95231cdc630bfa85cd67` and C17 result Git blob `d7fffbe4712bc5a188b2e9065527b86c2987846f`.

## Implementation

1. `d05/c18_native_15m_child_witness_graph.py`: independently recalculates closed 1h/4h and 1d parity from original 15m witness objects, refuses mutated native source-row IDs, ZIP SHA, prices, missing/overlapping bars and author-status claims. Calls unchanged C17 diagnostic on the strict as-of prefix.
2. First lower-TF price overlap with a 1d or 4h geometric IMB zone is recorded **only** from a native **closed 15m** bar whose start occurs after the HTF level formation; later overlaps counted separately. It is **not** certified as the author's true first POI test.
3. Detect every fully closed classic 3-bar 15m/1h IMB *geometry* on the native lineage. A possible child relationship is logged only when **all three child source bars** begin after the observed first contact bar CLOSES. Time-order co-occurrence is not enough for VC/BOS causality. No nearest candidate, first-in-list, directional exclusion, TTL/expiry, auto-parent choice or trade.
4. `d05/test_c18_native_15m_child_witness_graph.py`: **25 synthetic** positive/adversarial cases covering causal ordering, no-contact, future suffix/as-of, original 15m source identity, 1h/4h aggregation SHA/price corruption, author approval forgery, multiple contacts and no 5m identity claim.
5. `tests/probe_c18_original_ltf_witness_graph.py`: independently re-download 30 original C08 ZIP/.CHECKSUM and archived source receipt match, reproduce graph; separately replay early prefix via independent C16 and full C16 as-of and demand identical graph; compare result to pinned C18 Git receipt.
6. `evidence/c18/C18_ORIGINAL_C08_NATIVE15M_LTF_GRAPH_RECEIPT.json`: stored exact per-coin source replay counts pinned to Git blob `9178e96ec348414621bf58866a3c8001c0bee90b`.

## Measured 32-day results (observations only)

| Symbol | HTF 1d+4h geometric parents | Later native15m contact | 15m geometric child nodes | 1h geometric child nodes | Temporal co-occurrence edges | LTF child nodes with 2+ candidate HTF parents |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 34 | 29 | 634 | 123 | 8,444 | 680 |
| ETHUSDT | 38 | 32 | 640 | 126 | 10,838 | 684 |
| SOLUSDT | 36 | 30 | 579 | 126 | 9,830 | 652 |
| XRPUSDT | 33 | 30 | 576 | 132 | 9,938 | 623 |
| BCHUSDT | 38 | 33 | 619 | 139 | 11,577 | 689 |
| **TOTAL** | **179** | **154** | **3,048** | **646** | **50,627** | **3,328** |

Note: 50,627 edges deliberately allow **all later** matches without an author-supported TTL or parent selection; they are predominantly not meaningful enough to trade. 3,328 child nodes share multiple candidate HTF parents; this illustrates why the temporal linkage alone cannot identify author source attribution. No independently author-labelled Futures target, VC, StrongHL or approved trade has been discovered.

## Independent CI and self-criticism

- [C18 initial CI 38945892312](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38945892312) FAILED one synthetic assertion: a test for literal "5M" matched inside "15M". Original source, geometric code and 240 other tests were untouched; corrected test string to explicit "ORIGINAL_5M".
- [C18 source replay 38945991444](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38945991444) SUCCESS: 29 v05 + 241 C10–C18 = **270 tests PASS**, 30 original C08 source ZIP/checksum/CSV proof, 160 native daily equality, 32-day 15m/1h/4h causal graph, strict earlier as-of invariance.
- [Malformed new workflow 38946303375](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38946303375) and [38946373841](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38946373841): FAILED workflow parsing because test-assertion string replacement unintentionally appended YAML suffix and broke the regex. Fixed the NEW workflow YAML and preserved all failures.
- [C18 independently pinned repeat CI 38946424095](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38946424095) SUCCESS: validates exact Git blob for frozen C14/C16/C17 and new C18, repeats 270 tests, network re-download of 30 original native archives, exact per-coin pinned graph, 0 READY.

## Boundaries / unresolved

- Original educational diagrams do not contain independent author-labelled Binance USD-M timestamp/OHLCV goldens. **All** candidate output remains `AUTHOR_GOLDEN_SOURCE_UNAVAILABLE`; no approval despite engineering tests passing.
- Temporal correlation after a contact is NOT proof of linked author VC. BOS path is not built here, and first native15m price-zone overlap does NOT prove structural true first POI test. No retrospective selected nearest IMB.
- 1h/4h are derived from validated native 15m; not separately native ZIP; full original 5m history for all 32 days has **not** been revalidated. Therefore no complete 1d→4h→1h→15m→5m academic execution route.
- Five-symbol 32-day replay and candidate count do not demonstrate profitability, win rate, fills, entries, stops, FTA or exchange API reliability. PAPER ONLY.

**Next B1/C19:** source-verified 1h/15m liquidity-contact and candidate BOS-or-POI branch, inspect edge ambiguity and separate meaningful geometric relation from unbounded later time co-occurrence; add 32-day original 5m source only when separately SHA-validated; never auto-approve without author market labels.
