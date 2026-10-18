# EMBER C31 — Public 1H liquidity raid / LTF BOS analog examples, provenance and NON-substitution rule
Research date: 2026-10-19. **PAPER ONLY / NOT_TRADE_READY.**

## Scope and source hierarchy

**TIER AUTHOR / PRIMARY.** Author's [4. Entry By BOS lesson](https://drive.google.com/file/d/1wwGRmEo-3sNd9EHqmyKCVdevusQc-2SO/view) prescribes 1H fractal *wick* liquidity raid, reactive lower 3m/5m BOS, selected BOS below BSL raid / above SSL raid, authentic preceding session/day fractal, TP 1H opposing liquidity where FTA does not spoil RR, SL beyond swept extreme. It explicitly mentions **market entry on price BOS crossing OR wait for candle settlement then limit entry**. Those are TWO different executable mechanisms that cannot be settled by 3m OHLC snapshots alone. Author links [Notion BackTest 1H/3M Jan–Jul 2023](https://www.notion.so/BackTest-1H-3M-2023-01-2023-07-70d3bb308f844a05a9ff1f069b5c6a3c?pvs=21). Exact title/Notion-ID public searches, link open, Drive exact search only surfaced author lesson, **NOT original labeled trades**. The user independently confirms inaccessible. Do NOT claim the backtest is deleted, leaked, or reconstructed.

**TIER PUBLIC ANALOG: Not author, no rule transplant.** These pages independently demonstrate that sweep -> LTF structural shift and entries exist in the general ICT literature, but disagree materially on timeframe, swing definition, timing, FVG, SL/TP, filters and market:

| Independent public source | What it actually illustrates / asserts | Critical non-equivalence with author EMBER |
|---|---|---|
| [ICT Trading Killzone/Silver Bullet overlap](https://innercircletrader.net/tutorials/killzone-silver-bullet-overlap/) (Jun 21 2026) | Illustrated Jun 10 2026 previous-high sweep -> MSS sell -> retrace **FVG** entry, target previous low. Uses 15m/5m context with 3m/1m MSS. | This is another trader's **FVG retest** within a fixed killzone, not author's selected **3m BOS market crossing**; cannot infer author pivot or FTA. |
| [Secuora BTC/ETH strict versus relaxed 5m Silver Bullet](https://secuora.net/strategy/ict-silver-bullet) (published Jun 2026) | Explicit source rules: NY 10–11 DST, known swing sweep, close MSS and freshest 5m FVG 50% retest, 2R/fees. Crucial: **strict same-candle** reading on 5m yielded just 1 BTC + 1 ETH research trade, whereas **relaxed** variant yielded 46 BTC + 47 ETH = 93 trades with negative cost-inclusive results. | Shows operationalization sensitivity: grouping events on **one candle** vs sequential events changed counts. Article's headline 93/12.9% is the RELAXED sample, NOT strict 2-trade 2023 author replay. Site's own backtest not independently audited here. |
| [BacktestingMax trader-shared gold ICT strategy](https://www.backtestingmax.com/strategy/ict-gold-a-liquidity-sweep-market-structure-shift-fair-value-GykYIUp2xmTxMnmBFO37) (shared Jun 2026) | Claimed 49 trader-logged trades, 46.9% win, 1.90 PF; requires HTF bias, liquidity sweep, MSS, displacement, new FVG, FVG retest, London/NY filters, target at opposing liquidity. | User-created **gold** model uses discretionary MSS/FVG retest and an author's self-reported outcome, not verified 1H→3m BOS in historical Binance USD-M and not ground truth for EMBER. |
| [Tradeshala source trader's liquidity workflow](https://marketshala.com/blog/ict-liquidity-strategy-91-win-rate) (Feb 2026 search excerpt; direct read returned 502) | Search-indexed author claims liquidity sweep→MSS/BOS/CSD and opposing liquidity targeting with 2m/3m confirmation, alleged 148 manual cases and 91.2%. | Report not independently replayed; **MSS OR BOS OR CSD** is explicitly *not a single defined academic 3m BOS*. Reported success unverified, never adopt threshold/exit/edge. |
| [Backtrex generic MSS guide](https://backtrex.com/en/blog/ict-market-structure-shift-mss-guide) (Jun/Sep 2026) | Defines MSS as close beyond prior major swing after sweep; explanatory price-structure terminology. | Their MSS terminology is NOT verified identical to EMBER author's BOS exact pivot or crossing/close choice. |

## Mechanical divergence to investigate on source data, no invented trade

**Original frozen C21 proxy**: 1H strict 1+1 fractal first wick raid with separate next fully closed 1H confirmation; then last preknown 3m 1+1 swing beyond raid pivot and **first 3m close** across that selected swing, with no inferred tick order. C21 has 539 raw technical edges, narrowed to 165 research singleton candidate cases through C24. This proxy and count are NOT instructor-labeled BOS.

**C31 new testable contrast**: for the very same retrospectively selected C21 3m swing, look back from its selected break at all **previously CLOSED original 3m bars** since BOTH (a) the raid's next 1H confirmation and (b) the 3m swing's right candle confirmation. Record separately (i) previous strict **wick** penetration *without* closing through, (ii) any previous **close** beyond selected swing, and (iii) timing delay from raid confirmation to technical C21 close-break. Mark all outcomes `SOURCE_PRICE_RELATIONSHIP_ONLY`, not market fills. If earlier wick penetration exists but no earlier confirmed close, market-cross mode **could** precede the C21 close; OHLC cannot determine actual tick fill. If an earlier close exists, dynamic last-swing C21 selection may be a re-cross of the later-selected level rather than first close relative to that level — an important **research proxy discrepancy** to inspect, not a confirmed instructor mistake.

**Non-importability**: public 2025/26 crypto spot, 2026 gold, Nasdaq, discretionary chart screenshots or Notion 2023 cannot serve as exact labeled futures historical author BOS/FTA goldens in the 2026-09→10 USD-M source. Exclude public examples from author goldens, execution, risk, stop, target and all strategy performance metrics. No percentage success or RR extrapolation.

## Missing for author certification

- Original 2023 author Notion case charts or instructor-confirmed export;
- selected local 3m BOS swing pivot and whether entry occurred at first crossing, closed candle or retest;
- certified IANA session clock and freshness reference;
- authored FTA ranking/tie-break and RR;
- instrument-appropriate SL buffer and intrabar tick ordering;
- explicit author-positive AND author-invalid model examples.

Until at least selected 3m BOS swing and case labels are sourced: `NEEDS_AUTHOR_BOS_GOLDENS`, no author-validated entry and **NO PAPER SIGNAL EXECUTION**. Existing C20–C30 modules/evidence MUST NOT be mutated.
