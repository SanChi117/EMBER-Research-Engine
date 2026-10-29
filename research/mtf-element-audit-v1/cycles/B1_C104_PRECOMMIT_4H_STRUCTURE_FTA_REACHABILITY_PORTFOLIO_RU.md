# C104 PRECOMMIT — 4H структура, достижимость FTA, коррелированные позиции
Date: 2026-10-30. Research-only PAPER. Frozen before any new 10-symbol archive download, signal or PnL observation.

## Source-supported motivation (Kimi 30.10.2026 + independent cross-check)
C102/C103 original C93 exact 45/45 proof and all-four-negative net25. Kimi correctly identifies small structural entry→SL distance / high roundtrip bps, weak 1D direction test, concurrent directional clusters, apparently unreachable far 1H FTA under the 12h time cap. Do NOT assume that widening stop (1–1.5%), maker fill (0.05–0.10R), forcing target RR=2, or shortening holding period guarantees profitability; these remain SEPARATE untested hypotheses. Kimi's 12h-timeout claim is not verified as dominant: among C103 16 baseline trades derived RR>=4, 13 SL-first, 2 FTA, only 1 timeout. Retain 12h and original structural prices.

## New instruments and holdout designation
Ten native3m USD-M Binance Vision symbols **AAVEUSDT, APTUSDT, ARBUSDT, ATOMUSDT, ETCUSDT, FILUSDT, LTCUSDT, NEARUSDT, TRXUSDT, UNIUSDT** (no coins used in C93 original 5 or C102 transfer 5). Whole 32 full UTC days **2026-09-26 through 2026-10-27 inclusive** (2026-10-28 exclusive): 10×32 = **320 original 3m daily ZIP** + same-host CHECKSUM and each ZIP + CSV SHA. Exactly 10×15360=153600 native3m bars if available. Same 7d no-signal warmup, 12h final embargo, 12h paper horizon; only fully closed bars. Strict original C102 native_daily ZIP/CSV checker re-used through isolated, reversible research-only symbol-allowlist adjustment. C93 and C102 original source files must remain SHA-unchanged. If any archive missing, fail **BLOCKED_SOURCE** and do not substitute tickers/dates after looking at outcomes.

## PREDECLARED causal quality hypothesis
For an original unchanged C93 candidate 1H wick raid -> native3m BOS, next 3m OPEN entry, structural raid + ATR SL, original nearest unswept 1H liquidity FTA with ATR pad as TP; original minRR 1.25 is admissibility only. Never set RR target or retroactively choose distant/closer FTA. Original 14bps paper fill; 25 and 40bps stress by risk width.

A. **4H_DIRECTION** at the next-3m entry timestamp. Aggregate only FULLY CLOSED 4H candles aligned UTC; latest two fully confirmed **4H pivot lows** rising => long (latest LOW price > preceding LOW price); latest two fully confirmed **4H pivot highs** falling => short (latest HIGH price < preceding HIGH price). Both sides additionally require last fully closed 4H close to be on matching side of the midpoint of highest-high/lowest-low of last six fully closed 4H candles. 4H pivot=2 left and 2 right 4H candles (confirmed only when right two CLOSED); require enough confirmed pivots, else reject, never proxy with future or 5m candles. This is research/adaptation, not exact original academic certification.

B. **FTA_REACHABLE_12H** at same timestamp. Use last 12 **FULLY CLOSED 1H** original aggregated candles; absolute distance Entry→untouched original structural TP must not exceed empirical observed high-low range of those 12 closed 1H candles. Not fixed RR cap or fabricated TP. This 12h window matches frozen maximum horizon, but past range cannot guarantee future range.

C. **PRIMARY (one jointly predeclared hypothesis)** = A AND B. No threshold optimization, no choosing the best among the partial filters after outcome. Also report individual pass counts, reasons for missing 4H pivot or too far FTA, and early/late folds; individual checks are only diagnostics, NOT candidates for promotion.

## Portfolio risk context
Predeclare directional cap **at most one concurrently open PAPER position of same LONG/SHORT sign across all ten coins**, independent of per-symbol C93 busy. Side occupancy is tracked at the historical entry timestamp from accepted position through actual exit_ms; no future outcome is used to decide eligibility except the earlier observed exit by that time. Benchmark and new quality strategy evaluated with same cap. Report supplementary uncapped raw baselines / quality for diagnostic impact only (not chosen for success). Global same-direction cap controls concentration, cannot create favorable expected value by itself.

## Primary comparison and falsification
- PRIMARY: QUALITY_PORTFOLIO (A&B+directional cap) vs BASELINE_PORTFOLIO (original C93 + same cap), all 10 coins, 14/25/40bps, fully chronological; netR, PF, 1%-risk modeled DD, n, exits/side, early (<2026-10-15) vs late (>=2026-10-15), per symbol.
- Independent original C93 trade-by-trade baseline exact parity (pre-cap), not just source-code equivalence; reject if any Entry/SL/FTA/TP/exit/netR diverges from original unchanged C93 state machine.
- Predefined provisional economic admission PRIMARY only with >=30 trade observations, two temporal folds >=10 each, netR25>0, PF25>1.2, PF40>1.1, maxDD25<10%. Also require PnL25 and PF25 improvement versus BASELINE_PORTFOLIO (non-tautological); scenario reduction alone not success. NO_POWER if <30, REJECT if fail, NOT TRADE READY even if pass (multiple prior human hypotheses and historical-only data).
- PnL at *entry/stop* original C93 no invalid extra fills. 0 actual orders. No market-limit-execution claim.
- This is historical unseen-*symbol* holdout relative to prior C93/C102. NOT a truly prospective live OOS; drawdown with 1% per-trade assumption is illustrative, not realistic combined-margin stress.

## Required artifacts
Separate original full source manifest and SHA immutable witness, 3 Python adverse tests, independent CI all three Python versions with prior 602 tests each, original C93 parity checker, explicit falsification report, append-only journal **A167**, root maps and handoff updated. Any missing correctness or data => no DONE. Confirm SHA166 before run. Do not change immutable A166 evidence, C93, C102 or fixed RR.
