# B1/C27 — separate academic 1H target families: original Futures source replay

**Current review status:** independent source proof [39081484753](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39081484753) **SUCCESS**: all 45 original ZIP, complete pinned JSON equality, 20 tests across Python 3.10/3.11/3.12. Author BOS/FTA/TP/SL not approved. A097 97/97 SHA journal verification is still required before C27 [x]. PAPER ONLY / NOT_TRADE_READY. This report never retroactively revises original C26.

## Academic primary-source separation

- [4. Entry By BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): raid 1H -> BOS 3m/5m, first 1H liquidity and illustrated **1H EQL** TP, preferred previous-session high/low, skip on conflicting FTA/poor RR, stop beyond swept liquidity, no unambiguously specified Binance futures trade.
- [ликвидность.txt](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): a swing BSL/SSL is a strict 1+1 three-candle pivot, known after close of right candle; EQH/EQL require **at least two swing points**, not one. A complete near-equality numeric tolerance is not specified.
- [Strong High & Low.txt](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view): structural StrongHL needs contact and validation through POI or BOS; this is not an isolated 1H fractal detector or a numeric stop padding rule.

**Critical semantic correction to C26:** C26's 137 formerly swept / 28 untouched nearest **single opposing 1H historical fractal** are reproducible technical geometric observations, **not** counts of author-selected TP, EQL target, or real trades. C27 preserves the C26 receipt byte-for-byte and splits the target families.

## C27 formal contract

1. Source input: existing C21 native3m, C26 original research-only singleton (539 parent edges -> 165 surviving), original source 1H hours via 20 native 3m closed bars per hour. `known_ms <= break_start_ms` for any candidate, with breaking candle excluded from historical checks.
2. `EXACT_1H_EQL_WITNESS` / `EXACT_1H_EQH_WITNESS`: strictly equal `Decimal` price of **two distinct already confirmed** same-side 1H fractals, on the corresponding research-side price. A PRICE-EXACT pair witnesses a subset of price equality, **not** author EQ proximity tolerance, not author eligibility or a TP. Record separate first and second original hourly row IDs and known-at times. Counterexample: `110` versus `110.01` never implicitly merged.
3. Calendar candidate families separate: prior **full local calendar day** high and low, and prior **local 09–17** high and low, repeated individually across `UTC`, `Europe/Kyiv`, `Europe/London`. These are **hypothetical** calendars, not the author's session. Require the full set of already closed 1H bars, 23/24/25 for local DST day or 8 for 09–17. Missing source yields `UNKNOWN_SOURCE_INCOMPLETE`, not fabricated extremes. Record zone, local date, closed-bar coverage, price, earliest preknown event, original 1H row and strict historical wick/body/equality state.
4. Known intervening FTA obstacles and author's RR threshold remain `AUTHOR_FTA_RULE_UNKNOWN`. No single target family may be promoted over another because it appears to offer a better RR. No inferred Forex pip mapping, tick fill or actual author session timezone.
5. This is a taxonomy and source-replay study, not a complete EQH/EQL or session target detector. No real/paper position opens, no expectancy, win-rate or balance calculations.

## First original-market result (pinned; independent recheck required)

Original full 45 ZIP and C26 predecessor replay produced 165 source singleton observations. **65/165** contained at least one precise equal-price, same-side, preknown 1H fractal pair, with **178 total pair relationships**. These are *not* 65 validated EQL/EQH trade targets, because near-equality tolerance, directional author selection and freshness semantics are still unverified. Across hypothetical UTC/Kyiv/London calendar scenarios, **163/165** had at least one disagreement in previous-day or 09–17 date/price family; **62** of 1,980 expected scenario-family windows had insufficient prior 1H source coverage. Every output remains NOT_TRADE_READY; C26's separately established 137 crossed earliest single 1H-fractal targets remain unchanged.

Breakdown of **exact price pair research relationships** from first source replay: BCHUSDT 18/45 singletons (44 calendar-disagreeing), BTCUSDT 1/30 (30), ETHUSDT 11/23 (22), SOLUSDT 68/30 (30), XRPUSDT 80/37 (37). Many pairs may share a pivot or research case. They cannot be interpreted as opportunities, performance or independent positions.

A fast diagnostic GitHub Actions [39081162038](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39081162038) initially showed **three failed synthetic tests**: mismatched toy 3m known-at time units, missing explicit incomplete-calendar status, and a non-effective forged SHA choice. All three were corrected (no historical receipts changed), and rerun [39081236947](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39081236947) passed all 20. A subsequent full source run [39081225289](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39081225289) replayed all 45 ZIP and 20 controls successfully but failed on non-fast-forward `git push` because another GitHub job advanced the same branch concurrently; the runner logged that root cause and retained the negative diagnostic. The original source receipt was separately pinned in the branch (Git blob `d434ae830858fecf5e45cf7ef8ff7db1e627d489`). The separate **independent** [39081484753](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39081484753) full JSON, 45 original ZIP and Python matrix CI passed; verified independent witness Git blob `1869d771bd18ad8534a76cfb03522928fd71dae8`. Remaining acceptance gate is append-only A097 with independent 97/97 SHA+source rerun; no author trade.

## Adversarial tests

There are **20 controls** in `d05/test_c27_target_families_source.py`: one-pivot-not-EQ, exact two-pivot witness, nonexact tolerance cannot be invented, future second confirmation, wrong side, SHORT EQL, previously wick-crossed EQ price, invalid/nonfinite input, full day and 09–17 not collapsed, missing calendar coverage, timezone scenario difference, 23/25-hour DST transitions, fabricated timezone, invalid ordering, zero academic approvals, physical prefix truncation equivalence, false READY, original 3m row tamper, original ZIP SHA tamper. Explicit no-lookahead.

## Independent evidence gate

- Original ZIP replay program: `tests/probe_c27_original_1h_target_families.py`; output `evidence/c27/C27_ORIGINAL_1H_EQ_SESSION_SOURCE.json`.
- First source CI: `.github/workflows/mtf-b1-c27-original-target-families.yml`; re-download 45 original USD-M ZIP and compare C26 per-symbol counts, 76,800 original native3m bars, 15,360 exact native15m Decimal OHLCV equalities. Require 165 source-only C26 cases and an explicitly false author-approval state.
- Second immutable pinned-source CI and Python 3.10/3.11/3.12 tests are **SUCCESS** in run 39081484753. A097 append-only six-source SHA journal and independent 97/97 verification remain REQUIRED before accepting C27. Any failure is documented; no retroactive mutation of original C21–C26 or A001–A096.

## Academic dependency

No author-labelled positive and negative Binance USD-M 1H->3m BOS trade examples with exact chosen pivot and selected TP family; no confirmed EQ price tolerance, author timezone/DST, prior-session cutoff, FTA zones or RR threshold, SL buffer. Therefore B1 macro [~], Routes [ ], `NOT_TRADE_READY`. C27 cannot choose the correct executable TP from original 1H EQL illustration alone.
