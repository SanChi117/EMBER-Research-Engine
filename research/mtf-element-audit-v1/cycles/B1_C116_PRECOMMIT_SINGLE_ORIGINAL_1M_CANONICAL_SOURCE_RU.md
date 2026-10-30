# C116 — до нового источника: 1m canonical single-source for identical 3m & 5m price structure

2026-10-30 UTC. PAPER ONLY, LIVE BLOCKED. C114 SOURCE_BLOCKED A177 (22.02% original 3m/5m volume mismatch); C115 SOURCE_BLOCKED A178 (XLM original 3m/5m 15m LOW 0.39478 versus 0.39467, material). Never change C114 or C115 to appear green.

## Source hypothesis (no price alpha tuning)

An internally consistent 1m original trade stream can reconstruct both 3m execution and 5m CHoCH without contradicting itself. C116 obtains exactly **1344 ORIGINAL_BINANCE_VISION_USDM_NATIVE1M daily ZIP** across two fixed source-time windows, 1,935,360 raw 1m OHLCV rows. Every ZIP/CSV SHA and official Binance .CHECKSUM required. Each day exactly 1440 original 1m bars. UTC no gaps, duplicates, NaN, impossible prices, or missing days. Any anomaly SOURCE_BLOCKED, not interpolation.

**Derived 3m** is computed by grouping exactly 3 consecutive *fully known* original 1m candles; **derived 5m** by grouping exactly 5 consecutive original 1m candles. 3m+5m 15m OHLCV parity must be bitwise exact in Decimal for every bucket. Not independent original 3m/5m! Output must label DERIVED_FROM_ORIGINAL_1M and explicitly say original native3m/native5m were not used in C116. Raw original1m can be independently checked by provider metadata. If C116 accidentally claims 2688 original 3m/5m ZIPs, validation must fail.

## Economic study unaltered from frozen C114

C114 source and economic code unchanged, including all t0 parent identification, 5m CHoCH 2L2R, 6h common landmark, original 4H near-edge distal structure stop +/- 0.15 fully closed ATR14, nearest preconfirmed unswept 4H FTA pivot target, 48h stop-first at derived 3m OHLC, cost 14/25/40bps, matching same symbol/month/side/range/risk/reward bucket, fixed block-bootstrap seed 11420261030 2000, early-competing events, per-symbol capacity and 1% starting-equity DD bound.

Treat both intervals **as economically unexposed but NOT pristine market-data blind** because C114/C115 already inspected archived price/volume source compatibility, not any signal or profit outcome. Fixed 2025-01-01 .. 2025-02-26 exclusive and 2026-02-01 .. 2026-03-29 exclusive, 12 original symbols. Changing dates based on outcomes forbidden.

## Two-window binary gates (do NOT relax)

Per window >=40 matched T-C pairs >=10 early+late; T 25bps total netR>0, PF25>1.2, PF40>1.1; 95% block-bootstrap lower bound for mean matched T minus C 25bps>0; T higher TP-first than C in each temporal half; adverse-wick 1% initial capital risk portfolio DD<10%. Historical screen PASS is NOT live approval; NO_POWER if insufficient matched pairs; FAIL if economic negative. No tuning or cherry-picking based on source or outcome, no automated real orders.

## Notes on source and validity

C116 uses **single canonical 1m price source**. Therefore the test is a source architecture research hypothesis, NOT a clean independent replication of C114 original-native5m strategy and NOT a futures execution guarantee. 3m backtest stop-first remains an OHLC approximation despite availability of 1m original. Do not silently claim original 3m or 5m provenance, and do not refit 3m bars to previous contradictory originals.

Execute frozen negative tests for clocks, same-bar OHLC parity, as-of 5m pivots, no synthetic future leakage, source restoration, unchanged economic rules before any historical data. Only then load all 1344 provider source ZIP; record original checksum manifests, derived OHLC parity, 4H source geometry, full matched/control event and 14/25/40bps economics. Positive => research-stage only; source conflicts, unit fail, no-power => deny.
