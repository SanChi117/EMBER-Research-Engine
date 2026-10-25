# C76 — original60ZIP FVG 1H parent technical source verification

**2026-10-26; PAPER ONLY / NOT_TRADE_READY.** Start from C75/A145 SHA
`693bf5425ea68b76a06643ddb887243f091b399c7017a20c93634da1c9591cea`.

## Done — full original-source validation

Five crypto symbols BCH, BTC, ETH, SOL, XRP on Binance USD-M Sept 1–Oct 2 2026.
Full **60 original ZIP fresh** in [initial C76 workflow](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40238301069).
All original 3m (76,800), 5m (46,080), 15m (15,360), native1d (160);
3m→15m and 5m→15m exact Decimal OHLCV parity 15,360/15,360 each.
Original source ZIP and CSV SHA pinned with original frozen C08/C21/C73
proofs and original .CHECKSUM from the **same Binance host** (NOT third-party
digital authentication). Technical C75 FVG detector rescans all source data.

**ADAPTED_HYPOTHESIS geometric results — NOT signal count:**

| Period | Raw closed three-candle wick FVG |
|---|---:|
| Native3m | 18,762 |
| Native5m | 10,338 |
| Native15m | 3,048 |

153 original C73 parent 4H contexts, source-only classifications:
47 no proposed new 1H POI, 71 new 1H POI without source first touch,
29 without pre-touch parent-contained same-side 15m FVG, 5 with contained
15m FVG in parent source RB/SNR, 1 partial parent-zone overlap.
Six technically same-clock 15m FVG and first original 15m event are
not owner-verified 15m Trigger or VC. No source nested IMB promoted.

## Tests and falsification

Module `d05/c76_original_crypto_fvg_1h_parent_semantic_audit.py` enforces
parent POI RB/SNR/IMB source distinction, strict event clocks, parent nesting,
adversarial flag rejection, no 5m VC by association. Tests on Python
3.10/3.11/3.12 each pass the full negative suite under original C76 workflow.
Initial C76 proof and archive receipts are preserved byte-for-byte in
`evidence/c76/C76_FRESH_ORIGINAL60ZIP_ADAPTED_FVG_PARENT_REPLAY.json`;
static independent audit:
`tests/probe_c76_pinned_original60zip_static_review.py`.

Independent second fresh archive download and byte-comparison is in
`.github/workflows/mtf-c76-independent-second-original60zip.yml`.
Record actual CI result; do not claim duplicate success until green.

## Limits: academic and trade readiness

C76 rescans **real original crypto candles** and verifies parent source
linkage against the pinned 153 C73 cases; it does *not* independently
re-run the full earlier C73 153-case algorithm. External three-candle
FVG geometry is hypothesis and is not author-certified Volume Confirmation,
valid first test, eligible Trigger, IDM, Raid→BOS, StrongHL, stop/FTA/TP,
fills, winrate or return. There are still no timestamped authored Binance
positive/negative crypto goldens. **Zero orders, fills, trades, PnL.**

## Next C77

Validate genuine parent-sourced RB/SNR/IMB candidate eligibility and
source first/revisit versus closure chronology on all potential cases,
separate strict author text rules from adapted source patterns, never
force a route or construct a live order; OOS PAPER only after proof gates.


## Final observed independent CI — no inference from pending results

- **First genuine complete 60ZIP replay:** [GitHub Actions #40238301069](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40238301069), **SUCCESS**, with all 60 original archives freshly fetched and source reconciled.
- **Second independent genuine complete 60ZIP replay:** [GitHub Actions #40238604771](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40238604771), **SUCCESS**. Python `cmp` checks the entire new 40,791-byte C76 JSON evidence against freshly independently recreated C76 result: **BYTE EQUAL**.
- **Full source proof SHA256:** `ca5717073a30dd14c5ec830b065e4d4f67764bd9de856411d86a55e154270de7`. Both complete runs reproduced this exact file digest.
- **Adversarial independent matrix:** 40 tests × Python 3.10/3.11/3.12 (120 test executions) **SUCCESS**, all C76 proof grades remain SOURCE_TECHNICAL / ADAPTED_HYPOTHESIS, no trading decisions.
- **Same-clock 15m geometric FVG vs frozen first 15m event:** 6 source cases. Those six are **NOT** course author's independently confirmed 15m Trigger/VC.
- Frozen original C73 303,327-byte, 153-context source SHA remains `c79892079f00952030b778985b53c2cc11bd2e05bf1ea70555d4385bd7963f6b`; the entire C73 153-case algorithm was not independently rerun in C76, while the original 60 ZIP price sources were.
