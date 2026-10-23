# B1/C43 — ADAPTED per-candidate potential FTA re-ranking, original 45 Binance USD-M source

**Date:** 2026-10-23. **Scope:** historical original OHLC source eligibility research only. **PAPER ONLY / NOT_TRADE_READY**, zero orders/trades and no PnL.

## Frozen previous source

Accepted C42/A112 journal SHA `5b258f6c17f2505f6dfb36c31f6b225b9e701b3b94c4d382b89938dbf8140d7f`, independent [CI 39991697125](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39991697125) success 112/112. Frozen original C41 36-route source Git blob `ac3bb2b2babafdb28af71c4cbaa2b53fce03b06c`; C42 full original 3-policy source blob `bddf315c58a906fe58546512bc416c24bd1ce95f`. **No prior source or academic core mutation**.

C42 tested three restrictions **only on the candidate previously selected by C39**, and intentionally did not search other source candidates if that obstacle failed. C43 is independent **ADAPTED** research for precisely that missing alternate-source question.

## C43 source-only implementation

`d05/c43_adapted_per_candidate_fta_rerank.py` works with ALL **C39 source-preknown** original 1H directional fractals and original 1H 3-candle classic IMB zones, not only original chosen C39 level. It uses a native original3m segment-tree first-hit index: interval bounds **only prune**, exact source OHLC **leaf** tests first touch and first strict fractal sweep or entire IMB traversal. Each source candidate is independently tied to the exact tuple of 1H source kind, source level, fully known timestamp and first/last original native3m row IDs; 1H known must be no later than original BOS break candle START. Every inspection window begins after obstacle source-known and ends before BOS bar START. Final family choice is made **no earlier than BOS candle CLOSE** (C39 distances are calculated from retrospective break CLOSE, not a tradable entry at candle START).

For each independent C37 original BOS stream (four variants), the algorithm deduplicates identical source tuples, separately classifies touch/sweep for each candidate, ranks by each of the three original C39 **adapted priority hypotheses**, then selects the first candidate passing each of the three C42 gate hypotheses (ANY_SOURCE, EXCLUDE_STRICT_CROSS, REQUIRE_NO_PRIOR_OBSERVED_TOUCH). An unavailable alternative remains `None`, never an invented target. Re-selection never changes academic/frozen C39, C40, C41, C42 outputs. Original C39 first candidate and original C40 source touch classification/raw3m ID are cross-checked exactly for every event. Final 36 routes overlay the same 4 BOS × 3 Reaction × 3 FTA variants, yielding intentionally correlated context copies, not independent executions.

28 adversarial synthetic tests `d05/test_c43_adapted_per_candidate_fta_rerank.py`: first-hit index including exact/swept boundary, IMB full wick traversal in one original candle, empty windows, altered raw3m grid, alternative source ranked after rejected first, three family priority routes, policy nesting, no early BOS decision or orders, unchanged previous source selected. First [CI 39999023895](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39999023895) FAIL: *test-only* wrong attribute name `hypothesis_id` instead of `eligibility_policy_id`. Fixed in commit `b04827c079ff06427faaf88f9489939bbe549f5c`, independent [CI 39999123685](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39999123685) PASS all **28/28 × Python 3.10/3.11/3.12**.

## Original Binance USD-M 45ZIP complete-source experiment and evidence correction

`tests/probe_c43_original_per_candidate_fta_45zip.py` re-reads **45** original signed-by-receipt/checksum Binance USD-M ZIP, **76,800** original closed 3m and **15,360** exact Decimal native15m, checks independently source-cut historical prefix and compares every original BOS/raid/reaction/source-level selection with C41 and original gate decisions with C42.

First [CI 39999367449](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39999367449): source download, checks, **168,774,218 byte complete canonical C43 JSON PASS**, but **CI overall FAIL** at push, because documentation update had advanced remote branch (non-fast-forward). An unsplit 168MB output also exceeds normal GitHub per-file limits, therefore **no first-result GitHub blob was accepted** from that job. Error not hidden.

