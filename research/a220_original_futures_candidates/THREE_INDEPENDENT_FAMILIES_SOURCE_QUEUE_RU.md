# A220 — реестр независимых ORIGINAL Futures-кандидатов после A217–A219

Дата 2026-10-31. **Locked mandate main v1** прочитан; задача строго Binance **USDT-M Futures**. Ни один из нижеследующих источников ещё НЕ проверен на нашем after-cost/forward-гейте. Исторические отчёты авторов — гипотезы, не наши PnL. **Не использовать A214–A216, не добавлять в PAPER.**

## Зачем новый реестр

- A217 `TrendRider` long-only trend pullback, 24 genuine native runs → отрицательная экономика на 2024/2025 и стресс.
- A218 `djienne/pair_trading_NEDL` original two-perpetual cointegration, 56 Binance ZIP, 853 genuine bars / 730 diagnostic original signals → **BLOCKED**: funding, margin, actual rebalance and final close missing, а не доказанный минус. [CI](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41218765741).
- A219 `juriok/chart-pattern-backtester` original 4h pattern breakout → **REJECTED SOURCE VENUE**: положительный якобы futures-PnL в оригинале рассчитан на CCXT spot pair selection, constant funding. 4 blob SHA и 8 checks verified [CI](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41219075765).

## Новые оригиналы — разные механизмы

### C1 — cross-sectional risk-adjusted momentum, market-neutral futures

**Источник**: [AbdullaE100/perp-quant-lab](https://github.com/AbdullaE100/perp-quant-lab/tree/104dc669084b7f0d0a99748a0f4300950b49930d), pinned commit `104dc669084b7f0d0a99748a0f4300950b49930d`; `research/backtest.py` blob `cf02c6c525a297112b5f1f594a0ba2a0a1557cf8`, `research/fetch.py` blob `a0d8fe281792b2f87b1f66d21bf89b5e32ed1082`; script strategy `scripts/crossmom.ts` still requires independent audit.

Mechanism: rank relative futures strength by trailing price / realized volatility over ~40 liquid perpetual contracts, long leaders short laggards, dollar-neutral periodic rebalance. **Not** A211 1d Donchian single-pair or A217 indicator pullback. Author reported OOS Sharpe ~1.62 for cross-sectional momentum; other quoted 1-line momentum ~1.41. **Author admits** same original tests omit real funding carry and thin-alt slippage, plus point-in-time universe survivorship bias. Funding downloaded by `fetch.py` is not proof it was charged by `backtest.py`: the latter explicit `net = gross_ret - turnover*FEE` (5bps one-way) only.

**Next gate:** freeze exact original family/window/weights and universe; original current-universe issue must be labeled `SURVIVORSHIP_BIASED`; reconstruct genuine point-in-time availability if possible without silently replacing the original; add actual settled futures funding and execution stress as independent **audit only**, not parameter tuning. No VERIFIED until full after-cost OOS and marked risk.

### C2 — cross-sectional *funding* carry, two perpetual futures sets

**Источник**: [OctopusTakopi/funding-rate-alpha](https://github.com/OctopusTakopi/funding-rate-alpha/tree/cf9f87c01d3165bbc3bf34438baee289d248ffca), pinned commit `cf9f87c01d3165bbc3bf34438baee289d248ffca`; `scripts/baseline_carry.py` blob `459e3d03627add90e6f96fa67dfed082654584f2` plus `scripts/swing.py`, `scripts/risk_managed_carry.py` to audit before choosing frozen original.

Mechanism: short higher-funding USDT perpetuals / long lower-funding perpetuals, many contracts, NOT spot-perp hedge A212/A213. Source study includes delisted contracts and settlement histories, but some reported daily long-short carry has a severe price-leg drawdown (~74%) despite attractive Sharpe. **Не считать 17.7bps/day доказательством низкого риска или возможности розничного исполнения.** Independent portfolio margin, rebalance, short borrowing/funding costs, stop/liquidation and real fees required. If stress DD fails mandate, reject before broad backtest.

### C3 — event-driven pump reversal on futures (different from momentum/carry)

**Источник**: [agarwalchirag535-lab/smallcap-pump-reversal](https://github.com/agarwalchirag535-lab/smallcap-pump-reversal/tree/12e7227a0757ea855a995713be31c4c94b9c8d1f), pinned commit `12e7227a0757ea855a995713be31c4c94b9c8d1f`; `src/strategy.py` blob `7bff19337ca2a47753e9ac2e108eff9345fcc079`; `src/backtest.py` blob `f815e59e9410295fc99d97a6a9d89897948ff034`.

Mechanism: shorts after >=25% pump over 24h, 7-day volume confirmation, BTC regime gating, 72h hold, 143 futures universe. Author claims preregistered negative-screen history and forward paper pending; `backtest.py` has `COST_BPS=30` but no full funding/mark/liquidation in source inspected so far. High short tail exposure, danger of unlimited upside/liquidation even with 72h time exit. **Different from A207 taker-flow and A202 long dipcatcher**; source still may fail.

**Next gate:** prove causal event ordering and realistic intrabar STOP-first/gap for short squeeze; original 143 universe point-in-time listing; historical funding and margin; compare real margin loss tails. Never call 72h time stop a price stop.

## Source-selection rules

1. No source has `VERIFIED_FUTURES_CANDIDATE`; these are `SOURCE_ONLY` and can be rejected cheaply.
2. First inspect exact original code, version, dataset type, parameter selection history and full after-cost finance; **before** new PnL attempts prereg and protect untouched OOS/forward.
3. Start C1 cross-sectional futures momentum: original author has positive OOS claim, but funding+selection gaps. Test applicability and budget before running a multi-thousand-ZIP suite.
4. C2 depends on whether reported extreme drawdown survives a consistent capital normalization and independent mark-to-market; no free-carry assumption.
5. C3 is reserve if C1/C2 fail; short squeeze/liquidation is hard blocker.
6. **Never choose by attractive README Sharpe alone.** Cross-check full journals + (fees/funding/spread/slippage/margin) and independent period. No live orders or existing scheduler changes.

## Validation stages

`SOURCE_ONLY → ORIGINAL_CAUSALITY_PASS → REAL_BINANCE_LEDGER_PASS → AFTER_COST_ECONOMIC_PASS → INDEPENDENT_OOS_PASS → FORWARD_PAPER_PASS → VERIFIED_FUTURES_CANDIDATE`.

If no candidate passes, continue search under **the SAME immutable target**; do not invent SPOT replacement, good PnL or optimized parameter search.

Сводка A220 — **реальные FUTURES исходники найдены, прибыльность в EMBER НЕ ДОКАЗАНА**.