# A241 — R003 BearRegimeShortV1, восстановлены исходный портфель и авторские отрицательные результаты

31 октября 2026. Это **source-and-config evidence audit** из pinned upstream, а не новый экономический прогон EMBER. Исследовательский мандат `RESEARCH_MANDATE_LOCKED.md` и issue #9 без изменений. Binance USDT-M Futures; никакого Spot, реальных заявок или изменения PAPER.

## Pinned original source and full portfolio (R003 from A234)

Источник `IvPalmer/Master-Trader`, immutable commit `8e29d170982c36a502de2c6ed14a80c6510c4921`.

- `ft_userdata/user_data/strategies/BearRegimeShortV1.py`, Git blob `a6c62639e60a28b050a462f646241e7a2ba9076c`: timeframe=1h, can_short=True, isolated 2× via `leverage` (min(2, max_leverage)), `startup_candle_count=250` with BTC 1h `mom20d=close.pct_change(20*24)`. 480 bars plus 6-bar rolling confirmation needed for finite momentum and bear gate; source-defined startup 250 alone isn't enough. Early warmup neutral/not eligible does not establish a negative performance claim. Test needs enough pre-history and correct informative availability.
- `ft_userdata/user_data/configs/backtest-BearRegimeShortV1.json`, Git blob `edec9cf35dafd3116e13203726932d89e0639d31`: wallet **$200**, stake **$100**, max open **2**; **20 original futures contracts** ADA, ARB, AVAX, BCH, BNB, BTC, DOGE, ENA, ETH, HBAR, LINK, LTC, NEAR, SOL, SUI, TAO, TRX, UNI, XRP, ZEC; Freqtrade futures isolated. This is NOT A228/A230 baseline wallet $1000, 3 pairs, max3.
- `docs/short_research_2026-04-20.md`, Git blob `a08c8413a7779808186a5b1fc0423a69f2926523`, original-author **negative after-cost study**, with 20 pairs, 2x, max2; full ~3.3 years `+19.67%/PF1.10` but 2023 `-6.58%`, 2024 `+31.25%` (1m-detail `+26.18%`), 2025 `-19.63%` (1m-detail `-15.91%`), 2026 YTD `-0.79%`. Author reports 2025 DD 39.1% 1h (37.4% 1m-detail) and explicitly retires the strategy. This is **EXTERNAL AUTHOR EVIDENCE**, not a fresh independent EMBER futures backtest. Historical in-sample/stress claims have their own limitations. Do not replace them with A230 3-market model results or declare original fully independently tested.
- Author also built `BearRegimeShortV1Viability.py` and pairlist/F&G wrapper **not used in the failed raw backtest** per author report; cannot silently substitute it to rescue historical edge.

## Correction to prior assessment

A228/A230/A229 model `BearRegime` had 3 pairs, wallet $1000 and max3 and did NOT reproduce original 20-pair $200 account. Their net PnL cannot confirm nor falsify the exact original portfolio. However original author **already reported multi-year negatives** in 3/4 years, so we should not spend large download compute merely to reproduce the one positive 2024 or cherry-pick winning pairs after seeing results.

Recommended decision: `REVIEW_OPEN_WITH_AUTHOR_NEGATIVE_EVIDENCE`. A new native author-account replay is justified only if we can guarantee a *new independent validation value*: full pinned data/fee/portfolio parity and distinguish it from author's already disclosed losses, or future post-publication prospective records. Confirm detailed warmup and Freqtrade source chronology and preservation of 20x capital competition before any experiment.

## Remaining candidate queue

A234 74 entries + A236 two additional TRANSFER hypotheses = 76 records/variants, not independent strategy count. A240 Double MA one-account native replay (separate branch) already preregistered; A238 Risk S5 provisional positive stress 2024/25, negative early 2026 and 5x liquidation unverified. Preserve all negatives, do not declare any strategy VERIFIED from this memo. User's three A220 veto repos and A214–A216 remain excluded.
