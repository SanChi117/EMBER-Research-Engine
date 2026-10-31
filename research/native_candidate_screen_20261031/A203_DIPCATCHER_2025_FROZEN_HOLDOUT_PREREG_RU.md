# A203 — ЗАМОРОЖЕННЫЙ independent holdout для ORIGINAL dip_catcher, период 2025

Дата 31.10.2026. **ЗАПИСАНО ДО ПОСМОТРА РЕЗУЛЬТАТОВ 2025**, paper/research only, no live/SMOKE/planner changes.

## Мотив и baseline

A202 fixed 2026 May13–Oct1 original `viktors1982/trading@e572140b1b8cb550cb244c67d363087b81bd4ab8`, `dip_catcher.py` blob `76ab2b3f91dc7beaa0be8021a245caa2b3f4186f`: economic PASS 3/4 BTC/ETH/LINK after fees 5bps and 12.5bps; fast-hold and risk stop requirements FAIL (SL8% prices, p90 HOLD >24h). Primary result in `A202_NATIVE_DIPCATCHER_REAL_BINANCE_VERIFIED_RESULTS_RU.md`.

No source/parameter adjustment after A202: original stoploss −8%, minimal_roi 3% 0min /2% 30min /1% 60min, original entries/exits, original entry limit/exit limit, `can_short=True`, 5m, 1x, max 1 position per coin, fixed proposed stake $100, four separate $1000 isolated paper wallets. Only engine `freqtrade==2026.4`.

## Historical holdout (chronologically later than Freqle 2022–2024 benchmark)

**[2025-05-13,2025-10-01) UTC = 141 days**, BTC/ETH/SOL/LINK perpetual Binance USD-M genuine monthly Binance Vision 5m price and 1h trade/mark/funding for May–Sep2025. This date set NOT chosen after seeing these candidate outcomes; source is older but had not been evaluated with this original in our project. This holdout is independent of 2026 May–Sep tested dataset, yet not prospective as of 2026; do not call it live/forward validation.

Data source exact monthly ZIP URLs and SHA256 manifest; strictly 44,064 5m candles and 3,672 1h candles for each pair continuous, 1h mark daily repair only using authenticated Binance Vision daily source (no synthetic fills), funding only genuine scheduled settlements; no API credentials/orders. Report missing source as BLOCKED, never interpolate.

Two fee scenarios BASE 0.0005 each fill and STRESS 0.00125 each fill; no extra slippage or limit queue model, so even STRESS optimistic.

## Same PREDECLARED gates as A202, fixed before observing 2025 results

- **Economic:** at least 2/4 named symbols BOTH fees each: N≥35; net wallet profit >0 after fees/funding; PF≥1.20; max wallet DD <15%; top3 winning trades <60% of aggregate winnings, plus ≥141 completed trades across four independent series at each fee tier. Check exact native ZIP receipts.
- **Speed:** among economic passing pairs ≥2 have median hold ≤6h and p90 hold ≤24h in both tiers; otherwise FAIL.
- **Execution risk:** always FAIL for ORIGINAL -8% price stop (20–30x incompatible). No real, no autonomous paper orders under any result.
- No compound re-use of shared portfolios; don't claim 141 days sample implies 3–5 orders/day if trade concurrency, fees and real queue uncertain.
- Rejection criteria never relaxed after seeing data; if dataset, workflow or source missing → BLOCKED / technical-error and fix infrastructure only. No cherry-picked months/coins/parameter updates.
- OOS relative to 2026 strategy selection, but broader post-hoc candidate search across A188-A202 introduces multiple-testing bias, so even PASS warrants further truly contemporary validation and independent holdout/forward PAPER.

## Planned evidence

Native Freqtrade 8 archives, each trade ledger, actual SHA256 original source and Binance Vision downloads, exact 2025 timerange, costs, funding, full risk and hold stats. Compare to A202 only after 2025 frozen aggregate exists.
