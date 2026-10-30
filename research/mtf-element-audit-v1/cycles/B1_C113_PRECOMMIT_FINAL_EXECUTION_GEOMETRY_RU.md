# C113 / PRECOMMIT — финальная проверка геометрии исполнения C109 (PAPER ONLY)

Date: 2026-10-30 UTC. Registered **before any new 2024 H1 raw source is downloaded or processed for C113**. Hypothesis is NOT an established edge.

## Why C113, not another C112

C112/A175 already exists and tested a different question: frozen C109 entries with unchanged 4H stop and alternate fresh opposing 4H FVG targets, on July–September and October–December 2024. It failed its registered economic gate. Do NOT overwrite C112 or relabel its evidence. C109–C111 and C112 retained untouched.

The final competing explanation is that **execution economics, not predictive signal quality**, might account for negative C109 outcomes at 25–40 bps. This is a single terminal experiment for this C109 family; if the primary alternative fails, **ARCHIVE C109 execution-rescue attempts; NO C114 filter/threshold salvage**. A different research family can be proposed separately without pretending this one passed.

## Immutable signal / source lineage

Original C109 B1 code: `d05/c109_simple_p4_core_vs_original_research.py` expected SHA256 `39bf28a44cec0356b256853514c532b8f37be48f3da3477a365bd19c4add5557`. Do not rewrite it, nor C105 4H structural module, native3m provider or C109/C110/C111/C112 evidence/journals. Base signal: three CLOSED 4H FVG bars, first 15m physical touch, closed 1H FULL EXIT, genuine closed 15m preconfirmed swing-break OR 3-bar IMB, **first available next original 3m open**. NO 1D+4H gate of failed C111, no extra indicators or imported LuxAlgo, no price-known-after-signal features.

Use the *same original C109 signal opportunities* for all counterfactual arms, anchored by timestamp + symbol + parent zone ID. For a FAIR paired comparison, restrict **all three arms' signal eligibility** to the COMMON 7-day terminal entry embargo, even though the historical original A0 48h model could trade later; this is a study sample restriction, not a mutation of A0's exit algorithm. Report A0 full-old-window results, if calculated, as separate context only, never in the primary paired comparison. Arm-specific capacity/limit expirations are documented separately. A difference in number of filled orders is a real effect and must not be censored.

## Three predeclared comparison arms (one primary test)

- **A0 benchmark**: exact original C109 B1 original-native3m market-at-next-open, 4H-FVG distal stop +/-0.15 ATR14(H4), nearest previously confirmed unswept 4H FTA pivot TP +/-0.15 ATR14(H4), 48h max hold, physical stop-first 3m exit, original min RR=1.25 and risk 0.2–10% bounds.
- **B1 diagnostic execution only**: after the same confirmed signal, place *virtual* LIMIT at original parent FVG **near boundary** (LONG bullish FVG upper edge; SHORT bearish FVG lower edge). Price must retest this frozen 4H level in original 3m prints within 24h of signal; otherwise `UNFILLED_EXPIRED` and **0R at the signal/opportunity level**, not delete from the dataset. Original A0 protective SL, original as-of signal 4H FTA TP, 48h hold from limit fill. Limit is not filled using a 15m/H1 candle interpolated between 3m bars; strictly native3m. No assumed maker rebates: charge roundtrip 14/25/40bps exactly as A0.
- **B2 PRIMARY execution hypothesis**: identical B1 retest LIMIT and 24h expiry, but protective SL behind the SAME ORIGINAL 4H FVG distal edge by **0.35 ATR14 of fully CLOSED 4H bars** instead of 0.15. No fixed 1.5%/2.5% stop manufactured from 3m or signal candle. Report actual original and altered stop distances in % and 4H ATR; classify separately actual 1.5–2.5% subset *descriptively*, not as a trade filter. TP remains the **same 4H confirmed unconsumed FTA destination**, fixed from evidence visible at original signal time; no future zone shifting. Stop can never expand **after an order is filled**. Maximum holding = **7 calendar days from fill**. Hard stop is physically executable on native3m during all 7 days. No discretionary break-even / averaged positions / carry cost omission.

B1/B2 order behavior is CONSERVATIVE:
1. Virtual LIMIT becomes active only at first original 3m open after confirmation. If the opening print already crossed the would-be stop, score an assumed bad limit-fill then protective stop at that opening price (do not cancel as an easy escape). If open is already at/better than the limit but not across stop, fill at limit (do not claim price improvement).
2. A LONG limit is touched when native3m LOW <= limit; SHORT when HIGH >= limit. Check candle opening gap and STOP on same bar as fill pessimistically: if both occur, count a fill and stop-first, including beyond-stop gap fills at observed open when applicable. No fictional fill before the triggering market bar.
3. If the frozen parent zone has a **fully closed 4H invalidation before limit fill**, classify `CANCELLED_PARENT_INVALIDATION`; retain the signal at 0R. If existing candidate has another active limit/position on same symbol, mark `CAPACITY_BLOCKED` and retain it in opportunity-denominator. No simultaneous positions for one symbol.
4. Original 4H risk stop and 4H target must be on opposite sides of fill; derived RR >= 1.25 and stop distance 0.2–10%; otherwise `STRUCTURE_NOT_ADMISSIBLE` as 0R signal opportunity, not posthoc exclude. Underlying original B1 signals remain in A0 accounting.
5. Simulate entries/exits with actual original 3m OHLC only, stop-first within ambiguous same candle, stop gap at observed open, target no more favorable than target price, final hold timeout at first close at expiry. Emit separate fee and gross return components; same 14/25/40bps roundtrip for all. Funding and overnight holding must be reported as unavailable/underestimated unless actual historical rates are retrieved. **A favorable B2 pass with missing funding is not sufficient to turn on LIVE.**

