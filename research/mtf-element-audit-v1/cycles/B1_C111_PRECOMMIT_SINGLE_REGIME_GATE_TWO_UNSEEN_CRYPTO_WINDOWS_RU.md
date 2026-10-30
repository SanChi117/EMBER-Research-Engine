# C111 — precommit: один фильтр режима 1D + 4H (БЕЗ изменений C109)
Дата 2026-10-30. Paper only. Created BEFORE any C111 source-price retrieval or performance output.

## Замороженная гипотеза
C109 имеет качественно более корректную реакцию (fully closed H1 exits entire 4H FVG, direct 15m IMB or genuine pre-confirmed pivot BOS), 4H structural ATR hard stop and nearest unswept 4H pivot TP, но C110 на другом рынке 51 сделка -9.695331R и 19.05754% DD25. Гипотеза: C109 заведомо не следует использовать при разнонаправленном или шумовом контексте **предварительно закрытых 1D и 4H**, не увеличивая плечо, stop, target и не импортируя новый LuxAlgo.

КОД C109 BYTE FROZEN sha256 `39bf28a44cec0356b256853514c532b8f37be48f3da3477a365bd19c4add5557`. C111 only constructs a **pre-entry regime eligibility predicate** and evaluates it at FULLY CLOSED 1H reaction, *before 15m confirmation, before any paper entry*. No changes to entry price, 4H SL, 4H TP, max 48h hold, 4H zone lifecycle, previous-day D1/W1 base context, RR minimum1.25, costs 14/25/40bps, 1% modeled risk, virtual stop-first same 3m candle, target unconsumed 4H pivot.
**Eligibility exact**:
- Need 7 fully closed 4H candles as of current **CLOSED H1 reaction** `at`, and 4 fully closed D1 candles. All known close times `<= at` with no skipped original native3m interval.
- 4H net swing trend from last completed 4H close to closed 4H close six candles earlier. For LONG **delta4>0**, for SHORT **delta4<0**. 4H close-to-close six-step directional efficiency = abs(delta4)/sum(abs(adjacent 4H close changes) over six 4H bars) **>=1/3** exactly using Python Decimal, so flat/range chop and zero movement blocked (zero-efficiency fail closed).
- 1D direction = most recent fully closed D1 close minus closed D1 close three daily candles earlier. LONG **deltaD1>0**, SHORT **deltaD1<0**; strictly zero and opposing sign = NO_TRADE.
- These are a **single composite regime gate** derived purely from prior price action. 4H and 1D aligned with side; no new FVG/OB/BOS definitions, no data after 1H close, no retrospective early-loss side tuning. Exactly one fixed efficiency threshold 1/3, chosen before new data. A completed 4H candle at H1 reaction time is usable only if its CLOSE equals the actual reaction end, not when its beginning is historical.

## Two already frozen new historical windows (both not previously inspected by C105–C110)
WIN_A: 2025-03-01 00:00 UTC inclusive to 2025-05-04 00:00 UTC exclusive (64 full days).
WIN_B: 2025-07-01 00:00 UTC inclusive to 2025-09-03 00:00 UTC exclusive (64 full days).
Same 12 coins as C109/C110: `BNBUSDT,XLMUSDT,HBARUSDT,INJUSDT,OPUSDT,ALGOUSDT,CHZUSDT,ICPUSDT,SEIUSDT,PENDLEUSDT,LINKUSDT,UNIUSDT`, 12×64×2 **1536 original Binance Vision USD-M 3m daily ZIP + same-host .CHECKSUM, ZIP SHA and CSV SHA**, **737280 original native3m bars**, every source file 480 rows, no synthetic prices/substitution when missing (BLOCKED_SOURCE). Seven-day native3m warmup and last48h embargo, time-fold day32 in each window.
All C109 constants fixed. Use scoped temporary source calendar and scoped C109 `full_reclaim` predicate to test gating on TRUE 1H reaction **before** triggering 15m VC, restore bindings even under exceptions. Run the original C109 event-loop **separately** for each symbol and arm so busy-until, per-parent one-shot, and fills are recalculated. DO NOT merely remove losing existing trades from a post-exit journal; this is cherry picking and loses true overlap state.

Two predeclared arms for each window:
- CONTROL `B1_C109_UNCHANGED` uses exact original C109 full 1H reclaim + confirmed swing/15m IMB.
- GATED `B2_C111_1D_4H_REGIME` uses identical core and same original 4H SL/TP, with eligibility at 1H close.
Control and gated on SAME underlying original market. Report every blocked reason and original trade clock, no future data. C109 B0 weak previous candle baseline not needed for C111: already disproven.

**Economic gate, never redefined**: each window n>=30, early/late >=10 trades each; netR25>0, PF25>1.2, PF40>1.1, DD25<10% at modeled fixed 1% risk per PAPER trade. PLUS both windows individually must pass for a claim of period-robust historical gate, and both windows gated must improve / not significantly degrade vs control. A lower trade count is truthful `NO_POWER`, not permission to reduce n threshold. Report separately for each win and combined exploratory totals with caveat portfolio concurrent risks not modeled. There is no LIVE permission even on pass: historical prior windows, no tick bids/offers/liquidations, paper only.

## Acceptance
Negative tests for (1) fully closed H4/D1 availability and no lookahead, (2) contradictory/flat/noisy prices block, (3) directional clean H4+D1 qualifies, (4) strategy SHA frozen, (5) state restoration, (6) original parent4H stop & FTA exact, (7) recompute true paper replay not filter exited trades. CI Python 3.10/3.11/3.12 + previous 769/769, source checksums 1536/1536, JSON original receipts and all trades. Append A174 after end-to-end evidence frozen; update map/handoff. Economic FAIL must remain explicit even if one window looks good. No additional indicators or confidence claims.
