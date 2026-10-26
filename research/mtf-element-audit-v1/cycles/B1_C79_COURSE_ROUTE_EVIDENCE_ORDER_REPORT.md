# C79 — original Route A academic next-evidence gate

Date: 2026-10-26. Starting checkpoint C78/A148; frozen C46–C78 remain unchanged.

## Course logic (from original Google Drive Entry by IMB & SNR; Rejection Block)

A 4H POI needs an actual **valid first test** before interpreting 1H Trigger
(SSL raid, BSL raid, or eligible IMB). With a proven 1H Trigger, the
next proof is 15m VC [IMB,SNR]. Without it, 1H VC [RB,SNR,IMB]
is needed to form a new 1H POI. At a 4H liquidity raid, 1H
Trigger is absent by the lesson's rule: await 1H VC instead.

A new 1H POI must arise in the context of a 4H reaction, then itself
receive a genuine first valid POI test. With an eligible 15m Trigger,
the following proof is 5m VC [IMB,SNR]; with **no** 15m Trigger,
direct 15m VC [IMB,SNR] is expected. Do not force a 5m event into
the direct 15m VC branch.

The course specifically says an inner 1H IMB should not be considered
when parent 4H POI is IMB. Extension of the same veto to a 15m IMB
inside a 1H IMB is **not explicitly proven from the cited text**:
it is marked `1H_IMB_NESTED_ADAPTED_HYPOTHESIS` and routed to additional
author review, never used to authorize a trade.

## Implementation and falsification

`d05/c79_course_next_evidence_map.py` is an isolated **hypothetical**
course event-order matrix. It does not inspect candles or accept a
user-supplied 'verified' label as an authenticated golden.
`HYPOTHETICAL_AUTHOR_VALID` in tests means **scenario input only**.
Every output remains `author_authenticated=False`,
`entry_allowed=False`, `orders=fills=trades=()`,
`NOT_TRADE_READY`.

`d05/test_c79_course_next_evidence_map.py` covers missing first test,
4H raids, non-nested and nested IMB distinctions, Trigger and no-Trigger
routing, unrelated routes, spoofed labels and nontrading invariants.

**CI:** [GitHub Actions #40359161852](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/40359161852),
32 tests on each of Python 3.10 / 3.11 / 3.12: **SUCCESS**.
A prior C79 test run failed while the new 4H-test requirement was being
introduced; subsequent corrected run is green and documented, not concealed.

## Restrictions and next step

There remain **zero authenticated timestamped author-labelled Binance
goldens** for valid POI first test, 15m Trigger, 15m VC, 5m VC, StrongHL,
SL/FTA/TP. This cycle is an academic transition specification, NOT
independent profitability evidence, real execution, or a candidate trade.
Historical C78 source statistics stay frozen; B IDM and C Raid-BOS and
V5/QFVG unchanged. PAPER ONLY / NOT_TRADE_READY.

Next cycle: create an auditable **manual golden intake validation workflow**
that records exact author case source and timestamps when they exist,
failing closed otherwise, and audit older CI (< C55).
