# EMBER V3 — 50 USDT-M Futures / 4H POI / 1H initiative

Date: 2026-11-01. **RESEARCH_ONLY / NO_VERIFIED_EDGE / NO_PAPER / NO_LIVE**.

Research code branch: research/mtf-v3-structural-universe-20261101.
Successful proof: https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41278272053
Artifact: ember-mtf-v3-50-futures-POI-events (zone births/breaks, contacts, forward labels, source SHA256, structural transfer OHLC replay).

## Provenance and actual completion

Read SMOKE sources, NOT abstract SMC textbooks:
- structure.ts blob 7f8a18913d0674ab873964c43c18f32236fcf31a
- zones.ts blob f5ca1bd6a7757b8574d3cbd833abb9b0b077405d
- math.ts blob 125f8551a0fa27b093dd9e6ab94a146cd1607319

Adapted in EMBER:
- 4H BOS/CHoCH with confirmed 3-left/3-right pivots; swing POI width 0.28 Wilder ATR.
- Source order-block origin (last opposite candle in prior ten), original demand/supply bands.
- 4H 3-candle FVG with >=0.12 Wilder ATR gap.
- Each zone has separate origin_at, available_at (closed confirmation), retests, broken_at, expires_at.
- Original snapshot horizon approximated as last 24 OB births, 20 swings, 180 FVG bars; approximate 0.06% midpoint dedup.
- 1H contact can refer ONLY to a zone already known before that hour opens.

**Not full source-native parity:** scores/departure quality, dedup priority of inactive levels, and complete SMOKE source-native lifecycle are not yet shown bar-for-bar identical. The original SMOKE/Pine strategy has not been fully ported.

## Dataset

50 genuine USD-M futures contracts, curated BEFORE examining results. 17 source CSV batches saved in research/mtf_v3_universe/data, each SHA256 manifested. 75,000 true closed 1H + 50,000 true closed 4H Binance candles, with taker-buy volume. Approximately Aug 30–Oct 31 2026 for 1H, May 18–Oct 31 for 4H. UTC continuity and 1H↔4H overlapping OHLCV parity checked.

19,540 historical zone births; initial unbounded count 20,227 contact episodes was too broad. After source snapshot expiry and source-style midpoint dedup, **17,376 zone-contact episodes** remain, with 17,243 mature 12h forward price labels. These are **not independent trades**: multiple POIs can encode the same movement, and altcoins move together.

## 12-hour forward price response (NOT trading PnL)

| Pre-registered cohort | Mature events | Mean directional 12h response |
|---|---:|---:|
| All 4H zone contacts | 17,243 | +0.022% |
| Sweep and reclaim | 2,069 | +0.038% |
| Sweep/reclaim + elevated 1H volume | 1,781 | +0.044% |
| Plus seller/buyer aggressor taker pressure | 1,276 | +0.069% |
| Comparable effort but NO qualifying pressure | 505 | −0.021% |

Matched negative twins: same symbol + zone type + direction + calendar week and nearest pre-known volume, penetration, age. **147 matched pairs**; mean incremental 12h directional result of aggressor pressure **−0.002 percentage points**; day-cluster 95% interval **[−0.671,+0.709]**. In the broader cross-symbol week matches, **433 pairs** with mean difference **−0.183 pp**, interval **[−0.766,+0.588]**.

**No positive predictive edge confirmed for aggressor-flow alone.** A separate future-labeled cohort of 1H transfers appears stronger but is not a valid pre-confirmation trading signal: response is partly included in its subsequent outcome.

## True chronological post-transfer entry diagnostic (50-symbol pool)

Only after separate CLOSED 1H response, at NEXT 1H OPEN, use already known 4H zone structural SL/TP, requiring prospective room RR>=1.25. 24h stop-first OHLC replay, no false fills, provisional 0.35% notional roundtrip haircut.

| Model | Source sweep-effort events | Simulated complete trades | Mean stress proxy | Median stress |
|---|---:|---:|---:|---:|
| Price response only | 1,788 | 450 | **−0.574%** | −1.583% |
| Price + aligned taker flow | 1,788 | 311 | **−0.539%** | −1.583% |

Flow model: 201 STOP, 60 4H structural target, 50 time exits; 30.9% net-positive events. September 153 complete events, mean −1.171%; October 158, mean +0.073%. These percentages apply to nominal, **NOT user capital return**. This is 1H timing research, NOT final 15m execution.

Causality/geometry checks: **13/13 PASS**; test runner and archive passed. No 15m executable fill model for all 50, actual funding/mark/liquidation/orderbook/margin or portfolio ledger. No OOS and only ~62 days of 1H events. Historical delisted-contract universe omitted; survivorship caveat.

## Conclusion

**We have solved the earlier observation-frequency bottleneck at research scale**, not the profitability problem. A large universe yields many genuine historical POI interactions and negative lookalikes without weakening detection. Current definition of 1H initiative transfer fails too often after apparent confirmation; taker flow does not fix this. Do not tweak filters to chase numbers.

Remaining priority: source-native POI parity; research WHAT features separate real persistence after 1H transfer from temporary rebound, with separate labels and time-separated OOS; 15m execution and real futures economics. Keep 0 VERIFIED, existing research mandate, SMOKE, EMBER main, PAPER, accounts and live orders unchanged.
