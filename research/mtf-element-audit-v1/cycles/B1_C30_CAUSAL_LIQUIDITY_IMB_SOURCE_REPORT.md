# EMBER B1 / C30 — causal known-before-raid 1H liquidity and classic IMB interaction

**Status:** source-only experiment; admission requires pinned complete original 45 USD-M ZIP, independent second reproduction, Python matrix, A100 and 100/100 independent SHA verification. PAPER ONLY / NOT_TRADE_READY. Never creates or sends orders or trading signals.

## Academic source map

1. [ліквидність.txt](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): swing/fractal liquidity must be source-known after right-hand candle; a strict wick cross is not equality, and first touch/sweep is distinguished from reusing already crossed level. Prior 1H BSL/SSL research pivots remain C20's narrow strict one-left/one-right observer, **not** author-selected liquidity.
2. [Fair Value Gap / Imbalance.txt](https://drive.google.com/file/d/1ajvG1554qQ-5AnIV8HVmoDflkNRrU-LN/view): classic IMB is 3-candle wick-gap, third full bar closes before the zone exists. First subsequent POI test distinguished from repeat tests. The author also discusses BPR/iFVG which are NOT detected by this C30 classic-only instrument.
3. [Rejection Block.txt](https://drive.google.com/file/d/1bFjOPZdiHEAdM_QN58EWBDpgsYx_p0nT/view): opposite candle pair is insufficient; qualifying liquidity raid or IMB test needs a **wick-only** interaction and correct context; illustrated first/second pair candle raids. Exact authored wick boundaries/qualifying IMB and body-side confirmation not independently attested by native source.
4. [Support And Resistance .txt](https://drive.google.com/file/d/1OOyS7C8T8H4FdD47dXsnx7y3u33lNG7m/view): SNR differs from RB; liquidity/FVG context, fully closed subsequent candle relative to authored level, and first true test, with possible body interaction. No-raid/no-FVG Mitigation Block is weaker and not SNR volume confirmation.
5. [Context & TDA.txt](https://drive.google.com/file/d/14KFoZCWoJEue_WmlOyXg0sBZoXsozP2M/view): IMB, RB, BSL/SSL and SNR are distinct candidate first trouble areas. Course does not supply a complete numeric rank/tie-break of all simultaneously presented candidates.
6. [Entry by BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): author 1H raid → 3m/5m BOS and 1H liquidity/sessional targets; **selected 3m BOS pivot goldens, author FTA ranking, timezone/DST and SL buffer still unresolved**.

## New standalone causal module

`d05/c30_causal_wick_liquidity_imb.py` reuses original native3m→1H source from frozen C21/C26–C29 (20 SHA-attested original USD-M 3m bars per 1H). It computes per source-confirmed C20 strict 1+1 pivot the **first strict 1H wick or body crossing after the pivot right candle confirmation**. Equality-only is never a sweep. It also evaluates strictly pre-existing C28 classic three-hour IMB, with **correct-direction wick-only approach**: bullish IMB approached from above, bearish IMB from below, plus body interaction, exact boundary touch, first vs prior touch.

Each source-only opposing closed 1H pair (C29) is then linked to these **known-at source interactions** on **its first versus second closed hour**, maintaining hour source row ID and earlier pivot/IMB first original source row ID; all events identified as technical observational necessary conditions, **not** author-selected RB/SNR. First strict level cross / first IMB wick test must be explicitly distinguishable from previous level crossing or previous zone touch. Unknown selected pivot, IMB mitigation, authored SNR level and first FTA remain UNKNOWN.

For each older C26 research technical single case, only pairs whose **second full hour close** is known at/before the research 3m BOS **BAR START** are allowed. Never import later 3m close or future bars into prior eligibility. Full pair-interaction chain is SHA256 digested and selected sample rows are illustrative only; repeated pair-to-case relationships are not trades.

## Falsification and acceptance

The module includes **25 source/adversarial negative controls** in `d05/test_c30_causal_wick_liquidity_imb.py`: BSL/SSL strict wick vs body vs equality/no-cross, wrong pivot kind, both gap directions with wrong-side rejection, equality-only test, gap third hour not yet closed, 1H pivot right confirmation not yet known, first versus repeat wick, one/other candle provenance, forged author trade and malformed original SHA row, physically truncated causal source equivalence.

Original full-source program `tests/probe_c30_original_causal_wick_imb.py` re-downloads the same 45 SHA-checked Binance USD-M ZIP, verifies 76,800 closed 3m rows and 15,360 exact native15m Decimal OHLCV equalities, 3,840 native 1H bars, all source-only 539 C21 parent edges / 165 C26 singleton research cases and frozen 1,989 C29 opposite candle pairs. Per-case JSON receipt `evidence/c30/C30_ORIGINAL_PRIOR_WICK_IMB_CAUSAL_SOURCE.json`, pinned only if 25 controls and replay succeed. Independent Python 3.10/3.11/3.12 controls and complete JSON rereplay required; then append A100 six-evidence SHA and independently verify 100/100 entries. Never rewrite A001–A099 or C26–C29 immutable source receipts.

**Critical guardrail:** even if C30 observes source-known strict wick on the correct earlier liquidity or gap, it is **only a necessary geometric prerequisite**, not proof of author-approved 1H RB or SNR. This release does NOT choose FTA, TP, entry, SL, RR, calculate win rate or generate trades. All output `NOT_TRADE_READY`, zero author-positive BOS/RB/SNR goldens.
