# A235 — PREREG: correction of native timeframe parity (not new trading logic)

Date: 2026-10-31. Scope locked to **BINANCE_USDT_M_FUTURES**, PAPER research only. Canonical mandate: `main/RESEARCH_MANDATE_LOCKED.md`, issue #9. Candidate queue: A234 74 candidate/variant records (separate branch `research/a234-all-promising-candidates-review`).

## Evidence requiring a controlled correction

A230 runner `research/a228_five_original/a228_run_original_freqtrade_five.py` has `config_for_run()["timeframe"] == "1h"` and never provides per-original `--timeframe`. Pinned source attributes are:
- TrendFollowing 4h — pinned source commit `11d7d66c60cf49a148cb61619b8061dc40d2510c`, Git blob `ee2293e19f3cdecb082525f6d55a166249f74eb2`.
- Risk_Stair_S5 15m — commit `63c012a0329a280f99fe57896456d4b9363c9c71`, Git blob `9b6ba1f5466727da1e9446f4e283b1c555fca59b`.
- NASOSv7LongShort 5m — commit `44beaeb6a420cd8e9f2e4ea93e11d6cfa192ee03`, Git blob `172fd2b5e76cb1b14d4c9547b6046bff7f19ba7a`.

This is a **methodological defect** in A230 (and likely A228/A229, same runner lineage), not evidence that strategies are profitable. Previous PnL/MaxDD valid only for their actual runtime configurations; no old receipts deleted.

## Precommitted controlled replay

Keep pinned untouched original strategy bytes, Binance mainnet USD-M 5m OHLCV/mark/funding and original A228 downloader, Freqtrade==2026.9, 3-pair experimental basket BTC/ETH/SOL, 1000 USDT wallet, 100 USDT stake, max_open_trades=3, isolated, protections enabled, and fee base 0.05% per side / stress 0.11% per side.

**Only controlled change for this cycle:** remove the global 1h strategy override; pass `--timeframe 4h` for TrendFollowing, `--timeframe 15m` for Risk_Stair_S5, `--timeframe 5m` for NASOS. Validate source literal timeframe via AST before any run; if unmatched -> BLOCKED not substituted.

Use detail `--timeframe-detail 5m` on 4h and 15m runs only; none on base 5m. Each original runs in 2024-01-01..2024-12-31, 2025-01-01..2025-12-31, and 2026-01-01..2026-05-31; all three in both fee scenarios, **18 native configurations**, with full preserved ZIP trade ledgers and explicit failed-run receipts. This expands, rather than cherry-picks, A230's narrower later-period coverage. Use `--cache none` and distinct output directories. No hyperopt, no after-the-fact parameter/pair selection.

## Evidence and verdict conditions

Keep full native output JSON/ZIP, normalized strategy/timeframe/scenario/year/account PnL, max drawdown and trade counts; compare same 2025 A230 fee runs. Validate native transaction journals, funding inputs, and causal lookahead in later cycles. Until original author portfolio, real spread/slippage, margin/liquidation, complete source chronology, and untouched OOS/forward PAPER are verified, status `REVIEW_OPEN_PARITY_EXPERIMENT`, never `VERIFIED_FUTURES_CANDIDATE`.

A235 intentionally **does not** prove native author universe/account parity: baseline still fixes basket, stake, max_open_trades and order assumptions. Broader A234 queue, source restoration, Double MA one-account, other candidates proceed independently. Three A220 veto sources and A214–A216 remain excluded. No real trades, no active PAPER schedule changes.

If GitHub Actions cannot execute or official market archives are inaccessible, record BLOCKED with exact workflow/job evidence. Do not fabricate numeric performance.
