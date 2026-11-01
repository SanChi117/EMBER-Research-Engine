# RESET-05 / Part 3 — immutable strategy pre-registration (2026-11-01)

**Status:** owner review after CI. Stage 1 risk and stage 2 JSONL ledger are
already accepted/merged. This commit implements **part 3 only**: immutable
research registry. No economic backtest, active signals, PAPER deployment,
live keys, order adapter, collector, TS, AppDeploy or planner modifications.

## Explicit owner order / invariant

Risk scaffold first -> RESET-05 (append-only ledger, immutable registry,
Python-only golden fixtures, then machine gates) -> public USDT-M flow
collector -> future data QA and detection. **Data before detector, gates
before money.** R030 continuous extract/close remains queued after RESET-05.

## Two immutable registrations

### H1_CARRY_001
- Status: ECONOMIC_NOT_TESTED (not a profitable strategy).
- Research hypothesis: spot/perpetual funding-basis carry with Binance
  USDT-M Futures leg; spot is **only a possible hedged research leg**.
- Source pin: research/platform/basis_source.py,
  Git blob SHA b5b86e54ea4ff657d9e7ff351dfd49b102548cbf.
- 2025 source-feasibility receipt: docs/PROJECT_RESET_20261030/
  05_H1_SOURCE_FEASIBILITY_RU.md; not a two-leg fill/borrow/fee proof.
- Risk, execution model and economics not registered/validated: PAPER and
  LIVE blocked.

### VIRTUAL_MECH_920
- Registry-only snapshot from owner's supplied RESET-05 spec SHA256
  249bd6aa09f1eb8cb7f5115b6ad925aa8f709a79e38adf732573a9184e607d87.
- Equity 920 USDT, per-trade risk 4% = 36.8 USDT, kill equity 736 USDT.
- 1 concurrent position, **LIMIT_ONLY**, tradable SOL/LINK/AVAX/NEAR/SUI/
  ARB/APT/INJ/TIA/DOGE USDT perpetuals; BTCUSDT is **context only**, not
  a trade from this manifest. OPUSDT is blocked through 2026-11-03 UTC
  (conservative interpretation of owner cooldown).
- Costs: 4 bps entry/exit fees and 2 bps assumed slippage from the
  pre-existing A183 paper_execution.Policy defaults — **not measured or
  certified actual account charges**.
- Previously cited median notional ~$2,908 and harmful $15k positions
  are **historical observations, not an owner-approved maximum**. No
  verifiable numerical max-notional cap was found in accessible account
  material, and no max leverage or separate max drawdown gate was approved.
  These are stored as JSON null, and eligibility is explicitly BLOCKED.
  **Do not replace null with 2,908, 15,000 or any guessed value.**
- Source entry/exit rules are not pinned as executable code; this
  registration does NOT alter current snapshot schedule or make them trades.

## Locked review gates

Per registration: laboratory PF strictly >1.2 with >=30 closed trades
(necessary not sufficient for alpha); paper review >=100 CLOSED trades and
>=30 calendar days; max drawdown must be within the *registered* limit;
kill-equity matches registered risk policy. Missing drawdown limit or cost
assumptions blocks executable promotion. No gate certifies live execution.
All calculations are precommitted metadata, NOT a trading result.

The operation to update an entry is prohibited. Any later improvement
uses a NEW strategy_id and parent_strategy_id pointer, never in-place
editing of a registered artifact, not even to fill a missing risk cap.
The owner can review and authorize a new version after source confirmation.

## Integrity and acceptance

- research/registry/strategies/*.json: canonical UTF-8 JSON with
  sorted keys, no floats/NaN, exact schema and Decimal-strings.
- research/registry/registry_witness.jsonl: existing sha_ledger.extend /
  verify SHA256 chain, per-entry exact Git blob SHA, path and UTC date.
  Head: 76055470cfc7ad0b7c82e55deeafd2b264f3b83bd103b3171af8dd8b90eb511e.
- Negative byte change test detects manifest edit; altered witness payload
  is rejected; missing/added manifests reject; schema prevents permission
  flips, gate weakening, wrong owner numbers, and SPOT/OP substitution.
- CI checks repository file history for M/D/R/T on registered manifests.
  This is an operational immutability gate, **not GitHub ruleset protection**;
  force-push or changing the gate itself requires external governance.

    python -m research.platform.strategy_registry --root research/registry --verify-history
    python -m pytest tests/test_reset05_strategy_registry.py -q
    ruff check research/platform/strategy_registry.py tests/test_reset05_strategy_registry.py

## Future integration acceptance note (NOT implemented now)

Every attempted PAPER risk preflight, **including all risk_guard refusals**,
must be persisted as an EXECUTABILITY_* event in the accepted
paper_ledger's executability stream, with cause and timestamp and
independently verifiable correspondence to attempts. A successful
preflight is NOT a fill, and paper_execution gap-through-stop losses
supersede optimistic preflight stop estimates. No live permission.

Next separate phase after owner verdict: RESET-05 part 1 Python-only
single-stack freeze/golden fixtures, then part 4 deterministic gate report.
The public OI/liquidation/funding collector remains afterward.
