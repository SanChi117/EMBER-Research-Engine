# B1/C22A — original 3m OHLC price reach vs closed BOS-geometry bounds

17 October 2026. **PAPER ONLY**. **NOT_TRADE_READY**, zero author-approved entries.

## Author claim and its falsifiable implications

Primary source: [4. Entry by BOS.txt](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view). Author explicitly permits (a) a market entry **on price crossing the BOS level** or (b) **waiting for price confirmation / limit order**. They are distinct methods. The pictured 1H→3m example requires real 3m BOS, otherwise reject regardless of raid/target. For short the BOS is below BSL liquidity raid; for long above SSL. A raided fractal should be fresh from previous trading session, no older than previous day; meaningful FTA/TP and SL beyond the swept liquidity are required. **This source does not supply original timestamp-labelled Binance USD-M 3m BOS goldens, a machine-deterministic academic 3m structural pivot selection, author's timezone/DST, or tick sequence inside source OHLC.**

The frozen C21B already produced **539** first close-through *research-selected* 3m strict three-candle swing parent edges on 60 original source ZIP (including independent original 3m/5m OHLC 1H parity); these are NOT trade results. Key distinction: 3m OHLC high/low may **reach** the chosen swing before a later 3m candle closes past the level. Neither event proves *exact millisecond/tick of crossing*, executable fill, intrabar order relative to other levels, or an author-approved BOS.

## Code and source proof

- `d05/c22a_intrabar_vs_closed_3m_provenance.py`: pure source-verified, read-only audit. Recomputes **all C21B** closed 3m parent edges from independently attested original C21A source rows (checks symbol, source ZIP SHAs, UTC continuous 3m time grid, exact OHLCV, source raw ID, false READY). For each parent edge, inspect only fully closed 3m rows from `max(1h_raid_confirmed_ms, candidate_3m_swing_known_ms)` through observed C21B close-break candle. Reports earliest original 3m OHLC reach of that *same research-selected* swing: a strict wick low below 3m swing for short, high above for long; first price-reach candle's time **interval bounds**, whether its **close** confirmed crossing, and how many earlier source bars reached before chosen closed break. Never invent intrabar timestamps.
- `d05/test_c22a_intrabar_vs_closed_3m.py`: **9 adversarial/positive tests** including wick of a 3m bar reaches selected swing with no close, following bar **does close** past it (same closed 1H parent and original row identities). Rejected future/as-of, fake author READY, corrupt original 3m raw-row ID, early unconfirmed 1H raider, raid wick invalidation and earlier-prefix invariant. Prior **15 C21B tests** also run.
- `tests/probe_c22a_original_3m_intrabar_bounds.py`: independently re-downloads **45 original Binance USD-M Futures source ZIP** (15 original monthly/daily 3m plus 30 C08 native15m/1d), validates paired original ZIP SHA+.CHECKSUM and full 5×3m→C08 independently native 15m exact Decimal OHLCV before replay. Comparisons frozen C21B per-symbol **539 parent edges** and causal earlier as-of source prefix separately recreated and checked for exact equality. All per-symbol totals and five traceable source-raw-ID witness examples pinned in `evidence/c22/C22A_ORIGINAL_3M_CROSS_CLOSE_BOUNDS.json`.
- Independent original CI [39047983878](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39047983878) **SUCCESS**: 24 tests (9 new C22A, 15 prior C21B), 45 original original USD-M source ZIP independently re-downloaded, all pinned C21B first close events.
- Pinned evidence Git blob: `05817435a27fc9273de8192fa8937969edf46c0b`. [Independent pinned rerun](https://github.com/SanChi117/EMBER-Research-Engine/actions/workflows/mtf-b1-c22a-original3m-cross-close.yml) must be SUCCESS before treating C22A as source-closed. Original C08/C21A/B immutable blobs never changed.

## 32-day original source results by market

| Symbol | Original C21B research 3m break-parent edges | Selected level reached on earlier 3m bar **without** close |
|---|---:|---:|
| BCHUSDT | 99 | 22 |
| BTCUSDT | 104 | 23 |
| ETHUSDT | 129 | 30 |
| SOLUSDT | 103 | 31 |
| XRPUSDT | 104 | 16 |
| **Total** | **539** | **122** |

All **539** observed closed 3m geometry edges have an **unknown true intrabar crossing timestamp**. For **122/539** parent edges the selected LTF swing was touched by an earlier original 3m wick that **did NOT close beyond the level**. In the other 417, first observed OHLC reach is on the same 3m bar as later close-break. There were **zero** sample edges with earlier 3m **close** beyond the selected swing (for this frozen C21B first-close implementation), and **zero** break bars opening already beyond that selected level. These are counts of **parent edges**, not unique signals or trades; a single native 3m price bar can carry multiple raid parents.

## What is and is not proven

**Proven:** authentic native3m price high/low bounds and candle close timing differ; a plausible author's direct market **price-crossing** route may be earlier than a **closed-candle** researcher proxy. Existing 3m OHLC proves only that an extreme price was observed **at some time within a known source candle**, not actual millisecond order flow or executable fill at that level. Cases with intra-3m stop-and-target excursions in one candle cannot be sequenced from OHLC.

**NOT proven:** a touch qualifies as author's BOS, which 3m pivot is correct, whether session freshness, first HTF liquidity target, FTA obstacle, SL, market/limit execution, RR, win rate, or PNL meet author's rules. No upgrade to `APPROVED`, `READY` or live trading. The independent lesson's 2023 1H/3M backtest reference is historical Forex-context literature rather than the missing timestamp-labelled 2026 Binance Futures goldens.

**Next C22B:** explicitly compare author-annotated positive and negative BOS pivot examples to the frozen C21B choice; source-verify timezone/DST and session rules; if tick-level entry simulation is requested, acquire original historical tick/trade data and maintain real observed event ordering rather than imputing from 3m OHLC. C22A's source geometric distinction is necessary but insufficient.
