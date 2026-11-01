# R030 source audit + independent source block (2026) + next OOS 2023

**2026-11-01 · RESEARCH_ONLY · NO VERIFIED_FUTURES_CANDIDATE.**

## Original source (not a newly invented strategy)

Source repository freqtrade/freqtrade-strategies, frozen commit f3340ce11f5bdf62f598522e64d1f5638eaa13f5, path user_data/strategies/futures/VolatilitySystem.py, original Git blob **15ce2473f3f60bd33c4a67b0b8b228e379850f19**. Original source:
- 1H signals built from resampled 3H ATR multiplied by 2 against 3H candle-close change.
- Long if signed close_change exceeds prior 3H ATR; short if opposite signed change exceeds. Position exits on reverse signal; ROI is effectively not a tight profit target.
- **stoploss=-1 (−100% nominal strategy stop)**, can_short True, **2x leverage**, initial stake half of proposed, **position adjustment/DCA** on same-side follow-up signal, maximum 2 successful entry fills.
- The SOURCE contains no structural 4H stop. In isolated futures 2×, price/adverse mark move and maintenance margin can cause liquidation long before an absolute 100% unlevered price loss. Hence a positive Freqtrade proxy never proves safely deployable strategy.

## Existing native controlled A245 results — NOT author wallet and NOT fully verified

BTCUSDT, ETHUSDT, SOLUSDT, common USDT1000 wallet, stake USDT100, max3, isolated futures, genuine Binance Vision archived 5m/8h mark/funding, Freqtrade 2026.9, BASE 0.05%, STRESS 0.11% each-side fee:

- 2024 STRESS **+15.62758473%**, 88 trades, account MDD 11.176603%.
- 2025 STRESS **+16.166268094%**, 80 trades, account MDD 15.787493%.
- January–May 2026 STRESS **+2.238313457%**, 37 trades, account MDD 6.407465%.
- These are three favorable **previously inspected windows**, not independent-new test. Mark/funding source input does not equate to verified exchange maintenance tiers or L2 fills. **0 VERIFIED**.

Native original research proof source: A245 group B frozen metrics JSON in prior research branch.
[Historical A245 run](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41245981488).

## June–October 2026 independently preregistered **DATA_BLOCKED**, not FAIL or PASS

[Original frozen 2026 June–October rules](https://github.com/SanChi117/EMBER-Research-Engine/blob/research/r030-2026jun-oct-original-futures-oos-20261101/research/r030_oos_20261101/PRE_REGISTERED_R030_USDM_2026_JUN_OCT.md).

[CI data audit #41319112322](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41319112322) verified official Binance 8h BTCUSDT mark source June 2026 has **87/90** original bars. Same-month official 1H has **696/720** (missing entire June 29), and 5m mark 8352/8640 (same day). Checksums for those original ZIP match published Binance Vision checksums. We deliberately did **not** fabricate or substitute mark bars. An independent check also revealed official 2026-10 monthly 5m trading candles were **HTTP 404** on 2026-11-01, [CI #41319398781](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41319398781). Hence it is **not possible to report a complete clean native June-Oct PnL** under original published archives at this timestamp; any such claim would be fabricated.

A further source-repair attempt checked original daily Binance Vision and historical USD-M mark API for the missing 2026-06-29 before any PnL results. The source repair did not change strategy conditions and is not eligible for tuning. The immutable source problem and future-month publication are recorded.

## Independent alternative fixed before PnL: June–October 2023

Due solely to the 2026 data blockers, alternative independent pre-2024 period was **frozen before reviewing any R030 2023 returns**:
[PRE_REGISTERED_R030_2023_JUN_OCT.md](PRE_REGISTERED_R030_2023_JUN_OCT.md).

Exact original, same three symbols, costs, wallet, margin/fee assumptions and native engine; authentic May–Oct 2023 Binance futures price/mark/funding plus SHA receipts. [CI #41319667310](https://github.com/SanChi117/EMBER-Research-Engine/actions/runs/41319667310). The 2023 result must be recorded when CI completes, whether favorable, unfavorable or blocked; do not move dates because of PnL.

**Risk veto still active:** even if all controlled historical years have favorable means, no VERIFIED status until original full portfolio execution fidelity, mark-driven actual historical liquidation tiers, funding, fills, multi-regime and prospective PAPER. No live/PAPER changes.
