# C74 — static first-valid-POI-test and Route A Trigger/VC author-golden intake

Date: 2026-10-26. Starting point C73/A143 SHA `73dff2c95292c6f8f6dea5e6eb2bf56492d9537941fe8df2755d3cafb4e6b6e2`.

## Independently read authoritative course lessons
- POI.txt: POI support/resistance, especially those involving SSL/BSL or FVG. Reaction possibility is not a labelled crypto first valid test.
- 2. Entry by IMB & SNR.txt: parent 4H POI needs test; valid new 1H POI created via 1H VC after parent reaction; its test precedes 15m analysis; **actual** 15m SSL/BSL/eligible IMB Trigger -> 5m VC [IMB,SNR]; absent such Trigger -> direct 15m VC [IMB,SNR]. IMB nested inside larger IMB cannot be independently presumed eligible.
- Rejection Block.txt: first POI test matters; two-candle RB must raid liquidity or interact with IMB, wick-only interaction. Two native3m contacts or a raw wick do not establish author-rejected/revalidated POI by themselves.
- Strong High & Low.txt: cause liquidity/inefficiency and subsequent confirmed POI VC or BOS (same or lower TF); a price extremum alone is not a structural stop.
- Entry by IDM.txt: Route B independent, not forced through Route A 5m VC.

## New, isolated C74 contract
- `d05/c74_author_academic_golden_failclosed.py` exact-key author-golden intake; symbol, venue, route/TF, 4H parent, 1H POI, first native3m source touch, episodes/revisit, first 15m and 5m original event timestamps, separate Trigger/VC labels, StrongHL cause/confirmation, archived ZIP/CSV SHA, frozen C73 source SHA, lesson IDs, attestation, and as-of.
- Reject unknown fields, forged author claims, invalid SHA format/anchor, parent/TF mismatch, future-derived sequence, fabricated repeat visit, orphan 5m, Route B/C crossover.
- All possible accepted observations remain `SOURCE_ONLY_CANDIDATE` or `UNRESOLVED`; no user-provided author label can upgrade trust.
- `d05/test_c74_author_academic_golden_failclosed.py` adversarial tests use explicitly synthetic timestamps, not Binance goldens.
- `tests/probe_c74_static_source_anchor.py` independently checks frozen C73 source digest, state totals and absence of real trading.
- `evidence/c74/C74_STATIC_AUTHOR_GOLDEN_GAP_WITNESS.json` records exact boundaries.

## Epistemic boundary and next gate
The previous C73 data run contained 60 original ZIPs, 153 source 4H contexts: 47 + 71 + 23 + 9 + 3. This C74 step does **not** freshly download 60 ZIPs or independently certify price rows beyond the pinned frozen SHA; no author-labelled crypto `symbol+TF+UTC+ZIP-SHA+bar-ID` positive and negative goldens exist in the read material. Therefore SOURCE-only and unresolved branch classifications are not trades. Genuine author test/Trigger/VC/StrongHL labels, verified structural SL/FTA/TP and OOS PAPER remain blocked.

**PAPER ONLY / NOT_TRADE_READY / orders=fills=trades=0**. Previous C46–C73 frozen artifacts untouched.
