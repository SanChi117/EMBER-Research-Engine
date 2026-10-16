# B1/C20A — 32 дня ORIGINAL native 5m Futures → C08 original 15m/1d exact O/H/L/C/V

Date: 2026-10-16. Research and independent source verification, **PAPER ONLY**. Scope: **original 5m data lineage** required before the real 1H Raid → 5m BOS mechanism; no trades, VC, author-approved signal or backtest ROI.

## Author text — exact academic requirement vs our implementation

Source [4. Entry By BOS](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view): an intraday execution model most commonly uses **1H Liquidity Raid → 3m/5m BOS**, with a **wick-only 1H fractal raid**, BOS below the BSL raid for SHORT or above the SSL raid for LONG; fresh liquidity (previous session/max previous day), first 1H liquidity profit target, stop beyond the swept level, FTA invalidation and trading-session constraints. The source specifically says absence of 3m BOS invalidates the illustrative 1H/3m variant. It does NOT define crypto-equivalent pip thresholds or create labelled USD-M market executions.

Source [Liquidity / Fractals / Raid](https://drive.google.com/file/d/1sTrV-fAPe35xJ6WpMYrGfxy_WRV9i4JD/view): a 3-bar fractal needs its next candle to close and a clean fractal raid uses its wick. The previous C19 original native 15m geometric raid is NOT a substitute for the author-preferred 1H fractal raid + 3m/5m BOS. Source [StrongHL](https://drive.google.com/file/d/1lvPRbhfM6ZjfW7UP-30y9uND1R6VC13t/view): liquidity/inefficiency contact then confirmation via POI **or** BOS; those semantic approvals are not inferred from having a 5m price feed.

## Original source, closed-candle provenance, negative controls

- Five symbols: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BCHUSDT. UTC 2026-09-01 through 2026-10-02 inclusive.
- Per symbol independently downloaded Binance USD-M **monthly native 5m September ZIP** (8,640 original rows) + **daily native 5m Oct1 and Oct2 ZIPs** (288+288). **15 NEW original ZIPs**, each SHA256 of original binary compared to its same-host original `.CHECKSUM`; raw CSV SHA256 separately pinned. The same-host oracle is NOT a third-party digital signature. Exact HTTPS host, original Futures /um, timeframe 5m, symbol, period, 12 CSV columns, complete 300,000-ms UTC grid, `close_time=end-1`, finite exact Decimal OHLCV validated.
- Re-read **30 previously frozen original C08 15m/1d ZIP** (3x 15m + 3x 1d for each symbol, including monthly September and daily Oct1/2) using unchanged D04 strict source validator and immutable C08 receipts. Original D04 rejects 5m by design: it was left **unchanged**; C20 implements a separately restricted original 5m downloader and parser, not a relaxed C08 trust policy.
- Strict native **5m→15m** parity: aggregate every 3 consecutive **original 5m rows**, verify UTC start/end, O=first, H=max, L=min, C=third, V=exact Decimal sum; compare to **every one of 3,072 original C08 native 15m bars per symbol**. The upstream C16 separately proves 32 original 1d bars per symbol match aggregates from native 15m.
- New source models `d05/c20_original_32day_native5m_lineage.py`: immutable native original 5m row witnesses with origin ZIP SHA and raw row ID; separate September 8,640 and daily 288+288 source groups; reject corrupt/wrong ZIP, SHA, source root/host, symbol, row, UTC time, OHLCV, mutated in-memory proof, false author READY, 15m parity drift, incomplete history. Full original source validated before any past prefix, returns **only closed 5m rows as-of**.
- `tests/probe_c20_original_5m_monthly_cross_15m.py`: independent network reread of all **45 original ZIP sources**; exact pinned SHA, all 15,360 native15m OHLCV matches, 160 native daily matches and earlier 2026-10-02 00:05 UTC prefix (8,929 closed 5m rows). No future suffix leak.
- `d05/test_c20_original_32day_native5m_lineage.py`: **23 synthetic adversarial/positive tests**, checking full monthly size, continuity, checksum, wrong Futures market, wrong host, malformed ZIP member, incomplete 5m period, unclosed candle, tampered source SHA and mutated 5m/15m prices and volumes, false readiness and future as-of. These synthetic fixtures are NOT author-labelled goldens.

## 32-day original data evidence (independent CI)

| Source | BTC | ETH | SOL | XRP | BCH | Total |
|---|---:|---:|---:|---:|---:|---:|
| Native 5m original completed candles | 9,216 | 9,216 | 9,216 | 9,216 | 9,216 | **46,080** |
| Exact 5m→native C08 15m OHLCV equalities | 3,072 | 3,072 | 3,072 | 3,072 | 3,072 | **15,360 / 15,360** |
| Native C08 daily matches, 15m aggregated | 32 | 32 | 32 | 32 | 32 | **160 / 160** |
| New 5m original ZIPs | 3 | 3 | 3 | 3 | 3 | **15** |

- Verified [C20 initial original-source CI run 38951000322](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38951000322) SUCCESS: 29 original course-v05 plus **285 C10-C20** = **314 tests PASS**, 45 original native ZIP checks, 15,360 native 15m exact parity.
- Exact ZIP + CSV SHA identifiers for all 15 new archives are preserved in `evidence/c20/C20_ORIGINAL_5M_32DAY_LINEAGE_RESULT.json` pinned source Git blob `7fc957b210b14b8ab0380b8941a7b145def836dc`.
- Separate pinned results independent CI rerun: [C20 receipt replay](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38951260295) — see run conclusion for final status.

## Recorded failures and attempted falsification

1. [CI 38950844333](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38950844333) **FAILED** because the frozen **D04 C08-only approved whitelist** correctly rejects NEW 5m input. Reused same-host redirect/checksum primitive but isolated new 5m downloader; no modification to frozen C08/D04 source acceptance.
2. Two workflow config runs [38951205268](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38951205268) and [38951240102](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/38951240102) FAILED YAML parsing after a text replacement interpolated a literal `$` in regex and appended part of workflow. Repaired only the new workflow and retained failures.
3. Source unit tests catch future 5m timestamp, 15m tuple drift and foreign symbol. CI verifies frozen Git blobs from source-v05/C08/C14/C16/C17/C18/C19.
4. SHA same-host sources are **not** author labels; no 32-day independent **3m** archive yet; the source file does not provide a 1H raid, live entry, trader PNL or settled BOS geometry.

## Acceptance boundary and immediate next cycle

C20A (native5m lineage) is DONE only with independent pinned receipt PASS + A086 append-only SHA journal PASS; **B1/C20 as a whole PARTIAL**. Next **B1/C20B**: build source-backed, closed **1H three-bar fractal wick raid** on these C20 original native5m candles, then causal **5m BOS after 1H raid close**. Distinguish author 1+1 fractal definition from frozen v05 provisional 2+2 pivots, never copy v05 automatic 24h freshness approximation as exact author rule; test BOS below BSL extreme / above SSL extreme, no moving any bar from future; preserve multi-parent conflict and reason for no FTA/fresh-session certification. No author-labelled Futures goldens, no READY or orders.
