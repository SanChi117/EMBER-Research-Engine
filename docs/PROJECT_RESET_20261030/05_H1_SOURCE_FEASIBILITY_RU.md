# RESET R01 H1: историческая проверка доступности данных, не бэктест

Дата: 2026-10-30. Read-only подключённые публичные данные Binance spot/USDM. Монета BTCUSDT. Запрошенный UTC интервал: 2025-10-01 00:00 — 2025-10-03 00:00. Интервал свечи: 4H.

Проверено:
- Spot OHLCV: **13** исторических свечей, все непрерывные 4H, timestamp первого open 1759276800000, последнего open 1759449600000.
- USDM perpetual OHLCV: **13** исторических свечей, все 4H, совпадают с spot по open/close UTC меткам.
- Realized funding settlement: **6** historical records, fundingTime/rate:
  `1759276800000 0.00003355`, `1759305600000 0.00003457`, `1759334400000 0.00010000`,
  `1759363200000 0.00007784`, `1759392000013 0.00010000`, `1759420800000 0.00009543`.
- Historical USD-M OI 2025 same period: API **HTTP 400, -1130**, startTime invalid. No historical OI evidence for this window.
- Matched 4H close basis range (perpClose/spotClose -1) ×100 across 13 bars: **−0.05571% to −0.02976%**. This is NOT a quoted, executable spread.

**Boundary caveat:** 13 4H candles came back due endTime-inclusive API behavior. For intended two full days `[2025-10-01,2025-10-03)` use only **12** first candles. No future candle leakage allowed.

**Clock caveat:** fundingTime `1759392000013` deviates +13ms from ideal 8-hour lattice, adjacent gaps +13ms/−13ms. Keep actual provider timestamp, do not infer exact settlement by hard-coded 8-hour floor.

**Limitations:** Original provider spot/perp ZIP/CHECKSUM not fetched in this sample; no historical bid/ask book, no two-leg entry proof, no expected funding historically known at entry, no complete funding/borrow/liquidation/fee accounting. Historical settled funding is future information before that settlement. Source availability is not profitable alpha. No new market signal or trade.

Verdicts: `H1_SPOT_PERP_FUNDING_HISTORY_PARTIAL_SOURCE_PASS`; `H1_REAL_EXECUTABLE_SPREAD=SOURCE_BLOCKED`; `H2_2025_OI_BINANCE_REST=SOURCE_BLOCKED`; `LIVE_BLOCKED`.

Next: source-QA of original spot/perp archives with reliable data availability timestamps and cross-venue quotes, then preregister H1 economic test before evaluating PnL. Bybit/vendor OI coverage separate verification.