`tools/partition_c43_source_result.py` solves it without deleting any source contexts: splits into **five complete original-market JSON files** BCHUSDT/BTCUSDT/ETHUSDT/SOLUSDT/XRPUSDT, with SHA256 and exact bytes of each file plus overall **canonical original aggregate JSON SHA256**. Reassembles every market record in source order and checks the exact original 168,774,218-byte aggregate byte SHA256 `92956d189574d2a13a0f8aa3f5aa9f99ddd4cc33dcb128c3fbb2b9b8fc30e791`. Unlike summary-only evidence, no row/event/choice is omitted. Git push rebase against current remote is mandatory to avoid stale-branch update.

Corrected [CI 39999848721](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39999848721) **SUCCESS**, five market parts committed, manifest `evidence/c43/C43_ORIGINAL_45ZIP_MANIFEST.json` pinned immutable Git blob `c1db4afec81cb240f981e6e0ef2211044c75e372`. Their SHA-256 are:
- BCHUSDT `333b0f85d43450322e30d6243dfa0c98437e6bf7b21c8f60283c036b61ec03fc` — 29,670,463 bytes
- BTCUSDT `0274a2599b619708e0710eb92ad670120a90120d60845fe83d62f081aa18307f` — 28,900,657 bytes
- ETHUSDT `a0c232a71455037a4d16b6929722a55fffb537ac049a78b2f4e4d109e3333808` — 37,483,297 bytes
- SOLUSDT `580d75d78494e6eb3c3d9441f1729bbb7c47c18a2b52f0b0ec7efa8ad8c4ea2c` — 29,983,909 bytes
- XRPUSDT `c8472e0cd7e96530caa4b239030364f73852c7d2e79f1de0c56813f736a354ef` — 30,824,179 bytes

**Second independent replay** [CI 40000294077](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40000294077): three versions of Python independently 112/112 predecessor evidence and 28 C43 source negatives PASS; separately rebuild full 45ZIP from original downloads and compare **all 5 entire file bytes, manifest bytes, and the reconstructed 168MB aggregate hash**. **At the time this report was created, full independent 45ZIP source check was still running; do not mark accepted until result verified.**

## What counts actually mean: a useful falsification

Across 36 research-route overlays, **17,316 correlated parent contexts** (not separate setups). Previous C42 only selected first original C39 candidate: ANY 17,289; EXCLUDE_PRIOR_SWEEP 4,422; REQUIRE_NO_PRIOR_TOUCH 2,433. With C43 search of ALL eligible source candidates, the first full original replay showed:
- ANY_PREKNOWN: **17,289 selected**, **0 substitutions**; C39 unfiltered regression oracle unchanged
- EXCLUDE_PRIOR_STRICT_SWEEP: **17,262 selected**; **12,840 alternative substitutions** after original selected failed
- REQUIRE_NO_PRIOR_TOUCH: **17,262 selected**; **14,829 alternative substitutions** after original selected failed

**Interpretation:** this apparent almost-universal availability makes C43 *less* suitable as a trade-quality filter, not more! Within 32 original days many historical 1H levels exist in the distance; the nearest family-appropriate untouched obstacle could be very old or far away. This was the exact falsification C43 needed. **Do NOT treat 17,262 as signals or trades**. There are 27 correlated context copies without preknown source candidate. No checked academic author FTA golden or actual FTA reach exists. The same BOS parent can appear across routes and comparisons.

## Final gate / next cycle

C43 **[~] until independently successful original rerun AND A113 append-once and separate 113/113 SHA/evidence CI**. Evidence intended: source/test/original 45ZIP probe/sharding tool, five complete source-market original JSON blobs, SHA manifest, independently observed witness, this report (12 files total).

If C43 source-only acceptance passes, next **C44** should test separately **age of source, distance from BOS reference, source-type/family hierarchy, mitigation/reaction context, upper bounds or 4H/1D POI** with parameter-free baseline and explicit independent source hypotheses. No threshold retrofitting on reused 2026-09/10 source; use genuine unused holdout for performance. Academic Route A/B/C, structural SL/TP, fees/slippage/funding and entry execution remain unimplemented; `PAPER ONLY / NOT_TRADE_READY`. Coarse milestone count 29/40 remains unchanged.
