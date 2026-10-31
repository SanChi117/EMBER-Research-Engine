# A240 PRE-REGISTERED — Double MA, exact author BTC+ETH shared account

Date: 2026-10-31. First read main/RESEARCH_MANDATE_LOCKED.md + issue #9 and A239 checkpoint. R001 from A234 remains REVIEW_OPEN. Binance USDT-M Futures only, **no trades or PAPER modifications**.

## Author source and source config (not 4 separate sleeves)

- Original upstream: `MirrorNew/2026DoubleMaFuturesStrategy`, pinned commit `40af5c7c1c44253766428cfb06babf22f9817aa4`.
- Original Freqtrade source: `user_data/strategies/VideoDoubleMaFuturesStrategy.py`, git blob `22ca6588bbd056e671783f676f1a4010cbfc1bb6`. No edits to strategy logic, signals, stops, parameters, leverage (2x).
- Original Binance config: `config/config_binance_futures.json`, git blob `b16e6695673c58d8b7a712fd329994b3a85313f4`. Paper/offline operational changes only: disable author's localhost HTTP proxy, secrets and external services, bind data directory and author strategy original user_data, use a strict adapter for Freqtrade offline market metadata. No spot fallback.
- Author **one wallet 10000 USDT**, `stake_amount=unlimited`, `max_open_trades=1`, `tradable_balance_ratio=1`, **ordered whitelist BTC/USDT:USDT then ETH/USDT:USDT**, Freqtrade futures isolated, `timeframe=1h`, limit entry/exit, market SL and `stoploss_on_exchange=false`.

## Two fixed historical windows already seen; 4 runs, no optimization

- 2025 `[2025-04-01,2026-01-01)` with original A197 genuine Binance USD-M futures native 1h OHLCV, 4h/1d, mark and actual funding and native **5m** intrabar candles.
- 2026 `[2026-05-13,2026-10-01)` with original A195/A196 official genuine Binance USD-M archives and 5m detail.
- Frozen `freqtrade==2026.4`; base fee `0.0005` per side, stress fee `0.00125` per side; `--timeframe-detail 5m`, `--cache none`, source-backed original config for each period. Those periods are *historical robustness/parity*, **not fresh untouched OOS**, particularly 2025 pre-publication.
- Preserve complete native ZIPs for each of four runs, strategy + config + all trade timestamps, rejected signals, funding, reporting account-level net, DD, gross wins/losses, concentration top3, dollars and number of trades. Check that sum of all trade profit_abs matches native account profit, no two overlapping positive-length positions in author one-slot account. Never reconstruct result by filtering the A233 single-pair trades.
- Preserve SHA-256 of all official input source ZIP, Git blob SHA of original class/config. If 2025/2026 data missing, mark `BLOCKED_DATA` rather than replacing with spot. Adapter uses offline simulated Binance **contract metadata and one-tier liquidation model** as A195 did; this is NOT independently verified actual Binance precision, leverage tiers or liquidations.

## Promotion guard

Result at best `PROVISIONAL_HISTORICAL_PARITY` if economically positive, `NEGATIVE_NATIVE_PARITY` if negative, or `BLOCKED` on failure; never `VERIFIED_FUTURES_CANDIDATE` without authentic historical fills/limit queues, spread/slippage, official maintenance margin/liquidation/mark stops, source callbacks and post-publication untouched prospective PAPER. Top3-winner concentration is diagnostic, not automatic rejection.

A233 A232 4 separated wallets PnLs remain archival benchmark, not comparable capital geometry. A238 Risk S5 5x remains independently unverified, and all A234+A236 76 candidate/variant records remain in open review. Do not mutate A238, existing jobs, schedules, accounts or locked mandate.
