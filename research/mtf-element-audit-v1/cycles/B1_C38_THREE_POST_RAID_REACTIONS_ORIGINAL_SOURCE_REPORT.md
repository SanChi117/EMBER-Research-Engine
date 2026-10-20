# EMBER B1/C38 — 3 ADAPTED Reaction Hypotheses × 4 Native BOS Timelines

**Date:** 2026-10-20. Source: original 45 Binance USD-M Futures ZIP (September–October 2026). **Research-only reaction source predicates**, not an instructor-certified 2023 reaction or a trading/backtest engine. **PAPER ONLY · NOT_TRADE_READY**.

## What is new vs C37

C37 independently discovers the first 3m close-crossing of four adapted pivot-selection strategies after a confirmed 1H wick liquidity raid. C38 now inserts a distinct, explicitly **ADAPTED reaction observer** between the **fully closed 1H confirming bar** and the start of that variant's native 3m BOS-break candle.

All three reaction rules only read *already closed original native3m candles*, never the opening/current/future BOS bar. Every first reaction witness is identified by its original SHA-linked native3m row ID, `known_ms <= BOS_BAR_START_MS`. Candidate is a **historical source observation only**: no execution, PnL, FTA, stops, author approval or paper order.

| Reaction hypothesis | Exact technical adaptation | Limitation |
|---|---|---|
| `POST_CONFIRM_DIRECTIONAL_BODY_V1` | At least one source 3m candle CLOSED with body moving toward the intended BOS side (SHORT: close<open; LONG: close>open), after full 1H raid confirmation, before BOS-bar start. | Very permissive technical flag, not proof of original instructor's reaction |
| `POST_CONFIRM_TWO_PROGRESSIVE_CLOSES_V1` | Three successive contiguous source 3m closes with two strict increments toward the intended BOS side; last witness bar closed before BOS-bar start. | Not equal to author structure shift or liquidity raid response |
| `POST_CONFIRM_HALF_SWEEP_DISPLACEMENT_V1` | At least one 3m close beyond the **last already-closed 1H confirmation price** by 0.5× absolute difference between raided liquidity level and wick extreme, toward BOS side. | The **0.5** factor is an ADAPTED test hypothesis, not calibrated and not academically endorsed |

This restricted time window may **exclude genuine reaction inside the raid hour** already known at the subsequent confirmation time, and therefore cannot be treated as the original author definition or a final filter without independent testing.

## First exact original SHA 45 ZIP source result — before final independent acceptance

Source file `evidence/c38/C38_ORIGINAL_FOUR_BOS_BY_THREE_REACTION_MATRIX.json` (full original 4×3 per-case witness, Git blob `a69d69de29d4b52a9ee68ccdf0dbcb20222a6440`). Per *research parent context*, number of source-verifiable pre-BOS reactions:

| BOS selection | BOS research events | Directional body | Two progressive closes | Half-wick excursion from confirmed 1H close |
|---|---:|---:|---:|---:|
| LATEST (C21 research baseline) | **539** | **416** | **258** | **152** |
| EARLIEST | **462** | **402** | **323** | **246** |
| DEEP RAID SIDE | **412** | **351** | **270** | **236** |
| NEAREST RAID SIDE | **511** | **415** | **304** | **215** |

Each numerator counts a **true source-level prior-time predicate within the corresponding C37 BOS research context**, not unique market entries or profitable trades. Denominators are the C37 independent event totals, not cases from an author 2023 BackTest. A single original 3m source reaction bar or breakout candle may support multiple different raid contexts and adapted variants. **Correlated occurrences are NOT independent trade samples.**

Source provenance: 45 original SHA-checksummed USD-M ZIP (BCH, BTC, ETH, SOL, XRP; original3m total 76,800, original15m Decimal exact source equalities 15,360), 12 research combinations. The prior full original C37 source Git blob remains immutable `e4b702e8c6cdc34f1c2475df73ef44ae1631fe56`. Reconstructed truncated source `as_of` and physically truncated source prove equal reaction observations at cut; SHA-linked native3m source bars, no future/right-neighbor leakage.

## Code, negative and adversarial tests

- `d05/c38_adapted_post_raid_reaction.py`: typed `ReactionWitness`, `ReactionRouteReview`, `ReactionReview`; `_eligible_window` excludes break bar, verifies native original3m SHA/close price for the selected C37 event and confirms reaction only after full 1h confirmation.
- `d05/test_c38_adapted_post_raid_reaction.py`: **27 source/adversarial controls** including immediate BOS with no earlier reaction, delayed BOS with three distinct witnesses, false READY/trade tags, forged original3m source row hash or BOS price, future break bar, source prefix/suffix, invalid 1h/3m time placement and total 4×3 structure.
- [First 27 negative controls CI 39493969372](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39493969372) PASS.
- [First original ZIP 4×3 CI 39494276152](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39494276152) SUCCESS, full source recomputation and frozen receipt.
- [Independent C38 45 original USD-M ZIP, all 12 source combinations full per-case JSON equality and 27 source guards × Python 3.10/3.11/3.12 CI 39494609819](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39494609819) **SUCCESS across all five jobs**. Source witness `evidence/c38/C38_INDEPENDENT_RUN_WITNESS.json` frozen Git blob `d50a567ace14bf187c14f931a2b0309ee4ba852f`: 45 original source ZIP, 76,800 native3m and 15,360 original15m Decimal source equality, old A107 107/107 source chain, 27 negative cases per Python version, 12 route combinations. C38 narrow source acceptance still requires A108 append and independent 108/108 SHA; no goldens or trading.

## What is NOT built

**No actual long/short position, stop, FTA, volatility/swing-dependent reaction mechanism trained on positive labels, paper trading, author 2023 BOS, tick execution, spread/slippage, funding, return metric, out-of-sample performance or objective optimization.** These 3 predicate rates cannot rank expected trading PnL. The same 2026 chart windows are already inspected; future true holdout needs new untouched periods and complete entry/exit simulation.

**Next C39:** FTA historical source geometry/ranking variations should be modularized, distinguish academic literal from adapted choice, and integrated after causal Raid→Reaction→BOS. Only then implement paper event fills with explicit first-tick vs bar-close difference, fee/slippage and structured stop. No real trading.

Baseline immutable C37 A107 canonical SHA `b325185b98640c5af48b8bc084ae50034c8e35d44d4a761833702e350f139045`, old original C33 SHA and C37 original ZIP source retained. C38 author reaction/BOS goldens 0, order count 0, trade count 0.
