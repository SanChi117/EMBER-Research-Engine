# MTF Route Lab v0.4 | FROZEN PAPER research branch

Separate from existing EMBER engine, SMOKE terminal, Work and V2.2. No private keys, orders, or autopilot.

- Frozen model: independent IMB/SNR, IDM and BOS 15m **proxy** (not the original 3m BOS).
- Long history: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT, Binance USD-M Futures.
- 15m UTC interval: 2026-04-01 inclusive to 2026-10-13 exclusive (18,720 bars per symbol).
- Native 1d: 2024-01-01 inclusive to 2026-10-13 exclusive (1,016 days each).
- Downloader verifies Binance Vision official .zip.CHECKSUM, no gap or mixed Spot/Futures.
- Strict gate cross-checks 15m vs 1d (including volume).
- Fixed 2 FTA x 2 costs: COURSE_PARENT_FTA, V22_FIRST_OBSTACLE; BASE, COST_X2.
- Paper portfolio replay tracks candle-touch fills, closed equity and model drawdown; no exchange fills, funding, liquidation model, teacher-verification or untouched OOS.
- Existing EMBER prior artifact: run 30842493927 has PEPE/FET/WIF/SUI only; cannot substitute for this 5-symbol dataset.
- Existing Smoke-strategy downloaders and outputs are *not* imported to avoid changing source market or previous validation definitions.

View the [workflow](../../.github/workflows/mtf-route-lab-futures.yml) or Actions tab; open its run and download artifact `mtf-v04-usdm-20260401-20261012`. If it fails, `results_04/DOWNLOAD_ATTEMPT.json` records the blocker. An Actions success confirms engineering execution, **not** a trading edge.

Zip SHA256: `11a3276974396d5be31009cf68256e3d7b4aa43ece89a0efacb2c5620583486e`.