**Intention-to-treat primary accounting**: all original C109 B1 signal/trade opportunities must enter each arm's denominator, including unfilled, invalid, or capacity-blocked virtual orders (0R, no commission). Separately report **filled-only** netR/PF/DD and compare A0 on exact B2 filled timestamps (paired matched diagnostic). Do not announce a successful alternative based exclusively on the filled subset; lower fill rate is part of the economic result. Do not sum R across 12 symbols as literal achievable leveraged equity without a contemporaneous capital model. For DD, separately model 1% capital risk per fill, capital availability, simultaneous exposure and mark-to-market bounds.

## New PREDECLARED data and hold embargo

Two 64-day 2024 historical windows distinct from all C105–C112 research windows used for THIS family:

- WIN_A: **2024-01-01 00:00 UTC <= original time < 2024-03-05 00:00 UTC**.
- WIN_B: **2024-04-01 00:00 UTC <= original time < 2024-06-04 00:00 UTC**.

Fixed universe of 12 Binance USD-M symbols inherited from C109: BNB, XLM, HBAR, INJ, OP, ALGO, CHZ, ICP, SEI, PENDLE, LINK, UNI (each USDT). Expected `2 * 64 * 12 = 1536` original Binance Vision native3m DAILY ZIP; `1536 * 480 = 737280` OHLC rows. Demand provider .CHECKSUM plus ZIP and extracted CSV SHA, no fabricated bars. First 7 days warmup per period; **last 7 full days are embargo for eligibility of ALL arm signals and fills** to leave maximum B2 hold available. A limit issued BEFORE entry embargo that remains unfilled when embargo starts is recorded as 0R (not silently excluded); all eligible opportunities remain in the denominator. Temporal split day32 for each window (2024-02-02 and 2024-05-03 UTC). If any source missing, `BLOCKED_SOURCE`, do not substitute data, shift windows, or call it success.

Past 2024 C112 windows (whose A0 controls were positive: 81 trades +31.893675R and 45 trades +6.630285R at 25bps), 2025 C111 windows, 2025–26 C110 window and C109 2026 initial discovery window are prior EXPOSED evidence; do not repurpose them to select B2 parameters. Windows above are historical out-of-sample relative to this exact proposed experiment, **NOT future prospective OOS**. No true-trading claim is supported by them alone.

## Falsification, admission and locked stopping rule

**Primary prereg decision = B2 evaluated jointly across the two windows, each window separately passing**:
- B2 filled trade N>=30 per window, each early/late temporal fold filled N>=10; opportunity/limit fill rates always published.
- NetR at 25bps >0, profit factor at 25bps >1.2, profit factor at 40bps >1.1. 25bps **intention-to-treat** opportunity netR >0 AND full filled-trade netR >0 (their summed Rs coincide when nonfills=0; rates differ).
- Modelled portfolio DD at 1% capital risk per filled position <10% **including simultaneous exposures** and conservative stop gap fills; portfolio capital management fully specified before results, otherwise `NO_PORTFOLIO_DD_EVIDENCE`.
- B2 improves 25bps netR over A0 on the same full original-signal opportunity denominator in EACH window, not only on cherry-picked filled survivors.
- Source proof, timestamp causality, limit same-bar adversarial tests, immutable signal SHA, fee sensitivity and reproducible CI PASS.

Any failed criterion = `REJECT_B2_AND_ARCHIVE_C109_FAMILY`. Insufficient N = `NO_POWER_AND_ARCHIVE_C109_RESCUE_FOR_NOW` (not a pass). B1 cannot be promoted merely because B2 failed. No trial-and-error widening, choosing a different limit band, changing hold days or changing windows after reading outputs. Preserve all negative evidence. Even if both pass, **PAPER only** until separately preregistered prospective forward evaluation with funding/latency/order book execution evidence.

## Required deliverables

Before any data download: script hash, above precommit hash/commit, strategy definitions and test cases; then implementation and 3.10/3.11/3.12 unit tests; only then original Binance data acquisition and CI source receipts. Output per-signal source/event trace, fill/unfill counts, 25/40bps net R, PF, DD with capital concurrency, matched-pair comparisons, early/late halves, fatal-error diagnostics, and definitive PASS/FAIL. Record next A176 journal checkpoint **only on actual implemented, verified work**, not on this precommit alone.
