# RISK-CARCASE-01 — risk before strategies (2026-11-01)

**Status:** FIRST COMMIT CANDIDATE / OWNER_VERDICT_REQUIRED.
**Scope:** strategy-neutral, pure Python **PAPER preflight**, using the existing
research/platform/market_contract.py. No detector, new data source, API keys,
broker client, trader, or live order path.

## Build sequence locked by owner

1. Risk scaffold FIRST: policy, refusal codes, adverse tests, CI.
2. RESET-05 SECOND: Python-only persistent append-only paper ledger, registry,
   frozen golden fixtures, deterministic paper gate; one commit/CI per sub-part.
3. Collector THIRD: Binance public USDT-M OI, liquidations and funding,
   honest gaps/schema drift, SHA chain, coverage; no alpha claims before day 30.

**Invariant:** risk ahead of strategies, data ahead of detector, gates ahead
of money. No TS, no AppDeploy, no modifications to existing PAPER schedules.

## Technical contract

- Caller must explicitly supply a RiskLimits, RiskSnapshot, PaperIntent and UTC
  decision time. There is no tuned/default risk percentage in the production API.
- Fail closed on absent/invalid/non-Decimal inputs, untrusted/stale/future data,
  off-market venue, symbol not in allowlist, portfolio halt, kill-equity,
  peak drawdown, max positions, max leverage, per-trade risk, portfolio
  reserved-risk, notional cap, or insufficient free collateral.
- Stop-loss estimate includes adverse entry+stop slippage plus both fees.
  Gap-through-stop, liquidity, maintenance margin and liquidation are NOT modeled.
  Thus a PASS is not a guaranteed loss limit.
- A PASS is a **PAPER risk preflight only**. The gate is not wired into
  paper_execution.py or any persistent system yet. Enforcement integration
  follows only when RESET-05 ledger exists and review permits.
- RiskVerdict.live_allowed is always FALSE, even on a PASS.
- The numbers in test fixtures are synthetic contract tests, not a new
  registration of VIRTUAL_MECH_920 or a recommendation on leverage/risk.

## Evidence / reviewer checklist

Commands (CI Python 3.10, 3.11, 3.12):

    ruff check research/platform/risk_guard.py tests/test_risk_guard.py
    python -m pytest tests/test_risk_guard.py tests/test_reboot_platform.py -q

Proof requires a **real GitHub commit SHA + run URL + success conclusion**.
Until CI confirms these, verdict is CI_PENDING, not SUCCESS.
Tests prove only the enumerated gates, not a market edge or trading safety.

Base tree: 9587a66e64efb63e115974d62928daea7e4063dc
Base research branch: research/reboot-inventory-evidence-first-20261030
Risk code Git blob SHA: a0b885b9436d00b5bd88b4d8c693a1e553808935
Risk tests Git blob SHA: 356ec09eaf88ca614184c372298c59510106f6b6

Mandate read from main: RESEARCH_MANDATE_LOCKED.md
(the mandate is not present in the historic reboot branch; it is NOT changed here).
Sources: two owner-provided specifications RESET-05 and TЗ-2 (2026-11-01).
Next transition: **PAUSE FOR OWNER REVIEW** after SHA and CI.
