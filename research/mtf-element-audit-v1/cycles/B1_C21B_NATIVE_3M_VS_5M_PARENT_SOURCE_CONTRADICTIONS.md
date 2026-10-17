# B1/C21B — original USD-M 3m versus 5m LTF research structure after 1H first wick raid

2026-10-17. **PAPER ONLY**. This technical comparison is of price-source witnesses, not author-approved BOS or trade signals.

## Primary academic authority — preserved exactly

[4. Entry by BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) says a 1H HTF liquidity raid is synchronized to LTF BOS, usually 3–5m, **requires wick-only fractal 1H raid** and **BOS below raided BSL for short, above raided SSL for long**. The illustrated **1H→3m** setup is rejected if there is no **3m BOS**, even if HTF raid and target look correct. It allows market entry at BOS crossing **OR** waiting for price consolidation / limit entry. The source does not define exact machine-selectable 3m pivot priority or authorize mapping general screenshots to Binance Futures timestamp goldens. [Original Fractal/Liquidity/Raid](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): strict 1+1 three-candle fractal is only confirmed when the following candle has closed; 'clean' raid by wick. Prior-session freshness, appropriate liquidity/FTA target and SL beyond raided level remain independent required controls; timezone/DST of author session not established. Original sketch images are schematic reactions, **not original-timestamp Binance author goldens**.

## Code / scope

- `d05/c21b_original_3m_raid_break_geometry.py`: from **independently C21A price-attested native 3m**, reconstruct fully closed **20×3m = 1H** price candles, strict three-candle confirmed **1H BSL/SSL** high/low, first wick-only 1H raid confirmed only after next full 1H candle. Then identify strict **three-candle 3m fractal** and *first full 3m candle **close** across the most recent preknown eligible fractal* beyond swept BSL/SSL. Reject an event if a later 3m price extremum violates the raid wick before the close-cross. The swing-choice and waiting for next 1H close are explicit conservative **research definitions**, not claims of author-equivalent trade timing.
- `d05/c21b_3m_5m_geometry_compare.py`: verify original 3m-derived and original 5m-derived 1H candle OHLC price **equality over all 768 hours per symbol**; compare by actual same HTF raid parent tuple `(liquidity kind, 1H fractal center, first wick raid start, side)`. Retain **all** parent edges; NEVER group independent raids into a single trade, NEVER choose the nearest or preferred parent without author evidence.
- `d05/test_c21b_native_3m_vs_5m.py`: **15 synthetic adversarial/positive** tests for next 1H candle closure, first 3m close timing (no future suffix), prior swing known-at, body raid and wick invalidation, tampered original 3m row hash, unauthorized READY, 3m/5m 1h parity, and two explicit anti-equivalence cases: **same exact 1H candle geometry yet only native 3m exhibits an LTF closed structural cross, or only native 5m exhibits one**. Synthetic fixtures are not author-labelled goldens.
- `tests/probe_c21b_original_3m_vs_5m_60zip.py` independently re-downloads **60 original USD-M ZIP** for all five BTC/ETH/SOL/XRP/BCH: 30 frozen C08 native 15m/1d, 15 C21A original 3m, 15 C20A original 5m (Sept monthly + Oct 1/2 daily), checking all original SHA and original same-host .CHECKSUM plus exact native **5×3m→15m** and **3×5m→15m** Decimal OHLCV. C08/C20/C21A Git SHA never relaxed. Tests identical C21B full-history vs independently generated 2026-10-02 00:15 UTC partial native streams (**no lookahead or unclosed 3m/5m**). `evidence/c21/C21B_ORIGINAL_3M_VS_5M_REPLAY_RECEIPT.json` pins full per-coin results with Git blob `a9a121cb41477b105dd13a1228b5d0577ac3abda`.

## 32-day original source result, 5 symbols

| Original source-derived closed-candle metric | Result |
|---|---:|
| Original ZIPs re-downloaded across native 3m,5m,15m,1d | **60** |
| Original full native 3m bars | **76,800** |
| Original full native 5m bars | **46,080** |
| Exact independent C08 native 15m OHLCV matches each LTF | **15,360 / 15,360** each |
| Identical hour OHLC originals 3m vs 5m | **3,840 / 3,840** |
| Original **3m** closed structure break *edges* after first closed 1H wick raid | **539** |
| Original **5m** equivalent break *edges* | **512** |
| Matching raid parents seen on **both** native LTFs | **509** |
| Valid parent seen only on native 3m | **30** |
| Valid parent seen only on native 5m | **3** |
| Common parent: 3m break closed first | **385** |
| Common parent: 5m break closed first | **91** |
| Common parent: both closed simultaneously | **33** |
| Distinct original 3m native break bars | **390** |
| Distinct original 5m native break bars | **370** |
| Additional 3m edges from multi-parent same native break bars | **149** |
| Additional 5m edges from multi-parent same native break bars | **142** |

Per coin retained in pinned source JSON. Parent edges are **not** independent trades. Those extra 3m and 5m parent edges show that simply returning one 'best' parent would silently invent an academic attribution. 3m **is not equivalent to** 5m, including on perfectly matching 1H price history. There are **no** author-labelled Futures 3m BOS/FTA/SL positive or negative timestamp cases, and **0 author-approved entries or PNL**.

## CI / attempted falsification / limits

Initial [C21B original 60 ZIP CI 39043218316](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39043218316): **SUCCESS**, 15 synthetic cases and independent source replay. Pinned independent [C21B replay 39043362655](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/39043362655): full immutable Git SHA and independent original source re-read (**check conclusion before acceptance**).

No assumption of author timezone (including London DST), same-session freshness, previous-day clock, model FTA selection or structural SL crypto pip units is promoted as certified. A native 3m source witness is necessary but still insufficient for an author-approved 1H3m setup. The closed-candle method does not claim tick-level timing of market-on-cross entries. No trade execution hooks, account keys, futures orders, profitability or READY paths.

**Next B1/C22:** qualify author BOS structural pivot selection against independently labelled author positive and negative time-anchored market examples; research first-tick crossings vs candle close without inventing tick order within 3m OHLC; prior-session freshness with verified author timezone/DST, FTA and structural SL. All unresolved outcomes remain **UNKNOWN / NOT_TRADE_READY**.
