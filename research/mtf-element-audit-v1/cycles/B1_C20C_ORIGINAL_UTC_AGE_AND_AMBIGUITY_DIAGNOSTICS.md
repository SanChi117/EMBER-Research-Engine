# B1/C20C — original 45 ZIP replay: UTC age, multi-parent overlap and source restrictions

Date: 2026-10-16. **PAPER ONLY.** Research-only temporal observations, not trading or author-labelled academic BOS.

## Author primary sources and what is literally claimed

1. [4. Entry By BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): HTF raid on 1H → LTF 3m/5m BOS, wick-only fractal raid, structural BOS below BSL or above SSL. Fresh raided fractal should be from *previous session, no older than previous day*. Author gives working-time 09:00–17:00 **without a verified reference timezone**. TP typically first 1H liquidity or prior session extremum, SL only beyond swept liquidity; skip if nearby FTA invalidates effective R:R. The 15-pip SL example is FX-specific and has no validated USD-M crypto pip-unit translation. A model without the 3m BOS is rejected in the original illustrated 1H/3m variant.
2. [PDPWPM High&Low. Session Liquidity](https://drive.google.com/file/d/1HqGlqYUZptdNvOVLBHftx03XYASvo9MZ/view): prior calendar day/week/month PDH/PDL etc and earlier Asia/London session extrema can be candidate liquidity references, but no unambiguous timezone/DST policy or executable FTA priority.
3. [Типи сесій](https://drive.google.com/file/d/1DZ9fClxslV7GkQhIKNS-lh8EksePh3zQ/view): session scenarios depend on directional Order Flow and context; cannot replace author session with UTC hour proxies.
4. [Fractal / Liquidity original lesson](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): strict 1+1 three-candle swing high/low is geometric liquidity; equal-high/low clusters are not always exactly equal.

## Implementation and falsification method

- Historical source is C20A: five Binance USD-M Futures BTC, ETH, SOL, XRP, BCH 2026-09-01 to 2026-10-02, **45 original source ZIP** independently re-downloaded and .CHECKSUM verified, **46,080 native 5m**, original 15m/1d and 1h exact OHLCV parity frozen in C08/C20A.
- Historical price events are **512** C20B geometric closed 5m price crossings after a strict 3-bar 1H first wick fractal raid and subsequent complete 1H confirmation. C20B 5m BOS-pivot selection is still **RESEARCH_OPERATIONALIZATION**, not author-labeled.
- `d05/c20c_context_observations.py`: source-recomputes original C20B event set and categorizes 1H pivot confirmation UTC calendar day relative to the first 1H raid. It also checks post-raid confirmation→5m BOS-close interval `>24h`, events with **multiple parent 1H raids associated to the same native 5m bar**, and a **UTC 09:00–17:00 clock proxy**. None is turned into author session, author freshness, FTA or SL rule. Each output permanently says `UNKNOWN_SOURCE_TIMEZONE`, `UNKNOWN_SOURCE_FTA`, `UNKNOWN_SOURCE_BOS_LABELS`, `NOT_TRADE_READY`.
- `tests/probe_c20c_original_utc_context.py`: independently re-downloads and parses all 45 original ZIP, asserts all 512 geometric witnesses and UTC classification partition. Full resulting per-symbol table compared **exactly** to an immutable pinned JSON receipt `evidence/c20/C20C_ORIGINAL_UTC_CONTEXT_OBSERVATIONS.json`.
- `d05/test_c20c_context_observations.py`: synthetic negative checks on no author signoff, UTC age exhaustiveness, future/as-of barriers, false academic READY, tampered native 5m provenance, future suffix invariance. Synthetic controlled data do not author-approve any observed Binance bar.
- `evidence/c20/C20C_AUTHOR_CONTEXT_GATE_MATRIX.json` explicitly separates six quoted author rules from missing model evidence (structure, previous session, timezone, FTA, pip/SL, 3m goldens).

## Exact original 45 archive result

| Symbol | Original geometric 5m breaks | 1H pivot same UTC day as raid | Previous UTC day | Older UTC day | UTC close 09–17 | Multiple parent edges |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 101 | 76 | 16 | 9 | 46 | 51 |
| ETHUSDT | 122 | 78 | 23 | 21 | 46 | 75 |
| SOLUSDT | 98 | 67 | 20 | 11 | 41 | 40 |
| XRPUSDT | 97 | 59 | 22 | 16 | 32 | 49 |
| BCHUSDT | 94 | 62 | 19 | 13 | 34 | 31 |
| **TOTAL** | **512** | **342** | **100** | **70** | **199** | **246** |

Zero of these observed 5m closes occurred **more than 24 hours after the next-hour-confirmed 1H wick raid**, which is unsurprising because of the source algorithm's first crossing and subsequent sweep-extreme cancellation, and not evidence of author session freshness.

**70 older-than-previous UTC day** observations are NOT automatically author-disqualified, since UTC day != verified author session; this is a forensic contradiction candidate only. **246 event-edges** share a 5m candle with another raid-parent candidate; this is an ambiguity count and must NOT be read as 246 distinct candles or 246 independent trades. UTC 199-in-window is a proxy, not author's timezone.

## Acceptance and remaining evidence

- Initial original replay [C20C source CI 38967371422](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38967371422): **SUCCESS**, 2 initial synthetic and 45 original source ZIP replay.
- Strengthened adversarial suite now 8 total C20C synthetic tests; subsequent independent pinned receipt network replay: [C20C proof CI 38967618927](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38967618927). Only mark [x] when CI and A088 complete.
- **No unqualified author BOS, no author session fresh validation, no author FTA or SL sizing, no real crypto pips, no entry or PNL.**
- Required C21 follow-up: exact author 3m/5m BOS pivot classification on author-labelled time/price examples; resolve original session timezone explicitly before session gates; source-attest 3m historical complete archives, FTA obstacle and structural SL as separate evidence-only gates, and negative author examples. No nearest parent and no assumed 24h TTL.

**Readiness `NOT_TRADE_READY`, author positive timestamp goldens `0`, orders `0`.**
