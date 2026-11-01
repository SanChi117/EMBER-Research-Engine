# RESET-06 — v1.1 owner's evidence and limitations
Source: owner-provided RESET-06 specification dated 2026-11-02.

## Registration

VIRTUAL_MECH_920 revision 1.1 explicitly registers max leverage 3,
max notional 2760 USDT, initial equity 920, kill 736, and maximum
drawdown 0.20. The pre-existing 4% / 36.8 USDT record remains the
**absolute historical ceiling**, never the starting active budget.

Risk ladder starts at 2% = 18.4 USDT, then 3%, then 4% only after
verified gates and separately authorized upgrades. The original
registry SHA witnesses remain intact. A new STRATEGY_AMENDED event
pins previous blob SHA ade27bdb9264e31d82b709276fbc46be0ca4f433
and v1.1 SHA 89a8ddffcdc9e29cb3f37f81090d78f0e51c2240.
A fourth receipt registers the blocked CONVEX_RUNNER_001 skeleton.

Remaining blockers: OWNER_ENTRY_EXIT_RULES_NOT_PINNED and
RISK_DENIALS_NOT_YET_PERSISTED_TO_EXECUTABILITY. PAPER and LIVE
remain disabled, including after an otherwise positive gate report.

## Budget modules

research.platform.ramp_policy is pure Python; it does not connect to
risk_guard, paper_execution, exchange APIs, schedulers, or a live account.

Default regime NEUTRAL: at most one trade per UTC day. CHOP: 0.
WINDOW_OPEN: 3/day only with external owner weekly review VERIFIED.
The boolean review flag is NOT a cryptographic signature or a trusted
authorization if supplied by an untrusted process; detector and
authenticated journal adapters are not built yet.

Ratchet: risk = (920 × ladder fraction) +
0.08 × max(0, equity_current - 1104).
At equity 1200 and stage 2%, it is 25.08 USDT; at 1104 it is 18.4.
The bonus cannot alter kill 736, DD 20%, max nominal 2760, max 3x.
An optional remaining-series budget further caps this proposal.
Stop and gap risk require conservative separate execution testing.

CONVEX_RUNNER_001: BLOCKED_UNTIL_BACKTEST 2024–2026, NOT a trading
instruction or signal. Experimental 1–2% tickets and leverage <=15,
structural mandatory stop for long 1.5–2 ATR under swing,
TP only removed AFTER breakeven stop, no CHOP, fixed series cap.
No order execution code.

## Gate report

Command: python -m research.platform.gate_report
Optional: --journal-root PATH --expected-trades-head PINNED_SHA256
The report SHA-verifies the trades JSONL journal and uses only
TRADE_CLOSED events with unique trade IDs, Decimal-string PnL and
equity_after, timestamps and explicit strategy_id. Mixed strategy
ledgers FAIL CLOSED to avoid attributing portfolio equity incorrectly.

Four gates: >=100 closed trades, >=30 distinct UTC dates with closed
trades, PF strictly >1.2 (net gross positive / gross negative), and
closed-trade max DD <=0.20. No losses means PF undefined and the gate
stays IN_PROGRESS. Empty ledger: IN_PROGRESS and unlock false.
Deterministic text and JSON; no fake data or cached counts.

Limitation: closed-trade DD does NOT represent mark-to-market intratrade
drawdown, gap-through-stop, funding, liquidation or external flows;
therefore a numerical PASS cannot alone establish safe scaling.
Outstanding PAPER registration blockers keep LADDER_STEP_UNLOCK false.
LIVE_ALLOWED always false. CI runners are ephemeral, not a durable
production journal; no active PAPER planner is rewired.

## Acceptance

CI 3.10/3.11/3.12; existing registry SHA witness and Git history
verifier; owner tests for 2% 1104 and 1200 ratchet, cap, CHOP,
WINDOW_OPEN evidence, PF 1.1999/1.2 FAIL, 29 days, 99 trades,
empty journal, two identical deterministic reports. No TS or Telegram.

After review: owner verdict; separately integrate risk denials to the
executability stream, authentic regime journal verification, and
intratrade DD. Collector and R030 remain deferred.
