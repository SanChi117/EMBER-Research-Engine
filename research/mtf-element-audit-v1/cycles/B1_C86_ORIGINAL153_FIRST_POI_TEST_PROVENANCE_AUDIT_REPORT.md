# C86 — Original153 4H/1H first-valid POI source receipts and falsification

Date: 2026-10-28. Precondition: accepted C85/A155 journal 155/155,
SHA tip `330468624d81e7bcb61a6aae0a79c1bba692ce5830bd6e37a3a485c90acb2d30`.
Strict mode **PAPER ONLY / NOT_TRADE_READY**.

## Why this specific source audit matters

The original owner course *Entry by IMB & SNR* explicitly requires 4H POI
test/reaction before choosing the 1H trigger/VC fork, and a 1H POI test
before descending to the 15m branch. The *Rejection Block* lesson says
that the **first real test**, not subsequent pool-creating visits, matters.
The POI lesson relates POI strength to liquidity/FVG interactions.

A C46 parent index is only technical provenance, NOT author-valid 4H
first test; an earliest native3m wick overlapping a new 1H zone is only
physical price contact, NOT proof of the author's semantic first test;
a geometric 15m IMB or 5m SNR is not true Trigger/VC.

## Implemented source receipt contract

`d05/c86_original153_first_test_receipts.py` independently reconstructs
the C81 exact 153-case frozen queue from C73 original SHA and C72 original
Git blob, and writes one deterministic receipt for **every actual Binance
crypto source context** with:
- authenticated C46 parent *case index* while explicitly exposing that
  parent author valid-test timestamp and validity are **unknown**;
- 1H technical POI kind, creation time, original exact Decimal zone bounds;
- actual original native3m wick source ID, grid-aligned source bar open,
  completed native bar close, and physical visit episode classification;
- source 15m/5m availability clocks only where the frozen source provides them;
- separate immutable missing author-valid 4H/1H first test, RB source
  semantics, original positive/negative goldens, Trigger/VC requirements;
- no author entries, SL/TP, execution, orders, fills, trades, PnL.

Source-category counts:
- P0 12: selected 1H POI, raw3m contact, source15m + later source5m.
  Nine cases have one continuous physical visit; three have multiple
  (two cases have 2 episodes, one has 4). Their 1H first *valid* test
  remains UNKNOWN.
- P1 23: selected 1H POI with 3m raw touch, without a proven 15m chain.
- P2 71: opposing/ambiguous 1H parent branch with no eligible touch.
- P3 47: no selected new 1H POI. Important distinction: **23** have an
  original raw3m physical touch and **24** lack one; neither category
  authenticates a new parent POI nor supports an academic entry.

## Independent source and hostile counterchecks

Strict checks include a 64-hex original source namespace + 3m open,
exact +180,000 ms native3m close, closed-1h creation alignment, valid
Decimal 1H zone bounds, 15m/5m completion alignment, monotonic event
order, and group-specific parent existence. Negative tests reject
forged author labels, independent reviewer assertions, cross-branch
pseudo signals, fake entries/fills/trades, mutating C73/C72/C81 inputs,
future timestamps, malformed source ID, wrong zone and repeat visits.
Source (first physical wick) can never become (author-first-valid POI)
without separately authenticated positive and negative owner evidence.

Frozen evidence file:
`evidence/c86/C86_ORIGINAL153_4H_1H_FIRST_TEST_SOURCE_RECEIPTS.json`.
All 153 original records include their review gates. The archive was
captured from the independent original-source CI and **re-generated
byte-for-byte** after committing it to GitHub, without modification
of historical ZIP files or earlier C46–C85 evidence.

Independent source workflow: [GitHub Actions #40606898328](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40606898328)
SUCCESS, 61 tests × Python3.10/3.11/3.12.
Archived receipt re-check:
[GitHub Actions #40606960219](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40606960219)
SUCCESS, all three Python versions with frozen 153-receipt byte equality.

## Acceptance limitations / next phase

**0 author-positive/negative timestamp-certified crypto goldens, 0
author-semantic 4H/1H first-valid tests, 0 trades, 0 PnL.** Real
timestamp-labelled chart media for genuine 4H first test and exact
1H first valid POI test (with owner-supplied positive AND negative
cases) is still unavailable. These source receipts cannot be used as
trading signals, despite full deterministic data provenance.

Next C87: take author-proven test/trigger/VC evidence where it genuinely
exists, otherwise formally isolate compatible ADAPTED_HYPOTHESIS
assumptions for separate adversarial PAPER evaluation. Do not silently
substitute an arbitrary first 3m touch for the author's valid test.
Route B/C, V5/QFVG and SMOKE order routing remain isolated.
