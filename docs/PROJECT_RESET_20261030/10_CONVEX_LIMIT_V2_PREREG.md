# RESET-07 v2 — new preregistration before execution

The owner's newly uploaded RESET-07 (1) adds section 5.1 after RESET-07 first-run results; original rules forbid a second run on the same branch. This is explicitly a NEW hypothesis and a NEW branch, based on PR #16 but separately reviewable.

**Unspecified by owner:** actual limit-order price. Deterministic implementer convention: submit a pullback limit at previously completed 20-day breakout HIGH for LONG / LOW for SHORT. This is **not** explicitly chosen by owner. All results must be labeled ASSUMPTION_LIMIT_LEVEL and remain review-required even if CI is green.

The seven-day TTL is exact UTC wall clock (42 full 4h bars), not `random_fill_probability=36%`. Touch of historical OHLC high/low is a necessary condition for a limit fill, **not** sufficient proof of a queue fill. Same-candle order of fill/stop/TP cannot be established from 4h OHLC; apply pessimistic stop-first, annotate ambiguous bars. Keep separate `EXPIRED_UNFILLED` events. Do not change old PR #16 PnL, old parameters, old SHA files, or trading systems. 36% from prior archive conflates closed results with fills.

This experiment should not reinterpret v1 result or certify owner mechanism before independent parity review.
