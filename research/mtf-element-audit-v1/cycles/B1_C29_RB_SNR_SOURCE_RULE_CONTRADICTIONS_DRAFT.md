# B1 / C29 — RB vs SNR academic first-FTA distinction: scoped handoff (WIP)

**Current status:** only academic primary-source review and plan [~], no code, no original ZIP receipt, no A099, no route trades. C28 and prior source evidence SHA immutably pinned. PAPER ONLY / NOT_TRADE_READY. This file intentionally does not make new untested implementation assertions.

## Source-derived rules and non-equivalences

### Rejection Block (RB)
Primary: [3. Rejection Block.txt](https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view)
- The course describes visually opposed consecutive Buy+Sell or Sell+Buy candles showing a change in dominance.
- **Mandatory** liquidity raid or IMB interaction; the raid/IMB interaction must be with the candle **wick**, not a candle body.
- The RB is marked specifically by wick ranges and may be the originating VC, support POI, or future problem zone. First true POI test is privileged; later tests generate liquidity.
- Source illustrates raid in the first vs second candle and an IMB-based variant that also requires a body settlement across the relevant IMB. The exact diagram-dependent selected wick boundaries and test timing require positive/negative source images or authoritative author goldens. **Two opposite candle colors by themselves are NOT an RB.**

### Support and Resistance (SNR)
Primary: [5. Support And Resistance .txt](https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view)
- Course describes a two-candle Buy+Sell / Sell+Buy stage plus liquidity SSL raid or FVG test and a **subsequent fully formed candle closing beyond** the previous zone as part of its sequence.
- SNR raid/IMB test may involve **candle body**, unlike the wick-only RB requirement. A later first true test of the SNR zone can produce reaction.
- A no-liquidity/no-FVG Mitigation Block (MB) is a weaker interest zone and NOT the same volume confirmation as strong SNR.
- The source explicitly warns that RB and SNR have different formation and liquidity-removal logic; do not merge them as generic OB, 2-color reversal, or one 'reaction' proxy.
- Exact price edge for first/second candle and body-close determination needs source image alignment and author timestamped positives/negatives.

### First Trouble Area vs entry routes
Primary: [Context & TDA](https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view) and [IMB lesson](https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view)
- FTA candidates include IMB, RB, SNR and fractal liquidity with different underlying timeframes and mitigation/test states.
- Course's first POI test principle does not specify a single numeric expiry, tick tolerance or rank among simultaneous candidates.
- Validating *a* 1H RB/SNR source family does not select the instructor's intended first obstacle/TP for the 1H raid→3m BOS route without authoritative priority and selected BOS pivot.
- C28 confirmed 646 purely classic 1H IMB from 45 original ZIP; this price geometry MUST NOT be repackaged as RB, SNR or real first FTA.

## Proposed C29 source→rule negative controls (NOT YET IMPLEMENTED)

1. Two opposite-color candles with **no** liquidity/IMB interaction MUST NOT become a valid course RB.
2. RB body-only crossing without a qualifying wick interaction MUST NOT pass wick-only condition.
3. SNR must not be confirmed before its **subsequent** fully closed candle; strict `known_ms` and native 1H provenance.
4. RB vs SNR selected first POI test must not be backdated to zone formation candle.
5. Do not apply the SNR wick/body acceptance rule to RB or allow MB to masquerade as SNR volume confirmation.
6. Competing IMB/RB/SNR/fractal overlays stay **unranked** without author priorities and first-test semantics.
7. Source images and author model examples must validate the actual candle range selected as zone; a synthetic color pattern is insufficient.
8. Explicitly differentiate retrospective C26 research break-close price from a pre-BOS known price; no lookahead from later 3m close.
9. Falsify forged READY, price source SHA tamper, future right hour, missing original source, and branch-history mutation.
10. If strict source provenance or academic labels absent, return `NEEDS_AUTHOR_RB_SNR_LABELS` or `FTA_AUTHOR_PRIORITY_UNKNOWN` and **zero** approved trades.

## C29 execution gate

First identify whether original 1H source chart examples and labeled positive/negative cases genuinely support full RB and SNR semantics. Only then build an isolated native-hour technical observer with explicit partial/UNKNOWN states, negative falsification, original 45 ZIP replay, full pinned JSON and independent matrix CI, append-only A099 and independent 99/99 SHA. C28 C27 C26 documents, fixed receipts, SMOKE and all earlier ledger events stay unchanged.

**Macro:** 29/40 accepted major control points, B1 partial, Routes/E/G/H blocked, PAPER ONLY.
